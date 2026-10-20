"""Interface de terminal do ReaDroid. Mantemos o menu simples para telas pequenas."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import __version__
from .banner import render as render_banner
from .analyzer import (analyze_manifest, decompile_with_jadx, extension_warning, extract_smali_with_apktool,
                       inspect_apk, scan_strings, write_report)
from .builder import (DEFAULT_ALIAS, DEFAULT_STOREPASS, QUICK_EDITS, apply_quick_edits, build_pipeline,
                      rename_package, valid_package_name, verify_apk)

# Usa a pasta desta cópia do projeto, não uma pasta fixa em ~/ReaDroid.
# Isso evita salvar os resultados em outro lugar quando o projeto foi extraído
# em Downloads ou executado a partir de um clone do GitHub.
BASE = Path(__file__).resolve().parents[1]
REPORTS = BASE / "reports"
OUTPUTS = BASE / "output"
BUILDS = BASE / "builds"
KEYSTORE = BASE / ".readroid-keystore.jks"
GREEN, CYAN, YELLOW, RED, DIM, RESET, BOLD = "\033[92m", "\033[96m", "\033[93m", "\033[91m", "\033[2m", "\033[0m", "\033[1m"

# Remove sequências de escape ANSI e caracteres de controle antes de imprimir qualquer
# dado que veio de dentro de um APK (strings, nomes de arquivo, saída de ferramentas).
# Sem isso, um APK malicioso poderia manipular as cores/o cursor do seu terminal.
_CTRL_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize(text: str) -> str:
    return _CTRL_RE.sub("", str(text))


def clear() -> None:
    os.system("clear" if os.environ.get("TERM") else "")


def width() -> int:
    return max(32, min(shutil.get_terminal_size((44, 24)).columns, 78))


def banner() -> None:
    clear()
    cols = width()
    for line in render_banner(cols, (GREEN, CYAN, RESET)):
        print(line)
    print(BOLD + f"v{__version__}" + RESET + CYAN + " · IA opcional · Sem root · Offline por padrão" + RESET)
    print(DIM + "OffensiveTec" + RESET)


_PASTE_RE = re.compile(r"\x1b\[[0-9;?]*[~a-zA-Z]|\[20[01]~|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
                       r"|[\u200b-\u200f\u202a-\u202e\u2060\ufeff]")


def clean_path(raw: str) -> str:
    """Limpa o caminho digitado/colado: remove sequências de 'colar' do terminal (ESC[200~),
    caracteres invisíveis, espaços e aspas nas pontas. Colar no Termux às vezes traz lixo invisível."""
    return _PASTE_RE.sub("", raw).strip().strip('"').strip("'").strip()


def safe_input(prompt: str = "") -> str:
    """input() que não derruba o menu com traceback se o terminal fechar (Ctrl+D/Ctrl+C)."""
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


def pause() -> None:
    safe_input("\nENTER para voltar ao menu...")


def ask_apk() -> Path | None:
    # Para deixar o fluxo mais rápido no celular, tentamos encontrar APKs nas pastas comuns.
    candidates: list[Path] = []
    search_dirs = [Path.cwd(), Path.home() / "storage" / "downloads",
                   Path.home() / "storage" / "shared" / "Download",
                   Path.home() / "storage" / "shared" / "Documents",
                   Path("/storage/emulated/0/Download")]
    seen: set[str] = set()
    for folder in search_dirs:
        if not folder.is_dir():
            continue
        try:
            for item in sorted(folder.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if (item.is_file() and item.suffix.lower() in (".apk", ".apks", ".xapk")
                        and str(item) not in seen):
                    candidates.append(item)
                    seen.add(str(item))
        except OSError:
            # Uma pasta sem permissão não deve impedir o uso das demais.
            continue
    candidates = candidates[:20]
    if candidates:
        print(CYAN + "APKs encontrados nas pastas comuns:" + RESET)
        for index, item in enumerate(candidates, 1):
            try:
                size_mb = item.stat().st_size / (1024 * 1024)
                print(f" [{index}] {sanitize(item.name)} ({size_mb:.1f} MB)")
            except OSError:
                print(f" [{index}] {sanitize(item.name)}")
        print(" [P] Informar outro caminho")
        choice = safe_input("Escolha um APK: ").strip()
        if choice.lower() != "p":
            try:
                return candidates[int(choice) - 1]
            except (ValueError, IndexError):
                print(YELLOW + "Seleção não reconhecida; informe o caminho manualmente." + RESET)
    raw = clean_path(safe_input("Caminho completo do APK: "))
    if not raw:
        print(YELLOW + "Nenhum arquivo informado." + RESET)
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists() or not path.is_file():
        print(RED + "Arquivo não encontrado. Dica: execute termux-setup-storage e use ~/storage/shared/Download/app.apk" + RESET)
        print(DIM + f"Caminho lido pelo ReaDroid: {str(path)!r}" + RESET)
        return None
    warning = extension_warning(path)
    if warning:
        print(YELLOW + warning + RESET)
    return path


def ask_decoded_dir() -> Path | None:
    """Lista pastas já decodificadas pelo Apktool (opção 5) e deixa escolher ou digitar outra."""
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    candidates = sorted((p for p in OUTPUTS.glob("*_apktool") if p.is_dir()),
                        key=lambda p: p.stat().st_mtime, reverse=True)[:15]
    if candidates:
        print(CYAN + "Pastas decodificadas com Apktool:" + RESET)
        for index, item in enumerate(candidates, 1):
            print(f" [{index}] {sanitize(item.name)}")
        print(" [P] Informar outro caminho")
        choice = safe_input("Escolha a pasta: ").strip()
        if choice.lower() != "p":
            try:
                return candidates[int(choice) - 1]
            except (ValueError, IndexError):
                print(YELLOW + "Seleção não reconhecida; informe o caminho manualmente." + RESET)
    raw = clean_path(safe_input("Caminho da pasta decodificada (saída do Apktool): "))
    if not raw:
        return None
    path = Path(raw).expanduser()
    if not path.is_dir():
        print(RED + "Pasta não encontrada." + RESET)
        print(DIM + f"Caminho lido pelo ReaDroid: {str(path)!r}" + RESET)
        return None
    return path


def save_and_show(report: dict, prefix: str, apk: Path) -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = REPORTS / f"{apk.stem}_{prefix}_{stamp}.json"
    write_report(report, target)
    print(GREEN + f"\nRelatório salvo: {target}" + RESET)


def run_action(title: str, action: Callable[[Path], dict]) -> None:
    print(CYAN + f"\n{title}" + RESET)
    apk = ask_apk()
    if apk is None:
        return
    try:
        report = action(apk)
        save_and_show(report, title.lower().replace(" ", "_"), apk)
        for warning in report.get("warnings", []):
            print(YELLOW + warning + RESET)
        if "permissions" in report:
            print(f"Permissões encontradas: {len(report.get('permissions', []))}")
            for item in report.get("permissions", [])[:25]:
                print(" •", sanitize(item.get("name", "")))
            if not report.get("decoded"):
                print(YELLOW + "Manifesto não decodificado. Veja a mensagem no relatório." + RESET)
        if "urls" in report:
            print(f"URLs: {len(report['urls'])} | Domínios: {len(report['domains'])} | IPs candidatos: {len(report['ipv4_candidates'])}")
            if report.get("truncated_categories"):
                print(YELLOW + f"Atenção: categorias truncadas (limite atingido): {', '.join(report['truncated_categories'])}" + RESET)
        if "zip_entry_count" in report:
            print(f"Arquivos: {report['zip_entry_count']} | DEX: {len(report['dex_files'])} | Bibliotecas nativas: {len(report['native_libraries'])}")
    except Exception as exc:  # O menu não deve fechar por um erro inesperado de um arquivo.
        print(RED + f"A análise falhou: {exc}" + RESET)
        print("O arquivo original não foi modificado.")


def dependencies() -> None:
    print(CYAN + "\nVERIFICAÇÃO DE DEPENDÊNCIAS" + RESET)
    for name in ("python", "java", "jadx", "apktool", "aapt", "aapt2", "zipalign", "apksigner", "keytool", "unzip", "git", "opencode"):
        path = shutil.which(name)
        print(f"[{GREEN + 'OK' + RESET if path else YELLOW + '--' + RESET}] {name}: {path or 'não encontrado'}")
    if shutil.which("java"):
        try:
            result = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=5)
            print(sanitize((result.stderr or result.stdout).splitlines()[0]))
        except (OSError, subprocess.TimeoutExpired, IndexError):
            print("Java encontrado, mas não foi possível consultar a versão.")
    if shutil.which("jadx"):
        try:
            result = subprocess.run(["jadx", "--version"], capture_output=True, text=True, timeout=8)
            print("JADX:", sanitize((result.stdout or result.stderr).strip().splitlines()[0]))
        except (OSError, subprocess.TimeoutExpired, IndexError):
            print("JADX localizado; versão não confirmada.")
    print(CYAN + "\nPara reconstruir e assinar APKs (opção 11):" + RESET)
    print(" pkg install apktool aapt apksigner openjdk-21")
    print(" (aapt já inclui o zipalign; apksigner dá assinatura v1+v2+v3;")
    print("  sem ele, cai para jarsigner, que só assina v1.)")


def open_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    print("Pasta:", path)
    print("Conteúdo:")
    items = list(path.iterdir())
    if not items:
        print(" (vazia por enquanto)")
    for item in sorted(items, key=lambda p: p.name.lower())[:60]:
        print(" [DIR]" if item.is_dir() else " [FILE]", sanitize(item.name))


TEXT_EXTENSIONS = {
    ".java", ".kt", ".smali", ".xml", ".json", ".txt", ".md", ".html",
    ".js", ".css", ".properties", ".yml", ".yaml", ".gradle", ".pro",
    ".cfg", ".ini", ".log", ".sh", ".py", ".manifest"
}


def view_text_file(path: Path) -> None:
    """Abre arquivos de texto no próprio terminal, com paginação quando disponível."""
    try:
        if path.stat().st_size > 5 * 1024 * 1024:
            print(YELLOW + "Arquivo grande (>5 MB); não será carregado inteiro na tela." + RESET)
            print("Caminho:", path)
            return
        content = path.read_text(encoding="utf-8", errors="replace")
        clean = sanitize(content)
        less = shutil.which("less")
        if less:
            # Sem -R: não interpretamos códigos de escape do arquivo, só mostramos como texto.
            # Um arquivo decompilado/extraído é conteúdo não confiável.
            proc = subprocess.run([less], input=clean, text=True, check=False)
            return
        lines = clean.splitlines()
        page_size = 120
        for start in range(0, max(1, len(lines)), page_size):
            print("\n".join(lines[start:start + page_size]))
            if start + page_size < len(lines):
                answer = safe_input("\nENTER para próxima página, q para sair: ").strip().lower()
                if answer == "q":
                    break
        if not lines:
            print("(arquivo vazio)")
    except (OSError, UnicodeError) as exc:
        print(RED + f"Não foi possível abrir o arquivo: {exc}" + RESET)


def browse_directory(path: Path, allowed_roots: tuple[Path, ...]) -> None:
    """Navegador simples: seleciona diretórios e abre arquivos pelo número."""
    current = path.resolve()
    roots = tuple(root.resolve() for root in allowed_roots)
    while True:
        print(CYAN + f"\nExplorador ReaDroid: {current}" + RESET)
        try:
            entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError as exc:
            print(RED + f"Não foi possível listar a pasta: {exc}" + RESET)
            return
        if not entries:
            print(" (pasta vazia)")
        for index, item in enumerate(entries, 1):
            kind = "[DIR] " if item.is_dir() else "[ARQ] "
            try:
                size = f" ({item.stat().st_size / 1024:.1f} KB)" if item.is_file() else "/"
            except OSError:
                size = ""
            print(f" [{index}] {kind}{sanitize(item.name)}{size}")
        print(" [..] Voltar uma pasta | [0] Sair do explorador")
        choice = safe_input("Abrir > ").strip().lower()
        if choice in {"0", "q", "sair", ""}:
            return
        if choice in {"..", "p", "voltar"}:
            if current in roots:
                return
            parent = current.parent.resolve()
            if not any(parent == root or root in parent.parents for root in roots):
                return
            current = parent
            continue
        try:
            selected = entries[int(choice) - 1].resolve()
        except (ValueError, IndexError):
            print(YELLOW + "Seleção inválida." + RESET)
            continue
        if not any(selected == root or root in selected.parents for root in roots):
            print(RED + "Caminho fora das pastas de resultados bloqueado." + RESET)
            continue
        if selected.is_dir():
            current = selected
        elif selected.is_file():
            if selected.suffix.lower() in TEXT_EXTENSIONS or selected.suffix == "":
                view_text_file(selected)
            elif shutil.which("termux-open"):
                print("Abrindo com o aplicativo Android associado...")
                result = subprocess.run([shutil.which("termux-open"), str(selected)], check=False)
                if result.returncode:
                    print("Não foi possível abrir externamente. Caminho:", selected)
            else:
                print("Não há termux-open instalado. Caminho do arquivo:", selected)
                print("Instale o pacote termux-tools para abrir arquivos no Android.")
            safe_input("\nENTER para voltar ao explorador...")


def browse_generated_files() -> None:
    """Permite localizar e abrir saídas do JADX/Apktool, builds e relatórios JSON."""
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    BUILDS.mkdir(parents=True, exist_ok=True)
    while True:
        print(CYAN + "\nARQUIVOS GERADOS" + RESET)
        print(" [1] Código decompilado e recursos (output)")
        print(" [2] Relatórios JSON (reports)")
        print(" [3] APKs reconstruídos e assinados (builds)")
        print(" [0] Voltar ao menu principal")
        choice = safe_input("Explorar > ").strip()
        if choice == "0" or choice == "":
            return
        if choice == "1":
            browse_directory(OUTPUTS, (OUTPUTS, REPORTS, BUILDS))
        elif choice == "2":
            browse_directory(REPORTS, (OUTPUTS, REPORTS, BUILDS))
        elif choice == "3":
            browse_directory(BUILDS, (OUTPUTS, REPORTS, BUILDS))
        else:
            print(YELLOW + "Opção inválida." + RESET)


# ------------------------------------------------------------------ reconstrução e compilação

def prompt_rename_package(decoded: Path) -> None:
    """Pergunta o novo applicationId, valida e aplica. Usado nos dois fluxos
    (opção 10 isolada e dentro da opção 11, antes de reconstruir)."""
    print(DIM + "O pacote atual aparece no AndroidManifest.xml; isso move pastas smali" + RESET)
    print(DIM + "e troca as referências de classe - é melhor esforço, teste o resultado." + RESET)
    new_name = safe_input("Novo pacote (ex: com.exemplo.app) ou ENTER para pular: ").strip()
    if not new_name:
        return
    if not valid_package_name(new_name):
        print(RED + "Nome inválido. Use letras/números/'_' e pelo menos um ponto, ex: com.exemplo.app" + RESET)
        return
    result = rename_package(decoded, new_name)
    if result["ok"]:
        print(GREEN + result["message"] + RESET)
        if result["directories_moved"] or result["files_updated"]:
            print(f" {result['directories_moved']} pasta(s) de smali movida(s), "
                  f"{result['files_updated']} arquivo(s) atualizado(s).")
        if result.get("warning"):
            print(YELLOW + result["warning"] + RESET)
    else:
        print(RED + result["message"] + RESET)


def quick_edits_menu() -> None:
    decoded = ask_decoded_dir()
    if decoded is None:
        return
    keys = list(QUICK_EDITS)
    print(CYAN + "\nEdições rápidas disponíveis:" + RESET)
    for i, k in enumerate(keys, 1):
        print(f" [{i}] {QUICK_EDITS[k]}")
    choice = safe_input("Números separados por vírgula (ex: 1,3), ou ENTER para pular: ").strip()
    chosen = []
    for part in choice.split(","):
        part = part.strip()
        if part.isdigit() and 1 <= int(part) <= len(keys):
            chosen.append(keys[int(part) - 1])
    if chosen:
        result = apply_quick_edits(decoded, chosen)
        if result["ok"]:
            print(GREEN + "Aplicado: " + ", ".join(result["applied"]) + RESET)
        else:
            print(RED + result["message"] + RESET)
    elif choice:
        print(YELLOW + "Nenhuma edição válida selecionada." + RESET)

    if safe_input("Renomear o pacote (applicationId) também? (s/N): ").strip().lower() == "s":
        prompt_rename_package(decoded)
    print("Quando terminar de editar, use a opção 11 para reconstruir, alinhar e assinar.")


def rebuild_and_sign() -> None:
    print(CYAN + "\nReconstrução e compilação automatizada" + RESET)
    print(YELLOW + "Use só em APKs seus ou que você tem autorização para modificar." + RESET)
    print(DIM + "Reassinar troca a identidade do desenvolvedor original; o resultado" + RESET)
    print(DIM + "não substitui o app da loja nem deve ser redistribuído sem permissão." + RESET)
    decoded = ask_decoded_dir()
    if decoded is None:
        return
    if not (decoded / "AndroidManifest.xml").is_file() or not (decoded / "apktool.yml").is_file():
        print(YELLOW + "Essa pasta não parece ser uma saída do Apktool (opção 5). Confira o caminho." + RESET)
        if safe_input("Continuar mesmo assim? (s/N): ").strip().lower() != "s":
            return

    edits: list[str] = []
    if safe_input("Aplicar alguma edição rápida antes de compilar? (s/N): ").strip().lower() == "s":
        keys = list(QUICK_EDITS)
        for i, k in enumerate(keys, 1):
            print(f" [{i}] {QUICK_EDITS[k]}")
        choice = safe_input("Números separados por vírgula: ").strip()
        for part in choice.split(","):
            part = part.strip()
            if part.isdigit() and 1 <= int(part) <= len(keys):
                edits.append(keys[int(part) - 1])

    if safe_input("Renomear o pacote (applicationId) antes de compilar? (s/N): ").strip().lower() == "s":
        prompt_rename_package(decoded)

    name = decoded.name.replace("_apktool", "") or "app"
    work_dir = BUILDS / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def say(msg: str) -> None:
        print(CYAN + " · " + msg + RESET)

    result = build_pipeline(decoded, work_dir, KEYSTORE, DEFAULT_ALIAS, DEFAULT_STOREPASS, edits, say)
    steps = result["steps"]
    for name_step, label in (("quick_edits", "Edições"), ("rebuild", "Reconstrução (apktool b)"),
                             ("align", "Alinhamento (zipalign)"), ("keystore", "Chave de assinatura"),
                             ("sign", "Assinatura"), ("verify", "Verificação")):
        step = steps.get(name_step)
        if not step:
            continue
        ok = step.get("ok")
        mark = GREEN + "OK" + RESET if ok else (YELLOW + "pulado" + RESET if step.get("skipped") else RED + "falhou" + RESET)
        print(f" [{mark}] {label}")
        if step.get("message"):
            print("      " + step["message"])
        if step.get("warning"):
            print(YELLOW + "      " + step["warning"] + RESET)
        if not ok and step.get("stderr"):
            print(DIM + "      " + step["stderr"][-400:] + RESET)

    if result["ok"]:
        final = Path(result["final_apk"])
        print(GREEN + f"\nAPK pronto: {final}" + RESET)
        print("SHA256:", steps.get("sha256", "?"))
        # Facilita achar no celular: também copiamos pra Downloads, se liberado.
        downloads = Path.home() / "storage" / "downloads"
        if downloads.is_dir():
            dest = downloads / "ReaDroid" / final.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(final, dest)
            print(GREEN + f"Cópia em: {dest}" + RESET)
        if shutil.which("termux-open") and safe_input("Abrir o instalador do Android agora? (s/N): ").strip().lower() == "s":
            subprocess.run([shutil.which("termux-open"), str(final)], check=False)
    else:
        print(RED + "\nA reconstrução não terminou. Veja os passos acima." + RESET)


def keystore_menu() -> None:
    print(CYAN + "\nChave de assinatura" + RESET)
    if KEYSTORE.is_file():
        print(f" Em uso: {KEYSTORE}")
        print(f" Alias padrão: {DEFAULT_ALIAS}")
        print(" (a senha padrão é 'readroid123' - troque editando builder.py se quiser outra)")
        if safe_input("Apagar esta chave e gerar outra no próximo build? (s/N): ").strip().lower() == "s":
            KEYSTORE.unlink()
            print(GREEN + "Chave removida. Uma nova será criada na próxima reconstrução." + RESET)
    else:
        print(" Nenhuma chave gerada ainda. Ela é criada automaticamente na primeira")
        print(" reconstrução (opção 11) e reaproveitada nas seguintes.")
        print(f" Local: {KEYSTORE}")
    if shutil.which("apksigner") and KEYSTORE.is_file():
        print(DIM + " Dica: use a opção 11 para gerar um APK e depois 'readroid verify' nele." + RESET)


# ------------------------------------------------------------------ menu

MENU = [
    ("1", "Inspecionar estrutura do APK"),
    ("2", "Analisar manifesto e permissões"),
    ("3", "Buscar URLs, domínios e IPs"),
    ("4", "Decompilar para Java com JADX"),
    ("5", "Extrair smali e recursos com Apktool"),
    ("6", "Verificar dependências"),
    ("7", "Abrir pasta de relatórios"),
    ("8", "Abrir pasta de resultados"),
    ("9", "Explorar e abrir arquivos gerados"),
    ("10", "Edições rápidas e renomear pacote (pré-build)"),
    ("11", "Reconstruir, alinhar e assinar APK"),
    ("12", "Gerenciar chave de assinatura"),
]


def ai_available() -> bool:
    """A IA é um módulo à parte: se readroid/ai.py for apagado, o menu 13 some e nada quebra."""
    try:
        from . import ai  # noqa: F401
        return True
    except ImportError:
        return False


def ai_assistant() -> None:
    import sys
    from . import ai
    ai.run_menu(sys.modules[__name__])


def print_menu() -> None:
    for key, label in MENU:
        print(f" [{key}] {label}")
    if ai_available():
        print(f" [13] Assistente IA {DIM}(opcional){RESET}")
    print(" [0] Sair")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    BUILDS.mkdir(parents=True, exist_ok=True)
    while True:
        banner()
        print_menu()
        choice = safe_input(CYAN + "\nReaDroid > " + RESET).strip()

        if choice == "1":
            run_action("Inspeção APK", inspect_apk)
        elif choice == "2":
            run_action("Manifesto", lambda apk: analyze_manifest(apk, OUTPUTS / (apk.stem + "_manifest_work")))
        elif choice == "3":
            run_action("Scanner strings", scan_strings)
        elif choice == "4":
            apk = ask_apk()
            if apk:
                target = OUTPUTS / (apk.stem + "_jadx")
                print(YELLOW + "A decompilação pode demorar e consumir RAM. Use APKs confiáveis e que você tem autorização para analisar." + RESET)
                if safe_input(f"Salvar em {target}? [s/N]: ").strip().lower() == "s":
                    result = decompile_with_jadx(apk, target)
                    print((GREEN if result.get("ok") else YELLOW) + result.get("message", "Processo concluído.") + RESET)
                    print("Destino:", result.get("output_dir", target))
                    if result.get("stderr"):
                        print(sanitize(result["stderr"][-2500:]))
                    save_and_show(result, "jadx", apk)
        elif choice == "5":
            apk = ask_apk()
            if apk:
                target = OUTPUTS / (apk.stem + "_apktool")
                print(YELLOW + "A extração pode levar alguns minutos. O APK original não será alterado." + RESET)
                if safe_input(f"Salvar em {target}? [s/N]: ").strip().lower() == "s":
                    result = extract_smali_with_apktool(apk, target)
                    print((GREEN if result.get("ok") else YELLOW) + result.get("message", "Processo concluído.") + RESET)
                    print("Destino:", result.get("output_dir", target))
                    if result.get("stderr"):
                        print(sanitize(result["stderr"][-2500:]))
                    save_and_show(result, "apktool", apk)
                    if result.get("ok"):
                        print(DIM + "Edite os arquivos dentro dessa pasta e depois use as opções 10/11." + RESET)
        elif choice == "6":
            dependencies()
        elif choice == "7":
            open_folder(REPORTS)
        elif choice == "8":
            open_folder(OUTPUTS)
        elif choice == "9":
            browse_generated_files()
        elif choice == "10":
            quick_edits_menu()
        elif choice == "11":
            rebuild_and_sign()
        elif choice == "12":
            keystore_menu()
        elif choice == "13" and ai_available():
            ai_assistant()
        elif choice in ("0", ""):
            print(GREEN + "Até a próxima. ReaDroid encerrado." + RESET)
            break
        else:
            print(YELLOW + "Opção não reconhecida." + RESET)
        if choice != "0":
            pause()

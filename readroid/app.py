"""Interface de terminal do ReaDroid. Mantemos o menu simples para telas pequenas."""
from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import __version__
from .analyzer import (analyze_manifest, decompile_with_jadx, extract_smali_with_apktool,
                       inspect_apk, scan_strings, write_report)

# Usa a pasta desta cópia do projeto, não uma pasta fixa em ~/ReaDroid.
# Isso evita salvar os resultados em outro lugar quando o projeto foi extraído
# em Downloads ou executado a partir de um clone do GitHub.
BASE = Path(__file__).resolve().parents[1]
REPORTS = BASE / "reports"
OUTPUTS = BASE / "output"
GREEN, CYAN, YELLOW, RED, DIM, RESET = "\033[92m", "\033[96m", "\033[93m", "\033[91m", "\033[2m", "\033[0m"


def clear() -> None:
    # Se o terminal não aceitar ANSI, o programa ainda funciona; só perde as cores.
    os.system("clear" if os.environ.get("TERM") else "")


def banner() -> None:
    clear()
    print(GREEN + r"""
 ____       _ ____            _     _
|  _ \ ___ / |  _ \ _ __ ___ (_) __| |
| |_) / _ \ | | | | '__/ _ \| |/ _` |
|  _ <  __/ | |_| | | | (_) | | (_| |
|_| \_\___|_|____/|_|  \___/|_|\__,_|
""" + RESET)
    print(CYAN + " Android Reverse Engineering Toolkit " + RESET + f"v{__version__}")
    print("Sem IA  |  Sem root  |  Análise estática local")
    # Marca d'água intencionalmente discreta, conforme pedido do projeto.
    print(DIM + "OffensiveTec" + RESET)
    print(GREEN + "─" * 43 + RESET)


def pause() -> None:
    input("\nENTER para voltar ao menu...")


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
                if item.is_file() and item.suffix.lower() == ".apk" and str(item) not in seen:
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
                print(f" [{index}] {item.name} ({size_mb:.1f} MB)")
            except OSError:
                print(f" [{index}] {item.name}")
        print(" [P] Informar outro caminho")
        choice = input("Escolha um APK: ").strip()
        if choice.lower() != "p":
            try:
                selected = candidates[int(choice) - 1]
                return selected
            except (ValueError, IndexError):
                print(YELLOW + "Seleção não reconhecida; informe o caminho manualmente." + RESET)
    raw = input("Caminho completo do APK: ").strip().strip('"').strip("'")
    if not raw:
        print(YELLOW + "Nenhum arquivo informado." + RESET)
        return None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists() or not path.is_file():
        print(RED + "Arquivo não encontrado. Dica: execute termux-setup-storage e use ~/storage/shared/Download/app.apk" + RESET)
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
        if "permissions" in report:
            print(f"Permissões encontradas: {len(report.get('permissions', []))}")
            for item in report.get("permissions", [])[:25]:
                print(" •", item.get("name"))
            if not report.get("decoded"):
                print(YELLOW + "Manifesto não decodificado. Veja a mensagem no relatório." + RESET)
        if "urls" in report:
            print(f"URLs: {len(report['urls'])} | Domínios: {len(report['domains'])} | IPs candidatos: {len(report['ipv4_candidates'])}")
        if "zip_entry_count" in report:
            print(f"Arquivos: {report['zip_entry_count']} | DEX: {len(report['dex_files'])} | Bibliotecas nativas: {len(report['native_libraries'])}")
    except Exception as exc:  # O menu não deve fechar por um erro inesperado de um arquivo.
        print(RED + f"A análise falhou: {exc}" + RESET)
        print("O arquivo original não foi modificado.")


def dependencies() -> None:
    print(CYAN + "\nVERIFICAÇÃO DE DEPENDÊNCIAS" + RESET)
    for name in ("python", "java", "jadx", "apktool", "aapt2", "unzip", "git"):
        path = shutil.which(name)
        print(f"[{GREEN + 'OK' + RESET if path else YELLOW + '--' + RESET}] {name}: {path or 'não encontrado'}")
    if shutil.which("java"):
        try:
            result = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=5)
            print((result.stderr or result.stdout).splitlines()[0])
        except (OSError, subprocess.TimeoutExpired):
            print("Java encontrado, mas não foi possível consultar a versão.")
    if shutil.which("jadx"):
        try:
            result = subprocess.run(["jadx", "--version"], capture_output=True, text=True, timeout=8)
            print("JADX:", (result.stdout or result.stderr).strip().splitlines()[0])
        except (OSError, subprocess.TimeoutExpired, IndexError):
            print("JADX localizado; versão não confirmada.")


def open_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    print("Pasta:", path)
    print("Conteúdo:")
    items = list(path.iterdir())
    if not items:
        print(" (vazia por enquanto)")
    for item in sorted(items, key=lambda p: p.name.lower())[:60]:
        print(" [DIR]" if item.is_dir() else " [FILE]", item.name)


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
        if shutil.which("less"):
            subprocess.run([shutil.which("less"), "-R", str(path)], check=False)
            return
        content = path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        page_size = 120
        for start in range(0, max(1, len(lines)), page_size):
            print("\n".join(lines[start:start + page_size]))
            if start + page_size < len(lines):
                answer = input("\nENTER para próxima página, q para sair: ").strip().lower()
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
            print(f" [{index}] {kind}{item.name}{size}")
        print(" [..] Voltar uma pasta | [0] Sair do explorador")
        choice = input("Abrir > ").strip().lower()
        if choice in {"0", "q", "sair"}:
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
            input("\nENTER para voltar ao explorador...")


def browse_generated_files() -> None:
    """Permite localizar e abrir saídas do JADX/Apktool e relatórios JSON."""
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    while True:
        print(CYAN + "\nARQUIVOS GERADOS" + RESET)
        print(" [1] Código decompilado e recursos (output)")
        print(" [2] Relatórios JSON (reports)")
        print(" [0] Voltar ao menu principal")
        choice = input("Explorar > ").strip()
        if choice == "0":
            return
        if choice == "1":
            browse_directory(OUTPUTS, (OUTPUTS, REPORTS))
        elif choice == "2":
            browse_directory(REPORTS, (OUTPUTS, REPORTS))
        else:
            print(YELLOW + "Opção inválida." + RESET)


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    while True:
        banner()
        print(" [1] Inspecionar estrutura do APK")
        print(" [2] Analisar manifesto e permissões")
        print(" [3] Buscar URLs, domínios e IPs")
        print(" [4] Decompilar para Java com JADX")
        print(" [5] Extrair smali e recursos com Apktool")
        print(" [6] Verificar dependências")
        print(" [7] Abrir pasta de relatórios")
        print(" [8] Abrir pasta de resultados")
        print(" [9] Explorar e abrir arquivos gerados")
        print(" [0] Sair")
        choice = input(CYAN + "\nReaDroid > " + RESET).strip()

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
                if input(f"Salvar em {target}? [s/N]: ").strip().lower() == "s":
                    result = decompile_with_jadx(apk, target)
                    print(GREEN if result.get("ok") else YELLOW, result.get("message", "Processo concluído."), RESET)
                    print("Destino:", result.get("output_dir", target))
                    if result.get("stderr"):
                        print(result["stderr"][-2500:])
                    save_and_show(result, "jadx", apk)
        elif choice == "5":
            apk = ask_apk()
            if apk:
                target = OUTPUTS / (apk.stem + "_apktool")
                print(YELLOW + "A extração pode levar alguns minutos. O APK original não será alterado." + RESET)
                if input(f"Salvar em {target}? [s/N]: ").strip().lower() == "s":
                    result = extract_smali_with_apktool(apk, target)
                    print(GREEN if result.get("ok") else YELLOW, result.get("message", "Processo concluído."), RESET)
                    print("Destino:", result.get("output_dir", target))
                    if result.get("stderr"):
                        print(result["stderr"][-2500:])
                    save_and_show(result, "apktool", apk)
        elif choice == "6":
            dependencies()
        elif choice == "7":
            open_folder(REPORTS)
        elif choice == "8":
            open_folder(OUTPUTS)
        elif choice == "9":
            browse_generated_files()
        elif choice == "0":
            print(GREEN + "Até a próxima. ReaDroid encerrado." + RESET)
            break
        else:
            print(YELLOW + "Opção não reconhecida." + RESET)
        if choice != "0":
            pause()

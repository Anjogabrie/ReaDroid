"""Assistente de IA OPCIONAL do ReaDroid (OpenRouter + opencode).

Regras deste módulo:
- O núcleo do ReaDroid nunca depende dele: o app.py só o importa quando você abre o menu 13,
  e se este arquivo for apagado o menu 13 simplesmente some.
- Usa só a biblioteca padrão. A chave de API fica FORA do projeto (~/.readroid), com permissão
  600, para nunca ir parar num commit do GitHub.
- O opencode é sempre iniciado dentro de uma pasta de trabalho explícita, com a config e a
  chave passadas por variável de ambiente. Assim ele não depende de qual pasta você estava
  quando digitou o comando (era isso que fazia a IA "abrir mas não responder" fora de
  ~/projetos/opencode-teste).
"""
from __future__ import annotations

import getpass
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

HOME_DIR = Path(os.environ.get("READROID_HOME") or (Path.home() / ".readroid"))
KEY_FILE = HOME_DIR / "openrouter.key"
OC_CONFIG = HOME_DIR / "opencode.json"
SETTINGS_FILE = HOME_DIR / "ai.json"
WORKSPACE = HOME_DIR / "workspace"

OPENROUTER_API = "https://openrouter.ai/api/v1"
# IDs gratuitos vistos no catálogo do OpenRouter em out/2026. Modelos :free saem do ar com
# frequência (o nano-30b deixou de ser gratuito), por isso o ReaDroid também troca sozinho.
DEFAULT_MODEL = "nvidia/nemotron-3.5-lightning:free"
PREFERRED_MODELS = (
    "nvidia/nemotron-3.5-lightning:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
)

_CTRL_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_KEY_RE = re.compile(r"^[A-Za-z0-9_\-]{20,200}$")
_BAD_MODEL_WORDS = ("embed", "rerank", "guard", "safety", "-vl", "omni", "parse")
_UNAVAIL_RE = re.compile(r"unavailable for free|slug instead|no endpoints found|model.{0,30}(not found|not available)",
                         re.IGNORECASE)


def _clean(text: Any) -> str:
    """Remove escapes ANSI/controle: saída de IA e de rede é conteúdo não confiável."""
    return _CTRL_RE.sub("", str(text))


# ------------------------------------------------------------------ chave e configuração

def valid_key_format(key: str) -> bool:
    return bool(_KEY_RE.match(key))


def save_key(key: str) -> None:
    """Grava a chave com permissão 600 (só você lê)."""
    HOME_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(HOME_DIR, 0o700)
    except OSError:
        pass
    fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(key.strip() + "\n")
    try:
        os.chmod(KEY_FILE, 0o600)
    except OSError:
        pass


def load_key() -> str | None:
    env = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if env:
        return env
    try:
        value = KEY_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def load_model() -> str:
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        model = str(data.get("model", "")).strip()
        if model:
            return model
    except (OSError, ValueError):
        pass
    return DEFAULT_MODEL


def save_model(model: str) -> None:
    HOME_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps({"model": model}, indent=2) + "\n", encoding="utf-8")


def build_opencode_config(model: str) -> dict[str, Any]:
    """Config mínima e conservadora do opencode (só chaves documentadas).

    A chave NÃO vai neste arquivo: o provedor OpenRouter do opencode lê OPENROUTER_API_KEY
    do ambiente, e o ReaDroid injeta essa variável ao iniciar o processo."""
    return {
        "$schema": "https://opencode.ai/config.json",
        "model": f"openrouter/{model}",
        "small_model": f"openrouter/{model}",
        "provider": {"openrouter": {"models": {model: {}}}},
    }


def write_opencode_config(model: str) -> Path:
    HOME_DIR.mkdir(parents=True, exist_ok=True)
    OC_CONFIG.write_text(json.dumps(build_opencode_config(model), indent=2) + "\n", encoding="utf-8")
    return OC_CONFIG


def configure(key: str, model: str | None = None) -> dict[str, Any]:
    """Configuração automática: valida o formato, guarda a chave e gera o opencode.json."""
    key = key.strip()
    if not valid_key_format(key):
        return {"ok": False, "message": "Isso não parece uma chave de API (sem espaços, 20+ caracteres)."}
    model = (model or load_model()).strip()
    save_key(key)
    save_model(model)
    path = write_opencode_config(model)
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    return {"ok": True, "model": model, "config": str(path),
            "message": f"Chave salva em {KEY_FILE} (permissão 600) e opencode configurado."}


def disable() -> list[str]:
    """Apaga chave, config e preferências. O restante do ReaDroid não é afetado."""
    removed = []
    for path in (KEY_FILE, OC_CONFIG, SETTINGS_FILE):
        try:
            path.unlink()
            removed.append(str(path))
        except FileNotFoundError:
            continue
        except OSError:
            continue
    return removed


# ------------------------------------------------------------------ opencode

def find_opencode() -> str | None:
    found = shutil.which("opencode")
    if found:
        return found
    candidate = Path.home() / ".opencode" / "bin" / "opencode"
    return str(candidate) if candidate.is_file() else None


def safe_workdir(path: Path) -> tuple[bool, str]:
    """Recusa pastas enormes (HOME, raiz). Abrir o opencode na pasta pessoal faz ele
    tratar o Termux inteiro como projeto, e é uma das causas de travar sem responder."""
    resolved = path.resolve()
    if resolved in (Path.home().resolve(), Path("/"), Path("/data/data/com.termux/files")):
        return False, "Escolha a pasta de um APK (output/<app>_apktool), não a pasta pessoal."
    if not resolved.is_dir():
        return False, "Pasta não encontrada."
    return True, ""


def build_env(key: str) -> dict[str, str]:
    env = os.environ.copy()
    env["OPENROUTER_API_KEY"] = key
    env["OPENCODE_CONFIG"] = str(OC_CONFIG)
    return env


def opencode_command(binary: str, model: str, prompt: str | None = None) -> list[str]:
    """Sem prompt: abre a interface interativa. Com prompt: `opencode run` (uma pergunta)."""
    model_ref = f"openrouter/{model}"
    if prompt is None:
        return [binary, "-m", model_ref]
    return [binary, "run", "-m", model_ref, prompt]


def open_interactive(workdir: Path) -> dict[str, Any]:
    key, binary = load_key(), find_opencode()
    if not key:
        return {"ok": False, "message": "IA não configurada. Use a opção de configurar."}
    if not binary:
        return {"ok": False, "message": "opencode não encontrado no PATH."}
    ok, why = safe_workdir(workdir)
    if not ok:
        return {"ok": False, "message": why}
    model = load_model()
    write_opencode_config(model)
    try:
        code = subprocess.run(opencode_command(binary, model), cwd=workdir, env=build_env(key),
                              check=False).returncode
    except OSError as exc:
        return {"ok": False, "message": f"Não foi possível iniciar o opencode: {exc}"}
    return {"ok": True, "message": f"opencode encerrado (código {code})."}


def ask_once(workdir: Path, prompt: str, timeout: int = 300, emit=print) -> dict[str, Any]:
    """Faz uma pergunta e imprime a resposta linha a linha, já sanitizada."""
    key, binary = load_key(), find_opencode()
    if not key:
        return {"ok": False, "message": "IA não configurada."}
    if not binary:
        return {"ok": False, "message": "opencode não encontrado no PATH."}
    ok, why = safe_workdir(workdir)
    if not ok:
        return {"ok": False, "message": why}
    model = load_model()
    write_opencode_config(model)
    import threading
    try:
        proc = subprocess.Popen(opencode_command(binary, model, prompt), cwd=workdir, env=build_env(key),
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                errors="replace", stdin=subprocess.DEVNULL)
    except OSError as exc:
        return {"ok": False, "message": f"Não foi possível iniciar o opencode: {exc}"}
    timer = threading.Timer(timeout, proc.kill)
    timer.start()
    lines = 0
    unavailable = False
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            text = _clean(line.rstrip("\n"))
            if _UNAVAIL_RE.search(text):
                unavailable = True
            emit(text)
            lines += 1
        proc.wait()
    except KeyboardInterrupt:
        proc.kill()
        return {"ok": False, "message": "Interrompido."}
    finally:
        timer.cancel()
    if unavailable:
        return {"ok": False, "model_unavailable": True,
                "message": "O modelo escolhido não está mais disponível no plano gratuito."}
    if proc.returncode in (-9, 137):
        return {"ok": False, "message": f"Sem resposta em {timeout}s; processo encerrado."}
    return {"ok": proc.returncode == 0 and lines > 0,
            "message": "Concluído." if proc.returncode == 0 and lines else "O opencode não devolveu resposta."}


# ------------------------------------------------------------------ OpenRouter direto (diagnóstico)

def _request(url: str, key: str | None = None, payload: dict | None = None, timeout: int = 45) -> Any:
    headers = {"Content-Type": "application/json", "User-Agent": "ReaDroid"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310 (URL fixa https)
        return json.loads(response.read().decode("utf-8", errors="replace"))


def explain_http_error(code: int) -> str:
    return {
        401: "Chave recusada pelo OpenRouter (inválida, apagada ou com erro de digitação).",
        402: "Conta sem crédito para este modelo. Escolha um modelo :free.",
        404: "Modelo indisponível no OpenRouter. Use 'trocar modelo' para escolher outro :free.",
        408: "Tempo esgotado no OpenRouter. Tente de novo.",
        429: "Limite do plano gratuito atingido. Espere alguns minutos ou troque de modelo.",
    }.get(code, f"O OpenRouter respondeu com erro HTTP {code}.")


def test_api(key: str, model: str) -> dict[str, Any]:
    """Testa chave + modelo direto na API, sem opencode. Separa 'problema de chave/modelo'
    de 'problema do opencode'."""
    payload = {"model": model, "max_tokens": 64,
               "messages": [{"role": "user", "content": "Responda apenas: OK"}]}
    try:
        data = _request(f"{OPENROUTER_API}/chat/completions", key, payload)
    except urllib.error.HTTPError as exc:
        return {"ok": False, "model_unavailable": exc.code in (400, 404),
                "message": explain_http_error(exc.code)}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "message": f"Sem conexão com o OpenRouter ({_clean(exc)[:80]})."}
    except ValueError:
        return {"ok": False, "message": "Resposta inesperada do OpenRouter."}
    if isinstance(data, dict) and data.get("error"):
        err = data["error"]
        msg = err.get("message") if isinstance(err, dict) else err
        return {"ok": False, "model_unavailable": bool(_UNAVAIL_RE.search(str(msg))),
                "message": _clean(msg)[:200] or "Erro devolvido pelo OpenRouter."}
    return {"ok": True, "message": "Chave e modelo funcionando."}


def pick_free_models(models: list[dict]) -> list[str]:
    """Filtra, do catálogo, modelos de chat Nemotron gratuitos."""
    found = []
    for item in models:
        mid = str(item.get("id", ""))
        low = mid.lower()
        if "nemotron" in low and mid.endswith(":free") and not any(w in low for w in _BAD_MODEL_WORDS):
            found.append(mid)
    rank = {m: i for i, m in enumerate(PREFERRED_MODELS)}
    return sorted(found, key=lambda m: (rank.get(m, len(rank)), m))


def list_free_nemotron() -> list[str]:
    try:
        data = _request(f"{OPENROUTER_API}/models", timeout=20)
        return pick_free_models(data.get("data", []))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, AttributeError):
        return []


def ensure_working_model(key: str, tried: tuple[str, ...] = (), max_tests: int = 4) -> str | None:
    """Procura um modelo Nemotron :free que responda, salva e reescreve a config.
    Só considera IDs terminados em :free: nunca troca para a versão paga sem você saber."""
    candidates = list(PREFERRED_MODELS)
    for mid in list_free_nemotron():
        if mid not in candidates:
            candidates.append(mid)
    skip = set(tried) | {load_model()}
    tests = 0
    for mid in candidates:
        if mid in skip or tests >= max_tests:
            continue
        tests += 1
        if test_api(key, mid)["ok"]:
            save_model(mid)
            write_opencode_config(mid)
            return mid
    return None


# ------------------------------------------------------------------ menu

PRIVACY = ("Modelos gratuitos podem registrar os prompts. Tudo o que a IA ler (código, strings,\n"
           "manifesto) é enviado pela internet. Use só em APK seu ou autorizado.")

PROMPT_SUMMARY = ("Você está numa pasta de um APK decodificado (apktool ou jadx). Leia o "
                  "AndroidManifest.xml e a estrutura de pastas e faça um resumo curto em português: "
                  "o que o app faz, permissões relevantes, componentes expostos e pontos que merecem "
                  "revisão manual. Não modifique nenhum arquivo.")
PROMPT_BUILD = ("Esta pasta é um APK decodificado pelo apktool e a reconstrução falhou com o erro abaixo. "
                "Explique a causa provável, aponte o arquivo e a linha e sugira a correção mínima. "
                "Não modifique nenhum arquivo, só explique.\n\nERRO:\n")


def ask_with_fallback(ui, folder: Path, prompt: str) -> dict[str, Any]:
    """ask_once; se o modelo gratuito saiu do ar, troca por outro :free e tenta uma vez de novo."""
    res = ask_once(folder, prompt, emit=print)
    if res.get("model_unavailable"):
        key = load_key()
        print(ui.YELLOW + "Modelo gratuito indisponível. Procurando outro…" + ui.RESET)
        found = ensure_working_model(key, (load_model(),)) if key else None
        if found:
            print(ui.GREEN + f"Modelo trocado para openrouter/{found}. Tentando de novo…" + ui.RESET)
            res = ask_once(folder, prompt, emit=print)
        else:
            res["message"] += " Use [8] Trocar modelo para escolher outro."
    return res


def _choose_dir(ui) -> Path | None:
    outputs: Path = ui.OUTPUTS
    outputs.mkdir(parents=True, exist_ok=True)
    cands = sorted((p for p in outputs.iterdir()
                    if p.is_dir() and (p.name.endswith("_apktool") or p.name.endswith("_jadx"))),
                   key=lambda p: p.stat().st_mtime, reverse=True)[:15]
    if cands:
        print(ui.CYAN + "Pastas disponíveis:" + ui.RESET)
        for i, item in enumerate(cands, 1):
            print(f" [{i}] {ui.sanitize(item.name)}")
        print(" [P] Informar outro caminho")
        choice = ui.safe_input("Escolha a pasta: ").strip()
        if choice.lower() != "p":
            try:
                return cands[int(choice) - 1]
            except (ValueError, IndexError):
                print(ui.YELLOW + "Seleção não reconhecida." + ui.RESET)
    raw = ui.safe_input("Caminho da pasta do APK decodificado: ").strip().strip('"').strip("'")
    if not raw:
        return None
    path = Path(raw).expanduser()
    return path if path.is_dir() else None


def _paste_key(ui) -> str:
    print(ui.DIM + "Cole a chave do OpenRouter (a colagem não aparece na tela) e dê ENTER." + ui.RESET)
    try:
        return getpass.getpass("API key: ").strip()
    except (EOFError, KeyboardInterrupt, OSError):
        return ui.safe_input("API key: ").strip()


def _setup(ui) -> bool:
    key = _paste_key(ui)
    if not key:
        print(ui.YELLOW + "Nada informado." + ui.RESET)
        return False
    result = configure(key)
    if not result["ok"]:
        print(ui.RED + result["message"] + ui.RESET)
        return False
    print(ui.GREEN + result["message"] + ui.RESET)
    print(f" Modelo: openrouter/{result['model']}")
    return _run_checks(ui)


def _run_checks(ui) -> bool:
    key, model = load_key(), load_model()
    if not key:
        print(ui.YELLOW + "Sem chave configurada." + ui.RESET)
        return False
    print(ui.CYAN + "\nTestando…" + ui.RESET)
    api = test_api(key, model)
    if not api["ok"] and api.get("model_unavailable"):
        print(ui.YELLOW + f" Modelo {model} indisponível. Procurando outro gratuito…" + ui.RESET)
        found = ensure_working_model(key, (model,))
        if found:
            model = found
            api = {"ok": True, "message": f"Chave e modelo funcionando (trocado para {found})."}
    print(f" [{ui.GREEN + 'OK' + ui.RESET if api['ok'] else ui.RED + 'falhou' + ui.RESET}] "
          f"OpenRouter direto: {api['message']}")
    binary = find_opencode()
    print(f" [{ui.GREEN + 'OK' + ui.RESET if binary else ui.YELLOW + '--' + ui.RESET}] "
          f"opencode: {binary or 'não encontrado (instale o opencode para usar a IA)'}")
    if api["ok"] and binary:
        WORKSPACE.mkdir(parents=True, exist_ok=True)
        write_opencode_config(model)
        print(ui.DIM + " Testando o opencode numa pasta neutra (até 2 min)…" + ui.RESET)
        out: list[str] = []
        res = ask_once(WORKSPACE, "Responda apenas: OK", timeout=120, emit=out.append)
        print(f" [{ui.GREEN + 'OK' + ui.RESET if res['ok'] else ui.RED + 'falhou' + ui.RESET}] "
              f"opencode: {res['message']}")
        if out:
            print(ui.DIM + "   " + " | ".join(out)[-160:] + ui.RESET)
        return bool(res["ok"])
    return bool(api["ok"])


def _change_model(ui) -> None:
    print(ui.DIM + "Buscando modelos Nemotron gratuitos…" + ui.RESET)
    models = list_free_nemotron()
    if not models:
        print(ui.YELLOW + "Não consegui listar. Você pode digitar o ID manualmente." + ui.RESET)
    for i, mid in enumerate(models[:12], 1):
        print(f" [{i}] {ui.sanitize(mid)}")
    raw = ui.safe_input("Número, ID completo, ou ENTER para cancelar: ").strip()
    if not raw:
        return
    chosen = models[int(raw) - 1] if raw.isdigit() and 1 <= int(raw) <= len(models) else raw
    if not re.match(r"^[\w.\-]+/[\w.\-:]+$", chosen):
        print(ui.RED + "ID inválido. Formato: fornecedor/modelo:free" + ui.RESET)
        return
    save_model(chosen)
    write_opencode_config(chosen)
    print(ui.GREEN + f"Modelo definido: openrouter/{chosen}" + ui.RESET)


# ------------------------------------------------------------------ relatórios e ciclo editar -> reconstruir

MAX_ROUNDS = 3
PROMPT_CROSS = ("Abaixo está o resultado da análise estática do ReaDroid para este APK (JSON resumido). "
                "Para cada URL, domínio, IP e permissão sensível, procure no código desta pasta onde é usado "
                "e avalie o risco. Responda em português, de forma curta e organizada. "
                "Não modifique nenhum arquivo.\n\nRELATÓRIOS:\n")
EDIT_RULES = ("Regras: edite SOMENTE arquivos dentro desta pasta; não altere apktool.yml; faça a menor "
              "mudança possível; não rode comandos de build (o ReaDroid reconstrói depois); ao final, liste "
              "os arquivos que alterou.\n\n")


def _shrink(obj: Any, max_items: int = 40, max_str: int = 200) -> Any:
    """Reduz um JSON de relatório para caber num prompt (listas e textos longos cortados)."""
    if isinstance(obj, dict):
        return {k: _shrink(v, max_items, max_str) for k, v in obj.items()}
    if isinstance(obj, list):
        out = [_shrink(v, max_items, max_str) for v in obj[:max_items]]
        if len(obj) > max_items:
            out.append(f"... (+{len(obj) - max_items} itens omitidos)")
        return out
    if isinstance(obj, str) and len(obj) > max_str:
        return obj[:max_str] + "..."
    return obj


def find_reports(reports_dir: Path, decoded: Path) -> list[Path]:
    """Relatório mais recente de cada tipo para o APK desta pasta (nome: <apk>_<tipo>_<data>.json)."""
    stem = re.sub(r"_(apktool|jadx)$", "", decoded.name)
    latest: dict[str, Path] = {}
    try:
        files = sorted(reports_dir.glob(f"{stem}_*.json"), key=lambda p: p.stat().st_mtime)
    except OSError:
        return []
    for path in files:
        kind = path.name[len(stem) + 1:].rsplit("_", 2)[0]
        latest[kind] = path  # os mais novos vêm por último e sobrescrevem
    return list(latest.values())


def build_report_context(reports_dir: Path, decoded: Path, limit: int = 6000) -> str:
    chunks = []
    for path in find_reports(reports_dir, decoded):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        chunks.append(f"## {path.name}\n" + json.dumps(_shrink(data), ensure_ascii=False))
    return "\n\n".join(chunks)[:limit]


def snapshot(root: Path) -> dict[str, tuple[int, int]]:
    snap: dict[str, tuple[int, int]] = {}
    for item in root.rglob("*"):
        try:
            if item.is_file():
                st = item.stat()
                snap[str(item.relative_to(root))] = (st.st_size, st.st_mtime_ns)
        except OSError:
            continue
    return snap


def diff_snapshots(before: dict, after: dict) -> dict[str, list[str]]:
    return {"changed": sorted(k for k in after if k in before and before[k] != after[k]),
            "added": sorted(k for k in after if k not in before),
            "removed": sorted(k for k in before if k not in after)}


def build_error_text(result: dict[str, Any]) -> str:
    steps = result.get("steps", {})
    for name in ("quick_edits", "rebuild", "align", "keystore", "sign", "verify"):
        step = steps.get(name)
        if step and not step.get("ok") and not step.get("skipped"):
            return (f"Etapa: {name}\n{step.get('message', '')}\n"
                    f"{str(step.get('stderr', ''))[-3000:]}\n{str(step.get('stdout', ''))[-1000:]}").strip()
    return str(result.get("message", "Falha desconhecida na reconstrução."))


def fix_loop(decoded: Path, instruction: str, build_fn, ask_fn, confirm_fn, say,
             max_rounds: int = MAX_ROUNDS) -> dict[str, Any]:
    """Ciclo: (IA edita) -> reconstrói -> se falhar, devolve o erro à IA -> reconstrói de novo.

    build_fn() -> resultado do build_pipeline; ask_fn(prompt) -> {"ok":..,"message":..};
    confirm_fn(texto) -> bool; say(texto) imprime. Tudo injetado para ser testável."""
    def report_changes(before):
        d = diff_snapshots(before, snapshot(decoded))
        n = sum(len(v) for v in d.values())
        say(f"Arquivos mexidos pela IA: {n} (alterados {len(d['changed'])}, novos {len(d['added'])}, "
            f"removidos {len(d['removed'])})")
        for name in (d["changed"] + d["added"] + d["removed"])[:15]:
            say("   " + name)

    if instruction:
        before = snapshot(decoded)
        res = ask_fn(EDIT_RULES + f"Pasta: {decoded}\nTarefa: {instruction}")
        if not res.get("ok"):
            return {"ok": False, "rounds": 0, "message": res.get("message", "A IA não respondeu.")}
        report_changes(before)
    last: dict[str, Any] = {}
    for rnd in range(1, max_rounds + 1):
        say(f"Reconstruindo (tentativa {rnd}/{max_rounds})…")
        last = build_fn()
        if last.get("ok"):
            return {"ok": True, "rounds": rnd, "result": last, "message": "APK reconstruído."}
        error = build_error_text(last)
        say("Falhou:\n" + error[-600:])
        if rnd == max_rounds or not confirm_fn("Pedir para a IA corrigir e tentar de novo?"):
            break
        before = snapshot(decoded)
        res = ask_fn(EDIT_RULES + f"Pasta: {decoded}\nA reconstrução falhou com este erro. Corrija a causa:\n{error}")
        if not res.get("ok"):
            return {"ok": False, "rounds": rnd, "result": last, "message": res.get("message", "A IA não respondeu.")}
        report_changes(before)
    return {"ok": False, "rounds": rnd if last else 0, "result": last, "message": "Não foi possível reconstruir."}


def _print_build(ui, result: dict[str, Any]) -> None:
    for name, label in (("quick_edits", "Edições"), ("rebuild", "Reconstrução"), ("align", "Alinhamento"),
                        ("keystore", "Chave"), ("sign", "Assinatura"), ("verify", "Verificação")):
        step = result.get("steps", {}).get(name)
        if step:
            mark = (ui.GREEN + "OK" if step.get("ok") else ui.YELLOW + "pulado" if step.get("skipped")
                    else ui.RED + "falhou") + ui.RESET
            print(f" [{mark}] {label}")


def _backup(ui, decoded: Path) -> Path | None:
    dest = ui.BUILDS / f"_backup_{decoded.name}_{__import__('datetime').datetime.now():%Y%m%d_%H%M%S}"
    try:
        shutil.copytree(decoded, dest)
        return dest
    except (OSError, shutil.Error):
        return None


def _edit_and_rebuild(ui, decoded: Path) -> None:
    from . import builder
    from datetime import datetime
    if not (decoded / "apktool.yml").is_file():
        print(ui.YELLOW + "Essa pasta não é uma saída do Apktool (opção 5 do menu principal)." + ui.RESET)
        return
    print(ui.YELLOW + "Use só em APK seu ou que você tem autorização para modificar." + ui.RESET)
    instruction = ui.safe_input("O que a IA deve fazer? (ENTER = só reconstruir e corrigir erros): ").strip()
    print(f"A IA vai editar arquivos em {decoded}. Será feito um backup antes.")
    if ui.safe_input("Continuar? (s/N): ").strip().lower() != "s":
        return
    backup = _backup(ui, decoded)
    if backup is None:
        print(ui.YELLOW + "Não consegui criar o backup (espaço?)." + ui.RESET)
        if ui.safe_input("Continuar sem backup? (s/N): ").strip().lower() != "s":
            return
    else:
        print(ui.GREEN + f"Backup: {backup}" + ui.RESET)

    def build_fn():
        name = decoded.name.replace("_apktool", "") or "app"
        work = ui.BUILDS / f"{name}_{datetime.now():%Y%m%d_%H%M%S}"
        result = builder.build_pipeline(decoded, work, ui.KEYSTORE, builder.DEFAULT_ALIAS,
                                        builder.DEFAULT_STOREPASS, [], lambda m: print(ui.CYAN + " · " + m + ui.RESET))
        _print_build(ui, result)
        return result

    out = fix_loop(decoded, instruction, build_fn, lambda prompt: ask_with_fallback(ui, decoded, prompt),
                   lambda q: ui.safe_input(q + " (s/N): ").strip().lower() == "s", print)
    if out["ok"]:
        print(ui.GREEN + f"\nAPK pronto: {out['result'].get('final_apk')}" + ui.RESET)
    else:
        print(ui.RED + "\n" + out["message"] + ui.RESET)
        if backup:
            print(f"Para desfazer as mudanças da IA, restaure o backup: {backup}")


def run_menu(ui) -> None:
    """Menu 13. `ui` é o módulo app (cores, safe_input, sanitize, OUTPUTS, REPORTS, BUILDS, KEYSTORE)."""
    print(ui.CYAN + "\nASSISTENTE DE IA (opcional)" + ui.RESET)
    print(ui.DIM + "O ReaDroid funciona normalmente sem isto. Ignore se não quiser usar IA." + ui.RESET)
    if load_key() is None:
        print("Nenhuma chave configurada ainda.")
        if ui.safe_input("Configurar agora? Basta colar a API key do OpenRouter (s/N): ").strip().lower() == "s":
            _setup(ui)
        return
    consented = False
    while True:
        print(f"\n Modelo: openrouter/{load_model()}")
        print(" [1] Abrir o assistente numa pasta de APK (interativo)")
        print(" [2] Resumir o app")
        print(" [3] Cruzar relatórios do ReaDroid com o código")
        print(" [4] Editar com a IA e reconstruir (corrige erros em ciclo)")
        print(" [5] Explicar um erro de reconstrução")
        print(" [6] Pergunta livre sobre o APK")
        print(" [7] Testar / diagnosticar")
        print(" [8] Trocar modelo")
        print(" [9] Trocar a chave")
        print(" [10] Desativar IA (apaga chave e config)")
        print(" [0] Voltar")
        choice = ui.safe_input("IA > ").strip()
        if choice in ("", "0"):
            return
        if choice in ("1", "2", "3", "4", "5", "6"):
            if not consented:
                print(ui.YELLOW + PRIVACY + ui.RESET)
                if ui.safe_input("Continuar? (s/N): ").strip().lower() != "s":
                    continue
                consented = True
            folder = _choose_dir(ui)
            if folder is None:
                print(ui.YELLOW + "Pasta não encontrada." + ui.RESET)
                continue
            res: dict[str, Any] | None = None
            if choice == "1":
                res = open_interactive(folder)
            elif choice == "2":
                res = ask_with_fallback(ui, folder, PROMPT_SUMMARY)
            elif choice == "3":
                ctx = build_report_context(ui.REPORTS, folder)
                if not ctx:
                    print(ui.YELLOW + "Sem relatórios para este APK. Rode antes as opções 1, 2 e 3 do menu principal." + ui.RESET)
                    continue
                res = ask_with_fallback(ui, folder, PROMPT_CROSS + ctx)
            elif choice == "4":
                _edit_and_rebuild(ui, folder)
            elif choice == "5":
                err = ui.safe_input("Cole o erro (uma linha) ou ENTER para cancelar: ").strip()
                if not err:
                    continue
                res = ask_with_fallback(ui, folder, PROMPT_BUILD + err[:4000])
            else:
                question = ui.safe_input("Sua pergunta: ").strip()
                if not question:
                    continue
                res = ask_with_fallback(ui, folder, question[:4000])
            if res is not None:
                print((ui.GREEN if res["ok"] else ui.YELLOW) + res["message"] + ui.RESET)
        elif choice == "7":
            _run_checks(ui)
        elif choice == "8":
            _change_model(ui)
        elif choice == "9":
            _setup(ui)
        elif choice == "10":
            if ui.safe_input("Apagar chave e configuração da IA? (s/N): ").strip().lower() == "s":
                gone = disable()
                print(ui.GREEN + ("Removido: " + ", ".join(gone) if gone else "Nada para remover.") + ui.RESET)
                return
        else:
            print(ui.YELLOW + "Opção inválida." + ui.RESET)

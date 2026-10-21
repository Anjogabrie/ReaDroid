#!/usr/bin/env bash
# Instalador do ReaDroid para desktop Linux (complementa install.sh, que é do Termux).
# Cobre Debian/Ubuntu, Fedora e Arch. Uso: rodar a partir da raiz do ReaDroid.
# Relacionado: https://github.com/Mcsd7/ReaDroid/issues/5
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

detect_pm() {
  for pm in apt-get dnf pacman; do
    command -v "$pm" >/dev/null 2>&1 && { echo "$pm"; return 0; }
  done
  return 1
}

PM="$(detect_pm || true)"
if [ -z "$PM" ]; then
  echo "Gerenciador de pacotes não detectado (esperava apt-get, dnf ou pacman)." >&2
  echo "Instale manualmente: python3, Java 17+, jadx (opcional), apktool (opcional), aapt (traz zipalign), unzip, git." >&2
  exit 1
fi

echo "ReaDroid - configuração para desktop Linux (gerenciador: $PM)"
echo "Instala a base: Python 3, Java (para jadx/apktool), unzip, git."
echo "Opcionais ficam com você (pacotes da distro): jadx, apktool, aapt (traz zipalign), apksigner."
read -r -p "Instalar/atualizar pacotes com $PM? [s/N] " answer
case "$answer" in
  s|S|sim|SIM)
    case "$PM" in
      apt-get) sudo apt-get update && sudo apt-get install -y python3 default-jre-headless unzip git ;;
      dnf) sudo dnf install -y python3 java-17-openjdk-headless unzip git ;;
      # Arch: -Syu (upgrade completo) em vez de -Sy sozinho, que causa partial upgrade.
      pacman) sudo pacman -Syu --needed --noconfirm python jdk-openjdk unzip git ;;
    esac
    echo "(jadx/apktool/aapt/apksigner: instale pelos pacotes da sua distro ou veja o README original)"
    ;;
  *) echo "Pulando instalação. O menu básico (só Python) já funciona." ;;
esac

mkdir -p "$SCRIPT_DIR/reports" "$SCRIPT_DIR/output" "$SCRIPT_DIR/builds"

echo ""
echo "Verificação (base + opcionais):"
for cmd in python3 java unzip git jadx apktool aapt zipalign apksigner; do
  if command -v "$cmd" >/dev/null 2>&1; then
    case "$cmd" in
      python3) ver=$("$cmd" --version 2>&1) ;;
      java) ver=$(java -version 2>&1 | head -n 1) ;;
      *) ver=$("$cmd" --version 2>/dev/null | head -n 1 || true); [ -n "$ver" ] || ver="presente (sem --version)" ;;
    esac
    echo "  [ok] $cmd — $ver"
  else
    echo "  [--] $cmd ausente (opcional; veja o README para instalar)"
  fi
done

cat <<MSG

Estrutura preparada em: $SCRIPT_DIR
Para iniciar:
  cd "$SCRIPT_DIR"
  python3 readroid.py
MSG

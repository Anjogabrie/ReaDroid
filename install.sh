#!/data/data/com.termux/files/usr/bin/bash
# Instalador opcional: mostra o que será instalado e pede confirmação.
set -eu
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

if [ -z "${PREFIX:-}" ] || [ ! -d "$PREFIX" ]; then
  echo "Este instalador foi feito para Termux. Abra o Termux e tente novamente."
  exit 1
fi

printf '\nReaDroid - configuração inicial\n'
printf 'O núcleo usa apenas a biblioteca padrão do Python.\n'
printf 'JADX e Apktool são opcionais para decompilação/extração avançada.\n\n'
read -r -p 'Instalar/atualizar Python, Java, JADX e Apktool via pkg? [s/N] ' answer
case "$answer" in
  s|S|sim|SIM)
    pkg update
    pkg install python openjdk-21 jadx apktool unzip -y
    ;;
  *)
    echo "Pulando instalação de pacotes. O menu básico ainda pode ser usado."
    ;;
esac

mkdir -p "$SCRIPT_DIR/reports" "$SCRIPT_DIR/output"
cat <<'MSG'

Estrutura preparada na pasta do projeto. Para iniciar, execute:
  cd "$SCRIPT_DIR"
  python readroid.py

Se quiser escolher APKs da pasta compartilhada, execute uma vez:
  termux-setup-storage
E use um caminho como:
  ~/storage/shared/Download/aplicativo.apk
MSG

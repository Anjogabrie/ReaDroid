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
printf 'JADX, Apktool, aapt (zipalign) e apksigner são opcionais, para decompilação,\n'
printf 'extração avançada e para reconstruir/assinar um APK já pronto para instalar.\n\n'
read -r -p 'Instalar/atualizar Python, Java, JADX, Apktool, aapt e apksigner via pkg? [s/N] ' answer
case "$answer" in
  s|S|sim|SIM)
    pkg update
    pkg install python openjdk-21 jadx apktool aapt unzip -y
    # apksigner é opcional por cima do opcional: sem ele, o ReaDroid usa o jarsigner
    # do openjdk (assinatura v1 apenas) para reconstruir e assinar o APK.
    pkg install apksigner -y || echo "apksigner indisponível neste repositório; seguindo sem ele (jarsigner cobre o básico)."
    ;;
  *)
    echo "Pulando instalação de pacotes. O menu básico ainda pode ser usado."
    ;;
esac

mkdir -p "$SCRIPT_DIR/reports" "$SCRIPT_DIR/output" "$SCRIPT_DIR/builds"
cat <<MSG

Estrutura preparada em: $SCRIPT_DIR
Para iniciar, execute:
  cd "$SCRIPT_DIR"
  python readroid.py

Se quiser escolher APKs da pasta compartilhada, execute uma vez:
  termux-setup-storage
E use um caminho como:
  ~/storage/shared/Download/aplicativo.apk

A opção 11 do menu (reconstruir, alinhar e assinar) gera uma chave de
assinatura própria na primeira vez que você usar, em:
  $SCRIPT_DIR/.readroid-keystore.jks
MSG

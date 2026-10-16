# ReaDroid

**Android Reverse Engineering Toolkit** — uma ferramenta de análise estática de APKs para Android 12–16, projetada para rodar no Termux sem root e sem inteligência artificial.

> **OffensiveTec** é uma marca d'água discreta na interface do terminal.

## Recursos

- Inspeção da estrutura ZIP do APK, hashes SHA-256, arquivos DEX e bibliotecas nativas.
- Análise de manifesto e permissões quando o manifesto é XML textual ou quando uma ferramenta externa consegue decodificar o formato binário AXML.
- Busca estática de URLs, domínios e candidatos a endereços IPv4 em arquivos selecionados do APK.
- Integração opcional com JADX para decompilar DEX em código Java aproximado.
- Integração opcional com Apktool para extrair recursos e smali.
- Relatórios JSON locais, sem serviços externos ou telemetria.
- Menu de terminal pensado para telas de celular.
- Explorador interativo para navegar e abrir arquivos Java, Kotlin, Smali, XML, JSON e outros relatórios diretamente pelo menu.
- Resultado de JADX identificado como sucesso, parcial ou falha conforme o código de saída e os arquivos realmente gerados.
- Saídas salvas na pasta da cópia do projeto em uso, evitando confusão com outra pasta `~/ReaDroid`.

## Compatibilidade

O ReaDroid usa Python e biblioteca padrão para seu núcleo. Foi escrito visando Termux ARM64 e Android 12–16, mas não foi possível testar em todos os aparelhos/versões. As ferramentas externas dependem dos pacotes e da arquitetura disponíveis no repositório Termux do usuário.

O JADX requer Java compatível; a documentação upstream informa Java 11 ou posterior. O pacote JADX do Termux normalmente depende do OpenJDK empacotado no Termux. Apktool em Android tem incompatibilidades oficiais conhecidas em algumas configurações, portanto o recurso é opcional e deve ser validado no aparelho.

## Instalação no Termux

Atualize os pacotes:

```bash
pkg update && pkg upgrade
pkg install python openjdk-21 jadx apktool unzip git
```

Se `openjdk-21`, `jadx` ou `apktool` não estiverem disponíveis no repositório configurado, instale os pacotes disponíveis e consulte a documentação oficial/README do Termux. O ReaDroid não baixa binários executáveis de terceiros automaticamente.

Clone o repositório (substitua pela URL do seu repositório depois de criá-lo):

```bash
git clone https://github.com/Mcsd7/ReaDroid.git
cd ReaDroid
python readroid.py
```

Ou, se você já baixou os arquivos, execute `bash install.sh` e depois `python readroid.py`.

Para escolher APKs na pasta Download, habilite o acesso ao armazenamento quando o Termux pedir:

```bash
termux-setup-storage
```

Caminho de exemplo: `~/storage/shared/Download/app.apk`.

## Como usar

1. Abra `python readroid.py`.
2. Selecione a análise no menu.
3. Cole o caminho do APK quando solicitado.
4. Consulte relatórios em `reports/` e arquivos exportados em `output/`, dentro da pasta do projeto que você está executando. Use a opção **9 — Explorar e abrir arquivos gerados** para navegar pelas pastas e abrir os arquivos.

O caminho do APK pode ser absoluto ou relativo ao diretório atual. Para a opção JADX, o programa usa no máximo quatro threads (padrão de duas) para reduzir pressão de memória. APKs grandes podem continuar exigindo muita RAM e armazenamento.

## Limitações importantes

- ReaDroid faz análise estática. Não executa o APK nem monitora seu comportamento em tempo real.
- Manifestos binários AXML precisam de JADX/Apktool ou outra ferramenta compatível para decodificação. Se nenhuma funcionar, o relatório explicará que a análise do manifesto está incompleta.
- JADX não recupera perfeitamente todo o código original; nomes podem estar ofuscados e comentários/nomes originais podem ter sido perdidos.
- URLs, domínios, IPs e permissões são pistas para revisão manual, não provas de malware.
- O scanner tem limites de tamanho para evitar consumo excessivo de memória; alguns arquivos grandes podem ser ignorados ou lidos parcialmente.
- O ReaDroid não modifica nem assina APKs.

## Segurança e uso responsável

Analise aplicativos próprios, de teste ou para os quais você tem autorização. APKs são arquivos não confiáveis; evite executá-los. A ferramenta chama JADX/Apktool com argumentos separados (sem shell) e não envia os APKs para a internet. A saída das ferramentas é salva localmente.

## Testes

Execute:

```bash
python -m unittest discover -s tests -v
```

## Licença

MIT. Consulte `LICENSE`.

## Créditos

ReaDroid é uma interface/automação original que integra ferramentas de terceiros opcionais. JADX e Apktool mantêm seus próprios projetos, licenças e termos; veja os links abaixo.

- JADX: https://github.com/skylot/jadx
- Apktool: https://github.com/iBotPeaches/Apktool
- Termux: https://github.com/termux/termux-app

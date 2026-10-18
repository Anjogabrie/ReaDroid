# Política de segurança

Para relatar uma falha no ReaDroid, abra uma issue sem anexar APKs privados, tokens, chaves ou dados pessoais. Explique o impacto e forneça um exemplo mínimo não sensível.

O ReaDroid é uma ferramenta de análise estática. APKs desconhecidos devem ser tratados como arquivos não confiáveis e não devem ser executados apenas por terem sido analisados pela ferramenta.

## Sobre a reconstrução e assinatura de APKs

A partir da versão 0.3.0 o ReaDroid também reconstrói e assina APKs (apktool + zipalign + apksigner/jarsigner). Use esse recurso apenas em aplicativos seus ou para os quais você tem autorização explícita de modificar:

- Reassinar um APK troca a identidade do desenvolvedor original. O resultado não é uma atualização do app da loja e o Android vai tratá-lo como um aplicativo diferente.
- Redistribuir o APK modificado de outra pessoa sem permissão pode violar a licença e os termos de uso do app original.
- O ReaDroid não contorna proteções de DRM, verificação de licença ou ofuscação; ele só automatiza o fluxo padrão de build do ecossistema Android (o mesmo `apktool`/`zipalign`/`apksigner` documentados pelo próprio Android Open Source Project).

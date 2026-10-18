# Contribuindo com o ReaDroid

Obrigado por ajudar! Para mudanças pequenas, abra uma issue descrevendo o problema antes de enviar um pull request.

- Mantenha o núcleo sem dependências Python externas quando possível.
- Não adicione telemetria nem upload automático de APKs.
- Trate APKs como entrada não confiável e evite executar seu conteúdo.
- Ao imprimir qualquer string vinda de dentro de um APK (nomes, strings, saída de ferramentas),
  use `app.sanitize()` antes - isso remove sequências de escape ANSI e caracteres de controle.
- Prefira comentários claros em português e nomes de função que expliquem a intenção.
- Rode `python -m unittest discover -s tests -v` antes de enviar alterações.
- Informe aparelho, versão do Android, arquitetura, versão do Termux e ferramentas externas ao relatar problemas.

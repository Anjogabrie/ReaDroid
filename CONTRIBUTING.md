# Contributing to ReaDroid

Thank you for contributing! For small changes, please open an issue describing the problem before submitting a pull request.

- Keep the core free of external Python dependencies whenever possible.
- Do not add telemetry or automatic APK uploads.
- Treat APKs as untrusted input and avoid executing their contents.
- When printing any string originating from an APK (names, strings, tool output),
  use `app.sanitize()` first — this removes ANSI escape sequences and control characters.
- Prefer clear comments and intention-revealing function names.
- Run `python -m unittest discover -s tests -v` before submitting changes.
- Provide device model, Android version, CPU architecture, Termux version, and external tool versions when reporting issues.

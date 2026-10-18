# Security Policy

To report a vulnerability or bug in ReaDroid, please open an issue without attaching private APKs, tokens, keys, or personal data. Explain the impact and provide a minimal, non-sensitive reproduction example.

ReaDroid is a static analysis tool. Unknown APKs should always be treated as untrusted files and must not be executed merely because they were analyzed by this tool.

## On Rebuilding and Signing APKs

Starting with version 0.3.0, ReaDroid supports rebuilding and signing APKs (apktool + zipalign + apksigner/jarsigner). Only use this feature on your own applications or apps you have explicit authorization to modify:

- Re-signing an APK alters the original developer identity. The resulting package is not an update to the app store version, and Android will treat it as a distinct application.
- Redistributing someone else's modified APK without permission may violate the original app's license and terms of service.
- ReaDroid does not bypass DRM protections, license checks, or obfuscation; it merely automates the standard Android build workflow (using the same `apktool`/`zipalign`/`apksigner` tools documented by the Android Open Source Project).

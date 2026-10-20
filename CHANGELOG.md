# Changelog

## 0.1.0 - 2026-10-16
- Initial public release designed for non-root Termux.
- Interactive menu featuring a subtle OffensiveTec watermark.
- APK inspection, SHA-256 hash calculation, string scanner, and JSON reports.
- Optional JADX and Apktool integrations.
- Documentation, optional installer script, and basic tests.

## 0.2.0
- Fixed base path resolution: reports and outputs are stored alongside the running project clone.
- JADX now reports full success, partial output, or failure based on generated files.
- Added interactive file explorer to navigate and open decompiled files and reports from the menu.
- Improved automatic APK discovery in the Termux/Android Download directory.

## 0.3.0 - 2026-10-18
- **Native binary AndroidManifest.xml (AXML) parser with zero dependencies.** Previously, manifests
  were only parsed when present as plain text XML (almost no real-world APKs); the binary format used by
  real APKs is now decoded in pure Python. JADX/Apktool/aapt2 serve as fallbacks for
  rare parser failures rather than the primary path.
- **Automated rebuilding and compilation (new menu option 11).** `apktool b` + `zipalign` + signing
  (`apksigner`, with `jarsigner` fallback) in a single workflow: decode with option 5, edit,
  run option 11, and obtain an aligned, signed, install-ready APK — without memorizing commands.
- **Quick manifest edits (new menu option 10):** debuggable, allowBackup, cleartext traffic, and
  INTERNET permission, applied directly to the decoded directory before rebuilding.
- **Signing key management (new menu option 12):** the keystore is automatically created during the
  first rebuild and reused for subsequent builds.
- Fixed string scanner false positives: Android/Kotlin class names (`android.content.pm...`)
  no longer match as "domains"; domain matching now verifies against real TLDs.
- Scanner reports now indicate when a category (URLs/domains/IPs) hits item limits
  and may be truncated, rather than discarding items silently.
- File extensions are no longer rejected (`.xapk`, `.apks`, or any extension are accepted as long as the
  file is a valid ZIP archive); unusual extensions now generate an informational notice in the report.
- Fixed traceback on terminal close or Ctrl+D/Ctrl+C: the menu now exits cleanly
  instead of crashing with an unhandled exception.
- Fixed file viewing in the explorer: strings and filenames from APKs are
  sanitized before display (stripping ANSI escape sequences and control characters),
  and `less -R` was replaced with safe raw display mode.
- Fixed version number reported during APK inspection (previously hardcoded to "0.1.0").
- Fixed `install.sh`: the final path displayed now shows the actual project directory rather than
  literal `$SCRIPT_DIR`.
- Added `.gitignore` and `LICENSE` (MIT).

## 0.3.1
- **Package renaming (applicationId)** directly in the decoded directory (option 10, or within option 11
  prior to building): updates manifest `package=`, moves `smali`/`smali_classesN` directories from
  the old path to the new path, and rewrites class references across `.smali` files (both dotted format and
  `Lcom/package/Class;` format). This is best-effort — reflection, dynamically assembled strings, or heavy
  obfuscation may not be replaced, so ReaDroid prompts you to test the rebuilt APK before
  relying on it. Similar package names (e.g., `com.x.app` vs `com.x.app2`) are not conflated.

## 0.4.0
- **New solid-block "ReaDroid" banner** (adapts to terminal width; compact fallback on very narrow screens).
- **Optional AI assistant (new menu option 13)** via opencode + OpenRouter, in a separate module
  (`readroid/ai.py`). The core never imports it: ignore it, or delete the file and the option disappears.
- **One-step setup:** paste the OpenRouter API key; ReaDroid saves it outside the project (`~/.readroid`, mode 600),
  generates the opencode config for a free Nemotron model and runs a connection test.
- **Fixed the "opencode opens but AI doesn't answer" case:** opencode is now always launched inside the APK folder
  with config and key passed by environment variable, instead of depending on the current directory.
  Opening it in the home folder is refused.
- Diagnostics split the problem: direct OpenRouter test (key/model) vs. opencode test.
- Model switcher lists free Nemotron models from the OpenRouter catalog.
- `opencode` added to the dependency check (option 6).
- AI menu: **cross-check JSON reports with the code**, **edit → rebuild → fix-errors loop** (backup first, max 3 attempts,
  confirmation before each AI correction, list of files changed) and free-form questions.
- Default model is now `nvidia/nemotron-3.5-lightning:free`. If a free model is withdrawn, ReaDroid detects it and switches
  to another `:free` Nemotron automatically (never to a paid one) and retries.
- Pasted paths are cleaned of invisible terminal characters; "not found" messages show the path ReaDroid actually read.


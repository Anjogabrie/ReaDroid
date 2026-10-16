import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from readroid.analyzer import inspect_apk, scan_strings, analyze_manifest, decompile_with_jadx


class AnalyzerTests(unittest.TestCase):
    def make_apk(self, root: Path, manifest: bytes | None = None) -> Path:
        apk = root / "sample.apk"
        with zipfile.ZipFile(apk, "w") as z:
            if manifest is not None:
                z.writestr("AndroidManifest.xml", manifest)
            z.writestr("classes.dex", b"dex\n035\x00 https://example.com/api test.example.org 192.168.1.2")
            z.writestr("res/layout/main.xml", b"<view />")
        return apk

    def test_inspect_apk(self):
        with tempfile.TemporaryDirectory() as tmp:
            apk = self.make_apk(Path(tmp), b"<manifest package='org.example' />")
            result = inspect_apk(apk)
            self.assertEqual(result["file_name"], "sample.apk")
            self.assertEqual(result["dex_files"], ["classes.dex"])
            self.assertEqual(len(result["sha256"]), 64)

    def test_scan_strings(self):
        with tempfile.TemporaryDirectory() as tmp:
            apk = self.make_apk(Path(tmp))
            result = scan_strings(apk)
            self.assertTrue(any("example.com" in value for value in result["urls"]))
            self.assertIn("192.168.1.2", result["ipv4_candidates"])

    def test_manifest_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = b'''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.example"><uses-permission android:name="android.permission.INTERNET"/><application android:debuggable="false"><activity android:name=".Main" android:exported="true"/></application></manifest>'''
            apk = self.make_apk(Path(tmp), manifest)
            result = analyze_manifest(apk, Path(tmp) / "out")
            self.assertTrue(result["decoded"])
            self.assertEqual(result["permissions"][0]["name"], "android.permission.INTERNET")
            self.assertEqual(result["components"][0]["exported"], "true")

    def test_jadx_partial_output_is_reported_as_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            apk = self.make_apk(root, b"<manifest package='org.example'/>")
            output = root / "out"

            def fake_run(command, timeout=180):
                (output / "sources" / "org" / "example").mkdir(parents=True)
                (output / "sources" / "org" / "example" / "Main.java").write_text("class Main {}")
                return {"returncode": 1, "stdout": "", "stderr": "finished with errors"}

            with patch("readroid.analyzer.shutil.which", return_value="/usr/bin/jadx"), \
                 patch("readroid.analyzer._run", side_effect=fake_run):
                result = decompile_with_jadx(apk, output)

            self.assertFalse(result["ok"])
            self.assertTrue(result["partial"])
            self.assertEqual(result["status"], "partial")
            self.assertEqual(result["java_files"], 1)
            self.assertEqual(result["files_generated"], 1)


if __name__ == "__main__":
    unittest.main()

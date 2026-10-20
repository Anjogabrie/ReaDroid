from __future__ import annotations

import importlib
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from readroid import banner  # noqa: E402


class BannerTests(unittest.TestCase):
    def test_banner_cabe_em_tela_pequena(self):
        self.assertLessEqual(banner.big_width(), 40)

    def test_banner_largo_tem_7_linhas_e_so_blocos(self):
        lines = banner.render(60, ("", "", ""))
        self.assertEqual(len(lines), 7)
        self.assertTrue(set("".join(lines)) <= {"█", " "})

    def test_banner_compacto_em_terminal_estreito(self):
        lines = banner.render(30, ("", "", ""))
        self.assertEqual(len(lines), 1)
        self.assertIn("ReaDroid", lines[0])


class AiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["READROID_HOME"] = str(Path(self.tmp.name) / "rd")
        os.environ.pop("OPENROUTER_API_KEY", None)
        import readroid.ai as ai
        self.ai = importlib.reload(ai)

    def tearDown(self):
        os.environ.pop("READROID_HOME", None)
        self.tmp.cleanup()

    def test_configure_guarda_chave_com_permissao_600_fora_do_config(self):
        res = self.ai.configure("sk-or-v1-" + "a" * 30)
        self.assertTrue(res["ok"])
        mode = stat.S_IMODE(self.ai.KEY_FILE.stat().st_mode)
        self.assertEqual(mode, 0o600)
        cfg = self.ai.OC_CONFIG.read_text()
        self.assertNotIn("sk-or-v1", cfg)  # a chave nunca vai no opencode.json
        self.assertEqual(self.ai.load_key(), "sk-or-v1-" + "a" * 30)

    def test_configure_rejeita_lixo(self):
        self.assertFalse(self.ai.configure("oi tudo bem")["ok"])
        self.assertFalse(self.ai.KEY_FILE.exists())

    def test_config_usa_openrouter_e_modelo_padrao(self):
        self.ai.configure("sk-or-v1-" + "b" * 30)
        cfg = json.loads(self.ai.OC_CONFIG.read_text())
        self.assertEqual(cfg["model"], "openrouter/" + self.ai.DEFAULT_MODEL)
        self.assertIn(self.ai.DEFAULT_MODEL, cfg["provider"]["openrouter"]["models"])

    def test_env_aponta_config_e_chave(self):
        env = self.ai.build_env("KEY")
        self.assertEqual(env["OPENROUTER_API_KEY"], "KEY")
        self.assertEqual(env["OPENCODE_CONFIG"], str(self.ai.OC_CONFIG))

    def test_comando_interativo_e_run(self):
        self.assertEqual(self.ai.opencode_command("oc", "m:free"), ["oc", "-m", "openrouter/m:free"])
        self.assertEqual(self.ai.opencode_command("oc", "m:free", "oi"),
                         ["oc", "run", "-m", "openrouter/m:free", "oi"])

    def test_recusa_pasta_pessoal(self):
        ok, _ = self.ai.safe_workdir(Path.home())
        self.assertFalse(ok)
        ok, _ = self.ai.safe_workdir(Path(self.tmp.name))
        self.assertTrue(ok)

    def test_filtra_modelos_nemotron_free(self):
        models = [{"id": "nvidia/nemotron-3-nano-30b-a3b:free"},
                  {"id": "nvidia/nemotron-3-embed-1b:free"},
                  {"id": "nvidia/nemotron-nano-12b-v2-vl:free"},
                  {"id": "nvidia/nemotron-3-super-120b-a12b:free"},
                  {"id": "nvidia/nemotron-3-super-120b-a12b"},
                  {"id": "openai/gpt-5"}]
        self.assertEqual(self.ai.pick_free_models(models),
                         ["nvidia/nemotron-3-super-120b-a12b:free",
                          "nvidia/nemotron-3-nano-30b-a3b:free"])

    def test_disable_apaga_tudo(self):
        self.ai.configure("sk-or-v1-" + "c" * 30)
        self.assertEqual(len(self.ai.disable()), 3)
        self.assertIsNone(self.ai.load_key())

    def test_sem_chave_open_interactive_nao_quebra(self):
        res = self.ai.open_interactive(Path(self.tmp.name))
        self.assertFalse(res["ok"])

    def test_clean_remove_escapes(self):
        self.assertEqual(self.ai._clean("a\x1b[31mb\x07c"), "abc")

    def test_nucleo_nao_importa_ai(self):
        # Em subprocesso, para não mexer nos módulos já carregados por outros testes.
        import subprocess
        code = "import sys; import readroid.app; sys.exit(1 if 'readroid.ai' in sys.modules else 0)"
        res = subprocess.run([sys.executable, "-c", code], cwd=ROOT)
        self.assertEqual(res.returncode, 0)


class LoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["READROID_HOME"] = str(Path(self.tmp.name) / "rd")
        import readroid.ai as ai
        self.ai = importlib.reload(ai)
        self.root = Path(self.tmp.name)
        self.decoded = self.root / "app_apktool"
        (self.decoded / "smali").mkdir(parents=True)
        (self.decoded / "smali" / "A.smali").write_text("x")

    def tearDown(self):
        os.environ.pop("READROID_HOME", None)
        self.tmp.cleanup()

    def test_snapshot_diff(self):
        before = self.ai.snapshot(self.decoded)
        (self.decoded / "smali" / "A.smali").write_text("changed!!")
        (self.decoded / "new.txt").write_text("n")
        d = self.ai.diff_snapshots(before, self.ai.snapshot(self.decoded))
        self.assertEqual(d["changed"], [os.path.join("smali", "A.smali")])
        self.assertEqual(d["added"], ["new.txt"])

    def test_relatorios_pegam_o_mais_recente_de_cada_tipo_e_encurtam(self):
        reports = self.root / "reports"
        reports.mkdir()
        (reports / "app_manifesto_20260101_000000.json").write_text(json.dumps({"v": "velho"}))
        (reports / "app_manifesto_20260102_000000.json").write_text(
            json.dumps({"urls": [f"http://x{i}.com" for i in range(100)]}))
        os.utime(reports / "app_manifesto_20260101_000000.json", (1, 1))
        found = self.ai.find_reports(reports, self.decoded)
        self.assertEqual(len(found), 1)
        ctx = self.ai.build_report_context(reports, self.decoded)
        self.assertIn("omitidos", ctx)
        self.assertNotIn("velho", ctx)

    def test_loop_corrige_depois_de_um_erro(self):
        calls = {"build": 0, "ask": []}

        def build():
            calls["build"] += 1
            if calls["build"] == 1:
                return {"ok": False, "steps": {"rebuild": {"ok": False, "stderr": "erro smali linha 3"}}}
            return {"ok": True, "final_apk": "x.apk", "steps": {}}

        def ask(prompt):
            calls["ask"].append(prompt)
            (self.decoded / "smali" / "A.smali").write_text("consertado")
            return {"ok": True, "message": "ok"}

        out = self.ai.fix_loop(self.decoded, "", build, ask, lambda q: True, lambda m: None)
        self.assertTrue(out["ok"])
        self.assertEqual(out["rounds"], 2)
        self.assertEqual(len(calls["ask"]), 1)
        self.assertIn("erro smali linha 3", calls["ask"][0])
        self.assertIn("apktool.yml", calls["ask"][0])  # regra de não mexer no apktool.yml

    def test_loop_respeita_limite_e_recusa_do_usuario(self):
        build = lambda: {"ok": False, "steps": {"rebuild": {"ok": False, "stderr": "e"}}}
        asked = []
        out = self.ai.fix_loop(self.decoded, "", build, lambda p: asked.append(p) or {"ok": True},
                               lambda q: False, lambda m: None)
        self.assertFalse(out["ok"])
        self.assertEqual(asked, [])
        asked.clear()
        out = self.ai.fix_loop(self.decoded, "", build, lambda p: asked.append(p) or {"ok": True},
                               lambda q: True, lambda m: None, max_rounds=3)
        self.assertFalse(out["ok"])
        self.assertEqual(len(asked), 2)  # 3 builds => 2 pedidos de correção

    def test_loop_com_instrucao_edita_antes_de_compilar(self):
        order = []
        out = self.ai.fix_loop(self.decoded, "trocar texto X",
                               lambda: order.append("build") or {"ok": True, "steps": {}},
                               lambda p: order.append("ask") or {"ok": True},
                               lambda q: True, lambda m: None)
        self.assertEqual(order, ["ask", "build"])
        self.assertTrue(out["ok"])


class CleanPathTests(unittest.TestCase):
    def test_remove_lixo_de_colagem_e_aspas(self):
        from readroid.app import clean_path
        self.assertEqual(clean_path("\x1b[200~/sdcard/Download/F-Droid.apk\x1b[201~"), "/sdcard/Download/F-Droid.apk")
        self.assertEqual(clean_path("[200~/sdcard/Download/a.apk[201~"), "/sdcard/Download/a.apk")
        self.assertEqual(clean_path('  "/sdcard/Download/a b.apk"\u200b '), "/sdcard/Download/a b.apk")
        self.assertEqual(clean_path("/sdcard/Download/F-Droid.apk"), "/sdcard/Download/F-Droid.apk")


class ModelFallbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["READROID_HOME"] = str(Path(self.tmp.name) / "rd")
        import readroid.ai as ai
        self.ai = importlib.reload(ai)
        self.ai.configure("sk-or-v1-" + "d" * 30, "nvidia/nemotron-3-nano-30b-a3b:free")

    def tearDown(self):
        os.environ.pop("READROID_HOME", None)
        self.tmp.cleanup()

    def test_padrao_e_o_lightning(self):
        self.assertEqual(self.ai.DEFAULT_MODEL, "nvidia/nemotron-3.5-lightning:free")

    def test_reconhece_erro_de_modelo_nao_gratuito(self):
        msg = ("Error: This model is unavailable for free. The paid version is available now - "
               "use this slug instead: nvidia/nemotron-3-nano-30b-a3b")
        self.assertTrue(self.ai._UNAVAIL_RE.search(msg))

    def test_troca_para_o_primeiro_free_que_responde_e_nunca_para_pago(self):
        tested = []

        def fake_test(key, model):
            tested.append(model)
            return {"ok": model.endswith("super-120b-a12b:free")}

        with patch.object(self.ai, "test_api", fake_test), \
                patch.object(self.ai, "list_free_nemotron", lambda: []):
            found = self.ai.ensure_working_model("k", ("nvidia/nemotron-3-nano-30b-a3b:free",))
        self.assertEqual(found, "nvidia/nemotron-3-super-120b-a12b:free")
        self.assertTrue(all(m.endswith(":free") for m in tested))
        self.assertEqual(self.ai.load_model(), found)
        cfg = json.loads(self.ai.OC_CONFIG.read_text())
        self.assertEqual(cfg["model"], "openrouter/" + found)

    def test_sem_nenhum_funcionando_devolve_none(self):
        with patch.object(self.ai, "test_api", lambda k, m: {"ok": False}), \
                patch.object(self.ai, "list_free_nemotron", lambda: []):
            self.assertIsNone(self.ai.ensure_working_model("k"))

    def test_ask_once_marca_modelo_indisponivel(self):
        fake = Path(self.tmp.name) / "opencode"
        fake.write_text("#!/bin/sh\necho 'Error: This model is unavailable for free. use this slug instead: x'\n")
        fake.chmod(0o755)
        work = Path(self.tmp.name) / "w"
        work.mkdir()
        with patch.object(self.ai, "find_opencode", lambda: str(fake)):
            res = self.ai.ask_once(work, "oi", emit=lambda m: None)
        self.assertFalse(res["ok"])
        self.assertTrue(res.get("model_unavailable"))


if __name__ == "__main__":
    unittest.main()

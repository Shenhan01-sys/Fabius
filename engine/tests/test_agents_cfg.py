"""P159: daftar agent rumah + penyedia di config/agents.json; `tambah` = jalan pintas agent baru yang tervalidasi (tanpa kunci, tanpa tx);
penampilan NPC opsional diteruskan gerbang ke lantai /desk."""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, ROOT)

import analis as an                                                 # noqa: E402


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = os.path.join(self.tmp, "agents.json")
        shutil.copy(an.AGENTS_PATH, self.path)

    def test_the_registry_file_is_the_same_list_the_code_uses(self):
        prov, ags = an.muat_agents()
        self.assertEqual(ags, an.AGENTS)
        self.assertEqual([a["slug"] for a in ags][:2], ["glm", "qwen"])                        # urutan tetap (slot 2558, 2559)
        for a in ags:
            self.assertIn(a["provider"], prov)
            if a.get("npc"):
                an.cek_npc(a["npc"])

    def test_tambah_adds_a_validated_agent_and_a_new_provider_only_with_base_and_key(self):
        ag = an.tambah_agent(self.path, "kimi", "Kimi K2.6", "hcnsec", "Kimi-K2.6", "high", base="https://api.example.com/v1/", key_var="HCNSEC_API_KEY",
                             npc={"extra": "glasses", "short": "Kimi"})
        self.assertEqual((ag["name"], ag["key_var"]), ("Fabius Analyst · Kimi K2.6", "ANALIS_KIMI_PRIVATE_KEY"))
        prov, ags = an.muat_agents(self.path)
        self.assertEqual(prov["hcnsec"], {"base": "https://api.example.com/v1", "key_var": "HCNSEC_API_KEY"})
        self.assertEqual(ags[-1]["slug"], "kimi")
        an.tambah_agent(self.path, "kimi2", "Kimi B", "hcnsec", "Kimi-B", "high")                   # penyedia yang sudah ada: tanpa base
        for bad in (dict(slug="kimi"),                                                             # ganda
                    dict(slug="Kimi!"),                                                            # format
                    dict(slug="mm", provider="baru"),                                              # penyedia baru tanpa base/key
                    dict(slug="mm", effort="ultra"),
                    dict(slug="mm", npc={"extra": "crown"}),
                    dict(slug="mm", npc={"shirt": "violet"}),
                    dict(slug="mm", npc={"wings": True})):
            args = {"slug": "mm", "nama": "MiniMax", "provider": "hcnsec", "model": "MiniMax-M3", "effort": "high", **bad}
            npc = args.pop("npc", None)
            with self.assertRaises(ValueError, msg=str(bad)):
                an.tambah_agent(self.path, args["slug"], args["nama"], args["provider"], args["model"], args["effort"], npc=npc)
        self.assertEqual(len(an.muat_agents(self.path)[1]), len(an.AGENTS) + 2)                  # yang ditolak tidak menulis apa pun


    def test_ganti_swaps_the_model_keeps_the_slot_and_records_the_old_model(self):
        an.tambah_agent(self.path, "tesgrok", "Grok 4.7", "kios", "grok-4.7-free", "high", base="https://kios.example/v1", key_var="KIOS_API_KEY",
                        npc={"short": "Grok"})
        ag = an.ganti_model(self.path, "tesgrok", "GPT 6 Luna", "vyce", "gpt-6-luna", "high", base="https://vyce.example/v1", key_var="VYCE_API_KEY",
                            short="Luna", sampai_bar_close=1_791_244_800)
        self.assertEqual((ag["slug"], ag["key_var"], ag["model"], ag["name"], ag["npc"]["short"]),
                         ("tesgrok", "ANALIS_TESGROK_PRIVATE_KEY", "gpt-6-luna", "Fabius Analyst · GPT 6 Luna", "Luna"))   # slot + dompet tetap
        self.assertEqual(ag["riwayat"], [{"model": "grok-4.7-free", "provider": "kios", "effort": "high", "sampai_bar_close": 1_791_244_800}])
        self.assertEqual(an.muat_agents(self.path)[0]["vyce"]["key_var"], "VYCE_API_KEY")
        for bad in (dict(slug="tidakada"), dict(provider="vyce", model="gpt-6-luna"), dict(provider="baru"), dict(effort="ultra")):
            args = {"slug": "tesgrok", "nama": "X", "provider": "kios", "model": "m2", "effort": "high", **bad}
            with self.assertRaises(ValueError, msg=str(bad)):
                an.ganti_model(self.path, args["slug"], args["nama"], args["provider"], args["model"], args["effort"])
        card = an.card(ag, "0xsel")
        self.assertEqual(card["model"]["id"], "gpt-6-luna")
        self.assertEqual(card["model_history"][0]["id"], "grok-4.7-free")


    def test_nonaktif_and_aktif_toggle_an_agent_without_touching_its_identity(self):
        ag = an.set_nonaktif(self.path, "grok", "VyceAI 429")
        self.assertEqual((ag["nonaktif"], ag["key_var"]), ("VyceAI 429", "ANALIS_GROK_PRIVATE_KEY"))
        with self.assertRaises(ValueError):
            an.set_nonaktif(self.path, "grok", "  ")
        self.assertNotIn("nonaktif", an.set_nonaktif(self.path, "grok", None))
        with self.assertRaises(ValueError):
            an.set_nonaktif(self.path, "grok", None)                                              # sudah aktif
        with self.assertRaises(ValueError):
            an.set_nonaktif(self.path, "tidakada", "x")

    def test_the_model_comes_from_config_not_from_the_registration_record(self):
        from unittest import mock
        ag = next(a for a in an.AGENTS if a["slug"] == "glm")
        cfg = {"agents": {"glm": {"agent_id": 2558, "wallet": "0x" + "11" * 20, "model": "glm-5.3", "provider": "lama", "effort": "low"}}}
        env = {an.PROVIDERS[ag["provider"]]["key_var"]: "k", ag["key_var"]: "0x" + "22" * 32}
        with mock.patch.dict(os.environ, env), mock.patch.object(an, "ANALIS_ENV", os.path.join(self.tmp, "tidak-ada.env")):
            got = [a for a in an.active_agents(cfg) if a["slug"] == "glm"][0]
        self.assertEqual((got["model"], got["provider"], got["effort"], got["agent_id"]), (ag["model"], ag["provider"], ag["effort"], 2558))


class GateNpcTests(unittest.TestCase):
    def test_desk_books_carry_the_npc_look_from_the_registry(self):
        import meja
        import x402_sinyal as xs
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        old, os.environ["ANALIS_DIR"] = os.environ.get("ANALIS_DIR"), os.path.join(tmp, "analis")
        self.addCleanup(lambda: os.environ.pop("ANALIS_DIR") if old is None else os.environ.update(ANALIS_DIR=old))
        g = xs.Gate(xs.Data(ROOT), "0xk", "https://g", "https://w", log=lambda m: None, now=lambda: 1_791_200_100)
        books = {"konsensus": meja.buku_baru(), "glm": meja.buku_baru(), "v2:glm": meja.buku_baru(), "baru": meja.buku_baru()}
        g.meja_simpan([], {"siklus": 1_791_200_100, "daun": [], "harga": {}, "root": "0x1", "status": "dikomit", "n": 0}, books, {})
        by = {b["agent"]: b for b in g.meja_view()["buku"]}
        self.assertEqual(by["glm"]["npc"]["extra"], "headset")
        self.assertEqual(by["v2:glm"]["npc"], by["glm"]["npc"])
        self.assertIsNone(by["baru"]["npc"])                                                       # agent tanpa entri: web membuatnya dari slug
        self.assertIsNone(by["konsensus"]["npc"])
        json.dumps(by)
        self.assertIsNone(xs.kursi_aktif(g))                                                       # belum ada state kursi: perilaku lama
        books["_v2_kursi"] = {"kursi": {"glm": {"status": "aktif", "sejak": 0}, "baru": {"status": "uji", "sejak": 0}, "lain": {"status": "antre", "sejak": 0}}}
        g.meja_simpan([], {"siklus": 1_791_200_400, "daun": [], "harga": {}, "root": "0x2", "status": "dikomit", "n": 0}, books, {})
        self.assertEqual(xs.kursi_aktif(g), {"glm"})                                               # P162: hanya kursi aktif yang memilih harian
        self.assertEqual(xs.V1_AGEN, ("glm", "qwen", "berita"))


if __name__ == "__main__":
    unittest.main()

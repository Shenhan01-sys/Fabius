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


if __name__ == "__main__":
    unittest.main()

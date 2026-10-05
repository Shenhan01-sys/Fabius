"""P139 (F-D108): agent analis BERITA - judul berita + pengumuman Binance (tools/kabar.py) dibaca sekali per putaran dan DISALIN ke alasan ber-hash;
pengurai aman terhadap entitas XML; semua sumber gagal = agent berita tidak memilih bar itu. Jaringan, model, dan chain dipalsukan."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
try:
    import eth_abi                                                  # noqa: F401
    from eth_account import Account
    HAVE_ETH = True
except ImportError:
    HAVE_ETH = False

import analis as an                                                 # noqa: E402
import kabar                                                        # noqa: E402
from engine.tests.test_analis import NOW, SEL, FakeEv               # noqa: E402

RSS = b"""<?xml version="1.0"?>
<!DOCTYPE rss [<!ENTITY a "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"><!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]>
<rss version="2.0"><channel>
<item><title>BTC <b>holds</b> 120k</title><pubDate>Mon, 05 Oct 2026 02:00:00 GMT</pubDate><link>https://x.example/1</link></item>
<item><title>Old story</title><pubDate>Thu, 01 Oct 2026 02:00:00 GMT</pubDate><link>https://x.example/2</link></item>
<item><title></title><pubDate>Mon, 05 Oct 2026 02:00:00 GMT</pubDate></item>
</channel></rss>"""
BINANCE = json.dumps({"data": {"catalogs": [
    {"catalogId": 48, "articles": [{"title": "Binance Will List FOO", "releaseDate": (NOW - 3 * 86400) * 1000, "code": "abc"}]},
    {"catalogId": 93, "articles": [{"title": "Activity, ignored", "releaseDate": NOW * 1000}]}]}}).encode()


class SourceTests(unittest.TestCase):
    def test_rss_and_binance_are_parsed_inside_their_windows_and_a_failing_source_is_reported_not_hidden(self):
        def fetch(url):
            if "decrypt" in url:
                raise OSError("timeout")
            return BINANCE if "binance" in url else RSS
        k = kabar.kabar(NOW, fetch=fetch)
        self.assertEqual(k["status"]["decrypt"], "galat OSError: timeout")
        self.assertEqual(k["status"]["binance"], "ok 1")                                   # listing 3 hari lalu: masih di jendela 7 hari
        judul = [(x["sumber"], x["judul"]) for x in k["judul"]]
        self.assertIn(("binance-listing", "Binance Will List FOO"), judul)
        self.assertIn(("cointelegraph", "BTC holds 120k"), judul)                          # tag HTML dibuang
        self.assertNotIn("Old story", [j for _, j in judul])                               # > 36 jam
        self.assertFalse(any("Activity" in j for _, j in judul))                           # katalog di luar daftar
        self.assertNotIn("aaaa", json.dumps(k))                                            # DOCTYPE + entitas dibuang sebelum parse


@unittest.skipUnless(HAVE_ETH, "eth-abi/eth-account tidak terpasang")
class NewsRoundTests(unittest.TestCase):
    def setUp(self):
        self.acct = Account.create()
        k = self.acct.key.hex()
        self.env = {"XKIRO_API_KEY": "kunci-uji", "ANALIS_BERITA_PRIVATE_KEY": k if k.startswith("0x") else "0x" + k}
        self.cfg = {"selection": SEL, "agents": {"berita": {"agent_id": 3001, "wallet": self.acct.address}}}
        self.out = tempfile.mkdtemp()
        self.bodies, self.logs = [], []

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def run_(self, ev, news):
        def post(url, headers, body, timeout):
            self.bodies.append((url, body))
            return {"choices": [{"message": {"content": json.dumps({"fitur_berita": {"sentimen": 9, "kejadian": ["ETF inflows"], "aset_disebut": ["BTCUSDT"]},
                                                                  "bot": "B1-TREND", "keyakinan": 58, "alasan": "trend + inflows", "risiko": "reversal"})}}]}
        with mock.patch.dict(os.environ, self.env), mock.patch.object(an, "ANALIS_ENV", os.path.join(self.out, "tidak-ada.env")):
            return an.run_round(ROOT, self.cfg, ev, NOW, True, log=self.logs.append, post=post, out_dir=self.out, kabar_fn=lambda now: news)

    def test_the_news_read_is_inside_the_hashed_reasoning_and_the_xkiro_model_is_called_with_high_effort(self):
        news = {"judul": [{"sumber": "binance-listing", "judul": "Binance Will List FOO", "waktu": NOW - 600, "url": "u"}], "status": {"binance": "ok 1"}}
        ev = FakeEv()
        r = self.run_(ev, news)[0]
        url, body = self.bodies[0]
        self.assertEqual((url, body["model"], body["reasoning_effort"]), ("https://api.xkiro.com/v1/chat/completions", "qwen/qwen3.8-omni-flash:free", "high"))
        self.assertIn("Binance Will List FOO", body["messages"][1]["content"])
        a = r["alasan"]
        self.assertEqual((r["status"], a["berita"], a["sumber_berita"]), ("dikomit", news["judul"], news["status"]))
        self.assertEqual(a["pilihan"]["fitur_berita"], {"sentimen": 2, "kejadian": ["ETF inflows"], "aset_disebut": ["BTCUSDT"]})   # dijepit -2..2
        self.assertEqual(r["reasonHash"], an.sha(a))                                       # berita ikut di-hash -> terkomit on-chain
        self.assertNotEqual(a["masukan_sha256"], an.sha(an.masukan(ROOT, an.next_close(NOW))))
        self.assertEqual(len(ev.sent), 1)

    def test_without_any_news_the_news_agent_does_not_pick_that_bar(self):
        ev = FakeEv()
        r = self.run_(ev, {"judul": [], "status": {"cointelegraph": "galat OSError: x", "binance": "ok 0"}})[0]
        self.assertEqual(r["status"], "gagal")
        self.assertEqual((ev.sent, self.bodies), ([], []))
        self.assertTrue(any("tidak memilih" in m for m in self.logs))


if __name__ == "__main__":
    unittest.main()

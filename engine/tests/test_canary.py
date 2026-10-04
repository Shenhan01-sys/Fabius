"""P133 (F-D92 S3, F-D96): canary uang NYATA (tools/canary.py) - satu aset, <= 10 USDT, mengikuti B1. Venue, chain, Gist, pencatat on-chain dipalsukan."""
import json
import os
import shutil
import sys
import tempfile
import unittest

from engine.tests.test_eksekutor import BAR, COMMITTER, FakeAlert
from engine.tests.test_exec_feed import FakeGist, FeedVenue

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import canary as cn                                                       # noqa: E402
import signal_commit as sc                                                # noqa: E402
import venue_binance as vb                                                # noqa: E402
from engine.spec import SPECS                                             # noqa: E402

COMMIT_S = 1_791_017_100
ENV = {"EXEC_REAL": "canary", "BINANCE_REAL_API_KEY": "k", "BINANCE_REAL_SECRET_KEY": "s", "EXEC_LIVE_OK": "binance:sampai:2026-11-30",
       "EXEC_FEED_TOKEN": "t"}


class Chain:
    def __init__(self, committed=True):
        self.committed = committed

    def locked_at(self, committer, bot, spec):
        return 1

    def get_commit(self, cid):
        return {"committer": "0x" + ("11" * 20 if self.committed else "00" * 20), "committedAt": COMMIT_S}


class BadKeyVenue(FeedVenue):
    def assert_safe_key(self):
        raise vb.KeyPermissionError("kunci Binance punya izin tarik")


class CanaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.write_tick(BAR, "2026-10-02", {"XRPUSDT": 0.0625, "BTCUSDT": 0.0625})
        self.logs, self.alert, self.recorded = [], FakeAlert(), []

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_tick(self, asof, date, targets, mode="w"):
        with open(os.path.join(self.tmp, "B1-TREND.jsonl"), mode, encoding="utf-8") as f:
            f.write(json.dumps({"type": "tick", "asof": asof, "asof_date": date, "targets": targets}) + "\n")

    def canary(self, venue, env=None, gist=None, recorder="ok"):
        def rec(fills):
            if recorder == "fail":
                raise RuntimeError("rpc mati")
            self.recorded.append(fills)
            return "0xtx"
        return cn.Canary(env=env or ENV, log=self.logs.append, alert=self.alert, venue_factory=lambda e: venue, today=lambda: "2026-10-04",
                         now_ms=lambda: (COMMIT_S + 200) * 1000, sleep=lambda s: None,
                         feed_factory=lambda tok: cn.xf.GistFeed(tok, http=gist or FakeGist(), log=lambda s: None), recorder=rec)

    def test_off_by_default_and_refuses_without_keys_consent_or_with_an_outside_asset(self):
        self.assertEqual(cn.Canary(env={}, venue_factory=lambda e: 1 / 0).round(self.tmp, Chain(), COMMITTER), "off")
        for bad in ({"BINANCE_REAL_API_KEY": ""}, {"EXEC_LIVE_OK": ""}, {"EXEC_LIVE_OK": "binance:2026-10-04"},
                    {"EXEC_LIVE_OK": "binance:sampai:2026-10-03"}, {"EXEC_REAL_ASSET": "PEPEUSDT"}):
            v = FeedVenue()
            self.assertEqual(self.canary(v, env=dict(ENV, **bad)).round(self.tmp, Chain(), COMMITTER), "tolak")
            self.assertEqual(v.posts, 0)

    def test_follows_b1_on_one_asset_publishes_the_report_and_records_real_fills_on_chain(self):
        v, g = FeedVenue(), FakeGist()
        c = self.canary(v, gist=g)
        self.assertIn("TUNDA", c.round(self.tmp, Chain(committed=False), COMMITTER))           # bukti dulu
        self.assertEqual(v.posts, 0)
        self.assertIn("canary: 1 order", c.round(self.tmp, Chain(), COMMITTER))
        self.assertEqual(v.pos, {"XRPUSDT": 0.099})                                             # 10 x 0,998 / 100, dibulatkan ke lot 0,001
        self.assertEqual(v.lev, [("XRPUSDT", 1)])
        rec = json.loads(g.lines()[0])
        self.assertEqual((rec["venue"], rec["mode"], rec["bar"], len(rec["orders"])), ("binance-live", "live", "2026-10-02", 1))
        fill = self.recorded[0][0]
        self.assertEqual(fill[0], sc.commit_id(COMMITTER, "B1-TREND", SPECS["B1-TREND"].sha(), sc.asof_s_of({"asof": BAR})))
        self.assertTrue(fill[6])                                                                 # real = true
        self.assertEqual((fill[5], fill[9]), (1, 9_900_000))                                     # BUY, qty 0,099 x 1e8
        self.assertTrue(any(k.startswith("canary:2026-10-02") for k, _ in self.alert.sent))
        self.assertIn("sudah dieksekusi", c.round(self.tmp, Chain(), COMMITTER))
        self.assertEqual((v.posts, len(self.recorded)), (1, 1))
        self.write_tick(BAR + 86_400_000, "2026-10-03", {"BTCUSDT": 0.0625}, mode="a")         # B1 flat di XRP -> canary menutup
        self.assertIn("canary: 1 order", c.round(self.tmp, Chain(), COMMITTER))
        self.assertEqual(v.pos.get("XRPUSDT", 0), 0)
        self.assertEqual(self.recorded[1][0][5], 2)                                              # SELL

    def test_too_little_money_is_skipped_and_the_env_cap_cannot_exceed_ten_usdt(self):
        poor = FeedVenue(equity=4.0)
        g = FakeGist()
        self.assertIn("0 order, 1 dilewati", self.canary(poor, gist=g).round(self.tmp, Chain(), COMMITTER))
        self.assertEqual(poor.posts, 0)
        self.assertEqual([json.loads(x)["orders"] for x in g.lines()], [[]])                    # laporan tetap ada (0 order) untuk penjaga luar
        self.assertEqual(self.recorded, [])                                                      # tidak ada isi = tidak ada catatan on-chain
        rich = FeedVenue(equity=5000.0)
        self.canary(rich, env=dict(ENV, EXEC_REAL_MAX_USDT="50")).round(self.tmp, Chain(), COMMITTER)
        self.assertEqual(rich.pos, {"XRPUSDT": 0.099})                                           # tetap <= 10 USDT

    def test_an_unsafe_key_stops_the_canary_and_a_failed_chain_record_stays_pending(self):
        c = self.canary(BadKeyVenue())
        self.assertEqual(c.round(self.tmp, Chain(), COMMITTER), "berhenti")
        self.assertIn("izin tarik", c.halted)
        self.assertTrue(any(k.startswith("canary-berhenti") for k, _ in self.alert.sent))
        v = FeedVenue()
        c2 = self.canary(v, recorder="fail")
        c2.round(self.tmp, Chain(), COMMITTER)
        self.assertEqual(list(c2.pending_chain), ["2026-10-02"])
        self.assertTrue(any("catatan on-chain 2026-10-02 TERTUNDA" in x for x in self.logs))
        c2.recorder = lambda fills: "0xok"
        c2.round(self.tmp, Chain(), COMMITTER)
        self.assertEqual((c2.pending_chain, v.posts), ({}, 1))                                  # dicatat, order tidak digandakan


if __name__ == "__main__":
    unittest.main()

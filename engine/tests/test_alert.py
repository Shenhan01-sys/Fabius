"""P101: alert operator (tools/alert.py) dan pemicunya di worker (tools/operator_loop.py). Tanpa jaringan: pengirim Telegram tiruan."""
import os
import shutil
import sys
import tempfile
import unittest

from engine import ledger

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import alert as al                                                  # noqa: E402
import signal_commit as sc                                          # noqa: E402

from .test_signal_commit import HAVE_ETH                           # noqa: E402

TOKEN = "123456:ABC-rahasia-sekali"
LEDGER = os.path.join(ROOT, "ledger", "paper")


class Clock:
    def __init__(self):
        self.t = 1_000_000.0

    def __call__(self):
        return self.t


class AlerterTests(unittest.TestCase):
    def setUp(self):
        self.logs, self.posts, self.clock = [], [], Clock()

    def make(self, token=TOKEN, chat="42", post=None):
        def ok(url, data):
            self.posts.append((url, data))
            return {"ok": True}
        return al.Alerter(token=token, chat=chat, log=self.logs.append, post=post or ok, now=self.clock)

    def test_same_key_is_quiet_for_six_hours_then_repeats(self):
        a = self.make()
        self.assertEqual(a.send("alarm:B1:2026-10-02", "ALARM"), "terkirim")
        self.assertEqual(a.send("alarm:B1:2026-10-02", "ALARM"), "diredam")
        self.assertEqual(a.send("alarm:B3:2026-10-02", "ALARM"), "terkirim")      # kunci lain tetap lewat
        self.clock.t += al.COOLDOWN_S + 1
        self.assertEqual(a.send("alarm:B1:2026-10-02", "ALARM"), "terkirim")
        self.assertEqual(len(self.posts), 3)
        self.assertEqual(self.posts[0][1]["chat_id"], "42")
        self.assertTrue(self.posts[0][1]["text"].startswith("[Fabius] "))

    def test_once_keys_are_never_repeated_in_the_same_process(self):
        a = self.make()
        a.send("terlewat:B1:2026-10-02", "TERLEWAT", sekali=True)
        self.clock.t += 10 * al.COOLDOWN_S
        self.assertEqual(a.send("terlewat:B1:2026-10-02", "TERLEWAT", sekali=True), "diredam")

    def test_without_a_channel_it_only_logs_once(self):
        a = self.make(token="", chat="")
        self.assertEqual(a.send("k", "halo"), "tanpa-kanal")
        self.assertEqual(a.send("k", "halo"), "diredam")
        self.assertEqual(self.posts, [])
        self.assertEqual(sum("TANPA KANAL" in m for m in self.logs), 1)

    def test_send_failure_never_raises_and_never_prints_the_token(self):
        def boom(url, data):
            raise RuntimeError(f"HTTP 500 untuk {url}")
        a = self.make(post=boom)
        self.assertEqual(a.send("k", "halo"), "gagal")
        self.assertNotIn(TOKEN, " ".join(self.logs))
        self.assertIn("<token>", " ".join(self.logs))
        self.assertEqual(a.send("k", "halo"), "gagal")                             # gagal tidak dicatat sebagai terkirim: dicoba lagi

    def test_telegram_refusal_is_a_failure(self):
        a = self.make(post=lambda url, data: {"ok": False, "description": "chat not found"})
        self.assertEqual(a.send("k", "halo"), "gagal")
        self.assertIn("chat not found", self.logs[-1])


class MissingTickTests(unittest.TestCase):
    def test_official_tick_missing_twelve_hours_after_close_is_reported(self):
        import operator_loop as ol
        recs = ledger.load(os.path.join(LEDGER, "B1-TREND.jsonl"))
        last = max(r["asof"] for r in recs if r["type"] == "tick")
        close_next = (last + 2 * 86_400_000) // 1000                              # penutupan bar sesudah tick terakhir
        self.assertEqual(ol.missing_ticks(LEDGER, ["B1-TREND"], close_next + 3600), [])                   # masih dalam tenggang
        got = ol.missing_ticks(LEDGER, ["B1-TREND"], close_next + ol.TICK_GRACE_S + 60)
        self.assertEqual(got, [("B1-TREND", ledger.date_of(last + 86_400_000))])
        self.assertEqual(ol.missing_ticks(LEDGER, ["B1-TREND"], (last + 86_400_000) // 1000 + ol.TICK_GRACE_S + 60), [])   # bar yang punya tick

    def test_unreadable_ledger_is_reported_not_treated_as_fine(self):
        import operator_loop as ol
        d = tempfile.mkdtemp()
        try:
            with open(os.path.join(d, "B1-TREND.jsonl"), "w", encoding="utf-8") as f:
                f.write("{rusak\n")
            got = ol.missing_ticks(d, ["B1-TREND"], 1_791_118_800)                  # 4 Okt 13:00Z: lewat tenggang bar 3 Okt
            self.assertEqual(len(got), 1)
            self.assertIn("tak terbaca", got[0][1])
        finally:
            shutil.rmtree(d, ignore_errors=True)


@unittest.skipUnless(HAVE_ETH, "eth-account tidak terpasang")
class WorkerAlertTests(unittest.TestCase):
    def setUp(self):
        import operator_loop as ol
        self.ol = ol
        self.logs, self.posts = [], []
        self.orig = ol.log
        ol.log = self.logs.append
        self.w = ol.Worker(workdir=tempfile.gettempdir())
        self.w.alert = al.Alerter(token=TOKEN, chat="42", log=self.logs.append, post=lambda u, d: self.posts.append(d["text"]) or {"ok": True})

    def tearDown(self):
        self.ol.log = self.orig

    def test_alarm_terlewat_send_failure_and_missing_tick_each_alert(self):
        acts = [sc.Action("alarm", "B3-CARRY", "2026-10-02", "akar on-chain BEDA dari ledger"),
                sc.Action("skip", "B1-TREND", "2026-10-02", "TERLEWAT: 11.9 jam sesudah penutupan"),
                sc.Action("ok", "B1-TREND", "2026-10-01", "dikomit, 0/0 terungkap")]
        self.w.alerts_for(acts, {"commit": 0, "reveal": 0, "gagal": 2}, [("B1-TREND", "2026-10-03")])
        text = " | ".join(self.posts)
        for want in ("ALARM B3-CARRY", "TERLEWAT B1-TREND", "2 transaksi", "tick resmi B1-TREND bar 2026-10-03"):
            self.assertIn(want, text)
        self.assertEqual(len(self.posts), 4)
        self.w.alerts_for(acts, None, [("B1-TREND", "2026-10-03")])
        self.assertEqual(len(self.posts), 4)                                       # diulang: semuanya diredam

    def test_three_failed_rounds_in_a_row_alert_once(self):
        def broken(workdir=None):
            raise RuntimeError("git fetch gagal (128)")
        orig = self.ol.sync
        self.ol.sync = broken
        try:
            for _ in range(4):
                self.ol.guarded_round(self.w)
        finally:
            self.ol.sync = orig
        self.assertEqual(len(self.posts), 1)
        self.assertIn("3 putaran GAGAL", self.posts[0])


if __name__ == "__main__":
    unittest.main()

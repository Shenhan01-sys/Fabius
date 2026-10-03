"""P118 (epik 10): eksekutor venue (tools/eksekutor.py) + pembungkusnya di worker (tools/operator_loop.py). Venue dan chain dipalsukan."""
import json
import os
import shutil
import sys
import tempfile
import unittest

from engine import eksekusi as ex

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import eksekutor as ek                                                    # noqa: E402
import venue_binance as vb                                                # noqa: E402

BAR = 1_790_899_200_000
COMMITTER = "0x" + "cc" * 20
DEMO = {"EXEC_MODE": "demo", "BINANCE_API_ENV": "demo", "EXEC_MODAL_USDT": "1000"}


class FakeVenue:
    def __init__(self, dual=False, equity=5000.0, fail_place=0, fill=True):
        self.pos, self.orders, self.dual, self.eq, self.fail_place, self.fill = {}, {}, dual, equity, fail_place, fill
        self.lev, self.posts = [], 0

    def assert_safe_key(self):
        pass

    def dual_side(self):
        return self.dual

    def equity(self):
        return self.eq

    def filters(self, uni):
        return {a: ex.Filter(0.001, 0.001, 5.0) for a in uni}

    def book(self, uni):
        return {a: (99.9, 100.1) for a in uni}

    def positions(self):
        return dict(self.pos)

    def set_leverage(self, sym, lev):
        self.lev.append((sym, lev))

    def place(self, o):
        if o.client_id in self.orders:
            return dict(self.orders[o.client_id], _fabius="sudah ada (idempoten)")
        if self.fail_place:
            self.fail_place -= 1
            raise vb.VenueError("tak terjangkau")
        self.posts += 1
        self.orders[o.client_id] = {"status": "FILLED"}
        if self.fill:
            self.pos[o.asset] = round(self.pos.get(o.asset, 0.0) + (o.qty if o.side == "BUY" else -o.qty), 12)
        return {"status": "FILLED"}


class FakeChain:
    def __init__(self, committed=True, locked=1):
        self.committed, self.locked = committed, locked

    def locked_at(self, committer, bot, spec):
        return self.locked

    def get_commit(self, cid):
        return {"committer": "0x" + ("11" * 20 if self.committed else "00" * 20)}


class FakeAlert:
    def __init__(self):
        self.sent = []

    def send(self, key, text, sekali=False):
        self.sent.append((key, text))
        return "terkirim"


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        with open(os.path.join(self.tmp, "B1-TREND.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "tick", "asof": BAR, "asof_date": "2026-10-02", "targets": {"BTCUSDT": 0.5, "ETHUSDT": 0.5}}) + "\n")
        self.venue, self.alert, self.logs = FakeVenue(), FakeAlert(), []

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ex(self, env, venue=None, today="2026-10-03"):
        v = venue or self.venue
        return ek.Executor(env=env, log=self.logs.append, alert=self.alert, venue_factory=lambda e: v, today=lambda: today, sleep=lambda s: None)

    def test_off_by_default_touches_nothing(self):
        e = ek.Executor(env={}, venue_factory=lambda env: 1 / 0)
        self.assertEqual(e.round(self.tmp, FakeChain(), COMMITTER), "off")

    def test_live_is_refused_in_the_engine_and_without_the_builders_word_of_the_day(self):
        engine = self.ex({"EXEC_MODE": "live", "BINANCE_API_ENV": "prod", "RAILWAY_SERVICE_NAME": "fabius-engine", "EXEC_LIVE_OK": "binance:2026-10-03"})
        self.assertEqual(engine.round(self.tmp, FakeChain(), COMMITTER), "tolak")
        self.assertTrue(any("F-D93" in x for x in self.logs))
        stale = self.ex({"EXEC_MODE": "live", "BINANCE_API_ENV": "prod", "RAILWAY_SERVICE_NAME": "fabius-exec", "EXEC_LIVE_OK": "binance:2026-10-02"})
        self.assertEqual(stale.round(self.tmp, FakeChain(), COMMITTER), "tolak")
        mismatch = self.ex({"EXEC_MODE": "demo", "BINANCE_API_ENV": "testnet"})
        self.assertEqual(mismatch.round(self.tmp, FakeChain(), COMMITTER), "tolak")
        self.assertEqual(self.venue.posts, 0)

    def test_no_order_before_the_commit_then_exactly_once_per_bar(self):
        e = self.ex(DEMO)
        self.assertIn("TUNDA", e.round(self.tmp, FakeChain(committed=False), COMMITTER))
        self.assertEqual(self.venue.posts, 0)
        st = e.round(self.tmp, FakeChain(), COMMITTER)
        self.assertIn("dieksekusi: 2 order, posisi cocok", st)
        self.assertEqual(sorted(self.venue.lev), [("BTCUSDT", 1), ("ETHUSDT", 1)])          # leverage 1x sebelum order pertama
        self.assertEqual(self.venue.pos, {"BTCUSDT": 4.99, "ETHUSDT": 4.99})                # 0,5 x 1000 x (1 - 0,2 %) / 100, dibulatkan ke lot
        self.assertIn("sudah dieksekusi", e.round(self.tmp, FakeChain(), COMMITTER))
        self.assertEqual(self.venue.posts, 2)
        self.assertTrue(any(k.startswith("eksekusi:demo:B1-TREND:2026-10-02") for k, _ in self.alert.sent))

    def test_failed_send_is_retried_next_round_without_duplicates(self):
        v = FakeVenue(fail_place=1)
        e = self.ex(DEMO, venue=v)
        self.assertIn("1 order gagal", e.round(self.tmp, FakeChain(), COMMITTER))
        self.assertIn("posisi cocok", e.round(self.tmp, FakeChain(), COMMITTER))
        self.assertEqual(v.posts, 2)                                                   # dua aset, masing-masing satu kali

    def test_mismatch_after_orders_stops_the_executor_and_alerts(self):
        v = FakeVenue(fill=False)
        e = self.ex(DEMO, venue=v)
        self.assertEqual(e.round(self.tmp, FakeChain(), COMMITTER), "B1-TREND: berhenti")
        self.assertIn("tidak cocok", e.halted)
        self.assertTrue(any(k.startswith("eksekutor-berhenti") for k, _ in self.alert.sent))
        self.assertEqual(e.round(self.tmp, FakeChain(), COMMITTER), "berhenti")             # tetap berhenti sampai restart

    def test_hedge_mode_daily_loss_outside_universe_and_missing_keys_all_stop(self):
        self.assertEqual(self.ex(DEMO, venue=FakeVenue(dual=True)).round(self.tmp, FakeChain(), COMMITTER), "berhenti")
        v = FakeVenue()
        e = self.ex(DEMO, venue=v)
        e.round(self.tmp, FakeChain(committed=False), COMMITTER)                          # ekuitas awal hari 5000
        v.eq = 4700.0
        self.assertEqual(e.round(self.tmp, FakeChain(), COMMITTER), "berhenti")
        self.assertIn("rugi harian", e.halted)
        with open(os.path.join(self.tmp, "B1-TREND.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "tick", "asof": BAR, "asof_date": "2026-10-02", "targets": {"XAUUSDT": 1.0}}) + "\n")
        g = self.ex(DEMO, venue=FakeVenue())
        self.assertIn("berhenti", g.round(self.tmp, FakeChain(), COMMITTER))
        self.assertIn("di luar universe", g.halted)

        def no_keys(env):
            b = vb.BinanceFutures("demo", key="", secret="")
            return b
        k = ek.Executor(env=DEMO, log=self.logs.append, alert=self.alert, venue_factory=no_keys, today=lambda: "2026-10-03")
        self.assertEqual(k.round(self.tmp, FakeChain(), COMMITTER), "berhenti")
        self.assertIn("BINANCE_API_KEY", k.halted)

    def test_dry_plans_but_never_sends(self):
        v = FakeVenue()
        e = self.ex({"EXEC_MODE": "dry", "BINANCE_API_ENV": "demo", "EXEC_MODAL_USDT": "1000"}, venue=v)
        self.assertIn("dry: 2 order direncanakan", e.round(self.tmp, FakeChain(), COMMITTER))
        self.assertEqual(v.posts, 0)
        self.assertTrue(any("RENCANA BUY" in x for x in self.logs))


class WorkerWrapTests(unittest.TestCase):
    def test_executor_errors_never_fail_the_commit_round(self):
        import operator_loop as ol
        w = ol.Worker(workdir=tempfile.mkdtemp())
        sent = []
        w.alert.send = lambda key, text, sekali=False: sent.append(key)

        class Boom:
            def round(self, *a):
                raise RuntimeError("venue meledak")
        w.executor = Boom()
        for _ in range(3):
            self.assertEqual(w.exec_step(None, COMMITTER), "gagal")
        self.assertEqual(w.exec_fails, 3)
        self.assertIn("eksekutor-gagal", sent)


if __name__ == "__main__":
    unittest.main()

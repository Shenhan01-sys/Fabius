"""Epik 10 (eksekusi venue): inti eksekutor (engine/eksekusi.py), adaptor Binance (tools/venue_binance.py), kertas-venue (tools/kertas_eksekusi.py).
Tanpa jaringan dan tanpa kunci: venue, chain, dan kline dipalsukan."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from engine import eksekusi as ex
from engine import ledger
from engine.spec import SPECS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import kertas_eksekusi as ke                                               # noqa: E402
import venue_binance as vb                                                 # noqa: E402

UNI = list(SPECS["B1-TREND"].universe)
PX = {a: (60_000.0 if a == "BTCUSDT" else 3_000.0 if a == "ETHUSDT" else 100.0) for a in UNI}
FILT = {a: ex.Filter(step=0.001 if a == "BTCUSDT" else 0.01, min_qty=0.001, min_notional=50.0 if a == "BTCUSDT" else 20.0 if a == "ETHUSDT" else 5.0)
        for a in UNI}
EQUAL = {a: 1 / 16 for a in UNI}


class PlanTests(unittest.TestCase):
    def test_b1_on_2000_opens_all_16_within_capital_with_deterministic_ids(self):
        p = ex.plan("binance", "B1-TREND", "2026-10-02", EQUAL, 2000.0, {}, PX, FILT)
        self.assertEqual((len(p.orders), len(p.dilewati)), (16, 0))
        self.assertLessEqual(sum(abs(q) * PX[a] for a, q in p.intended.items()), 2000.0)
        ids = [o.client_id for o in p.orders]
        self.assertEqual(len(set(ids)), 16)
        self.assertTrue(all(len(i) <= 36 and i.isalnum() for i in ids))
        again = ex.plan("binance", "B1-TREND", "2026-10-02", EQUAL, 2000.0, {}, PX, FILT)
        self.assertEqual(ids, [o.client_id for o in again.orders])                  # tick yang sama = id yang sama (SK-E6)
        self.assertEqual(ex.guard(p, modal=2000.0, universe=UNI, price=PX, long_only=True), [])

    def test_ten_usdt_opens_nothing_and_says_why(self):
        # 10 USDT x 6,25 % = 0,625 USDT per aset < min notional 5: tidak ada yang dibuka, semuanya tercatat (SK-E5, UNGKAPKAN)
        p = ex.plan("binance", "B1-TREND", "2026-10-02", EQUAL, 10.0, {}, PX, FILT)
        self.assertEqual(len(p.orders), 0)
        self.assertEqual(len(p.dilewati), 16)
        self.assertTrue(all(("min notional" in r) or ("1 lot" in r) for _, r in p.dilewati))

    def test_closing_is_always_sent_reduce_only_even_below_min_notional(self):
        p = ex.plan("binance", "B1-TREND", "b", {}, 2000.0, {"DOTUSDT": 0.02}, PX, FILT)
        self.assertEqual(len(p.orders), 1)
        o = p.orders[0]
        self.assertEqual((o.side, o.qty, o.reduce_only, o.alasan), ("SELL", 0.02, True, "tutup"))
        self.assertEqual(p.intended["DOTUSDT"], 0.0)

    def test_small_rebalance_is_skipped_and_recorded(self):
        pos = {a: ex.floor_step(2000 / 16 / PX[a], FILT[a].step) for a in UNI}
        w = {a: 1 / 15 for a in UNI if a != "NEARUSDT"}                             # satu aset keluar: sisanya 6,25 % -> 6,67 %
        p = ex.plan("binance", "B1-TREND", "b", w, 2000.0, pos, PX, FILT)
        self.assertEqual([o.asset for o in p.orders], ["NEARUSDT"])
        self.assertTrue(any("ubah kecil" in r for _, r in p.dilewati))
        self.assertEqual(p.intended["ETHUSDT"], pos["ETHUSDT"])                     # dilewati = posisi lama dipertahankan

    def test_guard_refuses_outside_universe_short_on_long_only_and_overspend(self):
        p = ex.plan("binance", "B1-TREND", "b", {"XAUUSDT": 0.5, "BTCUSDT": -0.5}, 2000.0, {}, dict(PX, XAUUSDT=2000.0),
                    dict(FILT, XAUUSDT=ex.Filter(0.001, 0.001, 5.0)))
        probs = ex.guard(p, modal=2000.0, universe=UNI, price=dict(PX, XAUUSDT=2000.0), long_only=True)
        self.assertTrue(any("di luar universe" in x for x in probs))
        self.assertTrue(any("short pada bot long-only" in x for x in probs))
        big = ex.plan("binance", "B1-TREND", "b", EQUAL, 4000.0, {}, PX, FILT)
        self.assertTrue(any("notional total" in x for x in ex.guard(big, modal=2000.0, universe=UNI, price=PX, long_only=True)))

    def test_reconcile_fills_and_loss_stop(self):
        self.assertEqual(ex.reconcile({"BTCUSDT": 0.002}, {"BTCUSDT": 0.002}, FILT), [])
        self.assertEqual(ex.reconcile({"BTCUSDT": 0.002}, {"BTCUSDT": 0.001}, FILT), [("BTCUSDT", 0.002, 0.001)])
        o = ex.Order("BTCUSDT", "BUY", 0.002, 60_000.0, 120.0, "fx", False, "buka")
        px, fee = ex.fill_paper(o, 60_000.0, fee_bps=5.0, slip_bps=1.0)
        self.assertAlmostEqual(px, 60_006.0)
        self.assertAlmostEqual(fee, 0.002 * 60_006.0 * 5e-4)
        pos, cash = ex.apply_fills({}, 1000.0, [(o, px, fee)])
        self.assertEqual(pos, {"BTCUSDT": 0.002})
        self.assertAlmostEqual(cash, 1000.0 - 0.002 * 60_006.0 - fee)
        self.assertTrue(ex.loss_breached(100.0, 94.0, 0.05))
        self.assertFalse(ex.loss_breached(100.0, 96.0, 0.05))


class BinanceAdapterTests(unittest.TestCase):
    def test_signature_matches_the_official_binance_docs_vector(self):
        q = "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559"
        self.assertEqual(vb.sign(q, "NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j"),
                         "c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71")

    def test_filters_parse_lot_and_min_notional(self):
        info = {"symbols": [{"symbol": "BTCUSDT", "filters": [{"filterType": "LOT_SIZE", "stepSize": "0.001", "minQty": "0.001"},
                                                              {"filterType": "MARKET_LOT_SIZE", "stepSize": "0.001", "minQty": "0.001"},
                                                              {"filterType": "MIN_NOTIONAL", "notional": "100"}]}]}
        self.assertEqual(vb.parse_filters(info, ["BTCUSDT", "XYZ"]), {"BTCUSDT": ex.Filter(0.001, 0.001, 100.0)})

    def test_environments_point_at_the_official_sdk_hosts_and_prod_is_never_default(self):
        self.assertEqual(vb.BASE["demo"]["fapi"], "https://demo-fapi.binance.com")
        self.assertEqual(vb.BASE["testnet"]["fapi"], "https://testnet.binancefuture.com")
        self.assertEqual(vb.BASE["prod"]["fapi"], "https://fapi.binance.com")
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(vb.BinanceFutures(key="k", secret="s").env, "testnet")
        with mock.patch.dict(os.environ, {"BINANCE_API_ENV": "demo"}):
            b = vb.BinanceFutures(key="k", secret="s")
            self.assertEqual(b.env, "demo")
            b.assert_safe_key()                                                   # demo: saldo virtual, tidak ada panggilan izin
        with self.assertRaises(ValueError):
            vb.BinanceFutures(env="mainnet", key="k", secret="s")

    def test_key_with_withdraw_or_unknown_permissions_never_starts(self):
        for bad in ({"enableWithdrawals": True, "enableFutures": True}, {"enableFutures": True}, {"enableWithdrawals": False}):
            with self.assertRaises(vb.KeyPermissionError):
                vb.check_no_withdraw(bad)
        vb.check_no_withdraw({"enableWithdrawals": False, "enableFutures": True})

    def test_place_is_idempotent_and_secrets_never_leak(self):
        calls = []

        def http(method, url, headers):
            calls.append((method, url.split("?")[0]))
            if method == "GET":
                return (200, {"clientOrderId": "fxabc", "status": "FILLED"}) if "exists" in url else (400, {"code": -2013, "msg": "Order does not exist."})
            return 200, {"clientOrderId": "fxnew", "status": "NEW"}

        b = vb.BinanceFutures("testnet", key="KEY123", secret="SECRET456", http=http, now_ms=lambda: 1)
        o = ex.Order("BTCUSDT", "BUY", 0.002, 60_000.0, 120.0, "exists", False, "buka")
        self.assertEqual(b.place(o)["_fabius"], "sudah ada (idempoten)")
        self.assertEqual([m for m, _ in calls], ["GET"])                            # tidak ada POST: order lama dipakai
        calls.clear()
        b.place(ex.Order("BTCUSDT", "BUY", 0.002, 60_000.0, 120.0, "fxnew", True, "buka"))
        self.assertEqual([m for m, _ in calls], ["GET", "POST"])

        def boom(method, url, headers):
            raise OSError("SECRET456 KEY123 bocor?")
        with self.assertRaises(vb.VenueError) as cm:
            vb.BinanceFutures("testnet", key="KEY123", secret="SECRET456", http=boom, now_ms=lambda: 1).positions()
        self.assertNotIn("SECRET456", str(cm.exception))
        self.assertNotIn("KEY123", str(cm.exception))


class FakeChain:
    def __init__(self, locked, committed):
        self.locked, self.committed = locked, committed

    def locked_at(self, committer, bot, spec):
        return self.locked

    def get_commit(self, cid):
        c = self.committed
        return {"committer": "0x" + ("11" * 20 if c else "00" * 20), "committedAt": c or 0}


class KertasTests(unittest.TestCase):
    def tick(self, date, asof, targets):
        return {"type": "tick", "asof": asof, "asof_date": date, "targets": targets, "h": "0x" + date.replace("-", "") * 4}

    def test_one_step_measures_tracking_against_the_paper_return(self):
        a, b = "BTCUSDT", "ETHUSDT"
        bar = 1_790_899_200_000
        closes = {(a, bar): 100.0, (b, bar): 100.0, (a, bar + ke.DAY_MS): 110.0, (b, bar + ke.DAY_MS): 90.0}
        filt = {s: {"step": 0.001, "min_qty": 0.001, "min_notional": 5.0} for s in (a, b)}
        rec = ke.step(None, self.tick("2026-10-02", bar, {a: 0.5, b: 0.5}), {}, venue="aster", bot="B1-TREND", modal=1000.0, jadwal="komit",
                      commit_s=bar // 1000 + 86_400 + 31_500, filters=filt, px_exec=lambda s, t: 105.0 if s == a else 95.0,
                      close=lambda s, t: closes[(s, t)])
        self.assertEqual(rec["status"], "DIEKSEKUSI")
        self.assertEqual(len(rec["orders"]), 2)
        self.assertEqual(rec["exec_utc"], "2026-10-03T08:47:00Z")
        # paper: 0,5 x 10 % + 0,5 x -10 % - turnover 1 x 7 bps; kertas beli A di 105 (naik ke 110) dan B di 95 (turun ke 90)
        self.assertAlmostEqual(rec["ret_paper"], -0.0007)
        self.assertAlmostEqual(rec["tracking_bps"], (rec["ret_kertas"] - rec["ret_paper"]) * 1e4, places=3)
        self.assertGreater(rec["geser_harga_bps"], 400)                              # 105 vs 100 dan 95 vs 100 = 500 bps
        self.assertGreaterEqual(rec["kas"], 0.0)

    def test_no_commit_is_tunda_and_before_lock_is_recorded_not_executed(self):
        tk = self.tick("2026-10-02", 1_790_899_200_000, {"BTCUSDT": 1.0})
        with self.assertRaises(ke.Tunda):
            ke.commit_time(tk, "B1-TREND", FakeChain(locked=1, committed=None), "0x" + "cc" * 20)
        self.assertIsNone(ke.commit_time(tk, "B1-TREND", FakeChain(locked=0, committed=None), "0x" + "cc" * 20))
        rec = ke.step(None, tk, {}, venue="aster", bot="B1-TREND", modal=10.0, jadwal="komit", commit_s=None, filters={},
                      px_exec=lambda s, t: 1 / 0, close=lambda s, t: 1 / 0)
        self.assertEqual((rec["status"], rec["orders"], rec["ekuitas"]), ("SEBELUM_KUNCI", [], 10.0))

    def test_run_appends_once_stops_at_missing_data_and_verify_catches_tampering(self):
        tmp = tempfile.mkdtemp()
        try:
            led = os.path.join(tmp, "paper")
            os.makedirs(led)
            recs = []
            for date, asof in (("2026-10-01", 1_790_812_800_000), ("2026-10-02", 1_790_899_200_000)):
                recs.append(ledger.seal({"type": "tick", "asof": asof, "asof_date": date, "targets": {"BTCUSDT": 1.0}}, ledger.head(recs)))
            with open(os.path.join(led, "B1-TREND.jsonl"), "w", encoding="utf-8") as f:
                for r in recs:
                    f.write(json.dumps(r) + "\n")

            def commit_time(tk, bot, cv, committer):
                if tk["asof_date"] == "2026-10-01":
                    return None
                raise ke.Tunda("komit belum ada")

            with mock.patch.object(ke, "LEDGER", led), mock.patch.object(ke, "OUT", os.path.join(tmp, "kertas")), \
                 mock.patch.object(ke, "Closes", lambda uni: type("C", (), {"at": lambda self, s, t: 1 / 0})()), mock.patch.object(ke, "commit_time", commit_time), \
                 mock.patch.object(ke, "venue_filters", lambda v, uni: {}):
                logs = []
                n1 = ke.run(["aster"], ["B1-TREND"], None, "0xc", log=logs.append)
                n2 = ke.run(["aster"], ["B1-TREND"], None, "0xc", log=logs.append)
                path = ke.path_of("aster", "B1-TREND", 10.0, "komit")
                got = ledger.load(path)
            self.assertEqual((n1, n2), (len(ke.MODALS) * len(ke.JADWAL), 0))          # tick 10-01 dicatat sekali; 10-02 TUNDA, tidak dilompati
            self.assertEqual([r["status"] for r in got], ["SEBELUM_KUNCI"])
            self.assertTrue(any("TUNDA" in x for x in logs))
            self.assertEqual(ke.verify(got), [])
            self.assertTrue(ke.verify([dict(got[0], kas=-1.0)]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

"""F-D116 (usulan r4 "slot posisi"): maks 5 posisi, ukuran dikunci (margin 3-5 % x leverage 1-5x menurut keyakinan), tutup hanya oleh SL / TP /
aturan keluar bot / rem rugi, jeda 1 siklus sesudah tutup, ganti bot tidak menutup posisi; replay memakai aturan terkunci (`meja2.arah`)."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "tools"), ROOT]

import meja                                                         # noqa: E402
import meja_replay as mr                                            # noqa: E402
import meja_slot as ms                                              # noqa: E402

DAY = 86_400


def kand(a, arah=1, c=0.0, atr=0.05, bot="B1-TREND", skor=1.0):
    return {"aset": a, "arah": arah, "bot": bot, "skor": skor, "atr": atr, "uni": [a], "c": c}


def tidak(pos):
    return False


class SizingTests(unittest.TestCase):
    def test_margin_and_leverage_scale_with_confidence_within_the_caps(self):
        self.assertEqual(ms.ukuran(0.0, "B1-TREND", 0.05), {"margin": 0.03, "leverage": 1.0, "notional": 0.03, "stop": True})
        self.assertEqual(ms.ukuran(1.0, "B1-TREND", 0.05), {"margin": 0.05, "leverage": 5.0, "notional": 0.25, "stop": True})
        self.assertEqual(ms.ukuran(0.5, "B1-TREND", 0.05)["leverage"], 3.0)
        self.assertEqual(ms.ukuran(1.0, "B1-TREND", 0.2)["leverage"], 2.5)                    # SL 20 % <= separuh jarak likuidasi 1/L
        self.assertEqual(ms.ukuran(1.0, "B4-LISTING-FADE", 0.3), {"margin": 0.02, "leverage": 1.0, "notional": 0.02, "stop": False})

    def test_confidence_runs_from_the_instrument_threshold_to_unanimous(self):
        self.assertEqual(ms.keyakinan(2.0, 2.0, 5), 0.0)
        self.assertEqual(ms.keyakinan(1.0, 2.0, 5), 0.0)
        self.assertEqual(ms.keyakinan(3.5, 2.0, 5), 0.5)
        self.assertEqual(ms.keyakinan(5.0, 2.0, 5), 1.0)

    def test_candidates_come_from_rule_targets_in_score_order(self):
        rec = {"bot": "B2-RS", "aktif": ["a", "b", "c", "d", "e"], "ambang": {"ambang_instrumen": 2.0}, "veto": ["X"],
               "instrumen": ["A", "B", "C", "X"], "skor_instrumen": {"A": 2.5, "B": 4.0, "C": 3.0},
               "target": {"A": {"w": 0.1}, "B": {"w": -0.1}, "C": {"w": 0.0}}}
        k = ms.kandidat(rec, lambda a: 0.04)
        self.assertEqual([(x["aset"], x["arah"]) for x in k], [("B", -1), ("A", 1)])           # C datar oleh aturan -> bukan kandidat
        self.assertEqual(k[0]["uni"], ["A", "B", "C"])                                         # universe aturan tanpa veto
        self.assertAlmostEqual(k[0]["c"], 2 / 3)


class StepTests(unittest.TestCase):
    def setUp(self):
        self.b = ms.buku_baru()

    def test_fills_five_slots_in_order_and_never_closes_old_positions_for_new_signals(self):
        h = {a: 100.0 for a in "ABCDEFG"}
        f = ms.langkah(self.b, 300, h, [kand(a) for a in "ABCDEFG"], tidak, False)
        self.assertEqual([x["aset"] for x in f], list("ABCDE"))
        f = ms.langkah(self.b, 600, h, [kand("F", c=1.0), kand("G")], tidak, False)            # sinyal baru, slot penuh
        self.assertEqual(f, [])
        self.assertEqual(sorted(self.b["posisi"]), list("ABCDE"))

    def test_size_stays_locked_while_the_price_moves(self):
        ms.langkah(self.b, 300, {"A": 100.0}, [kand("A")], tidak, False)
        qty = self.b["posisi"]["A"]["qty"]
        self.assertEqual(ms.langkah(self.b, 600, {"A": 104.0}, [kand("A", c=1.0)], tidak, False), [])
        self.assertEqual(self.b["posisi"]["A"]["qty"], qty)

    def test_stop_loss_take_profit_and_rule_exit_close_then_the_book_pauses_one_cycle(self):
        ms.langkah(self.b, 300, {"A": 100.0, "B": 100.0, "C": 100.0}, [kand("A"), kand("B", arah=-1), kand("C")], tidak, False)
        self.assertAlmostEqual(self.b["posisi"]["A"]["sl"], 95.0)                               # 1 x ATR 5 %
        self.assertAlmostEqual(self.b["posisi"]["A"]["tp"], 110.0)                              # 2 x ATR
        self.assertAlmostEqual(self.b["posisi"]["B"]["sl"], 105.0)                              # short: SL di atas
        f = ms.langkah(self.b, 600, {"A": 94.0, "B": 89.0, "C": 100.0, "D": 100.0}, [kand("D")], lambda pos: pos["aset"] == "C", False)
        self.assertEqual({x["aset"]: x["alasan"] for x in f}, {"A": "SL", "B": "TP", "C": "exit rule B1-TREND"})
        self.assertNotIn("D", self.b["posisi"])                                                # siklus yang menutup tidak membuka
        f = ms.langkah(self.b, 900, {"D": 100.0}, [kand("D")], tidak, False)
        self.assertEqual([(x["aset"], x["alasan"]) for x in f], [("D", "open")])                # 5 menit sesudah tutup: boleh

    def test_a_bot_switch_keeps_old_positions_and_tags_new_ones_with_the_new_bot(self):
        ms.langkah(self.b, 300, {"A": 100.0}, [kand("A", bot="B1-TREND")], tidak, False)
        ms.langkah(self.b, 600, {"A": 100.0, "B": 100.0}, [kand("B", bot="B2-RS")], tidak, False)
        self.assertEqual({a: p["bot"] for a, p in self.b["posisi"].items()}, {"A": "B1-TREND", "B": "B2-RS"})

    def test_the_daily_loss_brake_closes_everything_and_opens_nothing(self):
        ms.langkah(self.b, 300, {"A": 100.0, "B": 100.0}, [kand("A"), kand("B")], tidak, False)
        f = ms.langkah(self.b, 600, {"A": 100.0, "B": 100.0, "C": 100.0}, [kand("C")], tidak, True)
        self.assertEqual({x["alasan"] for x in f}, {"daily loss brake"})
        self.assertEqual(self.b["posisi"], {})

    def test_equity_is_capital_plus_price_moves_minus_fees(self):
        ms.langkah(self.b, 300, {"A": 100.0}, [kand("A", c=1.0)], tidak, False)
        qty = self.b["posisi"]["A"]["qty"]
        self.assertAlmostEqual(qty * 100.0, 0.25 * 10_000)                                     # 5 % x 5x
        ms.langkah(self.b, 600, {"A": 120.0}, [], tidak, False)                                 # TP 110 tersentuh pada harga siklus 120
        self.assertEqual(self.b["posisi"], {})
        self.assertAlmostEqual(self.b["saldo"], 10_000 + qty * 20 - meja.PARAMS["fee"] * qty * (100 + 120))
        self.assertEqual(self.b["n_trade"], 2)


class FakeStore:
    """Pengganti `CandleVision`: SOL naik 100 hari lalu candle hari terakhir jatuh -> B1-TREND (long bila c > c 60 hari lalu) jadi datar."""
    def __init__(self, t_akhir, jatuh=True):
        d0 = (t_akhir // DAY - 100) * DAY * 1000
        rows = [(d0 + i * DAY * 1000, 100 + i, 101 + i, 99 + i, 100 + i, 5e6) for i in range(100)]
        if jatuh:
            rows[-1] = (rows[-1][0], 199, 199, 40, 40.0, 5e6)
        self._rows = {"SOLUSDT": rows}
        self.mulai = d0 - 30 * DAY * 1000

    def rows(self, a):
        return self._rows.get(a, [])


class SlotReplayTests(unittest.TestCase):
    def rec(self, t):
        return {"siklus": t, "bot": "B1-TREND", "dasar": "dominant bot", "aktif": ["a", "b", "c"], "ambang": {"ambang_instrumen": 1.2},
                "instrumen": ["SOLUSDT"], "veto": [], "skor_instrumen": {"SOLUSDT": 2.0}, "target": {"SOLUSDT": {"w": 0.2, "k": 1.0}},
                "isi": [], "ekuitas": 10_000.0}

    def test_the_locked_bot_rule_closes_a_position_when_a_new_daily_candle_ends_its_signal(self):
        t_hari2 = 1_791_244_800                                                                 # 00:00 UTC
        recs = [self.rec(t_hari2 - 600), self.rec(t_hari2 - 300), self.rec(t_hari2)]
        harga = {r["siklus"]: {"SOLUSDT": 150.0} for r in recs}
        x = mr.replay_slot(recs, harga, FakeStore(t_hari2))
        alasan = [(f["aset"], f["alasan"]) for _, fs in x["kirim"] for f in fs]
        self.assertEqual(alasan, [("SOLUSDT", "open"), ("SOLUSDT", "exit rule B1-TREND")])     # candle baru 00:00: 40 < 60 hari lalu -> datar
        self.assertEqual(x["tutup_per_alasan"], {"aturan keluar bot": 1})
        y = mr.replay_slot(recs, harga, FakeStore(t_hari2, jatuh=False))
        self.assertEqual([f["alasan"] for _, fs in y["kirim"] for f in fs], ["open"])           # tren masih naik -> tetap dipegang
        self.assertEqual(y["masih_terbuka"], 1)


    def test_a_held_asset_that_leaves_the_price_universe_keeps_its_last_price_and_is_counted(self):
        t = 1_791_200_100
        recs = [self.rec(t), dict(self.rec(t + 300), target={}), dict(self.rec(t + 600), target={})]
        harga = {t: {"SOLUSDT": 150.0}, t + 300: {"XUSDT": 1.0}, t + 600: {"SOLUSDT": 140.0}}
        x = mr.replay_slot(recs, harga, FakeStore(t, jatuh=False))
        self.assertEqual(x["siklus_posisi_tanpa_harga"], 1)
        self.assertAlmostEqual(x["seri"][1][1], x["seri"][0][1])                                # siklus tanpa harga: dinilai di harga terakhir
        self.assertEqual([f["alasan"] for _, fs in x["kirim"] for f in fs], ["open", "SL"])      # SL tetap jalan saat harga kembali


if __name__ == "__main__":
    unittest.main()

"""Rincian paket sinyal (engine/rincian.py): masuk, level keluar, jadwal - diturunkan dari aturan bot, tidak pernah berbeda dari tick yang dikomit."""
import os
import sys
import unittest

from engine import data, ledger, rincian
from engine.spec import SPECS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DAY = 86_400_000
T0 = 1_780_000_000_000 - 1_780_000_000_000 % DAY


def series(closes):
    return tuple(T0 + i * DAY for i in range(len(closes))), tuple(closes)


class B1Tests(unittest.TestCase):
    def setUp(self):
        n = 5
        self.n = n
        # turun 8 bar lalu naik: run long dimulai pada bar pertama yang penutupannya > penutupan n bar sebelumnya
        self.c = [100 - i for i in range(8)] + [93 + 3 * i for i in range(10)]
        self.t, _ = series(self.c)

    def test_entry_is_the_close_of_the_first_bar_of_the_current_long_run_and_exit_levels_are_already_known(self):
        i = len(self.c) - 1
        d = rincian.b1_aset(self.t, self.c, self.t[i], self.n, horizon=3)
        self.assertEqual(d["sisi"], "LONG")
        s = next(k for k in range(self.n, i + 1) if all(self.c[j] > self.c[j - self.n] for j in range(k, i + 1)))
        self.assertEqual((d["masuk"]["harga"], d["masuk"]["hari"]), (self.c[s], i - s))
        self.assertAlmostEqual(d["masuk"]["pnl"], self.c[i] / self.c[s] - 1)
        self.assertEqual(d["keluar_berikut"]["level"], self.c[i + 1 - self.n])                       # bar besok: dibanding penutupan n-1 bar lalu
        self.assertEqual([x["level"] for x in d["jadwal_keluar"]], [self.c[i + j - self.n] for j in (1, 2, 3)])

    def test_a_flat_asset_says_at_what_close_it_would_enter(self):
        i = 7                                                                                     # masih turun
        d = rincian.b1_aset(self.t, self.c, self.t[i], self.n)
        self.assertEqual(d["sisi"], "FLAT")
        self.assertNotIn("masuk", d)
        self.assertEqual(d["masuk_bila"]["di_atas"], self.c[i + 1 - self.n])

    def test_changes_vs_previous_bar(self):
        ch = rincian.perubahan({"A": 0.5, "B": 0.5}, {"B": 0.5, "C": 0.5})
        self.assertEqual(ch, {"masuk": ["A"], "keluar": ["C"], "tetap": ["B"]})

    def test_the_package_never_contradicts_the_committed_b1_ticks_and_states_there_is_no_tp(self):
        s = SPECS["B1-TREND"]
        md = data.load_csv_dir(os.path.join(ROOT, "ledger", "bars"), list(s.universe))
        ser = {a: (md.perp[a].t, md.perp[a].c) for a in md.perp}
        ticks = [r for r in ledger.load(os.path.join(ROOT, "ledger", "paper", "B1-TREND.jsonl")) if r.get("type") == "tick"]
        self.assertTrue(ticks)
        for tk in ticks:
            r = rincian.rincian("B1-TREND", s.metode, s.param, tk["targets"], None, tk["asof"], ser)
            for a in s.universe:
                if a in ser:
                    held = abs(float(tk["targets"].get(a, 0.0))) > 1e-12
                    self.assertEqual(r["aset"][a]["sisi"] == "LONG", held, (tk["asof_date"], a))
            self.assertIsNone(r["tp"])
            self.assertIsNone(r["sl"])


class GateDetailTests(unittest.TestCase):
    def test_the_bought_package_carries_entry_and_exit_details_and_the_message_shows_them(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import x402_sinyal as xs
        d = xs.Data(ROOT)
        led = d.ledgers()
        bar = [r["asof_date"] for r in led["B1-TREND"] if r.get("type") == "tick"][-1]
        p = xs.package(led, "B1-TREND", bar, d.cfg(), None, None, d.series("B1-TREND"))
        self.assertTrue(p["rincian"]["aset"])
        self.assertTrue(all("keluar_berikut" in x for x in p["rincian"]["aset"].values()))
        msg = xs.fmt_package(p)
        self.assertIn("exit next bar if close <= level", msg)
        self.assertIn("No TP/SL outside the rule", msg)
        self.assertEqual(p["rincian"]["aturan_en"], xs.RULE_EN["B1-TREND"])


if __name__ == "__main__":
    unittest.main()

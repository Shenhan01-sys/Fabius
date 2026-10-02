"""Perbandingan REST vs Vision (tools/rest_vs_vision.py): logika pasangan dan vonis diuji tanpa jaringan."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import rest_vs_vision as rv                                        # noqa: E402

D = 86_400_000
T0 = 1_790_000_000_000 // D * D


class KlineTests(unittest.TestCase):
    def test_identical_rows_are_equal(self):
        a = {T0: (1.0, 2.0, 0.5, 1.5, 10.0), T0 + D: (1.5, 2.5, 1.0, 2.0, 11.0)}
        c = rv.compare_klines(a, dict(a), T0, T0 + D)
        self.assertEqual((c["n"], c["equal"], c["diff"], c["only_csv"], c["only_rest"]), (2, 2, [], [], []))

    def test_one_field_different_is_reported_with_values(self):
        a = {T0: (1.0, 2.0, 0.5, 1.5, 10.0)}
        b = {T0: (1.0, 2.0, 0.5, 1.5000001, 10.0)}
        c = rv.compare_klines(a, b, T0, T0)
        self.assertEqual(c["equal"], 0)
        self.assertEqual(c["diff"], [(T0, "c", 1.5, 1.5000001)])

    def test_rows_outside_range_ignored_and_missing_rows_listed(self):
        a = {T0: (1.0,) * 5, T0 + D: (1.0,) * 5}
        b = {T0 + D: (1.0,) * 5, T0 + 5 * D: (9.0,) * 5}
        c = rv.compare_klines(a, b, T0, T0 + D)
        self.assertEqual((c["n"], c["only_csv"], c["only_rest"]), (1, [T0], []))


class FundingTests(unittest.TestCase):
    def test_jitter_within_tolerance_matches_and_day_sums_equal(self):
        a = [(T0, 1e-4), (T0 + 8 * 3600_000, -2e-5), (T0 + 16 * 3600_000, 3e-5)]
        b = [(T0 + 2, 1e-4), (T0 + 8 * 3600_000, -2e-5), (T0 + 16 * 3600_000 + 1, 3e-5)]
        c = rv.compare_funding(a, b, T0, T0 + 16 * 3600_000)
        self.assertEqual((c["matched"], c["rate_diff"], c["only_csv"], c["only_rest"], c["day_diff"], c["max_dt_ms"]), (3, [], [], [], [], 2))

    def test_rate_difference_and_missing_event_are_reported(self):
        a = [(T0, 1e-4), (T0 + 8 * 3600_000, -2e-5)]
        b = [(T0, 1.1e-4)]
        c = rv.compare_funding(a, b, T0, T0 + 8 * 3600_000)
        self.assertEqual(c["rate_diff"], [(T0, 1e-4, 1.1e-4)])
        self.assertEqual(c["only_csv"], [T0 + 8 * 3600_000])
        self.assertEqual(len(c["day_diff"]), 1)

    def test_event_beyond_tolerance_is_not_paired(self):
        a = [(T0, 1e-4)]
        b = [(T0 + 61_000, 1e-4)]
        c = rv.compare_funding(a, b, T0, T0)
        self.assertEqual((c["matched"], c["only_csv"], c["only_rest"]), (0, [T0], []))


class RunTests(unittest.TestCase):
    """Laporan lengkap dengan REST tiruan: beda volume dihitung terpisah dari beda HARGA (yang dicetak semua), vonis engine hanya peduli harga + funding."""

    def setUp(self):
        import tempfile
        self.dir = tempfile.mkdtemp()
        rows = [(T0 + i * D, 1.0 + i, 2.0 + i, 0.5 + i, 1.5 + i, 10.0 + i) for i in range(3)]
        for kind in ("fut", "spot"):
            with open(os.path.join(self.dir, f"{kind}_BTCUSDT_1d.csv"), "w", encoding="utf-8") as f:
                f.write("t,o,h,l,c,v\n" + "".join(",".join(repr(x) for x in r) + "\n" for r in rows))
        with open(os.path.join(self.dir, "fund_BTCUSDT.csv"), "w", encoding="utf-8") as f:
            f.write("t,rate\n" + "".join(f"{T0 + k * 8 * 3600_000},{1e-4}\n" for k in range(9)))
        self.rows = {r[0]: r[1:] for r in rows}

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def fake(self, perp_change=None, spot_change=None):
        test = self

        class FakeRest:
            calls = 0

            def klines(self, base, path, sym, t0, now_ms, limit):
                out = dict(test.rows)
                ch = perp_change if "fapi" in base else spot_change
                if ch:
                    t, i, val = ch
                    r = list(out[t])
                    r[i] = val
                    out[t] = tuple(r)
                return out

            def funding(self, sym, t0, now_ms):
                return [(T0 + k * 8 * 3600_000, 1e-4) for k in range(9)]
        return FakeRest()

    def test_volume_only_difference_keeps_engine_verdict(self):
        tot = rv.run(self.dir, ["BTCUSDT"], 0, self.fake(perp_change=(T0 + D, 4, 99.0)), T0 + 10 * D)
        self.assertEqual(tot["perp"][3], 1)
        self.assertEqual(tot["price_diffs"], 0)

    def test_price_difference_is_counted(self):
        tot = rv.run(self.dir, ["BTCUSDT"], 0, self.fake(spot_change=(T0, 3, 1.5000001)), T0 + 10 * D)
        self.assertEqual(tot["price_diffs"], 1)
        self.assertEqual(tot["fund"][0], tot["fund"][1])


if __name__ == "__main__":
    unittest.main()

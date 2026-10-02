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


if __name__ == "__main__":
    unittest.main()

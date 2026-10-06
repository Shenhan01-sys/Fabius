import dataclasses
import hashlib
import json
import math
import statistics
import unittest

from engine.bots import REGISTRY
from engine.freshness import StaleBars, assert_fresh
from engine.quality import find_gaps, missing_days
from engine.rule import RULE_METHOD
from engine.series import DAY_MS, Series, max_drawdown, pct_change, rolling_mean, rolling_std, sharpe
from engine.spec import SPECS, canon, sha0x

from .helpers import T0, mk_series


class SeriesTests(unittest.TestCase):
    def test_rolling_std_is_sample_std(self):
        x = [1.0, 4.0, 9.0, 16.0, 25.0, 36.0]
        out = rolling_std(x, 4)
        self.assertEqual(out[:3], [None, None, None])
        self.assertAlmostEqual(out[3], statistics.stdev(x[0:4]))
        self.assertAlmostEqual(out[5], statistics.stdev(x[2:6]))

    def test_rolling_none_propagates(self):
        out = rolling_mean([1.0, None, 3.0, 4.0, 5.0], 2)
        self.assertEqual(out, [None, None, None, 3.5, 4.5])

    def test_pct_change(self):
        self.assertEqual(pct_change([100.0, 110.0, None, 121.0]), [None, 0.10000000000000009, None, None])

    def test_from_rows_sorts_and_dedupes_first_wins(self):
        s = Series.from_rows([[2 * DAY_MS, 1, 1, 1, 7, 1], [0, 1, 1, 1, 5, 1], [0, 1, 1, 1, 99, 1]])
        self.assertEqual(s.t, (0, 2 * DAY_MS))
        self.assertEqual(s.c, (5.0, 7.0))

    def test_upto_and_index(self):
        s = mk_series([1.0, 2.0, 3.0, 4.0])
        self.assertEqual(len(s.upto(T0 + 2 * DAY_MS)), 3)
        self.assertEqual(s.index_at_or_before(T0 + 2 * DAY_MS + 5), 2)
        self.assertEqual(s.index_at_or_before(T0 - 1), -1)

    def test_sharpe_needs_30_and_nonzero_std(self):
        self.assertTrue(math.isnan(sharpe([0.01] * 29)))
        self.assertTrue(math.isnan(sharpe([0.01] * 40)))
        x = [0.002, 0.0] * 30
        m, sd = statistics.mean(x), statistics.stdev(x)
        self.assertAlmostEqual(sharpe(x), (m * 365) / (sd * math.sqrt(365)))

    def test_max_drawdown(self):
        self.assertAlmostEqual(max_drawdown([0.1, -0.5, 0.2]), -0.5)
        self.assertEqual(max_drawdown([0.1, 0.1]), 0.0)


class SpecTests(unittest.TestCase):
    def test_canon_order_independent_and_matches_direction_convention(self):
        self.assertEqual(canon({"b": 1, "a": 2}), '{"a":2,"b":1}')
        self.assertEqual(sha0x({"a": 2, "b": 1}), "0x" + hashlib.sha256(b'{"a":2,"b":1}').hexdigest())

    def test_param_change_makes_new_sha(self):
        sp = SPECS["B1-TREND"]
        self.assertEqual(sp.sha(), dataclasses.replace(sp).sha())
        self.assertNotEqual(sp.sha(), dataclasses.replace(sp, param=61).sha())
        self.assertNotEqual(sp.sha(), dataclasses.replace(sp, konstanta={**sp.konstanta, "long_only": False}).sha())

    def test_json_roundtrip_stable(self):
        for sp in SPECS.values():
            self.assertEqual(sha0x(json.loads(canon(sp.as_dict()))), sp.sha(), sp.bot_id)

    def test_one_method_one_parameter_and_registered(self):
        self.assertEqual(len(SPECS), 6)
        self.assertEqual(set(SPECS) | {RULE_METHOD}, set(REGISTRY))             # + mesin bot rule (P167a): satu fungsi untuk semua aturan, tanpa spec statis
        for k, sp in SPECS.items():
            self.assertEqual(sp.bot_id, k)
            self.assertTrue(sp.param_nama and sp.metode)
            self.assertNotIn(sp.param_nama, sp.konstanta, f"{k}: parameter tidak boleh juga jadi konstanta")
        self.assertEqual(len({sp.sha() for sp in SPECS.values()}), 6)


class FreshnessTests(unittest.TestCase):
    def test_unclosed_bar_rejected(self):
        s = mk_series([1.0, 2.0])
        with self.assertRaises(StaleBars):
            assert_fresh("x", s, T0 + DAY_MS + 3_600_000)          # bar ke-2 baru berjalan 1 jam

    def test_stale_rejected_fresh_ok(self):
        s = mk_series([1.0, 2.0])
        close = T0 + 2 * DAY_MS
        assert_fresh("x", s, close + 3_600_000)
        with self.assertRaises(StaleBars):
            assert_fresh("x", s, close + 13 * 3_600_000)

    def test_empty_rejected(self):
        with self.assertRaises(StaleBars):
            assert_fresh("x", mk_series([]), T0)


class QualityTests(unittest.TestCase):
    def test_find_gaps(self):
        s = mk_series([1.0] * 10, skip=[4, 5])
        g = find_gaps(s)
        self.assertEqual(len(g), 1)
        self.assertEqual(missing_days(g[0]), 2)
        self.assertEqual(find_gaps(mk_series([1.0] * 5)), [])


if __name__ == "__main__":
    unittest.main()

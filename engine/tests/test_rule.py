"""P167a (epik 12): aturan deklaratif `kind=rule` - validator tertutup, bentuk kanonik, fitur dihitung benar, kausalitas oleh konstruksi, mesin keadaan,
bobot, G5 atas parameter bernama, dan BUKTI EKUIVALENSI: B1-TREND, B6-BOUNCE, B2-RS dinyatakan ulang sebagai rule menghasilkan bobot dan PnL IDENTIK
dengan bot template (data sintetis ber-bolong + data nyata ledger/bars)."""
import contextlib
import copy
import dataclasses
import io
import json
import os
import random
import re
import shutil
import statistics
import subprocess
import time
import unittest

from engine import cli, gates, rule as R, submission
from engine.bots import REGISTRY
from engine.data import MarketData, load_csv_dir
from engine.replay import replay
from engine.series import DAY_MS, Series
from engine.spec import SPECS, BotSpec, sha0x

from .helpers import BNB, BTC, ETH, T0, md_perp, walk
from .test_gates_slots import FAST, by_gate, trending

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EX = os.path.join(ROOT, "engine", "examples", "submission.rule.example.json")
BARS = os.path.join(ROOT, "ledger", "bars")
MISSING = object()


def rule_example():
    with open(EX, encoding="utf-8") as f:
        return json.load(f)["spec"]["rule"]


def put(rule, path, value=MISSING):
    """Salinan dengan satu simpul diganti (path = tuple kunci/indeks); value=MISSING menghapus."""
    r = copy.deepcopy(rule)
    cur = r
    for k in path[:-1]:
        cur = cur[k]
    if value is MISSING:
        del cur[path[-1]]
    else:
        cur[path[-1]] = value
    return r


def spec_of(rule, universe=(BTC, ETH, BNB), bot_id="RULE-UJI"):
    probs = R.validate(rule)
    assert probs == [], probs
    return BotSpec(bot_id=bot_id, metode="metode uji", param_nama=R.PARAM_NAMA, param="x", konstanta={"rule": R.canonical(rule)},
                   universe=tuple(universe), penggaris=dict(R.PENGGARIS), template=R.RULE_METHOD)


def ohlcv(closes, t0=T0, skip=()):
    """OHLCV dengan o/h/l/v berbeda: o = c - 0,1; h = c + 0,5; l = c - 0,5; v = 100 x (hari + 1). `skip` = indeks hari yang dibolongkan."""
    rows = [[t0 + i * DAY_MS, c - 0.1, c + 0.5, c - 0.5, c, 100.0 * (i + 1)] for i, c in enumerate(closes) if i not in skip]
    return Series.from_rows(rows)


def md_of(series_by_asset):
    return MarketData(perp=dict(series_by_asset))


def feat_of(series):
    grid = list(series.t)
    return R._Feat(series, grid, {t: i for i, t in enumerate(grid)})


def cmp_(op, a, b):
    return {"cmp": op, "a": a, "b": b}


def f_(name, n=None, lag=None):
    d = {"f": name}
    if n is not None:
        d["n"] = n
    if lag is not None:
        d["lag"] = lag
    return d


def c_(x):
    return {"c": x}


def per_aset(masuk_long=None, keluar_long=None, masuk_short=None, keluar_short=None, params=None, gross=1.0, skema="sama", n=None):
    r = {"mode": "per_aset", "params": params or {}, "bobot": {"skema": skema, "gross_maks": gross}}
    if skema == "inv_vol":
        r["bobot"]["n"] = n
    for k, v in (("masuk_long", masuk_long), ("keluar_long", keluar_long), ("masuk_short", masuk_short), ("keluar_short", keluar_short)):
        if v is not None:
            r[k] = v
    return r


def peringkat(skor, kl=1, ks=1, min_aset=4, rotasi="harian", gross=2.0, params=None, skema="sama", n=None):
    r = {"mode": "peringkat", "params": params or {}, "skor": skor, "long_teratas": kl, "short_terbawah": ks, "min_aset": min_aset,
         "rotasi": rotasi, "bobot": {"skema": skema, "gross_maks": gross}}
    if skema == "inv_vol":
        r["bobot"]["n"] = n
    return r


# ================================================================ validator

class ValidatorTests(unittest.TestCase):
    def assertBad(self, rule, fragment):
        probs = R.validate(rule)
        self.assertTrue(any(fragment in p for p in probs), f"{fragment!r} tidak ada di {probs}")

    def test_the_example_rule_is_valid_and_both_modes_are_expressible(self):
        self.assertEqual(R.validate(rule_example()), [])
        self.assertEqual(R.validate(peringkat(f_("ret", 20))), [])

    def test_structure_and_vocabulary_are_closed(self):
        ex = rule_example()
        for rule, frag in (
            (put(ex, ("mode",), "acak"), "mode: harus salah satu"),
            (put(ex, ("rahasia",), 1), "field tidak dikenal untuk mode per_aset"),
            (put(ex, ("skor",), c_(1)), "field tidak dikenal untuk mode per_aset"),                 # kunci milik mode lain
            (put(ex, ("masuk_long",)), "butuh masuk_long dan/atau masuk_short"),
            (put(ex, ("keluar_short",), cmp_(">", f_("close"), c_(1))), "butuh masuk_short"),
            (put(ex, ("masuk_long",), {}), "kondisi harus objek"),
            (put(ex, ("masuk_long",), {"xor": []}), "bukan kondisi"),
            (put(ex, ("masuk_long", "and", 0, "cmp"), "=="), "perbandingan harus"),
            (put(ex, ("masuk_long", "and", 0, "a", "f"), "obv"), ".f: harus salah satu dari"),
            (put(ex, ("masuk_long", "and", 0, "a"), {"c": 1, "p": "R"}), "bukan ekspresi"),
            (put(ex, ("masuk_long", "and", 1, "a"), f_("close", 5)), "tidak punya jendela"),
            (put(ex, ("masuk_long", "and", 0, "a"), f_("rsi")), "wajib punya jendela"),
            (put(ex, ("masuk_long", "and", 0, "a"), {"f": "rsi", "n": 14, "x": 1}), "fitur hanya boleh punya f, n, lag"),
            (put(ex, ("masuk_long", "and", 0, "b"), {"op": "^", "a": c_(1), "b": c_(2)}), "operator harus"),
            (put(ex, ("masuk_long", "and", 0, "b"), {"op": "+", "a": c_(1)}), "operator harus"),
            (put(ex, ("masuk_long", "and", 0, "b"), {"fn": "abs", "args": [c_(1), c_(2)]}), "abs butuh 1..1 argumen"),
            (put(ex, ("masuk_long", "and", 0, "b"), {"fn": "min", "args": [c_(1)]}), "min butuh 2..4 argumen"),
            (put(ex, ("masuk_long", "and", 0, "b"), {"fn": "max", "args": [c_(i) for i in range(5)]}), "max butuh 2..4 argumen"),
            (put(ex, ("masuk_long", "and", 0, "b"), {"fn": "sqrt", "args": [c_(1)]}), "fungsi harus"),
            (put(ex, ("masuk_long",), {"and": [cmp_(">", c_(1), c_(0))]}), "daftar 2..4 kondisi"),
            (put(ex, ("masuk_long",), {"not": 5}), "kondisi harus objek"),
            (put(ex, ("masuk_long", "and", 0, "b", "c"), float("nan")), "angka hingga"),
            (put(ex, ("masuk_long", "and", 0, "b", "c"), 10 ** 7), "angka hingga"),
            (put(ex, ("masuk_long", "and", 0, "b", "c"), True), "angka hingga"),
        ):
            self.assertBad(rule, frag)

    def test_windows_and_lags_are_bounded_integers(self):
        ex = rule_example()
        for bad in (1, 366, 2.5, "60", True, -3, None):
            self.assertBad(put(ex, ("keluar_long", "a", "n"), bad), "jendela harus bilangan bulat dalam [2, 365]")
        for ok in (2, 365, 60.0):
            self.assertEqual(R.validate(put(ex, ("keluar_long", "a", "n"), ok)), [])
        for bad in (31, -1, 1.5, "1", True):
            self.assertBad(put(ex, ("masuk_long", "and", 1, "a"), f_("close", None, bad)), "lag harus bilangan bulat dalam [0, 30]")
        self.assertEqual(R.validate(put(ex, ("masuk_long", "and", 1, "a"), f_("close", None, 30))), [])

    def test_named_parameters_must_exist_be_used_nonzero_and_fit_where_they_are_used(self):
        ex = rule_example()
        self.assertBad(put(ex, ("masuk_long", "and", 0, "a", "n"), {"p": "Q"}), "tidak dideklarasikan")
        self.assertBad(put(ex, ("params",), {"R": 14, "T": 100, "Z": 3}), "parameter tidak dipakai")                     # yatim tidak bisa diuji G5
        for bad in (0, float("nan"), float("inf"), True, "7", None, [], 10 ** 7):
            self.assertBad(put(ex, ("params", "R"), bad), "params.R")
        self.assertBad(put(ex, ("params",), {f"p{i}": 1 for i in range(7)}), "paling banyak 6")
        self.assertBad(put(ex, ("params",), {"1x": 1, "R": 14, "T": 100}), "nama parameter tidak valid")
        for bad in (2.5, 1, 400):                                                                        # dipakai sebagai jendela
            self.assertBad(put(ex, ("params", "R"), bad), "dipakai sebagai jendela")
        lag_rule = put(ex, ("masuk_long", "and", 1, "a"), f_("close", None, {"p": "R"}))
        self.assertEqual(R.validate(lag_rule), [])                                                       # R = 14 sah sebagai lag
        self.assertBad(put(lag_rule, ("params", "R"), 40), "dipakai sebagai")                            # tetapi 40 > lag maks 30 (dan sah sebagai jendela)

    def test_weighting_scheme_and_gross_caps(self):
        ex = rule_example()
        self.assertBad(put(ex, ("bobot",), None), "wajib objek")
        self.assertBad(put(ex, ("bobot", "skema"), "kelly"), "skema: harus salah satu")
        for g in (0, -1, 1.01, True, float("nan")):
            self.assertBad(put(ex, ("bobot", "gross_maks"), g), "gross_maks")
        self.assertBad(put(ex, ("bobot", "n"), 20), "hanya untuk inv_vol")
        inv = put(put(ex, ("bobot", "skema"), "inv_vol"), ("bobot", "n"), 30)
        self.assertEqual(R.validate(inv), [])
        self.assertBad(put(inv, ("bobot", "n")), "wajib punya jendela volatilitas")
        self.assertBad(put(inv, ("bobot", "n"), 1), "jendela harus bilangan bulat")
        self.assertBad(put(ex, ("bobot", "x"), 1), "hanya skema, gross_maks, n")
        base = peringkat(f_("ret", 20))
        self.assertEqual(R.validate(put(base, ("bobot", "gross_maks"), 2.0)), [])
        self.assertBad(put(base, ("bobot", "gross_maks"), 2.01), "gross_maks")                      # peringkat <= 2,0 (1,0 per kaki)

    def test_ranking_mode_rules(self):
        base = peringkat(f_("ret", 20))
        for rule, frag in (
            (put(base, ("skor",)), "skor: wajib"),
            (put(base, ("long_teratas",), 9), "long_teratas: harus bilangan bulat 0..8"),
            (put(base, ("short_terbawah",), -1), "short_terbawah"),
            (put(put(base, ("long_teratas",), 0), ("short_terbawah",), 0), "butuh long_teratas dan/atau short_terbawah >= 1"),
            (put(base, ("min_aset",), 1), "min_aset: harus bilangan bulat 2..40"),
            (put(put(base, ("long_teratas",), 3), ("short_terbawah",), 3), "minimal long_teratas + short_terbawah (6)"),
            (put(base, ("rotasi",), "mingguan"), "rotasi: harus salah satu"),
            (put(base, ("rotasi",)), "rotasi: harus salah satu"),
            (put(base, ("masuk_long",), cmp_(">", c_(1), c_(0))), "field tidak dikenal untuk mode peringkat"),
        ):
            self.assertBad(rule, frag)
        self.assertEqual(R.validate_universe(base, 3), ["spec.rule.min_aset: 4 lebih besar dari jumlah aset universe (3)"])
        self.assertEqual(R.validate_universe(base, 4), [])
        self.assertEqual(R.validate_universe(rule_example(), 1), [])

    def test_size_depth_and_work_budget_are_bounded(self):
        leaf = cmp_(">", f_("close"), c_(1))                                                              # 3 simpul
        grp = {"and": [leaf, leaf, leaf, leaf]}                                                          # 13
        big = {"and": [grp, grp, grp, grp]}                                                              # 53
        self.assertEqual(R.validate(per_aset(big)), [])
        self.assertBad(per_aset({"or": [big, big]}), "lebih dari 64 simpul")
        deep = leaf
        for _ in range(8):
            deep = {"not": deep}
        self.assertBad(per_aset(deep), "tingkat bersarang")                                              # not x 8 + cmp + ekspresi = 10 tingkat
        self.assertEqual(R.validate(per_aset({"not": {"not": leaf}})), [])
        wins = [cmp_(">", f_("sma", w), c_(1)) for w in (365, 364, 363, 362, 361)]
        self.assertEqual(R.validate(per_aset({"and": wins[:4]})), [])                                    # 1454 <= 1500
        self.assertBad(per_aset({"or": [{"and": wins[:4]}, wins[4]]}), "anggaran kerja jendela")         # 1815 > 1500
        same = [cmp_(">", f_("sma", 365), c_(i)) for i in range(4)]                                      # jendela SAMA dihitung sekali
        self.assertEqual(R.validate(per_aset({"and": same})), [])

    def test_hostile_values_at_every_leaf_never_raise_and_never_echo_raw_text(self):
        hostile = [None, True, False, 0, -1, 10 ** 400, float("inf"), float("nan"), "", " ", "x" * 5000, [], {}, [1], {"a": 1}, "\x1b[2J",
                   {"p": 5}, {"p": "zz"}, {"f": {"x": 1}}, {"c": "1"}, "‮", "a\ud800b"]

        def paths(node, prefix=()):
            if isinstance(node, dict):
                for k, v in node.items():
                    yield prefix + (k,)
                    yield from paths(v, prefix + (k,))
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    yield prefix + (i,)
                    yield from paths(v, prefix + (i,))
        n = 0
        for base in (rule_example(), peringkat(f_("ret", {"p": "L"}), params={"L": 20}), put(rule_example(), ("bobot", "skema"), "inv_vol")):
            for p in paths(base):
                for h in hostile:
                    probs = R.validate(put(base, p, h))
                    self.assertIsInstance(probs, list, (p, h))
                    self.assertLessEqual(len(probs), 30)
                    for m in probs:
                        self.assertNotIn("\x1b", m)
                        self.assertLessEqual(len(m), 240, m)
                    n += 1
        self.assertGreater(n, 800)
        for notdict in (None, 5, "x", [], [{}]):
            self.assertTrue(R.validate(notdict))

    def test_absurd_nesting_is_rejected_without_recursing_forever(self):
        node = cmp_(">", c_(1), c_(0))
        for _ in range(5000):
            node = {"not": node}
        t0 = time.time()
        self.assertBad(per_aset(node), "tingkat bersarang")
        self.assertLess(time.time() - t0, 2.0)
        expr = c_(1)
        for _ in range(5000):
            expr = {"fn": "abs", "args": [expr]}
        self.assertBad(per_aset(cmp_(">", expr, c_(0))), "tingkat bersarang")


# ================================================================ bentuk kanonik + kelompok plateau

class CanonicalTests(unittest.TestCase):
    def test_two_and_two_point_zero_are_the_same_rule_for_sha_and_fingerprint(self):
        a = rule_example()
        b = copy.deepcopy(a)
        b["params"] = {"R": 14.0, "T": 100.0}
        b["masuk_long"]["and"][0]["b"] = c_(30.0)
        b["bobot"]["gross_maks"] = 1
        self.assertEqual(R.validate(b), [])
        self.assertEqual(R.canonical(a), R.canonical(b))
        self.assertEqual(spec_of(a).fingerprint(), spec_of(b).fingerprint())
        self.assertEqual(sha0x(R.canonical(a)), sha0x(R.canonical(b)))
        ca = R.canonical(b)
        self.assertIsInstance(ca["params"]["R"], int)                                                    # dipakai sebagai jendela: bulat
        self.assertIsInstance(ca["masuk_long"]["and"][0]["b"]["c"], float)
        self.assertIsInstance(ca["bobot"]["gross_maks"], float)
        self.assertNotEqual(spec_of(a).fingerprint(), spec_of(put(a, ("params", "R"), 15)).fingerprint())
        self.assertNotEqual(spec_of(a).fingerprint(), spec_of(a, universe=(BTC, ETH)).fingerprint())

    def test_float_typed_parameters_stay_float_and_null_keys_are_dropped(self):
        r = per_aset(cmp_("<", f_("zscore", 10), {"op": "*", "a": {"p": "Z"}, "b": c_(-1)}), params={"Z": 2})
        self.assertEqual(R.validate(r), [])
        self.assertEqual(R.canonical(r)["params"], {"Z": 2.0})
        self.assertIsInstance(R.canonical(r)["params"]["Z"], float)
        self.assertEqual(R.param_jenis(r), {})
        with_null = put(rule_example(), ("keluar_short",), None)
        self.assertEqual(R.validate(with_null), [])
        self.assertNotIn("keluar_short", R.canonical(with_null))
        pr = R.canonical(peringkat(f_("ret", 20), kl=2, ks=0))
        self.assertEqual((pr["long_teratas"], pr["short_terbawah"]), (2, 0))
        self.assertEqual(R.canonical({"mode": "peringkat", "skor": f_("ret", 20), "min_aset": 4, "rotasi": "harian", "long_teratas": 1,
                                      "bobot": {"skema": "sama", "gross_maks": 1.0}})["short_terbawah"], 0)

    def test_plateau_groups_one_per_parameter_plus_all_together_with_types_respected(self):
        g = dict(R.kelompok_plateau(rule_example(), (0.5, 0.75, 1.25, 1.5)))
        self.assertEqual(list(g), ["R", "T", "semua"])
        self.assertEqual([lab for lab, _ in g["R"]], ["7", "10", "18", "21"])                              # 14 x f, bulat (pembulatan bankir seperti G5 template)
        self.assertEqual([lab for lab, _ in g["T"]], ["50", "75", "125", "150"])
        self.assertEqual([r["params"] for _, r in g["semua"]][0], {"R": 7, "T": 50})
        self.assertTrue(all(isinstance(v, int) for _, r in g["R"] for v in r["params"].values()))
        solo = per_aset(cmp_(">", f_("ret", {"p": "N"}), c_(0)), params={"N": 20})
        one = R.kelompok_plateau(solo, (0.5, 0.75, 1.25, 1.5))
        self.assertEqual([n for n, _ in one], ["N"])                                                       # satu parameter: tanpa kelompok 'semua'
        self.assertEqual(R.kelompok_plateau(per_aset(cmp_(">", f_("ret", 20), c_(0))), (0.5, 1.5)), [])      # tanpa parameter bernama: tidak ada kelompok
        lag = per_aset(cmp_(">", f_("close", None, {"p": "G"}), c_(0)), params={"G": 2})
        self.assertEqual([lab for lab, _ in dict(R.kelompok_plateau(lag, (0.5, 0.75, 1.25, 1.5)))["G"]], ["1", "3"])   # varian sama dengan dasar dibuang
        flt = per_aset(cmp_("<", f_("zscore", 10), {"op": "*", "a": {"p": "Z"}, "b": c_(-1)}), params={"Z": 2.0})
        self.assertEqual([lab for lab, _ in dict(R.kelompok_plateau(flt, (0.5, 1.5)))["Z"]], ["1", "3"])
        self.assertEqual(R.varian_g5(rule_example(), 4), 12)
        self.assertEqual(R.varian_g5(solo, 4), 4)
        self.assertEqual(R.varian_g5(per_aset(cmp_(">", f_("ret", 20), c_(0))), 4), 0)


# ================================================================ fitur

C10 = [10.0, 11.0, 12.0, 11.0, 13.0, 14.0, 12.0, 15.0, 16.0, 18.0]


def near(test, got, want):
    test.assertEqual(len(got), len(want))
    for i, (g, w) in enumerate(zip(got, want)):
        if w is None:
            test.assertIsNone(g, f"i={i}")
        else:
            test.assertIsNotNone(g, f"i={i}")
            test.assertAlmostEqual(g, w, places=9, msg=f"i={i}")


class FeatureTests(unittest.TestCase):
    """Setiap fitur dibandingkan dengan hitungan tangan INDEPENDEN (bukan salinan kode mesin)."""

    def setUp(self):
        self.s = ohlcv(C10)
        self.ft = feat_of(self.s)
        self.c = C10
        self.h = [x + 0.5 for x in C10]
        self.l = [x - 0.5 for x in C10]
        self.v = [100.0 * (i + 1) for i in range(10)]

    def test_price_columns_and_lag_shift_backwards_only(self):
        for f, want in (("close", self.c), ("high", self.h), ("low", self.l), ("volume", self.v), ("open", [x - 0.1 for x in self.c])):
            near(self, self.ft.get(f, 0), want)
        params = {}
        near(self, R._eval(f_("close", None, 3), self.ft, params), [None] * 3 + self.c[:7])
        near(self, R._eval(f_("sma", 3, 2), self.ft, params), [None] * 4 + [statistics.mean(self.c[i - 2:i + 1]) for i in range(2, 8)])
        near(self, R._eval(f_("close", None, 30), self.ft, params), [None] * 10)                           # lag melewati seluruh riwayat

    def test_return_sma_std_zscore(self):
        n = 3
        near(self, self.ft.get("ret", n), [None] * n + [self.c[i] / self.c[i - n] - 1.0 for i in range(n, 10)])
        near(self, self.ft.get("sma", n), [None] * 2 + [statistics.mean(self.c[i - 2:i + 1]) for i in range(2, 10)])
        near(self, self.ft.get("std", n), [None] * 2 + [statistics.stdev(self.c[i - 2:i + 1]) for i in range(2, 10)])         # ddof = 1
        near(self, self.ft.get("zscore", n),
             [None] * 2 + [(self.c[i] - statistics.mean(self.c[i - 2:i + 1])) / statistics.stdev(self.c[i - 2:i + 1]) for i in range(2, 10)])

    def test_ema_rsi_atr(self):
        e, want = statistics.mean(self.c[:3]), [None] * 2
        want.append(e)
        for i in range(3, 10):
            e = 0.5 * self.c[i] + 0.5 * e                                                                  # alpha = 2/(3+1)
            want.append(e)
        near(self, self.ft.get("ema", 3), want)
        rsi = [None] * 3
        for i in range(3, 10):
            d = [self.c[j] - self.c[j - 1] for j in range(i - 2, i + 1)]
            g, l = sum(x for x in d if x > 0) / 3, sum(-x for x in d if x < 0) / 3
            rsi.append(100.0 if l == 0 else 100.0 - 100.0 / (1.0 + g / l))
        near(self, self.ft.get("rsi", 3), rsi)
        tr = [None] + [max(self.h[i] - self.l[i], abs(self.h[i] - self.c[i - 1]), abs(self.l[i] - self.c[i - 1])) for i in range(1, 10)]
        near(self, self.ft.get("atr_pct", 3), [None] * 3 + [100.0 * statistics.mean(tr[i - 2:i + 1]) / self.c[i] for i in range(3, 10)])

    def test_extremes_volume_ratio_and_drawdown(self):
        near(self, self.ft.get("max_high", 3), [None] * 2 + [max(self.h[i - 2:i + 1]) for i in range(2, 10)])
        near(self, self.ft.get("min_low", 3), [None] * 2 + [min(self.l[i - 2:i + 1]) for i in range(2, 10)])
        near(self, self.ft.get("vol_ratio", 3), [None] * 3 + [self.v[i] / statistics.mean(self.v[i - 3:i]) for i in range(3, 10)])   # n bar SEBELUM hari ini
        near(self, self.ft.get("drawdown", 3), [None] * 2 + [self.c[i] / max(self.c[i - 2:i + 1]) - 1.0 for i in range(2, 10)])

    def test_rsi_of_a_flat_window_is_undefined_not_fifty(self):
        ft = feat_of(ohlcv([5.0] * 8))
        near(self, ft.get("rsi", 3), [None] * 8)
        up = feat_of(ohlcv([1.0, 2.0, 3.0, 4.0, 5.0]))
        near(self, up.get("rsi", 3), [None, None, None, 100.0, 100.0])

    def test_arithmetic_propagates_undefined_and_division_by_zero_is_undefined(self):
        ft, p = self.ft, {"K": 2.0}
        near(self, R._eval({"op": "/", "a": c_(1), "b": {"op": "-", "a": f_("close"), "b": f_("close")}}, ft, p), [None] * 10)
        near(self, R._eval({"op": "+", "a": f_("ret", 3), "b": c_(1)}, ft, p), [None] * 3 + [self.c[i] / self.c[i - 3] for i in range(3, 10)])
        near(self, R._eval({"op": "*", "a": {"p": "K"}, "b": f_("close")}, ft, p), [2.0 * x for x in self.c])
        near(self, R._eval({"fn": "neg", "args": [f_("close")]}, ft, p), [-x for x in self.c])
        near(self, R._eval({"fn": "abs", "args": [{"op": "-", "a": f_("close"), "b": c_(12)}]}, ft, p), [abs(x - 12) for x in self.c])
        near(self, R._eval({"fn": "min", "args": [f_("close"), c_(12), f_("open")]}, ft, p), [min(x, 12.0, x - 0.1) for x in self.c])
        near(self, R._eval({"fn": "max", "args": [f_("close"), f_("sma", 3)]}, ft, p), [None, None] + [max(self.c[i], statistics.mean(self.c[i - 2:i + 1])) for i in range(2, 10)])

    def test_holes_in_the_data_follow_the_two_conventions(self):
        """Fitur jendela memakai n bar TERAKHIR aset itu (bolong dilewati, seperti B6); `ret` memakai selisih hari-grid (seperti B1/B2)."""
        a, b = ohlcv(C10, skip=(5,)), ohlcv([20.0 + i for i in range(10)])
        grid = sorted(set(a.t) | set(b.t))
        ft = R._Feat(a, grid, {t: i for i, t in enumerate(grid)})
        self.assertIsNone(ft.get("close", 0)[5])
        own = [C10[i] for i in range(10) if i != 5]
        self.assertAlmostEqual(ft.get("sma", 3)[6], statistics.mean([C10[3], C10[4], C10[6]]))           # 3 bar terakhir yang ADA
        self.assertIsNone(ft.get("sma", 3)[5])                                                            # hari tanpa bar tak terdefinisi
        self.assertIsNone(ft.get("ret", 2)[7])                                                            # i-2 = hari bolong
        self.assertAlmostEqual(ft.get("ret", 2)[6], C10[6] / C10[4] - 1.0)
        self.assertEqual(len(own), 9)


class SizeTests(unittest.TestCase):
    def test_size_counts_nodes_depth_and_distinct_windows_of_a_valid_rule_only(self):
        self.assertEqual(R.ukuran(rule_example()), {"simpul": 10, "kedalaman": 3, "jendela": 114})         # 3 + 3 + 1 (and) + 3 (keluar); jendela rsi(14) + sma(100)
        r = per_aset({"and": [cmp_(">", f_("sma", 5), f_("sma", 5, 2)), cmp_(">", f_("rsi", 14), c_(30))]}, skema="inv_vol", n=14)
        self.assertEqual(R.ukuran(r), {"simpul": 7, "kedalaman": 3, "jendela": 33})                       # sma(5) dua kali = satu jendela + rsi(14) + volatilitas 14
        self.assertIsNone(R.ukuran(put(rule_example(), ("mode",), "acak")))
        self.assertIsNone(R.ukuran("bukan objek"))
        self.assertIsNone(R.ukuran(put(rule_example(), ("params", "R"), 1)))


# ================================================================ kausalitas oleh konstruksi

def wide_rules():
    ex = rule_example()
    return {
        "contoh": ex,
        "ema_atr": per_aset(cmp_(">", f_("ema", 5), f_("sma", 8, 2)), cmp_("<", f_("atr_pct", 4), c_(0.5)), cmp_("<", f_("drawdown", 6), c_(-0.05)),
                            cmp_(">", f_("vol_ratio", 3), c_(2))),
        "ekstrem": per_aset({"or": [cmp_(">", f_("close"), f_("max_high", 10, 1)), {"not": cmp_(">", f_("zscore", 6), c_(-1))}]},
                            masuk_short=cmp_("<", f_("close"), f_("min_low", 10, 1)), gross=1.0),
        "inv_vol": put(put(ex, ("bobot", "skema"), "inv_vol"), ("bobot", "n"), 10),
        "peringkat_harian": peringkat(f_("zscore", 6), kl=1, ks=1, min_aset=3, rotasi="harian", gross=1.0),
        "peringkat_7": peringkat({"op": "-", "a": f_("ret", 5), "b": f_("ret", 10)}, kl=1, ks=1, min_aset=3, rotasi="tujuh_sub_buku"),
        "peringkat_inv": peringkat(f_("rsi", 6), kl=1, ks=1, min_aset=3, skema="inv_vol", n=8),
    }


def random_md(seed, n=260):
    rnd = random.Random(seed)
    out = {}
    for k, a in enumerate((BTC, ETH, BNB, "SOLUSDT")):
        p, rows, start = 100.0, [], 0 if k < 3 else 40                                   # aset ke-4 listing terlambat
        for i in range(start, n):
            if rnd.random() < 0.03:
                continue                                                                  # bolong acak
            r = rnd.gauss(0.0005, 0.03)
            o = p
            p *= 1.0 + r
            rows.append([T0 + i * DAY_MS, o, max(o, p) * 1.01, min(o, p) * 0.99, p, 1000.0 * (1 + rnd.random())])
        out[a] = Series.from_rows(rows)
    return md_of(out)


class CausalityTests(unittest.TestCase):
    def test_cutting_the_data_at_day_t_never_changes_the_target_of_day_t(self):
        md = random_md(1)
        for name, rule in wide_rules().items():
            sp = spec_of(rule, universe=(BTC, ETH, BNB, "SOLUSDT"))
            full = {t.t: t.weights for t in R.targets(sp, md)}
            self.assertGreater(len(full), 200, name)
            days = sorted(full)
            for t in days[40::17]:
                cut = R.targets(sp, md.upto(t))
                self.assertEqual(cut[-1].t, t, name)
                self.assertEqual(cut[-1].weights, full[t], f"{name} hari {t}")

    def test_perturbing_every_bar_after_day_t_never_changes_targets_up_to_day_t(self):
        md = random_md(2)
        t_cut = T0 + 150 * DAY_MS
        rnd = random.Random(9)
        alt = {}
        for a, s in md.perp.items():
            rows = [[t, o, h, l, c, v] if t <= t_cut else [t, o * rnd.uniform(0.2, 5), h * 9, l * 0.1, c * rnd.uniform(0.2, 5), v * 100]
                    for t, o, h, l, c, v in zip(s.t, s.o, s.h, s.l, s.c, s.v)]
            alt[a] = Series.from_rows(rows)
        for name, rule in wide_rules().items():
            sp = spec_of(rule, universe=(BTC, ETH, BNB, "SOLUSDT"))
            a = {t.t: t.weights for t in R.targets(sp, md) if t.t <= t_cut}
            b = {t.t: t.weights for t in R.targets(sp, md_of(alt)) if t.t <= t_cut}
            self.assertEqual(a, b, name)

    def test_the_gate_pit_check_passes_for_every_wide_rule(self):
        md = random_md(3, n=300)
        for name, rule in wide_rules().items():
            res = gates.g1_pit(gates._Ctx(spec_of(rule, universe=(BTC, ETH, BNB, "SOLUSDT")), md, FAST, None))
            self.assertEqual(res.status, gates.PASS, f"{name}: {res.value}")

    def test_targets_are_deterministic_and_use_only_declared_assets_with_gross_within_the_cap(self):
        md = random_md(4)
        for name, rule in wide_rules().items():
            sp = spec_of(rule, universe=(BTC, ETH, BNB, "SOLUSDT"))
            a, b = R.targets(sp, md), R.targets(sp, md)
            self.assertEqual(a, b, name)
            cap = rule["bobot"]["gross_maks"]
            for t in a:
                self.assertLessEqual(sum(abs(w) for w in t.weights.values()), cap + 1e-9, (name, t.t))
                self.assertTrue(set(t.weights) <= {BTC, ETH, BNB, "SOLUSDT"})


# ================================================================ mesin keadaan + bobot

def one_asset(closes):
    return md_of({BTC: ohlcv(closes), ETH: ohlcv([100.0] * len(closes))})            # ETH hanya menjaga grid dan pembagi aset berbar


def weights(rule, md, universe=(BTC, ETH), asset=BTC):
    return [t.weights.get(asset, 0.0) for t in R.targets(spec_of(rule, universe=universe), md)]


class StateMachineTests(unittest.TestCase):
    def test_enter_hold_and_explicit_exit_with_hysteresis(self):
        r = per_aset(cmp_("<", f_("close"), c_(90)), cmp_(">", f_("close"), c_(100)))
        self.assertEqual(weights(r, one_asset([95, 85, 88, 95, 105, 95, 80])), [0, .5, .5, .5, 0, 0, .5])      # gross 1 / 2 aset berbar

    def test_without_an_explicit_exit_the_position_ends_when_the_entry_is_no_longer_true(self):
        r = per_aset(cmp_(">", f_("close"), c_(90)))
        self.assertEqual(weights(r, one_asset([95, 85, 95, 70, 91])), [.5, 0, .5, 0, .5])

    def test_short_side_mirrors_the_long_side(self):
        r = per_aset(masuk_short=cmp_(">", f_("close"), c_(110)), keluar_short=cmp_("<", f_("close"), c_(100)))
        self.assertEqual(weights(r, one_asset([105, 115, 112, 99, 120])), [0, -.5, -.5, 0, -.5])

    def test_simultaneous_long_and_short_entry_is_a_conflict_and_stays_flat(self):
        r = per_aset(cmp_(">", f_("close"), c_(90)), masuk_short=cmp_(">", f_("close"), c_(95)))
        self.assertEqual(weights(r, one_asset([100, 92, 100])), [0, .5, .5])                # hari 0: kedua benar -> flat; hari 1: hanya long; hari 2: sudah long, tetap

    def test_undefined_values_never_trigger_an_entry_not_even_through_not(self):
        """Logika tiga-nilai: `not (tak terdefinisi)` tetap tak terdefinisi. Dengan logika dua-nilai aset masuk posisi pada bar pemanasan."""
        r = per_aset({"not": cmp_(">", f_("close", None, 5), c_(50))})
        self.assertEqual(weights(r, one_asset([40.0] * 10)), [0] * 5 + [.5] * 5)
        self.assertEqual(weights(r, one_asset([60.0] * 10)), [0] * 10)

    def test_the_state_survives_a_day_without_a_bar_and_the_asset_carries_no_weight_that_day(self):
        r = per_aset(cmp_("<", f_("close"), c_(90)), cmp_(">", f_("close"), c_(100)))
        a = ohlcv([95, 80, 85, 85, 85, 85, 85], skip=(3,))
        md = md_of({BTC: a, ETH: ohlcv([100.0] * 7)})
        tg = R.targets(spec_of(r), md)
        self.assertEqual([t.weights.get(BTC, 0.0) for t in tg], [0, .5, .5, 0, .5, .5, .5])          # hari 3: tak ada bar -> bobot 0, keadaan tetap long
        self.assertEqual(tg[3].meta["n_aset"], 1)

    def test_equal_weight_denominator_is_the_number_of_assets_with_a_bar_that_day(self):
        r = per_aset(cmp_(">", f_("close"), c_(0)))
        late = ohlcv([10.0] * 6, t0=T0 + 4 * DAY_MS)
        md = md_of({BTC: ohlcv([10.0] * 10), ETH: late})
        w = [t.weights for t in R.targets(spec_of(r), md)]
        self.assertEqual(w[0], {BTC: 1.0})                                                              # ETH belum listing
        self.assertEqual(w[5], {BTC: .5, ETH: .5})
        g = per_aset(cmp_(">", f_("close"), c_(0)), gross=0.6)
        self.assertEqual(R.targets(spec_of(g), md)[5].weights, {BTC: .3, ETH: .3})

    def test_inverse_volatility_weights_are_proportional_to_one_over_sigma_and_sum_to_the_gross(self):
        def alt(a, n=40):
            out, p = [], 100.0
            for i in range(n):
                p *= 1.0 + (a if i % 2 == 0 else -a)
                out.append(p)
            return out
        md = md_of({BTC: ohlcv(alt(0.01)), ETH: ohlcv(alt(0.02))})
        r = per_aset(cmp_(">", f_("close"), c_(0)), skema="inv_vol", n=10)
        tg = R.targets(spec_of(r), md)
        s = {a: [x / y - 1.0 for x, y in zip(md.perp[a].c[1:], md.perp[a].c[:-1])] for a in (BTC, ETH)}
        sig = {a: statistics.stdev(s[a][-10:]) for a in s}                                               # return di indeks 30..39
        inv = {a: 1.0 / sig[a] for a in sig}
        last = tg[-1].weights
        for a in (BTC, ETH):
            self.assertAlmostEqual(last[a], inv[a] / sum(inv.values()), places=9)
        self.assertAlmostEqual(sum(last.values()), 1.0, places=9)
        self.assertGreater(last[BTC], last[ETH])                                                         # volatilitas lebih rendah -> bobot lebih besar
        self.assertEqual(tg[5].weights, {})                                                              # sigma belum terdefinisi -> tidak ada posisi


class RankingTests(unittest.TestCase):
    def four(self, rates):
        return md_of({a: ohlcv([100.0 * (1.0 + r) ** i for i in range(30)]) for a, r in zip(("AAA", "BBB", "CCC", "DDD"), rates)})

    def spec(self, rule):
        return spec_of(rule, universe=("AAA", "BBB", "CCC", "DDD"))

    def test_top_and_bottom_k_with_dollar_neutral_legs(self):
        md = self.four((0.03, 0.02, 0.01, -0.01))
        r = peringkat(f_("ret", 5), kl=1, ks=1, min_aset=4)
        last = R.targets(self.spec(r), md)[-1].weights
        self.assertEqual(last, {"AAA": 1.0, "DDD": -1.0})                                                # gross 2,0 = 1,0 per kaki
        r2 = peringkat(f_("ret", 5), kl=2, ks=1, min_aset=4, gross=1.0)
        self.assertEqual(R.targets(self.spec(r2), md)[-1].weights, {"AAA": .25, "BBB": .25, "DDD": -.5})   # tiap kaki gross/2, dibagi rata di dalam kaki

    def test_ties_break_by_asset_name_and_a_book_needs_min_aset_defined_scores(self):
        md = self.four((0.0, 0.0, 0.0, 0.0))
        r = peringkat(f_("ret", 5), kl=1, ks=1, min_aset=4)
        self.assertEqual(R.targets(self.spec(r), md)[-1].weights, {"AAA": 1.0, "BBB": -1.0})              # seri: nama menentukan; kaki short dari sisa, tidak pernah aset yang sama
        three = md_of({a: ohlcv([100.0 + i for i in range(30)]) for a in ("AAA", "BBB", "CCC")})
        self.assertEqual(R.targets(spec_of(r, universe=("AAA", "BBB", "CCC")), three)[-1].weights, {})
        self.assertEqual(R.targets(self.spec(r), md)[3].weights, {})                                       # skor belum terdefinisi (n=5)

    def test_seven_sub_books_average_the_last_seven_daily_books(self):
        md = md_of({a: ohlcv(walk(120, 20 + i, drift=0.0, vol=0.03)) for i, a in enumerate(("AAA", "BBB", "CCC", "DDD"))})
        daily = R.targets(self.spec(peringkat(f_("ret", 5), kl=1, ks=1, min_aset=4, rotasi="harian")), md)
        seven = R.targets(self.spec(peringkat(f_("ret", 5), kl=1, ks=1, min_aset=4, rotasi="tujuh_sub_buku")), md)
        self.assertNotEqual([t.weights for t in daily], [t.weights for t in seven])
        for i in range(5 + 6, len(daily)):                                                               # semua 7 hari-minggu sudah punya buku
            acc = {}
            for j in range(i - 6, i + 1):
                for a, w in daily[j].weights.items():
                    acc[a] = acc.get(a, 0.0) + w / 7
            want = {a: w for a, w in acc.items() if abs(w) > 1e-12}
            self.assertEqual(set(seven[i].weights), set(want), i)
            for a in want:
                self.assertAlmostEqual(seven[i].weights[a], want[a], places=12)

    def test_inverse_volatility_inside_a_leg_and_the_gross_cap(self):
        md = md_of({a: ohlcv(walk(80, 40 + i, drift=0.002 * (4 - i), vol=0.01 * (i + 1))) for i, a in enumerate(("AAA", "BBB", "CCC", "DDD"))})
        r = peringkat(f_("ret", 10), kl=2, ks=2, min_aset=4, gross=2.0, skema="inv_vol", n=20)
        tg = R.targets(self.spec(r), md)
        last = tg[-1].weights
        self.assertAlmostEqual(sum(w for w in last.values() if w > 0), 1.0, places=9)
        self.assertAlmostEqual(sum(w for w in last.values() if w < 0), -1.0, places=9)
        for t in tg:
            self.assertLessEqual(sum(abs(w) for w in t.weights.values()), 2.0 + 1e-9)


# ================================================================ BUKTI EKUIVALENSI (kriteria penerimaan §3.1)

def rule_b1(n):
    return per_aset(cmp_(">", f_("ret", {"p": "N"}), c_(0)), params={"N": n})


def rule_b6(n):
    return per_aset(cmp_("<", f_("zscore", {"p": "N"}), c_(-2.0)), cmp_(">=", f_("zscore", {"p": "N"}), c_(0.0)), params={"N": n})


def rule_b2(l):
    return peringkat(f_("ret", {"p": "L"}), kl=3, ks=3, min_aset=8, rotasi="tujuh_sub_buku", gross=2.0, params={"L": l})


def sintetis_16(seed, n=420):
    rnd = random.Random(seed)
    out = {}
    for k, a in enumerate(SPECS["B1-TREND"].universe):
        p, rows = 100.0, []
        for i in range(0 if k % 4 else 30 * (k // 4), n):                                                # sebagian aset listing terlambat
            if rnd.random() < 0.02:
                continue                                                                                  # bolong acak (tidak ada bar)
            p *= 1.0 + rnd.gauss(0.0004, 0.035)
            rows.append([T0 + i * DAY_MS, p, p, p, p, 1.0])
        out[a] = Series.from_rows(rows)
    return md_of(out)


class EquivalenceTests(unittest.TestCase):
    def assertSame(self, template_spec, rule, md):
        sp = spec_of(rule, universe=template_spec.universe)
        a = REGISTRY[template_spec.method](template_spec, md)
        b = REGISTRY[R.RULE_METHOD](sp, md)
        self.assertEqual([t.t for t in a], [t.t for t in b])
        diff = [t.t for t, u in zip(a, b) if t.weights != u.weights]
        self.assertEqual(diff, [], f"{template_spec.bot_id}: bobot berbeda di {len(diff)} hari")
        self.assertGreater(sum(1 for t in a if t.weights), 50, "tes tanpa posisi tidak membuktikan apa pun")
        self.assertEqual(replay(template_spec, md, a), replay(sp, md, b))

    def test_b1_b6_b2_expressed_as_rules_give_identical_weights_and_pnl_on_synthetic_data_with_holes(self):
        for seed in (1, 2, 3):
            md = sintetis_16(seed)
            for n in (20, 45):
                self.assertSame(dataclasses.replace(SPECS["B1-TREND"], param=n), rule_b1(n), md)
            for n in (10, 15):
                self.assertSame(dataclasses.replace(SPECS["B6-BOUNCE"], param=n), rule_b6(n), md)
            for l in (14, 28):
                self.assertSame(dataclasses.replace(SPECS["B2-RS"], param=l), rule_b2(l), md)

    @unittest.skipUnless(os.path.isdir(BARS), "ledger/bars tidak ada")
    def test_b1_b6_b2_expressed_as_rules_give_identical_weights_and_pnl_over_the_whole_real_history(self):
        md = load_csv_dir(BARS, cli.DATA_SYMBOLS)
        for bid, mk, params in (("B1-TREND", rule_b1, (60, 30, 90)), ("B6-BOUNCE", rule_b6, (10, 20)), ("B2-RS", rule_b2, (28, 14))):
            for p in params:
                self.assertSame(dataclasses.replace(SPECS[bid], param=p), mk(p), md)

    def test_a_sub_book_kept_stale_through_a_day_with_too_few_ranked_assets_matches_b2(self):
        """B2 menyimpan buku hari-minggu yang lama bila peringkat hari itu tidak sah (aset kurang dari min_aset); rule harus meniru persis."""
        gaps = {"AAA": (50, 51, 90), "BBB": (50, 130), "CCC": (), "DDD": ()}
        md = md_of({a: ohlcv(walk(220, 90 + i, drift=0.0, vol=0.03), skip=gaps[a]) for i, a in enumerate(("AAA", "BBB", "CCC", "DDD"))})
        konst = {"k": 1, "tranche": 7, "min_aset": 4, "gross": 2.0}
        b2 = dataclasses.replace(SPECS["B2-RS"], param=10, konstanta=konst, universe=("AAA", "BBB", "CCC", "DDD"))
        rule = peringkat(f_("ret", {"p": "L"}), kl=1, ks=1, min_aset=4, rotasi="tujuh_sub_buku", gross=2.0, params={"L": 10})
        a = REGISTRY["B2-RS"](b2, md)
        b = REGISTRY[R.RULE_METHOD](spec_of(rule, universe=b2.universe), md)
        self.assertEqual([(t.t, t.weights) for t in a], [(t.t, t.weights) for t in b])
        days_without_book = [t.t for t in a if t.t in {T0 + 50 * DAY_MS, T0 + 51 * DAY_MS, T0 + 90 * DAY_MS}]
        self.assertEqual(len(days_without_book), 3)                                                   # hari-hari itu memang ada di grid (CCC/DDD punya bar)
        self.assertTrue(all(t.weights for t in a if t.t in set(days_without_book)))                  # buku lama dipertahankan, bukan dikosongkan

    def test_the_equivalence_test_would_notice_a_different_rule(self):
        md = sintetis_16(5)
        with self.assertRaises(AssertionError):
            self.assertSame(dataclasses.replace(SPECS["B1-TREND"], param=30), rule_b1(31), md)
        with self.assertRaises(AssertionError):
            self.assertSame(dataclasses.replace(SPECS["B6-BOUNCE"], param=10), put(rule_b6(10), ("keluar_long", "b"), c_(0.5)), md)


# ================================================================ G5 atas parameter bernama

class PlateauRuleTests(unittest.TestCase):
    def g5(self, rule):
        return by_gate(gates.run_gates(spec_of(rule, universe=(BTC, ETH, BNB, "SOLUSDT")), trending(), None, FAST))["G5"]

    def test_a_robust_rule_passes_and_every_named_parameter_gets_its_own_row(self):
        res = self.g5(rule_b1(20))
        self.assertEqual(res.status, gates.PASS, res.value)
        for v in ("N: 10:", "15:", "25:", "30:"):
            self.assertIn(v, res.value)

    def test_two_parameters_are_shifted_one_at_a_time_and_together(self):
        r = per_aset({"and": [cmp_(">", f_("ret", {"p": "N"}), c_(0)), cmp_(">", f_("ret", {"p": "M"}), c_(-0.5))]}, params={"N": 20, "M": 40})
        res = self.g5(r)
        self.assertEqual(res.status, gates.PASS, res.value)
        for g in ("N:", "M:", "semua:"):
            self.assertIn(g, res.value)

    def test_no_named_parameter_means_no_robustness_claim(self):
        res = self.g5(per_aset(cmp_(">", f_("ret", 20), c_(0))))
        self.assertEqual(res.status, gates.FAIL)
        self.assertIn("tanpa parameter bernama", res.value)

    def test_a_decorative_parameter_fails_even_when_the_rest_is_robust(self):
        r = per_aset({"and": [cmp_(">", f_("ret", 20), c_(0)), cmp_(">", {"op": "*", "a": {"p": "D"}, "b": c_(0)}, c_(-1))]}, params={"D": 3})
        res = self.g5(r)
        self.assertEqual(res.status, gates.FAIL, res.value)
        self.assertIn("parameter dekoratif", res.value)
        self.assertIn("D", res.value.split("parameter dekoratif")[1])

    def test_a_tiny_integer_parameter_cannot_shrink_the_standard(self):
        res = self.g5(rule_b1(2))
        self.assertEqual(res.status, gates.FAIL, res.value)
        self.assertIn("varian berbeda", res.value)

    def test_a_losing_base_fails_before_any_variant_is_run(self):
        noise = md_perp({a: walk(1500, 70 + i, drift=-0.001, vol=0.02) for i, a in enumerate((BTC, ETH, BNB, "SOLUSDT"))})
        res = by_gate(gates.run_gates(spec_of(rule_b1(20), universe=(BTC, ETH, BNB, "SOLUSDT")), noise, None, FAST))["G5"]
        self.assertEqual(res.status, gates.FAIL)
        self.assertTrue(res.value.startswith("dasar"))

    def test_the_whole_gate_suite_runs_on_a_rule_and_the_template_g5_is_untouched(self):
        res = by_gate(gates.run_gates(spec_of(rule_b1(20), universe=(BTC, ETH, BNB, "SOLUSDT")), trending(), None, FAST))
        self.assertTrue(set(gates.REQUIRED) <= set(res), set(gates.REQUIRED) - set(res))
        for g in ("G1", "G2", "G3", "G5", "G8", "G9"):
            self.assertEqual(res[g].status, gates.PASS, f"{g}: {res[g].value}")
        self.assertEqual(res["G6"].status, gates.TB)
        tpl = by_gate(gates.run_gates(dataclasses.replace(SPECS["B1-TREND"], param=20), trending(), None, FAST))["G5"]
        self.assertIn("dasar 20:", tpl.value)                                                             # cabang template tetap seperti sebelumnya


class ForwardLedgerTests(unittest.TestCase):
    def test_a_rule_bot_runs_the_forward_ledger_and_its_chain_verifies_against_the_bars(self):
        """Jam maju (ledger paper harian) memakai jalur kode yang sama dengan bot template: tick -> settle -> rantai -> hitung ulang dari bar."""
        from engine import ledger
        from .helpers import regime_closes
        from .test_ledger import LOCK, bar, now_after
        base = md_perp({BTC: regime_closes(160, 1), ETH: regime_closes(160, 2), BNB: regime_closes(160, 3)})
        md = MarketData(perp=base.perp, funding={a: {T0 + i * DAY_MS: 0.0001 for i in range(160)} for a in base.perp})       # settle butuh funding hari itu
        sp = spec_of(rule_b1(20))
        chain = [ledger.seal(ledger.make_genesis(sp, LOCK, None, bar(100), now_after(100, 0.5)), ledger.ZERO)]
        for k in range(100, 130):
            new, _ = ledger.step(sp, md.upto(bar(k)), now_after(k), chain)
            chain.extend(new)
        self.assertEqual(ledger.verify_chain(chain), [])
        self.assertEqual(ledger.verify_against_data(sp, chain, md, md), [])
        ticks = [r for r in chain if r["type"] == "tick"]
        self.assertGreaterEqual(len(ticks), 25)
        self.assertTrue(any(r["targets"] for r in ticks), "tanpa posisi tidak membuktikan apa pun")
        self.assertTrue(any(r["type"] == "settle" for r in chain))
        self.assertEqual(chain[0]["spec_sha"], sp.sha())
        # data bar diubah sesudah kejadian: rantai memang sah, tetapi hitung ulang dari bar BEDA
        s = md.perp[BTC]
        rows = [[t, o, h, l, c * (1.5 if i == 110 else 1.0), v] for i, (t, o, h, l, c, v) in enumerate(zip(s.t, s.o, s.h, s.l, s.c, s.v))]
        alt = MarketData(perp={**md.perp, BTC: Series.from_rows(rows)}, funding=md.funding)
        self.assertTrue(ledger.verify_against_data(sp, chain, alt, alt))


class IntakeCliTests(unittest.TestCase):
    @unittest.skipUnless(os.path.isdir(BARS), "ledger/bars tidak ada")
    def test_the_intake_command_validates_and_gates_a_rule_form_on_the_repo_bars(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli.main(["intake", "--file", EX, "--data", BARS, "--placebo-n", "30", "--boot-n", "50"])
        out = buf.getvalue()
        self.assertIn(rc, (0, 1))
        self.assertIn("formulir sah", out)
        self.assertIn("PULLBACK-TREND-1 (rule, sha aturan 0x", out)
        self.assertIn("G5   PLATEAU", out)
        self.assertIn("R:", out)                                                      # baris per parameter bernama
        self.assertIn("semua:", out)
        bad = io.StringIO()
        with open(EX, encoding="utf-8") as f:
            sub = json.load(f)
        sub["spec"]["rule"]["params"]["R"] = 1
        tmp = os.path.join(os.environ.get("TEMP", "."), "rule-intake-bad.json")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(sub, f)
        self.addCleanup(os.remove, tmp)
        with contextlib.redirect_stdout(bad):
            self.assertEqual(cli.main(["intake", "--file", tmp, "--data", BARS]), 1)
        self.assertIn("TOLAK: spec.rule", bad.getvalue())


# ================================================================ kontrak web -> gerbang

def node_ts():
    """Node yang bisa menjalankan TypeScript langsung (>= 22.6), atau None."""
    node = shutil.which("node")
    if not node:
        return None
    m = re.match(r"v(\d+)\.(\d+)", subprocess.run([node, "--version"], capture_output=True, text=True, timeout=30).stdout.strip())
    return node if m and (int(m.group(1)), int(m.group(2))) >= (22, 6) else None


@unittest.skipUnless(node_ts(), "Node >= 22.6 tidak ada: kontrak web tidak bisa dijalankan di mesin ini")
class WebContractTests(unittest.TestCase):
    """`web/src/lib/rule.ts` (pembangun aturan) menyusun JSON gerbang; `tools/web_rule_states.mjs` menjalankannya dengan Node dan mencetak hasilnya.
    Di sini hasil itu divalidasi dengan `engine/rule.py` dan dijalankan mesin: web dan gerbang tidak bisa menyimpang diam-diam."""

    @classmethod
    def setUpClass(cls):
        r = subprocess.run([node_ts(), "--experimental-strip-types", "--no-warnings", os.path.join(ROOT, "tools", "web_rule_states.mjs")],
                           capture_output=True, text=True, timeout=120, cwd=ROOT)
        assert r.returncode == 0, r.stderr[-400:]
        cls.out = json.loads(r.stdout)

    def sub_with(self, rule):
        with open(EX, encoding="utf-8") as f:
            sub = json.load(f)
        sub["spec"]["rule"] = rule
        sub["spec"]["universe"] = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "LINKUSDT", "LTCUSDT", "AVAXUSDT"]
        return sub

    def test_every_state_the_builder_can_emit_passes_the_gate_validator_and_runs_in_the_engine(self):
        md = sintetis_16(7)
        for name, rule in self.out["rules"].items():
            sub = self.sub_with(rule)
            self.assertEqual(submission.validate(sub), [], name)
            sp = submission.to_botspec(sub)
            tg = REGISTRY[sp.method](sp, md)
            self.assertGreater(len(tg), 300, name)
            cap = rule["bobot"]["gross_maks"]
            self.assertTrue(all(sum(abs(w) for w in t.weights.values()) <= cap + 1e-9 for t in tg), name)

    def test_numbers_typed_as_text_become_numbers_and_leftovers_are_not_sent(self):
        n = self.out["rules"]["nested"]
        self.assertEqual(n["params"], {"N": 20, "Z": 2, "G": 3})
        self.assertEqual(n["bobot"], {"skema": "inv_vol", "gross_maks": 0.8, "n": {"p": "N"}})
        self.assertEqual(n["keluar_short"], {"cmp": "<", "a": {"f": "rsi", "n": 14}, "b": {"c": 50}})
        self.assertEqual(self.out["rules"]["rank"]["long_teratas"], 3)
        stale = self.out["rules"]["stale_n"]
        self.assertEqual(stale["bobot"], {"skema": "sama", "gross_maks": 1})                              # `n` sisa inv_vol tidak ikut
        self.assertEqual(sorted(stale), ["bobot", "masuk_long", "mode", "params"])                         # slot kosong tidak ikut

    def test_the_web_counters_agree_with_the_gate_on_nodes_depth_and_window_work(self):
        for name, rule in self.out["rules"].items():
            web = self.out["sizes"][name]
            self.assertEqual(R.ukuran(rule), {"simpul": web["nodes"], "kedalaman": web["depth"], "jendela": web["work"]}, name)

    def test_renaming_a_parameter_in_the_builder_renames_every_reference(self):
        r = self.out["rules"]["renamed"]
        self.assertEqual(r["params"], {"WIN": 20})
        self.assertEqual(r["masuk_long"]["a"]["n"], {"p": "WIN"})
        self.assertEqual(self.out["meta"]["refs"], ["WIN"])
        self.assertEqual(submission.validate(self.sub_with(r)), [])
        self.assertIn("Go long an asset when ret(WIN) > 0.", self.out["meta"]["words_en"])
        self.assertIn("Masuk long pada suatu aset bila ret(WIN) > 0.", self.out["meta"]["words_id"])


if __name__ == "__main__":
    unittest.main()

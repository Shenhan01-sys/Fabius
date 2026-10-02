import dataclasses
import math
import statistics
import unittest

from engine.bots import REGISTRY
from engine.data import ListingEvent, MarketData
from engine.series import DAY_MS
from engine.spec import PERP_UNIVERSE, SPECS

from .helpers import BNB, BTC, ETH, T0, grow, md_perp, mk_series, walk

PAXG = "PAXGUSDT"


def rich_md(n=200, seed0=100) -> MarketData:
    perp = {a: mk_series(walk(n, seed0 + i, drift=0.0005, vol=0.03)) for i, a in enumerate(PERP_UNIVERSE)}
    spot = {a: mk_series(walk(n, seed0 + 50 + i, drift=0.0005, vol=0.03)) for i, a in enumerate(PERP_UNIVERSE)}
    spot[PAXG] = mk_series(walk(n, seed0 + 99, drift=0.0002, vol=0.01))
    funding = {a: {T0 + k * DAY_MS: 0.0003 + 0.0004 * math.sin(k / 9 + i) for k in range(n)}
               for i, a in enumerate(PERP_UNIVERSE)}
    return MarketData(perp=perp, spot=spot, funding=funding)


class B1Tests(unittest.TestCase):
    sp = dataclasses.replace(SPECS["B1-TREND"], param=5)

    def test_long_rising_flat_falling_equal_weight(self):
        md = md_perp({BTC: grow(30, 0.01), ETH: grow(30, -0.01), BNB: grow(30, 0.005)})
        tg = REGISTRY["B1-TREND"](self.sp, md)
        self.assertEqual(tg[4].weights, {})                      # belum ada riwayat N hari
        self.assertEqual(set(tg[5].weights), {BTC, BNB})
        self.assertAlmostEqual(tg[-1].weights[BTC], 1 / 3)       # 1/3: penyebut = SEMUA aset yang punya bar, bukan yang long

    def test_asset_without_last_bar_is_excluded_from_denominator(self):
        md = md_perp({BTC: grow(30, 0.01), ETH: grow(30, -0.01), BNB: grow(28, 0.005)})
        last = REGISTRY["B1-TREND"](self.sp, md)[-1]
        self.assertEqual(last.t, T0 + 29 * DAY_MS)
        self.assertEqual(last.weights, {BTC: 0.5})

    def test_deterministic(self):
        md = rich_md(80)
        self.assertEqual(REGISTRY["B1-TREND"](self.sp, md), REGISTRY["B1-TREND"](self.sp, md))


class B2Tests(unittest.TestCase):
    base = dataclasses.replace(SPECS["B2-RS"], param=5)

    @staticmethod
    def ten():
        names = list(PERP_UNIVERSE[:10])
        return names, {a: grow(80, 0.002 * (i - 4.5)) for i, a in enumerate(names)}

    def test_single_weekday_book_top_bottom_k(self):
        names, closes = self.ten()
        sp = dataclasses.replace(self.base, konstanta={**self.base.konstanta, "tranche": 1, "rebalance_hari_utc": 2})
        tg = REGISTRY["B2-RS"](sp, md_perp(closes))
        self.assertEqual(tg[6].weights, {})                      # i=6: Selasa; i=0 (Rabu) < L
        w = tg[7].weights                                        # i=7: Rabu pertama dengan riwayat L
        self.assertEqual(set(w), set(names[:3]) | set(names[7:]))
        for a in names[7:]:
            self.assertAlmostEqual(w[a], 1 / 3)
        for a in names[:3]:
            self.assertAlmostEqual(w[a], -1 / 3)
        self.assertEqual(tg[8].weights, w)                       # ditahan sampai rebalance berikut
        self.assertTrue(tg[7].meta["rebalanced"] and not tg[8].meta["rebalanced"])

    def test_below_min_assets_no_book(self):
        _, closes = self.ten()
        few = {a: c for a, c in list(closes.items())[:7]}
        sp = dataclasses.replace(self.base, konstanta={**self.base.konstanta, "tranche": 1, "rebalance_hari_utc": 2})
        self.assertTrue(all(t.weights == {} for t in REGISTRY["B2-RS"](sp, md_perp(few))))

    def test_tranche_requires_fixed_day_only_when_single(self):
        _, closes = self.ten()
        bad = dataclasses.replace(self.base, konstanta={**self.base.konstanta, "tranche": 1})
        with self.assertRaises(ValueError):
            REGISTRY["B2-RS"](bad, md_perp(closes))
        with self.assertRaises(ValueError):
            REGISTRY["B2-RS"](dataclasses.replace(self.base, konstanta={**self.base.konstanta, "tranche": 3}), md_perp(closes))

    def test_tranche7_is_dollar_neutral_and_averages_books(self):
        names, _ = self.ten()
        n, flip = 90, 45
        closes = {}
        for i, a in enumerate(names):                            # kelompok 0-2 memimpin dulu, lalu kelompok 7-9; sisanya datar
            lead_first = i < 3
            lead_later = i >= 7
            c, p = [], 100.0
            for d in range(n):
                if (lead_first and d < flip) or (lead_later and d >= flip):
                    p *= 1.01
                c.append(p)
            closes[a] = c
        tg = REGISTRY["B2-RS"](self.base, md_perp(closes))
        self.assertEqual(tg[0].weights, {})
        partial = False
        for t in tg:
            if not t.weights:
                continue
            self.assertAlmostEqual(sum(t.weights.values()), 0.0, places=9)
            self.assertLessEqual(max(abs(v) for v in t.weights.values()), 1 / 3 + 1e-9)
            partial = partial or any(1e-6 < abs(v) < 1 / 3 - 1e-6 for v in t.weights.values())
        self.assertTrue(partial, "saat urutan berbalik, bobot gabungan harus berupa rerata sub-buku (parsial)")


class B3Tests(unittest.TestCase):
    sp = SPECS["B3-CARRY"]

    def mk(self, rate, n=30, skip_fund=None):
        perp, spot = {BTC: mk_series(grow(n, 0.0))}, {BTC: mk_series(grow(n, 0.0))}
        f = {T0 + i * DAY_MS: rate for i in range(n) if not skip_fund or i not in skip_fund}
        return MarketData(perp=perp, spot=spot, funding={BTC: f})

    def test_flag_only_with_full_7_day_window_and_high_funding(self):
        tg = REGISTRY["B3-CARRY"](self.sp, self.mk(0.001))
        self.assertTrue(all(t.weights == {} for t in tg[:6]))    # <7 hari funding: tidak ditandai
        self.assertEqual(tg[6].weights, {BTC: 1.0})
        self.assertEqual(tg[-1].weights, {BTC: 1.0})

    def test_low_funding_not_flagged(self):
        tg = REGISTRY["B3-CARRY"](self.sp, self.mk(0.0001))      # 3.65%/tahun < theta 10%
        self.assertTrue(all(t.weights == {} for t in tg))

    def test_missing_funding_day_blocks_signal_until_window_clean(self):
        tg = REGISTRY["B3-CARRY"](self.sp, self.mk(0.001, skip_fund={10}))
        by = {(t.t - T0) // DAY_MS: t for t in tg}
        for d in range(10, 17):
            self.assertEqual(by[d].weights, {}, f"hari {d}")
        self.assertEqual(by[17].weights, {BTC: 1.0})

    def test_needs_spot_perp_and_funding(self):
        md = self.mk(0.001)
        self.assertEqual(REGISTRY["B3-CARRY"](self.sp, MarketData(perp=md.perp, funding=md.funding)), [])


class B5Tests(unittest.TestCase):
    sp = dataclasses.replace(SPECS["B5-CORE-RWA"], param=20)

    def data(self, n=50):
        return MarketData(spot={BTC: mk_series(walk(n, 7, vol=0.04)), PAXG: mk_series(walk(n, 8, vol=0.01))})

    def test_no_gold_no_targets(self):
        self.assertEqual(REGISTRY["B5-CORE-RWA"](self.sp, MarketData(spot={BTC: mk_series(grow(50, 0.01))})), [])

    def test_inverse_vol_update_on_first_of_month(self):
        md = self.data()
        tg = REGISTRY["B5-CORE-RWA"](self.sp, md)
        self.assertAlmostEqual(tg[30].weights[BTC], 0.5)         # 31 Jan: belum ada pembaruan
        b, g = md.spot[BTC].c, md.spot[PAXG].c
        rb = [b[i] / b[i - 1] - 1 for i in range(1, 32)][-20:]
        rg = [g[i] / g[i - 1] - 1 for i in range(1, 32)][-20:]
        sb, sg = statistics.stdev(rb), statistics.stdev(rg)
        wb = (1 / sb) / (1 / sb + 1 / sg)
        self.assertAlmostEqual(tg[31].weights[BTC], wb)          # 1 Feb: bobot baru
        self.assertAlmostEqual(tg[31].weights[PAXG], 1 - wb)
        self.assertLess(wb, 0.5)                                 # BTC lebih liar -> bobot lebih kecil
        self.assertTrue(tg[31].meta["rebalanced"])
        self.assertAlmostEqual(tg[40].weights[BTC], wb)          # ditahan sampai pembaruan berikut

    def test_update_day_constant_is_used(self):
        md = self.data()
        sp = dataclasses.replace(self.sp, konstanta={**self.sp.konstanta, "hari_pembaruan": 15})
        tg = REGISTRY["B5-CORE-RWA"](sp, md)
        self.assertAlmostEqual(tg[31].weights[BTC], 0.5)         # 1 Feb tidak lagi memperbarui
        self.assertNotAlmostEqual(tg[45].weights[BTC], 0.5)      # 15 Feb memperbarui


class B6Tests(unittest.TestCase):
    sp = SPECS["B6-BOUNCE"]

    @staticmethod
    def expected_long(closes, n=10, z_in=2.0, z_out=0.0):
        pos, cur = [], False
        for i, c in enumerate(closes):
            if i >= n - 1:
                w = closes[i - n + 1:i + 1]
                sd = statistics.stdev(w)
                if sd > 0:
                    z = (c - statistics.mean(w)) / sd
                    if not cur and z < -z_in:
                        cur = True
                    elif cur and z >= z_out:
                        cur = False
            pos.append(cur)
        return pos

    def test_buy_the_drop_exit_at_mean(self):
        closes = [100.0, 101.0] * 15 + [85.0, 95.0, 99.0, 100.0, 101.0, 100.0]
        tg = REGISTRY["B6-BOUNCE"](self.sp, md_perp({BTC: closes}))
        exp = self.expected_long(closes)
        self.assertTrue(any(exp), "skenario harus memicu masuk")
        for i, t in enumerate(tg):
            self.assertEqual(bool(t.weights), exp[i], f"bar {i}")
            self.assertTrue(all(w > 0 for w in t.weights.values()))
        self.assertEqual(tg[30].weights, {BTC: 1.0})             # hari jatuh: masuk di penutupan

    def test_weight_is_one_over_assets_with_a_bar(self):
        closes = [100.0, 101.0] * 15 + [85.0, 95.0]
        md = md_perp({BTC: closes, ETH: [100.0, 100.5] * 16 + [100.0]})
        tg = REGISTRY["B6-BOUNCE"](self.sp, md)
        self.assertEqual(tg[30].weights, {BTC: 0.5})


class B4Tests(unittest.TestCase):
    sp = SPECS["B4-LISTING-FADE"]

    def test_short_for_h_days_and_volume_filter(self):
        evs = [ListingEvent("AAAUSDT", T0 + 5 * DAY_MS, 1.0, 5e6), ListingEvent("BBBUSDT", T0 + 8 * DAY_MS, 1.0, 2e5)]
        tg = REGISTRY["B4-LISTING-FADE"](self.sp, MarketData(events=evs))
        by = {(t.t - T0) // DAY_MS: t for t in tg}
        self.assertEqual(min(by), 5)
        self.assertEqual(by[5].weights, {"AAAUSDT": -0.02})      # masuk di penutupan bar hari-1
        self.assertEqual(by[18].weights, {"AAAUSDT": -0.02})
        self.assertEqual(by[19].weights, {})                     # H=14 hari kemudian: keluar
        self.assertTrue(all("BBBUSDT" not in t.weights for t in tg))

    def test_no_events_no_targets(self):
        self.assertEqual(REGISTRY["B4-LISTING-FADE"](self.sp, MarketData()), [])


class PointInTimeTests(unittest.TestCase):
    """Memotong data di hari D tidak boleh mengubah target hari D (deteksi look-ahead)."""

    def check(self, bot, sp, md, cuts):
        full = {t.t: t for t in REGISTRY[bot](sp, md)}
        for c in cuts:
            t = T0 + c * DAY_MS
            cut = REGISTRY[bot](sp, md.upto(t))
            self.assertTrue(cut and cut[-1].t == t, f"{bot} cut {c}")
            a, b = cut[-1].weights, full[t].weights
            self.assertEqual(set(a), set(b), f"{bot} cut {c}")
            for k in a:
                self.assertAlmostEqual(a[k], b[k], places=12, msg=f"{bot} cut {c} {k}")

    def test_all_bots(self):
        md = rich_md(200)
        cuts = (80, 120, 150, 199)
        r = lambda sp, **k: dataclasses.replace(sp, **k)
        self.check("B1-TREND", r(SPECS["B1-TREND"], param=10), md, cuts)
        self.check("B2-RS", r(SPECS["B2-RS"], param=10), md, cuts)
        self.check("B2-RS", r(SPECS["B2-RS"], param=10, konstanta={**SPECS["B2-RS"].konstanta, "tranche": 1, "rebalance_hari_utc": 3}), md, cuts)
        self.check("B3-CARRY", r(SPECS["B3-CARRY"], param=0.05), md, cuts)
        self.check("B5-CORE-RWA", r(SPECS["B5-CORE-RWA"], param=20), md, cuts)
        self.check("B6-BOUNCE", SPECS["B6-BOUNCE"], md, cuts)

    def test_future_bar_does_not_change_past_target(self):
        md = rich_md(120)
        sp = dataclasses.replace(SPECS["B1-TREND"], param=10)
        base = {t.t: t.weights for t in REGISTRY["B1-TREND"](sp, md)}
        longer = rich_md(121)
        for t in REGISTRY["B1-TREND"](sp, longer):
            if t.t in base and t.t < T0 + 100 * DAY_MS:
                self.assertEqual(t.weights, base[t.t])


if __name__ == "__main__":
    unittest.main()

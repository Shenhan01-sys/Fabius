"""P92 / F-D76: estimasi funding dari indeks premium 1m (`engine/funding_est.py`), pembaruannya di `tools/feed_bars.py`, pandangan funding di
`engine.data.load_csv_dir`, laporan PROVISIONAL, dan jalur B3 (target = estimasi beku, settle final = aktual)."""
import csv
import dataclasses
import io
import os
import sys
import tempfile
import unittest
import zipfile

from engine import funding_est as fe
from engine import ledger
from engine.data import MarketData, load_csv_dir
from engine.series import DAY_MS
from engine.spec import SPECS

from .helpers import BNB, BTC, ETH, T0, mk_series, regime_closes
from .test_ledger import LOCK, bar, now_after, spec10

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import feed_bars as fb                                           # noqa: E402

D0 = T0                                                          # 2020-01-01 00:00 UTC


def rd(path, mode="r"):
    with open(path, mode) as f:
        return f.read()


class EstimatorTests(unittest.TestCase):
    def test_constant_premium_inside_the_clamp_zone_pins_funding_at_the_interest_rate(self):
        for p in (0.0003, 0.0001, -0.0003, 0.0):
            self.assertAlmostEqual(fe.estimate_rate([p] * 480, 0.0001), 0.0001, places=12, msg=str(p))

    def test_outside_the_clamp_zone_funding_follows_the_premium(self):
        self.assertAlmostEqual(fe.estimate_rate([-0.001] * 480, 0.0001), -0.0005, places=12)       # I - P = 0,0011 -> dijepit 0,0005
        self.assertAlmostEqual(fe.estimate_rate([0.002] * 480, 0.0001), 0.0015, places=12)         # I - P = -0,0019 -> dijepit -0,0005

    def test_weights_grow_with_time_the_last_minutes_count_most(self):
        up = [0.0] * 240 + [0.004] * 240                  # premium tinggi di paruh akhir interval
        down = [0.004] * 240 + [0.0] * 240                # premium tinggi di paruh awal
        p_up = 0.004 * (480 * 481 / 2 - 240 * 241 / 2) / (480 * 481 / 2)       # bobot menit ke-i = i: paruh akhir menimbang lebih besar
        self.assertAlmostEqual(fe.estimate_rate(up, 0.0), p_up - 0.0005, places=12)               # P di luar zona jepit: F = P - 0,05 %
        self.assertAlmostEqual(fe.estimate_rate(down, 0.0), (0.004 - p_up) - 0.0005, places=12)
        self.assertGreater(fe.estimate_rate(up, 0.0), fe.estimate_rate(down, 0.0) + 1e-3)

    def test_bnb_has_zero_interest_and_everything_else_the_default(self):
        self.assertEqual(fe.interest_for("BNBUSDT"), 0.0)
        self.assertEqual(fe.interest_for("BTCUSDT"), 0.0001)
        self.assertAlmostEqual(fe.estimate_rate([0.0003] * 480, fe.interest_for("BNBUSDT")), 0.0, places=12)       # |P| <= 0,05 %: funding BNB = 0

    def test_estimate_day_needs_every_minute_and_never_guesses(self):
        mins = {D0 - fe.H8_MS + k * fe.MIN_MS: 0.0003 for k in range(480 * 4)}          # 8 jam terakhir hari -1 + 24 jam hari 0 = menit untuk 3 peristiwa
        ev = fe.estimate_day("BTCUSDT", mins, D0)
        self.assertEqual([t for t, _ in ev], [D0, D0 + fe.H8_MS, D0 + 2 * fe.H8_MS])
        self.assertTrue(all(abs(r - 0.0001) < 1e-12 for _, r in ev))
        del mins[D0 + 2 * fe.H8_MS - 7 * fe.MIN_MS]                                      # satu menit hilang DI DALAM interval peristiwa ke-3
        self.assertIsNone(fe.estimate_day("BTCUSDT", mins, D0))

    def test_rates_are_rounded_to_eight_decimals_like_binance(self):
        mins = {D0 - fe.H8_MS + k * fe.MIN_MS: 0.000123456789 for k in range(480 * 4)}
        ev = fe.estimate_day("BTCUSDT", mins, D0)
        self.assertTrue(all(abs(r - round(r, 8)) < 1e-15 for _, r in ev))


def premium_zip(day_ms, value, header=True, skip=()):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    if header:
        w.writerow(["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume"])
    for k in range(1440):
        if k in skip:
            continue
        t = day_ms + k * 60_000
        v = value(t) if callable(value) else value
        w.writerow([t, v, v, v, v, 0, t + 59_999, 0])
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("p.csv", buf.getvalue())
    return out.getvalue()


def write_seed(path, last_day_index, rate=0.0001):
    with open(path, "w", newline="") as f:
        f.write("t,rate\n")
        for d in range(last_day_index + 1):
            for h in (0, 8, 16):
                f.write(f"{D0 + d * DAY_MS + h * 3_600_000 + 1},{rate}\n")


class EstFeedTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        write_seed(os.path.join(self.d, "fund_BTCUSDT.csv"), 0)                          # aktual sampai hari 0 16:00 (+1 ms)

    def fetch_days(self, published, value=0.0003):
        def fetch(url):
            day = url.rsplit("-1m-", 1)[1][:10]
            for k in published:
                if fb.date_of(D0 + k * DAY_MS) == day:
                    return premium_zip(D0 + k * DAY_MS, value)
            return None
        return fetch

    def test_appends_whole_days_only_starting_after_the_last_actual_event(self):
        rep = fb.update_funding_est(self.d, "BTCUSDT", D0 + 3 * DAY_MS, self.fetch_days([0, 1, 2]))       # hari ini = hari 3 -> hari 1 dan 2 lengkap
        self.assertEqual(rep["added"], 6)
        rows = list(csv.reader(io.StringIO(rd(os.path.join(self.d, "fund_est_BTCUSDT.csv")))))
        self.assertEqual(rows[0], ["t", "rate"])
        self.assertEqual([int(r[0]) for r in rows[1:]], [D0 + DAY_MS + k * fe.H8_MS for k in range(6)])
        self.assertTrue(all(abs(float(r[1]) - 0.0001) < 1e-12 for r in rows[1:]))

    def test_stops_at_the_first_unpublished_file_and_writes_nothing_for_a_partial_day(self):
        rep = fb.update_funding_est(self.d, "BTCUSDT", D0 + 3 * DAY_MS, self.fetch_days([0, 1]))         # berkas hari 2 belum terbit
        self.assertEqual(rep["added"], 3)                                                                 # hari 1 saja (tiga peristiwa sekaligus)
        self.assertIn("belum terbit", rep["stop"])

    def test_is_idempotent_and_continues_after_the_last_estimate(self):
        fetch = self.fetch_days([0, 1, 2, 3])
        fb.update_funding_est(self.d, "BTCUSDT", D0 + 2 * DAY_MS, fetch)                                  # hari 1
        before = rd(os.path.join(self.d, "fund_est_BTCUSDT.csv"), "rb")
        self.assertEqual(fb.update_funding_est(self.d, "BTCUSDT", D0 + 2 * DAY_MS, fetch)["added"], 0)
        self.assertEqual(rd(os.path.join(self.d, "fund_est_BTCUSDT.csv"), "rb"), before)
        self.assertEqual(fb.update_funding_est(self.d, "BTCUSDT", D0 + 4 * DAY_MS, fetch)["added"], 6)    # hari 2 dan 3
        self.assertTrue(rd(os.path.join(self.d, "fund_est_BTCUSDT.csv"), "rb").startswith(before))        # baris lama tidak disentuh

    def test_actual_funding_arriving_later_does_not_duplicate_or_replace_estimates(self):
        fetch = self.fetch_days([0, 1, 2, 3])
        fb.update_funding_est(self.d, "BTCUSDT", D0 + 3 * DAY_MS, fetch)                                  # est hari 1 dan 2
        est_before = rd(os.path.join(self.d, "fund_est_BTCUSDT.csv"), "rb")
        write_seed(os.path.join(self.d, "fund_BTCUSDT.csv"), 2, rate=0.00012)                             # aktual terbit sampai hari 2
        rep = fb.update_funding_est(self.d, "BTCUSDT", D0 + 4 * DAY_MS, fetch)
        self.assertEqual(rep["added"], 3)                                                                 # hanya hari 3
        self.assertTrue(rd(os.path.join(self.d, "fund_est_BTCUSDT.csv"), "rb").startswith(est_before))

    def test_missing_minutes_stop_the_day_and_missing_seed_is_refused(self):
        def holey(url):
            day = url.rsplit("-1m-", 1)[1][:10]
            k = 1 if day == fb.date_of(D0 + DAY_MS) else 0
            return premium_zip(D0 + k * DAY_MS, 0.0003, skip={5 * 60} if k == 1 else ())          # hari 1 kehilangan menit 05:00
        rep = fb.update_funding_est(self.d, "BTCUSDT", D0 + 3 * DAY_MS, holey)
        self.assertEqual(rep["added"], 0)
        self.assertIn("menit hilang", rep["stop"])
        self.assertFalse(os.path.exists(os.path.join(self.d, "fund_est_BTCUSDT.csv")))
        rep = fb.update_funding_est(self.d, "ETHUSDT", D0 + 3 * DAY_MS, self.fetch_days([0, 1]))
        self.assertIn("seed", rep["stop"])

    def test_dry_run_writes_nothing_and_bnb_uses_zero_interest(self):
        write_seed(os.path.join(self.d, "fund_BNBUSDT.csv"), 0, rate=0.0)
        rep = fb.update_funding_est(self.d, "BNBUSDT", D0 + 2 * DAY_MS, self.fetch_days([0, 1]), dry_run=True)
        self.assertEqual(rep["added"], 3)
        self.assertFalse(os.path.exists(os.path.join(self.d, "fund_est_BNBUSDT.csv")))
        fb.update_funding_est(self.d, "BNBUSDT", D0 + 2 * DAY_MS, self.fetch_days([0, 1]))
        rows = list(csv.reader(io.StringIO(rd(os.path.join(self.d, "fund_est_BNBUSDT.csv")))))[1:]
        self.assertTrue(all(abs(float(r[1])) < 1e-12 for r in rows))                                      # |P| <= 0,05 % -> funding BNB = 0


class ViewTests(unittest.TestCase):
    def build(self):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "fund_BTCUSDT.csv"), "w", newline="") as f:
            f.write("t,rate\n")
            for k in range(5):                                                     # aktual hari 0..4, tiap hari 3 x 0,0001
                for h in (0, 8, 16):
                    f.write(f"{D0 + k * DAY_MS + h * 3_600_000 + 2},0.0001\n")
        with open(os.path.join(d, "fund_est_BTCUSDT.csv"), "w", newline="") as f:
            f.write("t,rate\n")
            for k in (3, 4, 5, 6):                                                 # estimasi hari 3..6, tiap hari 3 x 0,0002
                for h in (0, 8, 16):
                    f.write(f"{D0 + k * DAY_MS + h * 3_600_000},0.0002\n")
            f.write(f"{D0 + 7 * DAY_MS},0.0009\n{D0 + 7 * DAY_MS + 8 * 3_600_000},0.0009\n")        # hari 7 parsial (2 peristiwa): tidak dipakai
        return d

    def test_actual_view_ignores_estimates(self):
        f = load_csv_dir(self.build(), ["BTCUSDT"], "actual").funding["BTCUSDT"]
        self.assertEqual(sorted(f), [D0 + k * DAY_MS for k in range(5)])
        self.assertAlmostEqual(f[D0 + 4 * DAY_MS], 0.0003)

    def test_provisional_view_prefers_actual_and_fills_with_estimates(self):
        f = load_csv_dir(self.build(), ["BTCUSDT"], "provisional").funding["BTCUSDT"]
        self.assertEqual(sorted(f), [D0 + k * DAY_MS for k in range(7)])
        self.assertAlmostEqual(f[D0 + 3 * DAY_MS], 0.0003)                       # aktual menang
        self.assertAlmostEqual(f[D0 + 5 * DAY_MS], 0.0006)                       # hanya estimasi
        self.assertNotIn(D0 + 7 * DAY_MS, f)                                     # hari parsial tidak masuk

    def test_targets_view_freezes_the_estimate_even_after_actual_arrives(self):
        f = load_csv_dir(self.build(), ["BTCUSDT"], "targets").funding["BTCUSDT"]
        self.assertAlmostEqual(f[D0 + 2 * DAY_MS], 0.0003)                       # sebelum hari estimasi pertama: aktual
        self.assertAlmostEqual(f[D0 + 3 * DAY_MS], 0.0006)                       # sejak hari estimasi pertama: estimasi, walau aktual juga ada
        self.assertAlmostEqual(f[D0 + 4 * DAY_MS], 0.0006)
        self.assertEqual(sorted(f), [D0 + k * DAY_MS for k in range(7)])

    def test_unknown_view_is_refused(self):
        with self.assertRaises(ValueError):
            load_csv_dir(self.build(), ["BTCUSDT"], "tebak")


class ProvisionalReportTests(unittest.TestCase):
    def test_provisional_settles_fill_in_while_the_chain_stays_final_only(self):
        sp = spec10()
        n = 160
        perp = {BTC: mk_series(regime_closes(n, 1), T0), ETH: mk_series(regime_closes(n, 2), T0), BNB: mk_series(regime_closes(n, 3), T0)}
        actual = MarketData(perp=perp, funding={a: {T0 + i * DAY_MS: 0.0003 for i in range(100, 103)} for a in perp})            # aktual hanya sampai hari 102
        prov = MarketData(perp=perp, funding={a: {T0 + i * DAY_MS: 0.0003 for i in range(n)} for a in perp})                      # + estimasi sesudahnya
        chain = [ledger.seal(ledger.make_genesis(sp, LOCK, None, bar(100), now_after(100, 0.5)), ledger.ZERO)]
        for k in range(100, 112):
            new, _ = ledger.step(sp, actual.upto(bar(k)), now_after(k), chain, actual.upto(bar(k)))
            chain.extend(new)
        finals = [r for r in chain if r["type"] == "settle"]
        self.assertEqual(len(finals), 2)                                          # bar 101, 102 (funding aktual ada); sisanya menunggu
        pend = ledger.provisional_settles(sp, prov.upto(bar(111)), chain)
        self.assertEqual([r["bar_date"] for r in pend][:1], [ledger.date_of(bar(103))])
        self.assertEqual(len(pend), 9)                                            # bar 103..111
        text = ledger.render_report(chain, pend)
        self.assertIn("PROVISIONAL", text)
        self.assertIn("BUKAN catatan rantai", text)
        self.assertNotIn("PROVISIONAL", ledger.render_report(chain))
        self.assertEqual(len([r for r in chain if r["type"] == "settle"]), 2)     # tidak ada settle provisional yang masuk rantai
        self.assertEqual(ledger.verify_chain(chain), [])


class B3ViewTests(unittest.TestCase):
    """B3 memakai funding untuk TARGET: tick memakai pandangan 'targets' (estimasi beku), settle final memakai funding aktual."""

    def test_b3_ticks_from_frozen_estimates_and_settles_only_with_actual(self):
        n = 150
        sp = dataclasses.replace(SPECS["B3-CARRY"], bot_id="LEDG-B3", template="B3-CARRY", universe=(BTC, ETH))
        perp = {BTC: mk_series(regime_closes(n, 4), T0), ETH: mk_series(regime_closes(n, 5), T0)}
        spot = {BTC: mk_series(regime_closes(n, 4, vol=0.0201), T0), ETH: mk_series(regime_closes(n, 5, vol=0.0201), T0)}
        est_from = 105
        fund_actual = {a: {T0 + i * DAY_MS: 0.0003 for i in range(est_from)} for a in perp}                     # aktual belum ada untuk hari >= 105
        fund_targets = {a: {T0 + i * DAY_MS: 0.0003 for i in range(n)} for a in perp}                           # estimasi beku untuk hari >= 105
        md_t = MarketData(perp=perp, spot=spot, funding=fund_targets)
        md_a = MarketData(perp=perp, spot=spot, funding=fund_actual)
        chain = [ledger.seal(ledger.make_genesis(sp, LOCK, None, bar(110), now_after(110, 0.5)), ledger.ZERO)]
        for k in range(110, 118):
            new, _ = ledger.step(sp, md_t.upto(bar(k)), now_after(k), chain, md_a.upto(bar(k)))
            chain.extend(new)
        ticks = [r for r in chain if r["type"] == "tick"]
        self.assertEqual(len(ticks), 8)
        self.assertTrue(all(r["targets"] for r in ticks))                          # funding 3 bps/hari (10,95 %/th) > theta 10 %: B3 memegang kedua aset
        self.assertEqual(ledger.stats(chain)["n_settle"], 0)                       # funding AKTUAL belum ada: settle final menunggu, tidak diisi estimasi
        self.assertEqual(ledger.verify_chain(chain), [])
        self.assertEqual(ledger.verify_against_data(sp, chain, md_t, md_a), [])
        # funding aktual terbit belakangan dengan nilai yang BERBEDA dari estimasi: tick lama tetap cocok (pakai estimasi beku), settle kini bisa ditutup
        fund_actual2 = {a: {T0 + i * DAY_MS: 0.00031 for i in range(n)} for a in perp}
        md_a2 = MarketData(perp=perp, spot=spot, funding=fund_actual2)
        new, _ = ledger.step(sp, md_t.upto(bar(117)), now_after(117), chain, md_a2.upto(bar(117)))
        chain.extend(new)
        self.assertGreater(ledger.stats(chain)["n_settle"], 0)
        self.assertEqual(ledger.verify_against_data(sp, chain, md_t, md_a2), [])

    def b3_setup(self, n=150):
        sp = dataclasses.replace(SPECS["B3-CARRY"], bot_id="LEDG-B3", template="B3-CARRY", universe=(BTC, ETH))
        perp = {BTC: mk_series(regime_closes(n, 4), T0), ETH: mk_series(regime_closes(n, 5), T0)}
        spot = {BTC: mk_series(regime_closes(n, 4, vol=0.0201), T0), ETH: mk_series(regime_closes(n, 5, vol=0.0201), T0)}
        fund = {a: {T0 + i * DAY_MS: 0.0003 for i in range(n)} for a in perp}
        chain = [ledger.seal(ledger.make_genesis(sp, LOCK, None, bar(110), now_after(110, 0.5)), ledger.ZERO)]
        return sp, perp, spot, fund, chain

    def test_b3_tick_is_refused_while_the_asof_funding_is_missing_instead_of_going_silently_flat(self):
        sp, perp, spot, fund, chain = self.b3_setup()
        del fund[ETH][T0 + 110 * DAY_MS]                                         # estimasi ETH hari 110 belum terbit
        md = MarketData(perp=perp, spot=spot, funding=fund)
        new, notes = ledger.step(sp, md.upto(bar(110)), now_after(110), chain, md.upto(bar(110)))
        self.assertEqual([r for r in new if r["type"] == "tick"], [])
        self.assertTrue(any("funding hari" in x for x in notes), notes)
        fund[ETH][T0 + 110 * DAY_MS] = 0.0003                                    # estimasi tiba, masih < 12 jam: tick dibuat
        new, _ = ledger.step(sp, MarketData(perp=perp, spot=spot, funding=fund).upto(bar(110)), now_after(110, 3), chain)
        self.assertEqual([r["type"] for r in new][:1], ["tick"])

    def test_b3_asset_without_a_spot_bar_counts_as_dropped(self):
        sp, perp, spot, fund, chain = self.b3_setup()
        md = MarketData(perp=perp, spot=spot, funding=fund)
        new, _ = ledger.step(sp, md.upto(bar(110)), now_after(110), chain, md.upto(bar(110)))
        chain.extend(new)
        pit = md.upto(bar(111))
        pit.spot[ETH] = pit.spot[ETH].upto(bar(110))                             # spot ETH berhenti; perp ETH tetap ada
        self.assertNotIn(ETH, ledger.present_assets(sp, pit, bar(111)))
        new, notes = ledger.step(sp, pit, now_after(111), chain, pit)
        self.assertEqual([r for r in new if r["type"] == "tick"], [])
        self.assertTrue(any("aset hilang" in x for x in notes), notes)


if __name__ == "__main__":
    unittest.main()

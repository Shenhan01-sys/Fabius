"""P129 (F-D95): kejadian listing untuk B4-LISTING-FADE - pemindai Vision (tools/listing_events.py), pemuat (engine/data.load_events), target flat
B4 di hari tanpa kejadian, dan B4 TUNDA bila pemindaian hari ini belum sukses (tools/paper_tick.py). Jaringan dipalsukan."""
import datetime as dt
import io
import os
import sys
import tempfile
import unittest
import zipfile

from engine.bots import REGISTRY
from engine.data import ListingEvent, MarketData, load_csv_dir, load_events
from engine.series import DAY_MS, Series
from engine.spec import SPECS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import feed_bars as fb                                                    # noqa: E402
import listing_events as le                                               # noqa: E402

T0 = int(dt.datetime(2026, 9, 20, tzinfo=dt.timezone.utc).timestamp() * 1000)
TODAY = T0 + 14 * DAY_MS + 9 * 3_600_000


def kz(rows):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("x.csv", "open_time,o,h,l,c,v,ct,qv\n" + "\n".join(",".join(map(str, r)) for r in rows))
    return b.getvalue()


class FakeVision:
    """Bucket: OLDUSDT (sejak 2020), NEWUSDT (hari-1 = T0+10, volume 5 juta), TINYUSDT (hari-1 = T0+11, volume 0,2 juta), BTCUSDT_261225 (berjangka)."""

    def __init__(self, broken=False):
        self.broken = broken
        self.first = {"OLDUSDT": "2020-01-01", "NEWUSDT": fb.date_of(T0 + 10 * DAY_MS), "TINYUSDT": fb.date_of(T0 + 11 * DAY_MS)}

    def __call__(self, url):
        if self.broken:
            raise fb.FeedError("HTTP 503")
        if "delimiter=/" in url:
            prefixes = "".join(f"<CommonPrefixes><Prefix>{le.PREFIX}{s}/</Prefix></CommonPrefixes>" for s in ["BTCUSDT_261225", *self.first])
            return f"<ListBucketResult><IsTruncated>false</IsTruncated>{prefixes}</ListBucketResult>".encode()
        if "max-keys=1" in url:
            s = next(s for s in self.first if f"klines/{s}/1d/&max-keys" in url)
            return f"<ListBucketResult><Key>{le.PREFIX}{s}/1d/{s}-1d-{self.first[s]}.zip</Key></ListBucketResult>".encode()
        for s, d in self.first.items():
            for i in range(0, 15):
                t = T0 + i * DAY_MS
                if f"/{s}-1d-{fb.date_of(t)}.zip" in url and fb.date_of(t) >= d:
                    vol = 5e6 if s == "NEWUSDT" else 2e5
                    return kz([(t, 1.0, 1.1, 0.9, 1.05, 100, t + DAY_MS - 1, vol)])
        return None


class ScanTests(unittest.TestCase):
    def test_new_usdt_perps_become_events_and_only_liquid_ones_get_price_series(self):
        with tempfile.TemporaryDirectory() as d:
            r = le.update(d, TODAY, get=FakeVision(), fetch=FakeVision(), log=lambda s: None)
            self.assertEqual(sorted(r["events_added"]), ["NEWUSDT", "TINYUSDT"])                 # OLD = lama; berjangka ber-_ tidak dihitung
            evs = load_events(d)
            self.assertEqual([(e.asset, e.day1_open_t, e.day1_quote_volume_usd) for e in evs],
                             [("NEWUSDT", T0 + 10 * DAY_MS, 5e6), ("TINYUSDT", T0 + 11 * DAY_MS, 2e5)])
            self.assertTrue(os.path.exists(os.path.join(d, "fut_NEWUSDT_1d.csv")))               # lolos volume minimum B4 (1 juta)
            self.assertFalse(os.path.exists(os.path.join(d, "fut_TINYUSDT_1d.csv")))
            self.assertEqual(open(os.path.join(d, le.STAMP_FILE), encoding="utf-8").read().strip(), fb.date_of(TODAY))
            md = load_csv_dir(d, [])
            self.assertIn("NEWUSDT", md.perp)                                                      # pemuat ikut membawa deret koin baru
            again = le.update(d, TODAY, get=FakeVision(), fetch=FakeVision(), log=lambda s: None)
            self.assertEqual((again["new_symbols"], again["events_added"]), ([], []))              # kedua kali: tidak ada yang diperiksa ulang

    def test_an_unreadable_bucket_raises_and_leaves_no_fresh_stamp(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(fb.FeedError):
                le.update(d, TODAY, get=FakeVision(broken=True), fetch=FakeVision(), log=lambda s: None)
            self.assertFalse(os.path.exists(os.path.join(d, le.STAMP_FILE)))


class B4WaitsForTodaysScanTests(unittest.TestCase):
    def test_b4_is_not_ticked_when_listings_were_not_scanned_today(self):
        import contextlib
        import paper_tick as pt
        now = TODAY
        with tempfile.TemporaryDirectory() as led, tempfile.TemporaryDirectory() as bars:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(pt.init_bot("B4-LISTING-FADE", led, now, False), 0)
            with open(os.path.join(bars, le.STAMP_FILE), "w", encoding="utf-8") as f:
                f.write(fb.date_of(now - DAY_MS) + "\n")                                        # pemindaian terakhir KEMARIN
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = pt.tick_bot("B4-LISTING-FADE", led, pt.Views(bars), now, False)
            self.assertEqual(rc, 4)
            self.assertIn("TUNDA - kejadian listing belum dipindai hari ini", out.getvalue())
            self.assertEqual(len(open(os.path.join(led, "B4-LISTING-FADE.jsonl"), encoding="utf-8").read().splitlines()), 1)   # genesis saja


class B4FlatTargetTests(unittest.TestCase):
    sp = SPECS["B4-LISTING-FADE"]

    def test_days_without_an_active_listing_still_have_a_flat_target_up_to_the_last_bar(self):
        ts = [T0 + i * DAY_MS for i in range(40)]
        one = [1.0] * 40
        btc = Series(ts, one, one, one, one, one)
        evs = [ListingEvent("NEWUSDT", T0 + 5 * DAY_MS, 1.0, 5e6)]
        tg = {x.t: x.weights for x in REGISTRY["B4-LISTING-FADE"](self.sp, MarketData(perp={"BTCUSDT": btc}, events=evs))}
        self.assertEqual(max(tg), ts[-1])                                                          # sampai bar terakhir, tidak lebih
        self.assertEqual(tg[T0 + 6 * DAY_MS], {"NEWUSDT": -0.02})                                   # di dalam jendela H = 14 hari
        self.assertEqual(tg[T0 + 30 * DAY_MS], {})                                                  # sesudahnya flat, bukan "tidak ada target"
        none = REGISTRY["B4-LISTING-FADE"](self.sp, MarketData(perp={"BTCUSDT": btc}))
        self.assertEqual((len(none), none[-1].weights), (40, {}))



class LateListingTests(unittest.TestCase):
    """P173 (28 Okt 2026): Vision menerbitkan MSTUUSDT/RDWUSDT dengan hari-1 2026-10-12 baru 16 hari kemudian; hitung ulang tick B4 2026-10-12 memakai
    event yang belum diketahui saat tick ditulis -> `data_hash` beda -> rantai paper-ledger berhenti. Event membawa `seen_ms`; tick + verify menyaringnya."""
    sp = SPECS["B4-LISTING-FADE"]

    def md(self, events):
        ts = [T0 + i * DAY_MS for i in range(30)]
        one = [1.0] * 30
        return MarketData(perp={a: Series(ts, one, one, one, one, one) for a in self.sp.universe}, events=list(events))

    def test_an_event_recorded_after_the_tick_does_not_change_its_recompute(self):
        from engine import ledger
        t = T0 + 12 * DAY_MS
        emitted = t + DAY_MS + 9 * 3_600_000                                                       # tick ditulis 9 jam sesudah penutupan
        old = ListingEvent("NEWUSDT", T0 + 5 * DAY_MS, 1.0, 5e6)                                   # baris lama: tanpa seen_ms
        late = ListingEvent("LATEUSDT", t, 1.0, 5e6, seen_t=emitted + 16 * DAY_MS)                  # hari-1 = bar tick, tercatat 16 hari kemudian
        then = ledger.compute_tick(self.sp, self.md([old]), t, emitted)
        now = ledger.compute_tick(self.sp, self.md([old, late]), t, emitted)
        self.assertEqual(then, now)
        self.assertNotEqual(ledger.compute_tick(self.sp, self.md([old, late]), t), then)            # tanpa saringan: cacat yang ditutup

    def test_an_event_recorded_in_the_same_run_as_the_tick_is_used(self):
        from engine import ledger
        t = T0 + 12 * DAY_MS
        now_ms = t + DAY_MS + 9 * 3_600_000 + 123                                                  # ms tidak bulat: emitted_utc dibulatkan ke detik
        same = ListingEvent("NEWUSDT", t, 1.0, 5e6, seen_t=now_ms // 1000 * 1000)
        made = ledger.compute_tick(self.sp, self.md([same]), t, now_ms)
        again = ledger.compute_tick(self.sp, self.md([same]), t, ledger.iso_ms(ledger.utc_iso(now_ms)))
        self.assertEqual(made, again)
        self.assertIn("NEWUSDT", made["targets"])

    def test_scan_writes_seen_ms_for_new_rows_only_and_loader_reads_it(self):
        with tempfile.TemporaryDirectory() as bars:
            ep = os.path.join(bars, le.EVENTS_FILE)
            with open(ep, "w", encoding="utf-8", newline="\n") as f:
                f.write("asset,day1_open_t,day1_close,day1_quote_volume_usd\nLEGACYUSDT,%d,1.0,5000000.0\n" % (T0 + DAY_MS))
            le.update(bars, TODAY, get=FakeVision(), fetch=FakeVision(), log=lambda *_: None, seen_ms=TODAY + 456)
            ev = {e.asset: e for e in load_events(bars)}
            self.assertIsNone(ev["LEGACYUSDT"].seen_t)
            self.assertEqual(ev["NEWUSDT"].seen_t, (TODAY + 456) // 1000 * 1000)


if __name__ == "__main__":
    unittest.main()

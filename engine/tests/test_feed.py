"""tools/feed_bars.py: perpanjangan CSV bar harian dan funding dengan `fetch` yang disuntikkan (tanpa jaringan)."""
import csv
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile

from engine.series import DAY_MS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import feed_bars as fb                                           # noqa: E402

D0 = 1_577_836_800_000                                           # 2020-01-01 00:00 UTC


def kline_zip(rows, header=False):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    if header:
        w.writerow(["open_time", "open", "high", "low", "close", "volume", "close_time"])
    for r in rows:
        w.writerow(r)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("x.csv", buf.getvalue())
    return out.getvalue()


def fund_zip(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["calc_time", "funding_interval_hours", "last_funding_rate"])
    for t, r in rows:
        w.writerow([t, 8, r])
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("f.csv", buf.getvalue())
    return out.getvalue()


def bar(d, c=100.0):
    return (D0 + d * DAY_MS, c, c * 1.01, c * 0.99, c, 5.0)


def rd(path, mode="rb"):
    with open(path, mode) as f:
        return f.read()


def seed(path, days, header=True):
    with open(path, "w", newline="") as f:
        f.write("t,o,h,l,c,v\n" if header else "")
        for d in range(days):
            t, o, h, l, c, v = bar(d)
            f.write(f"{t},{o},{h},{l},{c},{v}\n")


class KlineTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.path = os.path.join(self.d, "fut_BTCUSDT_1d.csv")
        seed(self.path, 3)                                       # hari 0,1,2

    def fetch_for(self, days_published, header=True):
        def fetch(url):
            day = url.rsplit("-1d-", 1)[1][:10]
            for d in days_published:
                if fb.date_of(D0 + d * DAY_MS) == day:
                    return kline_zip([bar(d, 100 + d)], header=header)
            return None
        return fetch

    def test_appends_only_closed_published_days_in_order(self):
        before = rd(self.path)
        rep = fb.update_klines(self.d, "fut", "BTCUSDT", D0 + 6 * DAY_MS, self.fetch_for([3, 4, 5, 6]))   # hari ini = hari 6 -> bar 6 belum tertutup
        self.assertEqual(rep["added"], 3)                                                                   # 3, 4, 5 saja
        self.assertEqual(fb.date_of(fb.last_t(self.path)), fb.date_of(D0 + 5 * DAY_MS))
        self.assertTrue(rd(self.path).startswith(before))                                    # baris lama tidak disentuh

    def test_stops_at_the_first_unpublished_day_and_never_skips_a_hole(self):
        rep = fb.update_klines(self.d, "fut", "BTCUSDT", D0 + 8 * DAY_MS, self.fetch_for([3, 5, 6]))        # hari 4 belum terbit
        self.assertEqual(rep["added"], 1)
        self.assertIn("belum terbit", rep["stop"])
        self.assertEqual(fb.date_of(fb.last_t(self.path)), fb.date_of(D0 + 3 * DAY_MS))                     # 5 dan 6 TIDAK dilompati

    def test_rejects_a_bar_with_the_wrong_day_or_bad_prices(self):
        bad_day = lambda url: kline_zip([bar(9)])                                                           # selalu hari 9
        rep = fb.update_klines(self.d, "fut", "BTCUSDT", D0 + 6 * DAY_MS, bad_day)
        self.assertEqual(rep["added"], 0)
        self.assertIn("0 baris", rep["stop"] or "")                                                         # tidak ada baris untuk hari yang diminta
        neg = lambda url: kline_zip([(D0 + 3 * DAY_MS, -1.0, 1.0, 1.0, 1.0, 1.0)])
        rep = fb.update_klines(self.d, "fut", "BTCUSDT", D0 + 6 * DAY_MS, neg)
        self.assertEqual(rep["added"], 0)
        self.assertIn("tidak positif", rep["stop"])
        hl = lambda url: kline_zip([(D0 + 3 * DAY_MS, 100.0, 99.0, 98.0, 100.0, 1.0)])                      # high < open/close
        self.assertEqual(fb.update_klines(self.d, "fut", "BTCUSDT", D0 + 6 * DAY_MS, hl)["added"], 0)

    def test_network_failure_is_reported_not_guessed(self):
        def boom(url):
            raise fb.FeedError("HTTP 451 untuk x")
        rep = fb.update_klines(self.d, "fut", "BTCUSDT", D0 + 6 * DAY_MS, boom)
        self.assertEqual(rep["added"], 0)
        self.assertIn("451", rep["stop"])

    def test_missing_seed_is_refused(self):
        rep = fb.update_klines(self.d, "fut", "ETHUSDT", D0 + 6 * DAY_MS, self.fetch_for([3]))
        self.assertEqual(rep["added"], 0)
        self.assertIn("seed", rep["stop"])

    def test_dry_run_writes_nothing_and_microsecond_spot_times_are_normalized(self):
        before = rd(self.path)
        rep = fb.update_klines(self.d, "fut", "BTCUSDT", D0 + 5 * DAY_MS, self.fetch_for([3, 4]), dry_run=True)
        self.assertEqual(rep["added"], 2)
        self.assertEqual(rd(self.path), before)
        self.assertEqual(fb._ms((D0 + 3 * DAY_MS) * 1000), D0 + 3 * DAY_MS)                                  # mikrodetik -> milidetik

    def test_update_all_skips_nothing_silently(self):
        reps = fb.update_all(self.d, ["BTCUSDT", "ETHUSDT"], D0 + 5 * DAY_MS, funding=False, fetch=self.fetch_for([3, 4]))
        by = {r["sym"]: r for r in reps}
        self.assertEqual(by["BTCUSDT"]["added"], 2)
        self.assertIn("seed", by["ETHUSDT"]["stop"])


class FundingTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.path = os.path.join(self.d, "fund_BTCUSDT.csv")
        with open(self.path, "w", newline="") as f:
            f.write("t,rate\n")
            for d in range(2):
                for h in (0, 8, 16):
                    f.write(f"{D0 + d * DAY_MS + h * 3_600_000 + 1},0.0001\n")                              # +1 ms, seperti zip Binance

    def rest(self, events):
        def fetch(url):
            if "fapi/v1/fundingRate" in url:
                return json.dumps([{"symbol": "BTCUSDT", "fundingTime": t, "fundingRate": str(r), "markPrice": "1"} for t, r in events]).encode()
            return None
        return fetch

    def test_rest_extends_with_complete_days_only_and_dedupes_the_same_event(self):
        last = D0 + 1 * DAY_MS + 16 * 3_600_000 + 1
        ev = [(last - 1, 0.0001)]                                                                           # peristiwa yang SAMA dengan baris terakhir (beda 1 ms)
        ev += [(D0 + 2 * DAY_MS + h * 3_600_000, 0.0002) for h in (0, 8, 16)]                               # hari 2 lengkap
        ev += [(D0 + 3 * DAY_MS, 0.0003)]                                                                   # awal hari ini: belum lengkap -> tidak masuk
        rep = fb.update_funding(self.d, "BTCUSDT", D0 + 3 * DAY_MS, self.rest(ev))
        self.assertEqual(rep["added"], 3)
        rows = list(csv.reader(io.StringIO(rd(self.path, "r"))))[1:]
        self.assertEqual(len(rows), 9)
        self.assertEqual(fb.date_of(fb.last_t(self.path)), fb.date_of(D0 + 2 * DAY_MS))

    def test_rest_pagination_uses_the_last_time_as_cursor(self):
        calls = []

        def fetch(url):
            calls.append(url)
            start = int(url.split("startTime=")[1].split("&")[0])
            k = len(calls)
            if k == 1:
                return json.dumps([{"fundingTime": D0 + 2 * DAY_MS + i * 3_600_000 * 8, "fundingRate": "0.0001"} for i in range(1000)]).encode()
            return json.dumps([]).encode()
        rep = fb.update_funding(self.d, "BTCUSDT", D0 + 2000 * DAY_MS, fetch)
        self.assertEqual(len(calls), 2)
        self.assertEqual(rep["added"], 1000)
        self.assertGreater(int(calls[1].split("startTime=")[1].split("&")[0]), D0 + 2 * DAY_MS)

    def test_rest_failure_falls_back_to_closed_months_only_and_says_so(self):
        # seed berakhir di Jan 2020; "hari ini" = 10 Maret 2020: zip bulanan Feb sah, Maret belum tutup -> tidak diminta
        feb = [(D0 + (31 + d) * DAY_MS + h * 3_600_000 + 3, 0.0002) for d in range(29) for h in (0, 8, 16)]
        asked = []

        def fetch(url):
            asked.append(url)
            if "fapi.binance.com" in url:
                raise fb.FeedError("SSLError untuk fapi")
            if url.endswith("2020-01.zip"):
                return fund_zip([(D0 + d * DAY_MS + h * 3_600_000 + 3, 0.0001) for d in range(31) for h in (0, 8, 16)])   # tumpang tindih dengan seed
            if url.endswith("2020-02.zip"):
                return fund_zip(feb)
            return None
        today = D0 + (31 + 29 + 9) * DAY_MS
        rep = fb.update_funding(self.d, "BTCUSDT", today, fetch)
        self.assertEqual(rep["added"], 29 * 3 + 29 * 3)                                                # Jan 3-31 (87) + Feb (87); peristiwa tumpang tindih dengan seed dibuang
        self.assertIn("REST gagal", rep["note"])
        self.assertFalse(any(u.endswith("2020-03.zip") for u in asked))                                # bulan berjalan tidak diminta
        rows = [int(float(r[0])) for r in list(csv.reader(io.StringIO(rd(self.path, "r"))))[1:]]
        self.assertEqual(rows, sorted(rows))
        self.assertEqual(len(rows), len(set(rows)))
        gaps = [b - a for a, b in zip(rows, rows[1:])]
        self.assertGreater(min(gaps), 60_000)                                                          # tak ada peristiwa ganda (beda ms)

    def test_missing_seed_is_refused(self):
        rep = fb.update_funding(self.d, "ETHUSDT", D0 + 5 * DAY_MS, self.rest([]))
        self.assertEqual(rep["added"], 0)
        self.assertIn("seed", rep["stop"])


if __name__ == "__main__":
    unittest.main()

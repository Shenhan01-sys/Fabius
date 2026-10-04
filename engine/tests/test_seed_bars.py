"""P128 (F-D95): penanam berkas bar baru dari Binance Vision (tools/seed_bars.py). Zip dipalsukan; tanpa jaringan."""
import datetime as dt
import io
import os
import sys
import tempfile
import unittest
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import feed_bars as fb                                                    # noqa: E402
import seed_bars as sb                                                    # noqa: E402

D = fb.DAY_MS
T0 = int(dt.datetime(2026, 8, 1, tzinfo=dt.timezone.utc).timestamp() * 1000)


def z(rows):
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as zf:
        zf.writestr("x.csv", "\n".join(",".join(map(str, r)) for r in rows))
    return b.getvalue()


def bars(start_day, n):
    return [(T0 + (start_day + i) * D, 10, 11, 9, 10.5, 5, 0) for i in range(n)]


class SeedTests(unittest.TestCase):
    def fetch(self, url, aug=None):
        if "monthly" in url and "2026-07" in url:
            return None                                                   # simbol belum terdaftar
        if "monthly" in url and "2026-08" in url:
            return z(aug if aug is not None else bars(0, 31))
        if "monthly" in url and "2026-09" in url:
            return None                                                   # zip bulanan belum terbit -> harian
        for i in range(31, 62):
            if "daily" in url and fb.date_of(T0 + i * D) in url:
                return z(bars(i, 1))
        return None

    def test_seeds_monthly_then_daily_without_holes_and_never_overwrites(self):
        today = T0 + 62 * D + 3_600_000
        rows = sb.collect("spot", "PAXGUSDT", "2026-07", today, self.fetch)
        self.assertEqual((len(rows), fb.date_of(rows[0][0]), fb.date_of(rows[-1][0])), (62, "2026-08-01", "2026-10-01"))
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "spot_PAXGUSDT_1d.csv")
            sb.write(p, rows)
            self.assertEqual(fb.last_t(p), rows[-1][0])
            with self.assertRaises(sb.SeedError):
                sb.write(p, rows)

    def test_a_missing_day_refuses_the_whole_seed(self):
        hole = bars(0, 10) + bars(11, 20)
        with self.assertRaises(sb.SeedError):
            sb.collect("spot", "PAXGUSDT", "2026-07", T0 + 62 * D, lambda u: self.fetch(u, aug=hole))


if __name__ == "__main__":
    unittest.main()

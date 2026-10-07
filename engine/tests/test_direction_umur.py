"""P71: guard umur bar di `tools/direction.py` - cache 1 jam yang basi diambil ulang, yang masih basi TIDAK dinilai - dengan inti yang sama dengan
mesin (`engine/freshness.cek_umur`). Kasus nyata: MARSCOIN di-anchor 27 Sep 08:08Z dengan bar terakhir yang tertutup 26 Sep 18:00Z (14 jam)."""
import calendar
import os
import sys
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, ROOT)

from engine.freshness import StaleBars, assert_fresh, cek_umur   # noqa: E402
from engine.series import DAY_MS, Series                          # noqa: E402

H = 3_600_000


def ms(iso: str) -> int:
    return calendar.timegm(time.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")) * 1000


def deret_1j(akhir_buka: int, n: int = 30) -> list:
    return [{"t": akhir_buka - (n - 1 - i) * H, "o": 1.0, "h": 1.0, "l": 1.0, "c": 1.0 + i / 1000, "v": 1.0, "n": 1} for i in range(n)]


class CekUmurTests(unittest.TestCase):
    def test_an_hourly_bar_must_be_closed_and_recent(self):
        now = ms("2026-09-27T08:08:00Z")
        self.assertEqual(cek_umur("X", ms("2026-09-27T07:00:00Z"), now, H, 2 * H), 8 * 60 * 1000)        # tertutup 08:00, umur 8 menit
        self.assertEqual(cek_umur("X", now - 3 * H, now, H, 2 * H), 2 * H)                              # tepat di batas = masih boleh
        with self.assertRaisesRegex(StaleBars, "belum tertutup"):
            cek_umur("X", ms("2026-09-27T08:00:00Z"), now, H, 2 * H)                                     # bar berjalan = harga setengah jadi
        with self.assertRaisesRegex(StaleBars, "basi"):
            cek_umur("MARSCOIN", ms("2026-09-26T17:00:00Z"), now, H, 2 * H)                              # kasus 27 Sep: 14,1 jam
        with self.assertRaisesRegex(StaleBars, "tidak ada bar"):
            cek_umur("X", None, now, H, 2 * H)

    def test_the_daily_guard_keeps_its_behaviour(self):
        t0 = ms("2026-09-01T00:00:00Z")
        s = Series.from_rows([[t0 + i * DAY_MS, 1, 1, 1, 1, 1] for i in range(3)])
        close = s.t[-1] + DAY_MS
        assert_fresh("x", s, close + H)
        with self.assertRaisesRegex(StaleBars, "belum tertutup"):
            assert_fresh("x", s, close - H)
        with self.assertRaisesRegex(StaleBars, "13.0 jam lalu .* basi"):
            assert_fresh("x", s, close + 13 * H)
        with self.assertRaisesRegex(StaleBars, "tidak ada bar"):
            assert_fresh("x", Series((), (), (), (), (), ()), close)


class MuatBarTests(unittest.TestCase):
    """`direction.muat_bar`: cache dipakai hanya bila segar; basi -> ambil ulang; masih basi -> ditandai, pemanggil tidak menilainya."""

    def setUp(self):
        import direction
        self.d = direction
        self.now = ms("2026-09-27T08:08:00Z")
        self.ambil, self.simpan = [], []

    def jalankan(self, cache, segar):
        def load(sym, iv):
            return None if cache is None else {"meta": {}, "bars": cache}

        def fetch(sym, iv, days, verbose=True):
            self.ambil.append((sym, iv, days))
            return segar, {"pages": 7}

        def save(sym, iv, b, meta):
            self.simpan.append((sym, iv, len(b), meta))
        return self.d.muat_bar("MARSCOINUSDT", self.now, load, fetch, save)

    def test_a_fresh_cache_is_used_without_fetching(self):
        cache = deret_1j(ms("2026-09-27T07:00:00Z"))
        data, info = self.jalankan(cache, [])
        self.assertIs(data, cache)
        self.assertEqual((info["sumber"], info["basi"], self.ambil), ("cache", None, []))
        self.assertAlmostEqual(info["umur_jam"], 0.13, places=2)

    def test_a_stale_cache_is_refetched_and_the_fresh_series_is_used(self):
        cache = deret_1j(ms("2026-09-26T17:00:00Z"))                  # kasus MARSCOIN: tertutup 14 jam sebelum anchor
        segar = deret_1j(ms("2026-09-27T07:00:00Z"))
        data, info = self.jalankan(cache, segar)
        self.assertEqual(len(self.ambil), 1)                         # guard dicabut = cache basi dipakai = tes ini gagal
        self.assertIs(data, segar)
        self.assertEqual((info["sumber"], info["basi"], info["t_last"]), ("ambil", None, segar[-1]["t"]))
        self.assertEqual(self.simpan[0][2:], (len(segar), {"pages": 7}))   # meta ambil diteruskan apa adanya

    def test_still_stale_after_refetch_is_flagged_not_judged(self):
        cache = deret_1j(ms("2026-09-26T17:00:00Z"))
        juga_basi = deret_1j(ms("2026-09-26T20:00:00Z"))              # venue berhenti (delist / halt): ambil ulang tetap basi
        data, info = self.jalankan(cache, juga_basi)
        self.assertEqual(info["sumber"], "ambil")
        self.assertIn("basi", info["basi"])
        self.assertIsNone(info["umur_jam"])
        data, info = self.jalankan(None, [])                         # tidak ada cache dan venue kosong
        self.assertEqual((data, info["sumber"]), ([], "cache"))
        self.assertIn("tidak ada bar", info["basi"])

    def test_main_skips_a_stale_symbol_and_hashes_the_bar_age(self):
        with open(self.d.__file__, encoding="utf-8") as f:
            src = f.read()
        self.assertIn('data, umur_bar = muat_bar(psym)', src)                  # jalur main memakai guard, bukan bars.load langsung
        self.assertIn('if umur_bar["basi"]:', src)
        self.assertNotIn('cached = bars.load(psym, "1h")', src)
        _, meta = self.d.snap_hash_for("X", {"t_last": 1, "umur_bar_jam": 0.5}, {})
        self.assertEqual(meta["last_bar_age_h"], 0.5)                          # umur bar ikut snapshotHash -> decisionHash


if __name__ == "__main__":
    unittest.main()

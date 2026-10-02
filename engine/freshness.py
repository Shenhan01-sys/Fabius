"""Guard umur bar - menutup cacat 2 Okt 2026: `direction.py` memuat cache bar tanpa memeriksa umurnya, sehingga long MARSCOIN
yang di-anchor 27 Sep 08:08Z memakai bar terakhir 26 Sep 18:00Z dan stop-nya sudah tersentuh 8 jam sebelum anchor
(lihat vault/09-Inbox/Session-2026-10-02.md temuan 1).

Aturan: bar terakhir harus SUDAH tertutup (t + 1 hari <= sekarang; kalau tidak, bar itu masih berjalan = look-ahead pada
harga) dan tidak boleh lebih tua dari `max_lag_ms` sejak penutupannya.
"""
from __future__ import annotations

from .series import DAY_MS, Series

DEFAULT_MAX_LAG_MS = 12 * 3_600_000


class StaleBars(Exception):
    pass


def assert_fresh(name: str, s: Series, now_ms: int, max_lag_ms: int = DEFAULT_MAX_LAG_MS) -> None:
    if len(s) == 0:
        raise StaleBars(f"{name}: tidak ada bar")
    close_t = s.t[-1] + DAY_MS
    lag = now_ms - close_t
    if lag < 0:
        raise StaleBars(f"{name}: bar terakhir (buka {s.t[-1]}) belum tertutup - tolak, bukan pakai harga setengah jadi")
    if lag > max_lag_ms:
        raise StaleBars(f"{name}: bar terakhir tertutup {lag / 3_600_000:.1f} jam lalu (> {max_lag_ms / 3_600_000:.0f} jam) - basi")

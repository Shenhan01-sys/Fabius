"""Guard umur bar - menutup cacat 2 Okt 2026: `direction.py` memuat cache bar tanpa memeriksa umurnya, sehingga long MARSCOIN
yang di-anchor 27 Sep 08:08Z memakai bar terakhir 26 Sep 18:00Z dan stop-nya sudah tersentuh 8 jam sebelum anchor
(lihat vault/09-Inbox/Session-2026-10-02.md temuan 1).

Aturan: bar terakhir harus SUDAH tertutup (t + panjang bar <= sekarang; kalau tidak, bar itu masih berjalan = look-ahead pada
harga) dan tidak boleh lebih tua dari `max_lag_ms` sejak penutupannya. `cek_umur` = inti untuk panjang bar apa pun (harian di mesin,
1 jam di `tools/direction.py`, P71); `assert_fresh` = bentuk harian untuk `Series`, perilakunya tidak berubah.
"""
from __future__ import annotations

from typing import Optional

from .series import DAY_MS, Series

DEFAULT_MAX_LAG_MS = 12 * 3_600_000


class StaleBars(Exception):
    pass


def cek_umur(name: str, t_buka_terakhir: Optional[int], now_ms: int, bar_ms: int = DAY_MS, max_lag_ms: int = DEFAULT_MAX_LAG_MS) -> int:
    """-> umur (ms) sejak penutupan bar terakhir. StaleBars bila tidak ada bar, bar terakhir belum tertutup, atau lebih tua dari `max_lag_ms`."""
    if t_buka_terakhir is None:
        raise StaleBars(f"{name}: tidak ada bar")
    lag = now_ms - (int(t_buka_terakhir) + bar_ms)
    if lag < 0:
        raise StaleBars(f"{name}: bar terakhir (buka {t_buka_terakhir}) belum tertutup - tolak, bukan pakai harga setengah jadi")
    if lag > max_lag_ms:
        raise StaleBars(f"{name}: bar terakhir tertutup {lag / 3_600_000:.1f} jam lalu (> {max_lag_ms / 3_600_000:.0f} jam) - basi")
    return lag


def assert_fresh(name: str, s: Series, now_ms: int, max_lag_ms: int = DEFAULT_MAX_LAG_MS) -> None:
    cek_umur(name, s.t[-1] if len(s) else None, now_ms, DAY_MS, max_lag_ms)

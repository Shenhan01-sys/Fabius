"""Deret harga harian dan alat hitung murni (stdlib saja; tanpa numpy/pandas).

Konvensi mesin (sama dengan layar eksploratif 2 Okt 2026):
  - satu bar = satu hari UTC, `t` = waktu BUKA bar dalam ms; bar baru "tertutup" saat t + 1 hari <= sekarang;
  - sinyal dihitung di PENUTUPAN bar i dari data <= i, posisi berlaku untuk return bar i+1;
  - simpangan baku memakai ddof=1 (sama dengan pandas rolling().std()).
"""
from __future__ import annotations

import bisect
import math
from dataclasses import dataclass
from typing import Optional, Sequence

DAY_MS = 86_400_000


@dataclass(frozen=True)
class Series:
    """OHLCV harian, terlama dulu. Semua tuple supaya hashable dan tak bisa diubah diam-diam."""
    t: tuple
    o: tuple
    h: tuple
    l: tuple
    c: tuple
    v: tuple

    @classmethod
    def from_rows(cls, rows: Sequence[Sequence[float]]) -> "Series":
        rows = sorted(rows, key=lambda r: r[0])
        seen, out = set(), []
        for r in rows:                      # dedupe per waktu (pertama menang), seperti loader eksploratif
            if r[0] in seen:
                continue
            seen.add(r[0])
            out.append(r)
        return cls(tuple(int(r[0]) for r in out), tuple(float(r[1]) for r in out), tuple(float(r[2]) for r in out),
                   tuple(float(r[3]) for r in out), tuple(float(r[4]) for r in out), tuple(float(r[5]) for r in out))

    def __len__(self) -> int:
        return len(self.t)

    def index_at_or_before(self, t_ms: int) -> int:
        """Indeks bar terakhir dengan waktu buka <= t_ms; -1 bila belum ada."""
        return bisect.bisect_right(self.t, t_ms) - 1

    def upto(self, t_ms: int) -> "Series":
        """Potong ke bar dengan waktu buka <= t_ms (point-in-time)."""
        n = bisect.bisect_right(self.t, t_ms)
        return Series(self.t[:n], self.o[:n], self.h[:n], self.l[:n], self.c[:n], self.v[:n])


def rolling_mean(x: Sequence[Optional[float]], n: int) -> list:
    out = [None] * len(x)
    for i in range(n - 1, len(x)):
        w = x[i - n + 1:i + 1]
        if any(v is None for v in w):
            continue
        out[i] = sum(w) / n
    return out


def rolling_std(x: Sequence[Optional[float]], n: int) -> list:
    """Simpangan baku sampel (ddof=1) jendela n; None bila ada None di jendela."""
    out = [None] * len(x)
    for i in range(n - 1, len(x)):
        w = x[i - n + 1:i + 1]
        if any(v is None for v in w):
            continue
        m = sum(w) / n
        out[i] = math.sqrt(sum((v - m) ** 2 for v in w) / (n - 1))
    return out


def pct_change(c: Sequence[Optional[float]]) -> list:
    out = [None] * len(c)
    for i in range(1, len(c)):
        if c[i] is not None and c[i - 1] not in (None, 0):
            out[i] = c[i] / c[i - 1] - 1.0
    return out


def sharpe(pnl: Sequence[Optional[float]], ppy: int = 365) -> float:
    x = [v for v in pnl if v is not None]
    if len(x) < 30:
        return float("nan")
    m = sum(x) / len(x)
    s = math.sqrt(sum((v - m) ** 2 for v in x) / (len(x) - 1))
    return (m * ppy) / (s * math.sqrt(ppy)) if s > 0 else float("nan")


def max_drawdown(pnl: Sequence[Optional[float]]) -> float:
    eq, peak, mdd = 1.0, 1.0, 0.0
    for v in pnl:
        if v is None:
            continue
        eq *= (1.0 + v)
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1.0)
    return mdd

"""Kualitas data: bolong bar (tak-terukur != bersih).

2 Okt 2026: lima perp (SOL, XRP, LTC, TRX, NEAR) bolong 26-28 Feb 2022 dan 1-2 Apr 2022 pada unduhan Binance Vision. Layar
pandas menghitung return melintasi bolong sebagai satu hari (pct_change) dan memberi posisi palsu; mesin tidak memegang aset
yang tak punya bar pada hari itu. Bolong dicatat di sini supaya selalu terlihat, bukan disembunyikan.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from .data import MarketData
from .series import DAY_MS, Series

Gap = Tuple[int, int]        # (waktu buka bar sebelum bolong, waktu buka bar sesudah bolong)


def find_gaps(s: Series) -> List[Gap]:
    return [(s.t[i - 1], s.t[i]) for i in range(1, len(s)) if s.t[i] - s.t[i - 1] != DAY_MS]


def gap_report(data: MarketData) -> Dict[str, List[Gap]]:
    out: Dict[str, List[Gap]] = {}
    for kind, bag in (("perp", data.perp), ("spot", data.spot)):
        for a, s in sorted(bag.items()):
            g = find_gaps(s)
            if g:
                out[f"{kind}:{a}"] = g
    return out


def missing_days(g: Gap) -> int:
    return (g[1] - g[0]) // DAY_MS - 1

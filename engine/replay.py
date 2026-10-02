"""Replay PnL harian dari deret target (penggaris yang sama dengan layar eksploratif 2 Okt 2026).

pnl[T] = sum_a w[T-1][a] * r[T][a]  -  turnover * biaya_per_sisi * kaki  -  funding yang dibayar (bot perp)
dengan w[T-1] = target pada penutupan bar sebelumnya. B3 memakai return hedged (spot - perp + funding diterima),
B5 memakai return spot tanpa funding. B4 (event) menyusul di M2.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .bots import REGISTRY
from .data import MarketData
from .series import Series
from .spec import BotSpec
from .target import Target


def _ret_table(s: Series) -> Dict[int, float]:
    out = {}
    for i in range(1, len(s)):
        if s.c[i - 1] not in (0, None):
            out[s.t[i]] = s.c[i] / s.c[i - 1] - 1.0
    return out


@dataclass(frozen=True)
class Tables:
    """Tabel return harian per aset; dibangun sekali lalu dipakai ulang (placebo menjalankan ratusan replay)."""
    perp: Dict[str, Dict[int, float]]
    spot: Dict[str, Dict[int, float]]


def prepare(data: MarketData) -> Tables:
    return Tables({a: _ret_table(s) for a, s in data.perp.items()}, {a: _ret_table(s) for a, s in data.spot.items()})


def replay(spec: BotSpec, data: MarketData, tg: Optional[List[Target]] = None,
           tables: Optional[Tables] = None) -> List[Tuple[int, float]]:
    if spec.method == "B4-LISTING-FADE":
        raise NotImplementedError("replay B4 butuh deret perp tiap event (M2)")
    tg = tg if tg is not None else REGISTRY[spec.method](spec, data)
    cost = float(spec.penggaris.get("fee_bps_sisi", spec.penggaris.get("fee_bps_sisi_per_kaki", 0.0))) / 1e4
    legs = 2 if spec.method == "B3-CARRY" else 1
    tb = tables if tables is not None else prepare(data)
    perp, spot = tb.perp, tb.spot
    out: List[Tuple[int, float]] = []
    for k in range(1, len(tg)):
        T = tg[k].t
        w = tg[k - 1].weights
        w_prev = tg[k - 2].weights if k >= 2 else {}
        pnl = 0.0
        for a, wa in w.items():
            f = data.funding.get(a, {}).get(T, 0.0)
            if spec.method == "B3-CARRY":
                rs, rp = spot.get(a, {}).get(T), perp.get(a, {}).get(T)
                if rs is None or rp is None:
                    continue
                pnl += wa * (rs - rp + f)
            elif spec.method == "B5-CORE-RWA":
                r = spot.get(a, {}).get(T)
                if r is not None:
                    pnl += wa * r
            else:
                r = perp.get(a, {}).get(T)
                if r is None:
                    continue
                pnl += wa * r - wa * f
        turn = sum(abs(w.get(a, 0.0) - w_prev.get(a, 0.0)) for a in set(w) | set(w_prev))
        pnl -= turn * cost * legs
        out.append((T, pnl))
    return out

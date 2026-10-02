"""B6-BOUNCE: beli bila z-score harga < -z_masuk (rerata dan simpangan baku N hari, ddof=1); keluar saat z >= z_keluar.

Mesin keadaan per aset dihitung ulang dari seluruh riwayat (tanpa keadaan tersimpan) - deterministik dan point-in-time.
Bobot = 1 / (jumlah aset yang punya bar) untuk aset yang sedang dipegang.
"""
from __future__ import annotations

from typing import Dict, List

from ..data import MarketData, aligned_closes
from ..series import rolling_mean, rolling_std
from ..spec import BotSpec
from ..target import Target


def _positions(closes: List[float], n: int, z_in: float, z_out: float) -> List[float]:
    m = rolling_mean(closes, n)
    s = rolling_std(closes, n)
    pos, cur = [], 0.0
    for i, c in enumerate(closes):
        if m[i] is not None and s[i] not in (None, 0):
            z = (c - m[i]) / s[i]
            if cur == 0.0:
                if z < -z_in:
                    cur = 1.0
            elif z >= z_out:
                cur = 0.0
        pos.append(cur)
    return pos


def targets(spec: BotSpec, data: MarketData) -> List[Target]:
    n = int(spec.param)
    z_in = float(spec.konstanta["z_masuk"])
    z_out = float(spec.konstanta["z_keluar"])
    assets = [a for a in spec.universe if a in data.perp]
    pos_by_asset: Dict[str, Dict[int, float]] = {}
    for a in assets:
        s = data.perp[a]
        pos_by_asset[a] = dict(zip(s.t, _positions(list(s.c), n, z_in, z_out)))
    grid, closes = aligned_closes(data.perp, assets)
    out: List[Target] = []
    for i, t in enumerate(grid):
        avail = [a for a in assets if closes[a][i] is not None]
        if not avail:
            continue
        w = {a: 1.0 / len(avail) for a in avail if pos_by_asset[a].get(t, 0.0) > 0}
        out.append(Target(spec.bot_id, t, w, {"N": n, "n_aset": len(avail)}))
    return out

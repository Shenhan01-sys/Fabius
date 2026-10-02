"""B3-CARRY: long spot + short perp saat funding rata-rata 7 hari (disetahunkan) > theta; selain itu flat.

Bobot = fraksi anggaran pada UNIT hedged (satu unit = long spot + short perp dengan nosional sama); dibagi rata atas aset
yang punya spot, perp, dan funding pada hari itu.
"""
from __future__ import annotations

from typing import List

from ..data import MarketData
from ..series import DAY_MS
from ..spec import BotSpec
from ..target import Target


def targets(spec: BotSpec, data: MarketData) -> List[Target]:
    """Jendela funding harus PENUH (win hari kalender berturut-turut ada datanya): hari yang hilang tidak dianggap 0 -
    aset yang baru muncul atau yang datanya bolong tidak ditandai (versi awal layar eksploratif tidak punya cacat ini,
    versi mesin pertama punya; ditangkap oleh perbandingan dengan rujukan pandas 2 Okt 2026)."""
    theta = float(spec.param)
    win = int(spec.konstanta["jendela_funding_hari"])
    ann = int(spec.konstanta["hari_setahun"])
    assets = [a for a in spec.universe if a in data.perp and a in data.spot and a in data.funding]
    if not assets:
        return []
    grid = sorted({t for a in assets for t in data.perp[a].t})
    have = {a: set(data.perp[a].t) & set(data.spot[a].t) for a in assets}
    out: List[Target] = []
    for t in grid:
        avail = [a for a in assets if t in have[a]]
        if not avail:
            continue
        w = {}
        days = [t - j * DAY_MS for j in range(win)]
        for a in avail:
            f = data.funding[a]
            if not all(d in f for d in days):
                continue
            if sum(f[d] for d in days) / win * ann > theta:
                w[a] = 1.0 / len(avail)
        out.append(Target(spec.bot_id, t, w, {"theta": theta, "n_aset": len(avail), "kaki": "long_spot+short_perp"}))
    return out

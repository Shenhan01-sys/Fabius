"""B4-LISTING-FADE: short perp yang baru onboard pada penutupan bar hari-1; tutup H hari kemudian.

Target pada penutupan bar t memuat event e bila  day1_open_t <= t < day1_open_t + H hari  (posisi dipegang untuk return bar
t1+1 ... t1+H). Ukuran tetap kecil per trade; tanpa stop (margin isolated + leverage <= 1 menggantikan stop - stop 30-50 %
terukur menghapus edge; lihat vault/08-Backlog/05 - Epik Enam Bot.md B4).

M1: hanya target (apa yang dipegang). Replay PnL B4 butuh deret perp tiap event (M2).
"""
from __future__ import annotations

from typing import List

from ..data import MarketData
from ..series import DAY_MS
from ..spec import BotSpec
from ..target import Target


def targets(spec: BotSpec, data: MarketData) -> List[Target]:
    h = int(spec.param)
    size = float(spec.konstanta["ukuran_per_trade"])
    min_vol = float(spec.konstanta["min_volume_kuotasi_hari1_usd"])
    evs = [e for e in data.events if e.day1_quote_volume_usd >= min_vol]
    if not evs:
        return []
    t0 = min(e.day1_open_t for e in evs)
    t1 = max(e.day1_open_t for e in evs) + h * DAY_MS
    out: List[Target] = []
    t = t0
    while t <= t1:
        active = [e for e in evs if e.day1_open_t <= t < e.day1_open_t + h * DAY_MS]
        w = {e.asset: -size for e in active}
        out.append(Target(spec.bot_id, t, w, {"H": h, "n_event_aktif": len(active), "ukuran": size}))
        t += DAY_MS
    return out

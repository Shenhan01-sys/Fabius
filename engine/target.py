"""Target = apa yang bot ingin pegang SETELAH penutupan satu bar (fraksi anggaran bot; + long, - short)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class Target:
    bot_id: str
    t: int                                   # waktu BUKA bar terakhir yang tertutup yang dipakai (ms UTC)
    weights: Dict[str, float] = field(default_factory=dict)    # aset -> bobot; aset yang tak tercantum = 0
    meta: Dict[str, object] = field(default_factory=dict)      # diagnostik yang ikut di-hash (bukan untuk dipakai agen)

    def w(self, asset: str) -> float:
        return self.weights.get(asset, 0.0)

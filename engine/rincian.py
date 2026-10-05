"""Rincian paket sinyal yang DIBELI (P138c+, permintaan builder 5 Okt: "open di harga brp, TP, SL, trailing"): semua angka DITURUNKAN dari aturan bot
yang terkunci + bar publik - tidak ada TP/SL/trailing yang tidak dipakai bot (menempelkannya = isi paket berbeda dari ledger + komit on-chain).

B1-TREND (long bila penutupan > penutupan N hari lalu, selain itu flat; bobot sama rata):
  - masuk      = penutupan bar PERTAMA dari run long yang sedang berjalan (aturan), + PnL sampai bar ini (paper, sebelum ongkos);
  - keluar     = bar berikutnya flat bila penutupannya <= penutupan (N-1) bar sebelum bar ini - angka itu SUDAH diketahui hari ini;
  - jadwal     = level keluar beberapa bar ke depan (jendela N bergeser tiap hari -> berperilaku seperti trailing stop berbasis penutupan harian);
  - TP         = tidak ada menurut aturan (tren dibiarkan berjalan sampai momentum berbalik); dinilai pada penutupan harian, bukan intraday.
Bot lain: sisi, bobot, perubahan vs bar sebelumnya + teks aturan (rincian per-aturan menyusul per bot).
Fungsi murni: tidak membaca berkas, jaringan, atau jam.
"""
from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional, Sequence

DAY_MS = 86_400_000


def _date(t_ms: int) -> str:
    return dt.datetime.fromtimestamp(t_ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d")


def perubahan(targets: Dict[str, float], prev: Optional[Dict[str, float]]) -> Dict[str, List[str]]:
    on = lambda d: {a for a, w in (d or {}).items() if abs(float(w)) > 1e-12}   # noqa: E731
    now, before = on(targets), on(prev)
    return {"masuk": sorted(now - before), "keluar": sorted(before - now), "tetap": sorted(now & before)} if prev is not None else \
        {"masuk": sorted(now), "keluar": [], "tetap": []}


def b1_aset(t: Sequence[int], c: Sequence[float], bar_ms: int, n: int, horizon: int = 5) -> Optional[dict]:
    """Rincian satu aset B1 pada bar `bar_ms` (waktu buka bar, = `asof` tick). None bila bar tidak ada di deret."""
    try:
        i = list(t).index(bar_ms)
    except ValueError:
        return None
    if i - n < 0:
        return None
    long = c[i] > c[i - n]
    out = {"sisi": "LONG" if long else "FLAT", "tutup": c[i], "tutup_n_lalu": c[i - n], "momentum": c[i] / c[i - n] - 1}
    nxt = c[i + 1 - n]                                                          # level keluar bar i+1: penutupan bar (i+1)-n, sudah diketahui
    out["keluar_berikut"] = {"bar": _date(t[i] + DAY_MS), "level": nxt, "jarak": nxt / c[i] - 1}
    out["jadwal_keluar"] = [{"bar": _date(t[i] + j * DAY_MS), "level": c[i + j - n]} for j in range(1, horizon + 1) if i + j - n < i + 1]
    if long:
        s = i
        while s - 1 - n >= 0 and c[s - 1] > c[s - 1 - n]:
            s -= 1
        out["masuk"] = {"bar": _date(t[s]), "harga": c[s], "pnl": c[i] / c[s] - 1, "hari": i - s}
    else:
        nxt_on = c[i + 1 - n]
        out["masuk_bila"] = {"bar": _date(t[i] + DAY_MS), "di_atas": nxt_on}
    return out


def rincian(bot: str, metode: str, param, targets: Dict[str, float], prev: Optional[Dict[str, float]], bar_ms: int,
            series: Dict[str, tuple], first_forward_ms: Optional[int] = None, horizon: int = 5) -> dict:
    """`series` = {aset: (t, c)} bar harian publik (`ledger/bars/fut_<SYM>_1d.csv`). -> dict yang ikut di paket (dan di-hash di log gerbang)."""
    out = {"aturan": metode, "param": param, "perubahan": perubahan(targets, prev), "tp": None, "sl": None,
           "catatan": ["dinilai pada penutupan harian 00:00 UTC; sinyal terbit ±08:40 UTC sesudahnya - bukan intraday",
                       "tidak ada TP/SL/trailing di luar aturan: keluar HANYA lewat aturan (lihat level keluar)"],
           "aset": {}}
    if bot == "B1-TREND":
        n = int(param)
        out["catatan"].append(f"level keluar bergeser tiap hari (jendela {n} hari) -> berperilaku seperti trailing stop berbasis penutupan harian")
        for a, w in sorted(targets.items(), key=lambda kv: kv[0]):
            if a not in series:
                continue
            d = b1_aset(series[a][0], series[a][1], bar_ms, n, horizon)
            if d is None:
                continue
            d["bobot"] = float(w)
            if first_forward_ms is not None and d.get("masuk") and d["masuk"]["bar"] < _date(first_forward_ms):
                d["masuk_maju_fabius"] = _date(first_forward_ms)
            out["aset"][a] = d
        near = sorted(((a, d["keluar_berikut"]["jarak"]) for a, d in out["aset"].items() if d["sisi"] == "LONG"), key=lambda x: -x[1])
        out["terdekat_keluar"] = near[0][0] if near else None
    else:
        for a, w in sorted(targets.items()):
            out["aset"][a] = {"sisi": "LONG" if float(w) > 0 else ("SHORT" if float(w) < 0 else "FLAT"), "bobot": float(w)}
    return out

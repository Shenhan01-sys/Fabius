"""F-D116 (DIKUNCI 6 Okt atas kata builder "Gas"): rumus r4 "slot posisi" untuk buku Fabius - fungsi murni yang dipakai SAMA oleh meja hidup
(`meja2.siklus2`) dan replay P163 (`meja_replay.replay_slot`), supaya yang diuji = yang dijalankan. `PARAMS_SLOT` ikut sha PARAMS2 r4.

Per siklus 5 menit (`langkah`): rem rugi -> tutup semua; selain itu tiap posisi dicek SL / TP / aturan keluar bot pembukanya, ditutup pada harga
siklus; siklus yang menutup posisi tidak membuka posisi baru (jeda 1 siklus); sisanya slot kosong (maks 5) diisi kandidat konsensus urut skor.
Ukuran dikunci saat dibuka: margin 3-5 % x leverage 1-5x menurut keyakinan konsensus; satu aset satu posisi; ganti bot tidak menutup posisi.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

import meja

PARAMS_SLOT = {"v": "r4", "maks_posisi": 5, "margin_min": 0.03, "margin_maks": 0.05, "leverage_maks": 5.0, "maks_per_posisi": 0.25,
               "maks_gross": 1.25, "atr_hari": 14, "sl_atr": 1.0, "tp_atr": 2.0, "sl_per_likuidasi": 0.5, "jeda_siklus": 1, "siklus_s": 300,
               "konstanta_bot": {"B4-LISTING-FADE": {"margin": 0.02, "leverage": 1.0, "stop": False}}}    # F-D116 #7: konstanta bot terkunci menang


def buku_baru() -> dict:
    return {"saldo": float(meja.PARAMS["modal_awal"]), "posisi": {}, "biaya": 0.0, "n_trade": 0, "jeda_sampai": 0}


def ekuitas(b: dict, harga: Dict[str, float]) -> float:
    return b["saldo"] + sum(p["qty"] * (harga.get(a, p["masuk"]) - p["masuk"]) for a, p in b["posisi"].items())


def atr_frac(s, n: int = PARAMS_SLOT["atr_hari"]) -> Optional[float]:
    """ATR n hari (rerata true range candle harian yang sudah tutup) sebagai pecahan harga penutupan terakhir; None bila data kurang."""
    if s is None or len(s) < n + 1 or not s.c[-1]:
        return None
    tr = [max(s.h[i] - s.l[i], abs(s.h[i] - s.c[i - 1]), abs(s.l[i] - s.c[i - 1])) for i in range(len(s) - n, len(s))]
    return sum(tr) / n / s.c[-1]


def keyakinan(skor: float, ambang_instrumen: float, n_aktif: int) -> float:
    """0 di ambang instrumen konsensus, 1 bila semua agent aktif memilih aset itu dengan keyakinan 100."""
    if n_aktif <= ambang_instrumen:
        return 0.0
    return max(0.0, min(1.0, (skor - ambang_instrumen) / (n_aktif - ambang_instrumen)))


def ukuran(c: float, bot: str, atr: float, P: dict = PARAMS_SLOT) -> dict:
    """-> {margin, leverage, notional (pecahan ekuitas), stop}. Leverage dipotong supaya jarak SL <= sl_per_likuidasi x jarak likuidasi (1/L)."""
    k = P["konstanta_bot"].get(bot)
    if k:
        return {"margin": k["margin"], "leverage": k["leverage"], "notional": k["margin"] * k["leverage"], "stop": k["stop"]}
    margin = P["margin_min"] + (P["margin_maks"] - P["margin_min"]) * c
    lev = 1.0 + (P["leverage_maks"] - 1.0) * c
    lev = max(1.0, min(lev, P["sl_per_likuidasi"] / max(P["sl_atr"] * atr, 1e-12)))
    return {"margin": round(margin, 6), "leverage": round(lev, 4), "notional": round(min(margin * lev, P["maks_per_posisi"]), 6), "stop": True}


def kandidat(rec: dict, atr: Callable[[str], Optional[float]]) -> List[dict]:
    """Kandidat buka dari rekaman konsensus satu siklus: aset dengan arah aturan != 0 di target (veto sudah dibuang oleh `meja2.posisi`), urut skor
    instrumen konsensus. `uni` = universe aturan saat itu (instrumen tanpa veto) untuk menilai aturan keluar nanti."""
    am, n = rec.get("ambang") or {}, len(rec.get("aktif") or [])
    skor = rec.get("skor_instrumen") or {}
    veto = set(rec.get("veto") or [])
    uni = [a for a in (rec.get("instrumen") or []) if a not in veto]
    out = []
    for a, t in (rec.get("target") or {}).items():
        w = (t or {}).get("w", 0.0)
        if abs(w) < 1e-12:
            continue
        out.append({"aset": a, "arah": 1 if w > 0 else -1, "bot": rec.get("bot"), "skor": skor.get(a, 0.0), "atr": atr(a), "uni": uni,
                    "c": keyakinan(skor.get(a, 0.0), am.get("ambang_instrumen", 0.0), n)})
    return sorted(out, key=lambda k: (-k["skor"], k["aset"]))


def _isi(b: dict, a: str, qty_baru: float, p: float, e: float, alasan: str, bot: Optional[str]) -> dict:
    cur = b["posisi"].get(a, {"qty": 0.0, "masuk": p})
    pnl = cur["qty"] * (p - cur["masuk"])                                                        # untung/rugi pasar yang direalisasi isi ini
    b["saldo"] += pnl
    fee = meja.PARAMS["fee"] * abs(qty_baru - cur["qty"]) * p
    b["saldo"] -= fee
    b["biaya"] = round(b["biaya"] + fee, 6)
    b["n_trade"] += 1
    return {"aset": a, "dari": round(cur["qty"] * p / e, 6), "ke": round(qty_baru * p / e, 6), "harga": p, "fee": round(fee, 6), "alasan": alasan,
            "bot": bot, "pnl": round(pnl, 6)}


def aset_dipegang(b: Optional[dict]) -> List[str]:
    """Harga isi meja hidup WAJIB mencakup aset ini walau sudah keluar dari universe (replay 6 Okt: SOXSUSDT tanpa harga 136 siklus)."""
    return sorted((b or {}).get("posisi") or {})


def migrasi(b: dict, harga: Dict[str, float], bot: Optional[str]) -> List[dict]:
    """Sekali saat r4 mulai: posisi buku r3 (tanpa metadata slot) ditutup pada harga siklus, alasan "r4 start"; buku (saldo, biaya) berlanjut."""
    b.setdefault("jeda_sampai", 0)
    lama = [a for a, x in b["posisi"].items() if "arah" not in x and harga.get(a)]
    e = ekuitas(b, harga)
    out = [_isi(b, a, 0.0, harga[a], e, "r4 start", bot) for a in sorted(lama)]
    for a in lama:
        b["posisi"].pop(a)
    return out


def snapshot(b: dict, harga: Dict[str, float]) -> List[dict]:
    """Slot terbuka untuk rekaman (ikut di-hash) + web: bobot = notional bertanda / ekuitas, pnl = untung/rugi belum direalisasi."""
    e = ekuitas(b, harga) or 1.0
    out = []
    for a, x in sorted(b["posisi"].items(), key=lambda kv: (kv[1].get("t", 0), kv[0])):
        p = harga.get(a, x["masuk"])
        out.append({"aset": a, "bot": x.get("bot"), "arah": x.get("arah"), "qty": round(x["qty"], 8), "masuk": x["masuk"], "harga": p,
                    "w": round(x["qty"] * p / e, 6), "pnl": round(x["qty"] * (p - x["masuk"]), 4), "margin": x.get("margin"), "leverage": x.get("leverage"),
                    "sl": None if x.get("sl") is None else round(x["sl"], 8), "tp": None if x.get("tp") is None else round(x["tp"], 8),
                    "atr": x.get("atr"), "t": x.get("t")})
    return out


def langkah(b: dict, t0: int, harga: Dict[str, float], kand: List[dict], keluar_bot: Callable[[dict], bool], rem: bool,
            P: dict = PARAMS_SLOT) -> List[dict]:
    """Satu siklus buku slot -> isi (format `meja.isi` + alasan + bot). `keluar_bot(pos)` = aturan terkunci bot pembuka bilang datar/berbalik."""
    fills: List[dict] = []
    e = ekuitas(b, harga)
    for a in sorted(b["posisi"]):
        pos, p = b["posisi"][a], harga.get(a)
        if not p:
            continue                                                                             # tanpa harga siklus: tidak bisa dinilai
        naik = pos["arah"] > 0
        if rem:
            why = "daily loss brake"
        elif pos["sl"] is not None and (p <= pos["sl"] if naik else p >= pos["sl"]):              # SK-M31: ditutup pada harga siklus, bukan level SL
            why = "SL"
        elif pos["tp"] is not None and (p >= pos["tp"] if naik else p <= pos["tp"]):
            why = "TP"
        elif keluar_bot(pos):
            why = f"exit rule {pos['bot']}"
        else:
            continue
        fills.append(_isi(b, a, 0.0, p, e, why, pos["bot"]))
        b["posisi"].pop(a)
    if fills:
        b["jeda_sampai"] = t0 + P["jeda_siklus"] * P["siklus_s"]                                 # jeda baru berjalan sesudah posisi ditutup
    if rem or t0 < b["jeda_sampai"]:
        return fills
    e = ekuitas(b, harga)
    gross = sum(abs(x["qty"]) * harga.get(a, x["masuk"]) for a, x in b["posisi"].items())
    for k in kand:
        if len(b["posisi"]) >= P["maks_posisi"]:
            break
        a, p = k["aset"], harga.get(k["aset"])
        if a in b["posisi"] or not p or not k.get("atr"):
            continue
        u = ukuran(k["c"], k["bot"], k["atr"], P)
        nominal = u["notional"] * e
        if gross + nominal > P["maks_gross"] * e + 1e-9:
            continue
        qty = k["arah"] * nominal / p
        fills.append(_isi(b, a, qty, p, e, "open", k["bot"]))
        jarak = P["sl_atr"] * k["atr"]
        b["posisi"][a] = {"aset": a, "qty": qty, "masuk": p, "arah": k["arah"], "bot": k["bot"], "t": t0, "uni": list(k["uni"]), "atr": round(k["atr"], 6),
                          "margin": u["margin"], "leverage": u["leverage"],
                          "sl": p * (1 - k["arah"] * jarak) if u["stop"] else None,
                          "tp": p * (1 + k["arah"] * P["tp_atr"] * k["atr"]) if u["stop"] else None}
        gross += nominal
    return fills

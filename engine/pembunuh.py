"""Pembunuh TERSTRUKTUR untuk bot Fabius (P107): kalimat `BotSpec.pembunuh` diterjemahkan menjadi syarat yang dihitung mesin dari ledger maju.

Kenapa kunci terpisah: kalimat pembunuh ikut `spec_sha` (mengubahnya = bot baru = ledger baru), jadi terjemahannya tidak boleh menyunting spesifikasi.
Terjemahan dikunci di `engine/locks/pembunuh.lock.json`, mengikat `spec_sha` dan kalimat aslinya, lalu di-pin ke LockRegistry seperti kunci F-D16.
Sampai dikunci, statusnya USULAN dan buku slot tetap mencatat pembunuh bot Fabius sebagai "TEKS" (dinilai manusia).

Terjemahan USULAN (ditulis 3 Okt 2026, SEBELUM ada satu pun settle maju final; tiap tafsir yang bisa diperdebatkan ditandai dan dipilih builder):
  B1-TREND  "12 bulan maju tanpa mengalahkan buy&hold pada MDD dan Sharpe; atau kalah dari placebo masuk-acak dengan distribusi lama tahan sama"
    B1-K1  jendela 365 hari maju (cakupan settle final >= 90 %): TERPICU bila TIDAK (Sharpe bot > Sharpe patokan DAN MDD bot > MDD patokan).
           Patokan = buy&hold SAMA RATA atas universe yang sama (16 perp), return close-to-close, tanpa ongkos (lebih keras bagi bot).
    B1-K2  jendela yang sama: placebo = target tick maju digeser melingkar k hari (k acak 60..n-60; eksposur dan lama tahan sama persis, seperti G8),
           1000 tarikan, benih dari ujung rantai ledger. TERPICU bila net bot <= median net placebo.
  B3-CARRY  "hasil hedged negatif tiga bulan berjalan saat aktif, atau satu kejadian ADL pada kaki perp"
    B3-K1  bulan kalender UTC yang SUDAH LEWAT dan AKTIF (>= 10 hari memegang posisi); TERPICU bila tiga bulan aktif terakhir masing-masing net < 0.
           Bulan dorman dilewati ("saat aktif"), bukan dihitung nol.
    B3-K2  kejadian ADL pada kaki perp: TERPICU pada kejadian pertama. Di paper TIDAK BERLAKU (tidak ada posisi nyata, ADL tidak bisa terjadi);
           berlaku sejak eksekusi nyata ada (OperatorGuard).
Status per syarat: TERPICU · TIDAK TERPICU · BELUM CUKUP DATA · TIDAK BERLAKU. Vonis bot: YA (ada yang terpicu) · BELUM · TIDAK.
Fungsi murni: tidak membaca berkas selain kunci, tanpa jaringan; pemanggil memverifikasi ledger lebih dulu.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import random
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .data import MarketData
from .locks import LOCK_DIR
from .replay import prepare, replay
from .series import DAY_MS, max_drawdown, sharpe
from .spec import SPECS, sha0x
from .target import Target

LOCK_FILE = os.path.join(LOCK_DIR, "pembunuh.lock.json")
LOCK_V = 1
TERPICU, TIDAK, BELUM, TAK_BERLAKU = "TERPICU", "TIDAK TERPICU", "BELUM CUKUP DATA", "TIDAK BERLAKU"

USULAN: Dict[str, List[Dict[str, Any]]] = {
    "B1-TREND": [
        {"id": "B1-K1", "jenis": "patokan_bh", "jendela_hari": 365, "cakupan_min": 0.9, "patokan": "bh_sama_rata_universe",
         "aturan": "terpicu bila TIDAK (Sharpe bot > Sharpe patokan DAN MDD bot > MDD patokan)"},
        {"id": "B1-K2", "jenis": "placebo_geser", "jendela_hari": 365, "cakupan_min": 0.9, "n": 1000, "geser_min": 60,
         "aturan": "terpicu bila net bot <= median net placebo geser-melingkar"},
    ],
    "B3-CARRY": [
        {"id": "B3-K1", "jenis": "bulan_aktif_negatif_beruntun", "bulan": 3, "hari_aktif_min": 10,
         "aturan": "terpicu bila tiga bulan kalender aktif terakhir (sudah lewat, >= 10 hari memegang posisi) masing-masing net < 0"},
        {"id": "B3-K2", "jenis": "kejadian_eksekusi", "kejadian": "ADL pada kaki perp", "batas": 1,
         "aturan": "terpicu pada kejadian pertama; paper = tidak berlaku"},
    ],
}


# ---------------------------------------------------------------- kunci
def current_params() -> Dict[str, Any]:
    return {"v": LOCK_V, "bot": {b: {"spec_sha": SPECS[b].sha(), "teks": SPECS[b].pembunuh, "syarat": s} for b, s in sorted(USULAN.items())}}


def status(path: Optional[str] = None) -> Dict[str, Any]:
    """{'state': BELUM_DIKUNCI | TERKUNCI | MENYIMPANG | RUSAK, ...}. MENYIMPANG = terjemahan atau spesifikasi di kode berubah sesudah kunci."""
    path = path or LOCK_FILE
    now_sha = sha0x(current_params())
    if not os.path.exists(path):
        return {"state": "BELUM_DIKUNCI", "sha_kini": now_sha, "sha_kunci": None, "dikunci": None}
    try:
        with open(path, encoding="utf-8") as f:
            lock = json.load(f)
        stored = lock["sha"]
        if sha0x(lock["params"]) != stored:
            return {"state": "RUSAK", "sha_kini": now_sha, "sha_kunci": stored, "dikunci": lock.get("dikunci")}
    except (OSError, ValueError, KeyError, TypeError):
        return {"state": "RUSAK", "sha_kini": now_sha, "sha_kunci": None, "dikunci": None}
    return {"state": "TERKUNCI" if stored == now_sha else "MENYIMPANG", "sha_kini": now_sha, "sha_kunci": stored, "dikunci": lock.get("dikunci")}


def write_lock(note: str, now_iso: Optional[str] = None, path: Optional[str] = None) -> Dict[str, Any]:
    """Tulis kunci dari terjemahan kode SEKARANG. Menolak menimpa: terjemahan baru = keputusan baru + kunci v2."""
    path = path or LOCK_FILE
    if not note or not note.strip():
        raise ValueError("catatan wajib (siapa yang menyetujui dan kapan)")
    if os.path.exists(path):
        raise FileExistsError("kunci pembunuh sudah ada: terjemahan baru = keputusan baru + kunci v2, bukan timpa")
    params = current_params()
    lock = {"v": LOCK_V, "sha": sha0x(params), "params": params,
            "dikunci": now_iso or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "catatan": note.strip()}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(lock, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    return lock


# ---------------------------------------------------------------- bahan dari ledger
def _settles(records: Sequence[dict]) -> List[dict]:
    return sorted((r for r in records if r.get("type") == "settle"), key=lambda r: r["bar"])


def _window(records: Sequence[dict], days: int, end_ms: int) -> List[dict]:
    return [r for r in _settles(records) if end_ms - days * DAY_MS < r["bar"] <= end_ms]


def _seed(records: Sequence[dict]) -> int:
    return int(str(records[-1].get("h", "0x0"))[2:18] or "0", 16)


def _bh_returns(spec, md: MarketData, bars: Sequence[int]) -> Dict[int, float]:
    """Return buy&hold SAMA RATA universe per bar (close bar / close bar sebelumnya - 1), hanya aset yang punya kedua bar."""
    out = {}
    for t in bars:
        rs = []
        for a in spec.universe:
            s = md.perp.get(a)
            if s is None:
                continue
            i = s.index_at_or_before(t)
            if i >= 1 and s.t[i] == t and s.t[i - 1] == t - DAY_MS and s.c[i - 1]:
                rs.append(s.c[i] / s.c[i - 1] - 1.0)
        if rs:
            out[t] = sum(rs) / len(rs)
    return out


# ---------------------------------------------------------------- syarat
def eval_patokan_bh(spec, records, md: MarketData, k: dict, end_ms: int) -> Tuple[str, str]:
    win = _window(records, k["jendela_hari"], end_ms)
    if len(win) < k["cakupan_min"] * k["jendela_hari"]:
        return BELUM, f"{len(win)}/{k['jendela_hari']} hari settle final (butuh >= {k['cakupan_min']:.0%})"
    bh = _bh_returns(spec, md, [r["bar"] for r in win])
    pairs = [(r["net"], bh[r["bar"]]) for r in win if r["bar"] in bh]
    bot, ben = [x for x, _ in pairs], [y for _, y in pairs]
    sb, sk, mb, mk = sharpe(bot), sharpe(ben), max_drawdown(bot), max_drawdown(ben)
    if math.isnan(sb) or math.isnan(sk):
        return BELUM, "Sharpe tak terdefinisi"
    menang = sb > sk and mb > mk
    return (TIDAK if menang else TERPICU), f"Sharpe {sb:+.2f} vs {sk:+.2f}; MDD {mb * 100:.1f}% vs {mk * 100:.1f}% ({len(pairs)} hari)"


def eval_placebo_geser(spec, records, md: MarketData, k: dict, end_ms: int, n: Optional[int] = None) -> Tuple[str, str]:
    win = _window(records, k["jendela_hari"], end_ms)
    if len(win) < k["cakupan_min"] * k["jendela_hari"]:
        return BELUM, f"{len(win)}/{k['jendela_hari']} hari settle final (butuh >= {k['cakupan_min']:.0%})"
    lo = end_ms - k["jendela_hari"] * DAY_MS - DAY_MS
    ticks = sorted((r for r in records if r.get("type") == "tick" and lo <= r["asof"] < end_ms), key=lambda r: r["asof"])
    tg = [Target(spec.bot_id, r["asof"], dict(r["targets"])) for r in ticks] + [Target(spec.bot_id, end_ms, {})]
    m = len(tg)
    if m - 1 < 2 * k["geser_min"] + 1:
        return BELUM, f"{m - 1} tick di jendela (butuh > {2 * k['geser_min']})"
    tables = prepare(md)
    actual = sum(v for _, v in replay(spec, md, tg, tables))
    rng = random.Random(_seed(records))
    nets = []
    body = tg[:-1]
    for _ in range(n or k["n"]):
        s = rng.randrange(k["geser_min"], len(body) - k["geser_min"])
        tg2 = [Target(spec.bot_id, body[j].t, body[(j + s) % len(body)].weights) for j in range(len(body))] + [tg[-1]]
        nets.append(sum(v for _, v in replay(spec, md, tg2, tables)))
    nets.sort()
    med = nets[len(nets) // 2]
    return (TERPICU if actual <= med else TIDAK), f"net {actual * 1e4:+.1f} bps vs median placebo {med * 1e4:+.1f} bps ({len(nets)} tarikan)"


def eval_bulan_aktif(records, k: dict, end_ms: int) -> Tuple[str, str]:
    cur = dt.datetime.fromtimestamp(end_ms / 1000, dt.timezone.utc).strftime("%Y-%m")
    by: Dict[str, List[float]] = {}
    for r in _settles(records):
        mon = dt.datetime.fromtimestamp(r["bar"] / 1000, dt.timezone.utc).strftime("%Y-%m")
        if mon < cur and r.get("n_held", 0) > 0:
            by.setdefault(mon, []).append(r["net"])
    active = [(m, sum(v)) for m, v in sorted(by.items()) if len(v) >= k["hari_aktif_min"]]
    if len(active) < k["bulan"]:
        return BELUM, f"{len(active)} bulan aktif selesai (butuh {k['bulan']})"
    last = active[-k["bulan"]:]
    txt = ", ".join(f"{m} {v * 1e4:+.1f} bps" for m, v in last)
    return (TERPICU if all(v < 0 for _, v in last) else TIDAK), txt


def eval_kejadian(k: dict, events: Optional[Sequence[dict]]) -> Tuple[str, str]:
    if events is None:
        return TAK_BERLAKU, f"paper: tidak ada posisi nyata, {k['kejadian']} tidak bisa terjadi"
    n = sum(1 for e in events if e.get("kejadian") == k["kejadian"])
    return (TERPICU if n >= k["batas"] else TIDAK), f"{n} kejadian"


def evaluate(bot: str, records: Sequence[dict], md: Optional[MarketData], end_ms: int, syarat: Optional[Sequence[dict]] = None,
             events: Optional[Sequence[dict]] = None, placebo_n: Optional[int] = None) -> Dict[str, Any]:
    spec = SPECS[bot]
    rows = []
    for k in (syarat if syarat is not None else USULAN[bot]):
        j = k["jenis"]
        if j == "patokan_bh":
            st, det = eval_patokan_bh(spec, records, md, k, end_ms)
        elif j == "placebo_geser":
            st, det = eval_placebo_geser(spec, records, md, k, end_ms, placebo_n)
        elif j == "bulan_aktif_negatif_beruntun":
            st, det = eval_bulan_aktif(records, k, end_ms)
        elif j == "kejadian_eksekusi":
            st, det = eval_kejadian(k, events)
        else:
            raise ValueError(f"jenis syarat pembunuh tak dikenal: {j}")
        rows.append({"id": k["id"], "status": st, "detail": det})
    sts = [r["status"] for r in rows]
    vonis = "YA" if TERPICU in sts else ("BELUM" if BELUM in sts else "TIDAK")
    return {"bot": bot, "vonis": vonis, "syarat": rows}


def fmt(res: Dict[str, Any]) -> str:
    lines = [f"{res['bot']}: pembunuh {res['vonis']}"]
    for r in res["syarat"]:
        lines.append(f"  {r['id']} {r['status']:16s} {r['detail']}")
    return "\n".join(lines)

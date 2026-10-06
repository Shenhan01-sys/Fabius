"""P163: replay deterministik buku Fabius (meja v2) dari arsip siklus - diagnosis fee per sumber + uji kebijakan perputaran (usulan rumus r4).

Masukan = rekaman konsensus (agent "v2": bot, target per siklus dari aturan bot) + harga isi v2 per siklus (`/desk/arsip/<tgl>`). Replay memakai
`meja.isi` yang sama (fee 0,05 %/sisi, ubah minimum 2 % ekuitas); kebijakan hanya MENGUBAH target sebelum diisi, aturan bot tidak disentuh.
Replay kebijakan "r3" harus mengulang ekuitas tercatat (bukti replay setia) sebelum kebijakan lain boleh dibandingkan.

Pakai:  python -X utf8 tools/meja_replay.py --dari 2026-10-05 --sampai 2026-10-06
Batas:  sampel kecil (±1 hari); kebijakan dipilih menurut prinsip biaya, bukan dicocokkan ke sampel ini (anti-snooping, Epik 11).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meja  # noqa: E402

GERBANG = "https://fabius-x402-production.up.railway.app"
REM = "daily loss brake"


def muat(dari: str, sampai: str, gerbang: str = GERBANG) -> Tuple[List[dict], Dict[int, Dict[str, float]]]:
    recs, harga = [], {}
    d0, d1 = dt.date.fromisoformat(dari), dt.date.fromisoformat(sampai)
    while d0 <= d1:
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{gerbang}/desk/arsip/{d0}", headers={"User-Agent": "fabius-replay"}), timeout=120) as r:
                a = json.loads(r.read().decode())
            recs += a["fabius"]
            harga.update({int(s["siklus"]): s.get("harga_v2") or {} for s in a["siklus"]})
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        d0 += dt.timedelta(days=1)
    return sorted(recs, key=lambda r: r["siklus"]), harga


# ---------------------------------------------------------------- kebijakan: target aturan -> target yang diisi

Policy = Callable[[dict, dict, dict, Dict[str, float]], Dict[str, dict]]


def _w_now(book: dict, harga: Dict[str, float]) -> Dict[str, float]:
    e = meja.ekuitas(book, harga)
    return {a: p["qty"] * harga.get(a, p["masuk"]) / e for a, p in book["posisi"].items()} if e else {}


def r3(rec: dict, prev: Optional[dict], st: dict, w_now: Dict[str, float]) -> Dict[str, dict]:
    return {a: dict(t) for a, t in (rec.get("target") or {}).items()}


def pita_ukuran(band: float = 0.5) -> Policy:
    """Posisi yang sudah dipegang searah TIDAK diubah ukurannya kecuali selisih >= band x ukuran sekarang. Buka, tutup, balik arah tetap jalan."""
    def f(rec, prev, st, w_now):
        tg = r3(rec, prev, st, w_now)
        for a, t in tg.items():
            cur = w_now.get(a, 0.0)
            if cur and t["w"] and (cur > 0) == (t["w"] > 0) and abs(t["w"] - cur) < band * abs(cur):
                t["w"] = cur
        return tg
    return f


def lekat_instrumen(n: int = 3) -> Policy:
    """Instrumen yang dipegang dan tiba-tiba tidak dipilih tetap dipegang sampai n siklus berturut tidak dipilih (bot sama); rem rugi menutup semua."""
    def f(rec, prev, st, w_now):
        tg = r3(rec, prev, st, w_now)
        if REM in (rec.get("dasar") or ""):
            st.clear()
            return {}
        if prev is not None and rec.get("bot") != prev.get("bot"):
            st.clear()
            return tg
        for a, w in w_now.items():
            if a in tg or abs(w) < 1e-9:
                st.pop(a, None)
                continue
            st[a] = st.get(a, 0) + 1
            if st[a] < n:
                tg[a] = {"w": w, "k": 1.0}
        return tg
    return f


def jeda(siklus_min: int = 6) -> Policy:
    """Posisi hanya diubah tiap >= siklus_min siklus, kecuali bot berganti atau rem rugi (dua-duanya langsung)."""
    def f(rec, prev, st, w_now):
        tg = r3(rec, prev, st, w_now)
        ganti = prev is None or rec.get("bot") != prev.get("bot") or REM in (rec.get("dasar") or "")
        if ganti or rec["siklus"] - st.get("terakhir", -10 ** 12) >= siklus_min * 300:
            st["terakhir"] = rec["siklus"]
            return tg
        return {a: {"w": w, "k": 1.0} for a, w in w_now.items()}
    return f


def gabung(*ps: Policy) -> Policy:
    def f(rec, prev, st, w_now):
        tg = None
        for i, p in enumerate(ps):
            sub = st.setdefault(i, {})
            tg = p({**rec, "target": tg} if tg is not None else rec, prev, sub, w_now)
        return tg
    return f


KEBIJAKAN: Dict[str, Policy] = {
    "r3 (sekarang)": r3,
    "pita ukuran 50%": pita_ukuran(0.5),
    "lekat instrumen 3 siklus": lekat_instrumen(3),
    "jeda 6 siklus (30 menit)": jeda(6),
    "pita 50% + lekat 3": gabung(lekat_instrumen(3), pita_ukuran(0.5)),
}


# ---------------------------------------------------------------- replay + diagnosis

def replay(recs: List[dict], harga: Dict[int, Dict[str, float]], pol: Policy = r3, rugi_maks: float = 0.03) -> dict:
    """Rem rugi harian (SK-M10) dihitung ulang dari ekuitas replay, sama dengan `meja2.siklus2`: ekuitas sebelum isi vs ekuitas awal hari UTC.
    Siklus yang tercatat datar karena rem tetap datar (target aturan saat itu tidak terekam) - batas replay yang dinyatakan."""
    book, st, prev, hari = meja.buku_baru(), {}, None, {}
    eq, fee, isi, puncak, dd, kirim, rem = [], 0.0, 0, meja.PARAMS["modal_awal"], 0.0, [], 0
    for r in recs:
        h = harga.get(int(r["siklus"]))
        if not h:
            continue
        e0 = meja.ekuitas(book, h)
        d = int(r["siklus"]) // 86_400
        hari.setdefault(d, e0)
        if e0 / hari[d] - 1 <= -rugi_maks and REM not in (r.get("dasar") or ""):
            r = {**r, "target": {}, "dasar": f"{r.get('dasar') or ''}; {REM} (replay)"}
            rem += 1
        tg = pol(r, prev, st, _w_now(book, h))
        f = meja.isi(book, tg, h)
        kirim.append((r, f))
        fee += sum(x["fee"] for x in f)
        isi += len(f)
        e = meja.ekuitas(book, h)
        eq.append((r["siklus"], e))
        puncak = max(puncak, e)
        dd = min(dd, e / puncak - 1)
        prev = r
    return {"ekuitas": round(eq[-1][1], 2) if eq else None, "fee": round(fee, 2), "isi": isi, "dd_pct": round(dd * 100, 3),
            "rem_replay": rem, "seri": eq, "kirim": kirim}


def sumber_fee(recs: List[dict]) -> Dict[str, dict]:
    """Pecah fee TERCATAT per sebab, per isi: ganti bot > rem rugi > instrumen masuk/keluar > balik arah > ubah ukuran."""
    out: Dict[str, dict] = {}
    prev = None
    for r in recs:
        for x in r.get("isi") or []:
            a, d0, d1 = x["aset"], x["dari"], x["ke"]
            if prev is not None and r.get("bot") != prev.get("bot"):
                k = "ganti bot"
            elif REM in (r.get("dasar") or "") and abs(d1) < 1e-9:
                k = "rem rugi harian"
            elif abs(d0) < 1e-9 or abs(d1) < 1e-9:
                k = "instrumen masuk/keluar"
            elif (d0 > 0) != (d1 > 0):
                k = "balik arah"
            else:
                k = "ubah ukuran"
            o = out.setdefault(k, {"isi": 0, "fee": 0.0})
            o["isi"] += 1
            o["fee"] = round(o["fee"] + x["fee"], 4)
        prev = r
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["fee"]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dari", required=True)
    ap.add_argument("--sampai", required=True)
    ap.add_argument("--gerbang", default=GERBANG)
    a = ap.parse_args()
    recs, harga = muat(a.dari, a.sampai, a.gerbang)
    if not recs:
        print("tidak ada rekaman")
        return 1
    tercatat = recs[-1]["ekuitas"]
    print(f"rekaman Fabius: {len(recs)} siklus ({recs[0]['siklus']} .. {recs[-1]['siklus']}), harga {len(harga)} siklus, ekuitas tercatat {tercatat:.2f}")
    tot = sum(x["fee"] for r in recs for x in r.get("isi") or [])
    print(f"\nFEE TERCATAT per sumber (total {tot:.2f} USDT):")
    for k, v in sumber_fee(recs).items():
        print(f"  {k:24s} {v['isi']:4d} isi  {v['fee']:8.2f} USDT  ({v['fee'] / tot * 100:5.1f} %)")
    print("\nREPLAY (aturan bot sama, target diubah kebijakan):")
    base = None
    for nama, pol in KEBIJAKAN.items():
        x = replay(recs, harga, pol)
        base = base or x
        print(f"  {nama:28s} ekuitas {x['ekuitas']:9.2f}  fee {x['fee']:7.2f}  isi {x['isi']:4d}  dd {x['dd_pct']:6.2f} %  rem+{x['rem_replay']}"
              + (f"   (replay r3 vs tercatat: {x['ekuitas'] - tercatat:+.2f})" if pol is r3 else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""P163: replay deterministik buku Fabius (meja v2) dari arsip siklus - diagnosis fee per sumber + uji kebijakan perputaran (usulan rumus r4).

Masukan = `GET /desk/archive/<YYYY-MM-DD>` per hari: rekaman konsensus Fabius (agent "v2": bot, instrumen, eksposur, target aturan per siklus, isi,
ekuitas) + harga isi v2 per siklus. Replay memakai `meja.isi` yang sama (fee 0,05 %/sisi, ubah minimum 2 % ekuitas); kebijakan hanya MENGUBAH
target sebelum diisi, arah dari aturan bot tidak disentuh. Replay r3 wajib mengulang ekuitas tercatat (SETIA) sebelum kebijakan lain boleh
dibandingkan; replay harus mulai dari hari pertama buku (buku 10.000 datar).

Pakai:  python -X utf8 tools/meja_replay.py --dari 2026-10-05 --sampai 2026-10-06
Batas:  sampel kecil (±1 hari); kebijakan dipilih menurut prinsip biaya, bukan dicocokkan ke sampel ini (anti-snooping, Epik 11). Siklus yang
        tercatat datar karena rem rugi tidak menyimpan target aturan, jadi tetap datar di semua kebijakan.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meja  # noqa: E402

GERBANG = "https://fabius-x402-production.up.railway.app"
REM = "daily loss brake"
B2 = "B2-RS"
SUMBER = ("ganti bot", "ganti instrumen", "ubah eksposur", "pembalikan peringkat B2", "rem rugi",        # lima sumber kriteria keluar P163 (1)
          "aturan buka/tutup/balik (bot lain)", "geser bobot (harga/aturan)", "buka awal")              # sisa, supaya total fee utuh
SETIA_USDT = 0.01


def muat(dari: str, sampai: str, gerbang: str = GERBANG) -> Tuple[List[dict], Dict[int, Dict[str, float]]]:
    recs, harga = [], {}
    d0, d1 = dt.date.fromisoformat(dari), dt.date.fromisoformat(sampai)
    while d0 <= d1:
        try:
            req = urllib.request.Request(f"{gerbang}/desk/archive/{d0}", headers={"User-Agent": "fabius-replay"})
            with urllib.request.urlopen(req, timeout=120) as r:
                a = json.loads(r.read().decode())
            recs += a["records"]
            harga.update({int(c["cycle"]): c.get("prices") or {} for c in a["cycles"]})
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        d0 += dt.timedelta(days=1)
    return sorted(recs, key=lambda r: r["siklus"]), harga


def _rem(r: Optional[dict]) -> bool:
    return bool(r) and REM in (r.get("dasar") or "")


# ---------------------------------------------------------------- kebijakan: target aturan -> target yang diisi

Policy = Callable[[dict, Optional[dict], dict, Dict[str, float]], Dict[str, dict]]


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
    """Instrumen yang dipegang lalu keluar dari daftar instrumen konsensus tetap dipegang (bobot sekarang) sampai n siklus berturut tidak dipilih,
    selama bot sama. Instrumen yang masih dipilih tetapi didatarkan aturan TETAP ditutup (arah milik aturan); ganti bot + rem rugi langsung."""
    def f(rec, prev, st, w_now):
        tg = r3(rec, prev, st, w_now)
        if _rem(rec) or prev is None or rec.get("bot") != prev.get("bot"):
            st.clear()
            return tg
        now_i, prev_i = set(rec.get("instrumen") or []), set(prev.get("instrumen") or [])
        for a, w in w_now.items():
            if a in tg or a in now_i or a not in prev_i | set(st) or abs(w) < 1e-9:
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
        if prev is None or rec.get("bot") != prev.get("bot") or _rem(rec) or rec["siklus"] - st.get("terakhir", -10 ** 12) >= siklus_min * 300:
            st["terakhir"] = rec["siklus"]
            return tg
        return {a: {"w": w, "k": 1.0} for a, w in w_now.items()}
    return f


def gabung(*ps: Policy) -> Policy:
    def f(rec, prev, st, w_now):
        tg = None
        for i, p in enumerate(ps):
            tg = p({**rec, "target": tg} if tg is not None else rec, prev, st.setdefault(i, {}), w_now)
        return tg
    return f


KEBIJAKAN: Dict[str, Policy] = {
    "r3 (sekarang)": r3,
    "pita ukuran 50%": pita_ukuran(0.5),
    "lekat instrumen 3 siklus": lekat_instrumen(3),
    "jeda 6 siklus (30 menit)": jeda(6),
    "lekat 3 + pita 50%": gabung(lekat_instrumen(3), pita_ukuran(0.5)),
}
KEPEKAAN: Dict[str, Policy] = {                                                                     # tetangga parameter (--kepekaan): hasil tidak boleh bergantung satu titik
    "jeda 3 siklus (15 menit)": jeda(3),
    "jeda 12 siklus (60 menit)": jeda(12),
    "lekat instrumen 6 siklus": lekat_instrumen(6),
    "pita ukuran 25%": pita_ukuran(0.25),
    "jeda 6 + lekat 3": gabung(lekat_instrumen(3), jeda(6)),
}


# ---------------------------------------------------------------- replay + diagnosis

def replay(recs: List[dict], harga: Dict[int, Dict[str, float]], pol: Policy = r3, rugi_maks: float = 0.03) -> dict:
    """Rem rugi harian (SK-M10) dihitung ulang dari ekuitas replay, sama dengan `meja2.siklus2`: ekuitas sebelum isi vs ekuitas awal hari UTC."""
    book, st, prev, hari = meja.buku_baru(), {}, None, {}
    eq, fee, isi, puncak, dd, kirim, rem = [], 0.0, 0, meja.PARAMS["modal_awal"], 0.0, [], 0
    for r in recs:
        h = harga.get(int(r["siklus"]))
        if not h:
            continue
        e0 = meja.ekuitas(book, h)
        d = int(r["siklus"]) // 86_400
        hari.setdefault(d, e0)
        if e0 / hari[d] - 1 <= -rugi_maks and not _rem(r):
            r = {**r, "target": {}, "dasar": f"{r.get('dasar') or ''}; {REM} (replay)"}
            rem += 1
        f = meja.isi(book, pol(r, prev, st, _w_now(book, h)), h)
        kirim.append((r, f))
        fee += sum(x["fee"] for x in f)
        isi += len(f)
        e = meja.ekuitas(book, h)
        eq.append((r["siklus"], e))
        puncak = max(puncak, e)
        dd = min(dd, e / puncak - 1)
        prev = r
    akhir: Dict[str, float] = {}
    for t, e in eq:                                                                                  # ekuitas akhir tiap hari UTC
        akhir[dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d")] = e
    lalu, ph = meja.PARAMS["modal_awal"], {}
    for d in sorted(akhir):                                                                          # % per hari = akhir hari vs akhir hari lalu
        ph[d] = round((akhir[d] / lalu - 1) * 100, 3)
        lalu = akhir[d]
    return {"ekuitas": round(eq[-1][1], 2) if eq else None, "fee": round(fee, 2), "isi": isi, "dd_pct": round(dd * 100, 3),
            "rem_replay": rem, "per_hari_pct": ph, "seri": eq, "kirim": kirim}


def sebab(x: dict, r: dict, prev: Optional[dict]) -> str:
    """Satu isi -> satu sebab (urutan = prioritas): rem rugi (tutup, atau buka lagi sesudah rem) > ganti bot > ganti instrumen (aset masuk/keluar
    daftar instrumen konsensus) > pembalikan peringkat B2 (B2-RS, aset tetap dipilih tetapi aturan membuka/menutup/membalik) > aturan bot lain >
    ubah eksposur (searah, eksposur konsensus berubah) > geser bobot (searah, eksposur sama: harga bergerak atau bobot aturan berubah)."""
    d0, d1 = x["dari"], x["ke"]
    if prev is None:
        return "buka awal"
    if (_rem(r) and abs(d1) < 1e-9) or (_rem(prev) and not _rem(r)):
        return "rem rugi"
    if r.get("bot") != prev.get("bot"):
        return "ganti bot"
    if (x["aset"] in (r.get("instrumen") or [])) != (x["aset"] in (prev.get("instrumen") or [])):
        return "ganti instrumen"
    if abs(d0) < 1e-9 or abs(d1) < 1e-9 or (d0 > 0) != (d1 > 0):
        return "pembalikan peringkat B2" if r.get("bot") == B2 else "aturan buka/tutup/balik (bot lain)"
    if abs((r.get("eksposur") or 0) - (prev.get("eksposur") or 0)) > 1e-9:
        return "ubah eksposur"
    return "geser bobot (harga/aturan)"


def sumber_fee(recs: List[dict]) -> Dict[str, dict]:
    """Fee TERCATAT (isi di rekaman) dipecah per sebab; jumlah semua sebab = total fee tercatat."""
    out: Dict[str, dict] = {}
    prev = None
    for r in recs:
        for x in r.get("isi") or []:
            o = out.setdefault(sebab(x, r, prev), {"isi": 0, "fee": 0.0})
            o["isi"] += 1
            o["fee"] = round(o["fee"] + x["fee"], 6)
        prev = r
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["fee"]))


def laporan(recs: List[dict], harga: Dict[int, Dict[str, float]], kepekaan: bool = False) -> dict:
    """Seluruh keluaran P163 dalam satu dict (dipakai CLI + tes integrasi). `kepekaan` menambah tetangga parameter (KEPEKAAN)."""
    tercatat = recs[-1]["ekuitas"]
    pols = {**KEBIJAKAN, **(KEPEKAAN if kepekaan else {})}
    hasil = {nama: {k: v for k, v in replay(recs, harga, pol).items() if k not in ("seri", "kirim")} for nama, pol in pols.items()}
    base = hasil["r3 (sekarang)"]
    return {"siklus": len(recs), "harga_siklus": sum(1 for r in recs if harga.get(int(r["siklus"]))), "ekuitas_tercatat": tercatat,
            "fee_tercatat": round(sum(x["fee"] for r in recs for x in r.get("isi") or []), 6), "sumber": sumber_fee(recs),
            "setia": base["ekuitas"] is not None and abs(base["ekuitas"] - tercatat) <= SETIA_USDT, "replay": hasil}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dari", required=True)
    ap.add_argument("--sampai", required=True)
    ap.add_argument("--gerbang", default=GERBANG)
    ap.add_argument("--json", action="store_true", help="cetak laporan sebagai JSON")
    ap.add_argument("--kepekaan", action="store_true", help="tambah tetangga parameter kebijakan (uji kepekaan)")
    a = ap.parse_args()
    recs, harga = muat(a.dari, a.sampai, a.gerbang)
    if not recs:
        print("tidak ada rekaman")
        return 1
    lp = laporan(recs, harga, a.kepekaan)
    if a.json:
        print(json.dumps(lp, indent=1, ensure_ascii=False))
        return 0 if lp["setia"] else 2
    print(f"rekaman Fabius: {lp['siklus']} siklus ({recs[0]['siklus']} .. {recs[-1]['siklus']}), berharga {lp['harga_siklus']}, "
          f"ekuitas tercatat {lp['ekuitas_tercatat']:.2f}")
    tot = lp["fee_tercatat"] or 1e-12
    print(f"\nFEE TERCATAT per sumber (total {lp['fee_tercatat']:.2f} USDT):")
    for k, v in lp["sumber"].items():
        print(f"  {k:36s} {v['isi']:4d} isi  {v['fee']:8.2f} USDT  ({v['fee'] / tot * 100:5.1f} %)")
    print("\nREPLAY (arah aturan bot sama, target diubah kebijakan):")
    for nama, x in lp["replay"].items():
        hari = "  ".join(f"{d[5:]} {v:+6.2f} %" for d, v in x["per_hari_pct"].items())
        print(f"  {nama:26s} ekuitas {x['ekuitas']:9.2f}  fee {x['fee']:7.2f}  isi {x['isi']:4d}  dd {x['dd_pct']:6.2f} %  rem+{x['rem_replay']:<3d} {hari}")
    base = lp["replay"]["r3 (sekarang)"]["ekuitas"]
    print(f"\nreplay r3 vs tercatat: {base - lp['ekuitas_tercatat']:+.4f} USDT -> {'SETIA' if lp['setia'] else 'TIDAK SETIA (kebijakan lain tidak boleh dibandingkan)'}")
    return 0 if lp["setia"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

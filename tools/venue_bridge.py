"""P41 - berapa banyak kabar yang bisa kami EKSEKUSI? (irisan venue ⑦ ↔ perp)

E11 (`tools/horizon_decay.py`) menemukan kabar yang berumur ±2 menit pada token spot BSC yang dilihat
⑦. Pertanyaan yang menentukan apakah itu milik agen ini bukan "sekuat apa sinyalnya" tapi
**"di venue kami ada berapa dari token-token itu"**. Kalau irisannya tipis, sekurantik apa pun
kabar itu, agen ini tidak punya jalan untuk mengambilnya - dan itu batas yang harus ditulis di
depan, bukan di catatan kaki.

Alat ini membandingkan dua daftar yang kami punya di repo:
  kiri  = simbol dari baris beli ⑦ (`universe/wallet-flow.jsonl`, field `y`) - tempat kabar hidup
  kanan = basis aset yang terdaftar di venue perp kami (`data/aster_symbols.json`, tanpa sufiks
          USDT/USDC/PERP)

Pakai:  python -X utf8 tools/venue_bridge.py
       python -X utf8 tools/venue_bridge.py --self-test
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
SYMS = os.path.join(ROOT, "data", "aster_symbols.json")
OUT = os.path.join(ROOT, "decisions", "p41-venue-bridge.json")
SFIKS = ("USDT", "USDC", "PERP")


def potong(x):
    """Satu entri daftar venue -> basis aset (sufiks kuotasi dibuang, bukan ditebak)."""
    s = x if isinstance(x, str) else str((x or {}).get("symbol") or (x or {}).get("baseAsset")
                                         or (x or {}).get("base") or "")
    s = s.strip().upper()
    for suf in SFIKS:
        if s.endswith(suf) and len(s) > len(suf):
            return s[: -len(suf)]
    return s


def venue():
    d = json.load(io.open(SYMS, encoding="utf-8"))
    cand = d if isinstance(d, list) else (d.get("symbols") or d.get("data")
                                          or next((v for v in d.values() if isinstance(v, list)),
                                                  []))
    return {potong(x) for x in (cand or [])} - {""}


def kabar():
    cnt, tok = collections.Counter(), {}
    for ln in io.open(FLOW, encoding="utf-8", errors="replace"):
        if not ln.startswith("{"):
            continue
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("k") not in ("tx", "txc") or not r.get("b"):
            continue
        y = str(r.get("y") or "").strip().upper()
        if not y:
            continue
        cnt[y] += 1
        tok.setdefault(y, str(r.get("tk") or "").lower())
    return cnt, tok


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--tulis", action="store_true", help="pakai default: artefak selalu ditulis")
    a = ap.parse_args()
    if a.self_test:
        assert potong("PEPEUSDT") == "PEPE" and potong("1000CATUSDT") == "1000CAT"
        assert potong({"symbol": "CAKEUSDC"}) == "CAKE" and potong("BOME") == "BOME"
        assert potong("USDT") == "USDT", "sufiks saja jangan terpotong jadi string kosong"
        assert potong(None) == "" and potong("") == ""
        print("self-test venue_bridge OK: sufiks kuotasi dibuang, simbol polos utuh, entri kosong "
              "tidak masuk himpunan")
        return
    if not (os.path.exists(SYMS) and os.path.exists(FLOW)):
        raise SystemExit("bahan tidak ada (%s / %s) - tanpa kedua daftar, irisan tidak bisa "
                         "disimpulkan" % (os.path.basename(SYMS), os.path.basename(FLOW)))
    vb = venue()
    kb, tk = kabar()
    inter = {y for y in kb if y in vb}
    berat = sum(kb[y] for y in inter)
    total = sum(kb.values())
    persen = 100.0 * berat / max(1, total)
    print("venue perp kami: %d basis aset | kabar beli ⑦: %d simbol, %d kabar"
          % (len(vb), len(kb), total))
    print("IRISAN: %d simbol (%0.1f %% dari kabar beli bisa dieksekusi di venue kami)"
          % (len(inter), persen))
    print("contoh beririsan:", ", ".join(sorted(inter)[:14]))
    print("contoh TIDAK beririsan (kabar yang tak bisa kami ambil):",
          ", ".join("%s=%d" % kv for kv in [(y, kb[y]) for y in sorted(kb, key=lambda z: -kb[z])
                                             if y not in vb][:8]))
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "basis_venue": len(vb), "simbol_kabar": len(kb), "kabar_beli_total": total,
           "irisan_simbol": len(inter), "kabar_beli_irisan": berat,
           "persen_kabar_bisa_dieksekusi": round(persen, 2),
           "contoh_irisan": sorted(inter)[:40],
           "sumber": {"venue": os.path.relpath(SYMS, ROOT).replace("\\", "/"),
                      "kabar": os.path.relpath(FLOW, ROOT).replace("\\", "/")}}
    json.dump(out, io.open(OUT, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(OUT))
    print("\nBatas kalimat yang boleh dipakai: kalau persen kecil, kabar hidup di tempat yang tidak "
          "kami pegang - 'ada edge' bukan 'agen ini bisa mengambilnya'.")


if __name__ == "__main__":
    utama()

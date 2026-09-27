"""Bidang ⑦ jadi masukan: sinyal aliran dompet pintar, dihitung POINT-IN-TIME.

Kenapa alat ini ada: perekam `universe/record_wallet_flow.py` sudah mengumpulkan 33.191 baris sejak
26 Sep 08:01Z, tapi tidak satu pun alat keputusan membacanya - `direction.py`, `ledger.py`, dan
`backtest.py` tidak menyebut aliran wallet sama sekali. Jadi gagasan "cocokkan dengan whale" selama
ini bukan ditolak, tapi **belum pernah diuji**.

Dua aturan yang membuatnya berarti, bukan cuma kencang:

1. **Point-in-time.** Jendela dihitung terhadap `as_of` (default: umur snapshot universe terakhir),
   dan baris dengan waktu AFTER `as_of` dibuang. Sekalipun data kami sendiri yang merekamnya,
   mengintip masa depan tetap mungkin dilakukan oleh alat yang ceroboh.
2. **Yang boleh dipakai hanya apa yang kami lihat saat itu terjadi.** Field `g` (tag `kol`,
   `top_followed`, ...) adalah **label GMGN hari ini** tentang dompet masa lalu - itu bagian yang
   contaminated oleh pilihan panel retroaktif (lihat vault 06-Results/06 + Concepts/Lookahead Bound).
   Karena itu alat ini melaporkan dua angka terpisah: aliran semua maker, dan aliran maker
   ber-tag - dan yang kedua jangan pernah dipanggil "prediktif" tanpa uji prospektif.

Pakai:
    python -X utf8 tools/flow_signal.py --overlap          # berapa kandidat yang punya data aliran
    python -X utf8 tools/flow_signal.py --signal MARSCOIN  # satu simbol, jendela 24 jam
    python -X utf8 tools/flow_signal.py --json MARSCOIN TAC
"""
import argparse
import io
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isfile(os.path.join(ROOT, "foundry.toml")):
    sys.exit(f"ROOT bukan akar Fabius: {ROOT} - harus berisi foundry.toml")

FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
UNIV = os.path.join(ROOT, "universe", "bsc-universe.jsonl")


def as_of_utc():
    """Umur snapshot terakhir, dari datanya sendiri - bukan jam laptop (aturan proyek ini)."""
    if not os.path.isfile(UNIV):
        return time.time()
    last = None
    for line in io.open(UNIV, encoding="utf-8", errors="replace"):
        line = line.strip()
        if line:
            try:
                last = json.loads(line)
            except json.JSONDecodeError:
                continue
    s = (last or {}).get("snapshot_utc")
    if not s:
        return time.time()
    return time.mktime(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone


def load_rows(as_of_epoch, window_h):
    """Baris `tx` dengan 0 <= as_of - t <= window, plus ringkasan kesehatan rekaman."""
    cut_lo = as_of_epoch - window_h * 3600
    rows, future, px = [], 0, {}
    kinds = {}
    for line in io.open(FLOW, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        k = r.get("k")
        kinds[k] = kinds.get(k, 0) + 1
        if k == "px":
            px[str(r.get("tk"))] = (r.get("p"), r.get("t"))
            continue
        if k != "tx":
            continue
        t = r.get("t") or 0
        if t > as_of_epoch:
            future += 1
            continue
        if cut_lo <= t <= as_of_epoch:
            rows.append(r)
    return rows, future, kinds, px


def agg(rows, want_tagged=None):
    makers, net_usd, gross, buys, sells, opens, closes = set(), 0.0, 0.0, 0, 0, 0, 0
    for r in rows:
        if want_tagged is True and not r.get("g"):
            continue
        if want_tagged is False and r.get("g"):
            continue
        makers.add(r.get("m"))
        u = float(r.get("u") or 0.0)
        gross += u
        if r.get("b"):
            net_usd += u
            buys += 1
        else:
            net_usd -= u
            sells += 1
        if r.get("c"):
            opens += 1
        else:
            closes += 1
    return {"makers": len([m for m in makers if m]), "net_usd": round(net_usd, 2),
            "gross_usd": round(gross, 2), "buys": buys, "sells": sells,
            "opens": opens, "closes": closes}


def by_symbol(rows):
    out = {}
    for r in rows:
        sym = str(r.get("y") or "").upper()
        out.setdefault(sym, []).append(r)
    return out


def universe_symbols():
    """Simbol kandidat arah dari snapshot terakhir (base = nama tanpa USDT)."""
    if not os.path.isfile(UNIV):
        return []
    last = None
    for line in io.open(UNIV, encoding="utf-8", errors="replace"):
        if line.strip():
            last = line.strip()
    try:
        snap = json.loads(last or "{}")
    except json.JSONDecodeError:
        snap = {}
    syms = []
    for r in snap.get("rows") or []:
        s = str(r.get("symbol") or "").upper()
        if s:
            syms.append(s)
    return syms, snap.get("snapshot_utc")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=float, default=24.0, help="jam ke belakang dari as_of")
    ap.add_argument("--as-of", default=None, help="UTC ISO (default: umur snapshot universe)")
    ap.add_argument("--overlap", action="store_true")
    ap.add_argument("--json", nargs="*", default=None)
    ap.add_argument("symbols", nargs="*")
    a = ap.parse_args()

    if not os.path.isfile(FLOW):
        sys.exit(f"tidak ada {FLOW} - jalankan universe/record_wallet_flow.py dulu")

    if a.as_of:
        as_of = time.mktime(time.strptime(a.as_of, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
    else:
        as_of = as_of_utc()
    rows, future, kinds, px = load_rows(as_of, a.window)
    groups = by_symbol(rows)

    print(f"as_of {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(as_of))} | jendela {a.window:g} jam | "
          f"baris tx jendela ini {len(rows)} | baris DI MASA DEPAN as_of dibuang {future}")
    print(f"jenis baris di seluruh berkas: {kinds}")

    if a.overlap or not a.symbols and not a.json:
        syms, snap_utc = universe_symbols()
        have = {s for s in groups}
        bases = {s[:-4] if s.endswith("USDT") else s for s in have}
        matched, missed = [], []
        for s in syms:
            b = s[:-4] if s.endswith("USDT") else s
            (matched if (s in have or b in bases) else missed).append(s)
        print(f"\nOVERLAP: universe snapshot {snap_utc} punya {len(syms)} simbol | "
              f"{len(matched)} tampak di aliran ⑦ ({100.0*len(matched)/max(len(syms),1):.0f} %)")
        print(f"  tidak tampak: {', '.join(missed) if missed else '-'}")
        print("  ARTINYA: konfluensi whale tidak bisa jadi syarat untuk semua keputusan - "
              "kelebihan kasus harus dilaporkan sebagai TAK ADA DATA, bukan sebagai nol atau netral.")
        if a.overlap:
            return

    targets = a.symbols or []
    for s in targets:
        key = s if s.upper() in groups else (s + "USDT") if (s + "USDT").upper() in groups else None
        sub = groups.get((key or "").upper(), [])
        allr, tagg, untag = agg(sub), agg(sub, True), agg(sub, False)
        print(f"\n### {s} | baris {len(sub)}")
        print(f"  SEMUA maker   : net {allr['net_usd']:+12,.2f} USD | gross {allr['gross_usd']:,.2f} | "
              f"maker {allr['makers']} | beli/jual {allr['buys']}/{allr['sells']} | buka/tutup {allr['opens']}/{allr['closes']}")
        print(f"  BERTAG (⑦)     : net {tagg['net_usd']:+12,.2f} USD | maker {tagg['makers']} | "
              f"beli/jual {tagg['buys']}/{tagg['sells']}   <- label GMGN hari ini, terkontaminasi")
        print(f"  TANPA TAG      : net {untag['net_usd']:+12,.2f} USD | maker {untag['makers']}")
        if not sub:
            print("  -> TAK ADA DATA pada jendela ini (bukan 'netral', bukan '0')")

    if a.json:
        out = {s: {"all": agg(groups.get(s.upper(), [])), "tagged": agg(groups.get(s.upper(), []), True),
                  "rows": len(groups.get(s.upper(), []))} for s in a.json}
        print("\n" + json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()

"""Diagnostik cepat untuk `maker_ledger.py` sebelum satu pun angkanya dipercaya.

Kejadian 27 Sep: readout pertama mengklaim 69/69 maker NET positif dengan gross +18.000..+57.000 bps
per trade dan hit rate 90-100 %. Itu bukan penemuan, itu alat yang salah - dan satu-satunya cara
membedakannya dari penemuan nyata adalah mencetak bahan mentahnya.

Yang dicek:
  A.Duplikat hash   : feed punya jendela tumpang-tindih; kalau `transaction_hash` muncul >1x,
                     lot FIFO kita menggandakan pembukaan/penutupan
  B.Sumber         : apakah maker yang sama masuk lewat `smartmoney` DAN `kol` (dedupe lintas sumber)
  C.Sebagian arah  : distribusi (b,c) - kalau mayoritas baris bukan (buy,open)/(sell,close),
                     arti `is_open_or_close` yang kupakai salah
  D.Trade nyata    : 10 trade pertama maker teratas, dengan harga masuk/keluar & selisih jam

    python -X utf8 tools/maker_audit.py
"""
import collections
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
if not os.path.isfile(FLOW):
    sys.exit(f"tidak ada {FLOW}")

rows = []
for line in io.open(FLOW, encoding="utf-8", errors="replace"):
    line = line.strip()
    if not line:
        continue
    r = json.loads(line)
    if r.get("k") == "tx":
        rows.append(r)

print(f"baris tx: {len(rows):,}")
h = collections.Counter(r.get("h") for r in rows)
dupe = {k: v for k, v in h.items() if v > 1}
print(f"A. hash unik {len(h):,} | hash muncul >1x: {len(dupe):,} | kemunculan ekstra: "
      f"{sum(v - 1 for v in dupe.values()):,}")
if dupe:
    ex = sorted(dupe.items(), key=lambda kv: -kv[1])[:3]
    print(f"   contoh: {[(k[:12], v) for k, v in ex]}")

src = collections.Counter((r.get("h"), r.get("s")) for r in rows)
both = collections.Counter()
for hh, s in src:
    both[hh] += 0
per = collections.defaultdict(set)
for r in rows:
    per[r.get("h")].add(r.get("s"))
multi = sum(1 for v in per.values() if len(v) > 1)
print(f"B. hash yang datang dari >1 sumber: {multi:,}")

c4 = collections.Counter((int(bool(r.get("b"))), int(bool(r.get("c")))) for r in rows)
tot = sum(c4.values())
print("C. distribusi (beli?, buka?) -> jumlah:")
for k in sorted(c4):
    nama = {(1, 1): "buka-beli", (0, 0): "tutup-jual", (1, 0): "beli-bukan-buka",
            (0, 1): "jual-bukan-tutup"}[k]
    print(f"   {k} {nama:16} {c4[k]:7,}  ({100.0*c4[k]/tot:5.1f} %)")

# trade pertama maker teratas dari artefak skor
arts = sorted(f for f in os.listdir(os.path.join(ROOT, "decisions")) if f.startswith("maker-scores"))
if arts:
    d = json.load(io.open(os.path.join(ROOT, "decisions", arts[-1]), encoding="utf-8"))
    top = max((s for s in d["rows"] if s["layak_label"]), key=lambda s: s["trades"], default=None)
    if top:
        m = top["maker"]
        sub = sorted([r for r in rows if r.get("m") == m], key=lambda r: int(r.get("t") or 0))
        syms = collections.Counter(r.get("y") for r in sub)
        print(f"\nD. maker teratas {m} ({top['trades']} trade 'tertutup', gross {top['gross_mean_bps']:+.0f} bps)")
        print(f"   baris {len(sub)} | simbol: {syms.most_common(5)}")
        print(f"   {'t':12} {'simbol':10} {'b/c':5} {'px':>14} {'usd':>12}")
        for r in sub[:14]:
            print(f"   {r.get('t')} {str(r.get('y'))[:10]:10} "
                  f"{str(int(bool(r.get('b'))))}/{str(int(bool(r.get('c')))):1} "
                  f"{float(r.get('p') or 0):14.10f} {float(r.get('u') or 0):12,.2f}")
        px = [float(r.get("p") or 0) for r in sub if float(r.get("p") or 0) > 0]
        if len(px) > 2:
            print(f"   rentang harga maker ini: min {min(px):.10f} max {max(px):.10f} "
                  f"(rasio {max(px)/min(px):,.1f}x)")

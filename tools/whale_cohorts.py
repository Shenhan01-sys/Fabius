"""Apakah "whale" itu per-kolam? Diukur dari rekaman ⑦ kami sendiri, point-in-time.

Pertanyaan yang dijawab alat ini: kalau kita akan memperdagangkan X, apakah dompet yang benar
untuk ditanya adalah dompet yang main di X (atau di kolam yang sama)? Kalau iya, maka satu panel
global - misalnya label "smart money" dari penyedia data - salah alat sejak awal.

Tiga hal yang diukur, semuanya hanya memakai baris yang lebih tua dari `as_of`:
  1. LEBAR   : berapa maker per simbol (koefisien variasi) -> apakah "cohort per aset" punya data
  2. KONSENTRASI: HHI per maker atas gross USD di seluruh simbol yang ia sentuh
                (H=1 -> cuma satu kolam; H kecil -> dompet serba-macam, bukan "whale BTC")
  3. KOLOM   : graf ko-occurrence maker<->simbol, lalu tetangga MARSCOIN (simbol apa yang
               diperdagangkan oleh maker yang SAMA) -> bukti struktural bahwa "kolam" itu nyata

Pakai:
    python -X utf8 tools/whale_cohorts.py
    python -X utf8 tools/whale_cohorts.py --neighbors MARSCOIN
    python -X utf8 tools/whale_cohorts.py --json
"""
import argparse
import collections
import io
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
UNIV = os.path.join(ROOT, "universe", "bsc-universe.jsonl")
if not os.path.isfile(FLOW):
    sys.exit(f"tidak ada {FLOW}")


def snapshot_epoch():
    last = None
    if os.path.isfile(UNIV):
        for line in io.open(UNIV, encoding="utf-8", errors="replace"):
            if line.strip():
                last = line.strip()
    try:
        s = json.loads(last or "{}").get("snapshot_utc")
    except json.JSONDecodeError:
        return None
    if not s:
        return None
    return time.mktime(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone


def load(window_h=None):
    """Baris `tx` + angka-angka turunan. `window_h` membatasi ke belakang dari as_of."""
    as_of = snapshot_epoch()
    lo = (as_of - window_h * 3600) if (as_of and window_h) else None
    per_tok = collections.defaultdict(collections.Counter)
    per_mkr = collections.defaultdict(collections.Counter)
    net_tok = collections.defaultdict(float)
    gross_all = 0.0
    kept = total = future = 0
    for line in io.open(FLOW, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get("k") != "tx":
            continue
        total += 1
        t = r.get("t") or 0
        if as_of and t > as_of:
            future += 1
            continue
        if lo is not None and t < lo:
            continue
        m, y = r.get("m"), str(r.get("y") or "").upper()
        u = float(r.get("u") or 0.0)
        if not m or not y:
            continue
        kept += 1
        per_tok[y][m] += u
        per_mkr[m][y] += u
        net_tok[y] += u if r.get("b") else -u
        gross_all += u
    return as_of, kept, total, future, per_tok, per_mkr, net_tok, gross_all


def hhi(shares):
    return sum(s * s for s in shares)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=float, default=None, help="jam ke belakang dari as_of (default: semua)")
    ap.add_argument("--neighbors", default=None, help="simbol, mis. MARSCOIN")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    as_of, kept, total, future, per_tok, per_mkr, net_tok, gross = load(a.window)
    makers = set(per_mkr)
    n_tok = len(per_tok)
    widths = sorted(len(v) for v in per_tok.values())
    single = sum(1 for w in widths if w == 1)

    hs = []
    for m, tok in per_mkr.items():
        tot = sum(tok.values()) or 1.0
        hs.append((hhi([v / tot for v in tok.values()]), len(tok), m))
    hs.sort(reverse=True)
    top1 = sum(1 for h, ntok, m in hs if h >= 0.9)
    multi = sum(1 for h, ntok, m in hs if ntok >= 4)
    med_h = hs[len(hs) // 2][0] if hs else None

    out = {
        "as_of": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(as_of)) if as_of else None,
        "window_h": a.window, "tx_dipakai": kept, "tx_total": total, "buang_masa_depan": future,
        "maker_unik": len(makers), "simbol_unik": n_tok, "gross_usd": round(gross, 0),
        "maker_per_simbol": {"min": widths[0] if widths else 0,
                             "median": widths[len(widths) // 2] if widths else 0,
                             "p90": widths[int(len(widths) * 0.9)] if widths else 0,
                             "max": widths[-1] if widths else 0},
        "simbol_dengan_1_maker_saja": single,
        "porsi_simbol_1_maker": round(100.0 * single / max(n_tok, 1), 1),
        "hhi_maker": {"median": round(med_h, 3) if med_h else None,
                      "maker_hhi>=0.9 (satu kolam dominates)": top1,
                      "maker_sentuh_>=4_simbol": multi},
    }

    if a.neighbors:
        sym = a.neighbors.upper()
        sym = sym if sym in per_tok else (sym + "USDT" if (sym + "USDT") in per_tok else None)
        peers = collections.Counter()
        me = per_tok.get(sym or "", {})
        for m, u in me.items():
            for other, ou in per_mkr.get(m, {}).items():
                if other != sym:
                    peers[other] += ou
        out["neighbors"] = {"simbol": sym, "makers": len(me),
                            "gross_di_simbol_ini": round(sum(me.values()), 2),
                            "kolam_tetangga": peers.most_common(12)}

    if a.json:
        print(json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False))
        return

    print(f"as_of {out['as_of']} | jendela {out['window_h'] or 'semua'} jam | "
          f"tx dipakai {out['tx_dipakai']:,} dari {out['tx_total']:,} | "
          f"buang baris masa depan {out['buang_masa_depan']}")
    print(f"maker unik {out['maker_unik']} | simbol unik {out['simbol_unik']} | "
          f"gross ~${out['gross_usd']:,.0f}")
    w = out["maker_per_simbol"]
    print(f"\n1) LEBAR cohort per simbol: min {w['min']} | median {w['median']} | p90 {w['p90']} | max {w['max']}")
    print(f"   simbol yang cuma punya SATU maker: {out['simbol_dengan_1_maker_saja']} "
          f"({out['porsi_simbol_1_maker']} % dari {out['simbol_unik']})")
    hm = out["hhi_maker"]
    print(f"\n2) KONSENTRASI per maker (HHI gross, 1 = cuma satu kolam): median {hm['median']}")
    print(f"   maker dengan HHI>=0,9 : {hm['maker_hhi>=0.9 (satu kolam dominates)']} dari {out['maker_unik']}")
    print(f"   maker yang menyentuh >=4 simbol: {hm['maker_sentuh_>=4_simbol']}")
    print("\n   Baca: kalau mayoritas maker HHI-nya dekat 1, 'whale BTC' dan 'whale memecoin' itu")
    print("   memang dua populasi berbeda -> satu panel global salah, cohort per kolam wajib.")
    nb = out.get("neighbors")
    if nb:
        print(f"\n3) KOLOM {nb['simbol']}: {nb['makers']} maker, gross ${nb['gross_di_simbol_ini']:,.2f}")
        for s, u in nb["kolam_tetangga"]:
            print(f"     {s:16} ${u:,.0f} dituker oleh maker yang sama")


if __name__ == "__main__":
    main()

"""Satu tempat untuk deret harga: dua sumber, SATU sumber per kejadian, dan biaya selisihnya.

Kenapa berkas ini ada (semuanya terukur 28 Sep 2026):
  - `universe/wallet-flow.jsonl` menulis `{"k":"px"}` dari payload GMGN (harga pool saat tarik).
  - `universe/watch-prices.jsonl` (P17) menulis `{"k":"wp"}` dari DexScreener untuk token yang
    sudah keluar dari daftar panas - jendela 2 jam, terukur 136 token / 5 batch / siklus.
  - Simulasi di `_research/sim_watch_value.py`: **83,9 %** kejadian beli punya kemunculan token
    yang sama <= 2 jam sebelumnya, tapi alat kami hanya bisa menilai **12,7 %** - karena tidak ada
    alat yang membaca `wp`. Yang hilang bukan datanya, tapi sambungannya.
  - DAN ada biaya yang harus dibayar di muka: pada menit yang sama, dua venue ini berbeda
    **+0,400 % / -0,157 % / -0,228 % / -0,267 %** (empat sampel pertama). 400 bps itu seukuran
    seluruh efek yang kita cari (median K>=2 = +393,4 bps). Jadi mencampur sumber dalam satu
    kejadian = menciptakan angka yang tidak ada di pasar mana pun.

Aturannya, dan ini yang dilakukan kode di bawah:
  1. Satu harga per (token, sumber, stempel) - lewat `flow_cluster_test.dedupe_px()` yang sama.
  2. SATU KEJADIAN SATU SUMBER: harga masuk dan harga keluar WAJIB dari sumber yang sama.
     Kalau tidak ada satu sumber pun yang bisa mengcover kedua ujung, kejadian itu DIBUANG dan
     dihitung sebagai sensor - tidak pernah dinolkan, tidak pernah dicampur.
  3. `--delta` mengukur sendiri selisih dua sumber pada pasangan menit yang berimpit, dan
     mencetak mediannya. Angka itu adalah anggaran kesalahan tiap klaim yang pakai sumber campuran.

Pakai:  python -X utf8 tools/prices.py --report
       python -X utf8 tools/prices.py --self-test
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import flow_cluster_test as FC  # noqa: E402  (dedupe + median kanonik, satu definisi untuk semua)

FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
WATCH = os.path.join(ROOT, "universe", "watch-prices.jsonl")
SRC_GMGN, SRC_WATCH = "gmgn", "watch"
MAX_STALE_MIN = 10


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load(path, kind):
    """Deret harga per token dari satu berkas: [(t, p), ...] terurut, dobel stempel dilebur."""
    raw = {}
    n_row = 0
    if not os.path.exists(path):
        return {}, 0
    for ln in io.open(path, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") != kind:
            continue
        tk = str(d.get("tk") or "").lower()
        t = int(d.get("t") or 0)
        p = float(d.get("p") or 0.0)
        if not tk or not t or p <= 0:
            continue
        raw.setdefault(tk, []).append((t, p))
        n_row += 1
    out = {}
    merged = 0
    for tk, s in raw.items():
        s.sort(key=lambda r: r[0])
        ded = FC.dedupe_px(s)
        merged += len(s) - len(ded)
        out[tk] = ded
    return {"rows": out, "n_row": n_row, "merged": merged}


def load_all():
    return {SRC_GMGN: load(FLOW, "px"), SRC_WATCH: load(WATCH, "wp")}


def pre(series, t, max_stale=MAX_STALE_MIN):
    """Harga terakhir yang STEMPELNYA <= t dan tidak basi (>max_stale menit)."""
    i = bisect.bisect_right([x[0] for x in series], t) - 1
    if i < 0:
        return None
    tt, pp = series[i]
    if t - tt > max_stale * 60:
        return None
    return pp


def exit_median(series, t, horizon, tol=15):
    """Median harga pada jendela keluar [t+H-tol, t+H+tol] menit; None kalau tidak ada."""
    lo, hi = t + (horizon - tol) * 60, t + (horizon + tol) * 60
    xs = [p for tt, p in series if lo <= tt <= hi]
    return FC.med(xs) if xs else None


def pick_source(sources, tk, t, horizon, order=(SRC_GMGN, SRC_WATCH)):
    """Pilih SATU sumber yang bisa cover kedua ujung kejadian. Kembalikan (sumber, p0, p1)."""
    for name in order:
        s = sources.get(name, {}).get("rows", {}).get(tk)
        if not s:
            continue
        p0 = pre(s, t)
        if p0 is None:
            continue
        p1 = exit_median(s, t, horizon)
        if p1 is None:
            continue
        return name, p0, p1
    return None, None, None


def delta_report(sources, max_gap_min=5, limit=None):
    """Selisih dua sumber pada titik yang berimpit (|dt| <= max_gap_min menit), dalam bps."""
    g, w = sources[SRC_GMGN]["rows"], sources[SRC_WATCH]["rows"]
    out = []
    for tk, gs in g.items():
        ws = w.get(tk)
        if not ws:
            continue
        wt = [x[0] for x in ws]
        for t, p in gs:
            i = bisect.bisect_right(wt, t)
            for j in (i - 1, i):
                if not (0 <= j < len(ws)):
                    continue
                tt, pp = ws[j]
                if abs(tt - t) <= max_gap_min * 60 and p > 0:
                    out.append({"tk": tk, "dt_sec": tt - t, "bps": 10000.0 * (pp - p) / p})
                    break
        if limit and len(out) >= limit:
            break
    out.sort(key=lambda r: r["bps"])
    if not out:
        return {"n": 0}
    v = [r["bps"] for r in out]
    return {"n": len(v), "median_bps": round(FC.med(v), 1),
            "p5": round(v[int(0.05 * (len(v) - 1))], 1),
            "p95": round(v[int(0.95 * (len(v) - 1))], 1),
            "min_bps": round(v[0], 1), "max_bps": round(v[-1], 1),
            "abs_median": round(FC.med([abs(x) for x in v]), 1),
            "n_token": len({r["tk"] for r in out})}


def coverage(sources, buys, horizon=30):
    """Berapa kejadian yang bisa dinilai per sumber - dengan aturan satu sumber per kejadian."""
    tot = {"gmgn": 0, "watch": 0, "keduanya": 0, "tidak_ada": 0, "n": 0}
    for tk, ts in buys.items():
        for t in ts:
            tot["n"] += 1
            ok = {}
            for name in (SRC_GMGN, SRC_WATCH):
                s = sources[name]["rows"].get(tk)
                if s and pre(s, t) is not None and exit_median(s, t, horizon) is not None:
                    ok[name] = True
            if ok.get(SRC_GMGN):
                tot["gmgn"] += 1
            if ok.get(SRC_WATCH):
                tot["watch"] += 1
            if ok.get(SRC_GMGN) and ok.get(SRC_WATCH):
                tot["keduanya"] += 1
            if not ok:
                tot["tidak_ada"] += 1
    return tot


def buys_from_flow():
    out = {}
    for ln in io.open(FLOW, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        try:
            d = json.loads(ln)
        except ValueError:
            continue
        if d.get("k") not in ("tx", "txc") or not d.get("b"):
            continue
        tk = str(d.get("tk") or "").lower()
        t = int(d.get("t") or 0)
        if tk and t:
            out.setdefault(tk, []).append(t)
    for tk in out:
        out[tk] = sorted(set(out[tk]))
    return out


def self_test():
    """Derivasi yang tidak boleh berubah: dedupe, basi, satu-sumber, dan delta sintetis."""
    s = [(100, 2.0), (100, 4.0), (200, 3.0)]
    d = FC.dedupe_px(s)
    assert d == [(100, 3.0), (200, 3.0)], d          # median pada stempel dobel = 3,0
    ser = [(0, 1.0), (600, 1.02)]
    assert pre(ser, 700) == 1.02, "harus ambil yang <= t"
    assert pre(ser, 600) == 1.02, "stempel sama boleh dipakai"
    assert pre(ser, 2000, 10) is None, "harga 23 menit lalu harus basi"
    assert exit_median([(0, 1.0), (1800, 2.0), (1900, 4.0)], 0, 30) == 3.0, "median jendela keluar"
    src = {SRC_GMGN: {"rows": {"t1": [(0, 1.0), (1800, 1.1)]}},
           SRC_WATCH: {"rows": {"t1": [(0, 2.0), (1800, 2.2)]}}}
    name, p0, p1 = pick_source(src, "t1", 100, 30)
    assert name == SRC_GMGN and p0 == 1.0 and p1 == 1.1, (name, p0, p1)
    dl = delta_report({SRC_GMGN: {"rows": {"t1": [(0, 1.0)]}},
                       SRC_WATCH: {"rows": {"t1": [(30, 1.01)]}}})
    assert dl["n"] == 1 and abs(dl["median_bps"] - 100.0) < 1e-6, dl
    print("self-test OK: dedupe=%s | basi=%s | satu-sumber=%s | delta=%s"
          % (d[0], pre(ser, 2000, 10) is None, name, dl["median_bps"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--horizon", type=int, default=30)
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    src = load_all()
    for name in (SRC_GMGN, SRC_WATCH):
        r = src[name]
        ts = [t for s in r["rows"].values() for t, _ in s]
        span = (max(ts) - min(ts)) / 3600.0 if ts else 0
        print("%-6s baris=%-6d token=%-5d dilebur=%-5d rentang=%.2f jam | sha=%s"
              % (name, r["n_row"], len(r["rows"]), r["merged"], span,
                 hashlib.sha256(canon(sorted(r["rows"].keys())).encode()).hexdigest()[:12]))
    dl = delta_report(src)
    print("delta dua sumber (|dt|<=5 m): %s" % (json.dumps(dl, sort_keys=True) if dl["n"] else
                                                 "TIDAK ADA PASANGAN - rekaman pantau belum cukup"))
    if a.report:
        cov = coverage(src, buys_from_flow(), a.horizon)
        n = max(cov["n"], 1)
        print("cakupan per kejadian (horison %d m, aturan satu-sumber):" % a.horizon)
        for k in ("gmgn", "watch", "keduanya", "tidak_ada"):
            print("   %-10s %6d  %5.1f %%" % (k, cov[k], 100.0 * cov[k] / n))


if __name__ == "__main__":
    main()

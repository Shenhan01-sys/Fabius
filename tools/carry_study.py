"""Uji carry: apakah funding ekstrem memprediksi arah, dan berapa yang benar-benar bisa diambil?

Ini jawaban atas P13 yang berubah bentuk 28 Sep (F-D25): histori funding ternyata bisa disedot
mundur tanpa kunci (`universe/record_funding_history.py`: OKX 97,7 hari, Bybit 66,3 hari, dua-duanya
per 8 jam), jadi pertanyaan "veto funding kita berguna tidak?" tidak perlu menunggu 30 hari kalender.

Tiga hal yang dijawab, dan ketiganya keluar sebelum satu pun angka disebut "hasil":

  A. **Apakah veto pernah kena.** `tools/direction.py` menolak posisi saat |funding| > 0,05 %/4 jam.
     Deret ini intervalnya 8 jam, jadi padanan aritmetiknya 0,10 %/8 jam. Kalau nol kejadian dalam
     97 hari, veto itu bukan "salah", dia **tidak pernah punya kesempatan benar** - dan itu
     pernyataan yang bisa diukur, bukan pendapat.
  B. **Apakah funding ekstrem memprediksi arah 24 jam berikutnya.** Per basis: kejadian = settlement
     dengan |rate| >= p90 seri itu sendiri; arah dagang = lawan kerumunan (funding positif ->
     shortsided); hasil = return 24 jam dari bar 1 jam `tools/bars.py` (Aster), non-overlap >= 24 jam,
     net sesudah ongkos **terukur** (`tools/costs.py`, default 59 bps). Statistik = MEDIAN +
     bootstrap 5.000 (seed tetap) + tanda-uji eksak; koreksi BH α 0,10 lintas basis untuk
     sumber utama. Mean sengaja BUKAN headline - distribusi funding/return itu ekor gemuk.
  C. **Berapa carry yang riil ada.** rata funding x 3 settlement/hari dalam bps, lawan 59 bps
     round-trip: kalau satu putaran butuh 59 dan carry setahun penuh belum menutupnya, "yield
     funding" bukan strategi, itu angka pembulatan.

Batas yang menempel di keluaran, bukan di kepala saja: funding 8 jam tidak bisa jadi fitur per-bar
1 j / 4 j; satu venue = satu definisi funding (tanda dan periodenya berbeda antar bursa); dan
harga forward kami diambil dari perp Aster untuk aset yang SAMA - kalau asetnya tidak ada di
keduanya, uji itu tidak dijalankan, bukan diisi nol.

Pakai:  python -X utf8 tools/carry_study.py
       python -X utf8 tools/carry_study.py --threshold 0.9 --horizon 24
Artefak: decisions/carry-study-<UTC>.json (+ rows_sha256 supaya bisa dibuktikan ulang)
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import bars as barsmod  # noqa: E402
import costs  # noqa: E402  (satu model ongkos untuk semua jalur uji)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

FLOW = os.path.join(ROOT, "universe", "funding-history.jsonl")
OUT_DIR = os.path.join(ROOT, "decisions")
BASES = ["BNB", "BTC", "ETH", "SOL", "DOGE", "XRP"]
SETTLE_PER_DAY = 3          # interval 8 jam, terukur di manifest
VETO_4H = 0.0005            # FUNDING_EXTREME di tools/direction.py (per 4 jam)
PRIMARY = "okx"             # yang paling dalam (97,7 hari)


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"))


def load_series():
    """{(base, sumber): [(t_ms, rate), ...]} terurut, tanpa duplikat (sumber, t)."""
    out = {}
    if not os.path.exists(FLOW):
        raise SystemExit("tidak ada universe/funding-history.jsonl - jalankan "
                         "python universe/record_funding_history.py dulu")
    for ln in io.open(FLOW, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        d = json.loads(ln)
        if d.get("k") != "fr":
            continue
        out.setdefault((d["base"], d["s"]), []).append((int(d["t"]), float(d["rate"])))
    return {k: sorted(set(v)) for k, v in out.items()}


def pctile(vals, q):
    s = sorted(vals)
    if not s:
        return 0.0
    return s[min(len(s) - 1, int(q * len(s)))]


def boot_median_ci(xs, draws=5000, alpha=0.05):
    if len(xs) < 4:
        return None, None
    rnd = random.Random(20260928)
    meds = []
    n = len(xs)
    for _ in range(draws):
        samp = [xs[rnd.randrange(n)] for _ in range(n)]
        samp.sort()
        meds.append(samp[n // 2] if n % 2 else 0.5 * (samp[n // 2 - 1] + samp[n // 2]))
    meds.sort()
    return meds[int(alpha / 2 * draws)], meds[int((1 - alpha / 2) * draws)]


def sign_test_p(k, n):
    """p satu arah (lebih banyak menang daripada kalah) dengan binomial eksak."""
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(k, n + 1)) / (2.0 ** n)
    return min(1.0, tail)


def bh(passes, alpha=0.10):
    """Benjamini-Hochberg pada daftar (label, p). Mengembalikan himpunan label yang lolos."""
    ordered = sorted(passes, key=lambda kv: kv[1])
    m = len(ordered)
    lolos = set()
    for i, (label, p) in enumerate(ordered, start=1):
        if p <= alpha * i / m:
            lolos.add(label)
    return lolos


def fwd_bps(closes, ts, t_event, horizon_h):
    """Return bersih bps dari t_event ke t_event+horizon pakai bar 1 jam yang tersedia."""
    tgt = t_event + horizon_h * 3600_000
    lo = hi = None
    for t, c in zip(ts, closes):
        if t <= t_event:
            lo = c
        if lo is not None and hi is None and t >= tgt:
            hi = c
    if lo is None or hi is None or lo <= 0:
        return None
    return 10000.0 * (hi - lo) / lo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.9, help="kuantil |funding| untuk kejadian")
    ap.add_argument("--horizon", type=int, default=24, help="jam, tetap, non-overlap")
    ap.add_argument("--days", type=int, default=140)
    a = ap.parse_args()

    rt = costs.rt_cost()
    basis = costs.cost_basis()
    gate = costs.gate_gross_bps(rt)
    ser = load_series()
    rows, veto_hits, carries = [], {}, {}

    print("sumber: %s | ongkos round-trip %.1f bps (basis %s) | ambang gross %.0f bps"
          % (os.path.basename(FLOW), rt, basis, gate))
    print("periode: %s\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    # A. veto pernah kena atau tidak (dihitung dulu, sebelum pembicaraan soal prediksitf)
    print("A. apakah veto funding |rate| > %.4f%%/4j (= %.3f%%/8j) pernah kena?"
          % (VETO_4H * 100, VETO_4H * 2 * 100))
    for (base, src), pts in sorted(ser.items()):
        rates = [abs(r) for _, r in pts]
        hit = sum(1 for r in rates if r > VETO_4H * 2)
        veto_hits["%s/%s" % (base, src)] = hit
        carries["%s/%s" % (base, src)] = sum(rates) / max(len(rates), 1)
        print("   %-6s %-6s n=%4d | max |f|=%.4f%%/8j | median=%.4f%% | kejadian di atas ambang: %d"
              % (base, src, len(pts), max(rates) * 100, pctile(rates, 0.5) * 100, hit))
    tot_hit = sum(veto_hits.values())
    tot_n = sum(len(v) for v in ser.values())
    print("   -> %d dari %d settlement (%.2f %%) melewati ambang veto\n"
          % (tot_hit, tot_n, 100.0 * tot_hit / max(tot_n, 1)))

    # B. funding ekstrem -> arah 24 jam berikutnya?
    print("B. funding ekstrem (|rate| >= p%.0f seri itu) vs return %d jam, arah LAWAN kerumunan"
          % (a.threshold * 100, a.horizon))
    print("   %-6s %-6s %5s %9s %9s %9s %9s %8s %s"
          % ("basis", "sumber", "n", "median", "p95-bawah", "p95-atas", "rata-rata", "p_sign", "lolos BH"))
    ps = []
    harga = {}
    for base in BASES:
        sym = base + "USDT"
        if base not in harga:                      # SATU penarikan bar per basis, bukan per sumber
            got = (barsmod.load(sym, "1h") or {}).get("bars") or []
            if len(got) < 30:
                fresh, meta = barsmod.fetch(sym, "1h", a.days, verbose=False)
                if fresh:
                    barsmod.save(sym, "1h", fresh, meta)
                    got = fresh
            harga[base] = ([b["t"] for b in got], [float(b["c"]) for b in got]) if got else (None, None)
        ts, cl = harga[base]
        for src in (PRIMARY, "bybit"):
            pts = ser.get((base, src)) or []
            if not pts:
                rows.append({"base": base, "sumber": src, "n": 0, "status": "TIDAK ADA DATA FUNDING"})
                continue
            thr = pctile([abs(r) for _, r in pts], a.threshold)
            if not ts or len(ts) < 30:
                rows.append({"base": base, "sumber": src, "n": 0, "status": "TIDAK ADA BAR " + sym})
                continue
            t0, t1 = ts[0], ts[-1]
            ev, last_take = [], None
            for t, r in pts:
                if abs(r) < thr or not (t0 <= t <= t1):
                    continue
                if last_take is not None and t - last_take < a.horizon * 3600_000:
                    continue                      # non-overlap
                fb = fwd_bps(cl, ts, t, a.horizon)
                if fb is None:
                    continue
                signed = -fb if r > 0 else fb      # lawan kerumunan
                ev.append(signed)
                last_take = t
            if len(ev) < 2:
                rows.append({"base": base, "sumber": src, "n": len(ev),
                             "status": "SAMPEL TIDAK CUKUP", "ambang_rate": thr})
                continue
            med = sorted(ev)[len(ev) // 2]
            lo, hi = boot_median_ci(ev)
            wins = sum(1 for x in ev if x > 0)
            p = sign_test_p(wins, len(ev))
            ps.append(("%s/%s" % (base, src), p))
            rows.append({"base": base, "sumber": src, "n": len(ev), "ambang_rate": thr,
                         "median_bps": round(med, 1),
                         "ci_lo": None if lo is None else round(lo, 1),
                         "ci_hi": None if hi is None else round(hi, 1),
                         "mean_bps": round(sum(ev) / len(ev), 1),
                         "net_mean_bps": round(sum(ev) / len(ev) - rt, 1),
                         "wins": wins, "p_sign": round(p, 4)})
            print("   %-6s %-6s %5d %9.1f %9s %9s %9.1f %8.4f %s"
                  % (base, src, len(ev), med, ("%.1f" % lo) if lo is not None else "-",
                     ("%.1f" % hi) if hi is not None else "-", sum(ev) / len(ev), p, ""))
    lolos = bh(ps)
    for r in rows:
        key = "%s/%s" % (r.get("base"), r.get("sumber"))
        if key in lolos:
            r["lolos_bh"] = True
            print("   %-6s %-6s -> LOLOS BH" % (r["base"], r["sumber"]))

    # C. carry vs ongkos
    print("\nC. berapa carry yang riil ada (rata |funding| x %.0f settlement/hari, bps)" % SETTLE_PER_DAY)
    worst = None
    for key, mean_rate in sorted(carries.items()):
        per_day = mean_rate * 10000.0 * SETTLE_PER_DAY
        if worst is None or per_day < worst[1]:
            worst = (key, per_day)
        print("   %-12s rata |f| %6.4f%%/8j -> %6.1f bps/hari | 59 bps tercapai dalam %s hari"
              % (key, mean_rate * 100, per_day,
                 ("%.1f" % (rt / per_day)) if per_day > 0 else "tidak"))

    verdict = ("NETAS - tidak ada satu pun basis yang net positif dengan ongkos terukur"
               if not any(r.get("net_mean_bps", 0) > 0 and r.get("lolos_bh") for r in rows)
               else "ADA kandidat - lihat barisnya, jangan rata-ratakan semuanya")
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "sumber_funding": "universe/funding-history.jsonl",
           "horizon_h": a.horizon, "threshold": a.threshold,
           "cost_bps_rt": rt, "cost_basis": basis, "gate_gross_bps": gate,
           "veto_hits": veto_hits, "veto_total_hit": tot_hit, "veto_total_n": tot_n,
           "carry_bps_per_hari": {k: round(v * 10000.0 * SETTLE_PER_DAY, 2) for k, v in carries.items()},
           "rows": rows, "verdict": verdict,
           "batas": ["funding interval 8 jam, bukan fitur per-bar 1j/4j",
                    "harga forward = perp Aster; venue funding = Bybit/OKX -> dua dunia berbeda",
                    "n per basis kecil; BH lintas basis, bukan lintas horizon",
                    "median + bootstrap sebagai headline; mean hanya pembanding"]}
    out["rows_sha256"] = "0x" + hashlib.sha256(canon(rows).encode()).hexdigest()
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, "carry-study-%s.json" % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True,
              ensure_ascii=False)
    print("\nverdict: %s" % verdict)
    print("artefak: decisions/%s  rows_sha256=%s..."
          % (os.path.basename(p), out["rows_sha256"][:16]))


if __name__ == "__main__":
    main()

# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/08 - Riset Optimasi Ambang.md dan 07 - Epik Kolaborasi Bot Terbuka.md §9).
# Bukan alat resmi; keluaran = bukan klaim produk. Hanya stdlib + paket `engine/` di akar repo. Tidak menyentuh jaringan, kunci, atau chain.
"""Kalibrasi NOL: seberapa sering bot TANPA edge lolos peninjau-bot? (baseline riset optimasi ambang)

    python -X utf8 run13_null_calibration.py [--workers 12] [--quick]

Dua percobaan pada pasar random-walk TANPA drift aritmetik (martingale; biaya tetap dibayar, jadi harapan PnL <= 0):

  A. PENAMBANG: SATU pasar 17 simbol; B1-TREND dan B6-BOUNCE x 10 parameter x 17 universe satu-simbol = 340 konfigurasi. Penambang menjalankan
     peninjau-bot di luar berkali-kali dan hanya mengirim yang lolos (temuan #1 peninjau keamanan). Dilaporkan pada N = 1 (penambang tidak
     mendeklarasikan apa pun) dan N = 340 (jujur: semua percobaan diakui; ambang G3 naik).
  B. SATU KALI: M pasar independen, satu konfigurasi per pasar (B1, N=60, satu simbol) = tingkat positif-palsu untuk pengajuan jujur satu kali.

Vonis memakai gerbang G1-G10 dan KPI K1-K5 dengan GateParams/KpiParams BAWAAN (yang dikunci). G10 = tidak berlaku (tanpa petahana).
Pembacaan: angka di sini adalah tingkat lolos pada DATA NOL - yang ingin kita turunkan tanpa mematikan bot beredge asli (daya: Epik 08 R2).
"""
import argparse
import dataclasses
import math
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from engine import gates, kpi                                  # noqa: E402
from engine.data import MarketData                             # noqa: E402
from engine.series import DAY_MS, Series, sharpe               # noqa: E402
from engine.spec import PERP_UNIVERSE, SPECS                   # noqa: E402

T0 = 1_577_836_800_000
SYMS = list(PERP_UNIVERSE) + ["PAXGUSDT"]
DAYS, VOL = 1400, 0.03
PARAMS = (5, 7, 10, 14, 20, 30, 45, 60, 90, 120)
REQUIRED_PASS = ("PASS", "TB")


def market(seed: int, k: int = len(SYMS)) -> MarketData:
    perp = {}
    for i, s in enumerate(SYMS[:k]):
        r = random.Random(seed * 1000 + i)
        p, rows = 100.0, []
        for d in range(DAYS):
            p *= 1.0 + r.gauss(0.0, VOL)
            p = max(p, 1e-6)
            rows.append([T0 + d * DAY_MS, p, p, p, p, 1.0])
        perp[s] = Series.from_rows(rows)
    return MarketData(perp=perp)


def run_one(job):
    """-> {gate: status}, Sharpe, p5, tahun, vonis (N=1)."""
    seed, tpl, param, sym = job
    md = market(seed)
    spec = dataclasses.replace(SPECS[tpl], bot_id="NOL-1", template=tpl, param=param, universe=(sym,))
    p = gates.GateParams()
    try:
        c = gates._Ctx(spec, md, p, None)
        pnl = c.pnl()
        vals = [v for _, v in pnl]
        sh, q = sharpe(vals), gates._boot_q(vals, p)
        res = [fn(c) for _, _, fn in gates.GATES]
        res += [gates.GateResult(r.gate, r.name, r.status, r.value, r.rule) for r in kpi.evaluate(spec, pnl, c.tg(), None, None)]
    except Exception as e:                                    # konfigurasi degenerat (mis. tanpa sinyal): hitung sebagai tidak lolos
        return job, {"ERR": type(e).__name__}, float("nan"), float("nan"), 0.0, "ERR"
    return job, {r.gate: r.status for r in res}, sh, q, len(pnl) / 365.0, gates.verdict(res)[0]


def verdict_at(statuses, sh, q, years, n_trials):
    """Vonis bila ambang G3 dideflasi untuk `n_trials` percobaan (gerbang lain tak berubah)."""
    if "ERR" in statuses:
        return "ERR"
    st = dict(statuses)
    req = gates.min_sharpe_for_trials(n_trials, years, gates.GateParams().min_net_sharpe)
    st["G3"] = "PASS" if (not math.isnan(sh) and not math.isnan(q) and sh >= req and q > 0) else "FAIL"
    bad = [g for g in gates.REQUIRED if st.get(g) not in REQUIRED_PASS]
    return "LOLOS_SHADOW" if not bad else "TOLAK"


def wilson(k, n, z=1.96):
    """Selang Wilson 95% untuk proporsi k/n. Catatan: pada percobaan A konfigurasi satu pasar saling bergantungan (17 deret, bukan 340 independen),
    jadi selang ini TERLALU SEMPIT; ia hanya memberi skala."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, c - h), min(1.0, c + h))


def summarize(title, rows, n_cfg):
    print(f"\n== {title} ({len(rows)} konfigurasi) ==")
    per_gate = {}
    for _, st, *_ in rows:
        for g, s in st.items():
            per_gate.setdefault(g, [0, 0])
            per_gate[g][0] += 1
            per_gate[g][1] += s in REQUIRED_PASS
    line = "  ".join(f"{g}:{per_gate[g][1]}/{per_gate[g][0]}" for g in sorted(per_gate, key=lambda x: (x[0], int(x[1:]) if x[1:].isdigit() else 0)))
    print("lolos per gerbang (PASS atau TB):", line)
    for n in sorted({1, n_cfg}):
        v = [verdict_at(st, sh, q, y, n) for _, st, sh, q, y, _ in rows]
        k = sum(1 for x in v if x == "LOLOS_SHADOW")
        lo, hi = wilson(k, len(v))
        print(f"LOLOS_SHADOW pada N={n:<4}: {k}/{len(v)} = {100 * k / max(len(v), 1):.1f}%  (Wilson 95%: {100 * lo:.1f}%-{100 * hi:.1f}%)")
    sh_ok = sum(1 for _, _, sh, *_ in rows if not math.isnan(sh) and sh >= 0.5)
    lo, hi = wilson(sh_ok, len(rows))
    print(f"Sharpe net mentah >= 0,5 saja: {sh_ok}/{len(rows)} = {100 * sh_ok / max(len(rows), 1):.1f}%  (Wilson 95%: {100 * lo:.1f}%-{100 * hi:.1f}%)")
    n_err = sum(1 for _, st, *_ in rows if "ERR" in st)
    print(f"konfigurasi galat (dihitung tidak lolos): {n_err}")
    winners = [(job, st) for (job, st, sh, q, y, _) in rows if verdict_at(st, sh, q, y, 1) == "LOLOS_SHADOW"]
    for job, _ in winners[:8]:
        print("  lolos penuh (N=1):", job[1], f"param={job[2]}", job[3])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=min(12, os.cpu_count() or 4))
    ap.add_argument("--quick", action="store_true", help="percobaan kecil (untuk uji skrip)")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    t0 = time.time()
    params = PARAMS[:3] if a.quick else PARAMS
    syms = SYMS[:4] if a.quick else SYMS
    jobs_a = [(a.seed, tpl, p, s) for tpl in ("B1-TREND", "B6-BOUNCE") for p in params for s in syms]
    m = 6 if a.quick else 60
    jobs_b = [(1000 + i, "B1-TREND", 60, SYMS[i % len(SYMS)]) for i in range(m)]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        rows_a = list(ex.map(run_one, jobs_a, chunksize=2))
        rows_b = list(ex.map(run_one, jobs_b, chunksize=1))
    summarize("A. PENAMBANG: satu pasar, semua konfigurasi dicoba", rows_a, len(jobs_a))
    summarize("B. SATU KALI: pasar independen, satu konfigurasi per pasar (B1, N=60)", rows_b, 1)
    print(f"\nwaktu {time.time() - t0:.0f} detik; {a.workers} pekerja; GateParams/KpiParams bawaan (lihat `engine.cli lock`).")
    print("Dalam-sampel pada data NOL; BUKAN klaim tentang pasar nyata.")


if __name__ == "__main__":
    main()

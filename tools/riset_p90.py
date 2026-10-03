"""P90 gelombang 1 - R1 (positif-palsu) + R2 (daya) gerbang v1 TERKUNCI pada pasar sintetik. Pra-registrasi: protokol di bawah di-hash dan di-push
SEBELUM lari sungguhan (vault/06-Results/31 - Pra-Registrasi P90 R1+R2.md). Gelombang ini MENGUKUR v1; ia tidak menyetel satu ambang pun.

    python -X utf8 tools/riset_p90.py protokol            # cetak protokol kanonik + sha (harus sama dengan halaman pra-registrasi)
    python -X utf8 tools/riset_p90.py pilot               # hanya WAKTU per pekerjaan (vonis tidak dicetak: aturan "pilot tidak mengintip")
    python -X utf8 tools/riset_p90.py kalibrasi           # R2: mu injeksi per (dunia, universe, s) + verifikasi s tercapai pada benih segar
    python -X utf8 tools/riset_p90.py r1 | r2 [--workers 14]   # lari; bisa dilanjutkan (id yang sudah ada di berkas hasil dilewati)
    python -X utf8 tools/riset_p90.py ringkas             # tabel + vonis menurut aturan keputusan pra-registrasi

Stdlib + paket `engine/`. Tanpa jaringan, kunci, atau chain. Hasil: riset/p90/*.jsonl, riset/p90/ringkasan.json.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import math
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from statistics import NormalDist

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from engine import gates, locks                                   # noqa: E402
from engine.data import MarketData                                # noqa: E402
from engine.replay import replay                                  # noqa: E402
from engine.series import DAY_MS, Series, sharpe                  # noqa: E402
from engine.spec import PERP_UNIVERSE, SPECS, sha0x               # noqa: E402

OUT = os.path.join(ROOT, "riset", "p90")
T0 = 1_577_836_800_000                                            # 2020-01-01T00:00Z
OK = ("PASS", "TB")

PROTOKOL = {
    "v": 1,
    "nama": "P90 gelombang 1: R1 positif-palsu + R2 daya, gerbang v1 TERKUNCI, pasar sintetik",
    "mengukur": "GateParams/KpiParams bawaan = kunci v1 (engine.cli lock: TERKUNCI); n_trials = 2 (formulir minimum percobaan 1 + 1, seperti review pada k = 1 keluarga)",
    "tidak_menyetel": "gelombang ini tidak mengubah satu ambang pun; perubahan = protokol baru dengan set setel != set konfirmasi + kunci v2 atas kata builder",
    "harga": {"return": "aritmetik harian, rerata 0 di bawah nol, dipotong >= -0.95", "vol_harian": 0.03, "T0": "2020-01-01T00:00Z",
              "biaya": "penggaris spesifikasi templat (7 bps per sisi)", "funding": 0, "simbol": "PERP_UNIVERSE urutan engine, k pertama"},
    "dunia": {
        "W1-iid": "r = 0.03 z, z ~ N(0,1) iid per aset",
        "W2-garch": "GARCH(1,1) per aset: h = w + 0.08 r^2 + 0.90 h, w = 0.03^2 x 0.02; z normal",
        "W3-ekor-t": "r = 0.03 t3 / sqrt(3) (t berderajat bebas 3, varians satu)",
        "W4-faktor": "faktor bersama rho 0.5; varians GARCH(0.08, 0.90) bersama dari return faktor; z t4 varians satu (faktor dan idiosinkratik)",
        "W5-rezim": "rezim volatilitas Markov bersama {0.015, 0.05}, peluang pindah 0.02 per hari; z normal",
    },
    "r1": {
        "dunia": ["W1-iid", "W2-garch", "W3-ekor-t", "W4-faktor", "W5-rezim"],
        "pasar_per_dunia": 1100, "hari": 1400, "seed": "31000000 + 100000 x indeks_dunia + i",
        "konfigurasi": "satu per pasar (pengajuan jujur satu kali), diundi dari rng pasar itu: templat seragam {B1-TREND, B6-BOUNCE, B2-RS}; "
                       "universe seragam {1, 4, 16} (B2-RS: 16, min_aset 8); parameter seragam dari grid",
        "grid": {"B1-TREND": [5, 7, 10, 14, 20, 30, 45, 60, 90, 120], "B6-BOUNCE": [5, 7, 10, 14, 20, 30, 45, 60], "B2-RS": [7, 14, 21, 28, 42, 56, 90]},
        "keluaran": "per pasar: status tiap gerbang G1-G11 + K1-K5, Sharpe, persentil bootstrap, vonis gates.verdict",
        "aturan_keputusan": {
            "per_dunia": "FP = lolos/1100, Wilson 95%: 'A1 TERPENUHI' bila batas atas <= 0.05; 'A1 DILANGGAR' bila batas bawah > 0.05; selain itu 'TIDAK TEGAS'",
            "global": "v1 memenuhi A1 bila semua dunia 'A1 TERPENUHI'",
            "leave_one_gate_out": "FP tanpa gerbang g (gerbang wajib lain tetap): 'penyaring' bila naik >= 0.01 absolut di >= 1 dunia; "
                                  "'tidak menahan beban' bila sama di semua dunia",
        },
    },
    "r2": {
        "dunia": ["W1-iid", "W4-faktor"], "templat": "B1-TREND N = 60", "s": [0.5, 0.75, 1.0, 1.5, 2.0], "hari": [1095, 1400, 2434],
        "universe": [1, 4], "pasar_per_sel": 300, "seed": "41000000 + 10000 x indeks_sel + i (urutan sel: dunia, universe, s, hari)",
        "injeksi": "r_t aset a += mu bila c(t-1) > c(t-61) aset itu (keunggulan yang dieksploitasi B1 N = 60)",
        "kalibrasi": "mu per (dunia, universe, s): grid mu 0..0.012 langkah 0.0005, benih sama (CRN) 20 pasar x 36500 hari, Sharpe NET B1 rata-rata, "
                     "interpolasi linear; s tercapai diverifikasi pada 20 pasar x 36500 hari benih segar (seed 52000000+), dilaporkan",
        "kalibrasi_seed": 51000000,
        "plafon": "run14: daya = 1 - Phi((1.645 - s sqrt(T)) / sqrt(1 + s^2/2))",
        "aturan_keputusan": "daya per sel + Wilson 95%; efisiensi = daya / plafon; 'gerbang memakan daya' bila efisiensi < 0.5 pada s >= 1.0 dan T = 2434 "
                            "di W1-iid. Tidak ada ambang yang berubah otomatis (A3 belum ditetapkan).",
    },
    "aturan": ["pilot hanya mencetak waktu", "hasil negatif dipublikasikan", "penyimpangan dari protokol dipajang di halaman hasil",
               "tidak ada kandidat luar yang antre (aturan #9)"],
    "batas": ["G10 tidak diuji (tanpa petahana)", "B3/B4/B5 tidak diuji (butuh funding/spot/event sintetik) - gelombang berikut",
              "dunia sintetik; tidak ada klaim tentang pasar nyata", "R4 (penambang/oracle) tidak di gelombang ini"],
}

WORLDS = PROTOKOL["r1"]["dunia"]
GRID = PROTOKOL["r1"]["grid"]
VOL = 0.03
_nd = NormalDist()


# ---------------------------------------------------------------- pasar sintetik

def _t_unit(rng: random.Random, nu: int) -> float:
    return rng.gauss(0.0, 1.0) / math.sqrt(rng.gammavariate(nu / 2.0, 2.0) / nu) * math.sqrt((nu - 2) / nu)


def paths(world: str, rng: random.Random, k: int, days: int, mu: float = 0.0, n_edge: int = 60):
    """k deret harga (hari 0 = 100). Return dihasilkan hari demi hari: faktor/rezim bersama dan injeksi bergantung jalur."""
    px = [[100.0] for _ in range(k)]
    h = [VOL * VOL] * k
    hm, state = VOL * VOL, 0
    a_g, b_g, w_g = 0.08, 0.90, VOL * VOL * 0.02
    prev_r = [0.0] * k
    prev_f = 0.0
    for d in range(1, days):
        if world == "W4-faktor":
            hm = w_g + a_g * prev_f * prev_f + b_g * hm
            zf = _t_unit(rng, 4)
            prev_f = math.sqrt(hm) * zf
        if world == "W5-rezim" and rng.random() < 0.02:
            state = 1 - state
        for a in range(k):
            if world == "W1-iid":
                r = VOL * rng.gauss(0.0, 1.0)
            elif world == "W2-garch":
                h[a] = w_g + a_g * prev_r[a] * prev_r[a] + b_g * h[a]
                r = math.sqrt(h[a]) * rng.gauss(0.0, 1.0)
            elif world == "W3-ekor-t":
                r = VOL * _t_unit(rng, 3)
            elif world == "W4-faktor":
                r = math.sqrt(hm) * (math.sqrt(0.5) * zf + math.sqrt(0.5) * _t_unit(rng, 4))
            elif world == "W5-rezim":
                r = (0.015, 0.05)[state] * rng.gauss(0.0, 1.0)
            else:
                raise ValueError(world)
            prev_r[a] = r
            if mu and d - 1 - n_edge >= 0 and px[a][d - 1] > px[a][d - 1 - n_edge]:
                r += mu
            px[a].append(px[a][-1] * (1.0 + max(r, -0.95)))
    return px


def market(world: str, rng: random.Random, k: int, days: int, mu: float = 0.0) -> MarketData:
    perp = {}
    for i, p in enumerate(paths(world, rng, k, days, mu)):
        perp[PERP_UNIVERSE[i]] = Series.from_rows([[T0 + d * DAY_MS, c, c, c, c, 1.0] for d, c in enumerate(p)])
    return MarketData(perp=perp)


def spec_for(tpl: str, param, k: int):
    return dataclasses.replace(SPECS[tpl], bot_id=f"SIN-{tpl}", template=tpl, param=param, universe=tuple(PERP_UNIVERSE[:k]))


# ---------------------------------------------------------------- satu pekerjaan

def _gate_params():
    return dataclasses.replace(gates.GateParams(), n_trials=2)


def evaluate(spec, md) -> dict:
    res = gates.run_gates(spec, md, None, _gate_params())
    v = gates.verdict(res)[0]
    st = {r.gate: r.status for r in res}
    return {"vonis": v, "st": st}


def job_r1(job):
    jid, widx, i = job
    world = WORLDS[widx]
    rng = random.Random(31_000_000 + 100_000 * widx + i)
    tpl = rng.choice(("B1-TREND", "B6-BOUNCE", "B2-RS"))
    k = 16 if tpl == "B2-RS" else rng.choice((1, 4, 16))
    param = rng.choice(GRID[tpl])
    t = time.time()
    md = market(world, rng, k, PROTOKOL["r1"]["hari"])
    out = evaluate(spec_for(tpl, param, k), md)
    return dict(out, id=jid, dunia=world, tpl=tpl, k=k, param=param, dt=round(time.time() - t, 2))


def r2_cells():
    p = PROTOKOL["r2"]
    return [(w, u, s, T) for w in p["dunia"] for u in p["universe"] for s in p["s"] for T in p["hari"]]


def job_r2(job):
    jid, c, i, mu = job
    w, u, s, T = r2_cells()[c]
    rng = random.Random(41_000_000 + 10_000 * c + i)
    t = time.time()
    md = market(w, rng, u, T, mu)
    out = evaluate(spec_for("B1-TREND", 60, u), md)
    return dict(out, id=jid, dunia=w, k=u, s=s, hari=T, mu=mu, dt=round(time.time() - t, 2))


# ---------------------------------------------------------------- kalibrasi R2

MU_GRID = [round(0.0005 * j, 4) for j in range(25)]          # 0 .. 0.012
CAL_N, CAL_DAYS = 20, 36_500


def cal_sharpe(job):
    w, u, mu, seed = job
    md = market(w, random.Random(seed), u, CAL_DAYS, mu)
    return job, sharpe([v for _, v in replay(spec_for("B1-TREND", 60, u), md)])


def kalibrasi(workers: int) -> dict:
    p = PROTOKOL["r2"]
    jobs = [(w, u, mu, PROTOKOL["r2"]["kalibrasi_seed"] + m) for w in p["dunia"] for u in p["universe"] for mu in MU_GRID for m in range(CAL_N)]
    acc = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for (w, u, mu, _), sh in ex.map(cal_sharpe, jobs, chunksize=4):
            acc.setdefault((w, u, mu), []).append(sh)
    curve = {(w, u): [(mu, sum(acc[(w, u, mu)]) / CAL_N) for mu in MU_GRID] for w in p["dunia"] for u in p["universe"]}
    table = {}
    for (w, u), pts in curve.items():
        for s in p["s"]:
            mu = None
            for (m0, s0), (m1, s1) in zip(pts, pts[1:]):
                if s0 <= s <= s1 and s1 > s0:
                    mu = m0 + (s - s0) * (m1 - m0) / (s1 - s0)
                    break
            table[f"{w}|{u}|{s}"] = mu
    ver_jobs = [(w, u, table[f"{w}|{u}|{s}"], 52_000_000 + m) for w in p["dunia"] for u in p["universe"] for s in p["s"]
                if table[f"{w}|{u}|{s}"] is not None for m in range(CAL_N)]
    got = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for (w, u, mu, _), sh in ex.map(cal_sharpe, ver_jobs, chunksize=4):
            got.setdefault((w, u, mu), []).append(sh)
    out = {"kurva": {f"{w}|{u}": pts for (w, u), pts in curve.items()}, "mu": table, "verifikasi": {}}
    for w in p["dunia"]:
        for u in p["universe"]:
            for s in p["s"]:
                mu = table[f"{w}|{u}|{s}"]
                xs = got.get((w, u, mu), [])
                if xs:
                    m = sum(xs) / len(xs)
                    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
                    out["verifikasi"][f"{w}|{u}|{s}"] = {"mu": mu, "s_tercapai": round(m, 3), "galat_baku": round(sd / math.sqrt(len(xs)), 3)}
    return out


# ---------------------------------------------------------------- ringkasan

def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, c - h), min(1.0, c + h))


def passes(st: dict, without: str = "") -> bool:
    if "G*" in st or any(g.endswith("*") and v == "FAIL" for g, v in st.items()):
        return False
    return all(st.get(g) in OK for g in gates.REQUIRED if g != without) and all(s != "NA" or g in gates.ALLOWED_NA for g, s in st.items() if g != without)


def plafon(s: float, years: float) -> float:
    return 1.0 - _nd.cdf((_nd.inv_cdf(0.95) - s * math.sqrt(years)) / math.sqrt(1.0 + s * s / 2.0))


def load(name: str):
    p = os.path.join(OUT, name)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def ringkas() -> dict:
    out = {"protokol_sha": sha0x(PROTOKOL), "r1": {}, "r2": {}}
    rows = load("r1.jsonl")
    print(f"== R1: positif-palsu gerbang v1 (n_trials 2), {len(rows)} pasar ==")
    beda = sum(1 for r in rows if passes(r["st"]) != (r["vonis"] == "LOLOS_SHADOW"))
    out["r1"]["beda_dengan_vonis_resmi"] = beda
    print(f"pemeriksa ulang vonis (passes vs gates.verdict) beda: {beda}")
    verdicts = []
    for w in WORLDS:
        rs = [r for r in rows if r["dunia"] == w]
        n = len(rs)
        k = sum(1 for r in rs if r["vonis"] == "LOLOS_SHADOW")
        lo, hi = wilson(k, n)
        v = "A1 TERPENUHI" if hi <= 0.05 else ("A1 DILANGGAR" if lo > 0.05 else "TIDAK TEGAS")
        verdicts.append(v)
        logo = {}
        for g in gates.REQUIRED:
            logo[g] = sum(1 for r in rs if passes(r["st"], without=g)) / max(n, 1)
        per_tpl = {t: [sum(1 for r in rs if r["tpl"] == t and r["vonis"] == "LOLOS_SHADOW"), sum(1 for r in rs if r["tpl"] == t)] for t in GRID}
        per_gate = {g: sum(1 for r in rs if r["st"].get(g) in OK) / max(n, 1) for g in gates.REQUIRED}
        out["r1"][w] = {"n": n, "lolos": k, "fp": k / max(n, 1), "wilson": [lo, hi], "vonis": v, "tanpa_gerbang": logo, "per_templat": per_tpl, "lolos_per_gerbang": per_gate}
        print(f"{w:10s} lolos {k:4d}/{n:<5d} = {100 * k / max(n, 1):5.2f}%  Wilson {100 * lo:.2f}-{100 * hi:.2f}%  -> {v}  | per templat {per_tpl}")
    out["r1"]["global"] = "v1 memenuhi A1 di semua dunia" if verdicts and all(v == "A1 TERPENUHI" for v in verdicts) else "v1 TIDAK terbukti memenuhi A1 di semua dunia"
    roles = {}
    for g in gates.REQUIRED:
        ups = [out["r1"][w]["tanpa_gerbang"][g] - out["r1"][w]["fp"] for w in WORLDS if out["r1"][w]["n"]]
        roles[g] = "penyaring" if any(x >= 0.01 for x in ups) else ("tidak menahan beban" if all(abs(x) < 1e-12 for x in ups) else "kecil")
    out["r1"]["peran_gerbang"] = roles
    print("peran gerbang (tanpa g):", roles)
    print("GLOBAL:", out["r1"]["global"])
    rows2 = load("r2.jsonl")
    print(f"\n== R2: daya B1 N=60, {len(rows2)} pasar ==")
    for (w, u, s, T) in r2_cells():
        rs = [r for r in rows2 if r["dunia"] == w and r["k"] == u and r["s"] == s and r["hari"] == T]
        if not rs:
            continue
        k = sum(1 for r in rs if r["vonis"] == "LOLOS_SHADOW")
        lo, hi = wilson(k, len(rs))
        pl = plafon(s, T / 365.0)
        out["r2"][f"{w}|{u}|{s}|{T}"] = {"n": len(rs), "daya": k / len(rs), "wilson": [lo, hi], "plafon": pl, "efisiensi": (k / len(rs)) / pl if pl else None}
        print(f"{w:10s} u{u:<2d} s {s:<4} T {T:<5d} daya {100 * k / len(rs):5.1f}% (Wilson {100 * lo:.1f}-{100 * hi:.1f})  plafon {100 * pl:5.1f}%  efisiensi {(k / len(rs)) / pl:.2f}")
    flags = [key for key, v in out["r2"].items() if key.startswith("W1-iid|") and float(key.split("|")[2]) >= 1.0 and key.endswith("|2434")
             and v["efisiensi"] is not None and v["efisiensi"] < 0.5]
    out["r2"]["vonis"] = ("gerbang memakan daya: " + ", ".join(flags)) if flags else "tidak ada sel s >= 1 / T 2434 / W1 dengan efisiensi < 0,5"
    print("R2:", out["r2"]["vonis"])
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "ringkasan.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    return out


# ---------------------------------------------------------------- lari

def run(kind: str, workers: int) -> None:
    st = locks.status()
    if st["state"] != "TERKUNCI":
        raise SystemExit(f"kunci gerbang {st['state']}: riset hanya mengukur v1 yang TERKUNCI")
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{kind}.jsonl")
    done = {r["id"] for r in load(f"{kind}.jsonl")}
    if kind == "r1":
        jobs = [(f"R1|{WORLDS[w]}|{i}", w, i) for w in range(len(WORLDS)) for i in range(PROTOKOL["r1"]["pasar_per_dunia"])]
        fn = job_r1
    else:
        with open(os.path.join(OUT, "kalibrasi.json"), encoding="utf-8") as f:
            mu = json.load(f)["mu"]
        jobs = []
        for c, (w, u, s, T) in enumerate(r2_cells()):
            m = mu[f"{w}|{u}|{s}"]
            if m is None:
                raise SystemExit(f"kalibrasi tidak mencapai s {s} di {w} u{u}: perluas grid mu = penyimpangan protokol, pajang dulu")
            jobs += [(f"R2|{w}|{u}|{s}|{T}|{i}", c, i, m) for i in range(PROTOKOL["r2"]["pasar_per_sel"])]
        fn = job_r2
    todo = [j for j in jobs if j[0] not in done]
    print(f"{kind}: {len(jobs)} pekerjaan, {len(done)} sudah ada, {len(todo)} dijalankan dengan {workers} pekerja; protokol {sha0x(PROTOKOL)}", flush=True)
    t0, n = time.time(), 0
    with ProcessPoolExecutor(max_workers=workers) as ex, open(path, "a", encoding="utf-8", newline="\n") as f:
        futs = [ex.submit(fn, j) for j in todo]
        for fu in as_completed(futs):
            f.write(json.dumps(fu.result(), sort_keys=True) + "\n")
            f.flush()
            n += 1
            if n % 200 == 0:
                el = time.time() - t0
                print(f"  {n}/{len(todo)} selesai, {el / 60:.1f} menit, sisa ~{el / n * (len(todo) - n) / 60:.0f} menit", flush=True)
    print(f"{kind} selesai: {n} pekerjaan dalam {(time.time() - t0) / 60:.1f} menit", flush=True)


def pilot(workers: int) -> None:
    """Waktu saja. Benih pilot (9_000_000+) di luar semua benih protokol; vonis tidak dicetak."""
    jobs = []
    for i, (tpl, k) in enumerate([(t, k) for t in ("B1-TREND", "B6-BOUNCE") for k in (1, 4, 16)] + [("B2-RS", 16)]):
        jobs.append((tpl, k, 9_000_000 + i))
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for (tpl, k, _), dt in zip(jobs, ex.map(_pilot_one, jobs)):
            print(f"  {tpl:10s} u{k:<2d} {dt:6.1f} s")
    print(f"pilot {time.time() - t0:.0f} s dinding")


def _pilot_one(job):
    tpl, k, seed = job
    rng = random.Random(seed)
    t = time.time()
    evaluate(spec_for(tpl, GRID[tpl][3], k), market("W4-faktor", rng, k, 1400))
    return round(time.time() - t, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("protokol", "pilot", "kalibrasi", "r1", "r2", "ringkas"))
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    a = ap.parse_args()
    if a.cmd == "protokol":
        print(json.dumps(PROTOKOL, indent=1, ensure_ascii=False))
        print(f"\nsha protokol: {sha0x(PROTOKOL)}")
    elif a.cmd == "pilot":
        pilot(a.workers)
    elif a.cmd == "kalibrasi":
        t0 = time.time()
        out = kalibrasi(a.workers)
        out["protokol_sha"] = sha0x(PROTOKOL)
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, "kalibrasi.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, indent=1)
        for key, v in out["verifikasi"].items():
            print(f"  {key:22s} mu {v['mu']:.5f} -> s tercapai {v['s_tercapai']:+.3f} (galat baku {v['galat_baku']:.3f})")
        missing = [k for k, v in out["mu"].items() if v is None]
        print(f"kalibrasi {time.time() - t0:.0f} s; tidak tercapai: {missing or 'tidak ada'}")
    elif a.cmd in ("r1", "r2"):
        run(a.cmd, a.workers)
    else:
        ringkas()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

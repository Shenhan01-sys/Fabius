"""P90 gelombang 2 - setel G8 (placebo) dan K2 (Calmar) pada SET SETEL, konfirmasi pada SET BARU (benih baru + satu keluarga dunia baru). Pra-registrasi:
protokol di bawah di-hash dan di-push SEBELUM lari sungguhan (vault/06-Results/33 - Pra-Registrasi P90 Gelombang 2.md). Gelombang ini TIDAK mengubah satu ambang pun:
ia hanya MENGUSULKAN, dan hanya bila terkonfirmasi, kunci baru atas kata builder (F-D126).

    python -X utf8 tools/riset_p90_g2.py protokol                  # protokol kanonik + sha (harus sama dengan halaman pra-registrasi)
    python -X utf8 tools/riset_p90_g2.py pilot                     # hanya WAKTU (benih di luar semua benih protokol; vonis tidak dicetak)
    python -X utf8 tools/riset_p90_g2.py setel-fp | setel-daya [--workers 14]       # SET SETEL (bisa dilanjutkan)
    python -X utf8 tools/riset_p90_g2.py pilih                     # aturan pilihan pra-registrasi -> riset/p90/g2-pilihan.json (SEBELUM konfirmasi)
    python -X utf8 tools/riset_p90_g2.py konfirmasi-fp | konfirmasi-daya [--workers 14]   # SET KONFIRMASI (menolak jalan tanpa pilihan)
    python -X utf8 tools/riset_p90_g2.py ringkas                   # vonis konfirmasi -> riset/p90/g2-ringkasan.json

Tiap pasar dijalankan SATU kali dengan ambang terkunci; yang direkam: status tiap gerbang + dua statistik mentah (G8: batas atas 95 % p placebo; K2: Calmar),
sehingga ambang kandidat dievaluasi OFFLINE tanpa lari ulang (`lolos`). Stdlib + paket `engine/`. Tanpa jaringan, kunci, atau chain.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import riset_p90 as rp                                            # noqa: E402
from engine import gates, kpi as kpimod, locks                      # noqa: E402
from engine.data import MarketData                                # noqa: E402
from engine.replay import replay                                  # noqa: E402
from engine.series import DAY_MS, Series, max_drawdown            # noqa: E402
from engine.spec import PERP_UNIVERSE, sha0x                      # noqa: E402
from engine.target import Target                                  # noqa: E402

OUT = rp.OUT
A1 = 0.05                                                         # anggaran A1 (F-D88); placebo_max_p k = 1 = 1 x A1
P_KALI = [1.0, 1.25, 1.5, 1.75, 2.0]                              # kandidat G8: placebo_max_p = c x A1 (c = 1 = ambang terkunci)
CALMAR = [0.5, 0.4, 0.3]                                          # kandidat K2: min_calmar (0,5 = terkunci)
MARGIN_SETEL = 0.01                                               # set setel: Wilson atas <= A1 - margin (pengaman terhadap optimisme pemenang)
GAIN_MIN = 0.05                                                   # kenaikan rerata daya (mutlak) yang dianggap material, di set setel DAN konfirmasi
TOL_SERI = 0.005                                                  # selisih daya <= ini = seri -> pilih yang lebih ketat
W6 = "W6-lompatan"
WORLDS_SETEL = list(rp.WORLDS)
WORLDS_KONF = list(rp.WORLDS) + [W6]
DAYA_DUNIA, DAYA_UNIVERSE, DAYA_S, DAYA_HARI = ["W1-iid", "W4-faktor"], [1, 4], [1.0, 1.5], [1400, 2434]
SEED = {"setel-fp": 61_000_000, "konfirmasi-fp": 71_000_000, "setel-daya": 81_000_000, "konfirmasi-daya": 91_000_000, "pilot": 9_500_000}
# mu injeksi = nilai kalibrasi gelombang 1 (riset/p90/kalibrasi.json, protokol sha 0xce2f814e...), disalin ke sini supaya ikut di-hash
MU = {"W1-iid|1|1.0": 0.0021500099446232534, "W1-iid|1|1.5": 0.0030219690381890585, "W1-iid|4|1.0": 0.0011642581590203774,
      "W1-iid|4|1.5": 0.001657936698305621, "W4-faktor|1|1.0": 0.0018802597065242645, "W4-faktor|1|1.5": 0.0026673508675394736,
      "W4-faktor|4|1.0": 0.0014455601088131866, "W4-faktor|4|1.5": 0.002064785547955466}

PROTOKOL2 = {
    "nama": "P90 gelombang 2: setel G8 (placebo_max_p) dan K2 (min_calmar) pada set setel, konfirmasi pada set baru; pasar sintetik",
    "mengukur": "gerbang TERKUNCI (GateParams/KpiParams bawaan, n_trials = 2) dijalankan APA ADANYA, satu kali per pasar; direkam status tiap gerbang + G8 batas atas 95% p placebo + K2 Calmar; "
                "ambang kandidat dievaluasi offline: G8 lolos bila batas_atas <= c x A1, K2 lolos bila Calmar >= min_calmar, gerbang lain tetap seperti terukur",
    "tidak_menyetel": "tidak ada ambang yang berubah oleh gelombang ini; hasil terkonfirmasi hanya menjadi USULAN kunci baru atas kata builder (F-D126)",
    "ambang_terkunci": {"placebo_max_p": 0.05, "min_calmar": 0.5, "A1": A1},
    "kandidat": {"placebo_max_p_kali_A1": P_KALI, "min_calmar": CALMAR,
                 "catatan": "15 kombinasi termasuk yang terkunci (c = 1, min_calmar 0,5); c > 1 ~ G8 mendekati uji nominal (batas atas 95% p placebo memang konservatif)"},
    "dunia": {**{w: rp.PROTOKOL["dunia"][w] for w in rp.WORLDS},
              W6: "lompatan: r = sqrt(0.03^2 - 0.01 x 0.12^2) z + J, J = 0.12 z' dengan peluang 0.01 per hari (varians total 0.03^2; tanpa keunggulan); HANYA di set konfirmasi (keluarga generatif baru)"},
    "konfigurasi_fp": "sama dengan R1 gelombang 1: templat seragam {B1-TREND, B6-BOUNCE, B2-RS}; universe seragam {1, 4, 16} (B2-RS: 16); parameter seragam dari grid gelombang 1; satu bot per pasar",
    "setel": {
        "fp": {"dunia": WORLDS_SETEL, "pasar_per_dunia": 600, "hari": 1400, "seed": "61000000 + 100000 x indeks_dunia + i"},
        "daya": {"templat": "B1-TREND N = 60", "dunia": DAYA_DUNIA, "universe": DAYA_UNIVERSE, "s": DAYA_S, "hari": DAYA_HARI, "pasar_per_sel": 200,
                 "seed": "81000000 + 10000 x indeks_sel + i (urutan sel: dunia, universe, s, hari)", "mu": MU,
                 "injeksi": "sama dengan R2 gelombang 1: r_t aset a += mu bila c(t-1) > c(t-61)"},
    },
    "konfirmasi": {
        "fp": {"dunia": WORLDS_KONF, "pasar_per_dunia": 1100, "hari": 1400, "seed": "71000000 + 100000 x indeks_dunia + i"},
        "daya": {"sel": "sama dengan set setel", "pasar_per_sel": 300, "seed": "91000000 + 10000 x indeks_sel + i"},
    },
    "aturan_pilihan": {
        "layak": f"kandidat layak bila di SET SETEL positif-palsu (lolos/600 per dunia, Wilson 95 %) batas atas <= A1 - {MARGIN_SETEL} = {A1 - MARGIN_SETEL} di SEMUA 5 dunia",
        "skor": "rerata daya atas 16 sel daya (bobot sama): W1-iid/W4-faktor x universe 1/4 x s 1,0/1,5 x hari 1400/2434",
        "pilih": f"kandidat layak dengan skor tertinggi; selisih skor <= {TOL_SERI} = seri -> ambil yang lebih ketat (c lebih kecil, lalu min_calmar lebih besar)",
        "materialitas": f"bila skor terpilih - skor terkunci < {GAIN_MIN} (mutlak): TETAP ambang terkunci; konfirmasi tidak dijalankan",
        "satu_kali": "pilihan dicetak ke riset/p90/g2-pilihan.json SEBELUM set konfirmasi dijalankan; konfirmasi menolak jalan tanpa berkas itu; tidak ada putaran setel kedua",
    },
    "aturan_konfirmasi": {
        "fp": f"kandidat terpilih: Wilson 95 % batas atas <= A1 = {A1} di SEMUA 6 dunia (set konfirmasi, 1100 pasar per dunia, termasuk {W6})",
        "daya": f"kenaikan rerata daya terpilih - terkunci >= {GAIN_MIN} (mutlak, pasar yang sama) di 16 sel set konfirmasi",
        "vonis": "TERKONFIRMASI bila keduanya terpenuhi -> USULAN kunci baru atas kata builder; selain itu TETAP ambang terkunci (hasil negatif dipublikasikan)",
    },
    "aturan": ["pilot hanya mencetak waktu", "hasil negatif dipublikasikan", "penyimpangan dari protokol dipajang di halaman hasil",
               "tidak ada kandidat luar yang antre (aturan #9 riset P90)", "tidak ada 'sekali lagi'"],
    "batas": ["G10 tidak diuji (tanpa petahana)", "B3/B4/B5 tidak diuji", "dunia sintetik; tidak ada klaim tentang pasar nyata",
              "K2 adalah KPI ekonomi: usulan mengendurkannya hanya dibenarkan oleh daya pada dunia sintetik, bukan oleh toleransi risiko pelanggan (R3)",
              "pada penerapan, G8 memakai alpha A1/k per pengajuan ke-k (`anggaran.gate_params_for`): c berlaku sebagai pengali alpha, skala per keluarga tetap"],
}


# ---------------------------------------------------------------- dunia baru (hanya konfirmasi)

def paths2(world: str, rng: random.Random, k: int, days: int, mu: float = 0.0):
    if world != W6:
        return rp.paths(world, rng, k, days, mu)
    if mu:
        raise ValueError("W6-lompatan hanya untuk positif-palsu (tanpa keunggulan)")
    base = math.sqrt(rp.VOL ** 2 - 0.01 * 0.12 ** 2)
    px = [[100.0] for _ in range(k)]
    for _ in range(1, days):
        for a in range(k):
            r = base * rng.gauss(0.0, 1.0)
            if rng.random() < 0.01:
                r += 0.12 * rng.gauss(0.0, 1.0)
            px[a].append(px[a][-1] * (1.0 + max(r, -0.95)))
    return px


def market2(world: str, rng: random.Random, k: int, days: int, mu: float = 0.0) -> MarketData:
    perp = {}
    for i, p in enumerate(paths2(world, rng, k, days, mu)):
        perp[PERP_UNIVERSE[i]] = Series.from_rows([[rp.T0 + d * DAY_MS, c, c, c, c, 1.0] for d, c in enumerate(p)])
    return MarketData(perp=perp)


# ---------------------------------------------------------------- gerbang dengan statistik mentah

def g8_raw(c, raw: dict) -> gates.GateResult:
    """Salinan setia `gates._placebo` + `g8_null` (bot jenis waktu) yang juga merekam pv dan batas atas; dijaga tes terhadap gerbang asli."""
    kind = gates.NULL_KIND.get(c.spec.method, ("waktu", ""))
    if kind[0] != "waktu":
        raise ValueError("gelombang 2 hanya menguji bot jenis waktu")
    p = c.p
    rule = f"batas atas 95% (galat Monte Carlo) dari p <= {p.placebo_max_p} terhadap {p.placebo_n} pergeseran waktu melingkar (eksposur sama)"
    actual = gates._sh(c.pnl())
    tg = c.tg()
    n = len(tg)
    if n < 240 or math.isnan(actual):
        return gates.GateResult("G8", "NULL", gates.FAIL, "riwayat terlalu pendek atau Sharpe tak terdefinisi", rule)
    rng = random.Random(p.seed + 1)
    ge = tot = 0
    for _ in range(p.placebo_n):
        k = rng.randrange(60, n - 60)
        tg2 = [Target(tg[j].bot_id, tg[j].t, tg[(j + k) % n].weights, {}) for j in range(n)]
        s = gates._sh(replay(c.spec, c.data, tg2, c.tables))
        if math.isnan(s):
            continue
        tot += 1
        ge += s >= actual
    pv = (1 + ge) / (1 + tot)
    upper = pv + 1.645 * math.sqrt(pv * (1 - pv) / (1 + tot))
    raw["g8_pv"], raw["g8_upper"] = pv, upper
    return gates.GateResult("G8", "NULL", gates.PASS if upper <= p.placebo_max_p else gates.FAIL,
                            f"placebo p = {pv:.3f}, batas atas 95% {upper:.3f} ({ge}/{tot} acak >= {gates._fmt(actual)})", rule)


def run_gates_raw(spec, md, params) -> Tuple[List[gates.GateResult], dict]:
    """Salinan setia `gates.run_gates` (G1-G11 + K1-K5) yang merekam statistik mentah G8 dan K2; dijaga tes terhadap gerbang asli."""
    c = gates._Ctx(spec, md, params, None)
    raw = {"g8_pv": None, "g8_upper": None, "k2_calmar": None}
    try:
        c.pnl()
    except NotImplementedError as e:
        return [gates.GateResult("G*", "SEMUA", gates.NA, str(e), "replay diperlukan")], raw
    except Exception as e:  # noqa: BLE001
        return [gates.GateResult("G*", "SEMUA", gates.FAIL, f"replay gagal ({type(e).__name__})", "replay diperlukan")], raw
    out: List[gates.GateResult] = []
    for gid, name, fn in gates.GATES:
        try:
            out.append(g8_raw(c, raw) if gid == "G8" else fn(c))
        except Exception as e:  # noqa: BLE001
            out.append(gates.GateResult(gid, name, gates.FAIL, f"galat tak terduga ({type(e).__name__}): gerbang gagal tertutup", "gerbang tidak boleh melempar"))
    try:
        for r in kpimod.evaluate(spec, c.pnl(), c.tg(), None, None):
            out.append(gates.GateResult(r.gate, r.name, r.status, r.value, r.rule))
        vals = [v for _, v in c.pnl()]
        if len(vals) >= 30:
            ann = sum(vals) / len(vals) * 365
            mdd = max_drawdown(vals)
            raw["k2_calmar"] = 1e18 if mdd == 0 else ann / abs(mdd)
    except Exception as e:  # noqa: BLE001
        out.append(gates.GateResult("K*", "KPI", gates.FAIL, f"galat tak terduga ({type(e).__name__}): KPI gagal tertutup", "KPI tidak boleh melempar"))
    return out, raw


def evaluate2(spec, md, params=None) -> dict:
    res, raw = run_gates_raw(spec, md, params or rp._gate_params())
    return {"vonis": gates.verdict(res)[0], "st": {r.gate: r.status for r in res}, **raw}


def lolos(rec: dict, c_mult: float, calmar: float) -> bool:
    """Apakah pasar ini LOLOS bila G8 memakai ambang c x A1 dan K2 memakai min_calmar `calmar` (gerbang lain seperti terukur). c = 1, calmar = 0,5 = vonis resmi."""
    st = dict(rec["st"])
    if "G*" in st:
        return False
    u, cal = rec.get("g8_upper"), rec.get("k2_calmar")
    st["G8"] = "PASS" if (u is not None and u <= c_mult * A1) else "FAIL"
    st["K2"] = "PASS" if (cal is not None and cal >= calmar) else "FAIL"
    return rp.passes(st)


# ---------------------------------------------------------------- pekerjaan

def daya_sel() -> List[Tuple[str, int, float, int]]:
    return [(w, u, s, T) for w in DAYA_DUNIA for u in DAYA_UNIVERSE for s in DAYA_S for T in DAYA_HARI]


def job_fp(job):
    jid, seed, world, days = job
    rng = random.Random(seed)
    tpl = rng.choice(("B1-TREND", "B6-BOUNCE", "B2-RS"))
    k = 16 if tpl == "B2-RS" else rng.choice((1, 4, 16))
    param = rng.choice(rp.GRID[tpl])
    t = time.time()
    md = market2(world, rng, k, days)
    out = evaluate2(rp.spec_for(tpl, param, k), md)
    return dict(out, id=jid, dunia=world, tpl=tpl, k=k, param=param, dt=round(time.time() - t, 2))


def job_pw(job):
    jid, seed, w, u, s, T, mu = job
    rng = random.Random(seed)
    t = time.time()
    md = market2(w, rng, u, T, mu)
    out = evaluate2(rp.spec_for("B1-TREND", 60, u), md)
    return dict(out, id=jid, dunia=w, k=u, s=s, hari=T, mu=mu, dt=round(time.time() - t, 2))


def jobs_for(name: str) -> Tuple[list, object]:
    base = SEED[name]
    if name.endswith("-fp"):
        konf = name.startswith("konfirmasi")
        spec = PROTOKOL2["konfirmasi" if konf else "setel"]["fp"]
        worlds = WORLDS_KONF if konf else WORLDS_SETEL
        return [(f"G2|{name}|{w}|{i}", base + 100_000 * wi + i, w, spec["hari"]) for wi, w in enumerate(worlds) for i in range(spec["pasar_per_dunia"])], job_fp
    n = PROTOKOL2["konfirmasi" if name.startswith("konfirmasi") else "setel"]["daya"]["pasar_per_sel"]
    jobs = []
    for ci, (w, u, s, T) in enumerate(daya_sel()):
        mu = MU[f"{w}|{u}|{s}"]
        jobs += [(f"G2|{name}|{w}|{u}|{s}|{T}|{i}", base + 10_000 * ci + i, w, u, s, T, mu) for i in range(n)]
    return jobs, job_pw


def path_of(name: str) -> str:
    return os.path.join(OUT, f"g2-{name}.jsonl")


def load(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def run_set(name: str, workers: int) -> None:
    st = locks.status()
    if st["state"] != "TERKUNCI":
        raise SystemExit(f"kunci gerbang {st['state']}: riset hanya mengukur gerbang yang TERKUNCI")
    if name.startswith("konfirmasi"):
        sel = load_pilihan()
        if sel is None:
            raise SystemExit("konfirmasi menolak jalan: riset/p90/g2-pilihan.json belum ada (jalankan `pilih` SESUDAH set setel selesai)")
        if sel["dipilih"] == sel["terkunci"]:
            raise SystemExit("pilihan = ambang terkunci (tidak material): konfirmasi tidak dijalankan (aturan pra-registrasi)")
    os.makedirs(OUT, exist_ok=True)
    path = path_of(name)
    jobs, fn = jobs_for(name)
    done = {r["id"] for r in load(path)}
    todo = [j for j in jobs if j[0] not in done]
    print(f"{name}: {len(jobs)} pekerjaan, {len(done)} sudah ada, {len(todo)} dijalankan dengan {workers} pekerja; protokol {sha0x(PROTOKOL2)}", flush=True)
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
    print(f"{name} selesai: {n} pekerjaan dalam {(time.time() - t0) / 60:.1f} menit", flush=True)


def pilot(workers: int) -> None:
    """Waktu saja; benih 9_500_000+ di luar semua benih protokol; vonis tidak dicetak."""
    b = SEED["pilot"]
    jobs = [("fp", job_fp, ("p", b + 1, "W4-faktor", 1400)), ("fp", job_fp, ("p", b + 2, "W6-lompatan", 1400)), ("fp", job_fp, ("p", b + 3, "W2-garch", 1400)),
            ("daya", job_pw, ("p", b + 11, "W1-iid", 1, 1.0, 2434, MU["W1-iid|1|1.0"])), ("daya", job_pw, ("p", b + 12, "W4-faktor", 4, 1.5, 2434, MU["W4-faktor|4|1.5"])),
            ("daya", job_pw, ("p", b + 13, "W1-iid", 4, 1.0, 1400, MU["W1-iid|4|1.0"]))]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [(k, ex.submit(fn, j)) for k, fn, j in jobs]
        for k, fu in futs:
            r = fu.result()
            print(f"  {k:5s} {r['dunia']:12s} u{r['k']:<2d} {r['dt']:6.1f} s")
    print(f"pilot {time.time() - t0:.0f} s dinding")


# ---------------------------------------------------------------- pilihan + konfirmasi (aturan pra-registrasi)

def kandidat() -> List[dict]:
    return [{"c": c, "placebo_max_p": round(c * A1, 6), "min_calmar": m} for c in P_KALI for m in CALMAR]


def terkunci() -> dict:
    return {"c": 1.0, "placebo_max_p": A1, "min_calmar": 0.5}


def tabel_fp(rows: list, worlds: List[str], cd: dict) -> dict:
    out = {}
    for w in worlds:
        rs = [r for r in rows if r["dunia"] == w]
        k = sum(1 for r in rs if lolos(r, cd["c"], cd["min_calmar"]))
        lo, hi = rp.wilson(k, len(rs))
        out[w] = {"n": len(rs), "lolos": k, "fp": k / len(rs) if rs else None, "wilson": [lo, hi]}
    return out


def daya_cd(rows: list, cd: dict) -> Tuple[float, dict]:
    per = {}
    for (w, u, s, T) in daya_sel():
        rs = [r for r in rows if r["dunia"] == w and r["k"] == u and r["s"] == s and r["hari"] == T]
        k = sum(1 for r in rs if lolos(r, cd["c"], cd["min_calmar"]))
        per[f"{w}|{u}|{s}|{T}"] = {"n": len(rs), "lolos": k, "daya": k / len(rs) if rs else None}
    vals = [v["daya"] for v in per.values() if v["daya"] is not None]
    return (sum(vals) / len(vals) if vals else float("nan")), per


def konsisten(rows: list) -> int:
    """Pemeriksa: ambang terkunci pada statistik mentah harus MENGHASILKAN vonis resmi (0 beda)."""
    return sum(1 for r in rows if lolos(r, 1.0, 0.5) != (r["vonis"] == "LOLOS_SHADOW"))


def pilih(fp_rows: list, pw_rows: list) -> dict:
    tab = []
    for cd in kandidat():
        fp = tabel_fp(fp_rows, WORLDS_SETEL, cd)
        layak = all(v["n"] > 0 and v["wilson"][1] <= A1 - MARGIN_SETEL for v in fp.values())
        skor, per = daya_cd(pw_rows, cd)
        tab.append({"kandidat": cd, "fp": fp, "layak": layak, "skor": skor})
    kunci = next(t for t in tab if t["kandidat"] == terkunci())
    layak = [t for t in tab if t["layak"]]
    out = {"protokol_sha": sha0x(PROTOKOL2), "terkunci": terkunci(), "n_setel_fp": len(fp_rows), "n_setel_daya": len(pw_rows),
           "konsisten_beda": konsisten(fp_rows) + konsisten(pw_rows), "tabel": tab, "skor_terkunci": kunci["skor"]}
    if not layak:
        out.update(dipilih=terkunci(), alasan="tidak ada kandidat layak (termasuk terkunci) di set setel")
        return out
    best = max(t["skor"] for t in layak)
    seri = [t for t in layak if best - t["skor"] <= TOL_SERI]
    pick = sorted(seri, key=lambda t: (t["kandidat"]["c"], -t["kandidat"]["min_calmar"]))[0]
    gain = pick["skor"] - kunci["skor"]
    if gain < GAIN_MIN or pick["kandidat"] == terkunci():
        out.update(dipilih=terkunci(), alasan=f"kenaikan skor {gain:+.4f} < {GAIN_MIN} (tidak material) atau terkunci sudah terbaik: TETAP ambang terkunci", gain=gain)
    else:
        out.update(dipilih=pick["kandidat"], alasan=f"kandidat layak terbaik: skor {pick['skor']:.4f} vs terkunci {kunci['skor']:.4f} (kenaikan {gain:+.4f})", gain=gain)
    return out


def load_pilihan() -> Optional[dict]:
    p = os.path.join(OUT, "g2-pilihan.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def cmd_pilih() -> dict:
    fp, pw = load(path_of("setel-fp")), load(path_of("setel-daya"))
    n_fp, n_pw = sum(PROTOKOL2["setel"]["fp"]["pasar_per_dunia"] for _ in WORLDS_SETEL), PROTOKOL2["setel"]["daya"]["pasar_per_sel"] * len(daya_sel())
    if len(fp) < n_fp or len(pw) < n_pw:
        raise SystemExit(f"set setel belum lengkap: fp {len(fp)}/{n_fp}, daya {len(pw)}/{n_pw}")
    out = pilih(fp, pw)
    if out["konsisten_beda"]:
        raise SystemExit(f"pemeriksa konsistensi GAGAL: {out['konsisten_beda']} pasar yang vonis ambang-terkuncinya (dari statistik mentah) beda dari vonis resmi - kode perekam harus diperbaiki, pilihan tidak dibuat")
    print(f"== SET SETEL: {len(fp)} pasar positif-palsu, {len(pw)} pasar daya | pemeriksa konsistensi (ambang terkunci vs vonis resmi): beda {out['konsisten_beda']} ==")
    print(f"{'c':>5} {'placebo<=':>9} {'K2>=':>5} {'layak':>6} {'skor':>7}  FP per dunia (Wilson atas)")
    for t in out["tabel"]:
        cd = t["kandidat"]
        print(f"{cd['c']:5.2f} {cd['placebo_max_p']:9.4f} {cd['min_calmar']:5.2f} {'ya' if t['layak'] else '-':>6} {t['skor']:7.4f}  "
              + " ".join(f"{100 * v['fp']:4.1f}({100 * v['wilson'][1]:4.1f})" for v in t["fp"].values()))
    print("TERPILIH:", out["dipilih"], "|", out["alasan"])
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "g2-pilihan.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    return out


def cmd_ringkas() -> dict:
    sel = load_pilihan()
    if sel is None:
        raise SystemExit("belum ada pilihan (jalankan `pilih`)")
    out = {"protokol_sha": sha0x(PROTOKOL2), "dipilih": sel["dipilih"], "terkunci": sel["terkunci"], "alasan_pilihan": sel["alasan"]}
    if sel["dipilih"] == sel["terkunci"]:
        out["vonis"] = "TETAP ambang terkunci (pilihan di set setel tidak material); konfirmasi tidak dijalankan"
        print(out["vonis"])
    else:
        fp, pw = load(path_of("konfirmasi-fp")), load(path_of("konfirmasi-daya"))
        n_fp = PROTOKOL2["konfirmasi"]["fp"]["pasar_per_dunia"] * len(WORLDS_KONF)
        n_pw = PROTOKOL2["konfirmasi"]["daya"]["pasar_per_sel"] * len(daya_sel())
        if len(fp) < n_fp or len(pw) < n_pw:
            raise SystemExit(f"set konfirmasi belum lengkap: fp {len(fp)}/{n_fp}, daya {len(pw)}/{n_pw}")
        cd = sel["dipilih"]
        fp_cd = tabel_fp(fp, WORLDS_KONF, cd)
        fp_ok = all(v["wilson"][1] <= A1 for v in fp_cd.values())
        s_cd, per_cd = daya_cd(pw, cd)
        s_lk, per_lk = daya_cd(pw, terkunci())
        gain = s_cd - s_lk
        out.update(konsisten_beda=konsisten(fp) + konsisten(pw), fp_terpilih=fp_cd, fp_terkunci=tabel_fp(fp, WORLDS_KONF, terkunci()), fp_ok=fp_ok,
                   skor_terpilih=s_cd, skor_terkunci=s_lk, gain=gain, daya_terpilih=per_cd, daya_terkunci=per_lk)
        out["informatif_semua_kandidat"] = [{"kandidat": c, "fp_maks_wilson_atas": max(v["wilson"][1] for v in tabel_fp(fp, WORLDS_KONF, c).values()), "skor": daya_cd(pw, c)[0]}
                                            for c in kandidat()]
        ok = fp_ok and gain >= GAIN_MIN
        out["vonis"] = ("TERKONFIRMASI: USULAN kunci baru (atas kata builder) placebo_max_p = %.4g (c = %.2f x A1), min_calmar = %.2f" % (cd["placebo_max_p"], cd["c"], cd["min_calmar"])
                        if ok else "TIDAK TERKONFIRMASI: TETAP ambang terkunci")
        print(f"== KONFIRMASI: {len(fp)} pasar FP + {len(pw)} pasar daya | konsistensi beda {out['konsisten_beda']} ==")
        for w, v in fp_cd.items():
            print(f"  FP {w:12s} terpilih {100 * v['fp']:5.2f}% (Wilson atas {100 * v['wilson'][1]:5.2f}%)   terkunci {100 * out['fp_terkunci'][w]['fp']:5.2f}%")
        print(f"  daya rerata 16 sel: terpilih {s_cd:.4f} vs terkunci {s_lk:.4f} (kenaikan {gain:+.4f}; syarat >= {GAIN_MIN}); FP semua dunia <= {A1}: {fp_ok}")
        print("VONIS:", out["vonis"])
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "g2-ringkasan.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("protokol", "pilot", "setel-fp", "setel-daya", "pilih", "konfirmasi-fp", "konfirmasi-daya", "ringkas"))
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    a = ap.parse_args()
    if a.cmd == "protokol":
        print(json.dumps(PROTOKOL2, indent=1, ensure_ascii=False))
        print(f"\nsha protokol: {sha0x(PROTOKOL2)}")
    elif a.cmd == "pilot":
        pilot(a.workers)
    elif a.cmd == "pilih":
        cmd_pilih()
    elif a.cmd == "ringkas":
        cmd_ringkas()
    else:
        run_set(a.cmd, a.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

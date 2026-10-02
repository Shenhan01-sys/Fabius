"""Gerbang seleksi bot (F-D71/F-D72): deterministik, dicetak ulang oleh perintahnya, dijalankan pada data dan penggaris KAMI.

Ini inti PENINJAU-BOT (tanpa agen LLM; keputusan builder 2 Okt malam): validitas bukti (G1-G11) + KPI ekonomi "Fabius juga untung"
(K1-K5, `engine/kpi.py`). Angka di formulir penerbit adalah klaim; yang dihitung sebagai bukti hanya keluaran modul ini. Ambang di
`GateParams`/`KpiParams` adalah USULAN sampai dikunci (`engine/locks.py`); setiap gerbang mencetak nilai terukurnya.

KETERBATASAN YANG HARUS DIBACA (temuan peninjau keamanan 2 Okt malam, diukur): gerbang ini deterministik dan publik, jadi penerbit bisa
menjalankannya berulang kali di luar dan hanya mengirim pemenang. Pada 476 konfigurasi random-walk tanpa edge, G3 meloloskan 5,3 % dan dua
konfigurasi lolos semua gerbang. Pertahanannya BUKAN gerbang ini sendirian: (1) ambang G3 naik menurut jumlah percobaan (`n_trials` =
percobaan yang dideklarasikan + riwayat pengajuan keluarga + 1); (2) lolos gerbang hanya membuka SHADOW maju - satu-satunya uji di luar
sampel yang sungguhan; (3) uang/penjualan berbayar menuntut F-D16 pada data maju; (4) batas antrean dan masa tunggu per keluarga
(`slots.can_submit`). Lolos gerbang bukan bukti edge.

Status: PASS | FAIL | NA | TB. NA = tidak terukur (menghalangi, kecuali gerbang yang diizinkan NA); TB = tidak berlaku secara struktural
(mis. G6 untuk bot tanpa jadwal berfase, K4 tanpa klaim). Vonis gagal-tertutup: semua gerbang wajib harus ada dan PASS/TB.

G1 PIT        memotong data di hari D tidak mengubah target hari D (deteksi look-ahead; hari dipilih dari seed) + deterministik
G2 DATA       riwayat cukup panjang; bolong bar kecil (gabungan DAN per seri)
G3 NET        Sharpe net >= max(ambang dasar, ambang terdeflasi N percobaan) DAN persentil-5 bootstrap blok > 0
G4 RECENT     24 bulan terakhir > 0 DAN >= seperempat Sharpe penuh (peluruhan); 12 bulan terakhir negatif = PERINGATAN
G5 PLATEAU    parameter x0,5 ... x1,5 (tipe parameter dihormati; butuh cukup varian berbeda) tetap menghasilkan
G6 PHASE      hasil tidak bergantung pada fase jadwal (hari-minggu / tanggal); RERATA fase, bukan fase terbaik
G7 FOLD       tetap positif setelah tahun terbaik dibuang (F-D16)
G8 NULL       lebih baik dari hipotesis nol: pengacakan waktu (pergeseran melingkar, eksposur sama; batas atas 95 % galat Monte Carlo);
              bot alokasi harus lolos DUA uji: buy&hold aset risiko utama (Sharpe DAN MDD) dan placebo bobot yang sama
G9 COST       tetap positif pada semua biaya (kunci *bps*, *pct*) 2x
G10 MARGINAL  menaikkan Sharpe EW petahana (BUKU SLOT SEKARANG, bukan hanya enam bot Fabius) dan tidak berkorelasi tinggi dengannya
G11 CAPACITY  NA sampai kedalaman/volume per venue terukur (satu-satunya gerbang yang boleh NA)
K1-K5         lihat `engine/kpi.py`
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import math
import random
import statistics
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from . import kpi as kpimod
from .bots import NULL_KIND, PHASE_VARIANTS, REGISTRY
from .data import MarketData
from .quality import find_gaps, missing_days
from .replay import Tables, prepare, replay
from .series import DAY_MS, max_drawdown, sharpe
from .spec import SPECS, BotSpec
from .target import Target

PASS, FAIL, NA, TB = "PASS", "FAIL", "NA", "TB"
Pnl = List[Tuple[int, float]]
REQUIRED = ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9", "G10", "K1", "K2", "K3", "K4", "K5")
ALLOWED_NA = ("G11",)


@dataclass(frozen=True)
class GateParams:
    min_bars: int = 1095                   # >= 3 tahun hari-pnl
    max_gap_frac: float = 0.01             # gabungan semua seri
    max_gap_frac_series: float = 0.05      # per seri: satu seri bolong 20 % tidak boleh tenggelam di antara yang bersih
    pit_days: int = 10                     # jumlah hari titik-potong G1 (selain hari terakhir), dipilih dari seed
    min_net_sharpe: float = 0.5
    boot_block: int = 20
    boot_n: int = 1000
    boot_q: float = 0.05
    n_trials: int = 1                      # percobaan jujur + riwayat pengajuan keluarga + 1; menaikkan ambang Sharpe G3
    recent_days: int = 730
    min_recent_sharpe: float = 0.0         # harus > ini
    recent_min_ratio: float = 0.25         # dan >= rasio x Sharpe penuh (peluruhan dari 3 ke 0,01 tidak boleh lolos)
    plateau_factors: Tuple[float, ...] = (0.5, 0.75, 1.25, 1.5)
    plateau_min_ok: int = 3
    plateau_ratio: float = 0.5             # varian lolos bila Sharpe >= rasio x Sharpe dasar (dan > 0)
    phase_min_mean: float = 0.5            # rerata semua fase; fase terburuk harus > 0
    placebo_n: int = 200
    placebo_max_p: float = 0.05
    cost_mult: float = 2.0
    marginal_min_dsharpe: float = 0.05
    marginal_max_corr: float = 0.7
    seed: int = 20261002

    @classmethod
    def fast(cls) -> "GateParams":
        """Untuk tes: resampling sedikit (tidak dipakai untuk keputusan). 120 placebo = p terkecil 0,008 dan batas atas ~0,02 (< 0,05)."""
        return cls(boot_n=60, placebo_n=120, pit_days=4)


@dataclass(frozen=True)
class GateResult:
    gate: str
    name: str
    status: str
    value: str
    rule: str


def _sh(pnl: Sequence[Tuple[int, float]]) -> float:
    return sharpe([v for _, v in pnl])


def expected_max_z(n: int) -> float:
    """Taksiran E[maks] dari n variabel normal baku iid (Bailey & Lopez de Prado): nilai maksimum yang MUNCUL KARENA UNTUNG bila
    n konfigurasi tanpa edge dicoba. n <= 1 -> 0."""
    if n <= 1:
        return 0.0
    nd = statistics.NormalDist()
    g = 0.5772156649015329
    return (1 - g) * nd.inv_cdf(1 - 1 / n) + g * nd.inv_cdf(1 - 1 / (n * math.e))


def min_sharpe_for_trials(n: int, years: float, base: float) -> float:
    """Ambang Sharpe terdeflasi: tidak lebih rendah dari `base`, dan tidak lebih rendah dari yang bisa muncul karena untung dari n percobaan."""
    return max(base, expected_max_z(n) / math.sqrt(max(years, 1e-9)))


class _Ctx:
    def __init__(self, spec: BotSpec, data: MarketData, p: GateParams, inc: Optional[Dict[str, Pnl]]):
        self.spec, self.data, self.p, self.inc = spec, data, p, inc or {}
        self.tables: Tables = prepare(data)
        self._tg: Optional[List[Target]] = None
        self._pnl: Optional[Pnl] = None

    def tg(self) -> List[Target]:
        if self._tg is None:
            self._tg = REGISTRY[self.spec.method](self.spec, self.data)
        return self._tg

    def pnl(self) -> Pnl:
        if self._pnl is None:
            self._pnl = replay(self.spec, self.data, self.tg(), self.tables)
        return self._pnl


def _same(a: Dict[str, float], b: Dict[str, float]) -> bool:
    return set(a) == set(b) and all(abs(a[k] - b[k]) < 1e-12 for k in a)


def _fmt(x: float) -> str:
    return "nan" if math.isnan(x) else f"{x:+.2f}"


# ---------------------------------------------------------------- gerbang

def g1_pit(c: _Ctx) -> GateResult:
    rule = "semua titik-potong identik dan hasil berulang identik"
    tg = c.tg()
    if not tg:
        return GateResult("G1", "PIT", FAIL, "tidak ada target", rule)
    full = {x.t: x for x in tg}
    days = [x.t for x in tg]
    pool = days[60:-1] if len(days) > 62 else days[:-1]
    rng = random.Random(c.p.seed)
    picks = sorted(rng.sample(pool, min(c.p.pit_days, len(pool)))) if pool else []
    picks.append(days[-1])
    bad = 0
    for t in picks:
        cut = REGISTRY[c.spec.method](c.spec, c.data.upto(t))
        if not (cut and cut[-1].t == t and _same(cut[-1].weights, full[t].weights)):
            bad += 1
    again = REGISTRY[c.spec.method](c.spec, c.data)
    det = len(again) == len(tg) and all(x.t == y.t and _same(x.weights, y.weights) for x, y in zip(again, tg))
    ok = bad == 0 and det
    return GateResult("G1", "PIT", PASS if ok else FAIL, f"{len(picks) - bad}/{len(picks)} hari identik; deterministik {'ya' if det else 'TIDAK'}", rule)


def g2_data(c: _Ctx) -> GateResult:
    p = c.p
    rule = f"hari-pnl >= {p.min_bars}; bolong gabungan <= {p.max_gap_frac * 100:.0f}% dan per seri <= {p.max_gap_frac_series * 100:.0f}%"
    n = len(c.pnl())
    used = set(c.spec.universe) | set(c.spec.konstanta.get("emas_kandidat", []))
    miss = tot = 0
    worst = (0.0, "")
    for kind, bag in (("perp", c.data.perp), ("spot", c.data.spot)):
        for a in sorted(used):
            s = bag.get(a)
            if s is not None and len(s):
                m = sum(missing_days(g) for g in find_gaps(s))
                miss += m
                tot += len(s) + m
                fr = m / (len(s) + m)
                if fr > worst[0]:
                    worst = (fr, f"{kind}:{a}")
    frac = miss / tot if tot else 1.0
    ok = n >= p.min_bars and frac <= p.max_gap_frac and worst[0] <= p.max_gap_frac_series
    return GateResult("G2", "DATA", PASS if ok else FAIL,
                      f"{n} hari-pnl; bolong {miss}/{tot} = {frac * 100:.2f}%; terburuk per seri {worst[0] * 100:.2f}% ({worst[1] or '-'})", rule)


def _boot_q(vals: List[float], p: GateParams) -> float:
    n = len(vals)
    if n < 60:
        return float("nan")
    rng = random.Random(p.seed)
    dbl = vals + vals
    nb = -(-n // p.boot_block)
    res: List[float] = []
    for _ in range(p.boot_n):
        x: List[float] = []
        for _ in range(nb):
            s = rng.randrange(n)
            x += dbl[s:s + p.boot_block]
        v = sharpe(x[:n])
        if not math.isnan(v):
            res.append(v)
    if not res:
        return float("nan")
    res.sort()
    return res[int(p.boot_q * len(res))]


def g3_net(c: _Ctx) -> GateResult:
    p = c.p
    pnl = c.pnl()
    years = len(pnl) / 365.0
    req = min_sharpe_for_trials(p.n_trials, years, p.min_net_sharpe)
    rule = (f"Sharpe net >= max({p.min_net_sharpe}, ambang terdeflasi untuk N={p.n_trials} percobaan) dan persentil-{int(p.boot_q * 100)} "
            f"bootstrap blok > 0")
    vals = [v for _, v in pnl]
    sh, q = sharpe(vals), _boot_q(vals, p)
    ok = not math.isnan(sh) and not math.isnan(q) and sh >= req and q > 0
    return GateResult("G3", "NET", PASS if ok else FAIL, f"Sharpe {_fmt(sh)}; p{int(p.boot_q * 100)} {_fmt(q)}; ambang {req:.2f} (N={p.n_trials})", rule)


def g4_recent(c: _Ctx) -> GateResult:
    p = c.p
    rule = (f"Sharpe {p.recent_days // 30} bulan terakhir > {p.min_recent_sharpe} dan >= {p.recent_min_ratio} x Sharpe penuh; "
            f"12 bulan terakhir negatif = PERINGATAN (tidak menggagalkan)")
    pnl = c.pnl()
    if not pnl:
        return GateResult("G4", "RECENT", FAIL, "tidak ada pnl", rule)
    cut = pnl[-1][0] - p.recent_days * DAY_MS
    rv = [v for t, v in pnl if t > cut]
    sh = sharpe(rv)
    full = _sh(pnl)
    cut12 = pnl[-1][0] - 360 * DAY_MS
    sh12 = sharpe([v for t, v in pnl if t > cut12])
    warn = "; PERINGATAN: 12 bulan terakhir negatif" if (not math.isnan(sh12) and sh12 < 0) else ""
    ratio_ok = math.isnan(full) or full <= 0 or sh >= p.recent_min_ratio * full
    ok = len(rv) >= 30 and not math.isnan(sh) and sh > p.min_recent_sharpe and ratio_ok
    return GateResult("G4", "RECENT", PASS if ok else FAIL, f"{p.recent_days // 30}b {_fmt(sh)} (n={len(rv)}; penuh {_fmt(full)}); 12b {_fmt(sh12)}{warn}", rule)


def _vary(base, f, like=None):
    """Varian dari NILAI parameter kandidat `base`, dengan TIPE parameter template (`like`; bawaan tipe `base`): bilangan bulat tetap bulat
    (>= 2), pecahan tetap pecahan. (Versi sebelumnya memvariasikan nilai bawaan template, bukan nilai kandidat: cacat yang ditangkap tes.)"""
    like = base if like is None else like
    if isinstance(like, int) and not isinstance(like, bool):
        return max(2, int(round(base * f)))
    return float(base) * f


def g5_plateau(c: _Ctx) -> GateResult:
    p = c.p
    rule = (f">= {p.plateau_min_ok} varian BERBEDA yang dievaluasi (param x{p.plateau_factors[0]}..x{p.plateau_factors[-1]}), dengan "
            f"Sharpe >= {p.plateau_ratio} x dasar dan > 0 pada >= {p.plateau_min_ok} di antaranya")
    base = _sh(c.pnl())
    if math.isnan(base) or base <= 0:
        return GateResult("G5", "PLATEAU", FAIL, f"dasar {_fmt(base)}", rule)
    tpl = SPECS.get(c.spec.method)
    like = tpl.param if tpl is not None else c.spec.param
    seen = {c.spec.param}
    rows: List[Tuple[object, float]] = []
    for f in p.plateau_factors:
        v = _vary(c.spec.param, f, like)
        if v in seen:
            continue
        seen.add(v)
        try:
            rows.append((v, _sh(replay(dataclasses.replace(c.spec, param=v), c.data, None, c.tables))))
        except Exception:                                   # varian yang melempar dihitung GAGAL, bukan dibuang diam-diam
            rows.append((v, float("nan")))
    ok_n = sum(1 for _, s in rows if not math.isnan(s) and s > 0 and s >= p.plateau_ratio * base)
    ok = len(rows) >= p.plateau_min_ok and ok_n >= p.plateau_min_ok
    val = f"dasar {c.spec.param}:{_fmt(base)} | " + " ".join(f"{v:g}:{_fmt(s)}" if isinstance(v, float) else f"{v}:{_fmt(s)}" for v, s in rows)
    if len(rows) < p.plateau_min_ok:
        val += f" | hanya {len(rows)} varian berbeda (parameter terlalu kecil untuk diuji landasannya)"
    return GateResult("G5", "PLATEAU", PASS if ok else FAIL, val, rule)


def g6_phase(c: _Ctx) -> GateResult:
    p = c.p
    rule = f"rerata semua fase >= {p.phase_min_mean} dan fase terburuk > 0"
    fn = PHASE_VARIANTS.get(c.spec.method)
    if fn is None:
        return GateResult("G6", "PHASE", TB, "tidak berlaku (bot tanpa jadwal berfase)", rule)
    shs = [_sh(replay(v, c.data, None, c.tables)) for v in fn(c.spec)]
    good = [s for s in shs if not math.isnan(s)]
    if len(good) != len(shs):
        return GateResult("G6", "PHASE", FAIL, "ada fase tanpa Sharpe terdefinisi", rule)
    mean = sum(good) / len(good)
    ok = mean >= p.phase_min_mean and min(good) > 0
    return GateResult("G6", "PHASE", PASS if ok else FAIL, f"rerata {_fmt(mean)}, rentang {_fmt(min(good))}..{_fmt(max(good))} ({len(good)} fase)", rule)


def g7_fold(c: _Ctx) -> GateResult:
    rule = "Sharpe > 0 setelah tahun kalender terbaik dibuang"
    pnl = c.pnl()
    by: Dict[int, float] = {}
    for t, v in pnl:
        y = dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).year
        by[y] = by.get(y, 0.0) + v
    if len(by) < 3:
        return GateResult("G7", "FOLD", FAIL, f"hanya {len(by)} tahun", rule)
    best = max(by, key=lambda y: by[y])
    rest = [v for t, v in pnl if dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc).year != best]
    sh = sharpe(rest)
    return GateResult("G7", "FOLD", PASS if (not math.isnan(sh) and sh > 0) else FAIL, f"tanpa {best}: Sharpe {_fmt(sh)}", rule)


def _bench(c: _Ctx, asset: str) -> Tuple[bool, str]:
    s = c.data.spot.get(asset) or c.data.perp.get(asset)
    if s is None or len(s) < 2:
        return False, f"benchmark {asset} tidak ada"
    rets = {s.t[i]: s.c[i] / s.c[i - 1] - 1.0 for i in range(1, len(s)) if s.c[i - 1]}
    pairs = [(v, rets[t]) for t, v in c.pnl() if t in rets]
    bot, ben = [x for x, _ in pairs], [y for _, y in pairs]
    sb, sk = sharpe(bot), sharpe(ben)
    mb, mk = max_drawdown(bot), max_drawdown(ben)
    ok = not (math.isnan(sb) or math.isnan(sk)) and sb > sk and mb > mk
    return ok, f"vs buy&hold {asset}: Sharpe {_fmt(sb)} vs {_fmt(sk)}; MDD {mb * 100:.1f}% vs {mk * 100:.1f}%"


def _placebo(c: _Ctx) -> Tuple[bool, str]:
    p = c.p
    actual = _sh(c.pnl())
    tg = c.tg()
    n = len(tg)
    if n < 240 or math.isnan(actual):
        return False, "riwayat terlalu pendek atau Sharpe tak terdefinisi"
    rng = random.Random(p.seed + 1)
    ge = tot = 0
    for _ in range(p.placebo_n):
        k = rng.randrange(60, n - 60)
        tg2 = [Target(tg[j].bot_id, tg[j].t, tg[(j + k) % n].weights, {}) for j in range(n)]
        s = _sh(replay(c.spec, c.data, tg2, c.tables))
        if math.isnan(s):
            continue
        tot += 1
        ge += s >= actual
    pv = (1 + ge) / (1 + tot)
    # Titik taksir p berfluktuasi antar seed (B1, 5 seed: 0,040-0,109 dengan 200 acak). Vonis memakai BATAS ATAS satu-sisi 95 %
    # supaya tidak ada bot yang lolos karena seed beruntung: "tidak lolos kecuali jelas lolos".
    upper = pv + 1.645 * math.sqrt(pv * (1 - pv) / (1 + tot))
    return upper <= p.placebo_max_p, f"placebo p = {pv:.3f}, batas atas 95% {upper:.3f} ({ge}/{tot} acak >= {_fmt(actual)})"


def g8_null(c: _Ctx) -> GateResult:
    p = c.p
    kind = NULL_KIND.get(c.spec.method, ("waktu", ""))
    if kind[0] == "alokasi":
        rule = ("bot alokasi: (a) mengalahkan buy&hold aset risiko utama pada Sharpe DAN MDD, dan (b) placebo bobot yang sama "
                f"(batas atas 95% dari p <= {p.placebo_max_p}): campuran saja tidak cukup, ATURANNYA harus menambah nilai")
        ok_b, t_b = _bench(c, kind[1])
        ok_p, t_p = _placebo(c)
        return GateResult("G8", "NULL", PASS if (ok_b and ok_p) else FAIL, f"(a) {t_b} | (b) {t_p}", rule)
    rule = (f"batas atas 95% (galat Monte Carlo) dari p <= {p.placebo_max_p} terhadap {p.placebo_n} pergeseran waktu melingkar "
            f"(eksposur sama); titik taksir p saja bergantung seed")
    ok, text = _placebo(c)
    return GateResult("G8", "NULL", PASS if ok else FAIL, text, rule)


def g9_cost(c: _Ctx) -> GateResult:
    p = c.p
    rule = f"Sharpe > 0 pada semua biaya (kunci *bps*, *pct*) {p.cost_mult:g}x"
    pen = {k: (v * p.cost_mult if (("bps" in k or "pct" in k) and isinstance(v, (int, float)) and not isinstance(v, bool)) else v)
           for k, v in c.spec.penggaris.items()}
    s = _sh(replay(dataclasses.replace(c.spec, penggaris=pen), c.data, c.tg(), c.tables))
    return GateResult("G9", "COST", PASS if (not math.isnan(s) and s > 0) else FAIL, f"Sharpe {_fmt(s)} pada {p.cost_mult:g}x", rule)


def _corr(x: List[float], y: List[float]) -> float:
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx, syy = sum((a - mx) ** 2 for a in x), sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else float("nan")


def g10_marginal(c: _Ctx) -> GateResult:
    p = c.p
    rule = f"dSharpe EW petahana >= {p.marginal_min_dsharpe:+.2f} dan korelasi maks <= {p.marginal_max_corr} (petahana = BUKU SLOT SEKARANG + antrean)"
    if not c.inc:
        return GateResult("G10", "MARGINAL", TB, "tidak ada petahana (slot kosong)", rule)
    mine = c.pnl()
    maps = {k: dict(v) for k, v in c.inc.items()}
    mm = dict(mine)
    starts = [min(m) for m in maps.values() if m] + ([min(mm)] if mm else [])
    start = max(starts)
    days = sorted({t for m in list(maps.values()) + [mm] for t in m if t >= start})
    if len(days) < 60:
        return GateResult("G10", "MARGINAL", FAIL, "jendela bersama terlalu pendek", rule)
    ew_inc = [sum(m.get(t, 0.0) for m in maps.values()) / len(maps) for t in days]
    ew_all = [(sum(m.get(t, 0.0) for m in maps.values()) + mm.get(t, 0.0)) / (len(maps) + 1) for t in days]
    d = sharpe(ew_all) - sharpe(ew_inc)
    mine_v = [mm.get(t, 0.0) for t in days]
    cors = {k: _corr(mine_v, [m.get(t, 0.0) for t in days]) for k, m in maps.items()}
    cmax = max((abs(x) for x in cors.values() if not math.isnan(x)), default=float("nan"))
    ok = not math.isnan(d) and d >= p.marginal_min_dsharpe and (math.isnan(cmax) or cmax <= p.marginal_max_corr)
    return GateResult("G10", "MARGINAL", PASS if ok else FAIL, f"dSharpe EW {d:+.2f}; korelasi maks {_fmt(cmax)} ({len(days)} hari bersama, {len(maps)} petahana)", rule)


def g11_capacity(c: _Ctx) -> GateResult:
    return GateResult("G11", "CAPACITY", NA, "kapasitas dan likuiditas per venue belum terukur (butuh volume kuotasi dan kedalaman buku)",
                      "diukur sebelum uang nyata")


GATES: Tuple[Tuple[str, str, Callable[[_Ctx], GateResult]], ...] = (
    ("G1", "PIT", g1_pit), ("G2", "DATA", g2_data), ("G3", "NET", g3_net), ("G4", "RECENT", g4_recent), ("G5", "PLATEAU", g5_plateau),
    ("G6", "PHASE", g6_phase), ("G7", "FOLD", g7_fold), ("G8", "NULL", g8_null), ("G9", "COST", g9_cost),
    ("G10", "MARGINAL", g10_marginal), ("G11", "CAPACITY", g11_capacity),
)


def run_gates(spec: BotSpec, data: MarketData, incumbents: Optional[Dict[str, Pnl]] = None,
              params: Optional[GateParams] = None, kpi: Optional[kpimod.KpiParams] = None,
              claims: Optional[dict] = None) -> List[GateResult]:
    """Jalankan G1-G11 dan K1-K5. Gagal-tertutup: gerbang yang melempar = FAIL (bukan hilang, bukan lolos)."""
    c = _Ctx(spec, data, params or GateParams(), incumbents)
    try:
        c.pnl()
    except NotImplementedError as e:
        return [GateResult("G*", "SEMUA", NA, str(e), "replay diperlukan")]
    except Exception as e:
        return [GateResult("G*", "SEMUA", FAIL, f"replay gagal ({type(e).__name__})", "replay diperlukan")]
    out: List[GateResult] = []
    for gid, name, fn in GATES:
        try:
            out.append(fn(c))
        except Exception as e:
            out.append(GateResult(gid, name, FAIL, f"galat tak terduga ({type(e).__name__}): gerbang gagal tertutup", "gerbang tidak boleh melempar"))
    try:
        for r in kpimod.evaluate(spec, c.pnl(), c.tg(), kpi, claims):
            out.append(GateResult(r.gate, r.name, r.status, r.value, r.rule))
    except Exception as e:
        out.append(GateResult("K*", "KPI", FAIL, f"galat tak terduga ({type(e).__name__}): KPI gagal tertutup", "KPI tidak boleh melempar"))
    return out


def verdict(results: Sequence[GateResult]) -> Tuple[str, List[str], List[str]]:
    """('LOLOS_SHADOW' | 'TOLAK' | 'TIDAK_TERUKUR' | 'TIDAK_VALID', gerbang gagal, gerbang tak terukur). GAGAL-TERTUTUP: semua gerbang wajib harus
    ada; FAIL -> TOLAK; NA pada gerbang wajib -> TIDAK_TERUKUR (hanya G11 boleh NA). Lolos hanya membuka SHADOW, BUKAN slot dan BUKAN uang nyata."""
    by = {r.gate: r for r in results}
    if len(results) == 1 and results[0].gate == "G*":
        return ("TIDAK_TERUKUR" if results[0].status == NA else "TOLAK"), [r.gate for r in results if r.status == FAIL], [r.gate for r in results if r.status == NA]
    missing = [g for g in REQUIRED if g not in by]
    fails = [g for g in REQUIRED if g in by and by[g].status == FAIL] + [r.gate for r in results if r.gate.endswith("*") and r.status == FAIL]
    nas = [r.gate for r in results if r.status == NA]
    blocking_na = [g for g in nas if g not in ALLOWED_NA]
    if missing:
        return "TIDAK_VALID", fails, sorted(set(nas) | set(missing))
    if fails:
        return "TOLAK", fails, nas
    if blocking_na:
        return "TIDAK_TERUKUR", fails, nas
    return "LOLOS_SHADOW", fails, nas


def format_results(title: str, results: Sequence[GateResult]) -> str:
    lines = [f"== {title} =="]
    for r in results:
        lines.append(f"{r.gate:4} {r.name:9} {r.status:4} {r.value}")
        lines.append(f"{'':15}aturan: {r.rule}")
    v, fails, nas = verdict(results)
    lines.append(f"VONIS: {v}" + (f" (gagal: {', '.join(fails)})" if fails else "") + (f" | tak terukur: {', '.join(nas)}" if nas else ""))
    return "\n".join(lines)

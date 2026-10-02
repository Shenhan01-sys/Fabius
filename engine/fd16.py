"""Pemeriksa F-D16 pada data MAJU (P88): gerbang "uang nyata / jual berbayar" = harapan bersih, bukan win-streak (F-D16, 26 Sep 2026).

Dijalankan atas ledger paper maju per bot (`ledger/paper/<bot>.jsonl`), HANYA memakai `settle` final (funding aktual) dan sinyal maju dari tick:
  S1 n        sinyal maju >= 20 (jumlah `signal_ids` semua tick)                - F-D16 "n >= 20"; KPI K3 memakai ambang yang sama
  S2 harapan  rerata net harian > 0 (net = `replay()` sesudah penggaris per sisi spesifikasi bot)
  S3 CI       batas bawah CI 95 % rerata > 0 (bootstrap blok melingkar 5 hari, 10.000 tarikan, benih = ujung rantai ledger)
  S4 fold     rerata tetap > 0 sesudah BULAN KALENDER (UTC) dengan jumlah net terbesar dibuang; butuh >= 2 bulan
  S5 BH       p satu sisi (bootstrap terpusat) lolos Benjamini-Hochberg alpha 0,10 LINTAS semua bot yang punya p
Vonis per bot: LOLOS (S1-S5 semua) · BELUM CUKUP DATA (S1 gagal, < 20 hari settle, atau < 2 bulan) · TIDAK LOLOS (data cukup, ada syarat yang gagal).

Parameter di atas = USULAN 2 Okt 2026, ditulis SEBELUM settle maju pertama ada (anti-snooping): mengubahnya sesudah melihat data adalah keputusan baru yang
dicatat, bukan penyetelan diam-diam. Batas: "ongkos nyata di ukuran itu" di sini = penggaris spesifikasi (fee per sisi); spread dan dampak belum dimodelkan
(P69), dan paper bukan fill. Fungsi murni: tidak membaca berkas, jaringan, atau jam; pemanggil (`engine.cli ledger fd16`) memverifikasi ledger lebih dulu.
"""
from __future__ import annotations

import datetime as dt
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Fd16Params:
    n_sinyal_min: int = 20
    hari_min: int = 20
    bulan_min: int = 2
    ci_level: float = 0.95
    blok_hari: int = 5
    boot_n: int = 10_000
    alpha_bh: float = 0.10


@dataclass
class Fd16Result:
    bot: str
    vonis: str = "BELUM CUKUP DATA"
    n_sinyal: int = 0
    n_hari: int = 0
    n_bulan: int = 0
    mean_bps: Optional[float] = None
    ci_lo_bps: Optional[float] = None
    ci_hi_bps: Optional[float] = None
    tanpa_bulan_terbaik_bps: Optional[float] = None
    p: Optional[float] = None
    bh_lolos: Optional[bool] = None
    alasan: List[str] = field(default_factory=list)


def _month(bar_ms: int) -> str:
    return dt.datetime.fromtimestamp(bar_ms / 1000, dt.timezone.utc).strftime("%Y-%m")


def seed_of(records: Sequence[dict]) -> int:
    """Benih deterministik = ujung rantai ledger: siapa pun yang menghitung ulang mendapat CI dan p yang sama."""
    h = records[-1].get("h", "0x0") if records else "0x0"
    return int(str(h)[2:18] or "0", 16)


def block_bootstrap_means(x: Sequence[float], block: int, n_draw: int, rng: random.Random) -> List[float]:
    n = len(x)
    if n == 0:
        return []
    block = max(1, min(block, n))
    k = -(-n // block)
    out = []
    for _ in range(n_draw):
        s = 0.0
        taken = 0
        for _b in range(k):
            i = rng.randrange(n)
            for j in range(block):
                if taken == n:
                    break
                s += x[(i + j) % n]
                taken += 1
        out.append(s / n)
    return out


def _quantile(sorted_xs: Sequence[float], q: float) -> float:
    if not sorted_xs:
        return float("nan")
    pos = q * (len(sorted_xs) - 1)
    lo = math.floor(pos)
    hi = min(lo + 1, len(sorted_xs) - 1)
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (pos - lo)


def evaluate_bot(bot: str, records: Sequence[dict], p: Fd16Params = Fd16Params()) -> Fd16Result:
    """S1-S4 + p satu sisi untuk satu bot (S5/BH diputuskan lintas bot oleh `check`)."""
    r = Fd16Result(bot)
    r.n_sinyal = sum(len(t.get("signal_ids", [])) for t in records if t.get("type") == "tick")
    settles = sorted((int(s["bar"]), float(s["net"])) for s in records if s.get("type") == "settle")
    r.n_hari = len(settles)
    months: Dict[str, List[float]] = {}
    for bar, net in settles:
        months.setdefault(_month(bar), []).append(net)
    r.n_bulan = len(months)
    x = [net for _, net in settles]
    if r.n_hari >= 2:
        m = sum(x) / len(x)
        r.mean_bps = m * 1e4
        boots = sorted(block_bootstrap_means(x, p.blok_hari, p.boot_n, random.Random(seed_of(records))))
        a = (1 - p.ci_level) / 2
        r.ci_lo_bps, r.ci_hi_bps = _quantile(boots, a) * 1e4, _quantile(boots, 1 - a) * 1e4
        r.p = (1 + sum(1 for b in boots if b - m >= m)) / (len(boots) + 1)            # H0: rerata <= 0, distribusi bootstrap dipusatkan
        if r.n_bulan >= 2:
            best = max(months, key=lambda k: sum(months[k]))
            rest = [v for k, vs in months.items() if k != best for v in vs]
            r.tanpa_bulan_terbaik_bps = sum(rest) / len(rest) * 1e4
    if r.n_sinyal < p.n_sinyal_min:
        r.alasan.append(f"S1 sinyal maju {r.n_sinyal} < {p.n_sinyal_min}")
    if r.n_hari < p.hari_min:
        r.alasan.append(f"hari settle {r.n_hari} < {p.hari_min}")
    if r.n_bulan < p.bulan_min:
        r.alasan.append(f"bulan {r.n_bulan} < {p.bulan_min} (S4 butuh fold untuk dibuang)")
    enough = not r.alasan
    if r.mean_bps is not None:
        if r.mean_bps <= 0:
            r.alasan.append(f"S2 rerata {r.mean_bps:+.2f} bps/hari <= 0")
        if r.ci_lo_bps is not None and r.ci_lo_bps <= 0:
            r.alasan.append(f"S3 batas bawah CI {r.ci_lo_bps:+.2f} bps <= 0")
        if r.tanpa_bulan_terbaik_bps is not None and r.tanpa_bulan_terbaik_bps <= 0:
            r.alasan.append(f"S4 tanpa bulan terbaik {r.tanpa_bulan_terbaik_bps:+.2f} bps <= 0")
    r.vonis = "BELUM CUKUP DATA" if not enough else ("TIDAK LOLOS" if r.alasan else "LOLOS")      # S5 dinilai di `check`
    return r


def bh_reject(pvals: Dict[str, float], alpha: float) -> Dict[str, bool]:
    """Benjamini-Hochberg step-up: True = hipotesis nol ditolak (lolos) pada FDR alpha."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    k = 0
    for i, (_, pv) in enumerate(items, 1):
        if pv <= i / m * alpha:
            k = i
    return {name: (rank <= k) for rank, (name, _) in enumerate(items, 1)}


def check(ledgers: Dict[str, Sequence[dict]], p: Fd16Params = Fd16Params()) -> List[Fd16Result]:
    res = [evaluate_bot(bot, recs, p) for bot, recs in sorted(ledgers.items())]
    fam = {r.bot: r.p for r in res if r.p is not None}
    dec = bh_reject(fam, p.alpha_bh) if fam else {}
    for r in res:
        if r.p is None:
            continue
        r.bh_lolos = dec[r.bot]
        if not r.bh_lolos:
            r.alasan.append(f"S5 BH alpha {p.alpha_bh} lintas {len(fam)} bot: p {r.p:.4f} tidak lolos")
            if r.vonis == "LOLOS":
                r.vonis = "TIDAK LOLOS"
    return res


def fmt(r: Fd16Result, p: Fd16Params = Fd16Params()) -> str:
    def b(v):
        return "-" if v is None else f"{v:+.2f}"
    return (f"{r.bot}: {r.vonis} | sinyal {r.n_sinyal}/{p.n_sinyal_min} | hari {r.n_hari} | bulan {r.n_bulan} | rerata {b(r.mean_bps)} bps/hari | "
            f"CI{int(p.ci_level * 100)} [{b(r.ci_lo_bps)}; {b(r.ci_hi_bps)}] | tanpa bulan terbaik {b(r.tanpa_bulan_terbaik_bps)} | "
            f"p {'-' if r.p is None else f'{r.p:.4f}'} | BH {'-' if r.bh_lolos is None else ('lolos' if r.bh_lolos else 'tidak')}"
            + (f"\n    alasan: {'; '.join(r.alasan)}" if r.alasan else ""))

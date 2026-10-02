"""KPI minimal "Fabius juga untung saat memakai bot itu" (F-D72) - bagian dari peninjau-bot deterministik (tanpa agen LLM).

Gerbang G1-G11 (`engine/gates.py`) menguji VALIDITAS bukti (look-ahead, overfit, biaya, placebo...). KPI di sini menguji EKONOMI:
apakah memakai bot ini menguntungkan Fabius setelah ongkos dan dibanding menaruh dana di instrumen tanpa risiko. Semua dihitung
pada data dan penggaris kami; ambang di `KpiParams` adalah USULAN yang ditetapkan sebelum melihat hasil enam bot Fabius, kecuali
K2 (lihat di bawah) - dan akan dikunci (`engine/locks.py`) sebelum kandidat luar pertama.

K1 ANN_NET   imbal hasil tahunan net (rerata harian x 365) >= hurdle bebas-risiko + margin. Pembanding = menaruh dana di T-bill token /
             stablecoin berimbal (asumsi 4 %/th; laporan peneliti menyebut 3,1-3,6 % untuk T-bill token KYC - belum diverifikasi ulang).
K2 CALMAR    tahunan net / |MDD| >= 0,5. Skala-bebas: MDD absolut bergantung ukuran posisi (plafon bisa diturunkan), Calmar tidak.
             CATATAN KOREKSI: rancangan awal K2 = "MDD >= -50 %"; saya melihat B1 -58 % lalu menyadari MDD absolut bergantung skala dan
             menggantinya dengan Calmar. Perubahan setelah melihat hasil: dicatat di epik 07.
K3 AKTIVITAS minimal 12 sinyal/tahun (rata-rata) DAN >= 20 sinyal total (F-D16: n >= 20): bot tanpa sinyal tidak ada yang dijual atau dipakai.
K4 KLAIM     klaim penerbit tidak boleh melebihi terukur: Sharpe klaim <= terukur + 0,5; |MDD| klaim tidak lebih kecil dari terukur - 10 poin.
             Tanpa klaim (bot Fabius sendiri): tidak berlaku.
K5 BAGI-LABA skenario TERBURUK bagi Fabius bila basis bagi hasil adalah PROFIT (penerbit ambil bagian dari bulan untung, Fabius menanggung
             bulan rugi). Selalu dicetak; hanya MENGGAGALKAN bila `fee_base == "profit"`. Basis yang dipilih builder = pendapatan penjualan
             sinyal (60/40), jadi K5 informatif: ia menunjukkan KENAPA basis profit ditolak.
"""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .economics import ISSUER_SHARE_BPS
from .series import max_drawdown, sharpe
from .sinyal import diff_signals
from .spec import BotSpec
from .target import Target

PASS, FAIL, NA, TB = "PASS", "FAIL", "NA", "TB"
Pnl = Sequence[Tuple[int, float]]


@dataclass(frozen=True)
class KpiParams:
    hurdle_ann: float = 0.04
    margin_ann: float = 0.02
    min_calmar: float = 0.5
    min_signals_year: float = 12.0
    min_signals_total: int = 20
    claim_tolerance_sharpe: float = 0.5
    claim_tolerance_mdd_pts: float = 10.0
    fee_base: str = "pendapatan"            # "pendapatan" (dipilih builder) | "profit" (K5 menjadi gerbang)
    issuer_share_bps: int = ISSUER_SHARE_BPS


@dataclass(frozen=True)
class KpiResult:
    gate: str
    name: str
    status: str
    value: str
    rule: str


def _years(pnl: Pnl) -> float:
    return len(pnl) / 365.0


def count_signals(spec: BotSpec, tg: Sequence[Target]) -> int:
    """Jumlah sinyal yang akan diterbitkan sepanjang riwayat (aturan yang sama dengan `sinyal.diff_signals`)."""
    h = "0x" + "00" * 32
    n, prev = 0, None
    for cur in tg:
        n += len(diff_signals(spec, prev, cur, h, {}))
        prev = cur
    return n


def monthly_returns(pnl: Pnl) -> List[float]:
    by: Dict[Tuple[int, int], float] = {}
    for t, v in pnl:
        d = dt.datetime.fromtimestamp(t / 1000, dt.timezone.utc)
        by[(d.year, d.month)] = by.get((d.year, d.month), 0.0) + v
    return [by[k] for k in sorted(by)]


def fabius_net_profit_share_ann(pnl: Pnl, issuer_bps: int) -> float:
    """Imbal hasil tahunan Fabius pada skenario 'penerbit ambil bagian dari bulan untung, tanpa menanggung bulan rugi' (kristalisasi
    bulanan, tanpa high-water mark - bentuk yang paling merugikan Fabius)."""
    keep = 1.0 - issuer_bps / 10_000
    yrs = _years(pnl)
    if yrs <= 0:
        return float("nan")
    return sum(keep * max(r, 0.0) + min(r, 0.0) for r in monthly_returns(pnl)) / yrs


def evaluate(spec: BotSpec, pnl: Pnl, tg: Sequence[Target], params: Optional[KpiParams] = None,
             claims: Optional[dict] = None) -> List[KpiResult]:
    p = params or KpiParams()
    vals = [v for _, v in pnl]
    out: List[KpiResult] = []
    if len(vals) < 30:
        return [KpiResult("K*", "SEMUA", FAIL, f"hanya {len(vals)} hari-pnl", "minimal 30 hari")]
    ann = sum(vals) / len(vals) * 365
    mdd = max_drawdown(vals)
    yrs = _years(pnl)

    thr = p.hurdle_ann + p.margin_ann
    out.append(KpiResult("K1", "ANN_NET", PASS if ann >= thr else FAIL,
                         f"tahunan net {ann * 100:+.1f}% vs ambang {thr * 100:.1f}% (hurdle {p.hurdle_ann * 100:.0f}% + margin {p.margin_ann * 100:.0f}%)",
                         "imbal hasil tahunan net >= hurdle bebas-risiko + margin"))

    calmar = math.inf if mdd == 0 else ann / abs(mdd)
    out.append(KpiResult("K2", "CALMAR", PASS if calmar >= p.min_calmar else FAIL,
                         f"Calmar {calmar:.2f} (tahunan {ann * 100:+.1f}% / MDD {mdd * 100:.1f}%)", f"tahunan net / |MDD| >= {p.min_calmar}"))

    n_sig = count_signals(spec, tg)
    per_year = n_sig / yrs
    out.append(KpiResult("K3", "AKTIVITAS", PASS if (per_year >= p.min_signals_year and n_sig >= p.min_signals_total) else FAIL,
                         f"{n_sig} sinyal ({per_year:.1f}/tahun)", f">= {p.min_signals_year:g} sinyal/tahun dan >= {p.min_signals_total} total"))

    if not claims:
        out.append(KpiResult("K4", "KLAIM", TB, "tidak ada klaim (bot Fabius sendiri)", "klaim tidak melebihi terukur"))
    else:
        sh = sharpe(vals)
        cs, cm = claims.get("sharpe_net"), claims.get("mdd_pct")
        bad = []
        if cs is not None and not math.isnan(sh) and cs > sh + p.claim_tolerance_sharpe:
            bad.append(f"Sharpe klaim {cs:+.2f} > terukur {sh:+.2f} + {p.claim_tolerance_sharpe}")
        if cm is not None and abs(cm) < abs(mdd * 100) - p.claim_tolerance_mdd_pts:
            bad.append(f"MDD klaim {cm:.0f}% lebih ringan dari terukur {mdd * 100:.0f}% (toleransi {p.claim_tolerance_mdd_pts:g} poin)")
        out.append(KpiResult("K4", "KLAIM", FAIL if bad else PASS, "; ".join(bad) if bad else f"klaim dalam toleransi (terukur Sharpe {sh:+.2f}, MDD {mdd * 100:.0f}%)",
                             f"Sharpe klaim <= terukur + {p.claim_tolerance_sharpe}; |MDD| klaim >= terukur - {p.claim_tolerance_mdd_pts:g} poin"))

    fab = fabius_net_profit_share_ann(pnl, p.issuer_share_bps)
    gate_on = p.fee_base == "profit"
    if gate_on:
        out.append(KpiResult("K5", "BAGI-LABA", PASS if fab > 0 else FAIL,
                             f"Fabius {fab * 100:+.1f}%/th pada skenario profit-share {p.issuer_share_bps / 100:.0f}% tanpa bagi rugi (bot sendiri {ann * 100:+.1f}%/th)",
                             "basis profit: Fabius harus tetap > 0 setelah bagian penerbit"))
    else:
        out.append(KpiResult("K5", "BAGI-LABA", TB,
                             f"tidak berlaku (basis = pendapatan penjualan). Skenario profit-share terburuk akan memberi Fabius {fab * 100:+.1f}%/th (bot sendiri {ann * 100:+.1f}%/th)",
                             "informatif; menjadi gerbang hanya bila fee_base='profit'"))
    return out

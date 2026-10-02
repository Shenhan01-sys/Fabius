"""Skor MAJU per bot dan statistik berpasangan antar-bot dari ledger paper (P85) - bahan `slots.decide`: `Entry.score_bps` untuk penghuni buku,
`Challenger.shadow_days` / `shadow_score_bps` / `paired` untuk penantang.

Aturan (sama dengan `engine/slots.py`, tidak ada angka baru di sini - semua dari `SlotParams` yang terkunci di kunci v1):
  - Hanya `settle` final (funding aktual) yang dipakai. Hari tanpa settle = TIDAK TERUKUR, bukan nol.
  - Skor = jumlah net harian x 1e4 pada `score_window` HARI KALENDER yang berakhir di `end_ms` (satu ujung bersama untuk semua bot), None bila tercakup
    kurang dari `min_coverage` hari (`slots.rolling_score_bps`).
  - Berpasangan = selisih penantang - penghuni pada hari yang SAMA di jendela yang sama + t-stat (`slots.paired_stat`); None bila cakupan kurang.
  - `shadow_days` = hari kalender sejak bar maju pertama (genesis `first_asof`) sampai `end_ms`; `shadow_score_bps` = jumlah net SEMUA settle sejak genesis.
Fungsi murni: tidak membaca berkas, jaringan, atau jam (CLI `engine.cli ledger skor` yang memuat dan memverifikasi ledger).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from .series import DAY_MS
from .slots import SlotParams, paired_stat, rolling_score_bps, win_rate_diag

Pnl = List[Tuple[int, float]]


@dataclass
class ForwardStats:
    bot: str
    first_asof_ms: Optional[int]
    shadow_days: int
    n_tick: int
    n_gap: int
    n_settle: int
    n_signals: int
    covered_days: int
    score_bps: Optional[float]
    shadow_score_bps: Optional[float]
    win_rate_diag: Optional[float]


def pnl_of(records: Sequence[dict]) -> Pnl:
    return sorted((int(r["bar"]), float(r["net"])) for r in records if r.get("type") == "settle")


def common_end(ledgers: Dict[str, Sequence[dict]], fallback_ms: int) -> int:
    """Ujung jendela bersama = bar settle terakhir di antara semua bot (bot yang tertinggal tidak menggeser jendela yang lain); tanpa settle = `fallback_ms`."""
    last = [p[-1][0] for p in (pnl_of(r) for r in ledgers.values()) if p]
    return max(last) if last else fallback_ms


def stats_for(bot: str, records: Sequence[dict], end_ms: int, p: SlotParams = SlotParams()) -> ForwardStats:
    g = records[0] if records and records[0].get("type") == "genesis" else {}
    first = g.get("first_asof")
    pnl = pnl_of(records)
    start = end_ms - p.score_window * DAY_MS
    return ForwardStats(
        bot=bot, first_asof_ms=first,
        shadow_days=max(0, (end_ms - int(first)) // DAY_MS) if first is not None else 0,
        n_tick=sum(1 for r in records if r.get("type") == "tick"), n_gap=sum(1 for r in records if r.get("type") == "gap"), n_settle=len(pnl),
        n_signals=sum(len(r.get("signal_ids", [])) for r in records if r.get("type") == "tick"),
        covered_days=sum(1 for t, _ in pnl if start < t <= end_ms),
        score_bps=rolling_score_bps(pnl, p.score_window, end_ms, p.min_coverage),
        shadow_score_bps=(sum(v for _, v in pnl) * 1e4) if pnl else None,
        win_rate_diag=win_rate_diag(pnl))


def paired_table(ledgers: Dict[str, Sequence[dict]], end_ms: int, p: SlotParams = SlotParams()) -> Dict[Tuple[str, str], Optional[Tuple[float, float]]]:
    """(a, b) -> (selisih bps a - b, t-stat) pada hari yang sama di jendela skor; None bila cakupan kurang."""
    pn = {b: pnl_of(r) for b, r in ledgers.items()}
    return {(a, b): paired_stat(pn[a], pn[b], p.score_window, end_ms, p.min_coverage) for a in sorted(pn) for b in sorted(pn) if a != b}


def challenger_fields(bot: str, ledgers: Dict[str, Sequence[dict]], incumbents: Sequence[str], end_ms: int,
                      p: SlotParams = SlotParams()) -> dict:
    """Bagian `slots.Challenger` yang datang dari ledger maju. Gerbang, `report_sha`, dan `book_sha` datang dari peninjau, bukan dari sini."""
    st = stats_for(bot, ledgers[bot], end_ms, p)
    pt = paired_table({k: ledgers[k] for k in set(incumbents) | {bot} if k in ledgers}, end_ms, p)
    return {"shadow_days": st.shadow_days, "shadow_score_bps": st.shadow_score_bps,
            "paired": {inc: pt[(bot, inc)] for inc in incumbents if (bot, inc) in pt and pt[(bot, inc)] is not None}}


def fmt(st: ForwardStats, p: SlotParams = SlotParams()) -> str:
    def f(v, d=1):
        return "-" if v is None else f"{v:+.{d}f}"
    return (f"{st.bot}: shadow {st.shadow_days} hari | tick {st.n_tick} gap {st.n_gap} settle {st.n_settle} | sinyal maju {st.n_signals} | "
            f"skor {p.score_window} hari {f(st.score_bps)} bps (cakupan {st.covered_days}/{p.score_window}, minimal {p.min_coverage:.0%}) | "
            f"net sejak genesis {f(st.shadow_score_bps)} bps | win-rate (diagnostik) {'-' if st.win_rate_diag is None else f'{st.win_rate_diag:.0%}'}")

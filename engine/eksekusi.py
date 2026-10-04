"""Inti eksekutor venue (P117, epik 10 "Eksekusi Venue"): rencana order dari target bot, pagar risiko, idempotensi, rekonsiliasi, isi kertas.

Murni: tanpa jaringan, tanpa kunci, tanpa jam dinding. Adaptor venue (`tools/venue_binance.py`, ...) dan kertas-venue (`tools/kertas_eksekusi.py`)
memanggil modul ini; satu jalur kode untuk kertas, testnet, dan live, sama seperti engine memakai satu jalur untuk replay dan live.

Aturan (PRD R-E2..R-E5, T8 SK-E*):
  - target qty = bobot x modal / harga, dibulatkan KE BAWAH ke kelipatan lot (tidak pernah melebihi modal);
  - posisi baru dengan notional di bawah min notional venue TIDAK dibuka - dicatat `dilewati` (UNGKAPKAN, bukan diam: itu yang terjadi pada modal kecil);
  - ubah kecil (< max(min notional, 10 % target)) dilewati dan dicatat; menutup posisi (target 0) selalu dikirim, `reduce_only`;
  - `client_id` deterministik dari (venue, bot, bar, aset, sisi): tick yang sama diproses dua kali = id yang sama = venue menolak order ganda;
  - pagar: aset harus di universe bot, bot long-only tidak boleh short, notional total <= modal x leverage maks (1x), batas per order.
    Posisi yang TIDAK disentuh order rencana ini dinilai pada batas bawah pita tanpa-transaksi (x (1 - `MIN_CHANGE_FRAC`)): rencana sengaja
    membiarkan posisi yang hanyut naik karena harga selama hanyutnya < pita, jadi hanyut itu bukan pelanggaran. Yang disentuh order dinilai penuh.
    (5 Okt 2026: tanpa ini, kenaikan harga ±0,2 % atas posisi yang ditahan menghentikan eksekutor demo - `notional total 2002 > modal 2000`.)
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

MIN_CHANGE_FRAC = 0.10


@dataclass(frozen=True)
class Filter:
    step: float               # kelipatan qty (LOT_SIZE stepSize)
    min_qty: float
    min_notional: float


@dataclass(frozen=True)
class Order:
    asset: str
    side: str                 # BUY | SELL
    qty: float
    ref_price: float
    notional: float
    client_id: str
    reduce_only: bool
    alasan: str


@dataclass(frozen=True)
class Plan:
    orders: Tuple[Order, ...]
    dilewati: Tuple[Tuple[str, str], ...]
    intended: Dict[str, float] = field(default_factory=dict)   # posisi yang dimaksud SESUDAH rencana (aset dilewati = posisi lama)


def client_id(venue: str, bot: str, bar: str, asset: str, side: str) -> str:
    """32 karakter [a-z0-9] (Binance: maks 36, pola ^[.A-Z:/a-z0-9_-]{1,36}$)."""
    return "fx" + hashlib.sha256(f"{venue}|{bot}|{bar}|{asset}|{side}".encode()).hexdigest()[:30]


def floor_step(q: float, step: float) -> float:
    if step <= 0:
        raise ValueError("step harus > 0")
    return round(math.floor(abs(q) / step + 1e-9) * step, 12) * (1 if q >= 0 else -1)


def plan(venue: str, bot: str, bar: str, targets: Dict[str, float], modal: float, pos: Dict[str, float], price: Dict[str, float],
         filt: Dict[str, Filter], min_change_frac: float = MIN_CHANGE_FRAC) -> Plan:
    """Rencana order untuk menyelaraskan `pos` (qty per aset, bertanda) ke `targets` (bobot per aset, bertanda) pada `modal` (quote)."""
    orders: List[Order] = []
    skipped: List[Tuple[str, str]] = []
    intended: Dict[str, float] = {}
    for a in sorted(set(targets) | {k for k, v in pos.items() if abs(v) > 0}):
        w, cur = float(targets.get(a, 0.0)), float(pos.get(a, 0.0))
        px, f = price.get(a), filt.get(a)
        if px is None or px <= 0 or f is None:
            skipped.append((a, "harga atau filter venue tidak ada"))
            intended[a] = cur
            continue
        tq = floor_step(w * modal / px, f.step) if abs(w) > 0 else 0.0
        if abs(w) > 0 and tq == 0 and cur == 0:
            skipped.append((a, f"target {abs(w) * modal:.4f} < 1 lot ({f.step:g} x {px:g})"))
            intended[a] = 0.0
            continue
        d = round(tq - cur, 12)
        intended[a] = cur
        if abs(d) < f.step / 2:
            intended[a] = tq
            continue
        notional = abs(d) * px
        reduce = abs(tq) < abs(cur) and (tq == 0 or (tq > 0) == (cur > 0))
        if tq != 0 and abs(tq) * px < f.min_notional and not reduce:
            skipped.append((a, f"target {abs(tq) * px:.4f} < min notional {f.min_notional:g}"))
            continue
        if not reduce and notional < max(f.min_notional, min_change_frac * abs(tq) * px):
            skipped.append((a, f"ubah kecil {notional:.4f} < max(min notional, {int(min_change_frac * 100)} % target)"))
            continue
        if reduce and tq != 0 and notional < min_change_frac * abs(cur) * px:
            skipped.append((a, f"kurangi kecil {notional:.4f}"))
            continue
        qty = floor_step(abs(d), f.step) if not (reduce and tq == 0) else abs(cur)
        if qty < f.min_qty and not (reduce and tq == 0):
            skipped.append((a, f"qty {qty:g} < min qty {f.min_qty:g}"))
            continue
        side = "BUY" if d > 0 else "SELL"
        orders.append(Order(a, side, qty, px, qty * px, client_id(venue, bot, bar, a, side), reduce,
                            "tutup" if tq == 0 else ("kurangi" if reduce else ("buka" if cur == 0 else "tambah"))))
        intended[a] = round(cur + (qty if side == "BUY" else -qty), 12)
    return Plan(tuple(orders), tuple(skipped), intended)


def guard(p: Plan, *, modal: float, universe: Iterable[str], price: Dict[str, float], long_only: bool,
          max_leverage: float = 1.0, max_order_notional: Optional[float] = None, drift: float = MIN_CHANGE_FRAC) -> List[str]:
    """Pelanggaran pagar (kosong = boleh dikirim). Satu pelanggaran = tidak ada order yang dikirim (PRD R-E5).
    `drift` = pita tanpa-transaksi rencana (`plan(min_change_frac=...)`): posisi tanpa order dinilai x (1 - drift)."""
    out: List[str] = []
    uni = set(universe)
    for o in p.orders:
        if o.asset not in uni:
            out.append(f"{o.asset}: di luar universe bot")
        if max_order_notional is not None and o.notional > max_order_notional * (1 + 1e-9):
            out.append(f"{o.asset}: notional order {o.notional:.4f} > batas {max_order_notional:g}")
    for a, q in p.intended.items():
        if long_only and q < -1e-12:
            out.append(f"{a}: posisi short pada bot long-only")
    touched = {o.asset for o in p.orders}
    gross = sum(abs(q) * price.get(a, 0.0) * (1.0 if a in touched else 1.0 - drift) for a, q in p.intended.items())
    if gross > modal * max_leverage * (1 + 1e-9):
        out.append(f"notional total {gross:.4f} > modal {modal:g} x leverage {max_leverage:g} (posisi tanpa order dinilai x {1 - drift:g})")
    return out


def reconcile(intended: Dict[str, float], actual: Dict[str, float], filt: Dict[str, Filter]) -> List[Tuple[str, float, float]]:
    """Aset yang posisinya di venue berbeda dari yang dimaksud lebih dari setengah lot (PRD R-E3; selisih = TOLAK, mode turun ke dry)."""
    out = []
    for a in sorted(set(intended) | set(actual)):
        i, x = intended.get(a, 0.0), actual.get(a, 0.0)
        step = filt[a].step if a in filt else 1e-12
        if abs(i - x) > step / 2:
            out.append((a, i, x))
    return out


def fill_paper(o: Order, px: float, fee_bps: float, slip_bps: float) -> Tuple[float, float]:
    """Isi kertas order pasar: harga dirugikan `slip_bps` searah order; fee = notional x fee_bps. -> (harga isi, fee quote)."""
    p = px * (1 + slip_bps / 1e4) if o.side == "BUY" else px * (1 - slip_bps / 1e4)
    return p, o.qty * p * fee_bps / 1e4


def loss_breached(equity_start: float, equity_now: float, max_loss_frac: float) -> bool:
    """Rugi harian melewati batas (PRD R-E5, T8 SK-E7): True = berhenti, mode dry, hanya builder yang menyalakan lagi."""
    return equity_start > 0 and (equity_start - equity_now) / equity_start > max_loss_frac


def apply_fills(pos: Dict[str, float], cash: float, fills: Sequence[Tuple[Order, float, float]]) -> Tuple[Dict[str, float], float]:
    """Posisi + kas sesudah isi (kertas/rekonsiliasi lokal). fills = (order, harga isi, fee)."""
    pos = dict(pos)
    for o, p, fee in fills:
        q = o.qty if o.side == "BUY" else -o.qty
        pos[o.asset] = round(pos.get(o.asset, 0.0) + q, 12)
        cash -= q * p + fee
        if abs(pos[o.asset]) < 1e-15:
            pos.pop(o.asset)
    return pos, cash

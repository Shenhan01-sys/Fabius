"""Buku slot bot (F-D71/F-D72): maksimal 10, minimal 1 bot identitas Fabius, sembilan sisanya terbuka; rolling berbasis PnL net.

Fungsi murni: keadaan masuk, keputusan keluar (tidak ada keadaan tersembunyi, tidak ada waktu sistem, tidak ada jaringan).
Semua ambang di `SlotParams` adalah USULAN sampai dikunci (`engine/locks.py`).

KEDUDUKAN SLOT (penting): slot = status operasional PAPER berhak-rendah (masuk ke himpunan pilihan operator dan katalog). Slot BUKAN bukti
edge: 60 hari shadow tidak bisa membuktikan edge yang realistis (t-stat 60 hari untuk Sharpe 1 tahunan hanya ~0,4). Hak tinggi - sinyal
berbayar dan bagi hasil nyata - menuntut F-D16 pada data maju (n >= 20, harapan net > 0, batas bawah CI > 0, BH) dan telaah hukum.

Aturan:
  - Kapasitas 10. Wajib ada >= 1 bot IDENTITAS milik Fabius; bot identitas TIDAK bisa digusur rolling dan hanya keluar lewat pembunuhnya
    sendiri (`killer_triggered`), itupun hanya bila bot identitas lain sudah ada. Sembilan slot lainnya bebas (termasuk bot Fabius lain).
  - Penantang masuk hanya bila: gerbang lolos (`gates.verdict == LOLOS_SHADOW`) DAN laporan peninjau dibuat terhadap BUKU YANG SAMA dengan
    sekarang (`book_sha`; G10 bergantung pada petahana, laporan lama basi), shadow maju >= `shadow_days` hari dengan PnL net shadow > 0 (hingga),
    spesifikasi EFEKTIF (`fingerprint`) belum ada di buku (ganti nama / ubah kalimat / urutan universe tidak membuat bot baru).
  - Satu penerbit luar paling banyak `MAX_PER_ISSUER` slot; "penerbit" = keluarga: yang berbagi dompet payout digabung (union-find).
  - Slot penuh -> rolling: penantang menggantikan penghuni TERLEMAH yang boleh digusur (bukan identitas, lewat masa tenggang) hanya bila
    selisih BERPASANGAN pada jendela yang sama >= `margin_bps` DAN t-stat >= `min_gap_tstat` (noise tidak menggusur apa pun). Penghuni yang
    belum terukur sesudah masa tenggang + jendela dianggap MATI/basi (skor -tak hingga) dan boleh digantikan oleh penantang sah mana pun.
    Seri diputus oleh hash (`fingerprint`, epoch), bukan nama yang bisa dipilih penerbit. Paling banyak `max_replace_per_epoch` per epoch.
  - Skor = PnL net bps pada jendela `score_window` HARI KALENDER setelah penggaris (bukan win-rate, bukan jumlah baris): F-D16 mematikan
    win-rate sebagai ukuran. Win-rate hanya diagnostik.
  - Antrean: `can_submit` membatasi pengajuan berjalan per keluarga dan menerapkan masa tunggu setelah penolakan (tanpa biaya pengajuan,
    jadi spam dibatasi dengan batas ini, bukan dengan uang).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Sequence, Tuple

from . import chain
from .series import DAY_MS, max_drawdown, sharpe
from .spec import sha0x

FABIUS = "FABIUS"
MAX_SLOTS = 10
MIN_IDENTITY = 1
MAX_PER_ISSUER = 2
DAY_S = 86_400

ADMIT, REPLACE, BENCH, REJECT = "ADMIT", "REPLACE", "BENCH", "REJECT"


@dataclass(frozen=True)
class SlotParams:
    shadow_days: int = 60
    grace_days: int = 60
    score_window: int = 90
    margin_bps: float = 100.0
    min_gap_tstat: float = 2.0
    max_replace_per_epoch: int = 1
    epoch_days: int = 30
    queue_max_per_family: int = 2
    cooldown_days: int = 30
    min_coverage: float = 0.8


@dataclass(frozen=True, kw_only=True)
class Entry:
    bot_id: str
    issuer: str                              # FABIUS atau alamat EIP-55 penerbit luar
    spec_sha: str
    fingerprint: str                         # BotSpec.fingerprint(): identitas EFEKTIF spesifikasi
    admitted_s: int                          # detik Unix saat masuk slot (WAJIB: bawaan 0 akan melewati masa tenggang)
    identity: bool = False
    score_bps: Optional[float] = None        # PnL net bps jendela skor; None = belum terukur
    payout: str = ""                         # dompet bagi hasil; WAJIB untuk penerbit luar; payout sama = satu keluarga


@dataclass(frozen=True, kw_only=True)
class Challenger:
    bot_id: str
    issuer: str
    spec_sha: str
    fingerprint: str
    gate_verdict: str                        # keluaran gates.verdict()[0]
    report_sha: str                          # sha laporan peninjau (di-anchor)
    book_sha: str                            # buku yang dipakai peninjau untuk G10; harus sama dengan buku sekarang
    shadow_days: int
    shadow_score_bps: Optional[float]        # PnL net bps selama shadow maju; None = belum terukur
    paired: Dict[str, Tuple[float, float]] = field(default_factory=dict)   # bot_id penghuni -> (selisih bps, t-stat berpasangan, jendela SAMA)
    payout: str = ""


@dataclass(frozen=True)
class Decision:
    action: str                              # ADMIT | REPLACE | BENCH | REJECT
    evict: Optional[str]
    reason: str


# ---------------------------------------------------------------- statistik jendela (tanggal, bukan jumlah baris)

def rolling_score_bps(pnl: Sequence[Tuple[int, float]], window_days: int, end_ms: Optional[int] = None,
                      min_coverage: float = 0.8) -> Optional[float]:
    """Jumlah PnL harian pada `window_days` hari kalender yang berakhir di `end_ms` (bawaan: baris terakhir) x 1e4. None bila tercakup
    kurang dari `min_coverage` hari (bot yang berhenti atau jarang melapor TIDAK mewarisi jendela lama)."""
    if not pnl:
        return None
    end = end_ms if end_ms is not None else pnl[-1][0]
    start = end - window_days * DAY_MS
    vals = [v for t, v in pnl if start < t <= end]
    if len(vals) < min_coverage * window_days or any(not math.isfinite(v) for v in vals):
        return None
    return sum(vals) * 1e4


def paired_stat(ch_pnl: Sequence[Tuple[int, float]], inc_pnl: Sequence[Tuple[int, float]], window_days: int,
                end_ms: int, min_coverage: float = 0.8) -> Optional[Tuple[float, float]]:
    """(selisih bps, t-stat berpasangan) penantang - penghuni pada hari-hari yang SAMA di jendela yang sama; None bila cakupan kurang."""
    a, b = dict(ch_pnl), dict(inc_pnl)
    start = end_ms - window_days * DAY_MS
    d = [a[t] - b[t] for t in sorted(set(a) & set(b)) if start < t <= end_ms and math.isfinite(a[t]) and math.isfinite(b[t])]
    n = len(d)
    if n < min_coverage * window_days or n < 3:
        return None
    m = sum(d) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1))
    if sd <= 1e-12:                                   # selisih (nyaris) konstan: t tak hingga, bukan 9e16 dari galat pembulatan
        t = math.inf if m > 1e-12 else (-math.inf if m < -1e-12 else 0.0)
    else:
        t = m / (sd / math.sqrt(n))
    return m * n * 1e4, t


def win_rate_diag(pnl: Sequence[Tuple[int, float]]) -> Optional[float]:
    """DIAGNOSTIK saja (bukan dasar keputusan): porsi hari berPnL positif di antara hari berPnL tak-nol."""
    nz = [v for _, v in pnl if v != 0.0]
    return None if not nz else sum(1 for v in nz if v > 0) / len(nz)


def killer_triggered(killer: dict, pnl_window: Sequence[float], n_signals: int) -> bool:
    """Penegakan pembunuh terstruktur (`theory.pembunuh`): True bila syaratnya terpenuhi pada PnL harian sejak `window_sinyal` sinyal terakhir.
    Belum cukup sinyal -> False (bukti belum cukup untuk membunuh MAUPUN untuk menyelamatkan)."""
    if n_signals < int(killer["window_sinyal"]) or not pnl_window:
        return False
    vals = list(pnl_window)
    if any(not math.isfinite(v) for v in vals):
        return True                           # data rusak pada bot yang sedang dinilai: gagal tertutup
    metric = killer["metric"]
    if metric == "net_pnl_bps":
        x = sum(vals) * 1e4
    elif metric == "rata_net_per_sinyal_bps":
        x = sum(vals) * 1e4 / max(n_signals, 1)
    elif metric == "mdd_pct":
        x = max_drawdown(vals) * 100.0
    elif metric == "sharpe":
        x = sharpe(vals)
        if math.isnan(x):
            return False
    else:
        raise ValueError(f"metrik pembunuh tak dikenal: {metric}")
    thr = float(killer["threshold"])
    return x < thr if killer["comparator"] == "<" else x <= thr


# ---------------------------------------------------------------- buku

def book_sha(book: Sequence[Entry]) -> str:
    """Sidik jari buku (daftar bot_id + fingerprint terurut): laporan peninjau terikat pada buku ini."""
    return sha0x(sorted([e.bot_id, e.fingerprint] for e in book))


def epoch_id(now_s: int, params: SlotParams) -> int:
    return now_s // (params.epoch_days * DAY_S)


def _tiebreak(fingerprint: str, epoch: int) -> str:
    return sha0x({"fp": fingerprint, "epoch": epoch})


def _valid_issuer(issuer: str) -> bool:
    return issuer == FABIUS or chain.is_checksum_address(issuer)


def _entry_problems(e: Entry) -> List[str]:
    out: List[str] = []
    if not _valid_issuer(e.issuer):
        out.append(f"{e.bot_id}: penerbit bukan FABIUS atau alamat EIP-55")
    if e.issuer != FABIUS and not chain.is_checksum_address(e.payout):
        out.append(f"{e.bot_id}: penerbit luar wajib punya dompet payout EIP-55")
    if e.score_bps is not None and not math.isfinite(e.score_bps):
        out.append(f"{e.bot_id}: skor tidak hingga")
    if not isinstance(e.admitted_s, int) or isinstance(e.admitted_s, bool) or e.admitted_s < 0:
        out.append(f"{e.bot_id}: admitted_s tidak valid")
    return out


def _family_counts(book: Sequence[Entry]) -> Dict[str, int]:
    """Slot per 'keluarga' penerbit luar: penerbit yang berbagi dompet payout (atau alamat yang sama) digabung (union-find)."""
    ext = [e for e in book if e.issuer != FABIUS]
    parent = {e.issuer: e.issuer for e in ext}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    by_payout: Dict[str, str] = {}
    for e in ext:
        if e.payout:
            if e.payout in by_payout:
                parent[find(e.issuer)] = find(by_payout[e.payout])
            else:
                by_payout[e.payout] = e.issuer
    out: Dict[str, int] = {}
    for e in ext:
        r = find(e.issuer)
        out[r] = out.get(r, 0) + 1
    return out


def book_problems(book: Sequence[Entry]) -> List[str]:
    out: List[str] = []
    if len(book) > MAX_SLOTS:
        out.append(f"{len(book)} slot > maksimum {MAX_SLOTS}")
    ids = [e.bot_id for e in book]
    if len(set(ids)) != len(ids):
        out.append("bot_id ganda")
    if len({e.fingerprint for e in book}) != len(book):
        out.append("fingerprint ganda (spesifikasi efektif yang sama dengan nama lain)")
    if book and sum(1 for e in book if e.identity) < MIN_IDENTITY:
        out.append(f"minimal {MIN_IDENTITY} bot identitas Fabius")
    for e in book:
        if e.identity and e.issuer != FABIUS:
            out.append(f"{e.bot_id}: bot identitas harus milik {FABIUS}")
        out += _entry_problems(e)
    for who, n in _family_counts(book).items():
        if n > MAX_PER_ISSUER:
            out.append(f"{who}: {n} slot > {MAX_PER_ISSUER} per penerbit")
    return out


def can_submit(*, family_pending: int, last_rejected_s: Optional[int], now_s: int, params: SlotParams = SlotParams()) -> Tuple[bool, str]:
    """Batas antrean tanpa biaya pengajuan: maksimal pengajuan berjalan per keluarga + masa tunggu setelah penolakan terakhir."""
    if family_pending >= params.queue_max_per_family:
        return False, f"keluarga sudah punya {family_pending} pengajuan berjalan (maks {params.queue_max_per_family})"
    if last_rejected_s is not None and now_s - last_rejected_s < params.cooldown_days * DAY_S:
        return False, f"masa tunggu {params.cooldown_days} hari setelah penolakan terakhir belum selesai"
    return True, "boleh"


def decide(book: Sequence[Entry], ch: Challenger, now_s: int, params: SlotParams = SlotParams(),
           replaced_this_epoch: int = 0) -> Decision:
    prob = book_problems(book)
    if prob:
        raise ValueError("buku slot tidak sah: " + "; ".join(prob))
    if not _valid_issuer(ch.issuer) or (ch.issuer != FABIUS and not chain.is_checksum_address(ch.payout)):
        return Decision(REJECT, None, "penerbit atau dompet payout penantang tidak sah")
    if ch.gate_verdict != "LOLOS_SHADOW":
        return Decision(REJECT, None, f"gerbang tidak lolos ({ch.gate_verdict})")
    if ch.book_sha != book_sha(book):
        return Decision(REJECT, None, "laporan peninjau basi: buku slot berubah sejak peninjauan (G10 bergantung pada petahana); tinjau ulang")
    if ch.bot_id in {e.bot_id for e in book} or ch.fingerprint in {e.fingerprint for e in book} or ch.spec_sha in {e.spec_sha for e in book}:
        return Decision(REJECT, None, "bot atau spesifikasi efektif yang sama sudah ada di buku")
    if ch.issuer != FABIUS:
        probe = list(book) + [Entry(bot_id="~probe", issuer=ch.issuer, spec_sha="~probe", fingerprint="~probe", admitted_s=now_s, payout=ch.payout)]
        if max(_family_counts(probe).values()) > MAX_PER_ISSUER:
            return Decision(REJECT, None, f"penerbit (atau dompet payout yang sama) sudah memegang {MAX_PER_ISSUER} slot")
    if ch.shadow_days < params.shadow_days:
        return Decision(REJECT, None, f"shadow maju baru {ch.shadow_days} hari < {params.shadow_days}")
    if ch.shadow_score_bps is None or not math.isfinite(ch.shadow_score_bps) or not ch.shadow_score_bps > 0:
        return Decision(REJECT, None, "PnL net shadow tidak positif, tidak hingga, atau belum terukur")
    if len(book) < MAX_SLOTS:
        return Decision(ADMIT, None, f"slot kosong ({len(book)}/{MAX_SLOTS}); slot = paper berhak-rendah, BUKAN bukti edge")
    stale_after = (params.grace_days + params.score_window) * DAY_S
    evictable = []
    for e in book:
        age = now_s - e.admitted_s
        if e.identity or age < params.grace_days * DAY_S:
            continue
        if e.score_bps is None and age < stale_after:
            continue                                                  # tak terukur != lemah (sampai masa tenggang + jendela lewat)
        evictable.append(e)
    if not evictable:
        return Decision(BENCH, None, "tidak ada penghuni yang boleh digusur (identitas, masa tenggang, atau belum terukur)")
    if replaced_this_epoch >= params.max_replace_per_epoch:
        return Decision(BENCH, None, "kuota penggantian epoch ini habis")
    ep = epoch_id(now_s, params)
    weakest = min(evictable, key=lambda e: (-math.inf if e.score_bps is None else e.score_bps, _tiebreak(e.fingerprint, ep)))
    if weakest.score_bps is None:                                     # basi/mati: penantang sah mana pun boleh menggantikan
        return Decision(REPLACE, weakest.bot_id, f"{weakest.bot_id} tak terukur sesudah masa tenggang + jendela (basi/mati)")
    stat = ch.paired.get(weakest.bot_id)
    if stat is None or any(math.isnan(x) for x in stat):
        return Decision(BENCH, None, f"statistik berpasangan terhadap {weakest.bot_id} pada jendela yang sama tidak ada")
    gap, tstat = stat
    if gap >= params.margin_bps and tstat >= params.min_gap_tstat:
        return Decision(REPLACE, weakest.bot_id, f"unggul {gap:.0f} bps (t = {tstat:.1f}) atas {weakest.bot_id} pada jendela yang sama")
    return Decision(BENCH, None, f"selisih berpasangan atas {weakest.bot_id} {gap:.0f} bps (t = {tstat:.1f}) < margin {params.margin_bps:.0f} bps / t {params.min_gap_tstat:g}")


def decide_epoch(book: Sequence[Entry], challengers: Sequence[Challenger], now_s: int, params: SlotParams = SlotParams(),
                 replaced_this_epoch: int = 0) -> List[Tuple[Challenger, Decision]]:
    """Semua penantang dinilai SEKALIGUS per epoch (bukan siapa-cepat-dapat). Satu perubahan per epoch: yang bukti-nya terkuat menang (seri: hash),
    sisanya BENCH karena buku berubah (laporan G10 mereka akan basi)."""
    ds = [(ch, decide(book, ch, now_s, params, replaced_this_epoch)) for ch in challengers]
    actionable = [(ch, d) for ch, d in ds if d.action in (ADMIT, REPLACE)]
    if len(actionable) <= 1:
        return ds
    ep = epoch_id(now_s, params)

    def strength(x: Tuple[Challenger, Decision]) -> Tuple[float, str]:
        ch, d = x
        s = ch.paired.get(d.evict, (0.0, 0.0))[1] if d.evict else (ch.shadow_score_bps or 0.0)
        return (-s if math.isfinite(s) else -1e18, _tiebreak(ch.fingerprint, ep))

    winner = min(actionable, key=strength)
    out: List[Tuple[Challenger, Decision]] = []
    for ch, d in ds:
        if d.action in (ADMIT, REPLACE) and ch is not winner[0]:
            out.append((ch, Decision(BENCH, None, "satu perubahan per epoch: penantang lain lebih kuat; tinjau ulang terhadap buku baru")))
        else:
            out.append((ch, d))
    return out


def apply(book: Sequence[Entry], d: Decision, ch: Challenger, now_s: int) -> List[Entry]:
    """Buku baru setelah keputusan (fungsi murni; buku lama tidak diubah)."""
    out = list(book)
    if d.action not in (ADMIT, REPLACE):
        return out
    if d.action == REPLACE:
        victim = next((e for e in out if e.bot_id == d.evict), None)
        if victim is None or victim.identity:
            raise ValueError("penggantian menunjuk bot yang tidak ada atau bot identitas")
        out = [e for e in out if e.bot_id != d.evict]
    out.append(Entry(bot_id=ch.bot_id, issuer=ch.issuer, spec_sha=ch.spec_sha, fingerprint=ch.fingerprint, admitted_s=now_s,
                     identity=False, score_bps=ch.shadow_score_bps, payout=ch.payout))
    problems = book_problems(out)
    if problems:
        raise ValueError("hasil penerapan melanggar invarian: " + "; ".join(problems))
    return out


def remove(book: Sequence[Entry], bot_id: str) -> List[Entry]:
    """Keluarkan bot (mis. oleh pembunuhnya sendiri). Menolak bila itu bot identitas TERAKHIR."""
    target = next((e for e in book if e.bot_id == bot_id), None)
    if target is None:
        raise ValueError(f"{bot_id} tidak ada di buku")
    if target.identity and sum(1 for e in book if e.identity) <= MIN_IDENTITY:
        raise ValueError("bot identitas terakhir tidak boleh keluar: tunjuk bot identitas lain lebih dulu")
    return [e for e in book if e.bot_id != bot_id]


def designate_identity(book: Sequence[Entry], bot_id: str) -> List[Entry]:
    """Tandai bot milik Fabius sebagai identitas (kebal rolling)."""
    target = next((e for e in book if e.bot_id == bot_id), None)
    if target is None:
        raise ValueError(f"{bot_id} tidak ada di buku")
    if target.issuer != FABIUS:
        raise ValueError("hanya bot milik Fabius yang boleh jadi identitas")
    return [replace(e, identity=True) if e.bot_id == bot_id else e for e in book]

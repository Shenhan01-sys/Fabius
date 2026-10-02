"""Ledger paper maju (M2; F-D74/F-D75): catatan append-only, berantai-hash, satu berkas JSONL per bot. Hanya stdlib; tidak menyentuh jaringan.

Empat jenis catatan; dua yang penting punya sifat WAKTU yang berbeda, dan itu disengaja:

  tick    EX-ANTE. Niat posisi (target bobot) pada penutupan satu bar, dihitung dari data sampai bar itu SAJA, dalam <= 12 jam sesudah
          penutupan (guard umur bar). Tidak boleh terlambat: hari yang terlewat dicatat `gap` dan TIDAK diisi belakangan ("tak terukur != bersih").
  settle  EX-POST. Hasil net paper satu bar: dihitung ULANG oleh `replay()` yang sama dengan gerbang (satu jalur kode) dari tick sebelumnya +
          harga dan funding nyata. Boleh terlambat (funding datang belakangan); tidak membuat klaim baru, hanya menutup yang sudah dikomit.
  gap     hari yang terlewat (tak ada tick sebelum batas 12 jam). Statistik maju hanya memakai hari yang kontigu.
  genesis awal rantai: bot, spec_sha, sha kunci ambang dan (bila ada) anchor-nya, bar pertama yang boleh dicatat.

Rantai: tiap catatan memuat `prev` (hash catatan sebelumnya) dan `h` (sha256 JSON kanonik tanpa `h`). Mengubah atau menyisipkan catatan lama
memutus rantai. `verify_against_data` menghitung ulang SETIAP tick (target, data_hash, id sinyal) dan SETIAP settle dari deret bar:
"run menang atas halaman". Semua angka paper maju; BUKAN klaim edge, BUKAN uang nyata.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from typing import Dict, List, Optional, Sequence, Set, Tuple

from .bots import REGISTRY
from .data import MarketData
from .freshness import DEFAULT_MAX_LAG_MS, StaleBars, assert_fresh
from .replay import replay
from .series import DAY_MS
from .sinyal import data_fingerprint, relevant_assets, signals_at
from .spec import SPECS, BotSpec, canon, sha0x
from .target import Target

LEDGER_V = 1
ZERO = "0x" + "00" * 32
TYPES = ("genesis", "tick", "gap", "settle")
MAX_LAG_S = DEFAULT_MAX_LAG_MS // 1000
SETTLE_TOL = 1e-12


class LedgerError(Exception):
    pass


# ---------------------------------------------------------------- waktu

def utc_iso(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso_ms(s: str) -> int:
    return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1000)


def date_of(t_ms: int) -> str:
    return utc_iso(t_ms)[:10]


def last_closed_bar(now_ms: int) -> int:
    """Waktu BUKA bar harian terakhir yang SUDAH tertutup pada `now_ms`."""
    return ((now_ms - DAY_MS) // DAY_MS) * DAY_MS


# ---------------------------------------------------------------- rantai hash + berkas

def record_hash(rec: dict) -> str:
    return sha0x({k: v for k, v in rec.items() if k != "h"})


def seal(rec: dict, prev: str) -> dict:
    out = dict(rec)
    out["v"] = LEDGER_V
    out["prev"] = prev
    out["h"] = record_hash(out)
    return out


def head(records: Sequence[dict]) -> str:
    return records[-1]["h"] if records else ZERO


def load(path: str) -> List[dict]:
    """Baca satu berkas ledger (kosong bila belum ada). Baris tak terbaca = LedgerError (jangan menebak)."""
    if not os.path.exists(path):
        return []
    out: List[dict] = []
    with open(path, "rb") as f:
        for n, raw in enumerate(f, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                out.append(json.loads(raw.decode("utf-8")))
            except (ValueError, UnicodeDecodeError) as e:
                raise LedgerError(f"{os.path.basename(path)} baris {n} tidak terbaca ({type(e).__name__}); rantai berhenti di sini")
    return out


def append(path: str, rec: dict, records: Sequence[dict]) -> dict:
    """Tambahkan SATU catatan yang sudah di-seal ke ujung rantai. Menolak bila `prev` bukan ujung rantai atau hash salah. LF murni."""
    if rec.get("prev") != head(records) or rec.get("h") != record_hash(rec):
        raise LedgerError("catatan tidak menyambung ke ujung rantai atau hash salah")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "ab") as f:
        f.write(canon(rec).encode("utf-8") + b"\n")
        f.flush()
        os.fsync(f.fileno())
    return rec


# ---------------------------------------------------------------- pembuat catatan (murni)

def make_genesis(spec: BotSpec, lock_sha: str, lock_anchor: Optional[dict], first_asof: int, now_ms: int, note: str = "") -> dict:
    """Awal rantai. `first_asof` = bar pertama yang boleh dicatat (waktu buka, ms UTC): jam maju dimulai dari sini."""
    if first_asof % DAY_MS:
        raise ValueError("first_asof harus awal hari UTC")
    return {"type": "genesis", "bot_id": spec.bot_id, "spec_sha": spec.sha(), "lock_sha": lock_sha, "lock_anchor": lock_anchor,
            "first_asof": first_asof, "first_asof_date": date_of(first_asof), "created_utc": utc_iso(now_ms), "note": note}


def bag_of(spec: BotSpec, md: MarketData) -> dict:
    return md.spot if spec.method == "B5-CORE-RWA" else md.perp


def present_assets(spec: BotSpec, md: MarketData, t: int) -> Set[str]:
    """Aset relevan yang punya bar TEPAT pada bar `t` (spot untuk B5, perp lainnya)."""
    bag, out = bag_of(spec, md), set()
    for a in relevant_assets(spec):
        s = bag.get(a)
        if s is None or not len(s):
            continue
        i = s.index_at_or_before(t)
        if i >= 0 and s.t[i] == t:
            out.add(a)
    return out


def compute_tick(spec: BotSpec, md: MarketData, t_asof: int) -> dict:
    """Isi tick pada bar `t_asof` dari data sampai bar itu SAJA. Fungsi murni: dipakai pembuat tick DAN pemeriksa ulang.

    Funding dibuang dari data tick untuk bot yang TARGET-nya tidak memakai funding (semua kecuali B3-CARRY): funding hari lalu bisa datang belakangan
    (zip bulanan), dan data yang datang belakangan tidak boleh mengubah `data_hash` sebuah tick yang sudah dikomit. Funding tetap dipakai oleh `settle`."""
    pit = md.upto(t_asof)
    if spec.method != "B3-CARRY":
        pit = MarketData(perp=pit.perp, spot=pit.spot, funding={}, events=pit.events)
    cur = next((x for x in REGISTRY[spec.method](spec, pit) if x.t == t_asof), None)
    if cur is None:
        raise StaleBars(f"{spec.bot_id}: tidak ada target pada bar {date_of(t_asof)} - data basi atau terpotong")
    sigs = signals_at(spec, pit, t_asof)
    return {"targets": {a: cur.weights[a] for a in sorted(cur.weights)}, "data_hash": data_fingerprint(spec, pit),
            "signal_ids": [s.id() for s in sigs], "n_aset": len(present_assets(spec, pit, t_asof))}


def make_tick(spec: BotSpec, md: MarketData, now_ms: int, genesis: dict) -> dict:
    """Tick untuk bar tertutup terakhir menurut `now_ms`. StaleBars bila data basi/terpotong/aset hilang atau lewat batas 12 jam."""
    if genesis["spec_sha"] != spec.sha():
        raise LedgerError(f"{spec.bot_id}: spesifikasi berubah sejak genesis (pivot = kunci baru): mulai ledger baru, jangan teruskan yang lama")
    t_asof = last_closed_bar(now_ms)
    if t_asof < genesis["first_asof"]:
        raise StaleBars(f"{spec.bot_id}: bar {date_of(t_asof)} sebelum bar pertama yang boleh dicatat ({genesis['first_asof_date']})")
    lag_s = (now_ms - (t_asof + DAY_MS)) // 1000
    if lag_s > MAX_LAG_S:
        raise StaleBars(f"{spec.bot_id}: bar {date_of(t_asof)} sudah {lag_s / 3600:.1f} jam sejak penutupan (> {MAX_LAG_S // 3600} jam): terlambat, bukan tick")
    ref = md.spot.get("BTCUSDT") if spec.method == "B5-CORE-RWA" else md.perp.get("BTCUSDT")
    if ref is None:
        raise StaleBars(f"{spec.bot_id}: seri acuan BTCUSDT tidak ada")
    assert_fresh(f"{spec.bot_id} acuan BTCUSDT", ref.upto(t_asof), now_ms)
    dropped = present_assets(spec, md, t_asof - DAY_MS) - present_assets(spec, md, t_asof)
    if dropped:
        raise StaleBars(f"{spec.bot_id}: aset hilang dari bar {date_of(t_asof)} yang ada sehari sebelumnya: {sorted(dropped)} (feed bolong? universe berubah = bot baru)")
    body = compute_tick(spec, md, t_asof)
    return {"type": "tick", "bot_id": spec.bot_id, "spec_sha": spec.sha(), "asof": t_asof, "asof_date": date_of(t_asof),
            "close_utc": utc_iso(t_asof + DAY_MS), "emitted_utc": utc_iso(now_ms), "lag_s": lag_s, **body}


def make_gap(spec: BotSpec, t_asof: int, reason: str, now_ms: int) -> dict:
    return {"type": "gap", "bot_id": spec.bot_id, "asof": t_asof, "asof_date": date_of(t_asof), "reason": reason[:200], "noted_utc": utc_iso(now_ms)}


# ---------------------------------------------------------------- settle (ex-post, lewat replay yang sama)

def _uses(spec: BotSpec) -> Tuple[bool, bool, bool]:
    """(perlu perp, perlu spot, perlu funding) untuk menutup satu bar bot ini - mengikuti `replay.py`."""
    if spec.method == "B3-CARRY":
        return True, True, True
    if spec.method == "B5-CORE-RWA":
        return False, True, False
    return True, False, True


def settle_pending_reason(spec: BotSpec, md: MarketData, held: Sequence[str], bar: int) -> Optional[str]:
    """None bila SEMUA data untuk menutup bar `bar` ada; selain itu alasan (settle ditunda, bukan diisi nol): tak terukur != bersih."""
    need_perp, need_spot, need_fund = _uses(spec)
    for a in held:
        for need, bag, nm in ((need_perp, md.perp, "perp"), (need_spot, md.spot, "spot")):
            if not need:
                continue
            s = bag.get(a)
            i = s.index_at_or_before(bar) if s is not None and len(s) else -1
            if i < 1 or s.t[i] != bar:
                return f"bar {nm} {a} {date_of(bar)} belum ada"
        if need_fund and bar not in md.funding.get(a, {}):
            return f"funding {a} {date_of(bar)} belum ada"
    return None


def settle_inputs(records: Sequence[dict], bar: int) -> Optional[Tuple[List[Target], List[str]]]:
    """Target-target yang dibutuhkan `replay` untuk menutup bar `bar`: tick sehari sebelumnya (posisi yang dipegang) dan tick dua hari
    sebelumnya (untuk turnover). None bila rantai tidak kontigu (hari bolong): turnover tak terukur, jadi bar itu TIDAK ditutup."""
    ticks = {r["asof"]: r for r in records if r["type"] == "tick"}
    prev, prev2 = ticks.get(bar - DAY_MS), ticks.get(bar - 2 * DAY_MS)
    if prev is None:
        return None
    first = not any(t < prev["asof"] for t in ticks)
    if prev2 is None and not first:
        return None
    bot = prev["bot_id"]
    tg: List[Target] = []
    if prev2 is not None:
        tg.append(Target(bot, prev2["asof"], dict(prev2["targets"])))
    tg.append(Target(bot, prev["asof"], dict(prev["targets"])))
    tg.append(Target(bot, bar, {}))
    return tg, sorted(prev["targets"])


def compute_settle(spec: BotSpec, md: MarketData, records: Sequence[dict], bar: int) -> Optional[dict]:
    """Isi settle bar `bar`; None bila tak bisa ditutup (rantai bolong atau data belum lengkap). Nilai net = `replay()` yang sama dengan gerbang."""
    got = settle_inputs(records, bar)
    if got is None:
        return None
    tg, held = got
    if settle_pending_reason(spec, md, held, bar) is not None:
        return None
    out = replay(spec, md, tg=tg)
    t, net = out[-1]
    if t != bar:
        raise LedgerError(f"replay mengembalikan bar {t}, bukan {bar}")
    w, w_prev = tg[-2].weights, (tg[-3].weights if len(tg) >= 3 else {})
    turn = sum(abs(w.get(a, 0.0) - w_prev.get(a, 0.0)) for a in sorted(set(w) | set(w_prev)))     # urut tetap: deterministik lintas proses
    return {"type": "settle", "bot_id": spec.bot_id, "bar": bar, "bar_date": date_of(bar), "net": net, "turnover": turn,
            "n_held": sum(1 for a in w if abs(w[a]) > 1e-12)}


def settleable_bars(records: Sequence[dict]) -> List[int]:
    """Bar yang SUDAH punya tick sehari sebelumnya tetapi belum punya settle, urut naik."""
    done = {r["bar"] for r in records if r["type"] == "settle"}
    return sorted(r["asof"] + DAY_MS for r in records if r["type"] == "tick" and r["asof"] + DAY_MS not in done)


# ---------------------------------------------------------------- satu putaran harian (murni; pemanggil yang menulis berkas)

def step(spec: BotSpec, md: MarketData, now_ms: int, records: Sequence[dict]) -> Tuple[List[dict], List[str]]:
    """Satu putaran harian pada jam `now_ms`: (1) `gap` untuk hari terlewat yang sudah lewat batas 12 jam; (2) `tick` untuk bar tertutup terakhir
    bila belum ada dan masih dalam batas; (3) `settle` untuk semua bar yang kini bisa ditutup. Mengembalikan (catatan baru yang sudah di-seal
    berantai, catatan untuk manusia). Idempoten: putaran kedua pada jam yang sama tidak menambah apa pun. Tidak menulis berkas."""
    if not records or records[0].get("type") != "genesis":
        raise LedgerError("ledger belum punya genesis")
    g = records[0]
    chain: List[dict] = list(records)
    new: List[dict] = []
    notes: List[str] = []

    def push(rec: dict) -> None:
        sealed = seal(rec, head(chain))
        chain.append(sealed)
        new.append(sealed)

    done = {r["asof"] for r in chain if r["type"] in ("tick", "gap")}
    last_closed = last_closed_bar(now_ms)
    d = max(g["first_asof"], (max(done) + DAY_MS) if done else g["first_asof"])
    while d <= last_closed:
        if d not in done and now_ms > d + DAY_MS + MAX_LAG_S * 1000:
            push(make_gap(spec, d, "tidak ada tick sebelum batas 12 jam", now_ms))
            notes.append(f"gap {date_of(d)}: tidak ada tick sebelum batas 12 jam")
            done.add(d)
        d += DAY_MS
    if last_closed >= g["first_asof"] and last_closed not in done:
        try:
            push(make_tick(spec, md, now_ms, g))
            notes.append(f"tick {date_of(last_closed)}: {len(chain[-1]['targets'])} aset dipegang, {len(chain[-1]['signal_ids'])} sinyal")
        except StaleBars as e:
            notes.append(f"tick {date_of(last_closed)} DITOLAK: {e}")
    for bar in settleable_bars(chain):
        rec = compute_settle(spec, md, chain, bar)
        if rec is not None:
            push(rec)
            notes.append(f"settle {rec['bar_date']}: net {rec['net'] * 1e4:+.1f} bps")
    return new, notes


# ---------------------------------------------------------------- verifikasi

def verify_chain(records: Sequence[dict]) -> List[str]:
    """Masalah struktur rantai (kosong = sah): urutan, hash, genesis tunggal, tick monoton, batas 12 jam, settle bertumpu pada tick."""
    p: List[str] = []
    if not records:
        return ["ledger kosong"]
    g = records[0]
    if g.get("type") != "genesis" or g.get("prev") != ZERO:
        p.append("catatan pertama bukan genesis dengan prev nol")
    prev, bot = ZERO, g.get("bot_id")
    seen_tick: Dict[int, str] = {}
    last_asof, last_bar, n_gen = None, None, 0
    for i, r in enumerate(records):
        tag = f"#{i} {r.get('type')}"
        if r.get("v") != LEDGER_V:
            p.append(f"{tag}: versi {r.get('v')} bukan {LEDGER_V}")
        if r.get("type") not in TYPES:
            p.append(f"{tag}: jenis tak dikenal")
            continue
        if r.get("bot_id") != bot:
            p.append(f"{tag}: bot_id {r.get('bot_id')} != {bot}")
        if r.get("prev") != prev:
            p.append(f"{tag}: prev tidak menyambung (rantai putus atau catatan disisipkan)")
        if r.get("h") != record_hash(r):
            p.append(f"{tag}: hash tidak cocok (isi diubah)")
        prev = r.get("h", "?")
        t = r["type"]
        if t == "genesis":
            n_gen += 1
            if i != 0:
                p.append(f"{tag}: genesis ganda")
        elif t in ("tick", "gap"):
            a = r.get("asof")
            if not isinstance(a, int) or a % DAY_MS:
                p.append(f"{tag}: asof bukan awal hari UTC")
                continue
            if a < g.get("first_asof", 0):
                p.append(f"{tag}: asof {date_of(a)} sebelum first_asof genesis")
            if last_asof is not None and a <= last_asof:
                p.append(f"{tag}: asof {date_of(a)} tidak naik ketat (duplikat atau mundur)")
            last_asof = a if last_asof is None else max(last_asof, a)
            seen_tick[a] = t
            if t == "tick":
                if r.get("spec_sha") != g.get("spec_sha"):
                    p.append(f"{tag}: spec_sha berbeda dari genesis (pivot = ledger baru)")
                lag = r.get("lag_s")
                if not isinstance(lag, int) or lag < 0 or lag > MAX_LAG_S:
                    p.append(f"{tag}: lag_s {lag} di luar 0..{MAX_LAG_S} (tick terlambat tidak sah)")
                try:
                    if (iso_ms(r["emitted_utc"]) - (a + DAY_MS)) // 1000 != lag:
                        p.append(f"{tag}: lag_s tidak sama dengan emitted_utc - close")
                except (KeyError, ValueError):
                    p.append(f"{tag}: emitted_utc tidak terbaca")
        elif t == "settle":
            b = r.get("bar")
            if not isinstance(b, int) or b % DAY_MS:
                p.append(f"{tag}: bar bukan awal hari UTC")
                continue
            if last_bar is not None and b <= last_bar:
                p.append(f"{tag}: bar {date_of(b)} tidak naik ketat")
            last_bar = b if last_bar is None else max(last_bar, b)
            if seen_tick.get(b - DAY_MS) != "tick":
                p.append(f"{tag}: settle bar {date_of(b)} tanpa tick sehari sebelumnya")
    if n_gen != 1:
        p.append(f"jumlah genesis {n_gen}, harus 1")
    return p


def verify_against_data(spec: BotSpec, records: Sequence[dict], md: MarketData) -> List[str]:
    """Hitung ULANG setiap tick (target, data_hash, id sinyal) dari deret bar dan setiap settle dari replay. Beda = bar diubah atau ledger dipalsukan."""
    p: List[str] = []
    if not records or records[0].get("spec_sha") != spec.sha():
        p.append("spec_sha genesis tidak sama dengan spesifikasi kode sekarang (bot berubah?)")
        return p
    for i, r in enumerate(records):
        if r["type"] == "tick":
            try:
                want = compute_tick(spec, md, r["asof"])
            except StaleBars as e:
                p.append(f"#{i} tick {r['asof_date']}: tak bisa dihitung ulang dari bar ({e})")
                continue
            for k in ("targets", "data_hash", "signal_ids", "n_aset"):
                if r.get(k) != want[k]:
                    p.append(f"#{i} tick {r['asof_date']}: {k} BEDA dari hitung-ulang")
        elif r["type"] == "settle":
            want = compute_settle(spec, md, records[:i], r["bar"])
            if want is None:
                p.append(f"#{i} settle {r['bar_date']}: tak bisa dihitung ulang (data bar/funding atau tick pendukung hilang)")
                continue
            # `replay()` menjumlahkan lewat himpunan Python (urutan bergantung benih hash per proses), jadi `net` bisa beda di bit terakhir antar
            # proses: dibandingkan dengan toleransi mutlak 1e-12 (1e-8 bps). Turnover dan n_held dihitung dengan urutan tetap: persis.
            if not isinstance(r.get("net"), (int, float)) or abs(r["net"] - want["net"]) > SETTLE_TOL:
                p.append(f"#{i} settle {r['bar_date']}: net {r.get('net')} != hitung-ulang {want['net']}")
            for k in ("turnover", "n_held"):
                if r.get(k) != want[k]:
                    p.append(f"#{i} settle {r['bar_date']}: {k} {r.get(k)} != hitung-ulang {want[k]}")
    return p


# ---------------------------------------------------------------- ringkasan (untuk laporan)

def render_report(records: Sequence[dict]) -> str:
    """Laporan manusia untuk satu ledger. Semua angka dicetak ulang dari catatan; jendela pendek diberi peringatan, bukan klaim."""
    from .report import fmt, summary
    if not records:
        return "ledger kosong"
    st = stats(records)
    g = records[0]
    anc = g.get("lock_anchor") or {}
    lines = [f"LEDGER {g['bot_id']}  spec {g['spec_sha'][:12]}…  kunci {g['lock_sha'][:12]}…  "
             f"{'ter-anchor tx ' + str(anc.get('tx', '?'))[:12] + '… @ ' + str(anc.get('anchoredAt_utc', '?')) if anc else 'kunci TIDAK ter-anchor'}",
             f"jam maju dimulai di bar {g['first_asof_date']} (dibuat {g['created_utc']}); tick terakhir {st['last_tick'] or '-'}; ujung rantai {st['head'][:14]}…",
             f"tick {st['n_tick']} | gap {st['n_gap']} | settle {st['n_settle']} | menunggu penutupan {st['n_unsettled']} | sinyal maju {st['n_signals']}"]
    lags = sorted(r["lag_s"] for r in records if r["type"] == "tick" and isinstance(r.get("lag_s"), int))
    if lags:
        lines.append(f"jeda tick terhadap penutupan bar: median {lags[len(lags) // 2] / 3600:.1f} j, maks {lags[-1] / 3600:.1f} j (guard {MAX_LAG_S // 3600} j); "
                     "settle mengandaikan masuk di harga penutupan, pengikut baru bisa masuk sesudah jeda ini")
    pnl = st["pnl"]
    if len(pnl) >= 2:
        lines.append("kinerja maju (net paper, hari kontigu yang ditutup): " + fmt(summary(pnl)))
    else:
        lines.append("kinerja maju: belum cukup hari ditutup (n < 2)")
    warn = []
    if st["n_signals"] < 20:
        warn.append(f"sinyal maju {st['n_signals']} < 20 (F-D16)")
    if st["n_settle"] < 90:
        warn.append(f"hanya {st['n_settle']} hari ditutup: Sharpe/MDD pada jendela ini tidak bermakna")
    if st["n_gap"]:
        warn.append(f"{st['n_gap']} hari bolong dihitung tak terukur, bukan nol")
    if warn:
        lines.append("PERINGATAN: " + "; ".join(warn) + ". Paper maju, BUKAN klaim edge, BUKAN uang nyata.")
    return "\n".join(lines)


def stats(records: Sequence[dict]) -> dict:
    ticks = [r for r in records if r["type"] == "tick"]
    gaps = [r for r in records if r["type"] == "gap"]
    settles = [r for r in records if r["type"] == "settle"]
    unsettled = settleable_bars(records)
    return {"genesis": records[0] if records else None, "n_tick": len(ticks), "n_gap": len(gaps), "n_settle": len(settles),
            "n_unsettled": len(unsettled), "n_signals": sum(len(t.get("signal_ids", [])) for t in ticks),
            "pnl": [(r["bar"], r["net"]) for r in settles], "head": head(records),
            "last_tick": ticks[-1]["asof_date"] if ticks else None}

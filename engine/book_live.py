"""Buku slot HIDUP (P87, F-D85): satu berkas append-only berantai hash (`ledger/book/buku.jsonl`), satu catatan `epoch` per epoch `SlotParams.epoch_days`.

Tiap catatan epoch memuat SEMUA masukan keputusan - skor maju penghuni (P85), bahan penantang (shadow + berpasangan + vonis gerbang + `report_sha`),
status pembunuh - lalu keputusan `slots.decide_epoch`, buku hasil, dan `book_sha`. Pemeriksa menghitung ULANG keputusan dari masukan yang tercatat
(tanpa data pasar, tanpa jaringan); vonis gerbang dibuktikan terpisah lewat laporan ber-sha di `ledger/book/laporan/`.

Pembagian kerja: fungsi murni di sini (susun, segel, verifikasi); `engine.cli book epoch` memuat ledger maju yang SAH, menjalankan gerbang penantang
(petahana = buku sekarang) dan menulis (penulis tunggal); `tools/pin_book.py` mem-pin `book_sha` tiap epoch ke LockRegistry.

Batas yang dikatakan terus terang: pembunuh bot Fabius berupa TEKS di spesifikasi (mengubahnya = spesifikasi baru); yang ditegakkan otomatis di sini
hanya pembunuh TERSTRUKTUR (bentuk `slots.killer_triggered`, penerbit luar). Bot dengan pembunuh teks dicatat "TEKS (dinilai manusia)" sampai ada
versi terstruktur yang dikunci (P107).
"""
from __future__ import annotations

import dataclasses
from typing import Dict, List, Optional, Sequence, Tuple

from . import ledger, slots
from .slots import Challenger, Entry, SlotParams

BOOK_V = 1


def entry_to(e: Entry) -> dict:
    return dataclasses.asdict(e)


def entry_from(d: dict) -> Entry:
    return Entry(**d)


def challenger_to(c: Challenger) -> dict:
    d = dataclasses.asdict(c)
    d["paired"] = {k: list(v) for k, v in sorted(c.paired.items())}
    return d


def challenger_from(d: dict) -> Challenger:
    d = dict(d)
    d["paired"] = {k: tuple(v) for k, v in (d.get("paired") or {}).items()}
    return Challenger(**d)


def make_genesis(book: Sequence[Entry], lock_sha: str, now_s: int, note: str) -> dict:
    return {"type": "genesis", "v_buku": BOOK_V, "buku": [entry_to(e) for e in book], "book_sha": slots.book_sha(book), "kunci_v1": lock_sha,
            "dibuat_utc": ledger.utc_iso(now_s * 1000), "catatan": note}


def current_book(records: Sequence[dict]) -> List[Entry]:
    return [entry_from(d) for d in records[-1]["buku"]]


def build_epoch(prev_book: Sequence[Entry], now_s: int, end_bar_ms: int, scores: Dict[str, Optional[float]], challengers: Sequence[Challenger],
                killers: Dict[str, str], params: SlotParams = SlotParams()) -> dict:
    """Satu epoch, murni. `killers[bot]` = 'TEKS' | 'TIDAK' | 'YA' (YA = pembunuh terstruktur terpicu; dihitung pemanggil dari ledger maju)."""
    book = [dataclasses.replace(e, score_bps=scores.get(e.bot_id)) for e in prev_book]
    removed: List[str] = []
    for e in list(book):
        if killers.get(e.bot_id) == "YA":
            try:
                book = slots.remove(book, e.bot_id)
                removed.append(e.bot_id)
            except ValueError:
                pass                                              # identitas terakhir: tetap, dan tercatat di status pembunuh
    decisions = slots.decide_epoch(book, list(challengers), now_s, params, 0) if challengers else []
    for ch, d in decisions:
        if d.action in (slots.ADMIT, slots.REPLACE):
            book = slots.apply(book, d, ch, now_s)
    return {"type": "epoch", "v_buku": BOOK_V, "epoch": slots.epoch_id(now_s, params), "now_s": now_s, "now_utc": ledger.utc_iso(now_s * 1000),
            "ujung_bar": end_bar_ms, "ujung_bar_tgl": ledger.date_of(end_bar_ms), "penghuni": [entry_to(e) for e in prev_book], "skor": dict(sorted(scores.items())),
            "pembunuh": dict(sorted(killers.items())), "dikeluarkan": removed, "penantang": [challenger_to(c) for c in challengers],
            "keputusan": [[ch.bot_id, d.action, d.evict, d.reason] for ch, d in decisions], "buku": [entry_to(e) for e in book],
            "book_sha": slots.book_sha(book)}


def verify_book(records: Sequence[dict], params: SlotParams = SlotParams()) -> List[str]:
    """Masalah (kosong = sah): rantai hash, genesis tunggal di depan, epoch naik, kesinambungan buku, dan keputusan tiap epoch DIHITUNG ULANG dari
    masukannya sendiri (skor, pembunuh, penantang) harus sama persis dengan yang tercatat."""
    p: List[str] = []
    if not records:
        return ["buku kosong"]
    prev = ledger.ZERO
    for i, r in enumerate(records):
        if r.get("prev") != prev or r.get("h") != ledger.record_hash(r):
            p.append(f"#{i}: rantai hash putus")
        prev = r.get("h")
    if records[0].get("type") != "genesis":
        p.append("catatan pertama bukan genesis")
    last_epoch = None
    for i in range(1, len(records)):
        r, before = records[i], records[i - 1]
        if r.get("type") != "epoch":
            p.append(f"#{i}: jenis {r.get('type')} tidak dikenal")
            continue
        kurang = [k for k in ("epoch", "now_s", "ujung_bar", "penghuni", "skor", "penantang", "pembunuh") if k not in r]
        if kurang:                                                    # P161: catatan rusak dilaporkan, pemeriksa tidak berhenti dengan galat
            p.append(f"#{i}: catatan epoch tidak lengkap ({', '.join(kurang)})")
            continue
        if last_epoch is not None and r["epoch"] <= last_epoch:
            p.append(f"#{i}: epoch {r['epoch']} tidak naik")
        last_epoch = r["epoch"]
        if r["penghuni"] != before["buku"]:
            p.append(f"#{i}: penghuni epoch tidak sama dengan buku catatan sebelumnya")
        want = build_epoch([entry_from(d) for d in r["penghuni"]], r["now_s"], r["ujung_bar"], r["skor"],
                           [challenger_from(d) for d in r["penantang"]], r["pembunuh"], params)
        for k in ("epoch", "dikeluarkan", "keputusan", "buku", "book_sha"):
            if want[k] != r.get(k):
                p.append(f"#{i} epoch {r.get('epoch')}: {k} BEDA dari hitung-ulang")
    return p


def append(path: str, rec: dict, records: Sequence[dict]) -> dict:
    sealed = ledger.seal(rec, ledger.head(records))
    ledger.append(path, sealed, records)
    return sealed


def fmt_epoch(r: dict) -> str:
    lines = [f"EPOCH {r['epoch']} ({r['now_utc']}; ujung bar {r['ujung_bar_tgl']}) | book_sha {r['book_sha'][:18]}…"]
    for e in r["buku"]:
        s = r["skor"].get(e["bot_id"])
        lines.append(f"  penghuni {e['bot_id']:12s} identitas={e['identity']} skor {'-' if s is None else f'{s:+.1f}'} bps | pembunuh {r['pembunuh'].get(e['bot_id'], '-')}")
    for c, (bot, act, ev, why) in zip(r["penantang"], r["keputusan"]):
        lines.append(f"  penantang {bot:12s} gerbang {c['gate_verdict']} | shadow {c['shadow_days']} hari, net {c['shadow_score_bps']} bps | "
                     f"-> {act}{' menggantikan ' + ev if ev else ''}: {why}")
    if not r["penantang"]:
        lines.append("  tidak ada penantang")
    for d in r.get("dilewati") or []:                          # P161: berhak menantang tetapi dilewati (ledger maju / peninjau LLM)
        lines.append(f"  dilewati  {d['bot']:12s} {d['alasan']}")
    if r["dikeluarkan"]:
        lines.append(f"  DIKELUARKAN oleh pembunuhnya: {r['dikeluarkan']}")
    return "\n".join(lines)

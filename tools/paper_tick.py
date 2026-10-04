"""Putaran harian ledger paper (M2; F-D74/F-D75): (opsional) perbarui bar dari jaringan -> tick/gap/settle per bot -> tulis ledger -> laporan.

Ledger = `ledger/paper/<bot>.jsonl` (append-only, berantai-hash); bar yang dipakai = `ledger/bars/*.csv` (ikut di-commit, jadi siapa pun bisa menghitung
ulang setiap tick: `python -X utf8 -m engine.cli ledger verify`). Paper penuh: tidak ada uang nyata, tidak ada kunci, tidak ada transaksi chain.
Satu-satunya jaringan: `tools/feed_bars.py` (kline harian + funding publik) bila `--feed`.

Pakai:  python -X utf8 tools/paper_tick.py --init --bots B1-TREND      # SEKALI per bot: genesis (menautkan kunci ambang + anchor-nya); jam maju dimulai
        python -X utf8 tools/paper_tick.py --feed                      # harian: bar -> tick/gap/settle -> laporan (semua bot yang punya genesis)
        python -X utf8 tools/paper_tick.py --dry-run [--now 2026-10-03T03:00:00Z]    # hitung dan cetak, tanpa menulis apa pun

Kode keluar: 0 beres; 3 rantai/bot bermasalah (TIDAK menulis apa pun untuk bot itu); 4 tick belum bisa dibuat (data basi/bolong, masih dalam batas 12 jam:
jalankan lagi nanti; lewat batas = `gap`).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from engine import book as bookmod, ledger, locks      # noqa: E402
from engine.data import load_csv_dir                   # noqa: E402
from engine.series import DAY_MS                       # noqa: E402
from engine.spec import PERP_UNIVERSE, SPECS           # noqa: E402

DATA_SYMBOLS = list(PERP_UNIVERSE) + ["PAXGUSDT", "XAUUSDT"]
ANCHORS_DIR = os.path.join(locks.LOCK_DIR, "anchors")


class Views:
    """Pandangan data per `funding_view` (F-D76), dimuat sekali dan malas: actual (settle final, verifikasi), targets (target B3: estimasi beku),
    provisional (laporan PROVISIONAL)."""

    def __init__(self, bars_dir: str):
        self.bars_dir = bars_dir
        self._cache = {}

    def get(self, view: str):
        if view not in self._cache:
            self._cache[view] = load_csv_dir(self.bars_dir, DATA_SYMBOLS, funding_view=view)
        return self._cache[view]


def anchor_info(lock: dict):
    """Catatan anchor kunci (ditulis `tools/anchor_lock.py --send`), atau None bila kunci belum ter-anchor."""
    p = os.path.join(ANCHORS_DIR, f"{lock['sha'][2:14]}.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        r = json.load(f)
    if r.get("lock_sha") != lock["sha"]:
        return None
    return {k: r.get(k) for k in ("id", "tx", "block", "anchoredAt", "anchoredAt_utc", "contract", "chainId", "asset")}


def init_bot(bot: str, ledger_dir: str, now_ms: int, dry: bool) -> int:
    if bot not in SPECS:
        print(f"{bot}: bot tidak dikenal")
        return 3
    if bot not in bookmod.FORWARD_BOTS:                     # F-D95: semua bot Fabius; bot luar (penerbit) tetap lewat gerbang -> bayangan -> slot
        print(f"{bot}: DITOLAK - bukan bot yang boleh punya jam maju (boleh: {', '.join(bookmod.FORWARD_BOTS)}). "
              "Bot luar lewat gerbang -> shadow -> slot seperti penerbit (engine/book.py).")
        return 3
    path = os.path.join(ledger_dir, f"{bot}.jsonl")
    if os.path.exists(path):
        print(f"{bot}: ledger sudah ada ({os.path.relpath(path, ROOT)}); --init hanya sekali per bot (pivot = ledger baru, bukan timpa)")
        return 3
    st = locks.status()
    if st["state"] != "TERKUNCI":
        print(f"{bot}: DITOLAK - kunci ambang {st['state']} (jam maju hanya dimulai di bawah kunci yang cocok dengan kode)")
        return 3
    with open(locks.LOCK_FILE, encoding="utf-8") as f:
        lock = json.load(f)
    anc = anchor_info(lock)
    last = ledger.last_closed_bar(now_ms)
    lag_s = (now_ms - (last + DAY_MS)) // 1000
    first = last if lag_s <= ledger.MAX_LAG_S else last + DAY_MS
    g = ledger.make_genesis(SPECS[bot], lock["sha"], anc, first, now_ms,
                            "ledger paper maju; kunci ambang v1 (sementara); paper penuh, bukan uang nyata, bukan klaim edge")
    sealed = ledger.seal(g, ledger.ZERO)
    print(f"{bot}: genesis bar pertama {g['first_asof_date']}  spec {g['spec_sha'][:14]}…  kunci {g['lock_sha'][:14]}…  "
          f"{'ter-anchor ' + str(anc['tx'])[:14] + '… @ ' + str(anc['anchoredAt_utc']) if anc else 'kunci TIDAK ter-anchor'}")
    if not dry:
        ledger.append(path, sealed, [])
        print(f"  ditulis: {os.path.relpath(path, ROOT)}")
    return 0


def tick_bot(bot: str, ledger_dir: str, views: "Views", now_ms: int, dry: bool) -> int:
    path = os.path.join(ledger_dir, f"{bot}.jsonl")
    try:
        records = ledger.load(path)
    except ledger.LedgerError as e:
        print(f"{bot}: RUSAK - {e}. Tidak menulis apa pun.")
        return 3
    if not records:
        print(f"{bot}: belum ada ledger; jalankan --init --bots {bot} dulu")
        return 3
    problems = ledger.verify_chain(records)
    if problems:
        print(f"{bot}: rantai TIDAK sah - tidak menulis apa pun:")
        for p in problems[:10]:
            print("  -", p)
        return 3
    spec = SPECS.get(bot)
    if spec is None or records[0].get("spec_sha") != spec.sha():
        print(f"{bot}: spesifikasi di kode tidak sama dengan genesis (pivot = ledger baru). Tidak menulis apa pun.")
        return 3
    md_tick = views.get("targets" if spec.method == "B3-CARRY" else "actual")      # B3: target memakai funding -> estimasi beku bila aktual belum terbit
    new, notes = ledger.step(spec, md_tick, now_ms, records, views.get("actual"))         # settle FINAL selalu dari funding aktual
    for n in notes:
        print(f"{bot}: {n}")
    chain = list(records)
    for rec in new:
        if not dry:
            ledger.append(path, rec, chain)
        chain.append(rec)
    if not new:
        print(f"{bot}: tidak ada catatan baru")
    print(ledger.render_report(chain, ledger.provisional_settles(spec, views.get("provisional"), chain)))
    last_closed = ledger.last_closed_bar(now_ms)
    done = {r["asof"] for r in chain if r["type"] in ("tick", "gap")}
    pending = last_closed >= chain[0]["first_asof"] and last_closed not in done
    return 4 if pending else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Putaran harian ledger paper (tick/gap/settle).")
    ap.add_argument("--ledger", default=os.path.join(ROOT, "ledger", "paper"))
    ap.add_argument("--bars", default=os.path.join(ROOT, "ledger", "bars"))
    ap.add_argument("--bots", help="daftar bot dipisah koma; bawaan: semua berkas ledger yang ada")
    ap.add_argument("--init", action="store_true", help="tulis genesis (sekali per bot) - memulai jam maju")
    ap.add_argument("--feed", action="store_true", help="perbarui bar dari jaringan (tools/feed_bars.py) sebelum tick")
    ap.add_argument("--spot", action="store_true", help="bersama --feed: juga kline spot (B3/B5)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--now", help="ISO UTC mengganti jam sekarang (uji / simulasi)")
    a = ap.parse_args()
    now_ms = ledger.iso_ms(a.now) if a.now else int(time.time() * 1000)
    bots = [b.strip() for b in a.bots.split(",") if b.strip()] if a.bots else sorted(os.path.basename(f)[:-6] for f in glob.glob(os.path.join(a.ledger, "*.jsonl")))
    if not bots:
        print("tidak ada bot: beri --bots <id> (dan --init sekali) atau buat ledger dulu")
        return 3
    if a.init:
        return max([init_bot(b, a.ledger, now_ms, a.dry_run) for b in bots] or [3])
    if a.feed:
        import feed_bars
        today = feed_bars.day_start(now_ms)
        need_spot = a.spot or any(SPECS[b].method in ("B3-CARRY", "B5-CORE-RWA") for b in bots if b in SPECS)    # B3 = long spot + short perp
        reps = feed_bars.update_all(a.bars, list(PERP_UNIVERSE), today, spot=need_spot, funding=True, dry_run=a.dry_run)
        # P128 (F-D95): emas spot untuk B5-CORE-RWA (kandidat yang berkasnya sudah ditanam `tools/seed_bars.py`; perpanjang saja, tidak menanam)
        if any(SPECS[b].method == "B5-CORE-RWA" for b in bots if b in SPECS):
            for g in SPECS["B5-CORE-RWA"].konstanta["emas_kandidat"]:
                if os.path.exists(os.path.join(a.bars, f"spot_{g}_1d.csv")):
                    reps.append(feed_bars.update_klines(a.bars, "spot", g, today, dry_run=a.dry_run))
        stuck = [r for r in reps if r["stop"]]
        print(f"feed: +{sum(r['added'] for r in reps)} baris; {len(stuck)} deret berhenti sebelum hari ini")
        for r in stuck[:6]:
            print(f"  ! {r['kind']} {r['sym']}: {r['stop']}")
        for n in sorted({r["note"] for r in reps if r.get("note")})[:2]:
            print(f"  i {n}")
    views = Views(a.bars)
    rc = 0
    for b in bots:
        rc = max(rc, tick_bot(b, a.ledger, views, now_ms, a.dry_run))
        print()
    return rc


if __name__ == "__main__":
    sys.exit(main())

"""P167c: jam maju harian bot `feed` (dipanggil rantai `paper-ledger` sesudah `paper_tick.py`; gagal di sini tidak menghentikan rantai ledger).

Untuk tiap bot feed yang tercatat di registri (vonis MAJU_FEED, `engine/terdaftar.py::feed_rincian`):
  1. ambil komit publik dari gerbang (`GET /bots/feed/<bot>`; hanya bar yang sudah dibuka memuat bobot + tanda tangan + bukti + anchor);
  2. salinan publik -> `ledger/feed/komit/<bot>.json` (siapa pun bisa memeriksa ulang tiap komit: tanda tangan, bukti Merkle, `lockedAt` on-chain);
  3. genesis otomatis sekali (`ledger/feed/<bot>.jsonl`), lalu `engine/feed.py::step`: komit sah + ter-anchor sebelum penutupan -> tick; tidak ada /
     tidak sah -> gap (UNGKAPKAN); gerbang atau RPC tidak terbaca -> TUNDA (lewat 12 jam = gap); settle lewat `replay` yang sama.
`lockedAt` dibaca ULANG dari LockRegistry chain 97 (alamat gerbang = `deployments/97.json` x402_sinyal.facilitator), bukan dipercaya dari gerbang.

Pakai:  python -X utf8 tools/feed_tick.py [--dry-run] [--now ISO] [--gerbang URL]
        python -X utf8 tools/feed_tick.py --verify              # periksa ulang semua ledger feed dari salinan komit publik + chain
Kode keluar: 0 beres / tidak ada bot feed; 3 rantai rusak; 4 TUNDA (gerbang / RPC tidak terbaca, coba lagi).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from typing import Callable, Dict, List, Optional

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [ROOT, HERE]

from engine import chain, feed as F, ledger, locks, terdaftar          # noqa: E402

GERBANG = "https://fabius-x402-production.up.railway.app"
CHAIN_ID = 97


def ambil(gerbang: str, bot: str) -> List[dict]:
    req = urllib.request.Request(f"{gerbang}/bots/feed/{bot}", headers={"User-Agent": "fabius-feed-tick"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())["komit"]


def pembaca_chain(root: str = ROOT):
    """(locked_at(locker, akar) dari LockRegistry chain 97, alamat gerbang yang sah). Galat RPC dilempar (TUNDA), tidak dibaca sebagai 0."""
    import evm as evmmod
    import signal_commit as sc
    cfg = json.load(open(os.path.join(root, "deployments", "97.json"), encoding="utf-8"))
    reg = cfg["contracts"]["LockRegistry"]
    gate = (cfg.get("x402_sinyal") or {}).get("facilitator")
    ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)

    def baca(locker: str, akar: str) -> int:
        return int(ev.call_decode(reg, sc.SIG_LOCKED_AT, ("address", "bytes32", "bytes32"),
                                  (locker, chain.ascii32(F.LABEL_ANCHOR), chain.from_hex(akar)), ("uint64",))[0])
    return baca, gate


def _tulis_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def tick(bots: Dict[str, dict], ledger_dir: str, md, now_ms: int, ambil_fn: Callable[[str], List[dict]],
         locked_at: Optional[Callable[[str, str], int]], locker: Optional[str], dry: bool, log: Callable[[str], None] = print) -> int:
    rc = 0
    for bot in sorted(bots):
        x = bots[bot]
        spec = x["spec"]
        path = os.path.join(ledger_dir, f"{bot}.jsonl")
        try:
            records = ledger.load(path)
        except ledger.LedgerError as e:
            log(f"{bot}: RUSAK - {e}. Tidak menulis apa pun.")
            rc = max(rc, 3)
            continue
        if records and ledger.verify_chain(records):
            log(f"{bot}: rantai feed TIDAK sah - tidak menulis apa pun: {ledger.verify_chain(records)[0]}")
            rc = max(rc, 3)
            continue
        if not records:
            last = ledger.last_closed_bar(now_ms)
            lag_s = (now_ms - (last + ledger.DAY_MS)) // 1000
            first = last if lag_s <= ledger.MAX_LAG_S else last + ledger.DAY_MS
            st = locks.status()
            g = ledger.make_genesis(spec, st["sha_kunci"] or ledger.ZERO, None, first, now_ms,
                                    f"ledger feed maju (P167c): bayangan {F.BAYANGAN_HARI} hari, TANPA slot sampai terbukti; label: {F.LABEL_KEPERCAYAAN}")
            records = [ledger.seal(g, ledger.ZERO)]
            log(f"{bot}: genesis feed bar pertama {g['first_asof_date']}")
            if not dry:
                ledger.append(path, records[0], [])
        try:
            komits: Optional[List[dict]] = ambil_fn(bot)
        except Exception as e:                                                  # noqa: BLE001 - gerbang mati != tidak ada komit
            log(f"{bot}: daftar komit tidak terbaca ({type(e).__name__}) - TUNDA")
            komits = None
        if komits is not None and not dry:
            _tulis_json(os.path.join(ledger_dir, "komit", f"{bot}.json"), [k for k in komits if "bobot" in k])
        try:
            new, notes = F.step(spec, md, now_ms, records, komits, x["issuer"], x["spec_sha"], CHAIN_ID, locked_at, locker)
        except Exception as e:                                                  # noqa: BLE001 - RPC lockedAt gagal = TUNDA, bukan gap
            log(f"{bot}: TUNDA - {type(e).__name__}: {str(e)[:160]}")
            rc = max(rc, 4)
            continue
        for n in notes:
            log(f"{bot}: {n}")
        chain_ = list(records)
        for rec in new:
            if not dry:
                ledger.append(path, rec, chain_)
            chain_.append(rec)
        if komits is None:
            rc = max(rc, 4)
        log(ledger.render_report(chain_) + f"\nLABEL: {F.LABEL_KEPERCAYAAN}; bayangan {F.BAYANGAN_HARI} hari; tanpa slot sampai terbukti")
    return rc


def verifikasi(bots: Dict[str, dict], ledger_dir: str, md, locked_at, locker, log: Callable[[str], None] = print) -> int:
    rc = 0
    for bot in sorted(bots):
        path = os.path.join(ledger_dir, f"{bot}.jsonl")
        if not os.path.exists(path):
            continue
        kp = os.path.join(ledger_dir, "komit", f"{bot}.json")
        komits = json.load(open(kp, encoding="utf-8")) if os.path.exists(kp) else []
        x = bots[bot]
        p = F.verify(x["spec"], ledger.load(path), md, komits, x["issuer"], x["spec_sha"], CHAIN_ID, locked_at, locker)
        log(f"{bot}: {'SAH' if not p else 'TIDAK SAH - ' + p[0]}")
        rc = max(rc, 0 if not p else 1)
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gerbang", default=os.environ.get("X402_PUBLIC_URL") or GERBANG)
    ap.add_argument("--ledger", default=os.path.join(ROOT, "ledger", "feed"))
    ap.add_argument("--bars", default=os.path.join(ROOT, "ledger", "bars"))
    ap.add_argument("--now")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    bots, masalah = terdaftar.feed_rincian(ROOT)
    for m in masalah:
        print(f"  ! bot feed: {m}")
    if not bots:
        print("tidak ada bot feed terdaftar (MAJU_FEED) - tidak ada yang dikerjakan")
        return 0
    from engine.data import load_csv_dir
    from paper_tick import DATA_SYMBOLS
    md = load_csv_dir(a.bars, DATA_SYMBOLS, funding_view="actual")
    baca, gate = pembaca_chain()
    if a.verify:
        return verifikasi(bots, a.ledger, md, baca, gate)
    now_ms = ledger.iso_ms(a.now) if a.now else int(time.time() * 1000)
    return tick(bots, a.ledger, md, now_ms, lambda b: ambil(a.gerbang, b), baca, gate, a.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())

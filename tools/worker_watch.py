"""Penjaga LUAR worker Railway (P111; T8 SK-R5): worker yang mati tidak bisa mengirim alert tentang dirinya sendiri, jadi pemeriksanya harus tinggal
di tempat lain. Alat ini dijalankan rantai GitHub `paper-ledger.yml` (penulis ledger) sesudah tick hari itu beres. Ia membaca chain 97 tanpa kunci:
tick resmi terakhir tiap bot sudah dikomit ke SignalAnchor, dan isinya sudah diungkap?

  OK             komit ada dan semua sinyal terungkap (atau ungkap masih dalam tenggang)
  SEBELUM KUNCI  tick lebih tua dari kunci committer: memang tidak bisa dikomit (by design)
  MENUNGGU       tick baru ditulis < TENGGANG_S lalu; worker polling 5 menit, jadi belum waktunya curiga
  ALARM          tick sudah ada >= TENGGANG_S tetapi komit belum ada ("WORKER DIAM"), atau komit ada tetapi ungkap tertahan >= TENGGANG_S
Kode keluar: 0 semua OK/SEBELUM KUNCI · 1 ada ALARM · 2 ada MENUNGGU (periksa lagi nanti) · 3 chain TAK TERBACA (gagal baca != worker mati: TUNDA).

Hanya stdlib (rantai GitHub tidak memasang pip): JSON-RPC lewat urllib, ABI lewat `engine/chain.py`. `--alert` mengirim Telegram bila
ALERT_TELEGRAM_TOKEN / ALERT_TELEGRAM_CHAT ada di lingkungan (secrets GitHub yang dipasang builder); tanpa itu hanya mencetak.

    python -X utf8 tools/worker_watch.py            # periksa sekarang (siapa pun, tanpa kunci)
    python -X utf8 tools/worker_watch.py --alert    # + kirim alert bila ALARM
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from typing import Dict, List, Optional, Sequence, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from engine import chain, ledger                       # noqa: E402
from engine.spec import SPECS                          # noqa: E402
import signal_commit as sc                             # noqa: E402

TENGGANG_S = 1800
RPCS = ("https://bsc-testnet.publicnode.com", "https://bsc-testnet-rpc.publicnode.com", "https://bsc-testnet.drpc.org")
OK, SEBELUM, MENUNGGU, ALARM = "OK", "SEBELUM KUNCI", "MENUNGGU", "ALARM"
RANK = {OK: 0, SEBELUM: 0, MENUNGGU: 2, ALARM: 1}


class ReadError(RuntimeError):
    pass


class Reader:
    """eth_call minimal tanpa eth-abi. Jawaban kosong ("0x") = galat, bukan "tidak ada" (SK-W3)."""

    def __init__(self, urls: Sequence[str] = RPCS, timeout: float = 15.0):
        self.urls, self.timeout = list(urls), timeout

    def call(self, to: str, data: bytes) -> bytes:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": "0x" + data.hex()}, "latest"]}).encode()
        last = None
        for u in self.urls:
            try:
                req = urllib.request.Request(u, data=body, headers={"Content-Type": "application/json", "User-Agent": "fabius-worker-watch/1.0"})
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    d = json.loads(r.read().decode())
            except Exception as e:  # noqa: BLE001 - endpoint berikutnya
                last = e
                continue
            if "error" in d:
                raise ReadError(f"eth_call ditolak: {str(d['error'])[:160]}")
            res = d.get("result") or "0x"
            if res == "0x":
                raise ReadError(f"jawaban kosong dari {to} (alamat salah / node belum sinkron)")
            return bytes.fromhex(res[2:])
        raise ReadError(f"semua {len(self.urls)} endpoint RPC gagal: {type(last).__name__}: {str(last)[:120]}")


def selector(sig: str) -> bytes:
    return chain.keccak256(sig.encode())[:4]


def decode_commit(raw: bytes) -> dict:
    """getCommit -> tuple statis 9 kata: (address, uint64 asof, uint64 committedAt, uint32 n, uint32 revealed, bool missed, bytes32 botId, specSha, root)."""
    if len(raw) < 9 * 32:
        raise ReadError(f"getCommit: {len(raw)} byte, harus >= 288")
    w = [raw[i * 32:(i + 1) * 32] for i in range(9)]
    num = lambda b: int.from_bytes(b, "big")                     # noqa: E731
    return {"committer": "0x" + w[0][12:].hex(), "asof": num(w[1]), "committedAt": num(w[2]), "n": num(w[3]), "revealed": num(w[4]),
            "missed": bool(num(w[5])), "botId": w[6], "specSha": w[7], "root": w[8]}


class ChainView:
    def __init__(self, reader, anchor: str, registry: str):
        self.r, self.anchor, self.registry = reader, anchor, registry

    def locked_at(self, committer: str, bot: str, spec_sha: str) -> int:
        data = selector(sc.SIG_LOCKED_AT) + chain.abi_encode(("address", "bytes32", "bytes32"), (committer, chain.ascii32(bot), chain.from_hex(spec_sha)))
        return int.from_bytes(self.r.call(self.registry, data)[:32], "big")

    def get_commit(self, cid: bytes) -> dict:
        return decode_commit(self.r.call(self.anchor, selector(sc.SIG_GET_COMMIT) + chain.abi_encode(("bytes32",), (cid,))))


def check(bots: Sequence[str], ledger_dir: str, cv, committer: str, now_s: int, tenggang_s: int = TENGGANG_S) -> Tuple[int, List[Tuple[str, str, str, str]]]:
    """-> (kode keluar, [(bot, bar, status, detail)]). Murni terhadap `cv` dan berkas ledger."""
    rows = []
    for bot in bots:
        spec = SPECS[bot]
        ticks = [r for r in ledger.load(os.path.join(ledger_dir, f"{bot}.jsonl")) if r.get("type") == "tick"]
        if not ticks:
            rows.append((bot, "-", OK, "belum ada tick"))
            continue
        tk = max(ticks, key=lambda r: r["asof"])
        asof_s, date = sc.asof_s_of(tk), tk["asof_date"]
        locked = cv.locked_at(committer, bot, spec.sha())
        if locked == 0 or locked > asof_s:
            rows.append((bot, date, SEBELUM, "tick lebih tua dari kunci committer (tidak bisa dikomit, by design)"))
            continue
        emitted = ledger.iso_ms(tk["emitted_utc"]) // 1000
        c = cv.get_commit(sc.commit_id(committer, bot, spec.sha(), asof_s))
        if int(c["committer"], 16) == 0:
            age = now_s - emitted
            if age < tenggang_s:
                rows.append((bot, date, MENUNGGU, f"tick ditulis {age // 60} menit lalu; komit belum ada (tenggang {tenggang_s // 60} menit)"))
            else:
                rows.append((bot, date, ALARM, f"WORKER DIAM: tick ada sejak {ledger.utc_iso(emitted * 1000)} ({age // 60} menit), komit belum ada di SignalAnchor"))
            continue
        n, rev = int(c["n"]), int(c["revealed"])
        if rev < n and now_s - int(c["committedAt"]) >= tenggang_s:
            rows.append((bot, date, ALARM, f"UNGKAP TERTAHAN: {rev}/{n} terungkap {(now_s - int(c['committedAt'])) // 60} menit sesudah komit"))
        else:
            rows.append((bot, date, OK, f"dikomit {ledger.utc_iso(int(c['committedAt']) * 1000)} ({(int(c['committedAt']) - asof_s) // 60} menit sesudah tutup), "
                                         f"{rev}/{n} terungkap"))
    worst = max((RANK[s] for _, _, s, _ in rows if RANK[s] == 1), default=None)
    code = 1 if worst == 1 else (2 if any(s == MENUNGGU for _, _, s, _ in rows) else 0)
    return code, rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Penjaga luar worker Railway: tick resmi terakhir sudah dikomit + diungkap? (tanpa kunci)")
    ap.add_argument("--bots", default=",".join(sc.BOTS_DEFAULT))
    ap.add_argument("--ledger", default=os.path.join(ROOT, "ledger", "paper"))
    ap.add_argument("--tenggang", type=int, default=TENGGANG_S)
    ap.add_argument("--alert", action="store_true", help="kirim Telegram bila ALARM (butuh ALERT_TELEGRAM_TOKEN/CHAT di lingkungan)")
    a = ap.parse_args()
    addrs = sc.load_addresses()
    committer = addrs["committer"]
    if not (addrs["anchor"] and addrs["registry"] and committer):
        print("deployments/97.json tidak lengkap (SignalAnchor/LockRegistry/m3.committer)")
        return 3
    cv = ChainView(Reader(), addrs["anchor"], addrs["registry"])
    now = int(time.time())
    try:
        code, rows = check([b.strip() for b in a.bots.split(",") if b.strip()], a.ledger, cv, committer, now, a.tenggang)
    except ReadError as e:
        print(f"TAK TERBACA: {e} - bukan bukti worker mati; diperiksa lagi nanti")
        return 3
    print(f"penjaga luar worker {ledger.utc_iso(now * 1000)} | committer {committer} | tenggang {a.tenggang // 60} menit")
    for bot, date, st, det in rows:
        print(f"  {bot} {date} {st:13s} {det}")
    if code == 1 and a.alert:
        import alert as alertmod
        al = alertmod.Alerter(prefix="Fabius penjaga luar")
        for bot, date, st, det in rows:
            if st == ALARM:
                al.send(f"watch:{bot}:{date}", f"{bot} bar {date}: {det}")
    print({0: "VONIS: worker hidup", 1: "VONIS: ALARM", 2: "VONIS: MENUNGGU (periksa lagi)"}[code])
    return code


def guarded_main() -> int:
    """Galat tak terduga = 3 (TAK TERBACA), BUKAN 1: rantai GitHub membaca 1 sebagai ALARM "worker diam" - crash alat ini tidak boleh jadi tuduhan."""
    try:
        return main()
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        print(f"TAK TERBACA: galat penjaga sendiri {type(e).__name__}: {str(e)[:200]} - bukan bukti worker mati")
        return 3


if __name__ == "__main__":
    raise SystemExit(guarded_main())

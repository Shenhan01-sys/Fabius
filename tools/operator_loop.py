"""Worker Railway Fabius (F-D80, tahap 1): jalan terus; tiap POLL_S detik: sinkron ledger dari GitHub -> `signal_commit` (komit + ungkap ke SignalAnchor
chain 97) -> catat.

Tahap 1 sengaja sempit: ledger tetap DITULIS rantai GitHub (penulis tunggal, F-D78) - worker ini hanya MEMBACA ledger yang sudah di-commit, menghitung
ulang sinyalnya dari bar yang di-commit, dan menandatangani komitnya. Dua penulis ledger = rantai hash bertabrakan; karena itu pemindahan penulis ke sini
adalah tahap terpisah dengan keputusan builder sendiri.

Lingkungan (variabel Railway):
  COMMITTER_PRIVATE_KEY   kunci committer (tanpa ini: mode RENCANA - menghitung dan mencatat, tidak mengirim apa pun)
  SIGNAL_ANCHOR_ADDRESS / LOCK_REGISTRY_ADDRESS   opsional; bawaan dari deployments/97.json di repo
  FABIUS_REPO (bawaan repo publik), FABIUS_BRANCH (master), FABIUS_BOTS (B1-TREND,B3-CARRY), POLL_S (300), RPC_URL, REVEAL_DELAY_S (0), WORKDIR

Saat mulai, worker mencatat apakah API Binance (fapi/api), Binance Vision, dan GitHub bisa dijangkau dari region-nya: bahan keputusan tahap 3
(bar dari REST segera sesudah penutupan, bukan zip Vision ~9 jam kemudian). Runner GitHub (AS) mendapat HTTP 451 dari fapi.

    python -X utf8 tools/operator_loop.py            # jalan terus (Railway)
    python -X utf8 tools/operator_loop.py --once     # satu putaran lalu keluar (uji lokal)
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import signal_commit as sc                             # noqa: E402
from engine.spec import SPECS                          # noqa: E402

REPO = os.environ.get("FABIUS_REPO", "https://github.com/Shenhan01-sys/Fabius.git")
BRANCH = os.environ.get("FABIUS_BRANCH", "master")
WORKDIR = os.environ.get("WORKDIR", os.path.join("/tmp", "fabius-ledger"))
BOTS = [b.strip() for b in os.environ.get("FABIUS_BOTS", ",".join(sc.BOTS_DEFAULT)).split(",") if b.strip()]
POLL_S = int(os.environ.get("POLL_S", "300"))
REVEAL_DELAY_S = int(os.environ.get("REVEAL_DELAY_S", "0"))
SUMMARY_EVERY_S = 6 * 3600
UA = {"User-Agent": "Mozilla/5.0 (compatible; fabius-worker/1.0)"}
PROBES = (("binance fapi", "https://fapi.binance.com/fapi/v1/time"),
          ("binance api", "https://api.binance.com/api/v3/time"),
          ("binance vision", "https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-01.zip.CHECKSUM"),
          ("github", "https://api.github.com/zen"))


def log(msg: str) -> None:
    print(f"{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} {msg}", flush=True)


def git(*args: str, cwd: str = None, timeout: int = 300) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"git {args[0]} gagal ({r.returncode}): {(r.stderr or r.stdout).strip()[:200]}")
    return r.stdout.strip()


def sync(workdir: str = WORKDIR) -> str:
    """Clone dangkal + sparse (hanya ledger/ dan deployments/; repo penuh ~145 MB) sekali, lalu fetch + reset tiap putaran. -> sha HEAD."""
    if not os.path.isdir(os.path.join(workdir, ".git")):
        if os.path.exists(workdir):
            shutil.rmtree(workdir)
        git("clone", "--depth", "1", "--filter=blob:none", "--sparse", "--branch", BRANCH, REPO, workdir)
        git("sparse-checkout", "set", "ledger", "deployments", cwd=workdir)
    else:
        git("fetch", "--depth", "1", "origin", BRANCH, cwd=workdir)
        git("reset", "--hard", "FETCH_HEAD", cwd=workdir)
    return git("rev-parse", "HEAD", cwd=workdir)


def probe(url: str) -> str:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=10) as r:
            return f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return f"{type(e).__name__}: {str(e)[:80]}"


class Worker:
    def __init__(self, workdir: str = WORKDIR):
        self.workdir = workdir
        self.last_lines = None
        self.last_state = None
        self.last_summary = 0.0

    def note_state(self, s: str) -> None:
        """Catat keadaan hanya saat berubah (log Railway tidak dibanjiri baris yang sama tiap 5 menit). Sha repo TIDAK masuk sini:
        commit bot ke master tiap ±4 menit akan membuat setiap putaran tampak 'berubah'. Sha repo ada di detak."""
        if s != self.last_state:
            log(s)
            self.last_state = s

    def heartbeat(self, head: str, extra: str) -> None:
        if time.time() - self.last_summary >= SUMMARY_EVERY_S:
            log(f"detak: repo {head[:10]} | {extra}")
            self.last_summary = time.time()

    def once(self) -> None:
        import evm as evmmod
        from paper_tick import Views
        head = sync(self.workdir)
        addrs = sc.load_addresses(os.path.join(self.workdir, "deployments", f"{sc.CHAIN_ID}.json"))
        if not addrs["anchor"] or not addrs["registry"]:
            self.note_state("menunggu deploy: SignalAnchor/LockRegistry belum ada di deployments/97.json (dan tidak di variabel)")
            self.heartbeat(head, "menunggu deploy")
            return
        pk = sc.committer_key()
        committer = evmmod.address_of(pk) if pk else addrs["committer"]
        if not committer:
            self.note_state("menunggu committer: tidak ada COMMITTER_PRIVATE_KEY dan tidak ada m3.committer di deployments/97.json")
            self.heartbeat(head, "menunggu committer")
            return
        self.note_state(f"aktif: SignalAnchor {addrs['anchor']} committer {committer} ({'KIRIM' if pk else 'RENCANA - tanpa kunci'})")
        ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
        ev.chain_check()
        cv = sc.AnchorView(ev, addrs["anchor"], addrs["registry"])
        acts = sc.plan(BOTS, os.path.join(self.workdir, "ledger", "paper"), Views(os.path.join(self.workdir, "ledger", "bars")), cv, committer,
                       sc.seed_from_key(pk) if pk else None, int(time.time()), REVEAL_DELAY_S)
        lines = [a.line() for a in acts]
        if lines != self.last_lines:
            for ln in lines or ["(tidak ada tick dalam jendela pindai)"]:
                log("  " + ln)
            self.last_lines = lines
        if pk and any(a.batch is not None and a.kind in ("commit", "reveal") for a in acts):
            st = sc.execute(acts, ev, addrs["anchor"], pk, log=lambda m: log(m))
            log(f"terkirim: {st['commit']} komit, {st['reveal']} ungkap, {st['gagal']} gagal")
            self.last_lines = None                      # paksa catat keadaan baru putaran berikutnya
        if time.time() - self.last_summary >= SUMMARY_EVERY_S:
            kinds = {k: sum(1 for a in acts if a.kind == k) for k in ("commit", "reveal", "ok", "skip", "alarm")}
            self.heartbeat(head, f"saldo committer {ev.balance(committer) / 1e18:.6f} tBNB | aksi {kinds}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Worker Railway: komit sinyal ledger ke SignalAnchor (tahap 1).")
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    specs = " ".join(f"{b}={SPECS[b].sha()[:12]}" for b in BOTS if b in SPECS)
    log(f"worker mulai | repo {REPO}@{BRANCH} | bot {specs} | poll {POLL_S}s | ungkap +{REVEAL_DELAY_S}s | "
        f"region {os.environ.get('RAILWAY_REPLICA_REGION', '?')} | build {os.environ.get('RAILWAY_GIT_COMMIT_SHA', 'lokal')[:10]} | "
        f"kunci {'ADA' if sc.committer_key() else 'TIDAK ADA (mode rencana)'}")
    for name, url in PROBES:
        log(f"probe {name}: {probe(url)}")
    w = Worker()
    while True:
        t0 = time.time()
        try:
            w.once()
        except Exception as e:  # noqa: BLE001 - satu putaran gagal tidak boleh mematikan worker; diulang putaran berikutnya
            log(f"putaran GAGAL: {type(e).__name__}: {str(e)[:240]}")
            tb = traceback.format_exc().strip().splitlines()
            log("  " + " | ".join(tb[-3:])[:400])
            w.last_lines = None
        if a.once:
            return 0
        time.sleep(max(5.0, POLL_S - (time.time() - t0)))


if __name__ == "__main__":
    raise SystemExit(main())

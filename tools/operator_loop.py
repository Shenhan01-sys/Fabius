"""Worker Railway Fabius (F-D80, tahap 1): jalan terus; tiap POLL_S detik: sinkron ledger dari GitHub -> `signal_commit` (komit + ungkap ke SignalAnchor
chain 97) -> catat.

Tahap 1 sengaja sempit: ledger tetap DITULIS rantai GitHub (penulis tunggal, F-D78) - worker ini hanya MEMBACA ledger yang sudah di-commit, menghitung
ulang sinyalnya dari bar yang di-commit, dan menandatangani komitnya. Dua penulis ledger = rantai hash bertabrakan; karena itu pemindahan penulis ke sini
adalah tahap terpisah dengan keputusan builder sendiri.

Lingkungan (variabel Railway):
  COMMITTER_PRIVATE_KEY   kunci committer (tanpa ini: mode RENCANA - menghitung dan mencatat, tidak mengirim apa pun)
  SIGNAL_ANCHOR_ADDRESS / LOCK_REGISTRY_ADDRESS   opsional; bawaan dari deployments/97.json di repo
  FABIUS_REPO (bawaan repo publik), FABIUS_BRANCH (master), FABIUS_BOTS (B1-TREND,B3-CARRY), POLL_S (300), RPC_URL, REVEAL_DELAY_S (0), WORKDIR
  PIN_BOOK (bawaan 1)     P108: epoch buku slot baru yang ditulis rantai GitHub (`ledger/book/buku.jsonl`) di-pin ke LockRegistry oleh committer
                          (F-D85: book_sha tiap epoch dicatat di chain). 0 = hanya dicatat "PERLU pin", tidak mengirim.
  ALERT_TELEGRAM_TOKEN / ALERT_TELEGRAM_CHAT   P101: kanal alert (dipasang builder sendiri; tanpa keduanya alert hanya dicatat di log), lihat tools/alert.py.
  ALERT_MIN_TBNB (0.01)   saldo committer di bawah ini = alert.
  EXEC_MODE (off) + BINANCE_API_KEY / BINANCE_SECRET_KEY / BINANCE_API_ENV   P118 (epik 10, F-D93): eksekutor venue di akhir putaran, DIBUNGKUS
                          SENDIRI (galatnya tidak menggagalkan komit/ungkap); lihat tools/eksekutor.py. Mode live ditolak di service ini.

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
PIN_BOOK = os.environ.get("PIN_BOOK", "1") != "0"
ALERT_MIN_TBNB = float(os.environ.get("ALERT_MIN_TBNB", "0.01"))
FAILS_BEFORE_ALERT = 3
TICK_GRACE_S = 12 * 3600 + 900          # tick resmi harus ada paling lambat 12 jam (+15 menit) sesudah penutupan; lewat itu rantai GitHub dianggap macet
SUMMARY_EVERY_S = 6 * 3600
UA = {"User-Agent": "Mozilla/5.0 (compatible; fabius-worker/1.0)"}
PROBES = (("binance fapi", "https://fapi.binance.com/fapi/v1/time"),
          ("binance api", "https://api.binance.com/api/v3/time"),
          ("binance demo fapi", "https://demo-fapi.binance.com/fapi/v1/time"),
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
        self.last_book = None
        self.last_summary = 0.0
        self.fails = 0
        self.executor = None
        self.exec_fails = 0
        self.last_exec = None
        self.canary = None
        self.canary_fails = 0
        self.last_canary = None
        import alert as alertmod
        self.alert = alertmod.Alerter(log=lambda m: log(m))

    def note_state(self, s: str) -> None:
        """Catat keadaan hanya saat berubah (log Railway tidak dibanjiri baris yang sama tiap 5 menit). Sha repo TIDAK masuk sini:
        commit bot ke master tiap ±4 menit akan membuat setiap putaran tampak 'berubah'. Sha repo ada di detak."""
        if s != self.last_state:
            log(s)
            self.last_state = s

    def note_book(self, s: str) -> None:
        if s != self.last_book:
            log(s)
            self.last_book = s

    def book_pin(self, ev, registry: str, committer: str, pk, head: str, pin: bool = None) -> str:
        """P108: pin `book_sha` epoch terakhir buku hidup ke LockRegistry bila belum. Membaca dari repo yang disinkron (penulis buku = rantai GitHub).
        Gagal membaca `lockedAt` TIDAK berarti "belum di-pin" (TUNDA, dicoba putaran berikutnya); buku tidak sah tidak di-pin (TOLAK). -> keadaan."""
        import pin_book as pb
        from engine import ledger as led
        pin = PIN_BOOK if pin is None else pin
        try:
            recs = led.load(os.path.join(self.workdir, "ledger", "book", "buku.jsonl"))
            rec, probs = pb.last_epoch(recs)
            if probs:
                self.note_book(f"buku hidup TIDAK SAH - tidak di-pin: {probs[0]}")
                return "tolak"
            if rec is None:
                return "kosong"
            at = pb.locked_at(ev, registry, committer, rec)
        except Exception as e:  # noqa: BLE001 - gagal baca != belum di-pin
            self.note_book(f"pin buku GAGAL dibaca ({type(e).__name__}: {str(e)[:120]}); dicoba lagi putaran berikutnya")
            return "tunda"
        name = pb.label_of(rec)
        if at:
            self.note_book(f"buku {name} sudah di-pin (lockedAt {led.utc_iso(at * 1000)}, book_sha {rec['book_sha'][:14]}…)")
            return "ok"
        if not pk or not pin:
            self.note_book(f"buku {name} PERLU pin (book_sha {rec['book_sha'][:14]}…): {'tanpa kunci' if not pk else 'PIN_BOOK=0'}")
            return "perlu"
        if ev.has_pending(committer):
            self.note_book(f"buku {name}: committer masih punya transaksi tertunda; pin ditunda")
            return "tunda"
        from evm import RpcError, error_name, receipt_ok
        try:
            r = ev.send(pk, registry, pb.lock_calldata(rec, pb.book_uri(head)))
        except RpcError as e:
            self.note_book(f"pin buku {name} DITOLAK sebelum kirim ({error_name(e.data, sc.ERRORS) or e}); nol gas terbakar")
            return "tolak"
        ok = receipt_ok(r)
        log(f"pin buku {name}: tx {r.get('transactionHash')} {'blok ' + str(ev.num(r.get('blockNumber'))) if ok else 'STATUS 0'} | uri {pb.book_uri(head)}")
        return "kirim" if ok else "gagal"

    def exec_step(self, cv, committer: str) -> str:
        """P118 (epik 10): eksekutor venue, DIBUNGKUS SENDIRI - galatnya dicatat (+ alert sesudah 3 kali berturut) dan TIDAK PERNAH menggagalkan
        putaran komit/ungkap (T8 SK-E10)."""
        try:
            if self.executor is None:
                import eksekutor
                self.executor = eksekutor.Executor(log=lambda m: log(m), alert=self.alert)
            st = self.executor.round(os.path.join(self.workdir, "ledger", "paper"), cv, committer)
            if st != "off" and st != self.last_exec:
                log(f"eksekutor: {st}")
                self.last_exec = st
            self.exec_fails = 0
            return st
        except Exception as e:  # noqa: BLE001 - eksekutor tidak boleh mematikan worker komit
            self.exec_fails += 1
            log(f"eksekutor GAGAL (komit/ungkap tidak terpengaruh): {type(e).__name__}: {str(e)[:200]}")
            if self.exec_fails >= FAILS_BEFORE_ALERT:
                self.alert.send("eksekutor-gagal", f"eksekutor: {self.exec_fails} putaran gagal berturut-turut; terakhir {type(e).__name__}: {str(e)[:160]}")
            return "gagal"

    def canary_step(self, cv, committer: str, ev=None, pk=None) -> str:
        """P133 (F-D96): canary uang NYATA, DIBUNGKUS SENDIRI seperti eksekutor - galatnya tidak pernah menggagalkan komit/ungkap (T8 SK-E26).
        Pencatat on-chain (ExecutionAnchor) dipasang tiap putaran dari kunci committer; tanpa kunci/alamat: catatan tertunda, order tetap jalan."""
        try:
            import canary as canmod
            if self.canary is None:
                self.canary = canmod.Canary(log=lambda m: log(m), alert=self.alert)
            anchor = canmod.anchor_address(os.path.join(self.workdir, "deployments", "97.json"))
            if ev is not None and pk and anchor:
                self.canary.recorder = canmod.chain_recorder(ev, pk, anchor)
            st = self.canary.round(os.path.join(self.workdir, "ledger", "paper"), cv, committer)
            if st != "off" and st != self.last_canary:
                log(f"canary: {st}")
                self.last_canary = st
            self.canary_fails = 0
            return st
        except Exception as e:  # noqa: BLE001 - canary tidak boleh mematikan worker komit
            self.canary_fails += 1
            log(f"canary GAGAL (komit/ungkap tidak terpengaruh): {type(e).__name__}: {str(e)[:200]}")
            if self.canary_fails >= FAILS_BEFORE_ALERT:
                self.alert.send("canary-gagal", f"canary uang nyata: {self.canary_fails} putaran gagal berturut-turut; terakhir {type(e).__name__}: {str(e)[:160]}")
            return "gagal"

    def alerts_for(self, acts, sent: dict = None, missing=()) -> None:
        """P101: aksi yang butuh mata manusia -> alert (dedupe per kunci di `tools/alert.py`)."""
        for a in acts:
            if a.kind == "alarm":
                self.alert.send(f"alarm:{a.bot}:{a.asof_date}", f"ALARM {a.bot} bar {a.asof_date}: {a.detail}")
            elif a.kind == "skip" and "TERLEWAT" in a.detail:
                self.alert.send(f"terlewat:{a.bot}:{a.asof_date}", f"TERLEWAT {a.bot} bar {a.asof_date}: {a.detail}", sekali=True)
        if sent and sent.get("gagal"):
            self.alert.send(f"kirim-gagal:{int(time.time()) // 3600}", f"{sent['gagal']} transaksi komit/ungkap GAGAL (lihat log fabius-engine)")
        for bot, date in missing:
            self.alert.send(f"tick-hilang:{bot}:{date}", f"tick resmi {bot} bar {date} TIDAK ADA 12 jam sesudah penutupan: rantai GitHub paper-ledger macet? "
                            "(gh run list --workflow paper-ledger.yml)", sekali=True)

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
        st = None
        if pk and any(a.batch is not None and a.kind in ("commit", "reveal") for a in acts):
            st = sc.execute(acts, ev, addrs["anchor"], pk, log=lambda m: log(m))
            log(f"terkirim: {st['commit']} komit, {st['reveal']} ungkap, {st['gagal']} gagal")
            self.last_lines = None                      # paksa catat keadaan baru putaran berikutnya
        self.alerts_for(acts, st, missing_ticks(os.path.join(self.workdir, "ledger", "paper"), BOTS, int(time.time())))
        pin = self.book_pin(ev, addrs["registry"], committer, pk, head)
        if pin in ("tolak", "gagal"):
            self.alert.send(f"pin-buku:{pin}", f"pin book_sha {pin.upper()}: {self.last_book}")
        self.exec_step(cv, committer)
        self.canary_step(cv, committer, ev, pk)
        if time.time() - self.last_summary >= SUMMARY_EVERY_S:
            kinds = {k: sum(1 for a in acts if a.kind == k) for k in ("commit", "reveal", "ok", "skip", "alarm")}
            bal = ev.balance(committer) / 1e18
            self.heartbeat(head, f"saldo committer {bal:.6f} tBNB | aksi {kinds}")
            if bal < ALERT_MIN_TBNB:
                self.alert.send("saldo-rendah", f"saldo committer {committer} tinggal {bal:.6f} tBNB (< {ALERT_MIN_TBNB}); isi ulang dari deployer")


def missing_ticks(ledger_dir: str, bots, now_s: int, grace_s: int = TICK_GRACE_S):
    """Bot yang ledger resminya tidak punya tick/gap untuk bar tertutup terakhir padahal sudah lewat `grace_s` sesudah penutupan. Ledger yang tak terbaca
    juga dilaporkan (gagal baca != tidak ada masalah)."""
    from engine import ledger as led
    from engine.series import DAY_MS
    d = led.last_closed_bar(now_s * 1000)
    if now_s * 1000 < d + DAY_MS + grace_s * 1000:
        return []
    out = []
    for bot in bots:
        try:
            recs = led.load(os.path.join(ledger_dir, f"{bot}.jsonl"))
        except led.LedgerError:
            out.append((bot, led.date_of(d) + " (ledger tak terbaca)"))
            continue
        if recs and recs[0].get("first_asof", 0) <= d and not any(r.get("type") in ("tick", "gap") and r.get("asof") == d for r in recs):
            out.append((bot, led.date_of(d)))
    return out


def guarded_round(w: "Worker") -> bool:
    """Satu putaran yang tidak boleh mematikan worker: galat apa pun (git, RPC, data) dicatat lalu diulang putaran berikutnya. Tidak ada yang dikirim
    dari putaran yang gagal sebelum `execute`; yang gagal DI TENGAH `execute` dilindungi `has_pending` + `AlreadyCommitted` di putaran berikutnya."""
    try:
        w.once()
        w.fails = 0
        return True
    except Exception as e:  # noqa: BLE001
        log(f"putaran GAGAL: {type(e).__name__}: {str(e)[:240]}")
        tb = traceback.format_exc().strip().splitlines()
        log("  " + " | ".join(tb[-3:])[:400])
        w.last_lines = None
        w.fails = getattr(w, "fails", 0) + 1
        if w.fails >= FAILS_BEFORE_ALERT and hasattr(w, "alert"):
            w.alert.send("putaran-gagal", f"worker: {w.fails} putaran GAGAL berturut-turut; terakhir {type(e).__name__}: {str(e)[:200]}")
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Worker Railway: komit sinyal ledger ke SignalAnchor (tahap 1).")
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    specs = " ".join(f"{b}={SPECS[b].sha()[:12]}" for b in BOTS if b in SPECS)
    log(f"worker mulai | repo {REPO}@{BRANCH} | bot {specs} | poll {POLL_S}s | ungkap +{REVEAL_DELAY_S}s | "
        f"region {os.environ.get('RAILWAY_REPLICA_REGION', '?')} | build {os.environ.get('RAILWAY_GIT_COMMIT_SHA', 'lokal')[:10]} | "
        f"kunci {'ADA' if sc.committer_key() else 'TIDAK ADA (mode rencana)'} | eksekutor {os.environ.get('EXEC_MODE', 'off')} | "
        f"umpan eksekusi {'nyala' if os.environ.get('EXEC_FEED_TOKEN') else 'mati (EXEC_FEED_TOKEN tidak ada, F-D94 H7)'} | "
        f"canary uang nyata {os.environ.get('EXEC_REAL', 'off')}")
    for name, url in PROBES:
        log(f"probe {name}: {probe(url)}")
    w = Worker()
    if w.alert.enabled:                                 # uji kanal tiap start: memasang variabel alert memicu redeploy, jadi pesan ini = bukti kanal hidup
        w.alert.send("mulai", f"worker mulai (region {os.environ.get('RAILWAY_REPLICA_REGION', '?')}, kunci {'ADA' if sc.committer_key() else 'TIDAK ADA'}); "
                              "alert aktif: ALARM, TERLEWAT, kirim gagal, 3 putaran gagal, pin buku ditolak, saldo < "
                              f"{ALERT_MIN_TBNB} tBNB, tick resmi hilang")
    while True:
        t0 = time.time()
        guarded_round(w)
        if a.once:
            return 0
        time.sleep(max(5.0, POLL_S - (time.time() - t0)))


if __name__ == "__main__":
    raise SystemExit(main())

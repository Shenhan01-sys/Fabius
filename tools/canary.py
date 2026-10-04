"""Canary uang NYATA (P133; F-D92 tahap S3, F-D96): satu aset, <= 10 USDT, mengikuti keputusan B1-TREND (bot INTI), di Binance USDⓈ-M PROD.

Ini membuktikan MEKANISME uang nyata - order, isi, fee nyata, rekonsiliasi, pencatatan publik - BUKAN kinerja B1 (B1 penuh butuh >= ±1.362 USDT;
kinerjanya tetap diukur di paper, kertas-venue, dan akun demo). Berjalan di worker `fabius-engine` (F-D96: paket gratis), DIBUNGKUS SENDIRI: galat
canary tidak pernah mengganggu komit/ungkap maupun eksekutor demo.

Lingkungan (variabel Railway `fabius-engine`, dipasang builder lewat dashboard - TIDAK lewat chat):
  EXEC_REAL                off (bawaan) | canary
  BINANCE_REAL_API_KEY     kunci akun Binance ASLI: Futures ON, Withdraw OFF (dicek saat start lewat `apiRestrictions`; gagal = tidak start)
  BINANCE_REAL_SECRET_KEY
  EXEC_LIVE_OK             izin builder bertanggal: "binance:sampai:YYYY-MM-DD" (sesudah tanggal itu: tidak ada order baru)
  EXEC_REAL_ASSET          aset B1 yang diikuti (bawaan XRPUSDT: order terkecil ±5,1 USDT, likuid)
  EXEC_REAL_MAX_USDT       plafon notional (bawaan 10); batas keras kode HARD_MAX_USDT = 10 (F-D92) tidak bisa dilewati env

SAKELAR PUBLIK (F-D97, permintaan builder "bikin toggle aja yg bisa dynamic nyalain real trade dan paper trade"): berkas repo
`config/uang_nyata.json` `{"aktif": true|false}` - dibalik builder lewat edit berkas di GitHub (tanpa Railway, tanpa redeploy), riwayatnya publik.
Uang nyata hanya bila KEDUANYA: variabel Railway di atas (bersenjata) DAN sakelar `aktif: true`. Sakelar dibaca SEKALI per bar, saat bar baru
dieksekusi (berlaku mulai bar BERIKUTNYA, bukan di tengah bar): satu bar = satu laporan, id order (venue, bot, bar, aset, sisi) dan kunci
ExecutionAnchor tidak pernah bertabrakan. Sakelar mati / tak terbaca + posisi datar = tidak ada order, tidak ada laporan; sakelar mati + posisi masih
terbuka = bar itu dieksekusi dengan target datar (tutup reduce-only) dan dilaporkan. Laporan membawa `sakelar: nyala|mati`. Paper (ledger resmi)
dan akun demo berjalan terus apa pun posisi sakelar. Keluar darurat di tengah bar = tutup manual di aplikasi Binance; canary membaca posisi nyata
di bar berikutnya (isi manual itu tidak masuk umpan).

Aturan (T8 SK-E22..SK-E27):
  - bukti dulu: tidak ada order sebelum komit bar itu ada di SignalAnchor (R-E1); tick lebih tua dari kunci = tidak dieksekusi;
  - bar yang sudah ada di ledger publik `ledger/eksekusi/binance-live/B1-TREND.jsonl` tidak dieksekusi ulang (worker restart / redeploy);
  - B1 memegang aset -> canary memegang anggaran = min(plafon, ekuitas akun) x (1 - 0,2 %) di aset itu; B1 flat -> tutup (reduce-only);
  - anggaran < order terkecil venue -> `dilewati` (dicatat), bukan dipaksa; posisi yang dimaksud > plafon = BERHENTI (posisi tanpa order dinilai
    x 0,9: hanyut harga di dalam pita tanpa-transaksi bukan pelanggaran, T8 SK-E30);
  - leverage dipaksa 1x; akun mode hedge = BERHENTI; kunci dengan izin tarik / tanpa futures = tidak start;
  - setiap bar yang dieksekusi: laporan ke umpan Gist (venue `binance-live`, `exec_feed`) DAN catatan isi on-chain di ExecutionAnchor
    (`recordBatch`, real = true). Gagal mencatat = TERTUNDA, diulang tiap putaran; order tidak pernah digandakan (id deterministik, `place` idempoten).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from typing import Callable, Dict, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from engine import chain, eksekusi as ex, ledger                            # noqa: E402
from engine.spec import SPECS                                               # noqa: E402
import exec_feed as xf                                                      # noqa: E402
import signal_commit as sc                                                  # noqa: E402
import venue_binance as vb                                                  # noqa: E402

BOT = "B1-TREND"
VENUE = "binance-live"
HARD_MAX_USDT = 10.0
CADANGAN = 0.002
CONSENT_RE = re.compile(r"^binance:sampai:(\d{4}-\d{2}-\d{2})$")
TOGGLE_REL = os.path.join("config", "uang_nyata.json")


def toggle_on(ledger_dir: str) -> bool:
    """Sakelar publik (F-D97) di klon repo yang memuat `ledger_dir` (= <repo>/ledger/paper). Tidak ada / tak terbaca / bukan true = MATI."""
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(ledger_dir))), TOGGLE_REL)
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f).get("aktif") is True
    except (OSError, ValueError, AttributeError):
        return False


FILL_TUPLE = "(bytes32,bytes32,bytes32,bytes32,uint64,uint8,bool,uint64,uint64,uint128,uint128,uint128,bytes32,bytes32)"
SIG_RECORD_BATCH = f"recordBatch({FILL_TUPLE}[])"
E8 = 10 ** 8


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def fills_of(rec: dict, commit_id: bytes) -> list:
    """Baris laporan -> tuple `ExecutionAnchor.Fill` untuk isi yang benar-benar terisi (qty > 0). reportHash = sha256 baris umpan yang sama."""
    rh = hashlib.sha256(xf.line_of(rec).encode()).digest()
    out = []
    for o in rec.get("orders", []):
        if not o.get("qty"):
            continue
        fee_asset = (o.get("fee_aset") or "").split(",")[0]
        out.append((commit_id, chain.ascii32(rec["venue"]), chain.ascii32(o["aset"]), chain.ascii32(o["id"]), int(o["order_id"]),
                    1 if o["sisi"] == "BUY" else 2, rec.get("mode") == "live", int(o["t_kirim"]), int(o["t_isi"]),
                    int(round(float(o["qty"]) * E8)), int(round(float(o["px"]) * E8)), int(round(float(o.get("fee") or 0) * E8)),
                    chain.ascii32(fee_asset) if fee_asset else b"\0" * 32, rh))
    return out


class Canary:
    def __init__(self, env: Optional[dict] = None, log: Callable[[str], None] = print, alert=None,
                 venue_factory: Optional[Callable[[dict], object]] = None, today: Callable[[], str] = _today,
                 now_ms: Callable[[], int] = lambda: int(time.time() * 1000), sleep: Callable[[float], None] = time.sleep,
                 feed_factory: Callable[[str], object] = lambda token: xf.GistFeed(token),
                 recorder: Optional[Callable[[list], str]] = None, toggle: Callable[[str], bool] = toggle_on):
        self.envvars = os.environ if env is None else env
        self.log, self.alert, self.today, self.now_ms, self.sleep = log, alert, today, now_ms, sleep
        self.venue_factory = venue_factory or (lambda e: vb.BinanceFutures("prod", key=e.get("BINANCE_REAL_API_KEY", ""),
                                                                           secret=e.get("BINANCE_REAL_SECRET_KEY", "")))
        self.feed_factory, self.feed, self.recorder, self.toggle = feed_factory, None, recorder, toggle
        self.venue = None
        self.done: Optional[str] = None                    # bar terakhir yang diproses (sakelar dibaca sekali per bar)
        self.halted: Optional[str] = None
        self.leverage_ok = False
        self.pending_feed: Dict[str, dict] = {}
        self.pending_chain: Dict[str, list] = {}
        self.last_note: Optional[str] = None

    # ---------------------------------------------------------------- konfigurasi + pagar
    def cfg(self) -> dict:
        e = self.envvars
        return {"mode": (e.get("EXEC_REAL") or "off").strip().lower(),
                "asset": (e.get("EXEC_REAL_ASSET") or "XRPUSDT").strip().upper(),
                "max": min(float(e.get("EXEC_REAL_MAX_USDT") or HARD_MAX_USDT), HARD_MAX_USDT),
                "consent": (e.get("EXEC_LIVE_OK") or "").strip(),
                "keys": bool((e.get("BINANCE_REAL_API_KEY") or "").strip() and (e.get("BINANCE_REAL_SECRET_KEY") or "").strip()),
                "feed_token": (e.get("EXEC_FEED_TOKEN") or "").strip()}

    def refuse(self, c: dict) -> Optional[str]:
        if c["mode"] not in ("off", "canary"):
            return f"EXEC_REAL tidak dikenal: {c['mode']}"
        if not c["keys"]:
            return "BINANCE_REAL_API_KEY / BINANCE_REAL_SECRET_KEY tidak ada"
        m = CONSENT_RE.match(c["consent"])
        if not m:
            return "izin builder tidak ada: EXEC_LIVE_OK harus 'binance:sampai:YYYY-MM-DD' (F-D96)"
        if self.today() > m.group(1):
            return f"izin builder kedaluwarsa ({m.group(1)}); perbarui EXEC_LIVE_OK"
        if c["asset"] not in SPECS[BOT].universe:
            return f"EXEC_REAL_ASSET {c['asset']} di luar universe {BOT}"
        if c["max"] <= 0:
            return "EXEC_REAL_MAX_USDT harus > 0"
        return None

    def note(self, s: str) -> None:
        if s != self.last_note:
            self.log(s)
            self.last_note = s

    def stop(self, why: str) -> str:
        self.halted = why
        self.log(f"CANARY BERHENTI: {why} - tidak ada order uang nyata sampai builder me-restart worker")
        if self.alert is not None:
            self.alert.send(f"canary-berhenti:{why[:40]}", f"CANARY UANG NYATA BERHENTI: {why}")
        return "berhenti"

    # ---------------------------------------------------------------- satu putaran
    def round(self, ledger_dir: str, cv, committer: str) -> str:
        c = self.cfg()
        if c["mode"] == "off":
            return "off"
        why = self.refuse(c)
        if why:
            self.note(f"canary TIDAK jalan: {why}")
            return "tolak"
        if self.halted:
            self.flush(c)
            return "berhenti"
        try:
            st = self._round(c, ledger_dir, cv, committer)
        except vb.KeyPermissionError as e:
            return self.stop(str(e))
        self.flush(c)
        return st

    def _round(self, c: dict, ledger_dir: str, cv, committer: str) -> str:
        if self.venue is None:
            v = self.venue_factory(self.envvars)
            v.assert_safe_key()                                                    # R-E6: tarik mati + futures hidup, di PROD
            if v.dual_side():
                return self.stop("akun futures dalam mode HEDGE; ubah ke one-way di UI Binance")
            self.venue = v
        v, spec, a = self.venue, SPECS[BOT], c["asset"]
        ticks = [r for r in ledger.load(os.path.join(ledger_dir, f"{BOT}.jsonl")) if r.get("type") == "tick"]
        if not ticks:
            return "belum ada tick"
        tk = max(ticks, key=lambda r: r["asof"])
        bar = tk["asof_date"]
        if self.done == bar:
            return f"bar {bar} sudah diproses"
        if bar in self.public_bars(ledger_dir):
            self.done = bar
            return f"bar {bar} sudah ada di ledger publik {VENUE}: tidak dieksekusi ulang"
        on = self.toggle(ledger_dir)
        if not on and abs(float(v.positions().get(a, 0.0))) == 0:
            self.done = bar
            return f"bar {bar}: sakelar uang nyata MATI ({TOGGLE_REL}), posisi datar - tidak ada order, tidak ada laporan"
        locked = cv.locked_at(committer, BOT, spec.sha())
        if locked == 0 or locked > sc.asof_s_of(tk):
            self.done = bar
            return f"bar {bar} lebih tua dari kunci: tidak dieksekusi"
        cid = sc.commit_id(committer, BOT, spec.sha(), sc.asof_s_of(tk))
        cm = cv.get_commit(cid)
        if int(str(cm["committer"]), 16) == 0:
            return f"bar {bar} TUNDA: komit belum ada di SignalAnchor (bukti dulu, uang kemudian)"
        hold = on and abs(float(tk.get("targets", {}).get(a, 0.0))) > 1e-12
        filt = v.filters([a])
        bid, ask = v.book([a]).get(a, (0.0, 0.0))
        px = (bid + ask) / 2
        if px <= 0 or a not in filt:
            return f"bar {bar} TUNDA: harga/filter {a} tidak terbaca"
        pos = {k: q for k, q in v.positions().items() if k == a}
        budget = min(c["max"], float(v.equity())) * (1 - CADANGAN)
        p = ex.plan(VENUE, BOT, bar, {a: 1.0} if hold else {}, budget, pos, {a: px}, filt)
        problems = ex.guard(p, modal=c["max"], universe=[a], price={a: px}, long_only=True)
        if problems:
            return self.stop(f"pagar menolak rencana canary {bar}: {problems[:3]}")
        self.log(f"canary NYATA {a} bar {bar}: sakelar {'NYALA' if on else 'MATI -> tutup'}, B1 {'memegang' if hold else 'flat'}, anggaran {budget:.4f} USDT, {len(p.orders)} order, "
                 f"{len(p.dilewati)} dilewati")
        for x, why in p.dilewati:
            self.log(f"  dilewati {x}: {why}")
        for o in p.orders:
            if not self.leverage_ok:
                v.set_leverage(a, 1)
                self.leverage_ok = True
            r = v.place(o)
            self.log(f"  ORDER NYATA {o.side} {o.qty:g} {a} id {o.client_id}: {r.get('status')} {r.get('_fabius', '')}".rstrip())
        diff = []
        for _ in range(3):
            diff = ex.reconcile(p.intended, {k: q for k, q in v.positions().items() if k == a}, filt)
            if not diff or not p.orders:
                break
            self.sleep(2.0)
        if diff:
            return self.stop(f"posisi canary {bar} tidak cocok sesudah order: {diff}")
        self.done = bar
        # laporan untuk SETIAP bar yang diproses (juga 0 order): penjaga luar SK-E17 menuntut laporan tiap bar terkomit; on-chain hanya isi nyata
        self.pending_feed[bar] = {"komit_s": int(cm.get("committedAt") or 0), "dilewati": list(p.dilewati), "px": {a: px}, "cid": cid, "sakelar": on}
        if p.orders:
            if self.alert is not None:
                self.alert.send(f"canary:{bar}", f"REAL TRADE canary {a} bar {bar}: {len(p.orders)} order uang nyata, posisi cocok", sekali=True)
        return f"bar {bar} canary: {len(p.orders)} order, {len(p.dilewati)} dilewati"

    @staticmethod
    def public_bars(ledger_dir: str) -> set:
        """Bar yang sudah ditulis rantai GitHub ke ledger eksekusi publik venue ini (klon repo yang sama dengan `ledger_dir`)."""
        p = os.path.join(os.path.dirname(os.path.abspath(ledger_dir)), "eksekusi", VENUE, f"{BOT}.jsonl")
        return {r.get("bar") for r in ledger.load(p)} if os.path.exists(p) else set()

    # ---------------------------------------------------------------- publikasi: umpan Gist + catatan on-chain
    def flush(self, c: dict) -> None:
        if self.venue is None:
            return
        for bar, job in sorted(self.pending_feed.items()):
            try:
                rec = xf.build_report(self.venue, VENUE, "live", BOT, bar, [c["asset"]], job["komit_s"], c["max"], job["dilewati"], self.now_ms(),
                                      job["px"])
                rec["sakelar"] = "nyala" if job.get("sakelar") else "mati"         # F-D97: ikut di-hash (reportHash on-chain)
            except Exception as e:  # noqa: BLE001
                self.note(f"canary: laporan {bar} TERTUNDA ({type(e).__name__}: {str(e)[:120]})")
                continue
            if c["feed_token"]:
                try:
                    if self.feed is None:
                        self.feed = self.feed_factory(c["feed_token"])
                    self.feed.append(rec)
                except Exception as e:  # noqa: BLE001
                    self.note(f"canary: umpan {bar} TERTUNDA ({type(e).__name__}: {str(e)[:120]})")
                    continue
            self.pending_chain[bar] = fills_of(rec, job["cid"])
            del self.pending_feed[bar]
        for bar, fills in sorted(self.pending_chain.items()):
            if not fills:
                del self.pending_chain[bar]
                continue
            if self.recorder is None:
                self.note("canary: pencatat on-chain belum dipasang - catatan isi TERTUNDA")
                return
            try:
                tx = self.recorder(fills)
                self.log(f"canary: {len(fills)} isi nyata bar {bar} dicatat on-chain (ExecutionAnchor) tx {tx}")
                del self.pending_chain[bar]
            except Exception as e:  # noqa: BLE001
                self.note(f"canary: catatan on-chain {bar} TERTUNDA ({type(e).__name__}: {str(e)[:140]})")


def chain_recorder(ev, pk: str, anchor_addr: str) -> Callable[[list], str]:
    """Pencatat on-chain: SATU tx `recordBatch` per bar dari committer. Status 0 = galat (tertunda, diulang)."""
    from evm import calldata, receipt_ok

    def rec(fills: list) -> str:
        r = ev.send(pk, anchor_addr, calldata(SIG_RECORD_BATCH, (f"{FILL_TUPLE}[]",), ([tuple(f) for f in fills],)))
        if not receipt_ok(r):
            raise RuntimeError(f"recordBatch status 0 tx {r.get('transactionHash')}")
        return r["transactionHash"]
    return rec


def anchor_address(deployments: str = sc.DEPLOYMENTS) -> Optional[str]:
    if os.environ.get("EXECUTION_ANCHOR_ADDRESS"):
        return os.environ["EXECUTION_ANCHOR_ADDRESS"]
    try:
        with open(deployments, encoding="utf-8") as f:
            return json.load(f).get("contracts", {}).get("ExecutionAnchor")
    except (OSError, ValueError):
        return None

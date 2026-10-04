"""Eksekutor venue (P118, epik 10 "Eksekusi Venue"): target tick resmi -> order di Binance USDⓈ-M, SESUDAH komitnya ada di SignalAnchor.

Dipanggil worker Railway (`tools/operator_loop.py`) di akhir tiap putaran, DIBUNGKUS SENDIRI: galat eksekutor dicatat + alert, jalur komit/ungkap tidak
tersentuh. Sejak F-D93 ia menumpang `fabius-engine` (paket gratis menolak service ketiga) - karena itu mode `live` DITOLAK di service itu.

Lingkungan:
  EXEC_MODE          off (bawaan) | dry (rencana saja, tanpa order) | demo | testnet | live
  EXEC_BOTS          B1-TREND (bawaan)
  EXEC_MODAL_USDT    modal yang dialokasikan ke bot (bawaan 2000; demo = saldo virtual). Bobot x modal = notional target.
  EXEC_MAX_LOSS      batas rugi harian ekuitas akun, pecahan (bawaan 0.05)
  EXEC_LIVE_OK       wajib untuk live: "binance:<YYYY-MM-DD>" hari ini (kata builder per hari, F-D92)
  BINANCE_API_ENV    harus cocok dengan mode (demo -> demo, testnet -> testnet, live -> prod)
  EXEC_FEED_TOKEN    token GitHub hanya-Gist (F-D94, langkah builder H7): laporan eksekusi + tanda ekuitas harian ke Gist publik -> rantai GitHub
                     menulis `ledger/eksekusi/` (P119). Tidak ada = umpan mati; eksekusi tetap jalan.

Aturan (PRD R-E1..R-E7, T8 SK-E*):
  - satu eksekusi per bar per bot; tick tanpa komit = TUNDA (tidak ada order), tick lebih tua dari kunci = dilewati selamanya;
  - leverage dipaksa 1x per simbol sebelum order pertama; akun mode hedge = TOLAK;
  - pagar menolak rencana = TOLAK; posisi sesudah order tidak cocok = TOLAK; rugi harian lewat batas = TOLAK. TOLAK = eksekutor BERHENTI (mode
    efektif dry) sampai builder me-restart worker; alert terkirim;
  - order yang gagal dikirim = dicoba putaran berikutnya; id deterministik + `place` yang mencari id dulu mencegah order ganda.
"""
from __future__ import annotations

import datetime as dt
import os
import sys
import time
from typing import Callable, Dict, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from engine import eksekusi as ex, ledger                                   # noqa: E402
from engine.spec import SPECS                                               # noqa: E402
import exec_feed as xf                                                      # noqa: E402
import signal_commit as sc                                                  # noqa: E402
import venue_binance as vb                                                  # noqa: E402

MODES = ("off", "dry", "demo", "testnet", "live")
CADANGAN = 0.002          # sama dengan kertas-venue: 0,2 % modal tidak dipakai supaya fee + slippage tidak memakan alokasi; ukuran demo = ukuran kertas
ENV_OF = {"demo": "demo", "testnet": "testnet", "live": "prod"}


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def public_bars(ledger_dir: str, venue: str, bot: str) -> set:
    """Bar yang sudah ditulis rantai GitHub ke ledger eksekusi publik (klon repo yang sama dengan `ledger_dir` = <repo>/ledger/paper)."""
    return {r.get("bar") for r in ledger.load(os.path.join(os.path.dirname(os.path.abspath(ledger_dir)), "eksekusi", venue, f"{bot}.jsonl"))}


class Executor:
    def __init__(self, env: Optional[dict] = None, log: Callable[[str], None] = print, alert=None,
                 venue_factory: Callable[[str], object] = lambda e: vb.BinanceFutures(e), today: Callable[[], str] = _today,
                 sleep: Callable[[float], None] = time.sleep, feed_factory: Callable[[str], object] = lambda token: xf.GistFeed(token),
                 now_ms: Callable[[], int] = lambda: int(time.time() * 1000)):
        self.envvars = os.environ if env is None else env
        self.log, self.alert, self.venue_factory, self.today, self.sleep = log, alert, venue_factory, today, sleep
        self.feed_factory, self.now_ms, self.feed = feed_factory, now_ms, None
        self.pending: Dict[str, dict] = {}          # laporan umpan yang belum terkirim (P119); kunci = jenis|bot|bar atau tanda|tanggal
        self.marked: Optional[str] = None
        self.backfilled = False
        self.done: Dict[str, str] = {}              # bot -> bar terakhir yang selesai dieksekusi (memori; id deterministik melindungi sesudah restart)
        self.halted: Optional[str] = None
        self.leverage_ok: set = set()
        self.day: Optional[str] = None
        self.day_equity: Optional[float] = None
        self.venue = None
        self.last_note = None

    # ---------------------------------------------------------------- konfigurasi
    def cfg(self) -> dict:
        e = self.envvars
        return {"mode": (e.get("EXEC_MODE") or "off").strip().lower(),
                "bots": [b.strip() for b in (e.get("EXEC_BOTS") or "B1-TREND").split(",") if b.strip()],
                "modal": float(e.get("EXEC_MODAL_USDT") or 2000),
                "max_loss": float(e.get("EXEC_MAX_LOSS") or 0.05),
                "live_ok": (e.get("EXEC_LIVE_OK") or "").strip(),
                "api_env": (e.get("BINANCE_API_ENV") or "testnet").strip().lower(),
                "feed_token": (e.get("EXEC_FEED_TOKEN") or "").strip(),
                "service": (e.get("RAILWAY_SERVICE_NAME") or "").strip()}

    def refuse(self, c: dict) -> Optional[str]:
        """Alasan mode ini TIDAK boleh jalan (None = boleh)."""
        if c["mode"] not in MODES:
            return f"EXEC_MODE tidak dikenal: {c['mode']}"
        if c["mode"] in ENV_OF and c["api_env"] != ENV_OF[c["mode"]]:
            return f"EXEC_MODE {c['mode']} butuh BINANCE_API_ENV={ENV_OF[c['mode']]} (sekarang {c['api_env']})"
        if c["mode"] == "live":
            if c["service"] == "fabius-engine":
                return "live DITOLAK di fabius-engine: kunci prod tidak boleh serumah dengan kunci committer (F-D93)"
            if c["live_ok"] != f"binance:{self.today()}":
                return f"live butuh EXEC_LIVE_OK=binance:{self.today()} (kata builder hari ini, F-D92)"
        return None

    def note(self, s: str) -> None:
        if s != self.last_note:
            self.log(s)
            self.last_note = s

    def stop(self, why: str) -> str:
        self.halted = why
        self.log(f"EKSEKUTOR BERHENTI: {why} - tidak ada order sampai builder me-restart worker")
        if self.alert is not None:
            self.alert.send(f"eksekutor-berhenti:{why[:40]}", f"EKSEKUTOR BERHENTI: {why}")
        return "berhenti"

    # ---------------------------------------------------------------- satu putaran
    def round(self, ledger_dir: str, cv, committer: str) -> str:
        c = self.cfg()
        if c["mode"] == "off":
            return "off"
        why = self.refuse(c)
        if why:
            self.note(f"eksekutor TIDAK jalan: {why}")
            return "tolak"
        if self.halted:
            self.flush(c)                          # laporan bar yang sudah dieksekusi tetap dipublikasikan sesudah berhenti
            return "berhenti"
        try:
            return self._round(c, ledger_dir, cv, committer)
        except vb.KeyPermissionError as e:
            return self.stop(str(e))

    def _round(self, c: dict, ledger_dir: str, cv, committer: str) -> str:
        if self.venue is None:
            self.venue = self.venue_factory(ENV_OF.get(c["mode"], c["api_env"]))
            self.venue.assert_safe_key()
            if self.venue.dual_side():
                return self.stop("akun futures dalam mode HEDGE; ubah ke one-way di UI Binance")
        v = self.venue
        eq = v.equity()
        if self.day != self.today():
            self.day, self.day_equity = self.today(), eq
        self.queue_mark(c)
        self.queue_backfill(c, ledger_dir, cv, committer)
        if ex.loss_breached(self.day_equity, eq, c["max_loss"]):
            return self.stop(f"rugi harian {100 * (self.day_equity - eq) / self.day_equity:.2f} % > {100 * c['max_loss']:.1f} %")
        out = []
        for bot in c["bots"]:
            out.append(f"{bot}: {self.bot_round(bot, c, ledger_dir, cv, committer)}")
            if self.halted:
                break
        self.flush(c)
        return "; ".join(out)

    # ---------------------------------------------------------------- umpan laporan (P119, F-D94)
    def queue_mark(self, c: dict) -> None:
        """Tanda ekuitas sekali per hari, hanya dalam 30 menit pertama sesudah 00:00Z (bahan tracking error harian)."""
        today = self.today()
        if not c["feed_token"] or c["mode"] == "dry" or self.marked == today:
            return
        self.marked = today
        if (self.now_ms() // 1000) % 86_400 <= xf.MARK_WINDOW_S:
            self.pending[f"tanda|{today}"] = {"kind": "tanda", "tanggal": today}

    def queue_backfill(self, c: dict, ledger_dir: str, cv, committer: str, days: int = 7) -> None:
        """Sekali per proses: bar terkomit lama (<= 7, tanpa bar terakhir yang diurus `bot_round`) diantre sebagai SUSULAN. Hanya bar yang order-nya
        benar-benar ditemukan di venue yang dilaporkan (lihat `flush`): bar tanpa order tidak diklaim "dieksekusi 0 order"."""
        if self.backfilled or not c["feed_token"] or c["mode"] == "dry":
            return
        self.backfilled = True
        for bot in c["bots"]:
            spec = SPECS[bot]
            ticks = sorted((r for r in ledger.load(os.path.join(ledger_dir, f"{bot}.jsonl")) if r.get("type") == "tick"), key=lambda r: r["asof"])
            for tk in ticks[-days - 1:-1]:
                asof_s = sc.asof_s_of(tk)
                locked = cv.locked_at(committer, bot, spec.sha())
                if locked == 0 or locked > asof_s:
                    continue
                cm = cv.get_commit(sc.commit_id(committer, bot, spec.sha(), asof_s))
                if int(str(cm["committer"]), 16) == 0:
                    continue
                self.pending.setdefault(f"eksekusi|{bot}|{tk['asof_date']}", {"kind": "eksekusi", "bot": bot, "bar": tk["asof_date"],
                                                                              "komit_s": int(cm.get("committedAt") or 0), "modal": c["modal"],
                                                                              "dilewati": [], "px": None, "susulan": True})

    def queue_report(self, c: dict, bot: str, bar: str, komit_s: int, p) -> None:
        if c["feed_token"] and c["mode"] != "dry":
            self.pending[f"eksekusi|{bot}|{bar}"] = {"kind": "eksekusi", "bot": bot, "bar": bar, "komit_s": komit_s, "modal": c["modal"],
                                                     "dilewati": list(p.dilewati), "px": {o.asset: o.ref_price for o in p.orders}}

    def flush(self, c: dict) -> None:
        """Kirim laporan tertunda. Gagal apa pun = tetap tertunda, dicoba putaran berikut; eksekusi TIDAK terganggu (T8 SK-E14)."""
        if not self.pending or self.venue is None:
            return
        venue = f"binance-{c['mode']}"
        try:
            if self.feed is None:
                self.feed = self.feed_factory(c["feed_token"])
            for k, job in sorted(self.pending.items()):
                if job["kind"] == "tanda":
                    rec = xf.build_mark(self.venue, venue, c["mode"], job["tanggal"], self.now_ms())
                else:
                    rec = xf.build_report(self.venue, venue, c["mode"], job["bot"], job["bar"], SPECS[job["bot"]].universe, job["komit_s"],
                                          job["modal"], job["dilewati"], self.now_ms(), job.get("px"), susulan=bool(job.get("susulan")))
                    if job.get("susulan") and not rec["orders"]:
                        del self.pending[k]
                        self.log(f"umpan eksekusi {k}: susulan tanpa order di venue - tidak dilaporkan")
                        continue
                added = self.feed.append(rec)
                del self.pending[k]
                self.log(f"umpan eksekusi {k}: {'ditambahkan' if added else 'sudah ada (idempoten)'}")
        except Exception as e:  # noqa: BLE001 - umpan tidak boleh menghentikan eksekutor
            self.note(f"umpan eksekusi TERTUNDA ({len(self.pending)}): {type(e).__name__}: {str(e)[:160]} - dicoba putaran berikut")

    def bot_round(self, bot: str, c: dict, ledger_dir: str, cv, committer: str) -> str:
        spec = SPECS[bot]
        ticks = [r for r in ledger.load(os.path.join(ledger_dir, f"{bot}.jsonl")) if r.get("type") == "tick"]
        if not ticks:
            return "belum ada tick"
        tk = max(ticks, key=lambda r: r["asof"])
        bar = tk["asof_date"]
        if self.done.get(bot) == bar:
            return f"bar {bar} sudah dieksekusi"
        if bar in public_bars(ledger_dir, f"binance-{c['mode']}", bot):
            self.done[bot] = bar                    # restart / redeploy: bar ini sudah dieksekusi + dilaporkan; mengulangnya = order telat tanpa laporan
            return f"bar {bar} sudah ada di ledger publik: tidak dieksekusi ulang"
        asof_s = sc.asof_s_of(tk)
        locked = cv.locked_at(committer, bot, spec.sha())
        if locked == 0 or locked > asof_s:
            self.done[bot] = bar
            return f"bar {bar} lebih tua dari kunci: tidak dieksekusi"
        cm = cv.get_commit(sc.commit_id(committer, bot, spec.sha(), asof_s))
        if int(str(cm["committer"]), 16) == 0:
            return f"bar {bar} TUNDA: komit belum ada di SignalAnchor (bukti dulu, order kemudian)"
        komit_s = int(cm.get("committedAt") or 0)
        v, uni = self.venue, list(spec.universe)
        targets = {a: float(w) for a, w in tk.get("targets", {}).items() if abs(float(w)) > 1e-12}
        outside = sorted(set(targets) - set(uni))
        if outside:
            return self.stop(f"target {bot} bar {bar} memuat aset di luar universe spesifikasi: {outside}")
        filt = v.filters(uni)
        book = v.book(uni)
        px = {a: (b + k) / 2 for a, (b, k) in book.items()}
        pos = {a: q for a, q in v.positions().items() if a in uni}
        p = ex.plan(f"binance-{c['mode']}", bot, bar, targets, c["modal"] * (1 - CADANGAN), pos, px, filt)
        problems = ex.guard(p, modal=c["modal"], universe=uni, price=px, long_only=bool(spec.konstanta.get("long_only")))
        if problems:
            return self.stop(f"pagar menolak rencana {bot} {bar}: {problems[:3]}")
        self.log(f"eksekutor {c['mode']} {bot} bar {bar}: {len(p.orders)} order, {len(p.dilewati)} dilewati, modal {c['modal']:g}")
        for a, why in p.dilewati:
            self.log(f"  dilewati {a}: {why}")
        if c["mode"] == "dry":
            for o in p.orders:
                self.log(f"  RENCANA {o.side} {o.qty:g} {o.asset} (~{o.notional:.2f}, {o.alasan}, id {o.client_id})")
            self.done[bot] = bar
            return f"bar {bar} dry: {len(p.orders)} order direncanakan"
        failed = 0
        for o in p.orders:
            try:
                if o.asset not in self.leverage_ok:
                    v.set_leverage(o.asset, 1)
                    self.leverage_ok.add(o.asset)
                r = v.place(o)
                self.log(f"  ORDER {o.side} {o.qty:g} {o.asset} id {o.client_id}: {r.get('status')} {r.get('_fabius', '')}".rstrip())
            except vb.VenueError as e:
                failed += 1
                self.log(f"  order {o.client_id} GAGAL: {e} - dicoba putaran berikut (id sama, tidak ganda)")
        if failed:
            return f"bar {bar}: {failed} order gagal, diulang putaran berikut"
        diff = []
        for attempt in range(3):                    # order pasar kadang baru tercermin di posisi sedetik kemudian: jangan berhenti karena itu
            actual = {a: q for a, q in v.positions().items() if a in uni}
            diff = ex.reconcile(p.intended, actual, filt)
            if not diff or not p.orders:
                break
            self.sleep(2.0)
        if diff:
            return self.stop(f"posisi {bot} bar {bar} tidak cocok sesudah order: {diff[:3]}")
        self.done[bot] = bar
        self.queue_report(c, bot, bar, komit_s, p)
        if self.alert is not None:
            self.alert.send(f"eksekusi:{c['mode']}:{bot}:{bar}", f"eksekusi {c['mode'].upper()} {bot} bar {bar}: {len(p.orders)} order, "
                                                               f"{len(p.dilewati)} dilewati, posisi cocok", sekali=True)
        return f"bar {bar} dieksekusi: {len(p.orders)} order, posisi cocok"

"""P119 (epik 10 R-E10, F-D94): umpan laporan eksekusi (tools/exec_feed.py + eksekutor) dan penulis ledger eksekusi (tools/eksekusi_ledger.py).
Venue, Gist, dan chain dipalsukan; tidak ada jaringan."""
import json
import os
import shutil
import sys
import tempfile
import unittest

from engine import eksekusi as ex, ledger
from engine.tests.test_eksekutor import BAR, COMMITTER, DEMO, FakeAlert, FakeChain, FakeVenue

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import eksekusi_ledger as el                                              # noqa: E402
import eksekutor as ek                                                    # noqa: E402
import exec_feed as xf                                                    # noqa: E402

COMMIT_S = 1_791_017_100                     # 2026-10-03T08:45:00Z: komit bar 2026-10-02
T_ORDER = (COMMIT_S + 120) * 1000
MIDNIGHT_10_04 = 1_791_072_000_000


class FeedVenue(FakeVenue):
    """FakeVenue yang menyimpan order seperti Binance: dicari lewat clientOrderId, isi + fee lewat userTrades."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.by_id = {}

    def place(self, o):
        r = super().place(o)
        if o.client_id not in self.by_id:
            self.by_id[o.client_id] = {"orderId": 1000 + len(self.by_id), "status": "FILLED", "executedQty": str(o.qty), "avgPrice": "100.05",
                                       "time": T_ORDER, "updateTime": T_ORDER + 300, "reduceOnly": o.reduce_only, "symbol": o.asset, "q": o.qty}
        return r

    def order_by_client_id(self, sym, cid):
        return self.by_id.get(cid)

    def user_trades(self, sym, oid):
        o = next(x for x in self.by_id.values() if x["orderId"] == oid)
        n = o["q"] * 100.05
        return [{"commission": f"{n * 0.0002:.8f}", "commissionAsset": "USDT"}, {"commission": f"{n * 0.0002:.8f}", "commissionAsset": "USDT"}]


class FakeGist:
    """API Gist palsu: GET /gists (milik token), POST /gists, GET/PATCH /gists/{id}."""

    def __init__(self, fail=False):
        self.gists, self.fail, self.calls = {}, fail, []

    def __call__(self, method, url, headers, body=None):
        self.calls.append((method, url, headers.get("Authorization", "")))
        if self.fail:
            raise OSError("jaringan putus")
        path = url.replace(xf.API, "")
        if method == "GET" and path.startswith("/gists?"):
            return 200, [{"id": k, "description": g["description"]} for k, g in self.gists.items()]
        if method == "POST" and path == "/gists":
            d = json.loads(body)
            self.gists["g1"] = {"description": d["description"], "files": {n: {"content": f["content"]} for n, f in d["files"].items()}}
            return 201, {"id": "g1", "html_url": "https://gist.github.com/g1"}
        gid = path.split("/")[2]
        if method == "GET":
            return 200, self.gists[gid]
        if method == "PATCH":
            for n, f in json.loads(body)["files"].items():
                self.gists[gid]["files"][n] = {"content": f["content"]}
            return 200, {}
        return 404, {}

    def lines(self):
        return [x for f, v in sorted(self.gists.get("g1", {"files": {}})["files"].items()) if f.endswith(".jsonl") for x in v["content"].splitlines()]


class LedgerChain:
    def __init__(self, committed_at=COMMIT_S):
        self.committed_at = committed_at

    def get_commit(self, cid):
        if self.committed_at is None:
            return {"committer": "0x" + "00" * 20, "committedAt": 0}
        return {"committer": "0x" + "11" * 20, "committedAt": self.committed_at}


class FeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        with open(os.path.join(self.tmp, "B1-TREND.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "tick", "asof": BAR, "asof_date": "2026-10-02", "targets": {"BTCUSDT": 0.5, "ETHUSDT": 0.5}}) + "\n")
        self.logs = []

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def executor(self, venue, gist, env=None, now_ms=T_ORDER):
        return ek.Executor(env=dict(DEMO, EXEC_FEED_TOKEN="ghp_rahasia", **(env or {})), log=self.logs.append, alert=FakeAlert(),
                           venue_factory=lambda e: venue, today=lambda: "2026-10-03", sleep=lambda s: None,
                           feed_factory=lambda tok: xf.GistFeed(tok, http=gist, log=self.logs.append), now_ms=lambda: now_ms)

    def test_report_is_rebuilt_from_the_venue_by_deterministic_ids_and_published_once(self):
        v, g = FeedVenue(), FakeGist()
        e = self.executor(v, g)
        self.assertIn("posisi cocok", e.round(self.tmp, FakeChain(), COMMITTER))
        self.assertEqual(len(g.lines()), 1)
        rec = json.loads(g.lines()[0])
        self.assertEqual((rec["type"], rec["venue"], rec["bot"], rec["bar"], len(rec["orders"])), ("eksekusi", "binance-demo", "B1-TREND", "2026-10-02", 2))
        o = rec["orders"][0]
        self.assertEqual(o["id"], ex.client_id("binance-demo", "B1-TREND", "2026-10-02", o["aset"], "BUY"))
        self.assertAlmostEqual(o["fee"], 2 * 4.99 * 100.05 * 0.0002, places=6)
        self.assertEqual(o["px_rencana"], 100.0)
        # restart: memori hilang, laporan disusun ulang dari venue -> isi sama, baris TIDAK ganda (idempoten)
        e2 = self.executor(v, g)
        e2.round(self.tmp, FakeChain(), COMMITTER)
        self.assertEqual(len(g.lines()), 1)
        self.assertTrue(any("sudah ada (idempoten)" in x for x in self.logs))
        self.assertFalse(any("ghp_rahasia" in x for x in self.logs))

    def test_feed_down_keeps_the_report_pending_and_never_disturbs_execution(self):
        v, g = FeedVenue(), FakeGist(fail=True)
        e = self.executor(v, g)
        self.assertIn("dieksekusi: 2 order, posisi cocok", e.round(self.tmp, FakeChain(), COMMITTER))
        self.assertIsNone(e.halted)
        self.assertEqual(list(e.pending), ["eksekusi|B1-TREND|2026-10-02"])
        self.assertTrue(any("umpan eksekusi TERTUNDA" in x for x in self.logs))
        g.fail = False
        e.round(self.tmp, FakeChain(), COMMITTER)
        self.assertEqual(e.pending, {})
        self.assertEqual(len(g.lines()), 1)

    def test_a_refused_gist_write_says_why_without_leaking_the_token(self):
        g = FakeGist()
        real = g.__call__

        def refuse_create(method, url, headers, body=None):
            if method == "POST":
                return 403, {"message": "Resource not accessible by personal access token"}
            return real(method, url, headers, body)
        e = self.executor(FeedVenue(), refuse_create)
        e.round(self.tmp, FakeChain(), COMMITTER)
        msg = next(x for x in self.logs if "TERTUNDA" in x)
        self.assertIn("HTTP 403 'Resource not accessible by personal access token'", msg)
        self.assertNotIn("ghp_rahasia", " ".join(self.logs))
        self.assertIn("eksekusi|B1-TREND|2026-10-02", e.pending)

    def test_backfill_reports_only_old_bars_whose_orders_exist_and_blanks_their_positions(self):
        v = FeedVenue()
        ek.Executor(env=DEMO, log=lambda s: None, venue_factory=lambda env: v, today=lambda: "2026-10-03", sleep=lambda s: None).round(
            self.tmp, FakeChain(), COMMITTER)                                            # bar 10-02 dieksekusi SEBELUM umpan menyala
        with open(os.path.join(self.tmp, "B1-TREND.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"type": "tick", "asof": BAR + 86_400_000, "asof_date": "2026-10-03", "targets": {"BTCUSDT": 0.5, "ETHUSDT": 0.5}}) + "\n")
        g = FakeGist()
        self.executor(v, g).round(self.tmp, FakeChain(), COMMITTER)                     # umpan menyala: bar terakhir 10-03 + susulan 10-02
        recs = {json.loads(x)["bar"]: json.loads(x) for x in g.lines()}
        self.assertEqual(sorted(recs), ["2026-10-02", "2026-10-03"])
        old, new = recs["2026-10-02"], recs["2026-10-03"]
        self.assertEqual((old["susulan"], old["posisi"], old["ekuitas"], len(old["orders"])), (True, None, None, 2))
        self.assertEqual((new.get("susulan"), len(new["orders"])), (None, 0))           # posisi sudah selaras: 0 order, tetap dilaporkan
        g2 = FakeGist()
        self.executor(FeedVenue(), g2).round(self.tmp, FakeChain(), COMMITTER)          # venue tanpa order 10-02: susulan TIDAK diklaim
        self.assertEqual(sorted(json.loads(x)["bar"] for x in g2.lines()), ["2026-10-03"])

    def test_no_token_means_no_feed_and_marks_only_right_after_midnight(self):
        v, g = FeedVenue(), FakeGist()
        e = ek.Executor(env=DEMO, log=self.logs.append, venue_factory=lambda env: v, today=lambda: "2026-10-03", sleep=lambda s: None,
                        feed_factory=lambda tok: 1 / 0)
        e.round(self.tmp, FakeChain(), COMMITTER)
        self.assertEqual((e.pending, g.calls), ({}, []))
        late = self.executor(FeedVenue(), FakeGist(), now_ms=MIDNIGHT_10_04 - 86_400_000 + 3 * 3600_000)       # 03:00Z: tidak ada tanda
        late.round(self.tmp, FakeChain(committed=False), COMMITTER)
        self.assertNotIn("tanda|2026-10-03", late.pending)
        g2 = FakeGist()
        early = self.executor(FeedVenue(), g2, now_ms=MIDNIGHT_10_04 - 86_400_000 + 5 * 60_000)              # 00:05Z: tanda ditulis
        early.round(self.tmp, FakeChain(committed=False), COMMITTER)
        self.assertEqual([json.loads(x)["type"] for x in g2.lines()], ["tanda"])


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.paper, self.out, self.kertas = (os.path.join(self.tmp, d) for d in ("paper", "eksekusi", "kertas"))
        os.makedirs(self.paper)
        prev = {"type": "tick", "asof": BAR - 86_400_000, "asof_date": "2026-10-01", "targets": {}, "h": "0xaa"}
        tick = {"type": "tick", "asof": BAR, "asof_date": "2026-10-02", "targets": {"BTCUSDT": 0.5, "ETHUSDT": 0.5}, "h": "0xbb"}
        with open(os.path.join(self.paper, "B1-TREND.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps(prev) + "\n" + json.dumps(tick) + "\n")
        os.makedirs(os.path.join(self.kertas, "binance"))
        with open(os.path.join(self.kertas, "binance", "B1-TREND-1000-komit.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"bar": "2026-10-02", "status": "DIEKSEKUSI", "orders": [{"aset": "BTCUSDT", "sisi": "BUY", "px": 100.01}]}) + "\n")
        self.close = lambda a, t: {BAR: 100.0, BAR + 86_400_000: 101.0}[t]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def feed_line(self, **over):
        v, g = FeedVenue(), FakeGist()
        e = ek.Executor(env=dict(DEMO, EXEC_FEED_TOKEN="t"), log=lambda s: None, venue_factory=lambda env: v, today=lambda: "2026-10-03",
                        sleep=lambda s: None, feed_factory=lambda tok: xf.GistFeed(tok, http=g, log=lambda s: None), now_ms=lambda: T_ORDER)
        with open(os.path.join(self.tmp, "B1-TREND.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "tick", "asof": BAR, "asof_date": "2026-10-02", "targets": {"BTCUSDT": 0.5, "ETHUSDT": 0.5}}) + "\n")
        e.round(self.tmp, FakeChain(), COMMITTER)
        rec = json.loads(g.lines()[0])
        rec.update(over)
        return json.dumps(rec)

    def run_lines(self, lines, chain=None):
        return el.run(lines, chain or LedgerChain(), COMMITTER, self.close, out_dir=self.out, paper_dir=self.paper, kertas_dir=self.kertas, log=lambda s: None)

    def test_a_clean_report_is_written_with_metrics_computed_here(self):
        n, alarms = self.run_lines([self.feed_line()])
        self.assertEqual((n, alarms), (1, []))
        r = ledger.load(el.path_of("binance-demo", "B1-TREND", self.out))[0]
        self.assertEqual((r["n_order"], r["pelanggaran"], r["komit_utc"], r["latensi_s"]), (2, [], "2026-10-03T08:45:00Z", 120))
        btc = next(o for o in r["orders"] if o["aset"] == "BTCUSDT")
        self.assertAlmostEqual(btc["fee_bps"], 4.0, places=3)                     # 2 isi x 2 bps
        self.assertAlmostEqual(btc["geser_bps"], 5.0, places=3)                   # 100,05 vs penutupan 100: beli lebih mahal = +5
        self.assertAlmostEqual(btc["slip_bps"], 5.0, places=3)                    # vs harga tengah rencana 100
        self.assertAlmostEqual(btc["selisih_kertas_bps"], 4.0, places=2)          # vs isi kertas 100,01
        self.assertEqual(self.run_lines([self.feed_line()]), (0, []))             # baris sama lagi = tidak ditulis ulang
        self.assertEqual(el.verify(ledger.load(el.path_of("binance-demo", "B1-TREND", self.out))), [])

    def test_forged_ids_are_rejected_and_orders_before_the_commit_are_disclosed(self):
        rec = json.loads(self.feed_line())
        rec["orders"][0]["id"] = "fx" + "0" * 30
        n, alarms = self.run_lines([json.dumps(rec)])
        self.assertEqual(n, 0)
        self.assertIn("DITOLAK", alarms[0])
        n, alarms = self.run_lines([self.feed_line()], chain=LedgerChain(committed_at=COMMIT_S + 3600))   # komit SESUDAH order
        self.assertEqual(n, 1)
        self.assertIn("PELANGGARAN", alarms[0])
        r = ledger.load(el.path_of("binance-demo", "B1-TREND", self.out))[0]
        self.assertEqual(len(r["pelanggaran"]), 2)
        self.assertIn("SEBELUM komit", r["pelanggaran"][0])

    def test_verify_catches_tampering_and_the_outside_watch_alarms_after_an_hour(self):
        self.run_lines([self.feed_line()])
        p = el.path_of("binance-demo", "B1-TREND", self.out)
        recs = ledger.load(p)
        recs[0]["fee"] = 0.0
        self.assertIn("rantai hash putus", el.verify(recs)[0])
        os.remove(p)
        with open(p, "w", encoding="utf-8") as f:                                       # ledger aktif, tetapi bar terakhir belum dilaporkan
            f.write(json.dumps(ledger.seal({"type": "eksekusi", "bar": "2026-10-01"}, ledger.ZERO)) + "\n")
        code, rows = el.periksa(LedgerChain(), COMMITTER, COMMIT_S + 600, out_dir=self.out, paper_dir=self.paper)
        self.assertEqual(code, 2)
        code, rows = el.periksa(LedgerChain(), COMMITTER, COMMIT_S + 3700, out_dir=self.out, paper_dir=self.paper)
        self.assertEqual(code, 1)
        self.assertIn("tanpa laporan eksekusi", rows[0])

    def test_the_outside_watch_spares_the_real_money_venue_only_when_the_switch_is_off_and_the_last_position_is_flat(self):
        p = el.path_of("binance-live", "B1-TREND", self.out)
        os.makedirs(os.path.dirname(p))

        def last_row(posisi):
            with open(p, "w", encoding="utf-8") as f:
                print(json.dumps(ledger.seal({"type": "eksekusi", "venue": "binance-live", "bar": "2026-10-01", "posisi": posisi}, ledger.ZERO)), file=f)

        def watch(on):
            return el.periksa(LedgerChain(), COMMITTER, COMMIT_S + 3700, out_dir=self.out, paper_dir=self.paper, sakelar=lambda d: on)
        last_row({"XRPUSDT": 0.0})
        code, rows = watch(False)
        self.assertEqual(code, 0)
        self.assertIn("sakelar uang nyata MATI", rows[0])
        self.assertEqual(watch(True)[0], 1)                                             # sakelar nyala: laporan tiap bar dituntut
        last_row({"XRPUSDT": 0.099})
        self.assertEqual(watch(False)[0], 1)                                            # mati tetapi posisi masih terbuka: penutupan dituntut
        last_row(None)
        self.assertEqual(watch(False)[0], 1)                                            # posisi tak diketahui = tetap dituntut

    def test_tracking_error_uses_midnight_marks_and_late_marks_are_kept_but_not_used(self):
        def mark(day, eq, minutes=3):
            t = ledger.iso_ms(f"{day}T00:00:00Z") + minutes * 60_000
            return json.dumps({"v": 1, "type": "tanda", "venue": "binance-demo", "mode": "demo", "tanggal": day, "t_ms": t, "ekuitas": eq, "posisi": {}})
        self.run_lines([self.feed_line(), mark("2026-10-03", 5000.0), mark("2026-10-04", 5009.0)])
        marks = ledger.load(el.path_of("binance-demo", "tanda", self.out))
        recs = ledger.load(el.path_of("binance-demo", "B1-TREND", self.out))
        te = el.tracking(recs, marks, self.close, paper_dir=self.paper)
        self.assertEqual(len(te), 1)
        self.assertAlmostEqual(te[0]["ret_eksekusi"], 9.0 / 1000)                       # Δekuitas / modal 1000
        self.assertAlmostEqual(te[0]["ret_paper"], 0.01 - 1.0 * 7 / 1e4)                # 1 % naik, turnover 1 x 7 bps
        self.run_lines([mark("2026-10-05", 5010.0, minutes=90)])
        late = ledger.load(el.path_of("binance-demo", "tanda", self.out))[-1]
        self.assertFalse(late["dipakai"])

    def test_missing_feed_is_not_an_error_and_unreachable_feed_is_unreadable(self):
        self.assertEqual(el.read_feed(get=lambda u, t: (200, []), gist_id=None), (None, []))       # id tak diketahui + gist belum ada
        def boom(u, t):
            raise el.Unreadable("tak terjangkau")
        with self.assertRaises(el.Unreadable):
            el.read_feed(get=boom, gist_id=None)
        # id dipatok: isi dibaca dari URL raw per bulan, tanpa token; bulan yang belum punya berkas (404) dilewati, galat lain = tak terbaca
        seen = []
        def raw(url):
            seen.append(url)
            return (200, '{"a":1}\n\n{"b":2}\n') if url.endswith("fabius-exec-2026-10.jsonl") else (404, "")
        gid, lines = el.read_feed(gist_id="g1", get_text=raw, now_ms=MIDNIGHT_10_04 + 40 * 86_400_000, get=lambda u, t: 1 / 0)
        self.assertEqual((gid, lines), ("g1", ['{"a":1}', '{"b":2}']))
        self.assertEqual([u[-13:-6] for u in seen], ["2026-10", "2026-11"])
        self.assertTrue(seen[0].startswith("https://gist.githubusercontent.com/Shenhan01-sys/g1/raw/"))
        with self.assertRaises(el.Unreadable):
            el.read_feed(gist_id="g1", get_text=lambda u: (500, ""), now_ms=MIDNIGHT_10_04)


if __name__ == "__main__":
    unittest.main()

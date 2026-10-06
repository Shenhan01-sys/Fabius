"""Jangkar tes tabel semantik kegagalan pipeline operator (P109; vault/07-Testing/T8 - Semantik Kegagalan Operator.md).

Tiap tes di sini menutup baris tabel yang sebelumnya hanya punya jangkar kode: arah kegagalannya (TUNDA / TOLAK / PERTAHANKAN / UNGKAPKAN) diuji, bukan
diandaikan. Yang paling penting kelasnya sama: GAGAL MEMBACA tidak boleh terbaca sebagai "tidak ada" (jawaban RPC kosong != belum ada komit; rentang log
yang ditolak != tidak ada pengungkapan)."""
import os
import shutil
import socket
import sys
import tempfile
import types
import unittest

from engine import ledger
from engine.spec import SPECS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import paper_tick as pt                                             # noqa: E402
import signal_commit as sc                                          # noqa: E402

from .test_signal_commit import B3_ASOF_S, BARS, COMMITTER, DEV_PK1, LEDGER, FakeChain, HAVE_ETH     # noqa: E402
from .test_paper_tick import quiet, rd                                                                # noqa: E402


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class LedgerWriterTests(unittest.TestCase):
    def test_broken_chain_writes_nothing(self):
        """Rantai yang disunting tanpa seal ulang: putaran harian keluar 3 dan berkasnya tidak bertambah satu byte pun (TOLAK)."""
        tmp = tempfile.mkdtemp()
        try:
            src = rd(os.path.join(LEDGER, "B1-TREND.jsonl"), "r").splitlines()
            src[1] = src[1][:-1] + ',"x":1}'                         # catatan kedua disunting, hash-nya tidak dihitung ulang
            p = os.path.join(tmp, "B1-TREND.jsonl")
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(src) + "\n")
            before = rd(p)
            rc, out = quiet(pt.tick_bot, "B1-TREND", tmp, pt.Views(BARS), ledger.iso_ms("2026-10-03T11:00:00Z"), False)
            self.assertEqual(rc, 3, out)
            self.assertIn("TIDAK sah", out)
            self.assertEqual(rd(p), before)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class PlanRefusalTests(unittest.TestCase):
    def test_ledger_spec_differs_from_worker_code_is_alarm(self):
        """Image worker basi (kode bot beda dari genesis ledger): ALARM, tidak ada yang dikomit (TOLAK)."""
        orig = sc.SPECS
        sc.SPECS = dict(orig)
        sc.SPECS["B3-CARRY"] = types.SimpleNamespace(sha=lambda: "0x" + "11" * 32, bot_id="B3-CARRY")
        try:
            acts = sc.plan(["B3-CARRY"], LEDGER, pt.Views(BARS), FakeChain(), COMMITTER, sc.seed_from_key(DEV_PK1), B3_ASOF_S + 36_000)
        finally:
            sc.SPECS = orig
        self.assertEqual([a.kind for a in acts], ["alarm"])
        self.assertIn("image basi", acts[0].detail)


@unittest.skipUnless(HAVE_ETH, "eth-account tidak terpasang")
class EvmReadTests(unittest.TestCase):
    def fake(self, answers, **kw):
        import evm

        class E(evm.Evm):
            def rpc(self, method, params):
                v = answers[method]
                return v(params) if callable(v) else v
        return E(["http://127.0.0.1:1"], 97, **kw)

    def test_all_endpoints_down_is_an_error_not_an_empty_answer(self):
        import evm
        ev = evm.Evm([f"http://127.0.0.1:{_free_port()}", f"http://127.0.0.1:{_free_port()}"], 97, timeout=2)
        with self.assertRaises(RuntimeError) as cm:
            ev.rpc("eth_chainId", [])
        self.assertIn("gagal di 2 endpoint", str(cm.exception))

    def test_empty_call_answer_raises_instead_of_reading_as_no_commit(self):
        """`eth_call` yang menjawab "0x" (alamat salah, node belum sinkron) TIDAK boleh didekode sebagai komit kosong -> worker mengomit ulang."""
        ev = self.fake({"eth_call": "0x"})
        cv = sc.AnchorView(ev, "0x" + "22" * 20, "0x" + "33" * 20)
        with self.assertRaises(RuntimeError) as cm:
            cv.get_commit(b"\x01" * 32)
        self.assertIn("jawaban kosong", str(cm.exception))

    def test_wrong_chain_id_stops_before_sending(self):
        with self.assertRaises(RuntimeError) as cm:
            self.fake({"eth_chainId": hex(56)}).chain_check()
        self.assertIn("berhenti sebelum mengirim", str(cm.exception))

    def test_pending_transaction_sends_nothing(self):
        fc = FakeChain()
        fc.lock("B3-CARRY", B3_ASOF_S - 3600)
        acts = sc.plan(["B3-CARRY"], LEDGER, pt.Views(BARS), fc, COMMITTER, sc.seed_from_key(DEV_PK1), B3_ASOF_S + 36_000)
        self.assertTrue(any(a.kind == "commit" and a.batch is not None for a in acts))
        sent = []
        ev = types.SimpleNamespace(has_pending=lambda addr: True, send=lambda *a, **k: sent.append(a))
        logs = []
        st = sc.execute(acts, ev, "0x" + "22" * 20, DEV_PK1, log=logs.append)
        self.assertEqual((st, sent), ({"commit": 0, "reveal": 0, "gagal": 0}, []))
        self.assertIn("tertunda", logs[0])

    def test_receipt_that_never_arrives_raises_instead_of_resending(self):
        ev = self.fake({"eth_estimateGas": hex(50_000), "eth_getTransactionCount": "0x0", "eth_gasPrice": hex(10**9),
                        "eth_sendRawTransaction": "0x" + "ab" * 32, "eth_getTransactionReceipt": None}, receipt_wait_s=0.3, poll_s=0.1)
        with self.assertRaises(RuntimeError) as cm:
            ev.send(DEV_PK1, "0x" + "22" * 20, b"\x00")
        self.assertIn("belum masuk blok", str(cm.exception))


@unittest.skipUnless(HAVE_ETH, "eth-account tidak terpasang")
class WorkerRoundTests(unittest.TestCase):
    def test_sync_failure_plans_and_sends_nothing_and_the_worker_survives(self):
        import operator_loop as ol
        planned, got = [], []

        def broken(workdir=None):
            raise RuntimeError("git fetch gagal (128): jaringan")
        orig = (ol.sync, ol.sc.plan, ol.log)
        ol.sync, ol.sc.plan, ol.log = broken, (lambda *a, **k: planned.append(a) or []), got.append
        try:
            ok = ol.guarded_round(ol.Worker(workdir=tempfile.gettempdir()))
        finally:
            ol.sync, ol.sc.plan, ol.log = orig
        self.assertFalse(ok)
        self.assertEqual(planned, [])
        self.assertTrue(got and got[0].startswith("putaran GAGAL: RuntimeError"), got)


BOOK = os.path.join(ROOT, "ledger", "book", "buku.jsonl")


def tampered_copy(src, dst):
    lines = rd(src, "r").splitlines()
    lines[-1] = lines[-1][:-1] + ',"x":1}'                          # catatan terakhir disunting, hash tidak dihitung ulang
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


class BookEpochTests(unittest.TestCase):
    """P108: rantai GitHub menjalankan `book epoch --write` tiap hari sesudah tick; hanya hari pertama epoch baru yang menulis."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.f = os.path.join(self.tmp, "buku.jsonl")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def epoch(self, now):
        from engine import cli
        return quiet(cli.main, ["book", "epoch", "--write", "--no-gates", "--file", self.f, "--now", now])

    def test_invalid_book_writes_no_epoch(self):
        tampered_copy(BOOK, self.f)
        before = rd(self.f)
        rc, out = self.epoch("2026-10-04T09:30:00Z")
        self.assertEqual(rc, 1, out)
        self.assertIn("TIDAK SAH", out)
        self.assertEqual(rd(self.f), before)

    def test_new_epoch_is_written_once_then_left_alone(self):
        shutil.copy(BOOK, self.f)
        rc, out = self.epoch("2026-10-04T09:30:00Z")
        self.assertEqual(rc, 0, out)
        once = rd(self.f)
        self.assertEqual(len(once.splitlines()), 3)
        rc, out = self.epoch("2026-10-05T09:30:00Z")
        self.assertEqual((rc, rd(self.f)), (0, once))
        self.assertIn("tidak menulis dua kali", out)


class FakeRegistry:
    def __init__(self, locked=0, pending=False, fail_read=False):
        self.locked, self.pending, self.fail_read, self.sent = locked, pending, fail_read, []

    def call_decode(self, to, sig, types, values, out):
        if self.fail_read:
            raise RuntimeError("RPC eth_call gagal di 3 endpoint")
        return (self.locked,)

    def has_pending(self, addr):
        return self.pending

    def send(self, pk, to, data):
        self.sent.append(data)
        return {"status": "0x1", "transactionHash": "0x" + "ab" * 32, "blockNumber": "0x10"}

    @staticmethod
    def num(h):
        return int(h, 16) if h else 0


@unittest.skipUnless(HAVE_ETH, "eth-abi tidak terpasang")
class WorkerBookPinTests(unittest.TestCase):
    """P108: worker mem-pin book_sha epoch baru yang ditulis rantai GitHub."""

    def setUp(self):
        import operator_loop as ol
        self.ol = ol
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, "ledger", "book"))
        self.f = os.path.join(self.tmp, "ledger", "book", "buku.jsonl")
        shutil.copy(BOOK, self.f)
        self.logs = []
        self.orig = ol.log
        ol.log = self.logs.append
        self.w = ol.Worker(workdir=self.tmp)

    def tearDown(self):
        self.ol.log = self.orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def pin(self, ev, pk=DEV_PK1, pin=True):
        return self.w.book_pin(ev, "0x" + "33" * 20, COMMITTER, pk, "f" * 40, pin=pin)

    def test_book_pin_sends_once_and_never_twice(self):
        ev = FakeRegistry()
        self.assertEqual(self.pin(ev), "kirim")
        self.assertEqual(len(ev.sent), 1)
        recs = ledger.load(self.f)
        self.assertIn(b"FABIUS-BUKU-E" + str(recs[-1]["epoch"]).encode(), ev.sent[0])
        self.assertIn(bytes.fromhex(recs[-1]["book_sha"][2:]), ev.sent[0])
        ev.locked = 1_790_961_969
        self.assertEqual(self.pin(ev), "ok")
        self.assertEqual(len(ev.sent), 1)

    def test_failed_lockedat_read_is_not_read_as_unpinned(self):
        ev = FakeRegistry(fail_read=True)
        self.assertEqual(self.pin(ev), "tunda")
        self.assertEqual(ev.sent, [])
        self.assertIn("GAGAL dibaca", self.logs[-1])

    def test_tampered_book_is_not_pinned(self):
        tampered_copy(BOOK, self.f)
        ev = FakeRegistry()
        self.assertEqual(self.pin(ev), "tolak")
        self.assertEqual(ev.sent, [])
        self.assertIn("TIDAK SAH", self.logs[-1])

    def test_pin_off_or_no_key_only_reports(self):
        ev = FakeRegistry()
        self.assertEqual(self.pin(ev, pin=False), "perlu")
        self.assertEqual(self.pin(ev, pk=None), "perlu")
        self.assertEqual(ev.sent, [])
        self.assertIn("PERLU pin", self.logs[-1])

    def test_pending_transaction_postpones_the_pin(self):
        ev = FakeRegistry(pending=True)
        self.assertEqual(self.pin(ev), "tunda")
        self.assertEqual(ev.sent, [])


@unittest.skipUnless(HAVE_ETH, "eth-abi tidak terpasang")
class WorkerSpecPinTests(unittest.TestCase):
    """P161 B1b: worker mem-pin spec_sha bot penerbit yang LOLOS_SHADOW di registri; yang tidak cocok registri tidak di-pin."""

    def setUp(self):
        import json
        import operator_loop as ol
        from engine import anggaran, registri
        self.ol = ol
        self.tmp = tempfile.mkdtemp()
        d = os.path.join(self.tmp, "ledger", "pengajuan")
        os.makedirs(os.path.join(d, "spec"))
        e = {"type": "pengajuan", "t_s": 1_791_000_000, "t_utc": "-", "issuer": "0x" + "a" * 40, "payout": "0x" + "a" * 40, "bot_id": "TREND-ETH-30",
             "submission_sha": "0x" + "11" * 32, "spec_sha": "0x" + "22" * 32, "fingerprint": "0x3", "report_sha": "0x4", "vonis": registri.LOLOS, "k": 1,
             "alpha": anggaran.alpha_for(1), "n_trials": 1}
        with open(os.path.join(d, "registri.jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps(ledger.seal(e, ledger.head([])), sort_keys=True) + "\n")
        self.spec = os.path.join(d, "spec", "TREND-ETH-30.json")
        with open(self.spec, "w", encoding="utf-8") as f:
            json.dump({"bot_id": "TREND-ETH-30", "submission_sha": e["submission_sha"], "spec_sha": e["spec_sha"], "t_lolos": e["t_s"]}, f)
        self.logs = []
        self.orig = ol.log
        ol.log = self.logs.append
        self.w = ol.Worker(workdir=self.tmp)

    def tearDown(self):
        self.ol.log = self.orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def pin(self, ev, pk=DEV_PK1, pin=True):
        return self.w.spec_pin(ev, "0x" + "33" * 20, COMMITTER, pk, "f" * 40, pin=pin)

    def test_a_registered_spec_is_pinned_once_under_its_bot_id(self):
        ev = FakeRegistry()
        self.assertEqual(self.pin(ev), "kirim")
        self.assertIn(b"TREND-ETH-30", ev.sent[0])
        self.assertIn(bytes.fromhex("22" * 32), ev.sent[0])
        ev.locked = 1_791_000_100
        self.assertEqual(self.pin(ev), "ok")
        self.assertEqual(len(ev.sent), 1)

    def test_a_spec_that_does_not_match_the_registry_is_never_pinned(self):
        import json
        with open(self.spec, "w", encoding="utf-8") as f:
            json.dump({"bot_id": "TREND-ETH-30", "submission_sha": "0x" + "11" * 32, "spec_sha": "0x" + "99" * 32, "t_lolos": 1}, f)
        ev = FakeRegistry()
        self.assertEqual(self.pin(ev), "kosong")
        self.assertEqual(ev.sent, [])

    def test_unreadable_lock_state_waits(self):
        self.assertEqual(self.pin(FakeRegistry(fail_read=True)), "tunda")


@unittest.skipUnless(HAVE_ETH, "eth-abi tidak terpasang")
class VerifierReadTests(unittest.TestCase):
    def test_rejected_log_range_is_halved_then_raised_never_read_as_no_reveals(self):
        import evm
        import verify_signals as vs
        spans = []

        def rpc_limit(limit):
            def rpc(method, params):
                lo, hi = int(params[0]["fromBlock"], 16), int(params[0]["toBlock"], 16)
                spans.append(hi - lo + 1)
                if hi - lo + 1 > limit:
                    raise evm.RpcError("block range too large")
                return []
            return types.SimpleNamespace(rpc=rpc)

        self.assertEqual(vs.revealed_events(rpc_limit(1500), "0x" + "22" * 20, 0, 9_999, chunk=5000), {})
        self.assertEqual(spans[:3], [5000, 2500, 1250])
        spans.clear()
        with self.assertRaises(evm.RpcError):
            vs.revealed_events(rpc_limit(10), "0x" + "22" * 20, 0, 9_999, chunk=5000)
        self.assertLessEqual(min(spans), 100)


if __name__ == "__main__":
    unittest.main()

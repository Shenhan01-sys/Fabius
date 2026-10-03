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

"""P111: penjaga luar worker (tools/worker_watch.py) - stdlib saja, dijalankan rantai GitHub. Jalur penuh terhadap kontrak sungguhan ada di
test_signal_commit.AnvilEndToEndTests.test_external_watch_reads_the_same_chain_state."""
import os
import shutil
import socket
import sys
import tempfile
import unittest

from engine import chain, ledger
from engine.spec import SPECS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import signal_commit as sc                                          # noqa: E402
import worker_watch as ww                                           # noqa: E402

LEDGER = os.path.join(ROOT, "ledger", "paper")
B3_BAR = 1_790_812_800_000
ASOF = (B3_BAR + 86_400_000) // 1000
COMMITTER = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"


def frozen_ledger(tmp):
    """Salinan ledger B3 sampai tick bar 2026-10-01 saja (ledger repo terus bertambah; tes tidak boleh ikut bergeser)."""
    out = []
    with open(os.path.join(LEDGER, "B3-CARRY.jsonl"), encoding="utf-8") as f:
        for ln in f:
            out.append(ln)
            if '"type":"tick"' in ln and f'"asof":{B3_BAR}' in ln:
                break
    with open(os.path.join(tmp, "B3-CARRY.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        f.writelines(out)
    import json
    return json.loads(out[-1])


class FakeView:
    def __init__(self, locked=ASOF - 3600, commit=None):
        self.locked, self.commit = locked, commit

    def locked_at(self, committer, bot, spec):
        return self.locked

    def get_commit(self, cid):
        return self.commit or {"committer": "0x" + "00" * 20, "committedAt": 0, "n": 0, "revealed": 0}


class DecodeTests(unittest.TestCase):
    def test_get_commit_words_decode_in_order(self):
        raw = chain.abi_encode(("address", "uint64", "uint64", "uint32", "uint32", "bool", "bytes32", "bytes32", "bytes32"),
                               (COMMITTER, ASOF, ASOF + 600, 2, 1, False, chain.ascii32("B3-CARRY"), chain.from_hex(SPECS["B3-CARRY"].sha()), b"\x11" * 32))
        c = ww.decode_commit(raw)
        self.assertEqual(c["committer"].lower(), COMMITTER.lower())
        self.assertEqual((c["asof"], c["committedAt"], c["n"], c["revealed"], c["missed"]), (ASOF, ASOF + 600, 2, 1, False))
        self.assertEqual(c["root"], b"\x11" * 32)
        with self.assertRaises(ww.ReadError):
            ww.decode_commit(raw[:200])

    def test_selector_matches_the_engine_keccak_of_the_signature(self):
        self.assertEqual(ww.selector("getCommit(bytes32)"), chain.keccak256(b"getCommit(bytes32)")[:4])

    def test_dead_rpc_is_a_read_error_not_an_empty_answer(self):
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        with self.assertRaises(ww.ReadError):
            ww.Reader([f"http://127.0.0.1:{port}"], timeout=2).call("0x" + "22" * 20, b"\x00" * 4)


class CrashTests(unittest.TestCase):
    def test_own_crash_exits_3_not_the_alarm_code(self):
        orig = ww.main
        ww.main = lambda: 1 / 0
        try:
            self.assertEqual(ww.guarded_main(), 3)
        finally:
            ww.main = orig


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.tick = frozen_ledger(self.tmp)
        self.emitted = ledger.iso_ms(self.tick["emitted_utc"]) // 1000

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_check(self, view, now):
        return ww.check(["B3-CARRY"], self.tmp, view, COMMITTER, now)

    def test_no_commit_inside_grace_is_waiting_then_alarm(self):
        code, rows = self.run_check(FakeView(), self.emitted + 600)
        self.assertEqual((code, rows[0][2]), (2, ww.MENUNGGU))
        code, rows = self.run_check(FakeView(), self.emitted + ww.TENGGANG_S + 60)
        self.assertEqual((code, rows[0][2]), (1, ww.ALARM))
        self.assertIn("WORKER DIAM", rows[0][3])

    def test_commit_with_all_reveals_is_ok_and_stuck_reveals_alarm(self):
        cid_commit = {"committer": COMMITTER, "committedAt": ASOF + 600, "n": 2, "revealed": 2}
        self.assertEqual(self.run_check(FakeView(commit=cid_commit), ASOF + 7200)[0], 0)
        stuck = dict(cid_commit, revealed=1)
        self.assertEqual(self.run_check(FakeView(commit=stuck), ASOF + 600 + 60)[0], 0)          # ungkap masih dalam tenggang
        code, rows = self.run_check(FakeView(commit=stuck), ASOF + 600 + ww.TENGGANG_S + 60)
        self.assertEqual(code, 1)
        self.assertIn("UNGKAP TERTAHAN", rows[0][3])

    def test_tick_older_than_the_lock_is_not_an_alarm(self):
        code, rows = self.run_check(FakeView(locked=ASOF + 1), ASOF + 10 * 86400)
        self.assertEqual((code, rows[0][2]), (0, ww.SEBELUM))

    def test_commit_id_is_the_worker_commit_id(self):
        seen = []

        class V(FakeView):
            def get_commit(self, cid):
                seen.append(cid)
                return super().get_commit(cid)
        self.run_check(V(), ASOF)
        self.assertEqual(seen, [sc.commit_id(COMMITTER, "B3-CARRY", SPECS["B3-CARRY"].sha(), ASOF)])


if __name__ == "__main__":
    unittest.main()

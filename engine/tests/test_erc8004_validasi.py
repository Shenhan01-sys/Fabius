"""P136 (F-D98): validasi ERC-8004 untuk komit sinyal Fabius (tools/erc8004_validasi.py). Registry, chain, dan pengirim tx dipalsukan."""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
try:
    import eth_abi                                                  # noqa: F401
    import eth_account                                              # noqa: F401
    HAVE_ETH = True
except ImportError:
    HAVE_ETH = False

import erc8004_validasi as v8                                       # noqa: E402
import signal_commit as sc                                          # noqa: E402
from engine.spec import SPECS                                       # noqa: E402
from verify_signals import Row                                      # noqa: E402

COMMITTER = "0x" + "11" * 20
VALIDATOR = "0x" + "22" * 20
CFG = {"agent_id": 2494, "identity": "0x" + "a1" * 20, "validation": "0x" + "a2" * 20, "validator": VALIDATOR, "tag": v8.TAG}
BAR_MS = 1_790_985_600_000                                          # 2026-10-02T00:00Z


def cid_of(i: int) -> bytes:
    return bytes([i]) * 32


class FakeReg:
    def __init__(self, ok=True, statuses=None, requests=()):
        self.cfg, self.ok, self.st, self.reqs = CFG, ok, dict(statuses or {}), list(requests)

    def authorized(self, agent_id, who):
        return self.ok

    def status(self, rh):
        return self.st.get(bytes(rh))

    def validator_requests(self, validator):
        return list(self.reqs)


class FakeCv:
    def __init__(self, committed):
        self.committed = committed

    def get_commit(self, cid):
        return {"committer": COMMITTER if cid in self.committed else "0x" + "00" * 20}


def args_of(sig_types, data):
    from eth_abi import decode
    return decode(list(sig_types), bytes(data[4:]))


@unittest.skipUnless(HAVE_ETH, "eth-abi/eth-account tidak terpasang")
class RequestTests(unittest.TestCase):
    def setUp(self):
        self.sent, self.logs = [], []

    def send(self, to, data):
        self.sent.append((to, data))
        return {"status": "0x1", "transactionHash": "0xtx"}

    def test_nothing_is_sent_until_the_owner_of_2494_approves_the_committer(self):
        st = v8.request_round(FakeReg(ok=False), self.send, COMMITTER, CFG, [("B1-TREND", "2026-10-02", cid_of(1))], log=self.logs.append)
        self.assertEqual((st["belum_setuju"], self.sent), (1, []))

    def test_each_existing_commit_is_requested_once_with_its_commit_id_as_request_hash(self):
        reg = FakeReg(statuses={cid_of(2): {"validator": VALIDATOR, "responseHash": b"\0" * 32}})
        cands = [("B1-TREND", "2026-10-02", cid_of(1)), ("B3-CARRY", "2026-10-02", cid_of(2)), ("B1-TREND", "2026-10-03", cid_of(3))]
        st = v8.request_round(reg, self.send, COMMITTER, CFG, cands, log=self.logs.append)
        self.assertEqual((st["diminta"], st["sudah"]), (2, 1))
        to, data = self.sent[0]
        self.assertEqual(to, CFG["validation"])
        val, agent, uri, rh = args_of(("address", "uint256", "string", "bytes32"), data)
        self.assertEqual((val.lower(), agent, rh), (VALIDATOR, 2494, cid_of(1)))
        self.assertIn("B1-TREND", uri)
        self.assertIn("2026-10-02", uri)
        for _, _, c in cands:                                                   # sesudah diminta, status ada -> putaran berikut tidak mengirim apa pun
            reg.st.setdefault(c, {"validator": VALIDATOR, "responseHash": b"\0" * 32})
        self.sent.clear()
        v8.request_round(reg, self.send, COMMITTER, CFG, cands, log=self.logs.append)
        self.assertEqual(self.sent, [])

    def test_a_backlog_is_capped_per_round(self):
        cands = [("B1-TREND", f"2026-09-{d:02d}", cid_of(d)) for d in range(1, 11)]
        st = v8.request_round(FakeReg(), self.send, COMMITTER, CFG, cands, log=self.logs.append)
        self.assertEqual((st["diminta"], len(self.sent)), (v8.LIMIT, v8.LIMIT))

    def test_candidates_are_only_ticks_whose_commit_exists_on_chain(self):
        d = tempfile.mkdtemp()
        try:
            with open(os.path.join(d, "B1-TREND.jsonl"), "w", encoding="utf-8") as f:
                for i, day in enumerate(("2026-10-02", "2026-10-03")):
                    print(json.dumps({"type": "tick", "asof": BAR_MS + i * 86_400_000, "asof_date": day}), file=f)
            sha = SPECS["B1-TREND"].sha()
            c2 = sc.commit_id(COMMITTER, "B1-TREND", sha, sc.asof_s_of({"asof": BAR_MS}))
            got = v8.candidates(["B1-TREND", "B3-CARRY"], d, FakeCv({c2}), COMMITTER)
            self.assertEqual(got, [("B1-TREND", "2026-10-02", c2)])
        finally:
            shutil.rmtree(d, ignore_errors=True)


@unittest.skipUnless(HAVE_ETH, "eth-abi/eth-account tidak terpasang")
class AnswerTests(unittest.TestCase):
    def test_final_verdicts_are_answered_with_the_hash_of_the_printed_report_and_open_ones_wait(self):
        open_ = {"validator": VALIDATOR, "responseHash": b"\0" * 32}
        done = {"validator": VALIDATOR, "responseHash": b"\x01" * 32}
        reg = FakeReg(statuses={cid_of(1): open_, cid_of(2): open_, cid_of(3): open_, cid_of(4): done, cid_of(5): open_},
                      requests=[cid_of(i) for i in range(1, 6)])
        hx = lambda i: "0x" + cid_of(i).hex()                                       # noqa: E731
        rows = [Row("B1-TREND", "2026-10-02", "SAH", "", hx(1)), Row("B3-CARRY", "2026-10-02", "ALARM", "daun beda", hx(2), problems=["daun beda"]),
                Row("B1-TREND", "2026-10-03", "BELUM DIUNGKAP", "", hx(3)), Row("B3-CARRY", "2026-10-03", "SAH", "", hx(4))]
        sent, logs = [], []
        st = v8.answer_round(reg, lambda to, data: sent.append(data) or {"status": "0x1", "transactionHash": "0xtx"}, VALIDATOR, rows,
                             "https://github.com/x/actions/runs/1", "abc", log=logs.append)
        self.assertEqual(st, {"dijawab": 2, "sudah": 1, "tunggu": 1, "asing": 1, "gagal": 0})
        got = [args_of(("bytes32", "uint8", "string", "bytes32", "string"), d) for d in sent]
        self.assertEqual([(g[0], g[1], g[4]) for g in got], [(cid_of(1), 100, v8.TAG), (cid_of(2), 0, v8.TAG)])
        rep = v8.report_of(rows[0], "https://github.com/x/actions/runs/1", "abc")
        self.assertEqual(got[0][3], v8.report_hash(rep))                            # hash = laporan yang dicetak di log, bisa dihitung ulang
        self.assertTrue(any(x.startswith("LAPORAN ") and '"vonis": "SAH"' in x for x in logs))
        self.assertEqual(got[0][2], "https://github.com/x/actions/runs/1")


class WorkerTests(unittest.TestCase):
    def test_validation_is_silent_without_a_validator_and_its_errors_never_fail_the_commit_round(self):
        import operator_loop as ol
        w = ol.Worker(workdir=tempfile.mkdtemp())
        sent = []
        w.alert.send = lambda key, text, sekali=False: sent.append(key)
        self.assertEqual(w.validation_step(None, None, COMMITTER, "0xkunci"), "mati")       # deployments/97.json tidak ada di workdir
        os.makedirs(os.path.join(w.workdir, "deployments"))
        with open(os.path.join(w.workdir, "deployments", "97.json"), "w", encoding="utf-8") as f:
            json.dump({"erc8004": CFG}, f)

        class Boom:
            def has_pending(self, a):
                raise RuntimeError("rpc mati")
        for _ in range(3):
            self.assertEqual(w.validation_step(Boom(), None, COMMITTER, "0xkunci"), "gagal")
        self.assertIn("validasi-gagal", sent)


if __name__ == "__main__":
    unittest.main()

"""Indeks tx on-chain (P178, tools/tx_index.py): log mentah eth_getLogs dilipat jadi petunjuk hash tx per komit/ungkap/kunci; web memeriksa ulang lewat struk."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import tx_index as ti                                               # noqa: E402

ANCHOR = "0x9B78200beFbbBe836585d31bd5b6dB32587064f3"
REGISTRY = "0xcF6fBF95fc04DEd8d670512CEc0723a2246Fbb0C"
LOCKER = "0xca9c7322210e9a7f7d0953c862d4ef60cc0d64a4"
CID = "0x" + "11" * 32
BOT = "0x" + "42" * 32
SPEC = "0x" + "23" * 32


def log(addr, topics, tx, block, data="0x"):
    return {"address": addr, "topics": topics, "transactionHash": tx, "blockNumber": hex(block), "data": data}


def committed(tx="0x" + "c1" * 32, block=100):
    return log(ANCHOR, [ti.T_COMMITTED, CID, "0x" + "00" * 12 + LOCKER[2:], BOT], tx, block)


def revealed(leaf, tx, block):
    return log(ANCHOR, [ti.T_REVEALED, CID, leaf], tx, block)


def locked(tx="0x" + "a1" * 32, block=50):
    return log(REGISTRY, [ti.T_LOCKED, "0x" + "99" * 32, "0x" + "00" * 12 + LOCKER[2:], BOT], tx, block, data=SPEC + "00" * 96)


class ApplyLogsTests(unittest.TestCase):
    def setUp(self):
        self.ix = ti.empty_index(ANCHOR, REGISTRY, 10)

    def test_commit_reveals_and_lock_are_indexed(self):
        n = ti.apply_logs(self.ix, [locked(), committed(), revealed("0x" + "02" * 32, "0x" + "b2" * 32, 102), revealed("0x" + "01" * 32, "0x" + "b1" * 32, 101)])
        self.assertEqual(n, 4)
        c = self.ix["commits"][CID]
        self.assertEqual((c["tx"], c["block"]), ("0x" + "c1" * 32, 100))
        self.assertEqual([r["block"] for r in c["reveals"]], [101, 102])      # urut blok
        self.assertEqual(self.ix["locks"][ti.lock_key(LOCKER, BOT, SPEC)], {"tx": "0x" + "a1" * 32, "block": 50})

    def test_idempotent_on_rescan(self):
        logs = [committed(), revealed("0x" + "01" * 32, "0x" + "b1" * 32, 101), locked()]
        ti.apply_logs(self.ix, logs)
        self.assertEqual(ti.apply_logs(self.ix, logs), 0)
        self.assertEqual(len(self.ix["commits"][CID]["reveals"]), 1)

    def test_foreign_contract_logs_ignored(self):
        other = "0x" + "77" * 20
        n = ti.apply_logs(self.ix, [log(other, [ti.T_COMMITTED, CID], "0x" + "c1" * 32, 1), log(other, [ti.T_LOCKED, CID, CID, BOT], "0x" + "a1" * 32, 1, SPEC)])
        self.assertEqual(n, 0)
        self.assertEqual(self.ix["commits"], {})
        self.assertEqual(self.ix["locks"], {})

    def test_reveal_before_commit_in_same_batch_keeps_both(self):
        ti.apply_logs(self.ix, [revealed("0x" + "01" * 32, "0x" + "b1" * 32, 101)])
        ti.apply_logs(self.ix, [committed()])
        c = self.ix["commits"][CID]
        self.assertEqual(c["tx"], "0x" + "c1" * 32)
        self.assertEqual(len(c["reveals"]), 1)

    def test_get_logs_falls_to_next_source_and_splits_range(self):
        class Src:
            def __init__(self, fail):
                self.fail, self.calls = fail, []

            def rpc(self, method, params):
                self.calls.append((params[0]["fromBlock"], params[0]["toBlock"]))
                if self.fail:
                    raise ti.evmmod.RpcError("limit exceeded")
                return []

        bad, good = Src(True), Src(False)
        ti.get_logs([(bad, 9_999), (good, 999)], {}, 0, 2_500, lambda s: None)
        self.assertEqual(len(bad.calls), 5)                                 # 1 + 4 ulang, lalu menyerah ke sumber berikut
        self.assertEqual(good.calls, [("0x0", "0x3e7"), ("0x3e8", "0x7cf"), ("0x7d0", "0x9c4")])


if __name__ == "__main__":
    unittest.main()

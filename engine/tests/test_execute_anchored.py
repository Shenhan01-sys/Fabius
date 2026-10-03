"""P72: `tools/execute_live.py::require_anchored` harus MENOLAK keputusan yang tidak ter-anchor. Versi lama tidak pernah menyala: jawaban `getAnchor`
dinamis, kata pertamanya selalu offset 0x20. Jawaban chain tiruan dibentuk persis seperti jawaban nyata (`cast call ... getAnchor(0x..01)` 3 Okt)."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

try:
    import execute_live as el                                       # butuh eth-abi / eth-utils (terpasang di CI tests.yml)
    HAVE = True
except ImportError:
    HAVE = False

DEC = {"decisionHash": "0x" + "ab" * 32, "snapshotHash": "0x" + "cd" * 32, "file": "x.jsonl", "asset": "BTCB"}
EMPTY = "0x" + "".join(["%064x" % 0x20, "0" * 64, "%064x" % 0xe0] + ["0" * 64] * 5 + ["0" * 64])          # struct nol (id tak dikenal)


def anchored(dh, at=1_790_000_000):
    agent = "0" * 24 + "11" * 20
    return "0x" + "".join(["%064x" % 0x20, agent, "%064x" % 0xe0, "%064x" % 1, dh[2:], "ee" * 32, "cd" * 32, "%064x" % at, "%064x" % 4,
                           "42544342" + "0" * 56])


@unittest.skipUnless(HAVE, "eth-abi tidak terpasang")
class RequireAnchoredTests(unittest.TestCase):
    def run_with(self, raw):
        orig = (el.vd.resolve_anchor, el.vd.call, el.an.expected_id)
        el.vd.resolve_anchor = lambda: "0x" + "dd" * 20
        el.vd.call = lambda *a, **k: raw
        el.an.expected_id = lambda *a: "0x" + "99" * 32
        try:
            return el.require_anchored(DEC, "0x" + "11" * 20)
        finally:
            el.vd.resolve_anchor, el.vd.call, el.an.expected_id = orig

    def test_unknown_id_zero_struct_is_refused(self):
        with self.assertRaises(SystemExit):
            self.run_with(EMPTY)

    def test_anchored_with_the_same_decision_hash_passes(self):
        self.assertEqual(self.run_with(anchored(DEC["decisionHash"])), "0x" + "99" * 32)

    def test_anchored_but_different_decision_hash_is_refused(self):
        with self.assertRaises(SystemExit):
            self.run_with(anchored("0x" + "12" * 32))


if __name__ == "__main__":
    unittest.main()

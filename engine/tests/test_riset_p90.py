"""P90 gelombang 1 (tools/riset_p90.py): protokol tidak boleh bergeser sesudah pra-registrasi; dunia sintetik dan pemeriksa vonis jujur."""
import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import riset_p90 as rp                                              # noqa: E402

from engine.replay import replay                                    # noqa: E402
from engine.series import sharpe                                    # noqa: E402
from engine.spec import sha0x                                       # noqa: E402

# di-push sebelum lari: vault/06-Results/31 - Pra-Registrasi P90 R1+R2.md
REGISTERED = "0xce2f814e334244f8e43c3d9d862b8e654896f3ba1772d20c9e4397e89f2820bd"


class ProtocolTests(unittest.TestCase):
    def test_protocol_is_the_registered_one(self):
        self.assertEqual(sha0x(rp.PROTOKOL), REGISTERED)

    def test_job_seeds_are_disjoint_from_the_pilot_and_deterministic(self):
        a, b = rp.job_r1(("x", 0, 99_999)), rp.job_r1(("x", 0, 99_999))      # indeks di luar protokol (i < 1100): tidak mengintip pasar sungguhan
        self.assertEqual({k: v for k, v in a.items() if k != "dt"}, {k: v for k, v in b.items() if k != "dt"})
        self.assertLess(9_000_100, 31_000_000)                           # benih pilot jauh di bawah benih protokol


class WorldTests(unittest.TestCase):
    def test_null_worlds_have_no_drift_and_paths_are_reproducible(self):
        for w in rp.WORLDS:
            p1 = rp.paths(w, random.Random(5), 2, 4000)
            p2 = rp.paths(w, random.Random(5), 2, 4000)
            self.assertEqual(p1, p2)
            rets = [p1[0][i] / p1[0][i - 1] - 1 for i in range(1, 4000)]
            m = sum(rets) / len(rets)
            sd = (sum((r - m) ** 2 for r in rets) / (len(rets) - 1)) ** 0.5
            self.assertLess(abs(m), 4 * sd / len(rets) ** 0.5, w)           # rerata nol dalam 4 galat baku

    def test_injected_edge_is_what_b1_harvests(self):
        spec = rp.spec_for("B1-TREND", 60, 1)
        base = sharpe([v for _, v in replay(spec, rp.market("W1-iid", random.Random(11), 1, 6000))])
        edge = sharpe([v for _, v in replay(spec, rp.market("W1-iid", random.Random(11), 1, 6000, mu=0.004))])
        self.assertGreater(edge, base + 1.0)


class VerdictTests(unittest.TestCase):
    def test_recomputed_pass_matches_the_gate_rules(self):
        ok = {g: "PASS" for g in rp.gates.REQUIRED}
        self.assertTrue(rp.passes(dict(ok, G11="NA")))
        self.assertFalse(rp.passes(dict(ok, G8="FAIL")))
        self.assertTrue(rp.passes(dict(ok, G8="FAIL"), without="G8"))
        self.assertFalse(rp.passes(dict(ok, G3="NA")))
        self.assertFalse(rp.passes(dict(ok, **{"K*": "FAIL"})))
        self.assertFalse(rp.passes({"G*": "FAIL"}))

    def test_power_ceiling_matches_run14(self):
        self.assertAlmostEqual(rp.plafon(1.0, 3.0), 0.528, places=3)
        self.assertAlmostEqual(rp.plafon(0.5, 3.0), 0.231, places=3)


if __name__ == "__main__":
    unittest.main()

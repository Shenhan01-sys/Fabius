"""P137 (F-D98/F-D99): teaser confidence (engine/confidence.py) = 1 - p bootstrap F-D16 atas settle maju, tanpa detail sinyal."""
import json
import os
import sys
import unittest

from engine import confidence, fd16
from engine.tests.test_fd16 import ledger, wobble

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ConfidenceTests(unittest.TestCase):
    def test_no_number_at_all_before_two_settled_days(self):
        t = confidence.teasers({"B1-TREND": ledger([0.002], n_signals=3)}, {"B1-TREND": "INTI"}, {"B1-TREND": "TOLAK"})["B1-TREND"]
        self.assertIsNone(t["confidence_pct"])
        self.assertEqual(t["label"], "belum terukur")
        self.assertTrue(any("butuh >= 2" in a for a in t["alasan"]))
        self.assertTrue(any("TOLAK" in a for a in t["alasan"]))                    # vonis gerbang yang buruk tetap tampil
        self.assertTrue(any("bukan bukti bot terbaik" in a for a in t["alasan"]))

    def test_a_few_days_give_an_early_number_that_is_labelled_not_meaningful(self):
        t = confidence.teasers({"X": ledger(wobble(8, 0.0005, 0.001), n_signals=8)}, {}, {})["X"]
        self.assertIsNotNone(t["confidence_pct"])
        self.assertEqual((t["label"], t["fd16"]), ("awal - belum bermakna", "BELUM CUKUP DATA"))
        self.assertEqual(t["kematangan"]["hari"], [8, 20])

    def test_the_number_is_one_minus_the_locked_f_d16_p_value(self):
        led = {"A": ledger(wobble(90, 0.0005, 0.001)), "B": ledger(wobble(90, 0.0, 0.001))}
        res = {r.bot: r for r in fd16.check(led)}
        tz = confidence.teasers(led, {}, {})
        for b in ("A", "B"):
            self.assertEqual(tz[b]["confidence_pct"], int(round((1 - res[b].p) * 100)))
            self.assertEqual(tz[b]["label"], "terukur")
        self.assertGreater(tz["A"]["confidence_pct"], tz["B"]["confidence_pct"])

    def test_the_teaser_never_leaks_assets_direction_size_or_signal_ids(self):
        recs = ledger(wobble(30, 0.0005, 0.001), n_signals=30)
        for r in recs:
            if r.get("type") == "tick":
                r["targets"] = {"XRPUSDT": 0.0625, "BTCUSDT": -0.0625}
                r["sizes"] = {"XRPUSDT": 123.45}
        t = confidence.teasers({"B1-TREND": recs}, {"B1-TREND": "INTI"}, {"B1-TREND": "TOLAK"})["B1-TREND"]
        blob = json.dumps(t, ensure_ascii=False)
        ids = [s for r in recs if r.get("type") == "tick" for s in r["signal_ids"]]
        for leak in ["XRPUSDT", "BTCUSDT", "0.0625", "123.45", "targets", "long", "short"] + ids:
            self.assertNotIn(leak, blob)

    def test_the_web_snapshot_carries_a_teaser_for_every_forward_bot(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        import web_snapshot
        from engine import book
        c = web_snapshot.confidence_block()
        self.assertEqual(sorted(c), sorted(b for b in book.FORWARD_BOTS if os.path.exists(os.path.join(ROOT, "ledger", "paper", f"{b}.jsonl"))))
        self.assertTrue(all(set(v) >= {"confidence_pct", "label", "dasar", "alasan", "kematangan"} for v in c.values()))


if __name__ == "__main__":
    unittest.main()

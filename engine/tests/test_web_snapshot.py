"""Snapshot landing otomatis (tools/web_snapshot.py --if-changed): commit hanya bila isi berubah; chain tak terbaca = TUNDA (T8 SK-P1)."""
import copy
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import web_snapshot as ws                                           # noqa: E402

OLD = {"v": 1, "generated_utc": "2026-10-03T09:00:00Z", "repo_head": "aaa", "ledger": {"B3-CARRY": {"n_signals": 3, "days_live": 3}},
       "chain": {"block": 100, "block_utc": "2026-10-03T09:00:00Z", "commit_count": 2, "verdicts": [{"bot": "B3-CARRY", "bar": "2026-10-02", "verdict": "SAH"}]}}


class DecideTests(unittest.TestCase):
    def test_only_timestamp_head_and_block_moved_is_the_same(self):
        new = copy.deepcopy(OLD)
        new.update(generated_utc="2026-10-03T15:00:00Z", repo_head="bbb")
        new["chain"].update(block=9999, block_utc="2026-10-03T15:00:00Z")
        self.assertEqual(ws.decide(new, OLD), "sama")

    def test_a_new_verdict_or_ledger_day_is_written(self):
        new = copy.deepcopy(OLD)
        new["chain"]["verdicts"].append({"bot": "B3-CARRY", "bar": "2026-10-03", "verdict": "SAH"})
        self.assertEqual(ws.decide(new, OLD), "tulis")
        new = copy.deepcopy(OLD)
        new["ledger"]["B3-CARRY"]["days_live"] = 4
        self.assertEqual(ws.decide(new, OLD), "tulis")
        self.assertEqual(ws.decide(new, None), "tulis")

    def test_unreadable_chain_keeps_the_old_snapshot(self):
        new = copy.deepcopy(OLD)
        new["chain"], new["chain_error"] = None, "ReadError: rpc mati"
        self.assertEqual(ws.decide(new, OLD), "tunda")
        old_without_chain = dict(OLD, chain=None, chain_error="x")
        self.assertEqual(ws.decide(new, old_without_chain), "tulis")


if __name__ == "__main__":
    unittest.main()

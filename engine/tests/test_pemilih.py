"""P143 (F-D102): bot aktif dari pilihan agent (engine/pemilih.py, terkunci) + skor pilihan + reputasi ERC-8004 (tools/analis.py). Chain dipalsukan."""
import json
import os
import shutil
import sys
import tempfile
import unittest

from engine import pemilih as pm

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
try:
    import eth_abi                                                  # noqa: F401
    HAVE_ETH = True
except ImportError:
    HAVE_ETH = False

import analis as an                                                 # noqa: E402

DAY = 86_400


class RuleTests(unittest.TestCase):
    def test_the_rule_is_locked_before_any_scored_pick(self):
        self.assertEqual(pm.status()["state"], "TERKUNCI")

    def test_no_picks_majority_and_tie_fall_back_to_the_identity_bot(self):
        self.assertEqual(pm.aktif({}, {}, "B1-TREND", 100)[0], "B1-TREND")
        self.assertEqual(pm.aktif({1: "B3-CARRY", 2: "B3-CARRY", 3: "B1-TREND"}, {}, "B1-TREND", 100)[0], "B3-CARRY")
        self.assertEqual(pm.aktif({1: "B3-CARRY", 2: "B1-TREND"}, {}, "B1-TREND", 100)[0], "B1-TREND")
        self.assertEqual(pm.aktif({1: "B3-CARRY", 2: "B6-BOUNCE"}, {}, "B1-TREND", 100)[0], "B3-CARRY")       # seri tanpa identitas -> abjad

    def test_a_leader_needs_enough_scored_picks_and_only_bars_before_the_close_count(self):
        good = {1: [(c, 0.001) for c in range(1, 21)], 2: [(c, -0.001) for c in range(1, 21)]}
        self.assertEqual(pm.aktif({1: "B6-BOUNCE", 2: "B1-TREND", 3: "B1-TREND"}, good, "B1-TREND", 100)[0], "B6-BOUNCE")
        self.assertEqual(pm.aktif({1: "B6-BOUNCE", 2: "B1-TREND", 3: "B1-TREND"}, good, "B1-TREND", 20)[0], "B1-TREND")  # skor bar >= close tidak dihitung
        few = {1: [(c, 0.01) for c in range(1, 20)]}
        self.assertIsNone(pm.pemimpin(few, 100))


class ScoreTests(unittest.TestCase):
    def picks(self, close):
        return [{"agent": "a", "agent_id": 1, "bar_close": close, "bot": "B3-CARRY", "keyakinan": 50, "reasonHash": "0x" + "00" * 32, "committedAt": 0},
                {"agent": "b", "agent_id": 2, "bar_close": close, "bot": "B1-TREND", "keyakinan": 50, "reasonHash": "0x" + "00" * 32, "committedAt": 0}]

    def test_closed_bars_are_scored_provisionally_and_the_identity_bot_has_zero_excess(self):
        from paper_tick import Views
        md = Views(os.path.join(ROOT, "ledger", "bars")).get("provisional")
        r = an.skor(ROOT, self.picks(1_790_899_200), md)                    # bar yang dibuka 2026-10-02 00:00Z (posisi tick 10-01)
        self.assertEqual([x["status_skor"] for x in r], ["provisional", "provisional"])
        self.assertAlmostEqual(r[0]["selisih"], r[0]["net"] - r[0]["net_identitas"])
        self.assertEqual(r[1]["selisih"], 0.0)
        board = an.papan(r)
        self.assertEqual({b["agent_id"]: b["terskor"] for b in board}, {1: 1, 2: 1})

    def test_bars_without_data_wait_and_are_never_invented(self):
        r = an.skor(ROOT, self.picks(4_102_444_800), None)                  # 2100-01-01: belum ada apa pun
        self.assertEqual({x["status_skor"] for x in r}, {"menunggu"})
        self.assertTrue(all(x["selisih"] is None for x in r))

    def test_the_active_bot_uses_only_picks_for_that_close(self):
        picks = self.picks(2 * DAY) + [{"agent": "a", "agent_id": 1, "bar_close": 3 * DAY, "bot": "B6-BOUNCE", "keyakinan": 1, "reasonHash": "0x", "committedAt": 0}]
        out = an.bot_aktif(picks, [], 3 * DAY, "B1-TREND")
        self.assertEqual((out["bot"], out["pilihan"]), ("B6-BOUNCE", {1: "B6-BOUNCE"}))
        self.assertIn("majority", out["alasan_en"])


class FakeEv:
    def __init__(self):
        self.sent = []

    def send(self, pk, to, data, gas=None, value=0):
        self.sent.append((to, data))
        return {"status": "0x1", "transactionHash": f"0xtx{len(self.sent)}"}


@unittest.skipUnless(HAVE_ETH, "eth-abi tidak terpasang")
class ReputationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_feedback_is_the_excess_in_bps_tagged_by_status_once_per_agent_bar_and_status(self):
        from eth_abi import decode
        scored = [{"agent": "a", "agent_id": 2558, "bar_close": 100, "bot": "B3-CARRY", "net": 0.001, "net_identitas": -0.0005, "selisih": 0.0015,
                   "status_skor": "provisional", "reasonHash": "0x" + "11" * 32, "bar_hasil": "2026-10-06"},
                  {"agent": "b", "agent_id": 2559, "bar_close": 100, "bot": "B1-TREND", "net": None, "net_identitas": None, "selisih": None,
                   "status_skor": "menunggu", "reasonHash": "0x" + "22" * 32, "bar_hasil": "2026-10-06"}]
        ev, state = FakeEv(), os.path.join(self.tmp, "rep.json")
        self.assertEqual(an.reputasi(ev, "0xk", "0xrep", scored, state, "https://g", log=lambda m: None), 1)
        aid, val, dec, t1, t2, ep, uri, h = decode(["uint256", "int128", "uint8", "string", "string", "string", "string", "bytes32"], bytes(ev.sent[0][1][4:]))
        self.assertEqual((aid, val, dec, t1, t2, uri), (2558, 1500, 2, "fabius-pick-v1", "provisional", "https://g/analysts/100"))
        self.assertEqual(an.reputasi(ev, "0xk", "0xrep", scored, state, "https://g", log=lambda m: None), 0)       # tidak dobel
        scored[0]["status_skor"] = "final"
        self.assertEqual(an.reputasi(ev, "0xk", "0xrep", scored, state, "https://g", log=lambda m: None), 1)       # final = feedback baru
        self.assertEqual(json.load(open(state, encoding="utf-8")), {"2558:100:provisional": "0xtx1", "2558:100:final": "0xtx2"})


class ArchiveTests(unittest.TestCase):
    def test_only_published_reasoning_whose_hash_matches_the_on_chain_pick_is_archived(self):
        tmp = tempfile.mkdtemp()
        try:
            good = {"agent": "glm", "bot": "B1-TREND", "alasan": {"bar_close": 100, "pilihan": {"bot": "B1-TREND"}, "x": 1}}
            bad = {"agent": "qwen", "bot": "B1-TREND", "alasan": {"bar_close": 100, "pilihan": {"bot": "B1-TREND"}, "x": 2}}
            picks = [{"agent": "glm", "bar_close": 100, "bot": "B1-TREND", "reasonHash": an.sha(good["alasan"])},
                     {"agent": "qwen", "bar_close": 100, "bot": "B1-TREND", "reasonHash": an.sha({"lain": True})}]
            logs = []
            self.assertEqual(an.arsip(picks, lambda c: {"pilihan": [good, bad]}, tmp, log=logs.append, now_s=99), 0)   # bar belum tutup: tersegel
            self.assertEqual(logs, [])
            n = an.arsip(picks, lambda c: {"pilihan": [good, bad]}, tmp, log=logs.append)
            self.assertEqual(n, 1)
            self.assertTrue(any("DITOLAK" in x and "qwen" in x for x in logs))
            self.assertEqual([r["agent"] for r in an.records([tmp])], ["glm"])
            self.assertEqual(an.arsip(picks, lambda c: {"pilihan": [good, bad]}, tmp, log=logs.append), 0)        # tidak ditulis ulang
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

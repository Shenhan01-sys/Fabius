"""P87: buku slot hidup (engine/book_live.py) - catatan epoch, rantai hash, dan keputusan yang DIHITUNG ULANG dari masukannya sendiri."""
import dataclasses
import os
import shutil
import tempfile
import unittest

from engine import book_live, ledger, slots
from engine.book import genesis_book
from engine.spec import SPECS

DAY_S = 86_400
NOW = 1_791_000_000                                                  # 2026-10-03, dalam satu epoch 30 hari
B3 = SPECS["B3-CARRY"]


def chall(book, shadow_days=70, score=50.0, verdict="LOLOS_SHADOW"):
    return slots.Challenger(bot_id="B3-CARRY", issuer=slots.FABIUS, spec_sha=B3.sha(), fingerprint=B3.fingerprint(), gate_verdict=verdict,
                            report_sha="0x" + "cd" * 32, book_sha=slots.book_sha(book), shadow_days=shadow_days, shadow_score_bps=score, paired={}, payout="")


class BookLiveTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "buku.jsonl")
        self.book = genesis_book(NOW - 100 * DAY_S)
        self.recs = [book_live.append(self.path, book_live.make_genesis(self.book, "0x" + "11" * 32, NOW - 100 * DAY_S, "uji"), [])]

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def epoch(self, now, challengers, killers=None, scores=None, book=None):
        b = book if book is not None else book_live.current_book(self.recs)
        rec = book_live.build_epoch(b, now, now * 1000, scores or {e.bot_id: None for e in b}, challengers, killers or {"B1-TREND": "TEKS"})
        self.recs.append(book_live.append(self.path, rec, self.recs))
        return rec

    def test_no_challenger_keeps_book_and_verifies(self):
        rec = self.epoch(NOW, [])
        self.assertEqual(rec["book_sha"], slots.book_sha(self.book))
        self.assertEqual(book_live.verify_book(ledger.load(self.path)), [])

    def test_young_challenger_rejected_old_one_admitted(self):
        r1 = self.epoch(NOW, [chall(self.book, shadow_days=1)])
        self.assertEqual(r1["keputusan"][0][1], slots.REJECT)
        b = book_live.current_book(self.recs)
        r2 = self.epoch(NOW + 31 * DAY_S, [chall(b, shadow_days=70)])
        self.assertEqual(r2["keputusan"][0][1], slots.ADMIT)
        self.assertEqual(sorted(e["bot_id"] for e in r2["buku"]), ["B1-TREND", "B3-CARRY"])
        self.assertEqual(book_live.verify_book(ledger.load(self.path)), [])

    def test_tampered_decision_is_caught_even_when_resealed(self):
        self.epoch(NOW, [chall(self.book, shadow_days=1)])
        recs = ledger.load(self.path)
        bad = {k: v for k, v in recs[1].items() if k not in ("h", "prev", "v")}
        bad["keputusan"] = [["B3-CARRY", slots.ADMIT, None, "dipalsukan"]]
        resealed = [recs[0], ledger.seal(bad, recs[0]["h"])]
        probs = book_live.verify_book(resealed)
        self.assertTrue(any("keputusan BEDA" in p for p in probs), probs)

    def test_same_epoch_twice_and_broken_continuity_are_flagged(self):
        self.epoch(NOW, [])
        self.epoch(NOW + 3600, [])                                    # epoch sama
        probs = book_live.verify_book(ledger.load(self.path))
        self.assertTrue(any("tidak naik" in p for p in probs), probs)

    def test_structured_killer_removes_non_identity_but_not_last_identity(self):
        b = book_live.current_book(self.recs)
        b2 = slots.apply(b, slots.Decision(slots.ADMIT, None, "uji"), chall(b), NOW - 40 * DAY_S)
        rec = book_live.build_epoch(b2, NOW, NOW * 1000, {"B1-TREND": None, "B3-CARRY": None}, [], {"B1-TREND": "YA", "B3-CARRY": "YA"})
        self.assertEqual(rec["dikeluarkan"], ["B3-CARRY"])            # B1 = identitas terakhir: tidak dikeluarkan
        self.assertEqual([e["bot_id"] for e in rec["buku"]], ["B1-TREND"])

    def test_scores_are_inputs_not_hidden_state(self):
        rec = self.epoch(NOW, [], scores={"B1-TREND": 12.5})
        self.assertEqual(rec["buku"][0]["score_bps"], 12.5)
        self.assertEqual(book_live.verify_book(ledger.load(self.path)), [])


if __name__ == "__main__":
    unittest.main()

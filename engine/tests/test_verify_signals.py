"""Pemeriksa publik komit sinyal (P106, tools/verify_signals.py): vonis per (bot, bar) terhadap tiruan chain yang dibangun dari tick ledger repo.
Jalur penuh di anvil ada di test_signal_commit.AnvilEndToEndTests.test_public_verifier_reads_back_sah."""
import os
import sys
import unittest

from engine import chain
from engine.spec import SPECS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import signal_commit as sc                                          # noqa: E402
import verify_signals as vs                                         # noqa: E402
from paper_tick import Views                                        # noqa: E402

LEDGER = os.path.join(ROOT, "ledger", "paper")
BARS = os.path.join(ROOT, "ledger", "bars")
COMMITTER = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
OTHER = "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"
SEED = b"\x07" * 32
B3_BAR = 1_790_812_800_000
ASOF = (B3_BAR + 86_400_000) // 1000


class Cv:
    def __init__(self, locked=ASOF - 3600):
        self.locked = locked

    def max_lag(self):
        return 43_200

    def reveal_window(self):
        return 604_800

    def locked_at(self, committer, bot, spec):
        return self.locked if committer.lower() == COMMITTER.lower() else 0


def scenario(bot="B3-CARRY", committer=COMMITTER, drop=0, tamper=False):
    spec = SPECS[bot]
    tk = next(r for r in sc.ledger.load(os.path.join(LEDGER, f"{bot}.jsonl")) if r["type"] == "tick" and r["asof"] == B3_BAR)
    sigs, probs = sc.rebuild_signals(spec, tk, Views(BARS))
    assert not probs
    b = sc.batch_for(spec, tk, sigs, SEED)
    cid = sc.commit_id(committer, bot, spec.sha(), ASOF)
    c = {"committer": committer, "asof": ASOF, "committedAt": ASOF + 36_000, "n": len(b.entries), "revealed": len(b.entries) - drop, "missed": False,
         "botId": chain.ascii32(bot), "specSha": chain.from_hex(spec.sha()), "root": b.root}
    evs = []
    for e in b.entries[:len(b.entries) - drop]:
        f = e.signal.abi_fields()
        evs.append({"leaf": e.leaf, "asset": f[4], "aksi": f[5], "bobotLama": f[6], "bobotBaru": f[7] + (1 if tamper else 0), "hargaRef": f[8],
                    "dataHash": f[9], "salt": e.salt})
    return cid, c, evs


def row_of(rows, bot="B3-CARRY", bar="2026-10-01"):
    got = [r for r in rows if r.bot == bot and r.bar == bar]
    assert len(got) == 1, [(r.bot, r.bar, r.vonis) for r in rows]
    return got[0]


class VerifyTests(unittest.TestCase):
    def run_v(self, commits, events, now=ASOF + 40_000, cv=None, bots=("B3-CARRY",)):
        return vs.verify(list(bots), LEDGER, Views(BARS), cv or Cv(), commits, events, COMMITTER, now)

    def test_full_reveal_matching_ledger_is_sah(self):
        cid, c, evs = scenario()
        rows, st = self.run_v([(cid, c)], {cid: evs})
        r = row_of(rows)
        self.assertEqual(r.vonis, "SAH", r.detail)
        self.assertEqual((r.n, st["ALARM"], st["komit_resmi"]), (2, 0, 1))

    def test_tampered_payload_is_alarm(self):
        cid, c, evs = scenario(tamper=True)
        r = row_of(self.run_v([(cid, c)], {cid: evs})[0])
        self.assertEqual(r.vonis, "ALARM")
        self.assertIn("tidak bisa dihitung ulang", r.detail)

    def test_partial_reveal_inside_and_after_window(self):
        cid, c, evs = scenario(drop=1)
        self.assertEqual(row_of(self.run_v([(cid, c)], {cid: evs})[0]).vonis, "BELUM DIUNGKAP")
        self.assertEqual(row_of(self.run_v([(cid, c)], {cid: evs}, now=ASOF + 604_801)[0]).vonis, "TIDAK DIUNGKAP")

    def test_missing_commit_states(self):
        self.assertEqual(row_of(self.run_v([], {}, now=ASOF + 3_600)[0]).vonis, "MENUNGGU KOMIT")
        self.assertEqual(row_of(self.run_v([], {}, now=ASOF + 50_000)[0]).vonis, "TIDAK DIKOMIT")
        self.assertEqual(row_of(self.run_v([], {}, cv=Cv(locked=ASOF + 1))[0]).vonis, "SEBELUM KUNCI")

    def test_commit_from_other_address_is_counted_not_trusted(self):
        cid, c, evs = scenario(committer=OTHER)
        rows, st = self.run_v([(cid, c)], {cid: evs}, now=ASOF + 50_000)
        self.assertEqual(row_of(rows).vonis, "TIDAK DIKOMIT")
        self.assertEqual((st["komit_resmi"], st["komit_alamat_lain_untuk_bot_kita"]), (0, 1))

    def test_official_commit_without_ledger_tick_is_alarm(self):
        cid, c, evs = scenario()
        c2 = dict(c, asof=ASOF + 5 * 86_400)
        cid2 = sc.commit_id(COMMITTER, "B3-CARRY", SPECS["B3-CARRY"].sha(), ASOF + 5 * 86_400)
        rows, st = self.run_v([(cid, c), (cid2, c2)], {cid: evs})
        self.assertEqual(st["ALARM"], 1)
        self.assertTrue(any(r.vonis == "ALARM" and "tanpa tick" in r.detail for r in rows))

    def test_rebuilt_leaf_matches_engine_leaf(self):
        cid, c, evs = scenario()
        for ev in evs:
            leaf, _ = vs.rebuild_leaf(c, ev)
            self.assertEqual(leaf, ev["leaf"])


if __name__ == "__main__":
    unittest.main()

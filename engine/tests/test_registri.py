"""P83: registri pengajuan = penghitung percobaan global per keluarga; gerbang pengajuan ke-k dinilai dengan alpha A1/k (F-D88)."""
import os
import shutil
import tempfile
import unittest
from unittest import mock

from engine import anggaran, ledger, registri, review as reviewmod
from engine.gates import GateParams
from engine.slots import SlotParams

from .helpers import BNB, ETH, md_perp, regime_closes
from .test_submission import example

FAST = GateParams.fast()
DAY = 86_400
T = 1_791_000_000
X, Y, Z, P, Q = ("0x" + c * 40 for c in "abcde")
IDENT = {"signature": "0x00", "chain_id": 97, "nonce": 1, "deadline": 2, "now_s": 1}


def entry(issuer, payout, t_s, vonis="TOLAK", k=1):
    return {"type": "pengajuan", "t_s": t_s, "t_utc": "-", "issuer": issuer, "payout": payout, "bot_id": "X", "submission_sha": "0x1", "spec_sha": "0x2",
            "fingerprint": "0x3", "report_sha": "0x4", "vonis": vonis, "k": k, "alpha": anggaran.alpha_for(k), "n_trials": 1}


def chain(*entries):
    out = []
    for e in entries:
        out.append(ledger.seal(e, ledger.head(out)))
    return out


class BudgetTests(unittest.TestCase):
    def test_gate_v1_is_the_first_submission_and_the_kth_is_judged_at_a1_over_k(self):
        base = GateParams()
        a1 = anggaran.Anggaran().a1_per_pengajuan
        self.assertEqual((base.boot_q, base.placebo_max_p), (a1, 2.0 * a1))                    # G3 pada A1; G8 pada c x A1, c = 2,0 (F-D129)
        self.assertIs(anggaran.gate_params_for(1, base), base)
        g = anggaran.gate_params_for(4, base)
        self.assertEqual((g.boot_q, g.placebo_max_p), (0.0125, 0.025))                          # pengali c berlaku pada alpha A1/k
        lama = anggaran.gate_params_for(4, GateParams(placebo_max_p=a1))
        self.assertEqual(lama.placebo_max_p, 0.0125)                                             # c = 1 = perilaku kunci sebelumnya
        self.assertEqual((g.boot_n, g.placebo_n), (4 * base.boot_n, 4 * base.placebo_n))
        # dengan 0 placebo di atas Sharpe asli, batas atas p ~ 2,6/N harus bisa <= alpha: tanpa penskalaan G8 mustahil lolos
        g26 = anggaran.gate_params_for(26, base)
        self.assertLessEqual(2.645 / g26.placebo_n, g26.placebo_max_p)
        self.assertGreater(2.645 / base.placebo_n, g26.placebo_max_p)


class FamilyTests(unittest.TestCase):
    def test_shared_payout_joins_issuers_into_one_family(self):
        es = chain(entry(X, P, T), entry(Y, P, T + DAY, k=2))
        st = registri.status_keluarga(es, Z, P, T + 40 * DAY)
        self.assertEqual(st["k"], 3)
        self.assertEqual(set(st["anggota"]), {X, Y, Z, P})
        self.assertEqual(registri.status_keluarga(es, Z, Q, T + 40 * DAY)["k"], 1)           # dompet lain = keluarga lain (batas Sybil)

    def test_window_is_365_days_and_form_rejections_cost_nothing(self):
        es = chain(entry(X, X, T), entry(X, X, T + 100 * DAY, vonis="TOLAK_FORMULIR"))
        self.assertEqual(registri.status_keluarga(es, X, X, T + 364 * DAY)["k"], 2)
        self.assertEqual(registri.status_keluarga(es, X, X, T + 366 * DAY)["k"], 1)

    def test_cooldown_after_a_rejection_is_read_from_the_registry(self):
        es = chain(entry(X, X, T, vonis="TOLAK"))
        self.assertFalse(registri.status_keluarga(es, X, X, T + 10 * DAY)["boleh_ajukan"])
        self.assertTrue(registri.status_keluarga(es, X, X, T + (SlotParams().cooldown_days + 1) * DAY)["boleh_ajukan"])
        self.assertTrue(registri.status_keluarga(chain(entry(X, X, T, vonis="LOLOS_SHADOW")), X, X, T + DAY)["boleh_ajukan"])

    def test_verify_recomputes_k_and_catches_a_made_up_one(self):
        good = chain(entry(X, X, T), entry(X, X, T + 40 * DAY, k=2))
        self.assertEqual(registri.verify(good), [])
        faked = chain(entry(X, X, T), entry(X, X, T + 40 * DAY, k=1))
        self.assertTrue(any("hitung ulang 2" in p for p in registri.verify(faked)))
        broken = [dict(good[0], vonis="LOLOS_SHADOW"), good[1]]
        self.assertTrue(any("rantai hash" in p for p in registri.verify(broken)))
        back = chain(entry(X, X, T + DAY), entry(Y, Y, T))
        self.assertTrue(any("mundur" in p for p in registri.verify(back)))


class RegistryReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "registri.jsonl")
        self.md = md_perp({ETH: regime_closes(1500, 21), BNB: regime_closes(1500, 22)})

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_(self, now_s, catat=True, identity=IDENT):
        with mock.patch.object(reviewmod.submission, "verify_identity", return_value=[]):
            return reviewmod.tinjau_tercatat(example(), self.md, None, path=self.path, now_s=now_s, catat=catat, identity=identity, gate_params=FAST)

    def test_unreadable_or_broken_registry_is_tolak_and_no_gate_runs(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("{bukan json\n")
        with mock.patch.object(reviewmod, "run_gates") as gates:
            rc, rep, msgs = self.run_(T)
        self.assertEqual((rc, rep), (3, None))
        self.assertTrue(any("k tidak ditebak" in m for m in msgs))
        gates.assert_not_called()
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(ledger.canon(dict(chain(entry(X, X, T))[0], k=5)) + "\n")
        rc, rep, msgs = self.run_(T + DAY)
        self.assertEqual(rc, 3)
        self.assertTrue(any("registri rusak" in m for m in msgs))

    def test_recorded_submissions_raise_k_and_the_cooldown_blocks_a_quick_retry(self):
        rc, rep, _ = self.run_(T)
        self.assertEqual((rep["keluarga"]["k"], rep["keluarga"]["alpha"], rep["keluarga"]["sumber"]), (1, 0.05, "registri"))
        es = registri.load(self.path)
        self.assertEqual(len(es), 1)
        self.assertEqual(registri.verify(es), [])
        if rep["vonis"] != "LOLOS_SHADOW":
            rc2, rep2, msgs = self.run_(T + 5 * DAY)
            self.assertEqual((rc2, rep2), (1, None))
            self.assertTrue(any("ANTREAN" in m for m in msgs))
            self.assertEqual(len(registri.load(self.path)), 1)                  # yang ditolak antrean tidak dicatat
        rc3, rep3, _ = self.run_(T + 40 * DAY)
        self.assertEqual((rep3["keluarga"]["k"], rep3["keluarga"]["alpha"]), (2, 0.025))
        self.assertEqual(rep3["n_trials"], 6 + 1 + 1)
        g3 = [g for g in rep3["gerbang"] if g["gate"] == "G3"][0]
        self.assertIn("persentil-2.5", g3["rule"])
        self.assertEqual(registri.verify(registri.load(self.path)), [])

    def test_preview_and_unverified_identity_are_never_recorded_or_binding(self):
        rc, rep, _ = self.run_(T, catat=False)
        self.assertEqual(rep["keluarga"]["sumber"], "pratinjau")
        self.assertFalse(os.path.exists(self.path))
        rc, rep, msgs = reviewmod.tinjau_tercatat(example(), self.md, None, path=self.path, now_s=T, catat=True, identity=None, gate_params=FAST)
        self.assertEqual(rep["keluarga"]["sumber"], "tidak-dicatat")
        self.assertFalse(rep["mengikat"])
        self.assertTrue(any("TIDAK dicatat" in m for m in msgs))
        self.assertFalse(os.path.exists(self.path))
        body = {k: v for k, v in rep.items() if k != "report_sha"}
        from engine.spec import sha0x
        self.assertEqual(rep["report_sha"], sha0x(body))                        # disegel ulang sesudah diturunkan

    def test_binding_needs_k_from_the_registry(self):
        locked = {"state": "TERKUNCI", "sha_kini": "0x1", "sha_kunci": "0x1", "berkas": "x"}
        with mock.patch.object(reviewmod.locks, "status", return_value=locked), \
             mock.patch.object(reviewmod, "verdict", return_value=("LOLOS_SHADOW", [], [])):
            _, pre, _ = self.run_(T, catat=False)
            with mock.patch.object(reviewmod.submission, "verify_identity", return_value=[]):
                manual = reviewmod.review(example(), self.md, None, gate_params=FAST, identity=IDENT, prior_family_submissions=0)
            _, rec, _ = self.run_(T)
        self.assertFalse(pre["mengikat"])
        self.assertEqual(manual["keluarga"]["sumber"], "manual")
        self.assertFalse(manual["mengikat"])
        self.assertTrue(rec["mengikat"])
        self.assertIn("sumber k: registri", reviewmod.render(rec))


if __name__ == "__main__":
    unittest.main()

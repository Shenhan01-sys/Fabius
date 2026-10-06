"""P161 B1b: peninjau pengajuan di repo publik - kiriman antrean gerbang ditinjau dengan identitas diverifikasi ULANG pada waktu terima, registri
hash-berantai + laporan + spesifikasi lolos ditulis, kontak tidak pernah sampai ke repo, kiriman yang tertahan masa tunggu dicoba lagi."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from engine import registri, submission
from engine.gates import GateParams

from .helpers import BNB, ETH, md_perp, regime_closes
from .test_submission import Account, encode_typed_data, example

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import tinjau_pengajuan as tp                                       # noqa: E402

T = 1_791_000_000


def kiriman(acct, t, bot_id="TREND-ETH-30", param=30, nonce=1):
    sub = example()
    sub["identity"]["issuer_wallet"] = sub["identity"]["payout_wallet"] = acct.address
    sub["spec"]["bot_id"], sub["spec"]["param"] = bot_id, param
    sig = "0x" + acct.sign_message(encode_typed_data(full_message=submission.typed_data(sub, 97, nonce, t + 600))).signature.hex().removeprefix("0x")
    pub = json.loads(json.dumps(sub))
    pub["identity"].pop("contact")
    return {"t": t, "submission_sha": submission.submission_sha(sub), "spec_sha": submission.spec_sha_of(sub), "bot_id": bot_id, "issuer": acct.address,
            "payout": acct.address, "chain_id": 97, "nonce": nonce, "deadline": t + 600, "signature": sig, "payout_signature": None, "submission": pub,
            "status": "waiting for review"}


@unittest.skipIf(Account is None, "eth-account tidak terpasang")
class TinjauTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.md = md_perp({ETH: regime_closes(1500, 21), BNB: regime_closes(1500, 22)})
        self.acct = Account.create()                                # kunci sekali-pakai untuk tes

    def test_a_queued_submission_is_reviewed_recorded_and_its_files_are_public_without_the_contact(self):
        row = kiriman(self.acct, T)
        out = tp.tinjau([row], self.tmp, self.md, None, gate_params=GateParams.fast(), log=lambda m: None)
        self.assertEqual(len(out), 1)
        reg = registri.load(os.path.join(self.tmp, "registri.jsonl"))
        self.assertEqual((len(reg), reg[0]["submission_sha"], reg[0]["t_s"]), (1, row["submission_sha"], T))   # waktu = waktu terima di gerbang
        self.assertEqual(registri.verify(reg), [])
        rep = json.load(open(os.path.join(self.tmp, "laporan", f"{row['submission_sha']}.json"), encoding="utf-8"))
        self.assertTrue(rep["identitas"]["diverifikasi"])                                        # tanda tangan diverifikasi ulang pada t terima
        self.assertEqual(rep["vonis"], out[0]["vonis"])
        for root, _, files in os.walk(self.tmp):
            for fn in files:
                self.assertNotIn("contoh@example.invalid", open(os.path.join(root, fn), encoding="utf-8").read())
        spec_path = os.path.join(self.tmp, "spec", "TREND-ETH-30.json")
        self.assertEqual(os.path.exists(spec_path), rep["vonis"] == registri.LOLOS)
        self.assertEqual(tp.tinjau([row], self.tmp, self.md, None, gate_params=GateParams.fast(), log=lambda m: None), [])   # tidak ditinjau dua kali

    def test_a_lolos_shadow_verdict_writes_the_spec_with_its_structured_killer(self):
        row = kiriman(self.acct, T)
        fake = {"vonis": registri.LOLOS, "spec_sha": row["spec_sha"], "report_sha": "0xr", "identitas": {"diverifikasi": True}}
        with mock.patch.object(tp.reviewmod, "tinjau_tercatat", return_value=(0, fake, ["ok"])):
            tp.tinjau([row], self.tmp, self.md, None, log=lambda m: None)
        spec = json.load(open(os.path.join(self.tmp, "spec", "TREND-ETH-30.json"), encoding="utf-8"))
        self.assertEqual((spec["submission_sha"], spec["botspec"]["bot_id"], spec["botspec"]["param"]), (row["submission_sha"], "TREND-ETH-30", 30))
        self.assertEqual(spec["pembunuh"], row["submission"]["theory"]["pembunuh"])

    def test_waiting_family_cooldown_is_kept_queued_and_a_tampered_row_is_rejected(self):
        row = kiriman(self.acct, T)
        with mock.patch.object(tp.reviewmod, "tinjau_tercatat", return_value=(1, None, ["ANTREAN: masa tunggu 30 hari"])):
            out = tp.tinjau([row], self.tmp, self.md, None, log=lambda m: None)
        st = json.load(open(os.path.join(self.tmp, "status.json"), encoding="utf-8"))
        self.assertEqual((out[0]["vonis"], st[row["submission_sha"]]["status"], st[row["submission_sha"]]["final"]), (None, "queued", False))
        palsu = dict(row, submission_sha="0x" + "00" * 32)
        out = tp.tinjau([palsu], self.tmp, self.md, None, log=lambda m: None)
        self.assertEqual(out[0]["vonis"], "SHA_TIDAK_COCOK")


if __name__ == "__main__":
    unittest.main()

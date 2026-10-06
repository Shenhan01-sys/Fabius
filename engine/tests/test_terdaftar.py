"""P161 B1c: bot penerbit LOLOS_SHADOW ikut jam maju - BotSpec disusun ulang dari formulir publik yang cocok dengan registri; formulir yang diubah,
vonis lain, atau registri rusak tidak pernah dijalankan; genesis ledger maju ditulis dengan sha BotSpec itu."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from engine import anggaran, ledger, registri, submission, terdaftar

from .test_submission import example

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
T = 1_791_000_000


def pasang(root, vonis=registri.LOLOS, ubah=False):
    d = os.path.join(root, "ledger", "pengajuan")
    os.makedirs(os.path.join(d, "masuk"), exist_ok=True)
    sub = example()
    sha, spec_sha = submission.submission_sha(sub), submission.spec_sha_of(sub)
    pub = json.loads(json.dumps(sub))
    pub["identity"].pop("contact")
    if ubah:
        pub["spec"]["param"] = 99                                   # isi diubah sesudah lolos
    with open(os.path.join(d, "masuk", f"{sha}.json"), "w", encoding="utf-8") as f:
        json.dump({"submission_sha": sha, "submission": pub}, f)
    e = {"type": "pengajuan", "t_s": T, "t_utc": "-", "issuer": sub["identity"]["issuer_wallet"], "payout": sub["identity"]["payout_wallet"],
         "bot_id": sub["spec"]["bot_id"], "submission_sha": sha, "spec_sha": spec_sha, "fingerprint": "0x3", "report_sha": "0x4", "vonis": vonis, "k": 1,
         "alpha": anggaran.alpha_for(1), "n_trials": 1}
    with open(os.path.join(d, "registri.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps(ledger.seal(e, ledger.head([])), sort_keys=True) + "\n")
    return sub


class TerdaftarTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_a_passing_submission_runs_as_the_botspec_rebuilt_from_its_public_form(self):
        sub = pasang(self.tmp)
        specs, masalah = terdaftar.penerbit(self.tmp)
        self.assertEqual(masalah, [])
        self.assertEqual(specs["TREND-ETH-30"], submission.to_botspec(sub))
        self.assertIn("B1-TREND", terdaftar.semua(self.tmp))                                   # bot Fabius tetap ada

    def test_tampered_forms_other_verdicts_and_broken_registries_never_run(self):
        pasang(self.tmp, ubah=True)
        specs, masalah = terdaftar.penerbit(self.tmp)
        self.assertEqual((specs, len(masalah)), ({}, 1))
        pasang(self.tmp, vonis="TOLAK")
        self.assertEqual(terdaftar.penerbit(self.tmp)[0], {})
        pasang(self.tmp)
        with open(os.path.join(self.tmp, "ledger", "pengajuan", "registri.jsonl"), "a", encoding="utf-8") as f:
            f.write('{"type": "pengajuan", "h": "0xpalsu"}\n')
        self.assertEqual(terdaftar.penerbit(self.tmp)[0], {})

    def test_the_forward_clock_starts_with_the_submitted_spec(self):
        import paper_tick as pt
        sub = pasang(self.tmp)
        led = os.path.join(self.tmp, "paper")
        os.makedirs(led)
        with mock.patch.object(pt, "ROOT", self.tmp), mock.patch("builtins.print"):
            self.assertEqual(pt.init_bot("TREND-ETH-30", led, (T + 5 * 86_400) * 1000, False), 0)
            self.assertEqual(pt.init_bot("TIDAK-ADA", led, (T + 5 * 86_400) * 1000, False), 3)
        g = ledger.load(os.path.join(led, "TREND-ETH-30.jsonl"))[0]
        self.assertEqual((g["type"], g["bot_id"], g["spec_sha"]), ("genesis", "TREND-ETH-30", submission.to_botspec(sub).sha()))
        self.assertIn("P161", g["note"])


class PembunuhPenerbitTests(unittest.TestCase):
    """P161 B1d: pembunuh terstruktur kiriman ditegakkan di epoch buku dari ledger maju penerbit."""

    def ledger_(self, nets, sinyal_per_hari=1):
        recs = [{"type": "genesis"}]
        for i, x in enumerate(nets):
            t = (20_000 + i) * 86_400_000
            recs.append({"type": "tick", "asof": t, "signal_ids": ["s"] * sinyal_per_hari})
            recs.append({"type": "settle", "bar": t, "net": x})
        return recs

    def test_pnl_window_starts_at_the_nth_last_signal(self):
        pnl, n = terdaftar.pnl_sejak_sinyal(self.ledger_([0.01, -0.02, 0.03, -0.04]), 2)
        self.assertEqual((pnl, n), ([0.03, -0.04], 4))
        self.assertEqual(terdaftar.pnl_sejak_sinyal(self.ledger_([0.01]), 5), ([], 1))

    def test_a_triggered_issuer_killer_marks_the_occupant_ya(self):
        from engine import cli
        killer = {"metric": "net_pnl_bps", "comparator": "<", "threshold": -100, "window_sinyal": 3}
        luar = {"TREND-ETH-30": {"pembunuh": killer}}
        book = [type("E", (), {"bot_id": "TREND-ETH-30"})()]
        with mock.patch.object(terdaftar, "rincian", return_value=(luar, [])):
            ok = {"TREND-ETH-30": self.ledger_([-0.01, -0.01, -0.01])}                     # -300 bps < -100
            self.assertEqual(cli._book_killers(book, ok, None, 0)["TREND-ETH-30"], "YA")
            ok = {"TREND-ETH-30": self.ledger_([0.01, 0.01, 0.01])}
            self.assertEqual(cli._book_killers(book, ok, None, 0)["TREND-ETH-30"], "TIDAK")
            ok = {"TREND-ETH-30": self.ledger_([-0.05])}                                    # baru 1 sinyal < 3: belum bisa dinilai
            self.assertEqual(cli._book_killers(book, ok, None, 0)["TREND-ETH-30"], "BELUM")
            self.assertEqual(cli._book_killers(book, {}, None, 0)["TREND-ETH-30"], "TEKS")


if __name__ == "__main__":
    unittest.main()

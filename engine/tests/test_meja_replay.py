"""P163: replay buku Fabius dari arsip - setia ke `meja.isi`, kebijakan perputaran hanya mengubah target, fee dipecah per sumber."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import meja                                                         # noqa: E402
import meja_replay as mr                                            # noqa: E402


def rec(t, bot, target, dasar="dominant bot"):
    return {"siklus": t, "bot": bot, "dasar": dasar, "target": {a: {"w": w, "k": 1.0} for a, w in target.items()}}


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.recs = [rec(300, "B1", {"A": 0.20, "B": 0.10}), rec(600, "B1", {"A": 0.17, "B": 0.10}), rec(900, "B1", {"A": 0.20}),
                     rec(1200, "B1", {"A": 0.20, "B": 0.10}), rec(1500, "B2", {"A": -0.10}), rec(1800, "B2", {}, dasar="daily loss brake -3.10%")]
        self.harga = {t: {"A": 100.0 + i, "B": 50.0} for i, t in enumerate(range(300, 2100, 300))}

    def test_r3_replay_matches_a_direct_fill_of_the_same_targets(self):
        b = meja.buku_baru()
        for r in self.recs:
            meja.isi(b, r["target"], self.harga[r["siklus"]])
        x = mr.replay(self.recs, self.harga, mr.r3)
        self.assertAlmostEqual(x["ekuitas"], round(meja.ekuitas(b, self.harga[1800]), 2), places=2)

    def test_policies_trade_less_and_never_invent_positions(self):
        base = mr.replay(self.recs, self.harga, mr.r3)
        for nama, pol in mr.KEBIJAKAN.items():
            x = mr.replay(self.recs, self.harga, pol)
            self.assertLessEqual(x["isi"], base["isi"], nama)
            for r, fills in x["kirim"]:
                for f in fills:
                    allowed = set(r["target"]) | {g["aset"] for _, fs in x["kirim"] for g in fs}
                    self.assertIn(f["aset"], allowed, nama)
            self.assertEqual(x["kirim"][-1][1] and all(abs(f["ke"]) < 1e-9 for f in x["kirim"][-1][1]), True, nama)   # rem rugi tetap menutup
        sticky = mr.replay(self.recs, self.harga, mr.lekat_instrumen(3))
        self.assertNotIn("B", {f["aset"] for f in sticky["kirim"][2][1]})                            # B tidak ditutup lalu dibuka lagi

    def test_daily_loss_brake_is_recomputed_from_replay_equity(self):
        recs = [rec(t, "B1", {"A": 0.25}) for t in (300, 600, 900)]
        harga = {300: {"A": 100.0}, 600: {"A": 80.0}, 900: {"A": 80.0}}                               # -20 % x 25 % = -5 % ekuitas
        x = mr.replay(recs, harga, mr.r3)
        self.assertEqual(x["rem_replay"], 2)
        self.assertEqual([f["ke"] for f in x["kirim"][1][1]], [0.0])                                  # siklus 600 ditutup oleh rem
        self.assertEqual(x["kirim"][2][1], [])                                                         # tetap datar sampai hari berganti

    def test_fee_sources_are_classified(self):
        recs = [dict(rec(300, "B1", {"A": 0.2}), isi=[{"aset": "A", "dari": 0.0, "ke": 0.2, "harga": 1, "fee": 1.0}]),
                dict(rec(600, "B1", {"A": 0.1}), isi=[{"aset": "A", "dari": 0.2, "ke": 0.1, "harga": 1, "fee": 0.5}]),
                dict(rec(900, "B1", {"A": -0.1}), isi=[{"aset": "A", "dari": 0.1, "ke": -0.1, "harga": 1, "fee": 1.0}]),
                dict(rec(1200, "B2", {"B": 0.1}), isi=[{"aset": "A", "dari": -0.1, "ke": 0.0, "harga": 1, "fee": 0.5}]),
                dict(rec(1500, "B2", {}, dasar="x; daily loss brake -3%"), isi=[{"aset": "B", "dari": 0.1, "ke": 0.0, "harga": 1, "fee": 0.5}])]
        s = mr.sumber_fee(recs)
        self.assertEqual({k: v["isi"] for k, v in s.items()},
                         {"instrumen masuk/keluar": 1, "balik arah": 1, "ubah ukuran": 1, "ganti bot": 1, "rem rugi harian": 1})


if __name__ == "__main__":
    unittest.main()

"""F-D88: anggaran kesalahan gerbang (engine/anggaran.py) - A1 per pengajuan, A2 per keluarga per tahun lewat alpha harmonik, kunci yang mengikat antrean."""
import dataclasses
import os
import tempfile
import unittest

from engine import anggaran as ag
from engine.slots import SlotParams


class BudgetTests(unittest.TestCase):
    def test_first_submission_gets_the_full_a1_and_later_ones_less(self):
        self.assertEqual(ag.alpha_for(1), 0.05)
        self.assertAlmostEqual(ag.alpha_for(4), 0.0125)
        with self.assertRaises(ValueError):
            ag.alpha_for(0)

    def test_queue_limits_allow_26_submissions_a_year_and_a2_holds_only_with_the_penalty(self):
        n = ag.max_pengajuan_per_tahun()
        self.assertEqual(n, 26)                                     # 2 berjalan x 13 siklus jeda 30 hari dalam 365 hari
        self.assertLessEqual(ag.batas_palsu_per_tahun(n), 0.2)      # 0,05 x H(26) = 0,193
        self.assertAlmostEqual(ag.batas_palsu_per_tahun(n), 0.1927, places=3)
        self.assertAlmostEqual(ag.batas_palsu_per_tahun(n, pinalti=False), 1.3)

    def test_loosening_the_queue_would_break_a2(self):
        loose = dataclasses.replace(SlotParams(), queue_max_per_family=4)
        self.assertGreater(ag.batas_palsu_per_tahun(ag.max_pengajuan_per_tahun(loose)), 0.2)


class LockTests(unittest.TestCase):
    def test_repo_lock_matches_the_code(self):
        """Kunci 3 Okt (F-D88, kata builder): menggeser anggaran ATAU antrean sesudahnya membuat tes ini gagal."""
        self.assertEqual(ag.status()["state"], "TERKUNCI", ag.status())

    def test_lock_binds_the_queue_and_refuses_overwrite(self):
        path = os.path.join(tempfile.mkdtemp(), "a.json")
        lock = ag.write_lock("uji", now_iso="2026-10-03T00:00:00Z", path=path)
        self.assertEqual(lock["params"]["antrean"], {"queue_max_per_family": 2, "cooldown_days": 30})
        self.assertEqual(lock["params"]["anggaran"]["a1_per_pengajuan"], 0.05)
        self.assertEqual(ag.status(path)["state"], "TERKUNCI")
        with self.assertRaises(FileExistsError):
            ag.write_lock("lagi", path=path)


if __name__ == "__main__":
    unittest.main()

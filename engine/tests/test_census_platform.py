"""P186 (28 Okt 2026): `tools/test_census.py --wajib-semua` tidak menghitung skip khusus platform LAIN (tes Windows di runner Linux), tapi tetap
menggagalkan skip karena dependensi/keadaan yang hilang."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools"))
import test_census as tc                                                  # noqa: E402


class PlatformSkipTests(unittest.TestCase):
    def test_windows_only_test_on_linux_is_a_platform_skip(self):
        self.assertTrue(tc.platform_skip("khusus Windows: DACL", "posix"))

    def test_windows_only_test_on_windows_still_counts(self):
        self.assertFalse(tc.platform_skip("khusus Windows: DACL", "nt"))

    def test_missing_dependency_or_state_still_counts(self):
        self.assertFalse(tc.platform_skip("kunci ini belum ter-anchor (belum ada catatan)", "posix"))
        self.assertFalse(tc.platform_skip("anvil tidak terpasang", "posix"))


if __name__ == "__main__":
    unittest.main()

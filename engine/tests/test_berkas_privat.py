"""P167b: berkas kode privat hanya bisa dibaca akun proses ini - POSIX mode 0600, Windows DACL terlindung satu ACE (dibaca ulang dari sistem berkas)."""
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from engine import berkas_privat                                  # noqa: E402


class BerkasPrivatTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="privat-")

    def test_a_private_file_is_owner_only_and_keeps_its_text(self):
        p = os.path.join(self.tmp, "kode", "abc.py")
        os.makedirs(os.path.dirname(p))
        berkas_privat.tulis(p, "def target(bars, params):\n    return {}\n")
        with open(p, encoding="utf-8") as f:
            self.assertEqual(f.read(), "def target(bars, params):\n    return {}\n")
        self.assertTrue(berkas_privat.hanya_pemilik(p))
        berkas_privat.tulis(p, "baru\n")                                                    # tulis ulang tetap tertutup
        self.assertTrue(berkas_privat.hanya_pemilik(p))

    def test_an_ordinary_file_is_not_reported_as_private(self):
        p = os.path.join(self.tmp, "biasa.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("x")
        if os.name != "nt":
            os.chmod(p, 0o644)
        self.assertFalse(berkas_privat.hanya_pemilik(p))                                   # pemeriksa tidak hampa

    @unittest.skipUnless(os.name == "nt", "khusus Windows: DACL")
    def test_on_windows_the_file_and_its_folder_carry_one_protected_ace_for_this_account(self):
        p = os.path.join(self.tmp, "kode", "abc.py")
        os.makedirs(os.path.dirname(p))
        berkas_privat.tulis(p, "x")
        sid = berkas_privat.sid_saya()
        self.assertRegex(sid, r"^S-1-5-")
        self.assertEqual(berkas_privat.dacl_sddl(p), f"D:P(A;;FA;;;{sid})")                 # tanpa warisan, tanpa Administrators / SYSTEM / Users
        d = berkas_privat.dacl_sddl(os.path.dirname(p))
        self.assertTrue(d.startswith("D:P"), d)
        self.assertEqual(re.findall(r"\(([^)]*)\)", d), [f"A;OICI;FA;;;{sid}"])            # berkas baru di folder ini tertutup sejak dibuat
        q = os.path.join(os.path.dirname(p), "lain.txt")
        with open(q, "w", encoding="utf-8") as f:
            f.write("x")
        aces = re.findall(r"\(([^)]*)\)", berkas_privat.dacl_sddl(q))                     # berkas biasa di folder itu: hanya ACE warisan kita
        self.assertEqual(len(aces), 1, aces)
        self.assertRegex(aces[0], r"^A;(ID)?;FA;;;" + re.escape(sid) + "$")


if __name__ == "__main__":
    unittest.main()

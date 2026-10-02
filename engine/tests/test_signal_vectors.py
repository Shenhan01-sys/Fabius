"""Vektor lintas bahasa SignalAnchor (M3): fixture `test/fixtures/signal_vectors.json` harus persis sama dengan yang dihasilkan engine sekarang.

Kalau penyandian sinyal di `engine/sinyal.py` berubah, tes ini gagal lebih dulu (sebelum kontrak dan engine diam-diam berbeda): jalankan
`python -X utf8 tools/gen_signal_vectors.py` lalu `forge test --match-contract SignalAnchorTest`."""
import json
import os
import sys
import unittest

from engine import chain

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gen_signal_vectors as gsv                                    # noqa: E402


class SignalVectorTests(unittest.TestCase):
    def test_fixture_matches_the_engine(self):
        with open(gsv.OUT, encoding="utf-8") as f:
            on_disk = f.read().replace("\r\n", "\n")
        self.assertEqual(on_disk, json.dumps(gsv.build(), indent=2, sort_keys=True) + "\n")

    def test_every_proof_verifies_against_its_root_in_python(self):
        data = gsv.build()
        for name in ("tiga", "satu"):
            b = data[name]
            root = chain.from_hex(b["root"])
            for s in b["signals"]:
                self.assertTrue(chain.merkle_verify([chain.from_hex(p) for p in s["proof"]], root, chain.from_hex(s["leaf"])), (name, s["asset"]))

    def test_generation_is_deterministic(self):
        self.assertEqual(json.dumps(gsv.build(), sort_keys=True), json.dumps(gsv.build(), sort_keys=True))


if __name__ == "__main__":
    unittest.main()

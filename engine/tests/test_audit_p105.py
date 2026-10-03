"""P105: temuan audit 1-2 Okt yang diperiksa ulang dan diperbaiki 3 Okt. Tiap tes menunjukkan cacatnya hilang tanpa menulis ulang hash lama.
(b) "net-of-cost" E16/E25 dan (e) README/kartu agen tidak punya tes: (b) dikoreksi di vault (kodenya patuh teks kunci), (e) dokumen."""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "universe"))


class ModelCannotRaiseSizeTests(unittest.TestCase):
    """(a) `tools/direction.py`: confidence model 0,9 dulu menggandakan risk_pct 0,5 % -> 1 %, melanggar "model hanya boleh membatalkan/mengecilkan"."""

    def test_model_confidence_never_raises_risk(self):
        import direction as d
        f = {"ok": True, "n": 10_000, "sma_gap_pct": 0.05, "ret24": 0.03, "acf_abs": 0.5, "last": 1.0, "atr": 0.01}
        with_model = d.decide_one(f, {}, None, {"confidence": 0.9, "side": "long", "probabilities": {}})
        without = d.decide_one(f, {}, None, None)
        self.assertEqual(with_model["side"], "long")
        self.assertEqual(with_model["risk_pct"], d.RISK_SAFE)
        self.assertLessEqual(with_model["risk_pct"], without["risk_pct"])

    def test_model_veto_still_flattens(self):
        import direction as d
        f = {"ok": True, "n": 10_000, "sma_gap_pct": 0.05, "ret24": 0.03, "acf_abs": 0.5, "last": 1.0, "atr": 0.01}
        self.assertEqual(d.decide_one(f, {}, None, {"veto": True, "dominant_risk": "rug", "probabilities": {"rug": 0.7}})["side"], "flat")


class SignTestIsNotVacuousTests(unittest.TestCase):
    """(c) `tools/flow_test.py`: n = 2k untuk wins dari satu kelompok membuat p SELALU 1,0 dan BH tak mungkin lulus."""

    def test_wins_and_n_come_from_the_same_extreme_group(self):
        import flow_test as ft
        hi, lo = [1.0] * 10, [-1.0] * 10
        self.assertEqual(ft.ekstrem_menang(hi, lo, +1), (10, 10))
        self.assertEqual(ft.ekstrem_menang(hi, lo, -1), (0, 10))
        self.assertLess(ft.sign_p(*ft.ekstrem_menang(hi, lo, +1)), 0.01)        # 10/10 menang: p ~ 0,001
        self.assertEqual(ft.sign_p(10, 20), 1.0)                                  # bentuk lama (n = 2k): hampa, apa pun datanya


class SnapshotKeyOrderTests(unittest.TestCase):
    """(d) snapshot universe "60/62": `gdelt.cols_seen` di-hash berkunci int, dimuat ulang berkunci string."""

    def snap(self, keys):
        return {"snapshot_utc": "2026-10-01T00:00:00Z", "gdelt": {"cols_seen": {keys(8): 3, keys(27): 900}, "lines": 903}}

    def test_legacy_int_keys_are_recognised_without_rewriting_the_stored_hash(self):
        import write_universe_manifest as w
        body = self.snap(int)
        stored = w.canon_sha(body)                                               # cara penulis LAMA: hash di memori, kunci int
        row = json.loads(json.dumps(dict(body, sha256=stored)))                  # ditulis lalu dimuat ulang: kunci jadi string
        self.assertEqual(w.verify_row(row), "cocok-kunci-int")
        self.assertEqual(row["sha256"], stored)

    def test_string_keys_hash_the_same_after_reload_and_tampering_is_still_caught(self):
        import write_universe_manifest as w
        body = self.snap(str)                                                    # penulis BARU (P105d)
        row = json.loads(json.dumps(dict(body, sha256=w.canon_sha(body))))
        self.assertEqual(w.verify_row(row), "cocok")
        row["gdelt"]["lines"] = 904
        self.assertEqual(w.verify_row(row), "beda")


if __name__ == "__main__":
    unittest.main()

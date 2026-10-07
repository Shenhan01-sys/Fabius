"""P166: penjawab aturan agent luar uji - jawabannya diurai dari prompt meja v2 SUNGGUHAN dan lolos `meja2.parse2` (validator gerbang yang sama)."""
import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "tools"), ROOT]

import agen_luar_uji_jawab as jw                                   # noqa: E402
import meja                                                        # noqa: E402
import meja2                                                       # noqa: E402

UNI = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "PAXGUSDT"]


def prompt(tren, z):
    snap = {"sha": "0x1", "fitur_aset": {a: {"r_1j": 0.001, "vol_1j": 0.008} for a in UNI}, "fitur_bot": {}}
    far = {a: {"tren_60h": tren[i], "z_10h": z[i], "r_28h": 0.01, "hari_data": 400} for i, a in enumerate(UNI)}
    tick = {a: {"r_24j": 0.01, "volume_24j": 1e9} for a in UNI}
    return meja2.prompt2(snap, UNI, tick, meja.buku_baru(), {a: 100.0 for a in UNI}, None, far), meja2.nama_fitur(snap)


class JawabTests(unittest.TestCase):
    def test_answers_parse_with_the_gate_validator_and_follow_the_stated_rules(self):
        kasus = {"B6-BOUNCE": ([0.1, 0.1, 0.1, -0.1, 0.0], [0.5, -2.6, 0.1, 0.0, 0.2]),
                 "B1-TREND": ([0.12, 0.05, 0.08, -0.1, 0.01], [0.5, -1.0, 0.1, 0.0, 0.2]),
                 "B5-CORE-RWA": ([-0.1, -0.05, 0.02, -0.1, -0.01], [0.5, -1.0, 0.1, 0.0, 0.2])}
        for bot, (tren, z) in kasus.items():
            with self.subTest(bot=bot):
                teks, fitur = prompt(tren, z)
                a, nama = jw.urai(teks)
                self.assertEqual(set(a), set(UNI))
                self.assertIn("tren_60h", nama)
                jawab = jw.putuskan(a, nama)
                d = meja2.parse2(json.dumps(jawab), UNI, fitur)                                      # lolos validator gerbang
                self.assertEqual(d["bot"], bot)
                self.assertTrue(30 <= jawab["keyakinan"] <= 70)
                self.assertEqual([x for x in d["ditolak"] if "faktor" in x], [])                      # tidak mengutip fitur karangan
        self.assertEqual(jw.putuskan(*jw.urai(prompt(*kasus["B6-BOUNCE"])[0]))["instrumen"][0]["aset"], "ETHUSDT")   # paling tertekan

    def test_the_answer_command_reads_stdin_and_prints_one_json(self):
        teks, _ = prompt([0.12, 0.05, 0.08, -0.1, 0.01], [0.5, -1.0, 0.1, 0.0, 0.2])
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "agen_luar_uji_jawab.py")], input=json.dumps({"siklus": 1, "deadline": 2,
                           "system": "s", "prompt": teks}), capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["bot"], "B1-TREND")


if __name__ == "__main__":
    unittest.main()

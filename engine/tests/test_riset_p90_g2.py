"""P90 gelombang 2 (tools/riset_p90_g2.py): protokol tidak boleh bergeser sesudah pra-registrasi; perekam statistik mentah SETIA pada gerbang asli;
aturan pilihan + konfirmasi bekerja seperti ditulis; konfirmasi menolak jalan tanpa pilihan."""
import dataclasses
import math
import os
import random
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import riset_p90 as rp                                              # noqa: E402
import riset_p90_g2 as g2                                           # noqa: E402

from engine import gates                                             # noqa: E402
from engine.spec import sha0x                                        # noqa: E402

# di-push sebelum lari: vault/06-Results/33 - Pra-Registrasi P90 Gelombang 2.md
REGISTERED = "0x4587f1efc4c418ed0b3d6873ed86e3cc922278e5c1250e1d777d206e8b7e2140"


def fast():
    return dataclasses.replace(gates.GateParams.fast(), n_trials=2)


class ProtocolTests(unittest.TestCase):
    def test_protocol_is_the_registered_one(self):
        self.assertEqual(sha0x(g2.PROTOKOL2), REGISTERED)

    def test_wave_one_protocol_is_untouched(self):
        self.assertEqual(sha0x(rp.PROTOKOL), "0xce2f814e334244f8e43c3d9d862b8e654896f3ba1772d20c9e4397e89f2820bd")

    def test_job_counts_and_seeds_are_unique_and_disjoint_from_wave_one_and_the_pilot(self):
        n = {k: len(g2.jobs_for(k)[0]) for k in ("setel-fp", "setel-daya", "konfirmasi-fp", "konfirmasi-daya")}
        self.assertEqual(n, {"setel-fp": 3000, "setel-daya": 3200, "konfirmasi-fp": 6600, "konfirmasi-daya": 4800})
        seeds = []
        for k in n:
            seeds += [j[1] for j in g2.jobs_for(k)[0]]
        self.assertEqual(len(seeds), len(set(seeds)))
        wave1 = [(31_000_000, 31_400_000), (41_000_000, 41_600_000), (51_000_000, 52_000_100), (9_000_000, 9_000_100)]
        for s in seeds:
            self.assertFalse(any(a <= s <= b for a, b in wave1), s)
        self.assertGreater(g2.SEED["pilot"], 9_000_100)                      # pilot gelombang 2 di luar pilot gelombang 1
        self.assertLess(g2.SEED["pilot"] + 100, min(seeds))                  # dan jauh di bawah semua benih protokol

    def test_every_calibrated_mu_the_power_cells_need_is_in_the_protocol(self):
        for (w, u, s, T) in g2.daya_sel():
            self.assertIn(f"{w}|{u}|{s}", g2.MU)

    def test_candidates_include_the_locked_thresholds_once(self):
        c = g2.kandidat()
        self.assertEqual(len(c), 15)
        self.assertEqual(sum(1 for x in c if x == g2.terkunci()), 1)


class WorldTests(unittest.TestCase):
    def test_jump_world_is_reproducible_driftless_and_fat_tailed(self):
        a = g2.paths2(g2.W6, random.Random(3), 1, 200_000)
        b = g2.paths2(g2.W6, random.Random(3), 1, 200_000)
        self.assertEqual(a, b)
        r = [a[0][i] / a[0][i - 1] - 1 for i in range(1, len(a[0]))]
        m = sum(r) / len(r)
        v = sum((x - m) ** 2 for x in r) / (len(r) - 1)
        k4 = sum((x - m) ** 4 for x in r) / len(r) / v ** 2
        self.assertLess(abs(m), 4 * math.sqrt(v / len(r)))
        self.assertAlmostEqual(math.sqrt(v), 0.03, delta=0.002)           # varians total tetap 0,03^2
        self.assertGreater(k4, 6.0)                                        # ekor tebal (teori ~10,6)
        with self.assertRaises(ValueError):
            g2.paths2(g2.W6, random.Random(1), 1, 10, mu=0.001)           # tanpa keunggulan di dunia ini

    def test_older_worlds_are_delegated_unchanged(self):
        self.assertEqual(g2.paths2("W2-garch", random.Random(5), 2, 300), rp.paths("W2-garch", random.Random(5), 2, 300))


class RecorderFidelityTests(unittest.TestCase):
    def test_the_recorder_gives_the_same_verdicts_texts_and_raw_numbers_as_the_real_gates(self):
        for tpl, k, param, world, seed in (("B1-TREND", 1, 30, "W1-iid", 7), ("B6-BOUNCE", 4, 20, "W4-faktor", 8)):
            md = g2.market2(world, random.Random(seed), k, 1400)
            spec = rp.spec_for(tpl, param, k)
            real = gates.run_gates(spec, md, None, fast())
            mine, raw = g2.run_gates_raw(spec, md, fast())
            self.assertEqual([(r.gate, r.status, r.value) for r in real], [(r.gate, r.status, r.value) for r in mine], tpl)
            g8 = next(r for r in mine if r.gate == "G8")
            k2 = next(r for r in mine if r.gate == "K2")
            self.assertIn(f"batas atas 95% {raw['g8_upper']:.3f}", g8.value)
            self.assertIn(f"placebo p = {raw['g8_pv']:.3f}", g8.value)
            self.assertIn(f"Calmar {raw['k2_calmar']:.2f}", k2.value)
            rec = g2.evaluate2(spec, md, fast())
            self.assertEqual(g2.lolos(rec, 1.0, 0.5), rec["vonis"] == "LOLOS_SHADOW")      # ambang terkunci pada statistik mentah = vonis resmi


class OfflineThresholdTests(unittest.TestCase):
    ALL = {g: "PASS" for g in gates.REQUIRED}

    def rec(self, upper, calmar, **st):
        return {"st": dict(self.ALL, **st), "g8_upper": upper, "k2_calmar": calmar}

    def test_g8_and_k2_are_re_judged_and_other_gates_are_kept(self):
        self.assertTrue(g2.lolos(self.rec(0.06, 0.6, G8="FAIL", K2="PASS"), 1.25, 0.5))      # 0,06 <= 1,25 x 0,05
        self.assertFalse(g2.lolos(self.rec(0.06, 0.6), 1.0, 0.5))
        self.assertTrue(g2.lolos(self.rec(0.04, 0.35, K2="FAIL"), 1.0, 0.3))
        self.assertFalse(g2.lolos(self.rec(0.04, 0.35), 1.0, 0.5))
        self.assertFalse(g2.lolos(self.rec(0.01, 9.0, G3="FAIL"), 2.0, 0.3))                  # gerbang lain tidak pernah dilonggarkan
        self.assertFalse(g2.lolos(self.rec(None, 1.0), 2.0, 0.3))                             # statistik tak terdefinisi = tidak lolos
        self.assertFalse(g2.lolos({"st": {"G*": "FAIL"}, "g8_upper": None, "k2_calmar": None}, 2.0, 0.0))


def _baris_fp(world, pola):
    """600 pasar; pasar i lolos gerbang lain hanya bila i % 40 == 0 (15 pasar); statistik G8 mereka mengikuti `pola` (15 nilai)."""
    rows = []
    for i in range(600):
        lain = i % 40 == 0
        st = dict({g: "PASS" for g in gates.REQUIRED}, **({} if lain else {"G3": "FAIL"}))
        u = pola[(i // 40) % len(pola)] if lain else 0.5
        rec = {"id": f"{world}|{i}", "dunia": world, "st": st, "g8_upper": u, "k2_calmar": 1.0}
        rec["vonis"] = "LOLOS_SHADOW" if g2.lolos(rec, 1.0, 0.5) else "TOLAK"
        rows.append(rec)
    return rows


def _baris_daya(pola):
    rows = []
    for (w, u, s, T) in g2.daya_sel():
        for j in range(20):
            rec = {"id": f"{w}|{u}|{s}|{T}|{j}", "dunia": w, "k": u, "s": s, "hari": T, "st": {g: "PASS" for g in gates.REQUIRED}, "g8_upper": pola[j % len(pola)], "k2_calmar": 1.0}
            rec["vonis"] = "LOLOS_SHADOW" if g2.lolos(rec, 1.0, 0.5) else "TOLAK"
            rows.append(rec)
    return rows


POLA = [0.01] * 3 + [0.055] * 3 + [0.07] * 3 + [0.085] * 3 + [0.095] * 3          # 15 nilai: lolos 3/6/9/12/15 pada c = 1 / 1,25 / 1,5 / 1,75 / 2


class SelectionTests(unittest.TestCase):
    def test_the_most_permissive_feasible_candidate_wins_and_ties_go_to_the_stricter_one(self):
        fp = [r for w in g2.WORLDS_SETEL for r in _baris_fp(w, POLA)]
        pw = _baris_daya([0.01, 0.055, 0.07, 0.085, 0.095])
        out = g2.pilih(fp, pw)
        layak = {(t["kandidat"]["c"]) for t in out["tabel"] if t["layak"]}
        self.assertEqual(layak, {1.0, 1.25, 1.5, 1.75})                    # c = 2,0: 2,5 % lolos, Wilson atas 4,08 % > 4 %
        self.assertEqual((out["dipilih"]["c"], out["dipilih"]["min_calmar"]), (1.75, 0.5))   # daya naik tiap c; K2 tak membedakan -> yang ketat (0,5)
        self.assertEqual(out["konsisten_beda"], 0)
        self.assertGreater(out["gain"], g2.GAIN_MIN)

    def test_without_a_material_gain_the_locked_thresholds_stay(self):
        fp = [r for w in g2.WORLDS_SETEL for r in _baris_fp(w, POLA)]
        pw = _baris_daya([0.01])                                            # semua pasar daya lolos pada ambang apa pun: tidak ada kenaikan
        out = g2.pilih(fp, pw)
        self.assertEqual(out["dipilih"], g2.terkunci())
        self.assertIn("TETAP", out["alasan"])

    def test_a_single_leaky_world_disqualifies_the_permissive_candidates(self):
        bocor = [0.01] * 3 + [0.055] * 12                                  # c = 1: 3 lolos (0,5 %); c >= 1,25: 15 lolos (2,5 %) = Wilson atas 4,08 %
        fp = [r for w in g2.WORLDS_SETEL[:-1] for r in _baris_fp(w, POLA)] + _baris_fp(g2.WORLDS_SETEL[-1], bocor)
        pw = _baris_daya([0.01, 0.055, 0.07, 0.085, 0.095])
        out = g2.pilih(fp, pw)
        self.assertEqual({t["kandidat"]["c"] for t in out["tabel"] if t["layak"]}, {1.0})
        self.assertEqual(out["dipilih"], g2.terkunci())

    def test_when_not_even_the_locked_thresholds_are_feasible_the_locked_ones_stay(self):
        fp = [r for w in g2.WORLDS_SETEL[:-1] for r in _baris_fp(w, POLA)] + _baris_fp(g2.WORLDS_SETEL[-1], [0.01] * 15)
        out = g2.pilih(fp, _baris_daya([0.01, 0.055]))
        self.assertEqual([t for t in out["tabel"] if t["layak"]], [])
        self.assertEqual(out["dipilih"], g2.terkunci())
        self.assertIn("tidak ada kandidat layak", out["alasan"])


class GuardTests(unittest.TestCase):
    def test_confirmation_refuses_to_run_without_a_selection(self):
        old = g2.OUT
        g2.OUT = tempfile.mkdtemp()
        try:
            with self.assertRaises(SystemExit) as cm:
                g2.run_set("konfirmasi-fp", 1)
            self.assertIn("g2-pilihan.json belum ada", str(cm.exception))
        finally:
            g2.OUT = old


if __name__ == "__main__":
    unittest.main()

"""P74: evaluasi lapisan pemilih - pembanding IDENTITAS / EW / TRAILING / ACAK / NONE kausal, ongkos ganti, uji berpasangan + BH, Brier, vonis,
pra-registrasi (status MENYIMPANG bila kode bergeser), dan perakitan data maju (pilihan dikomit + aturan hidup `engine/pemilih.py`)."""
import contextlib
import copy
import io
import json
import os
import random
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, ROOT)

from engine import pemilih_eval as pe                               # noqa: E402
from engine.series import DAY_MS                                    # noqa: E402

T0 = 1_700_006_400_000
ID = "B1-TREND"
BIAYA = {"B1-TREND": 0.0007, "B2-RS": 0.0007, "B6-BOUNCE": 0.0007}


def cepat(**ubah):
    """Params uji: aturan sama, tarikan lebih sedikit supaya tes cepat (sha beda = bukan pra-registrasi, sengaja)."""
    P = copy.deepcopy(pe.PARAMS_P74)
    P["angka"].update({"n_acak": 200, "boot_n": 1000, **ubah})
    return P


def net_acak(n=200, seed=1, drift=None):
    rng = random.Random(seed)
    drift = drift or {}
    return {b: {T0 + i * DAY_MS: rng.gauss(drift.get(b, 0.0), 0.01) for i in range(n)} for b in BIAYA}


class KebijakanTests(unittest.TestCase):
    def test_trailing_never_reads_the_future(self):
        net = net_acak(160)
        cal = pe.kalender(net, sorted(net))
        a = pe.kebijakan_trailing(net, cal, sorted(net), ID, 20, 3)
        for k in (40, 90, 150):
            ganggu = copy.deepcopy(net)
            for b in ganggu:
                for T in cal[k:]:
                    ganggu[b][T] = random.Random(f"{b}:{T}").uniform(-1, 1)  # masa depan (bar ke-k dan sesudahnya) diacak total, beda per bot
            b2 = pe.kebijakan_trailing(ganggu, cal, sorted(net), ID, 20, 3)
            self.assertEqual([a[T] for T in cal[:k + 1]], [b2[T] for T in cal[:k + 1]])   # pilihan s/d bar k tidak berubah

    def test_trailing_warms_up_on_identity_picks_the_best_window_and_respects_the_gap(self):
        cal = [T0 + i * DAY_MS for i in range(40)]
        net = {"B1-TREND": {T: 0.0 for T in cal}, "B2-RS": {T: 0.0 for T in cal}, "B6-BOUNCE": {T: 0.0 for T in cal}}
        for i, T in enumerate(cal):
            net["B2-RS"][T] = 0.01 if i < 20 else -0.01
            net["B6-BOUNCE"][T] = -0.01 if i < 20 else 0.01
        p = pe.kebijakan_trailing(net, cal, sorted(net), ID, 10, 7)
        self.assertEqual({p[T] for T in cal[:10]}, {ID})                     # riwayat < jendela -> identitas
        self.assertEqual(p[cal[10]], "B2-RS")                                # jendela 0..9 terbaik B2
        switches = [i for i in range(1, 40) if p[cal[i]] != p[cal[i - 1]]]
        self.assertTrue(all(b - a >= 7 for a, b in zip(switches, switches[1:])), switches)
        self.assertEqual(p[cal[-1]], "B6-BOUNCE")

    def test_ties_go_to_identity_then_alphabetical(self):
        self.assertEqual(pe._pilih_seri({"B2-RS": 1.0, ID: 1.0, "B6-BOUNCE": 0.0}, ID), ID)
        self.assertEqual(pe._pilih_seri({"B6-BOUNCE": 1.0, "B2-RS": 1.0, ID: 0.0}, ID), "B2-RS")

    def test_random_policy_is_reproducible_and_changes_only_on_its_grid(self):
        cal = [T0 + i * DAY_MS for i in range(50)]
        a = pe.kebijakan_acak(cal, sorted(BIAYA), 5, random.Random(7))
        self.assertEqual(a, pe.kebijakan_acak(cal, list(reversed(sorted(BIAYA))), 5, random.Random(7)))   # urutan masukan tidak berpengaruh
        self.assertTrue(all(a[cal[i]] == a[cal[i - 1]] for i in range(1, 50) if i % 5))


class OngkosTests(unittest.TestCase):
    def test_a_switch_costs_exit_plus_entry_and_holding_costs_nothing_extra(self):
        cal = [T0 + i * DAY_MS for i in range(4)]
        net = {"A": {T: 0.001 for T in cal}, "B": {T: 0.002 for T in cal}}
        gross = {"A": {T: 1.0 for T in cal}, "B": {T: 0.5 for T in cal}}
        r = pe.jalankan({cal[0]: "A", cal[1]: "A", cal[2]: "B", cal[3]: "B"}, net, cal, gross, {"A": 0.0007, "B": 0.0010})
        self.assertEqual(r["ganti"], 1)
        self.assertAlmostEqual(r["ongkos"], 1.0 * 0.0007 + 0.5 * 0.0010)
        self.assertAlmostEqual(r["seri"][cal[2]], 0.002 - (0.0007 + 0.0005))
        self.assertEqual([r["seri"][T] for T in (cal[0], cal[1], cal[3])], [0.001, 0.001, 0.002])

    def test_none_is_free_and_an_unknown_fee_is_refused(self):
        cal = [T0 + i * DAY_MS for i in range(3)]
        net = {"A": {T: 0.01 for T in cal}}
        r = pe.jalankan({cal[0]: "A", cal[1]: pe.NONE, cal[2]: pe.NONE}, net, cal, None, {"A": 0.001})
        self.assertAlmostEqual(r["seri"][cal[1]], -1.0 * 0.001)                # keluar A (gross tanpa data = 1,0); NONE gratis
        self.assertEqual(r["seri"][cal[2]], 0.0)
        with self.assertRaisesRegex(ValueError, "tidak boleh dianggap nol"):
            pe.jalankan({cal[0]: "A", cal[1]: "B", cal[2]: "B"}, {"A": net["A"], "B": net["A"]}, cal, None, {"A": 0.001})

    def test_the_spec_ruler_gives_the_fee_per_side(self):
        from engine.spec import SPECS
        self.assertAlmostEqual(pe.biaya_dari_penggaris(SPECS["B1-TREND"].penggaris), 0.0007)
        self.assertAlmostEqual(pe.biaya_dari_penggaris(SPECS["B3-CARRY"].penggaris), 0.0014)      # per kaki x 2 kaki
        self.assertAlmostEqual(pe.biaya_dari_penggaris(SPECS["B5-CORE-RWA"].penggaris), 0.0010)
        with self.assertRaises(ValueError):
            pe.biaya_dari_penggaris({"funding": "x"})


class UjiTests(unittest.TestCase):
    def test_identical_series_are_never_significant(self):
        x = [random.Random(3).gauss(0, 0.01) for _ in range(100)]
        self.assertEqual(pe.uji_berpasangan(x, x, 5, 500, 1)["p"], 1.0)

    def test_a_clearly_better_series_is_significant_and_a_worse_one_is_not(self):
        rng = random.Random(4)
        b = [rng.gauss(0, 0.01) for _ in range(200)]
        a = [v + 0.003 for v in b]
        self.assertLess(pe.uji_berpasangan(a, b, 5, 2000, 1)["p"], 0.01)
        self.assertGreater(pe.uji_berpasangan(b, a, 5, 2000, 1)["p"], 0.5)

    def test_random_policy_p_value(self):
        self.assertAlmostEqual(pe.p_acak(5.0, [1.0, 2.0, 6.0, 7.0]), 3 / 5)
        self.assertIsNone(pe.p_acak(1.0, []))


class BrierTests(unittest.TestCase):
    def test_binary_brier_skill_and_calibration(self):
        sempurna = pe.brier_biner([(1.0, 1), (0.0, 0)] * 10)
        self.assertEqual((sempurna["brier"], sempurna["skill"]), (0.0, 1.0))
        koin = pe.brier_biner([(0.5, 1), (0.5, 0)] * 10)
        self.assertAlmostEqual(koin["skill"], 0.0)
        salah = pe.brier_biner([(0.9, 0)] * 10)
        self.assertLess(salah["skill"], 0)
        self.assertEqual(salah["kalibrasi"], [{"ember": "0.8-1.0", "n": 10, "rata_p": 0.9, "frekuensi": 0.0}])
        with self.assertRaises(ValueError):
            pe.brier_biner([(1.5, 1)])

    def test_confidence_events_exclude_identity_picks_and_ties(self):
        cal = [T0 + i * DAY_MS for i in range(4)]
        net = {ID: {T: 0.0 for T in cal}, "B2-RS": {cal[0]: 0.01, cal[1]: -0.01, cal[2]: 0.0, cal[3]: 0.02}}
        pil = {cal[0]: ("B2-RS", 70), cal[1]: ("B2-RS", 60), cal[2]: ("B2-RS", 90), cal[3]: (ID, 80)}
        self.assertEqual(pe.kejadian_keyakinan(pil, net, cal, ID), [(0.7, 1), (0.6, 0)])
        with self.assertRaises(ValueError):
            pe.kejadian_keyakinan({cal[0]: ("B2-RS", 140)}, net, cal, ID)

    def test_multiclass_brier_against_uniform(self):
        cal = [T0 + i * DAY_MS for i in range(3)]
        net = {"A": {T: 0.02 for T in cal}, "B": {T: 0.0 for T in cal}}
        self.assertAlmostEqual(pe.brier_multi({T: {"A": 0.5, "B": 0.5} for T in cal}, net, cal, ["A", "B"])["skill"], 0.0)
        self.assertEqual(pe.brier_multi({T: {"A": 1.0, "B": 0.0} for T in cal}, net, cal, ["A", "B"])["brier"], 0.0)
        with self.assertRaisesRegex(ValueError, "jumlah peluang"):
            pe.brier_multi({cal[0]: {"A": 0.7, "B": 0.7}}, net, cal, ["A", "B"])


class EvaluasiTests(unittest.TestCase):
    def test_short_forward_data_is_never_a_verdict(self):
        net = net_acak(30)
        lap = pe.evaluasi(net, sorted(net), {"S": {T: "B2-RS" for T in net[ID]}}, biaya=BIAYA, P=cepat())
        self.assertEqual(lap["subjek"]["S"]["vonis"], pe.BELUM)
        self.assertIn("hari terukur 30 < 60", lap["subjek"]["S"]["alasan"][0])

    def test_a_selector_that_only_copies_the_identity_bot_is_not_superior(self):
        net = net_acak(200)
        lap = pe.evaluasi(net, sorted(net), {"S": {}}, biaya=BIAYA, P=cepat())        # tanpa pilihan sama sekali = identitas
        s = lap["subjek"]["S"]
        self.assertEqual(s["tanpa_pilihan"], 200)
        self.assertEqual(s["uji"][pe.IDENTITAS]["p"], 1.0)
        self.assertEqual(s["vonis"], pe.TIDAK_UNGGUL)

    def test_a_selector_that_knows_the_best_bot_beats_every_baseline_after_costs(self):
        net = net_acak(200, seed=5)
        cal = pe.kalender(net, sorted(net))
        orakel = {T: max(net, key=lambda b: net[b][T]) for T in cal}                    # tahu masa depan: batas atas, hanya untuk menguji mesin
        lap = pe.evaluasi(net, sorted(net), {"ORAKEL": orakel}, biaya=BIAYA, P=cepat())
        s = lap["subjek"]["ORAKEL"]
        self.assertGreater(s["ganti"], 50)
        self.assertGreater(s["ongkos_pct"], 0)
        self.assertEqual(s["vonis"], pe.UNGGUL, s["alasan"])
        self.assertTrue(all(h["lolos_bh"] for h in lap["hipotesis"] if h["h"].startswith("ORAKEL vs ")))

    def test_backward_mode_never_gives_a_verdict(self):
        net = net_acak(200, seed=6)
        lap = pe.evaluasi(net, sorted(net), biaya=BIAYA, mode=pe.MUNDUR, P=cepat())
        self.assertEqual(list(lap["subjek"]), [pe.TRAILING])
        self.assertEqual(lap["subjek"][pe.TRAILING]["vonis"], pe.EKSPLORATIF)
        self.assertNotIn("TRAILING vs TRAILING", [h["h"] for h in lap["hipotesis"]])
        self.assertIn("EKSPLORATIF", pe.teks(lap))

    def test_missing_identity_or_empty_calendar_is_reported_not_raised(self):
        net = {"B2-RS": {T0: 0.01}}
        lap = pe.evaluasi(net, ["B2-RS"], {"S": {}}, biaya=BIAYA, P=cepat())
        self.assertIn("identitas", lap["galat"])
        self.assertEqual(lap["subjek"]["S"]["vonis"], pe.BELUM)
        lap = pe.evaluasi({ID: {T0: 0.0}, "B2-RS": {T0 + DAY_MS: 0.0}}, [ID, "B2-RS"], {"S": {}}, biaya=BIAYA, P=cepat())
        self.assertIn("kalender kosong", lap["galat"])

    def test_a_pick_outside_the_candidates_is_unmeasured_not_guessed(self):
        net = net_acak(100)
        cal = pe.kalender(net, sorted(net))
        pil = {T: ("B4-LISTING-FADE" if i % 10 == 0 else "B2-RS") for i, T in enumerate(cal)}
        s = pe.evaluasi(net, sorted(net), {"S": pil}, biaya=BIAYA, P=cepat())["subjek"]["S"]
        self.assertEqual((s["tak_terukur"], s["n"]), (10, 90))

    def test_the_report_prints_forecasts_before_pnl(self):
        net = net_acak(80)
        cal = pe.kalender(net, sorted(net))
        yakin = {"S": {T: ("B2-RS", 60) for T in cal}}
        txt = pe.teks(pe.evaluasi(net, sorted(net), {"S": {T: "B2-RS" for T in cal}}, biaya=BIAYA, keyakinan=yakin, P=cepat()))
        self.assertLess(txt.index("PRAKIRAAN (Brier"), txt.index("rata bps"))


class PraRegistrasiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="p74-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.u, self.k = os.path.join(self.tmp, "u.json"), os.path.join(self.tmp, "k.json")

    def test_proposal_then_drift_then_lock_only_on_the_same_sha(self):
        st = lambda P=None: pe.status(P, self.k, self.u)["state"]                       # noqa: E731
        self.assertEqual(st(), "BELUM_DIUSULKAN")
        pe.tulis_usulan("pra-registrasi uji", "2026-10-07T00:00:00Z", path=self.u, lock_path=self.k)
        self.assertEqual(st(), "USULAN")
        geser = cepat()
        self.assertEqual(st(geser), "MENYIMPANG")                                       # satu angka berubah = terlihat
        with self.assertRaisesRegex(ValueError, "sha-nya beda"):
            pe.tulis_kunci("disetujui", P=geser, path=self.k, usulan_path=self.u)
        with self.assertRaisesRegex(ValueError, "catatan wajib"):
            pe.tulis_kunci("  ", path=self.k, usulan_path=self.u)
        pe.tulis_kunci("disetujui uji", "2026-10-08T00:00:00Z", path=self.k, usulan_path=self.u)
        self.assertEqual(st(), "TERKUNCI")
        with self.assertRaises(FileExistsError):
            pe.tulis_kunci("lagi", path=self.k, usulan_path=self.u)
        with self.assertRaises(FileExistsError):
            pe.tulis_usulan("usulan baru", path=self.u, lock_path=self.k)
        with open(self.k, encoding="utf-8") as f:
            d = json.load(f)
        d["params"]["angka"]["hari_min"] = 1
        with open(self.k, "w", encoding="utf-8") as f:
            json.dump(d, f)
        self.assertEqual(st(), "RUSAK")                                                 # isi diubah tanpa sha baru

    def test_the_repo_preregistration_matches_the_code(self):
        st = pe.status()
        self.assertIn(st["state"], ("USULAN", "TERKUNCI"), st)                          # kode bergeser dari berkas = tes ini gagal


class MajuTests(unittest.TestCase):
    """Perakitan data maju di `tools/pemilih_eval.py`: pilihan dikomit + aturan hidup `engine/pemilih.py` hanya dengan skor sebelum penutupan."""

    def setUp(self):
        import pemilih_eval as tool
        self.tool = tool
        self.tmp = tempfile.mkdtemp(prefix="p74-analis-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def tulis(self, close, rows):
        with open(os.path.join(self.tmp, f"{close}.jsonl"), "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    def rec(self, agent, aid, close, bot, k, status="dikomit"):
        return {"agent": agent, "bot": bot, "keyakinan": k, "status": status, "alasan": {"agent_id": aid, "bar_close": close}}

    def test_committed_picks_win_and_one_per_agent_and_close(self):
        C = T0 // 1000
        self.tulis(C, [self.rec("glm", 2558, C, "B2-RS", 60, "gagal"), self.rec("glm", 2558, C, "B6-BOUNCE", 70), self.rec("qwen", 2559, C, ID, 55)])
        picks = self.tool.baca_pilihan(self.tmp)
        self.assertEqual([(p["agent"], p["bot"], p["keyakinan"]) for p in picks], [("glm", "B6-BOUNCE", 70), ("qwen", ID, 55)])

    def test_the_live_rule_uses_only_scores_from_before_each_close(self):
        closes = [T0 // 1000 + i * 86_400 for i in range(30)]
        picks = []
        for C in closes:
            picks += [{"agent": "glm", "agent_id": 2558, "bar_close": C, "bot": "B2-RS", "keyakinan": 60, "status": "dikomit"},
                      {"agent": "qwen", "agent_id": 2559, "bar_close": C, "bot": ID, "keyakinan": 50, "status": "dikomit"}]
        net = {ID: {C * 1000: 0.0 for C in closes}, "B2-RS": {C * 1000: 0.01 for C in closes}, "B6-BOUNCE": {C * 1000: -0.01 for C in closes}}
        a = self.tool.pemilih_dari_pilihan(picks, net, ID)
        self.assertEqual(set(a["pemilih"]), {"PEMILIH", "agent:glm", "agent:qwen"})
        P = a["pemilih"]["PEMILIH"]
        self.assertEqual({P[C * 1000] for C in closes[:20]}, {ID})                      # < 20 pilihan terskor: seri 1-1 -> identitas (aturan 3)
        self.assertEqual({P[C * 1000] for C in closes[20:]}, {"B2-RS"})                 # glm pemimpin (selisih +100 bps per pilihan)
        self.assertEqual(a["keyakinan"]["agent:glm"][closes[1] * 1000], ("B2-RS", 60.0))
        ganggu = copy.deepcopy(net)
        ganggu["B2-RS"][closes[25] * 1000] = -5.0                                       # hasil bar penutupan ke-25 sendiri
        Q = self.tool.pemilih_dari_pilihan(picks, ganggu, ID)["pemilih"]["PEMILIH"]
        self.assertEqual([P[C * 1000] for C in closes[:26]], [Q[C * 1000] for C in closes[:26]])   # skor bar C tidak pernah dipakai untuk C
        self.assertEqual(Q[closes[26] * 1000], ID)                                      # sesudahnya skor itu dipakai: pemimpin berganti ke qwen

    def test_the_repo_forward_ledgers_load_with_chains_intact(self):
        d = self.tool.data_maju(provisional=False)
        self.assertEqual({k: v for k, v in d["rusak"].items() if "(provisional)" not in k}, {})
        self.assertTrue(all(isinstance(T, int) and isinstance(x, float) for xs in d["final"].values() for T, x in xs.items()))

    def test_a_broken_forward_ledger_is_excluded_and_reported(self):
        led = os.path.join(self.tmp, "paper")
        os.makedirs(led)
        with open(os.path.join(ROOT, "ledger", "paper", "B3-CARRY.jsonl"), encoding="utf-8") as f:
            recs = [json.loads(x) for x in f if x.strip()]
        settle = next(i for i, r in enumerate(recs) if r.get("type") == "settle")
        recs[settle]["net"] = 0.5                                                      # isi diubah tanpa menyegel ulang = rantai putus
        with open(os.path.join(led, "B3-CARRY.jsonl"), "w", encoding="utf-8", newline="\n") as f:
            f.write("".join(json.dumps(r) + "\n" for r in recs))
        d = self.tool.data_maju(led, provisional=False)
        self.assertIn("B3-CARRY", d["rusak"])
        self.assertNotIn("B3-CARRY", d["final"])                                       # angka dari ledger rusak tidak pernah dipakai

    def test_forward_provisional_numbers_never_carry_a_verdict(self):
        out = os.path.join(self.tmp, "maju.json")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.tool.main(["maju", "--json", out]), 0)
        with open(out, encoding="utf-8") as f:
            lap = json.load(f)
        self.assertTrue(lap["provisional"]["subjek"])
        self.assertEqual({s["vonis"] for s in lap["provisional"]["subjek"].values()}, {"PROVISIONAL (bukan vonis)"})
        self.assertNotIn(pe.UNGGUL, {s["vonis"] for s in lap["final"]["subjek"].values()})


if __name__ == "__main__":
    unittest.main()

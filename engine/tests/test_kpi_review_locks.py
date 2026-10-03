import dataclasses
import json
import os
import random
import tempfile
import unittest
from unittest import mock

from engine import chain, economics, kpi, locks, review as reviewmod, submission
from engine.gates import GateParams
from engine.series import DAY_MS
from engine.slots import SlotParams
from engine.spec import SPECS
from engine.target import Target

from .helpers import BNB, ETH, T0, md_perp, regime_closes
from .test_submission import EXAMPLE, Account, encode_typed_data, example, with_

FAST = GateParams.fast()


def series(daily, start=T0):
    return [(start + i * DAY_MS, v) for i, v in enumerate(daily)]


def noisy(n, mean, sd, seed=1):
    r = random.Random(seed)
    return [r.gauss(mean, sd) for _ in range(n)]


def targets_flip(n, every=20, asset="BTCUSDT"):
    """Target yang berganti long/flat tiap `every` hari: sinyal MASUK/KELUAR teratur."""
    out = []
    for i in range(n):
        out.append(Target("B1-TREND", T0 + i * DAY_MS, {asset: 1.0} if (i // every) % 2 == 0 else {}, {}))
    return out


class EconomicsTests(unittest.TestCase):
    def test_sixty_forty_split_is_exact_and_lossless(self):
        self.assertEqual((economics.ISSUER_SHARE_BPS, economics.FABIUS_SHARE_BPS), (6000, 4000))
        self.assertEqual(economics.split(10_000), (6_000, 4_000))
        self.assertEqual(economics.split(1), (0, 1))                               # debu pembulatan ke Fabius
        self.assertEqual(economics.split(0), (0, 0))
        self.assertEqual(economics.split(999_990_001), (599_994_000, 399_996_001))
        rng = random.Random(7)
        for _ in range(2000):
            a = rng.randrange(0, 10 ** 30)
            i, f = economics.split(a)
            self.assertEqual(i + f, a)
            self.assertEqual(i, a * 6000 // 10_000)
            self.assertGreaterEqual(f, 0)

    def test_split_rejects_bad_input(self):
        for bad in (-1, 1.5, True, "10", None):
            with self.assertRaises(ValueError):
                economics.split(bad)
        for bad in (-1, 10_001, True, 0.5):
            with self.assertRaises(ValueError):
                economics.split(100, bad)

    def test_fabius_share_may_only_go_down(self):
        self.assertTrue(economics.share_change_allowed(4000, 4000))
        self.assertTrue(economics.share_change_allowed(4000, 3000))
        self.assertTrue(economics.share_change_allowed(4000, 0))
        self.assertFalse(economics.share_change_allowed(4000, 4001))
        self.assertFalse(economics.share_change_allowed(4000, -1))
        self.assertFalse(economics.share_change_allowed(10_001, 10_001))

    def test_break_even_calculator(self):
        self.assertAlmostEqual(economics.break_even_subscribers(20.0, 10.0), 5.0)      # 40% x $10 = $4 per pelanggan -> 5 pelanggan menutup $20
        with self.assertRaises(ValueError):
            economics.break_even_subscribers(20.0, 0.0)


class KpiTests(unittest.TestCase):
    def ev(self, daily, claims=None, params=None, tg=None, n=None):
        n = n or len(daily)
        return {r.gate: r for r in kpi.evaluate(SPECS["B1-TREND"], series(daily), tg if tg is not None else targets_flip(n), params, claims)}

    def test_k1_annual_net_must_beat_the_risk_free_hurdle_plus_margin(self):
        good = self.ev(noisy(720, 0.0005, 0.004))                        # ~ +18 %/th
        self.assertEqual(good["K1"].status, kpi.PASS, good["K1"].value)
        weak = self.ev(noisy(720, 0.00005, 0.004))                       # ~ +1,8 %/th < 6 %
        self.assertEqual(weak["K1"].status, kpi.FAIL, weak["K1"].value)
        strict = self.ev(noisy(720, 0.0005, 0.004), params=kpi.KpiParams(hurdle_ann=0.30))
        self.assertEqual(strict["K1"].status, kpi.FAIL)

    def test_k2_calmar_is_scale_free(self):
        a = noisy(720, 0.0006, 0.01, seed=3)
        small = [x * 0.1 for x in a]                                     # posisi 10x lebih kecil: Calmar sama, MDD absolut jauh lebih kecil
        ra, rs = self.ev(a)["K2"], self.ev(small)["K2"]
        self.assertEqual(ra.status, rs.status)
        calmar = lambda r: float(r.value.split()[1])
        self.assertAlmostEqual(calmar(ra), calmar(rs), delta=0.15)
        crash = self.ev([0.002] * 300 + [-0.02] * 40 + [0.001] * 380)
        self.assertEqual(crash["K2"].status, kpi.FAIL, crash["K2"].value)

    def test_k3_activity_needs_signals_per_year_and_in_total(self):
        d = noisy(720, 0.0005, 0.004)
        busy = self.ev(d, tg=targets_flip(720, every=20))
        self.assertEqual(busy["K3"].status, kpi.PASS, busy["K3"].value)
        idle = self.ev(d, tg=targets_flip(720, every=2000))              # satu sinyal masuk saja
        self.assertEqual(idle["K3"].status, kpi.FAIL, idle["K3"].value)
        few_total = self.ev(noisy(100, 0.0005, 0.004), tg=targets_flip(100, every=10))
        self.assertEqual(few_total["K3"].status, kpi.FAIL)                # >= 12/th tercapai tetapi < 20 total? (100 hari: ~10 sinyal)

    def test_k4_claims_cannot_exceed_measured(self):
        d = [0.002] * 300 + [-0.02] * 40 + [0.001] * 380                  # MDD terukur dalam (~ -55 %): klaim -1 % jelas terlalu rosy
        r = self.ev(d)["K4"]
        self.assertEqual(r.status, kpi.TB)                                # tanpa klaim: tidak berlaku
        measured = float(self.ev(d)["K2"].value.split("MDD ")[1].rstrip("%)"))
        self.assertLess(measured, -40.0)
        honest = self.ev(d, claims={"sharpe_net": 0.5, "mdd_pct": measured})["K4"]
        self.assertEqual(honest.status, kpi.PASS, honest.value)
        inflated = self.ev(d, claims={"sharpe_net": 60.0, "mdd_pct": measured})["K4"]
        self.assertEqual(inflated.status, kpi.FAIL)
        self.assertIn("Sharpe klaim", inflated.value)
        rosy = self.ev(d, claims={"sharpe_net": 0.5, "mdd_pct": -1.0})["K4"]
        self.assertEqual(rosy.status, kpi.FAIL)
        self.assertIn("MDD klaim", rosy.value)

    def test_k5_profit_share_scenario_can_hurt_fabius_even_when_the_bot_earns(self):
        # bulan KALENDER bergantian untung +10 % dan rugi -5 %: bot untung rata-rata +2,5 %/bulan; kalau penerbit ambil 60 % dari bulan untung
        # tanpa menanggung rugi, Fabius: 0,4 x 10 - 5 = -1 % per dua bulan
        import datetime as dt
        days = []
        for i in range(720):
            d = dt.datetime.fromtimestamp((T0 + i * DAY_MS) / 1000, dt.timezone.utc)
            n_days = (dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1) - dt.date(d.year, d.month, 1)).days
            days.append((0.10 if (d.year * 12 + d.month) % 2 == 0 else -0.05) / n_days)
        pnl = series(days)
        self.assertLess(kpi.fabius_net_profit_share_ann(pnl, 6000), 0)
        self.assertGreater(sum(days) / len(days) * 365, 0)
        info = {r.gate: r for r in kpi.evaluate(SPECS["B1-TREND"], pnl, targets_flip(720), None, None)}["K5"]
        self.assertEqual(info.status, kpi.TB)                              # basis = pendapatan: informatif, tidak menggagalkan
        self.assertIn("-", info.value.split("memberi Fabius")[1].split("%")[0])
        gate = {r.gate: r for r in kpi.evaluate(SPECS["B1-TREND"], pnl, targets_flip(720), kpi.KpiParams(fee_base="profit"), None)}["K5"]
        self.assertEqual(gate.status, kpi.FAIL, gate.value)
        steady = series([0.0005] * 720)
        self.assertGreater(kpi.fabius_net_profit_share_ann(steady, 6000), 0)
        ok = {r.gate: r for r in kpi.evaluate(SPECS["B1-TREND"], steady, targets_flip(720), kpi.KpiParams(fee_base="profit"), None)}["K5"]
        self.assertEqual(ok.status, kpi.PASS)

    def test_too_little_data_fails_closed(self):
        r = kpi.evaluate(SPECS["B1-TREND"], series([0.001] * 10), targets_flip(10), None, None)
        self.assertEqual([x.status for x in r], [kpi.FAIL])


class LockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "locks", "review.lock.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_fingerprint_is_stable_and_sensitive_to_every_family_of_numbers(self):
        base = locks.fingerprint()
        self.assertEqual(base, locks.fingerprint())
        self.assertRegex(base, r"^0x[0-9a-f]{64}$")
        changes = [locks.current_params(gate=dataclasses.replace(GateParams(), min_net_sharpe=0.6)),
                   locks.current_params(gate=dataclasses.replace(GateParams(), seed=1)),
                   locks.current_params(gate=dataclasses.replace(GateParams(), plateau_factors=(0.5, 1.5))),
                   locks.current_params(kpi=kpi.KpiParams(min_calmar=0.6)),
                   locks.current_params(kpi=kpi.KpiParams(fee_base="profit")),
                   locks.current_params(slot=SlotParams(margin_bps=101.0)),
                   locks.current_params(slot=SlotParams(min_gap_tstat=1.0))]
        shas = {locks.fingerprint(p) for p in changes}
        self.assertEqual(len(shas), len(changes))
        self.assertNotIn(base, shas)

    def test_lifecycle_unlocked_locked_drifted_corrupt(self):
        st = locks.status(path=self.path)
        self.assertEqual((st["state"], st["sha_kunci"]), ("BELUM_DIKUNCI", None))
        lock = locks.write_lock("disetujui builder 2026-10-02", now_iso="2026-10-02T12:00:00Z", path=self.path)
        self.assertEqual(lock["sha"], locks.fingerprint())
        self.assertEqual(locks.status(path=self.path)["state"], "TERKUNCI")
        drift = locks.status(gate=dataclasses.replace(GateParams(), min_net_sharpe=0.4), path=self.path)
        self.assertEqual(drift["state"], "MENYIMPANG")                       # ada yang menggeser angka sesudah kunci
        self.assertNotEqual(drift["sha_kini"], drift["sha_kunci"])
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        data["params"]["gerbang"]["min_net_sharpe"] = 0.1                     # berkas kunci disunting tangan tanpa menghitung ulang sha
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        self.assertEqual(locks.status(path=self.path)["state"], "RUSAK")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("{bukan json")
        self.assertEqual(locks.status(path=self.path)["state"], "RUSAK")

    def test_write_lock_refuses_overwrite_requires_note_and_keeps_history(self):
        with self.assertRaises(ValueError):
            locks.write_lock("   ", path=self.path)
        locks.write_lock("v1", now_iso="2026-10-02T12:00:00Z", path=self.path)
        with self.assertRaises(FileExistsError):
            locks.write_lock("v2", path=self.path)
        new = locks.write_lock("v2 dengan margin lain", now_iso="2026-11-01T12:00:00Z", supersede=True, path=self.path,
                               slot=SlotParams(margin_bps=150.0))
        hist = os.path.join(os.path.dirname(self.path), "history")
        self.assertEqual(len(os.listdir(hist)), 1)                           # kunci lama tetap terlihat, tidak dihapus
        with open(os.path.join(hist, os.listdir(hist)[0]), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["catatan"], "v1")
        self.assertEqual(locks.status(slot=SlotParams(margin_bps=150.0), path=self.path)["sha_kunci"], new["sha"])


    def test_repo_lock_file_if_present_matches_the_code_defaults(self):
        """Tanpa ini kunci hanya hiasan: bila ada yang mengubah satu angka bawaan tanpa menulis kunci baru (`lock --write --supersede`), tes ini gagal."""
        if not os.path.exists(locks.LOCK_FILE):
            self.skipTest("belum ada berkas kunci di repo")
        st = locks.status()
        self.assertEqual(st["state"], "TERKUNCI", f"angka bawaan menyimpang dari kunci: {st}")
        with open(locks.LOCK_FILE, encoding="utf-8") as f:
            lock = json.load(f)
        self.assertTrue(lock["catatan"].strip())
        self.assertEqual(lock["params"]["ekonomi"], {"issuer_bps": 6000, "fabius_bps": 4000})


class BookTests(unittest.TestCase):
    def test_genesis_book_is_valid_and_has_exactly_the_crypto_identity_bot(self):
        from engine import book as bookmod, slots
        b = bookmod.genesis_book(1_800_000_000)
        self.assertEqual(slots.book_problems(b), [])
        self.assertEqual([(e.bot_id, e.issuer, e.identity) for e in b], [("B1-TREND", slots.FABIUS, True)])
        self.assertEqual(b[0].spec_sha, SPECS["B1-TREND"].sha())
        self.assertEqual(b[0].fingerprint, SPECS["B1-TREND"].fingerprint())
        self.assertEqual(slots.book_sha(b), slots.book_sha(bookmod.genesis_book(1_900_000_000)))          # waktu masuk tidak ikut sidik jari buku
        self.assertEqual(list(bookmod.fabius_specs(b)), ["B1-TREND"])

    def test_identity_bot_must_trade_crypto_instruments_only(self):
        from engine import book as bookmod
        self.assertTrue(bookmod.trades_crypto_only(SPECS["B1-TREND"]))
        self.assertTrue(bookmod.trades_crypto_only(SPECS["B3-CARRY"]))
        self.assertFalse(bookmod.trades_crypto_only(SPECS["B5-CORE-RWA"]))                                 # campuran BTC + emas
        rwa = dataclasses.replace(SPECS["B1-TREND"], universe=("BTCUSDT", "XAUUSDT"))
        self.assertFalse(bookmod.trades_crypto_only(rwa))
        self.assertFalse(bookmod.trades_crypto_only(dataclasses.replace(SPECS["B1-TREND"], universe=())))
        with mock.patch.object(bookmod, "IDENTITY_BOT_ID", "B5-CORE-RWA"):
            with self.assertRaises(ValueError):
                bookmod.genesis_book(1)

    def test_genesis_book_requires_a_time_and_other_fabius_bots_get_no_free_slot(self):
        from engine import book as bookmod
        with self.assertRaises(TypeError):
            bookmod.genesis_book()
        self.assertNotIn("B2-RS", [e.bot_id for e in bookmod.genesis_book(1)])


class ReviewTests(unittest.TestCase):
    def data(self, n=1500):
        return md_perp({ETH: regime_closes(n, 21), BNB: regime_closes(n, 22)})

    def sub(self, **over):
        s = example()
        for path, val in over.items():
            s = with_(s, path.replace("__", "."), val)
        return s

    def run_review(self, sub=None, **kw):
        kw.setdefault("gate_params", FAST)
        return reviewmod.review(sub or self.sub(), self.data(), kw.pop("incumbents", None), **kw)

    def test_report_is_deterministic_sealed_and_data_bound(self):
        a, b = self.run_review(), self.run_review()
        self.assertEqual(a, b)
        self.assertRegex(a["report_sha"], r"^0x[0-9a-f]{64}$")
        body = {k: v for k, v in a.items() if k != "report_sha"}
        from engine.spec import sha0x
        self.assertEqual(a["report_sha"], sha0x(body))
        other = reviewmod.review(self.sub(), md_perp({ETH: regime_closes(1500, 31), BNB: regime_closes(1500, 32)}), None, gate_params=FAST)
        self.assertNotEqual(a["data_hash"], other["data_hash"])
        self.assertNotEqual(a["report_sha"], other["report_sha"])
        for k in ("spec_sha", "fingerprint", "submission_sha", "data_hash", "vonis", "gerbang", "kunci", "identitas", "n_trials"):
            self.assertIn(k, a)

    def test_report_has_all_required_gates_and_kpis_and_is_not_binding_without_lock_and_identity(self):
        unlocked = {"state": "BELUM_DIKUNCI", "sha_kini": "0x1", "sha_kunci": None, "berkas": "x"}      # tidak bergantung pada berkas kunci repo
        with mock.patch.object(reviewmod.locks, "status", return_value=unlocked):
            rep = self.run_review()
        got = {g["gate"] for g in rep["gerbang"]}
        from engine import gates
        self.assertTrue(set(gates.REQUIRED) <= got, set(gates.REQUIRED) - got)
        self.assertFalse(rep["mengikat"])                                    # tanpa tanda tangan dan tanpa kunci: indikatif
        self.assertEqual(rep["kunci"]["state"], "BELUM_DIKUNCI")
        self.assertFalse(rep["identitas"]["diverifikasi"])

    def test_non_default_parameters_never_bind_even_when_a_lock_exists(self):
        # FAST != parameter yang dikunci: laporan mencatat MENYIMPANG/BELUM_DIKUNCI dan tidak pernah mengikat tanpa identitas
        rep = self.run_review()
        self.assertIn(rep["kunci"]["state"], ("BELUM_DIKUNCI", "MENYIMPANG"))
        self.assertFalse(rep["mengikat"])

    def test_binding_requires_lock_identity_and_a_passing_verdict(self):
        locked = {"state": "TERKUNCI", "sha_kini": "0x1", "sha_kunci": "0x1", "berkas": "x"}
        with mock.patch.object(reviewmod.locks, "status", return_value=locked):
            rep = self.run_review()
            self.assertFalse(rep["mengikat"])                                # terkunci tetapi identitas belum terverifikasi
            with mock.patch.object(reviewmod.submission, "verify_identity", return_value=[]):
                rep2 = self.run_review(identity={"signature": "0x00", "chain_id": 97, "nonce": 1, "deadline": 2, "now_s": 1})
            self.assertTrue(rep2["identitas"]["diverifikasi"])
            # sejak P83 (3 Okt): k yang diketik (sumber 'manual') TIDAK PERNAH mengikat, lolos atau tidak; jalur yang mengikat (k dari registri)
            # diuji di test_registri.RegistryReviewTests.test_binding_needs_k_from_the_registry
            self.assertEqual(rep2["keluarga"]["sumber"], "manual")
            self.assertFalse(rep2["mengikat"])
            with mock.patch.object(reviewmod.submission, "verify_identity", return_value=["salah"]):
                rep3 = self.run_review(identity={"signature": "0x00", "chain_id": 97, "nonce": 1, "deadline": 2, "now_s": 1})
            self.assertEqual(rep3["vonis"], "TOLAK_IDENTITAS")
            self.assertFalse(rep3["mengikat"])

    def test_invalid_or_closed_kinds_are_rejected_before_any_computation(self):
        bad = self.run_review(self.sub(kind="feed", spec__template=None))
        self.assertEqual(bad["vonis"], "TOLAK_FORMULIR")
        self.assertTrue(any("belum dibuka" in p for p in bad["masalah_formulir"]))
        self.assertEqual(bad["gerbang"], [])
        self.assertFalse(bad["mengikat"])
        self.assertIn("PENGAJUAN DITOLAK", reviewmod.render(bad))
        dup = self.run_review(existing_ids=["TREND-ETH-30"])
        self.assertEqual(dup["vonis"], "TOLAK_FORMULIR")

    def test_trials_include_declared_percobaan_and_family_history(self):
        rep = self.run_review(prior_family_submissions=4)
        self.assertEqual(rep["n_trials"], 6 + 4 + 1)                          # percobaan 6 (contoh) + 4 pengajuan lama + 1
        rep0 = self.run_review()
        self.assertEqual(rep0["n_trials"], 7)
        g3 = [g for g in rep["gerbang"] if g["gate"] == "G3"][0]
        self.assertIn("(N=11)", g3["value"])

    def test_epoch_seed_changes_the_seed_and_the_report(self):
        a = self.run_review()
        b = self.run_review(epoch_seed=12345)
        self.assertEqual(b["seed"], 12345)
        self.assertNotEqual(a["report_sha"], b["report_sha"])

    def test_k4_claims_are_compared_with_measured_inside_the_review(self):
        honest = {g["gate"]: g for g in self.run_review()["gerbang"]}["K4"]
        self.assertIn(honest["status"], ("PASS", "FAIL"))                     # contoh punya klaim: K4 dievaluasi (bukan TB)
        wild = self.sub(evidence__klaim={"sharpe_net": 19.0, "mdd_pct": -1, "n_sinyal": 5, "tahunan_pct": 9000})
        k4 = {g["gate"]: g for g in self.run_review(wild)["gerbang"]}["K4"]
        self.assertEqual(k4["status"], "FAIL", k4["value"])

    def test_render_prints_the_numbers_from_the_report(self):
        rep = self.run_review()
        txt = reviewmod.render(rep)
        for token in ("VONIS:", "KUNCI PARAMETER:", "MENGIKAT:", rep["report_sha"], rep["spec_sha"], rep["data_hash"], "K1", "G1"):
            self.assertIn(token, txt)

    @unittest.skipIf(Account is None, "eth-account tidak terpasang")
    def test_real_signature_flow_end_to_end(self):
        acct = Account.create()
        sub = with_(with_(self.sub(), "identity.issuer_wallet", acct.address), "identity.payout_wallet", acct.address)
        now, deadline, nonce = 1_900_000_000, 1_900_000_600, 3
        msg = encode_typed_data(full_message=submission.typed_data(sub, 97, nonce, deadline))
        sig = "0x" + acct.sign_message(msg).signature.hex().removeprefix("0x")
        ok = reviewmod.review(sub, self.data(), None, gate_params=FAST,
                              identity={"signature": sig, "chain_id": 97, "nonce": nonce, "deadline": deadline, "now_s": now})
        self.assertTrue(ok["identitas"]["diverifikasi"], ok["identitas"])
        replay_attack = reviewmod.review(sub, self.data(), None, gate_params=FAST,
                                         identity={"signature": sig, "chain_id": 97, "nonce": nonce, "deadline": deadline, "now_s": now,
                                                   "used_nonces": [nonce]})
        self.assertEqual(replay_attack["vonis"], "TOLAK_IDENTITAS")
        self.assertTrue(any("nonce" in p for p in replay_attack["identitas"]["masalah"]))


if __name__ == "__main__":
    unittest.main()

import dataclasses
import math
import random
import unittest
from unittest import mock

from engine import chain, gates, slots
from engine.bots import REGISTRY
from engine.data import MarketData
from engine.replay import replay
from engine.series import DAY_MS
from engine.spec import SPECS, sha0x
from engine.target import Target

from .helpers import BNB, BTC, ETH, T0, md_perp, mk_series, regime_closes, walk
from .test_bots import rich_md

SOL = "SOLUSDT"
N = 1500


def trending(seed0=10, n=N):
    return md_perp({a: regime_closes(n, seed0 + i) for i, a in enumerate((BTC, ETH, BNB, SOL))})


def noise(seed0=50, n=N):
    return md_perp({a: walk(n, seed0 + i, drift=0.0, vol=0.02) for i, a in enumerate((BTC, ETH, BNB, SOL))})


def b1(param=20):
    return dataclasses.replace(SPECS["B1-TREND"], param=param)


def by_gate(results):
    return {r.gate: r for r in results}


FAST = gates.GateParams.fast()


def R(gate, status):
    return gates.GateResult(gate, "X", status, "v", "r")


def full_results(**override):
    """Daftar hasil lengkap semua gerbang wajib PASS (G6/G10/K4/K5 TB-boleh) + G11 NA; `override` mengganti status satu gerbang."""
    st = {g: gates.PASS for g in gates.REQUIRED}
    st.update(override)
    out = [R(g, s) for g, s in st.items()]
    out.append(R("G11", gates.NA))
    return out


class GateTests(unittest.TestCase):
    def test_trend_following_on_trending_market_passes_validity_and_edge_gates(self):
        r = by_gate(gates.run_gates(b1(), trending(), None, FAST))
        for g in ("G1", "G2", "G3", "G5", "G8", "G9"):
            self.assertEqual(r[g].status, gates.PASS, f"{g}: {r[g].value}")
        self.assertEqual(r["G10"].status, gates.TB)                     # tanpa petahana: tidak berlaku, bukan lulus
        self.assertEqual(r["G6"].status, gates.TB)                      # bot tanpa jadwal berfase
        self.assertEqual(r["G11"].status, gates.NA)                     # kapasitas tak terukur != lulus
        self.assertEqual({"K1", "K2", "K3", "K4", "K5"} <= set(r), True)

    def test_placebo_verdict_uses_conservative_upper_bound_not_lucky_point_estimate(self):
        few = dataclasses.replace(FAST, placebo_n=30)              # 30 acak: p terkecil 0,032 tetapi batas atas ~0,084 > 0,05
        g8 = by_gate(gates.run_gates(b1(), trending(), None, few))["G8"]
        self.assertEqual(g8.status, gates.FAIL, g8.value)
        self.assertIn("batas atas 95%", g8.value)
        many = dataclasses.replace(FAST, placebo_n=150)
        self.assertEqual(by_gate(gates.run_gates(b1(), trending(), None, many))["G8"].status, gates.PASS)

    def test_no_edge_market_is_rejected(self):
        res = gates.run_gates(b1(), noise(), None, FAST)
        v, fails, nas = gates.verdict(res)
        self.assertEqual(v, "TOLAK", [(r.gate, r.value) for r in res])
        self.assertTrue({"G3", "G8"} & set(fails), fails)
        self.assertEqual(nas, ["G11"])

    def test_lookahead_bot_is_caught_by_pit_gate(self):
        def leaky(spec, data):                                           # sengaja mengintip penutupan bar BESOK
            from engine.data import aligned_closes
            assets = [a for a in spec.universe if a in data.perp]
            grid, closes = aligned_closes(data.perp, assets)
            out = []
            for i, t in enumerate(grid):
                avail = [a for a in assets if closes[a][i] is not None]
                w = {a: 1.0 / len(avail) for a in avail if i + 1 < len(grid) and closes[a][i + 1] and closes[a][i + 1] > closes[a][i]}
                out.append(Target(spec.bot_id, t, w, {}))
            return out
        with mock.patch.dict(REGISTRY, {"B1-TREND": leaky}):
            r = by_gate(gates.run_gates(b1(), trending(), None, FAST))
        self.assertEqual(r["G1"].status, gates.FAIL, r["G1"].value)
        self.assertEqual(gates.verdict(list(r.values()))[0], "TOLAK")

    def test_short_history_and_gappy_data_fail_data_gate(self):
        short = by_gate(gates.run_gates(b1(), trending(n=600), None, FAST))
        self.assertEqual(short["G2"].status, gates.FAIL)
        md = trending()
        gappy = MarketData(perp={a: mk_series(list(s.c), skip=list(range(100, N, 11))) for a, s in md.perp.items()})
        self.assertEqual(by_gate(gates.run_gates(b1(), gappy, None, FAST))["G2"].status, gates.FAIL)

    def test_one_gappy_series_cannot_hide_among_clean_ones(self):
        md = trending()
        perp = dict(md.perp)
        perp[SOL] = mk_series(list(perp[SOL].c), skip=list(range(100, N, 7)))              # ~14 % bolong pada SATU seri
        loose = dataclasses.replace(FAST, max_gap_frac=0.5)                                # batas gabungan dilonggarkan: yang menahan = per seri
        g2 = by_gate(gates.run_gates(b1(), MarketData(perp=perp), None, loose))["G2"]
        self.assertEqual(g2.status, gates.FAIL, g2.value)
        self.assertIn("per seri", g2.rule)

    def test_cost_gate_fails_when_costs_dominate(self):
        c = gates._Ctx(b1(), trending(), dataclasses.replace(FAST, cost_mult=1000.0), None)
        self.assertEqual(gates.g9_cost(c).status, gates.FAIL)

    def test_cost_gate_scales_every_bps_and_pct_key(self):
        sp = dataclasses.replace(b1(), penggaris={"fee_bps_sisi": 7, "biaya_putaran_tipis_pct": 1.0, "funding": "nyata", "catatan": "x"})
        seen = {}

        def fake_replay(spec, data, tg=None, tables=None):
            seen["pen"] = dict(spec.penggaris)
            return [(T0 + i * DAY_MS, 0.001) for i in range(100)]
        c = gates._Ctx(sp, trending(n=100), dataclasses.replace(FAST, cost_mult=3.0), None)
        c._tg = []
        with mock.patch.object(gates, "replay", fake_replay):
            gates.g9_cost(c)
        self.assertEqual(seen["pen"], {"fee_bps_sisi": 21.0, "biaya_putaran_tipis_pct": 3.0, "funding": "nyata", "catatan": "x"})

    def test_marginal_gate_rejects_clones_and_marks_empty_book_not_applicable(self):
        md = trending()
        sp = b1()
        clone = {"KLON": replay(sp, md)}
        self.assertEqual(by_gate(gates.run_gates(sp, md, clone, FAST))["G10"].status, gates.FAIL)       # korelasi 1.0
        self.assertEqual(by_gate(gates.run_gates(sp, md, {}, FAST))["G10"].status, gates.TB)

    def test_phase_gate_sweeps_all_phases_for_scheduled_bots(self):
        sp = dataclasses.replace(SPECS["B2-RS"], param=10)
        res = by_gate(gates.run_gates(sp, rich_md(1300), None, FAST))
        self.assertIn("7 fase", res["G6"].value)

    def test_allocation_bot_must_pass_both_benchmark_and_placebo(self):
        n = 1300
        md = MarketData(spot={BTC: mk_series(regime_closes(n, 3, mu=0.004, vol=0.03)), "PAXGUSDT": mk_series(regime_closes(n, 4, mu=0.0, vol=0.008))})
        sp = dataclasses.replace(SPECS["B5-CORE-RWA"], param=30)
        g8 = by_gate(gates.run_gates(sp, md, None, FAST))["G8"]
        self.assertIn("(a)", g8.value)
        self.assertIn("buy&hold BTCUSDT", g8.value)
        self.assertIn("(b)", g8.value)
        self.assertIn("placebo p", g8.value)

    def test_b4_is_not_measurable(self):
        res = gates.run_gates(SPECS["B4-LISTING-FADE"], MarketData(), None, FAST)
        self.assertEqual([r.status for r in res], [gates.NA])
        self.assertEqual(gates.verdict(res)[0], "TIDAK_TERUKUR")

    def test_a_gate_that_raises_fails_closed_instead_of_vanishing_or_passing(self):
        def boom(c):
            raise RuntimeError("meledak")
        patched = tuple((g, n, boom if g == "G9" else f) for g, n, f in gates.GATES)
        with mock.patch.object(gates, "GATES", patched):
            r = by_gate(gates.run_gates(b1(), trending(), None, FAST))
        self.assertEqual(r["G9"].status, gates.FAIL)
        self.assertIn("RuntimeError", r["G9"].value)
        self.assertEqual(gates.verdict(list(r.values()))[0], "TOLAK")

    def test_verdict_is_fail_closed(self):
        v = gates.verdict
        self.assertEqual(v([])[0], "TIDAK_VALID")                                    # kosong bukan lolos
        self.assertEqual(v([R("G1", gates.PASS)])[0], "TIDAK_VALID")                 # gerbang wajib hilang
        self.assertEqual(v(full_results())[0], "LOLOS_SHADOW")                       # hanya G11 yang boleh NA
        self.assertEqual(v(full_results(G3=gates.NA))[0], "TIDAK_TERUKUR")           # NA pada gerbang inti memblokir
        self.assertEqual(v(full_results(G3=gates.FAIL))[0], "TOLAK")
        self.assertEqual(v(full_results(K2=gates.FAIL, G6=gates.TB))[0], "TOLAK")
        self.assertEqual(v(full_results(G6=gates.TB, G10=gates.TB, K4=gates.TB, K5=gates.TB))[0], "LOLOS_SHADOW")
        no_k = [r for r in full_results() if not r.gate.startswith("K")]
        self.assertEqual(v(no_k)[0], "TIDAK_VALID")                                  # KPI wajib ada
        self.assertEqual(v([gates.GateResult("G*", "SEMUA", gates.FAIL, "x", "y")])[0], "TOLAK")
        txt = gates.format_results("uji", full_results(G3=gates.FAIL))
        self.assertIn("VONIS: TOLAK", txt)

    def test_gates_are_deterministic(self):
        md = trending()
        a = [(r.gate, r.status, r.value) for r in gates.run_gates(b1(), md, None, FAST)]
        b = [(r.gate, r.status, r.value) for r in gates.run_gates(b1(), md, None, FAST)]
        self.assertEqual(a, b)

    def test_bootstrap_uses_seed(self):
        r = random.Random(3)
        vals = [r.gauss(0.0004, 0.01) for _ in range(500)]
        q1 = gates._boot_q(vals, FAST)
        self.assertEqual(q1, gates._boot_q(vals, FAST))
        self.assertNotEqual(q1, gates._boot_q(vals, dataclasses.replace(FAST, seed=FAST.seed + 1)))

    def test_deflated_sharpe_threshold_rises_with_the_number_of_trials(self):
        self.assertEqual(gates.expected_max_z(1), 0.0)
        self.assertAlmostEqual(gates.expected_max_z(2), 0.52, delta=0.06)            # E[maks 2 normal baku] = 0,564
        zs = [gates.expected_max_z(n) for n in (2, 6, 20, 100, 476, 10000)]
        self.assertEqual(zs, sorted(zs))
        self.assertAlmostEqual(gates.min_sharpe_for_trials(1, 6.7, 0.5), 0.5)       # honest N=1: ambang dasar
        self.assertGreater(gates.min_sharpe_for_trials(476, 6.7, 0.5), 1.0)         # 476 percobaan: yang muncul karena untung > 1
        self.assertGreater(gates.min_sharpe_for_trials(476, 6.7, 0.5), gates.min_sharpe_for_trials(20, 6.7, 0.5))
        self.assertGreater(gates.min_sharpe_for_trials(20, 2.0, 0.5), gates.min_sharpe_for_trials(20, 8.0, 0.5))   # riwayat pendek: ambang lebih tinggi

    def test_g3_uses_trials_and_prints_the_threshold(self):
        rng = random.Random(11)
        c1 = gates._Ctx(b1(), trending(n=100), FAST, None)
        c1._pnl = [(T0 + i * DAY_MS, rng.gauss(0.0006, 0.01)) for i in range(1500)]            # Sharpe tahunan ~1,1 pada ~4,1 tahun
        ok = gates.g3_net(c1)
        self.assertEqual(ok.status, gates.PASS, ok.value)
        self.assertIn("(N=1)", ok.value)
        c2 = gates._Ctx(b1(), trending(n=100), dataclasses.replace(FAST, n_trials=10 ** 6), None)
        c2._pnl = c1._pnl                                                                       # bukti yang SAMA, tetapi sejuta percobaan di baliknya
        hard = gates.g3_net(c2)
        self.assertEqual(hard.status, gates.FAIL, hard.value)
        self.assertIn("N=1000000", hard.value)

    def test_plateau_helpers_respect_parameter_type_and_need_enough_variants(self):
        self.assertEqual(gates._vary(0.1, 0.5), 0.05)
        self.assertIsInstance(gates._vary(0.1, 0.5), float)
        self.assertEqual(gates._vary(2, 1.5), 3)
        self.assertEqual(gates._vary(3, 0.5), 2)
        self.assertEqual(gates._vary(1, 0.5), 2)                                     # lantai 2
        # parameter kecil: hanya 1-2 varian berbeda -> gerbang tidak boleh menyusutkan standarnya sendiri
        res = by_gate(gates.run_gates(b1(2), trending(), None, FAST))
        self.assertEqual(res["G5"].status, gates.FAIL, res["G5"].value)
        self.assertIn("varian berbeda", res["G5"].value)

    def test_plateau_varies_the_candidates_own_parameter_not_the_template_default(self):
        res = by_gate(gates.run_gates(b1(20), trending(), None, FAST))["G5"]                  # kandidat N=20; bawaan template 60
        self.assertIn("dasar 20:", res.value)
        for v in ("10:", "15:", "25:", "30:"):                                                # x0,5 x0,75 x1,25 x1,5 dari 20 - bukan dari 60
            self.assertIn(v, res.value)
        self.assertNotIn("45:", res.value)

    def test_g4_requires_recent_to_keep_a_fraction_of_the_full_sample_sharpe(self):
        c = gates._Ctx(b1(), trending(n=100), FAST, None)
        rng = random.Random(5)
        early = [(T0 + i * DAY_MS, rng.gauss(0.004, 0.005)) for i in range(1000)]               # Sharpe tahunan tinggi
        # 730 hari terakhir: positif tetapi nyaris nol -> meluruh dari ~tinggi ke ~0
        decayed = early + [(T0 + (1000 + i) * DAY_MS, rng.gauss(0.00003, 0.02)) for i in range(730)]
        c._pnl = decayed
        r = gates.g4_recent(c)
        self.assertEqual(r.status, gates.FAIL, r.value)
        healthy = [(T0 + i * DAY_MS, rng.gauss(0.004, 0.005)) for i in range(1730)]
        c._pnl = healthy
        self.assertEqual(gates.g4_recent(c).status, gates.PASS)
        c._pnl = early + [(T0 + (1000 + i) * DAY_MS, rng.gauss(-0.002, 0.005)) for i in range(730)]
        self.assertEqual(gates.g4_recent(c).status, gates.FAIL)


# ---------------------------------------------------------------- slot

DAY = slots.DAY_S
NOW = 1_800_000_000
FAB = slots.FABIUS


def ext(i):
    """Alamat EIP-55 sah dan berbeda untuk i = 1..9 (hanya angka: checksum = dirinya)."""
    return "0x" + str(i) * 40


WA, WB, WC = (chain.to_checksum_address("0x" + c * 40) for c in "abc")
P1, P2 = "0x" + "1" * 40, "0x" + "2" * 40


def E(i, issuer=FAB, identity=False, age_days=200, score=100.0, payout=None):
    pay = "" if issuer == FAB else (payout or issuer)
    return slots.Entry(bot_id=f"BOT{i}", issuer=issuer, spec_sha=f"0x{i:064x}", fingerprint=f"0x{i + 5000:064x}",
                       admitted_s=NOW - age_days * DAY, identity=identity, score_bps=score, payout=pay)


def CH(book, i=99, issuer=WA, verdict="LOLOS_SHADOW", days=90, score=500.0, paired=None, payout=None, book_hash=None, fp=None):
    return slots.Challenger(bot_id=f"NEW{i}", issuer=issuer, spec_sha=f"0x{i + 1000:064x}", fingerprint=fp or f"0x{i + 9000:064x}",
                            gate_verdict=verdict, report_sha="0x" + "ab" * 32, book_sha=book_hash or slots.book_sha(book),
                            shadow_days=days, shadow_score_bps=score, paired=paired or {}, payout=(payout or issuer) if issuer != FAB else "")


def full_book(scores=(10, 20, 30, 40, 50, 60, 70, 80, 90), identity_score=-999.0):
    return [E(0, identity=True, score=identity_score)] + [E(i + 1, issuer=ext(i + 1), score=s) for i, s in enumerate(scores)]


STRONG = (500.0, 4.0)


def beats(book, who="BOT1", stat=STRONG):
    return {who: stat}


class SlotTests(unittest.TestCase):
    def test_book_invariants(self):
        self.assertEqual(slots.book_problems(full_book()), [])
        self.assertTrue(any("maksimum" in p for p in slots.book_problems(full_book() + [E(50)])))
        self.assertTrue(any("identitas" in p for p in slots.book_problems([E(1), E(2)])))
        self.assertTrue(any("ganda" in p for p in slots.book_problems([E(0, identity=True), E(0)])))
        self.assertTrue(any("milik FABIUS" in p for p in slots.book_problems([E(0, issuer=WA, identity=True)])))
        self.assertTrue(any("per penerbit" in p for p in slots.book_problems([E(0, identity=True), E(1, WA), E(2, WA), E(3, WA)])))
        self.assertEqual(slots.book_problems([]), [])
        dup_fp = dataclasses.replace(E(2), fingerprint=E(1).fingerprint)
        self.assertTrue(any("fingerprint ganda" in p for p in slots.book_problems([E(0, identity=True), E(1), dup_fp])))

    def test_required_fields_have_no_fail_open_defaults(self):
        with self.assertRaises(TypeError):
            slots.Entry(bot_id="x", issuer=FAB, spec_sha="s", fingerprint="f")               # admitted_s wajib: bawaan 0 melewati masa tenggang
        with self.assertRaises(TypeError):
            slots.Entry("x", FAB, "s", "f", 0)                                                # hanya kata-kunci

    def test_book_validity_checks_issuer_payout_scores_and_time(self):
        probs = lambda e: slots.book_problems([E(0, identity=True), e])
        self.assertTrue(any("EIP-55" in p for p in probs(dataclasses.replace(E(1), issuer="siapa-saja"))))       # string bebas bukan penerbit sah
        self.assertTrue(any("payout" in p for p in probs(dataclasses.replace(E(1, issuer=WA), payout=""))))
        self.assertTrue(any("payout" in p for p in probs(dataclasses.replace(E(1, issuer=WA), payout="bukan-alamat"))))
        self.assertTrue(any("tidak hingga" in p for p in probs(E(1, score=float("nan")))))
        self.assertTrue(any("tidak hingga" in p for p in probs(E(1, score=float("inf")))))
        self.assertTrue(any("admitted_s" in p for p in probs(dataclasses.replace(E(1), admitted_s=-5))))
        self.assertEqual(probs(dataclasses.replace(E(1), score_bps=None)), [])

    def test_reject_reasons(self):
        book = [E(0, identity=True)]
        d = lambda ch, b=book: slots.decide(b, ch, NOW)
        self.assertEqual(d(CH(book, verdict="TOLAK")).action, slots.REJECT)
        self.assertEqual(d(CH(book, verdict="TIDAK_TERUKUR")).action, slots.REJECT)
        self.assertEqual(d(CH(book, verdict="TIDAK_VALID")).action, slots.REJECT)
        self.assertEqual(d(CH(book, days=59)).action, slots.REJECT)
        for bad in (None, 0.0, -5.0, float("nan"), float("-inf")):
            self.assertEqual(d(CH(book, score=bad)).action, slots.REJECT, repr(bad))
        self.assertEqual(d(CH(book, score=float("inf"))).action, slots.REJECT)              # tak hingga bukan bukti
        dup_id = dataclasses.replace(CH(book), bot_id="BOT0")
        self.assertEqual(d(dup_id).action, slots.REJECT)
        same_spec = dataclasses.replace(CH(book), spec_sha=book[0].spec_sha)
        self.assertEqual(d(same_spec).action, slots.REJECT)
        renamed = CH(book, fp=book[0].fingerprint)                                          # ganti nama, spesifikasi efektif sama
        r = d(renamed)
        self.assertEqual(r.action, slots.REJECT)
        self.assertIn("efektif", r.reason)
        self.assertEqual(d(CH(book, issuer="siapa-saja")).action, slots.REJECT)
        self.assertEqual(d(dataclasses.replace(CH(book), payout="")).action, slots.REJECT)

    def test_stale_review_report_is_rejected_when_the_book_changed(self):
        book = [E(0, identity=True)]
        ch = CH(book)
        self.assertEqual(slots.decide(book, ch, NOW).action, slots.ADMIT)
        changed = book + [E(1)]
        d = slots.decide(changed, ch, NOW)
        self.assertEqual(d.action, slots.REJECT)
        self.assertIn("basi", d.reason)
        self.assertEqual(slots.decide(book, CH(book, book_hash="0x" + "00" * 32), NOW).action, slots.REJECT)

    def test_per_issuer_cap_counts_shared_payout_wallet_as_one_family(self):
        held = [E(0, identity=True), E(1, WA, payout=P1), E(2, WA, payout=P1)]
        sybil = CH(held, issuer=WB, payout=P1)                              # penerbit BARU tetapi dompet payout yang sama -> satu orang
        self.assertEqual(slots.decide(held, sybil, NOW).action, slots.REJECT)
        self.assertEqual(slots.decide(held, CH(held, issuer=WB, payout=P2), NOW).action, slots.ADMIT)
        capped = [E(0, identity=True), E(1, WA), E(2, WA)]
        self.assertEqual(slots.decide(capped, CH(capped, issuer=WA), NOW).action, slots.REJECT)
        self.assertEqual(slots.decide(capped, CH(capped, issuer=WB), NOW).action, slots.ADMIT)
        chained = [E(0, identity=True), E(1, WA, payout=P1), E(2, WB, payout=P1), E(3, WC, payout=P1)]
        self.assertTrue(any("per penerbit" in x for x in slots.book_problems(chained)))
        # rantai: A(P1) - B(P1, lalu P2) tidak menggabung A dan C hanya lewat B bila payout masing-masing berbeda
        self.assertEqual(slots.book_problems([E(0, identity=True), E(1, WA, payout=P1), E(2, WB, payout=P2)]), [])

    def test_admit_while_capacity_remains_and_apply(self):
        book = [E(0, identity=True)]
        ch = CH(book)
        d = slots.decide(book, ch, NOW)
        self.assertEqual(d.action, slots.ADMIT)
        self.assertIn("BUKAN bukti edge", d.reason)
        new = slots.apply(book, d, ch, NOW)
        self.assertEqual([e.bot_id for e in new], ["BOT0", "NEW99"])
        self.assertEqual(len(book), 1)                                   # buku lama tak berubah
        self.assertFalse(new[-1].identity)
        self.assertEqual((new[-1].admitted_s, new[-1].payout, new[-1].fingerprint), (NOW, WA, ch.fingerprint))

    def test_full_book_replaces_weakest_only_with_significant_paired_gap(self):
        book = full_book()
        d = slots.decide(book, CH(book, paired=beats(book)), NOW)
        self.assertEqual((d.action, d.evict), (slots.REPLACE, "BOT1"))
        self.assertIn("t = 4.0", d.reason)
        new = slots.apply(book, d, CH(book, paired=beats(book)), NOW)
        self.assertEqual(len(new), 10)
        self.assertNotIn("BOT1", [e.bot_id for e in new])
        self.assertIn("NEW99", [e.bot_id for e in new])
        self.assertEqual(slots.book_problems(new), [])

    def test_noise_cannot_replace_an_incumbent(self):
        book = full_book()
        for stat in ((99.9, 4.0), (500.0, 1.99), (500.0, float("nan")), (float("nan"), 3.0)):
            d = slots.decide(book, CH(book, paired=beats(book, stat=stat)), NOW)
            self.assertEqual(d.action, slots.BENCH, stat)
        self.assertEqual(slots.decide(book, CH(book, paired={}), NOW).action, slots.BENCH)                         # tanpa statistik berpasangan
        self.assertEqual(slots.decide(book, CH(book, paired={"BOT2": STRONG}), NOW).action, slots.BENCH)        # statistik untuk penghuni lain
        self.assertEqual(slots.decide(book, CH(book, paired=beats(book, stat=(100.0, 2.0))), NOW).action, slots.REPLACE)   # tepat di ambang
        self.assertEqual(slots.decide(book, CH(book, paired=beats(book, stat=(500.0, math.inf))), NOW).action, slots.REPLACE)

    def test_identity_is_never_evicted_even_if_worst(self):
        book = full_book(identity_score=-5000.0)
        d = slots.decide(book, CH(book, score=1000.0, paired=beats(book)), NOW)
        self.assertEqual((d.action, d.evict), (slots.REPLACE, "BOT1"))      # bukan BOT0 (identitas, skor terburuk)

    def test_grace_period_unmeasured_and_dead_incumbents(self):
        book = full_book()
        book[1] = E(1, issuer=ext(1), age_days=10, score=-100.0)               # terlemah tetapi masih masa tenggang
        book[2] = dataclasses.replace(book[2], score_bps=None)                 # belum terukur, usia 200 hari -> SUDAH melewati tenggang + jendela
        d = slots.decide(book, CH(book, paired={}), NOW)
        self.assertEqual((d.action, d.evict), (slots.REPLACE, "BOT2"))         # mati/basi: penantang sah mana pun boleh menggantikan
        self.assertIn("basi", d.reason)
        young_unmeasured = [E(0, identity=True)] + [dataclasses.replace(E(i, issuer=ext(i), age_days=100), score_bps=None) for i in range(1, 10)]
        d2 = slots.decide(young_unmeasured, CH(young_unmeasured), NOW)         # usia 100 < 60 + 90 hari: tak terukur != lemah
        self.assertEqual(d2.action, slots.BENCH)
        only_protected = [E(0, identity=True)] + [E(i, issuer=ext(i), age_days=5) for i in range(1, 10)]
        d3 = slots.decide(only_protected, CH(only_protected, score=1000.0), NOW)
        self.assertEqual(d3.action, slots.BENCH)
        self.assertIn("tidak ada penghuni", d3.reason)

    def test_epoch_replacement_quota(self):
        book = full_book()
        d = slots.decide(book, CH(book, score=1000.0, paired=beats(book)), NOW, replaced_this_epoch=1)
        self.assertEqual(d.action, slots.BENCH)
        self.assertIn("kuota", d.reason)

    def test_tie_break_is_a_hash_not_an_alphabetical_name_the_issuer_chooses(self):
        book = full_book(scores=(5, 5, 50, 60, 70, 80, 90, 95, 99))
        ep = slots.epoch_id(NOW, slots.SlotParams())
        tied = [book[1], book[2]]
        expect = min(tied, key=lambda e: sha0x({"fp": e.fingerprint, "epoch": ep})).bot_id
        paired = {"BOT1": STRONG, "BOT2": STRONG}
        d1 = slots.decide(book, CH(book, score=500.0, paired=paired), NOW)
        d2 = slots.decide(list(reversed(book)), CH(list(reversed(book)), score=500.0, paired=paired), NOW)
        self.assertEqual(d1.evict, expect)
        self.assertEqual(d2.evict, expect)                                       # tidak bergantung urutan masuk

    def test_decide_epoch_ranks_challengers_together_and_allows_one_change(self):
        book = full_book()
        weak = CH(book, i=1, issuer=WA, paired=beats(book, stat=(150.0, 2.5)))
        strong = CH(book, i=2, issuer=WB, paired=beats(book, stat=(600.0, 5.0)))
        res = slots.decide_epoch(book, [weak, strong], NOW)
        by = {ch.bot_id: d for ch, d in res}
        self.assertEqual(by["NEW2"].action, slots.REPLACE)
        self.assertEqual(by["NEW1"].action, slots.BENCH)
        self.assertIn("satu perubahan per epoch", by["NEW1"].reason)
        res2 = slots.decide_epoch(book, [strong, weak], NOW)                      # urutan datang tidak menentukan pemenang
        self.assertEqual({ch.bot_id: d.action for ch, d in res2}, {"NEW2": slots.REPLACE, "NEW1": slots.BENCH})
        single = slots.decide_epoch(book, [weak], NOW)
        self.assertEqual(single[0][1].action, slots.REPLACE)

    def test_can_submit_queue_cap_and_cooldown(self):
        p = slots.SlotParams()
        self.assertEqual(slots.can_submit(family_pending=0, last_rejected_s=None, now_s=NOW)[0], True)
        self.assertEqual(slots.can_submit(family_pending=p.queue_max_per_family, last_rejected_s=None, now_s=NOW)[0], False)
        ok, why = slots.can_submit(family_pending=0, last_rejected_s=NOW - 5 * DAY, now_s=NOW)
        self.assertFalse(ok)
        self.assertIn("masa tunggu", why)
        self.assertTrue(slots.can_submit(family_pending=1, last_rejected_s=NOW - 31 * DAY, now_s=NOW)[0])

    def test_invalid_book_is_refused_not_silently_decided(self):
        with self.assertRaises(ValueError):
            slots.decide([E(1), E(2)], CH([E(1), E(2)]), NOW)                    # tanpa bot identitas

    def test_apply_refuses_to_evict_identity_or_unknown(self):
        book = full_book()
        with self.assertRaises(ValueError):
            slots.apply(book, slots.Decision(slots.REPLACE, "BOT0", "x"), CH(book), NOW)
        with self.assertRaises(ValueError):
            slots.apply(book, slots.Decision(slots.REPLACE, "TIDAKADA", "x"), CH(book), NOW)
        self.assertEqual(slots.apply(book, slots.Decision(slots.BENCH, None, "x"), CH(book), NOW), book)
        with self.assertRaises(ValueError):
            slots.apply(book, slots.Decision(slots.ADMIT, None, "x"), CH(book), NOW)                   # buku penuh: melanggar kapasitas

    def test_remove_and_designate_identity_rules(self):
        book = [E(0, identity=True), E(1)]
        with self.assertRaises(ValueError):
            slots.remove(book, "BOT0")                                       # identitas terakhir
        book2 = slots.designate_identity(book, "BOT1")
        self.assertEqual([e.bot_id for e in slots.remove(book2, "BOT0")], ["BOT1"])
        with self.assertRaises(ValueError):
            slots.designate_identity([E(0, identity=True), E(1, issuer=WA)], "BOT1")                  # bukan milik Fabius
        with self.assertRaises(ValueError):
            slots.remove(book, "TIDAKADA")

    def test_book_sha_is_order_independent_and_tracks_membership(self):
        a = full_book()
        self.assertEqual(slots.book_sha(a), slots.book_sha(list(reversed(a))))
        self.assertNotEqual(slots.book_sha(a), slots.book_sha(a[:-1]))
        swapped = a[:-1] + [dataclasses.replace(a[-1], fingerprint="0x" + "ee" * 32)]
        self.assertNotEqual(slots.book_sha(a), slots.book_sha(swapped))

    def test_score_is_net_pnl_by_calendar_window_not_win_rate_not_row_count(self):
        pnl = [(T0 + i * DAY_MS, 0.001) for i in range(80)] + [(T0 + (80 + i) * DAY_MS, -0.01) for i in range(10)]
        self.assertAlmostEqual(slots.rolling_score_bps(pnl, 90), (0.08 - 0.10) * 1e4)
        self.assertIsNone(slots.rolling_score_bps(pnl[:50], 90))
        self.assertAlmostEqual(slots.win_rate_diag(pnl), 80 / 90)              # win-rate tinggi, PnL negatif: persis kasus F-D16
        self.assertIsNone(slots.win_rate_diag([(0, 0.0)]))
        # bot yang berhenti 200 hari lalu TIDAK mewarisi jendela lama: jendela dihitung dari `end_ms`, bukan dari baris terakhirnya
        old = [(T0 + i * DAY_MS, 0.002) for i in range(120)]
        self.assertIsNotNone(slots.rolling_score_bps(old, 90))
        self.assertIsNone(slots.rolling_score_bps(old, 90, end_ms=T0 + 320 * DAY_MS))
        self.assertIsNone(slots.rolling_score_bps([(T0, float("nan"))] * 100, 90))

    def test_paired_stat_uses_the_same_days_and_returns_t(self):
        rng = random.Random(1)
        inc = [(T0 + i * DAY_MS, rng.gauss(0.0, 0.01)) for i in range(120)]
        ch = [(t, v + 0.004) for t, v in inc]                                  # selisih konstan +40 bps/hari
        end = T0 + 119 * DAY_MS
        gap, t = slots.paired_stat(ch, inc, 90, end)
        self.assertAlmostEqual(gap, 0.004 * 90 * 1e4, places=3)
        self.assertEqual(t, math.inf)                                           # tanpa varians selisih
        noisy = [(tt, v + 0.004 + rng.gauss(0, 0.02)) for tt, v in inc]
        gap2, t2 = slots.paired_stat(noisy, inc, 90, end)
        import statistics
        d = [a[1] - b[1] for a, b in zip(noisy, inc) if a[0] > end - 90 * DAY_MS]
        self.assertAlmostEqual(t2, statistics.mean(d) / (statistics.stdev(d) / math.sqrt(len(d))), places=9)
        self.assertAlmostEqual(gap2, sum(d) * 1e4, places=6)
        self.assertTrue(math.isfinite(t2))
        self.assertIsNone(slots.paired_stat(ch[:30], inc, 90, end))             # cakupan kurang
        self.assertIsNone(slots.paired_stat(ch, [(t + 1000 * DAY_MS, v) for t, v in inc], 90, end))   # hari tidak sama

    def test_killer_triggered_enforces_the_structured_killer(self):
        k = lambda m, c, th, w=10: {"metric": m, "comparator": c, "threshold": th, "window_sinyal": w}
        loss = [-0.001] * 60
        self.assertTrue(slots.killer_triggered(k("net_pnl_bps", "<", -100), loss, 20))                 # -600 bps < -100
        self.assertFalse(slots.killer_triggered(k("net_pnl_bps", "<", -1000), loss, 20))
        self.assertTrue(slots.killer_triggered(k("net_pnl_bps", "<=", -600), loss, 20))                # sama dengan ambang
        self.assertFalse(slots.killer_triggered(k("net_pnl_bps", "<", -600), loss, 20))
        self.assertFalse(slots.killer_triggered(k("net_pnl_bps", "<", -100, w=50), loss, 20))          # sinyal belum cukup: tidak membunuh
        self.assertTrue(slots.killer_triggered(k("rata_net_per_sinyal_bps", "<", -10), loss, 20))      # -600/20 = -30 per sinyal
        self.assertTrue(slots.killer_triggered(k("mdd_pct", "<", -3), loss, 20))                       # drawdown ~ -5,8 %
        self.assertFalse(slots.killer_triggered(k("mdd_pct", "<", -30), loss, 20))
        rng = random.Random(2)
        good = [rng.gauss(0.003, 0.005) for _ in range(120)]
        self.assertFalse(slots.killer_triggered(k("sharpe", "<", 0), good, 20))
        self.assertTrue(slots.killer_triggered(k("sharpe", "<", 50), good, 20))
        self.assertFalse(slots.killer_triggered(k("sharpe", "<", 0), [0.001] * 10, 20))                # Sharpe tak terdefinisi: tidak membunuh
        self.assertTrue(slots.killer_triggered(k("net_pnl_bps", "<", -100), [0.001, float("nan")], 20))  # data rusak: gagal tertutup
        with self.assertRaises(ValueError):
            slots.killer_triggered(k("perasaan", "<", 0), loss, 20)


if __name__ == "__main__":
    unittest.main()

"""P156 (F4, epik 11 §6): evaluasi + perbaikan diri meja v2 sebagai BAYANGAN. IC / hit / kalibrasi pada kasus hitung tangan; rumus bobot agent
(pemanasan, jendela, batas 0,5-2, irama per jam) dan bobot yang berubah sesuai rumus di bayangan; buku ablasi = buku Fabius tercatat bila tidak ada
yang dibuang (SETIA, pola P163); usulan evaluator tidak punya jalan ke konfigurasi hidup; sakelar F4 mati = nol efek, bayangan = keputusan hidup
identik; arsip HTTP gerbang -> CLI rapor harian (gerbang dan berkas luring). Binance + model dipalsukan."""
import copy
import io
import json
import math
import os
import random
import shutil
import sys
import tempfile
import threading
import time
import types
import unittest
from contextlib import redirect_stdout
from http.server import ThreadingHTTPServer
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, "tools"), ROOT, HERE]

import meja                                                         # noqa: E402
import meja2                                                        # noqa: E402
import meja_data as md                                              # noqa: E402
import meja_eval as me                                              # noqa: E402
import meja_slot as ms                                              # noqa: E402
from test_meja2 import UNI, FakePasar, out                          # noqa: E402

B = meja2.BOTS                                                       # B1-TREND, B2-RS, B3-CARRY, B4-LISTING-FADE, B5-CORE-RWA, B6-BOUNCE
T0 = 1_791_200_100                                                   # 11:35 UTC; 30 siklus tetap di hari yang sama


def kep(bot, skor, k=0.7, eks=0.8, ins=(("SOLUSDT", 0.8, ("r_1j",)),), faktor=("r_1j",), veto=()):
    return {"bot": bot, "skor_bot": {b: skor.get(b, 0) for b in B}, "k": k, "eksposur": eks, "faktor": list(faktor),
            "instrumen": [{"aset": a, "k": x, "faktor": list(f)} for a, x, f in ins], "veto": [{"aset": a, "faktor": f} for a, f in veto]}


def get_harga(i):
    def get(url):
        return [{"symbol": a, "markPrice": str(100 + (j + 1) * 0.6 * i * (1 if j % 2 else -1)), "lastFundingRate": "0"} for j, a in enumerate(UNI)]
    return get


def jawab(i):
    """Tiga agent palsu yang bergantian: B1 -> B5 -> B1; agent c gagal tiap siklus ke-4."""
    def call(ag, system, user):
        if ag["slug"] == "c" and i % 4 == 3:
            raise RuntimeError("429")
        if 10 <= i < 20:
            return out(bot="B5-CORE-RWA", skor={b: (80 if b == "B5-CORE-RWA" else (40 if b == "B1-TREND" else -10)) for b in B},
                       ins=(("BTCUSDT", 80), ("PAXGUSDT", 70)), eks=70)
        return out(skor={b: (90 if b == "B1-TREND" else (20 * B.index(b) - 50)) for b in B}, ins=(("SOLUSDT", 80), ("NEARUSDT", 60), ("WIFUSDT", 70)), eks=60)
    return call


AGENTS = [{"slug": s, "agent_id": i + 1, "model": "m"} for i, s in enumerate("abc")]
SNAP = {"sha": "0xabc", "t": T0, "fitur_aset": {"SOLUSDT": {"r_1j": 0.01}, "WIFUSDT": {"rug_bahaya": True}}, "fitur_bot": {"B1-TREND": {"breadth_naik_1j": 0.9}}}


def jalankan(n, P=me.PARAMS_F4, lewati=(), books=None, st=None, ubah_rek=None):
    """n siklus meja hidup (`meja2.siklus2`) + bayangan F4 sesudah tiap siklus, seperti gerbang. -> (books, st, [(rek, rekaman F4)])."""
    books = {} if books is None else books
    ring, hasil = {}, []
    for i in range(n):
        if i in lewati:
            continue
        t0 = T0 + i * 300
        pra = me.pra_siklus(books)
        rek, harga = meja2.siklus2(t0, AGENTS, books, ring, jawab(i), SNAP, FakePasar(), get=get_harga(i), log=lambda m: None)
        salinan = copy.deepcopy((pra, rek, harga))
        rek_f4 = ubah_rek(i, rek) if ubah_rek else rek
        st, ev = me.siklus_bayangan(st, pra, rek_f4, harga, SNAP, FakePasar(), t0, P)
        assert meja.canon(salinan) == meja.canon((pra, rek, harga))                         # bayangan tidak mengubah masukan hidup
        hasil.append((rek, ev))
    return books, st, hasil


class MathTests(unittest.TestCase):
    def test_rank_ic_matches_a_hand_computed_case_with_ties(self):
        skor = {"B1-TREND": 70, "B2-RS": 10, "B3-CARRY": -20, "B4-LISTING-FADE": 30, "B5-CORE-RWA": 40, "B6-BOUNCE": 0}
        R = {"B1-TREND": 0.01, "B2-RS": -0.02, "B3-CARRY": 0.0, "B4-LISTING-FADE": 0.005, "B5-CORE-RWA": 0.002, "B6-BOUNCE": 0.0}
        self.assertEqual(me.peringkat([R[b] for b in B]), [6, 1, 2.5, 5, 4, 2.5])                 # B3 dan B6 seri di 0 -> (2+3)/2
        self.assertEqual(me.peringkat([skor[b] for b in B]), [6, 3, 1, 4, 5, 2])
        # rx-3,5 = [2,5 -0,5 -2,5 0,5 1,5 -1,5]; ry-3,5 = [2,5 -2,5 -1 1,5 0,5 -1]; sum xy = 13; sum x2 = 17,5; sum y2 = 17
        self.assertEqual(me.spearman([skor[b] for b in B], [R[b] for b in B]), round(13 / math.sqrt(17.5 * 17), 6))
        self.assertEqual(me.spearman([1, 2, 3], [10, 20, 30]), 1.0)
        self.assertEqual(me.spearman([1, 2, 3], [30, 20, 10]), -1.0)
        self.assertIsNone(me.spearman([5, 5, 5], [1, 2, 3]))                                     # skor sama semua: tanpa IC, bukan 0
        self.assertIsNone(me.spearman([1, 2], [1, 2]))
        self.assertIsNone(me.spearman([1, 2, 3], [1, 2]))

    def test_top_pick_hit_counts_ties_and_reports_the_random_baseline(self):
        skor = {b: 10 * i for i, b in enumerate(B)}
        R = {"B1-TREND": 0.01, "B2-RS": -0.02, "B3-CARRY": 0.0, "B4-LISTING-FADE": 0.005, "B5-CORE-RWA": 0.002, "B6-BOUNCE": 0.0}
        v = me.nilai_agent(skor, "B1-TREND", R)
        self.assertEqual((v["hit"], v["acak"], v["terbaik"], v["r_pilihan"]), (1, round(1 / 6, 6), "B1-TREND", 0.01))
        turun = {"B1-TREND": -0.01, "B2-RS": -0.02, "B3-CARRY": 0.0, "B4-LISTING-FADE": -0.005, "B5-CORE-RWA": -0.002, "B6-BOUNCE": 0.0}
        self.assertEqual((me.nilai_agent(skor, "B6-BOUNCE", turun)["hit"], me.nilai_agent(skor, "B6-BOUNCE", turun)["acak"]), (1, round(2 / 6, 6)))
        self.assertEqual(me.nilai_agent(skor, "B1-TREND", turun)["hit"], 0)                       # datar (B3/B6) mengalahkan B1 yang turun

    def test_calibration_buckets_and_biggest_miss_are_hand_computed(self):
        rows = [{"siklus": 300 * i, "k": k, "hit": h, "acak": 0.2, "ic": ic, "bot": "B1-TREND", "r_pilihan": rp, "terbaik": "B5-CORE-RWA", "r_terbaik": rt}
                for i, (k, h, ic, rp, rt) in enumerate([(0.40, 1, 0.5, 0.01, 0.01), (0.45, 0, None, -0.01, 0.02), (0.70, 1, 0.1, 0.0, 0.0),
                                                        (0.90, 1, -0.3, 0.02, 0.02), (0.95, 0, 0.2, -0.03, 0.01)])]
        m = me.ringkas(rows)
        self.assertEqual((m["n"], m["n_ic"], m["ic"], m["hit"], m["acak"]), (5, 4, round((0.5 + 0.1 - 0.3 + 0.2) / 4, 6), 0.6, 0.2))
        self.assertEqual([(e["dari"], e["sampai"], e["n"], e["hit"]) for e in m["kalibrasi"]],
                         [(0, 49, 2, 0.5), (50, 64, 0, None), (65, 79, 1, 1.0), (80, 100, 2, 0.5)])
        self.assertEqual(m["kalibrasi"][0]["keyakinan"], 42.5)
        self.assertEqual(m["salah_terbesar"]["siklus"], 1200)                                     # selisih 0,04 (0,95: -3 % vs +1 %)

    def test_bot_portfolio_return_and_missing_data_is_not_evaluated(self):
        self.assertAlmostEqual(me.return_portofolio({"A": 0.5, "B": -0.25}, {"A": 100, "B": 50}, {"A": 102, "B": 49}), 0.5 * 0.02 + 0.25 * 0.02)
        self.assertIsNone(me.return_portofolio({"A": 0.5}, {"A": 100}, {}))                      # SK-M36: harga hilang -> tidak dinilai
        self.assertEqual(me.return_portofolio({}, {}, {}), 0.0)                                   # bot datar = return 0, bukan hilang
        self.assertEqual(me.bobot_normal({"A": 1.0, "B": 1.0, "C": -1.0, "D": 0.0}), {"A": round(1 / 3, 10), "B": round(1 / 3, 10), "C": round(-1 / 3, 10)})
        p = FakePasar()
        w1 = me.portofolio_bot("B1-TREND", UNI, p)
        self.assertEqual(set(w1), {"BTCUSDT", "PAXGUSDT", "SOLUSDT", "WIFUSDT"})                 # NEAR turun 60 hari; NEW tanpa riwayat
        self.assertLessEqual(sum(abs(x) for x in w1.values()), 1 + 1e-9)
        self.assertEqual(me.portofolio_bot("B3-CARRY", UNI, p), {})

        class CandleRusak(FakePasar):
            def harian(self, a):
                if a == "SOLUSDT":
                    raise OSError("klines 451")
                return super().harian(a)
        self.assertIsNone(me.portofolio_bot("B1-TREND", UNI, CandleRusak()))                     # universe bolong = tidak terbaca
        e = {"t": 0, "harga": {"SOLUSDT": 100.0}, "w": {b: ({"SOLUSDT": 1.0} if b == "B1-TREND" else {}) for b in B},
             "kep": {"a": {"skor": {b: i for i, b in enumerate(B)}, "bot": "B6-BOUNCE", "k": 0.5, "kursi": "aktif"}}}
        rows, R, why = me.nilai_entri(e, {"SOLUSDT": 101.0}, 12)
        self.assertEqual((why, R["B1-TREND"], rows[0]["hit"], rows[0]["kursi"]), (None, 0.01, 0, "aktif"))
        self.assertEqual(me.nilai_entri(e, {}, 12)[2], "harga hilang (B1-TREND)")
        self.assertEqual(me.nilai_entri({**e, "w": {**e["w"], "B2-RS": None}}, {"SOLUSDT": 1.0}, 1)[2], "portofolio B2-RS tidak terbaca")


class WeightTests(unittest.TestCase):
    def test_weight_formula_warmup_window_clamp_and_non_finite(self):
        t0 = (T0 // 3600 + 1) * 3600
        rows = lambda ic, n=200, lama=0: [[t0 - 3600 - lama - i * 300, ic] for i in range(n)]    # noqa: E731
        riw = {"baik": rows(0.1), "hebat": rows(0.3), "buruk": rows(-0.2), "baru": rows(0.3), "jarang": rows(0.3, n=100),
               "nan": rows(0.1)[:-1] + [[t0 - 3600, float("nan")]], "lama": rows(0.3, lama=86_400)}
        n_kum = {s: 400 for s in riw} | {"baru": 100}
        W, why = me.hitung_bobot(riw, n_kum, t0)
        self.assertEqual(W, {"baik": 1.5, "hebat": 2.0, "buruk": 0.5, "baru": 1.0, "jarang": 1.0, "nan": 1.0, "lama": 1.0})   # 1 + 5 x IC, batas 0,5-2
        self.assertEqual(why["baru"], "pemanasan 100/288")
        self.assertEqual(why["jarang"], "IC dalam jendela 100 < 144")
        self.assertIn("tidak hingga", why["nan"])                                                 # SK-M37
        self.assertEqual(why["lama"], "IC dalam jendela 0 < 144")                                 # di luar 24 jam terakhir

    def test_weights_change_only_on_the_first_cycle_of_a_new_hour(self):
        jam = T0 // 3600 * 3600
        self.assertTrue(me.perlu_bobot(T0, None))
        self.assertFalse(me.perlu_bobot(jam + 300, jam))
        self.assertFalse(me.perlu_bobot(jam + 3300, jam + 600))
        self.assertTrue(me.perlu_bobot(jam + 3600, jam + 3300))
        self.assertTrue(me.perlu_bobot(jam + 3900, jam + 3300))                                   # siklus :00 bolong -> siklus pertama jam itu

    def test_unit_weights_feed_the_live_consensus_bit_for_bit_and_other_weights_follow_the_formula(self):
        rng = random.Random(156)
        for _ in range(300):
            n = rng.randint(1, 7)
            sah = {f"g{j}": kep(rng.choice(B), {b: rng.randint(-100, 100) for b in B}, k=rng.randint(0, 100) / 100, eks=rng.randint(0, 100) / 100,
                                ins=[(rng.choice(UNI), rng.randint(0, 100) / 100, ("r_1j",)) for _ in range(rng.randint(0, 4))],
                                veto=[(rng.choice(UNI), "rug_bahaya")] if rng.random() < 0.3 else ())
                   for j in range(n)}
            st = {"bot": rng.choice(B), "pegang": rng.randint(0, 5), "instrumen": ["SOLUSDT"], "eksposur": 0.4}
            a = meja2.konsensus2(copy.deepcopy(sah), copy.deepcopy(st), SNAP, n_aktif=n + rng.randint(0, 2))
            for W in ({}, {s: 1.0 for s in sah}):
                self.assertEqual(meja.canon(meja2.konsensus2(me.berbobot(copy.deepcopy(sah), W), copy.deepcopy(st), SNAP, n_aktif=n + 0)),
                                 meja.canon(meja2.konsensus2(copy.deepcopy(sah), copy.deepcopy(st), SNAP, n_aktif=n + 0)))
            self.assertTrue(a)
        sah = {"a": kep("B1-TREND", {"B1-TREND": 100}, k=0.8, eks=0.8), "b": kep("B2-RS", {"B2-RS": 100}, k=0.5, eks=0.2)}
        k, _ = meja2.konsensus2(me.berbobot(sah, {"a": 2.0, "b": 0.5}), {}, None, n_aktif=2)
        self.assertEqual((k["nilai_bot"]["B1-TREND"], k["nilai_bot"]["B2-RS"], k["eksposur"]), (64.0, 10.0, 0.68))   # (2x0,8x100)/2,5; (0,5x0,5x100)/2,5
        self.assertEqual(sah["a"]["k"], 0.8)                                                      # masukan tidak diubah

    def test_shadow_weights_change_exactly_as_the_formula_says_and_only_hourly(self):
        P = copy.deepcopy(me.PARAMS_F4)
        P["bobot"].update(pemanasan=5, n_min_jendela=3)
        days = me.contoh_arsip(hari=1, siklus=40, t_awal=1_791_540_000, P=P)
        ev = [e for d in days for e in d["evaluation"]]
        self.assertTrue(all(e["setia"] for e in ev))
        rows = [r for e in ev for r in e["nilai"] if r["h"] == 12]
        lalu = None
        for e in ev:
            if not e["bobot"]["diperbarui"]:
                self.assertEqual(e["bobot"]["W"], lalu)                                           # di antara jam: tetap
            else:
                self.assertEqual(e["siklus"] % 3600, 0)                                           # siklus pertama jam baru (jendela tanpa bolong)
                for s, w in e["bobot"]["W"].items():                                              # dihitung ulang dari baris nilai yang tercatat
                    ics = [r["ic"] for r in rows if r["agent"] == s and r["siklus"] + 3600 <= e["siklus"] and r["ic"] is not None]
                    exp = 1.0 if len(ics) < 5 else round(max(0.5, min(2.0, 1 + 5 * sum(ics) / len(ics))), 6)
                    self.assertEqual(w, exp, (e["siklus"], s))
            lalu = e["bobot"]["W"]
        akhir = ev[-1]["bobot"]["W"]
        self.assertEqual((akhir["tajam"], akhir["balik"]), (2.0, 0.5))                           # IC +1 -> batas atas; IC -1 -> batas bawah
        self.assertTrue(any(e["dunia"]["bobot"]["ekuitas"] != e["dunia"]["penuh"]["ekuitas"] for e in ev))   # dunia berbobot benar-benar hidup


class AblationTests(unittest.TestCase):
    def test_every_feature_an_agent_may_cite_belongs_to_one_source(self):
        keys = set(md.f_binance(None, None, None)) | set(md.f_dex(None, None, 1)) | set(md.f_rug(None)) | set(md.f_fomo(None, None, "X", "x")) \
            | set(md.f_berita(None, ["X"], 0)) | {f"z_{k}" for k in ("r_1j", "oi_ubah_1j", "taker_beli_jual", "dex_vol_1j_rel", "berita_sebut_6j")} \
            | {k for b in B for k in md.f_bot(b, {}, {}, [])} | set(meja2.FITUR_ATURAN) | {"r_24j", "volume_24j"}
        peta = me.peta_sumber()
        self.assertEqual(sorted(k for k in keys if me.sumber_dari(k, peta) == "lain"), [])
        semua = [f for fs in me.SUMBER.values() for f in fs]
        self.assertEqual(len(semua), len(set(semua)))                                             # satu fitur = satu sumber

    def test_source_ablation_drops_only_what_rests_on_that_source(self):
        peta = me.peta_sumber()
        sah = {"a": kep("B1-TREND", {"B1-TREND": 90}, faktor=("fomo_thesis",)),
               "b": kep("B1-TREND", {"B1-TREND": 90}, faktor=("fomo_thesis", "r_1j"), ins=(("SOLUSDT", 0.9, ("fomo_thesis",)), ("NEARUSDT", 0.8, ("r_1j",))),
                        veto=(("WIFUSDT", "fomo_thesis"), ("BTCUSDT", "rug_bahaya")))}
        asli = copy.deepcopy(sah)
        k2, sn2 = me.tanpa_sumber(sah, SNAP, "fomo", peta)
        self.assertEqual(sorted(k2), ["b"])                                                       # a bertumpu hanya pada FOMO
        self.assertEqual([i["aset"] for i in k2["b"]["instrumen"]], ["NEARUSDT"])
        self.assertEqual([v["aset"] for v in k2["b"]["veto"]], ["BTCUSDT"])
        self.assertEqual(sn2, {**SNAP, "fitur_aset": SNAP["fitur_aset"]})                         # FOMO tidak ada di snapshot ini
        self.assertEqual(sah, asli)
        _, sn3 = me.tanpa_sumber(sah, SNAP, "rugcheck", peta)
        self.assertIsNone(sn3["fitur_aset"]["WIFUSDT"]["rug_bahaya"])                             # veto keras RugCheck hilang di dunia ini
        self.assertTrue(SNAP["fitur_aset"]["WIFUSDT"]["rug_bahaya"])
        two = {"x": kep("B1-TREND", {"B1-TREND": 90}, ins=(("WIFUSDT", 0.9, ("r_1j",)),)), "y": kep("B1-TREND", {"B1-TREND": 90}, ins=(("WIFUSDT", 0.9, ("r_1j",)),))}
        self.assertIn("WIFUSDT", meja2.konsensus2(two, {}, SNAP)[0]["veto"])
        self.assertNotIn("WIFUSDT", meja2.konsensus2(two, {}, sn3)[0]["veto"])
        self.assertEqual(me.sumber_keputusan(sah["b"], peta), ["binance", "fomo", "rugcheck"])

    def test_the_full_shadow_book_equals_the_live_fabius_book_every_cycle(self):
        books, st, hasil = jalankan(30)
        hidup = [next(r for r in rek if r["agent"] == "v2") for rek, _ in hasil]
        for (rek, ev), lv in zip(hasil, hidup):
            self.assertTrue(ev["setia"], (ev["siklus"], ev["beda"]))                              # SETIA: tidak dibuang = buku Fabius tercatat
            self.assertEqual(ev["dunia"]["penuh"]["ekuitas"], lv["ekuitas"])
            self.assertEqual(ev["dunia"]["bobot"]["ekuitas"], lv["ekuitas"])                      # pemanasan: W = 1 -> identik
            for y in ("fomo", "dexscreener", "berita", "binance_ekstra", "candle_harian", "ledger_bot"):   # sumber yang tidak disitasi
                self.assertEqual(ev["dunia"][f"tanpa_sumber:{y}"]["ekuitas"], lv["ekuitas"], y)
            self.assertEqual(ev["galat"], [])
        self.assertEqual(books["v2"]["saldo"], st["dunia"]["penuh"]["buku"]["saldo"])
        self.assertTrue(any(lv["isi"] for lv in hidup))                                           # buku hidup benar-benar bertransaksi
        beda = lambda n: any(ev["dunia"][n]["ekuitas"] != lv["ekuitas"] for (_, ev), lv in zip(hasil, hidup))   # noqa: E731
        self.assertTrue(beda("tanpa_sumber:binance"))                                             # semua faktor = binance: tanpa kuorum
        self.assertTrue(beda("tanpa_sumber:rugcheck"))                                            # WIF tidak diveto keras lagi
        self.assertTrue(beda("tanpa:a"))                                                          # ambang n-1 + suara a hilang
        h12 = [r for _, ev in hasil for r in ev["nilai"] if r["h"] == 12]
        self.assertEqual({r["siklus"] for r in h12}, {T0 + i * 300 for i in range(18)})          # 1 jam sesudahnya, siklus tepat
        self.assertEqual(len([r for _, ev in hasil for r in ev["nilai"] if r["h"] == 1]), sum(len(ev["nilai"]) for _, ev in hasil) - len(h12))
        self.assertEqual({r["agent"] for r in h12}, {"a", "b", "c"})
        self.assertNotIn("c", {r["agent"] for r in h12 if r["siklus"] == T0 + 3 * 300})           # c gagal di siklus itu: tidak dinilai
        self.assertEqual([e["siklus"] for _, e in hasil if e["bobot"]["diperbarui"]], [T0, T0 + 5 * 300, T0 + 17 * 300, T0 + 29 * 300])
        self.assertTrue(all(set(e["rapor"]) <= {"a", "b", "c"} for _, e in hasil if e["bobot"]["diperbarui"]))
        self.assertTrue(all("rapor" not in e for _, e in hasil if not e["bobot"]["diperbarui"]))  # rapor hanya tiap jam

    def test_the_daily_loss_brake_is_mirrored_in_every_shadow_world(self):
        hari = time.strftime("%Y-%m-%d", time.gmtime(T0))
        books = {"_v2_state": {"hari": hari, "ekuitas_awal_hari": 10_500.0}, "v2": meja.buku_baru()}       # -4,8 % sejak 00:00 UTC (SK-M10)
        _, st, hasil = jalankan(4, books=books)
        for rek, ev in hasil:
            lv = next(r for r in rek if r["agent"] == "v2")
            self.assertIn("daily loss brake", lv["dasar"])
            self.assertTrue(ev["setia"], ev["beda"])
            self.assertTrue(all(x["rem"] and x["slot"] == 0 for x in ev["dunia"].values()), ev["dunia"])
        self.assertTrue(any(lv["target"] for lv in (next(r for r in rek if r["agent"] == "v2") for rek, _ in hasil)))   # ada yang akan dibuka tanpa rem

    def test_a_gap_or_a_mismatch_resyncs_only_the_full_world_and_is_recorded(self):
        _, st, hasil = jalankan(8, lewati=(4,))
        ev = {e["siklus"]: e for _, e in hasil}
        celah = ev[T0 + 5 * 300]
        self.assertEqual((celah["celah_siklus"], celah.get("sinkron_ulang"), celah["setia"]), (1, True, True))
        self.assertEqual(st["dunia"]["penuh"]["mulai"], T0 + 5 * 300)                             # SK-M40: dunia penuh disinkron ulang
        self.assertEqual(st["dunia"]["tanpa:a"]["mulai"], T0)                                     # dunia ablasi tidak
        self.assertEqual(len([e for e in ev.values() if e.get("sinkron_ulang")]), 2)              # awal + sesudah celah

        def rusak(i, rek):
            if i != 3:
                return rek
            return [({**r, "ekuitas": r["ekuitas"] + 5.0} if r["agent"] == "v2" else r) for r in rek]
        _, st, hasil = jalankan(6, ubah_rek=rusak)
        ev = [e for _, e in hasil]
        self.assertEqual((ev[3]["setia"], ev[3]["beda"]), (False, ["ekuitas"]))
        self.assertTrue(ev[4].get("sinkron_ulang"))
        self.assertTrue(ev[4]["setia"] and ev[5]["setia"])
        self.assertEqual([x[1] for x in st["setia"]], [1, 1, 1, 0, 1, 1])


class LoopTests(unittest.TestCase):
    """Gerbang: `x402_sinyal.v2_siklus` + `f4_gabung` dengan model + Binance dipalsukan (tanpa jaringan)."""

    def setUp(self):
        import x402_sinyal as xs
        self.xs = xs
        self.t0 = (int(time.time()) // 300 + 1) * 300
        self.simpan = []
        self.gate = types.SimpleNamespace(data_tunggu=lambda t0, sampai: SNAP, log=lambda m: None, eval_simpan=self.simpan.append,
                                          luar=types.SimpleNamespace(agents=lambda: [], bukti=None, minta=None))

    def _siklus(self, mode, books, selesai=lambda h: "f4" in h):
        hasil = {}
        env = {k: v for k, v in os.environ.items() if k != "FABIUS_F4"} | ({"FABIUS_F4": mode} if mode is not None else {})
        with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(self.xs.an, "call_model", lambda ag, s, u, timeout=0: jawab(0)(ag, s, u)), \
                mock.patch.object(self.xs.an, "muat_kursi_builder", lambda: []), mock.patch.object(meja, "_get_json", get_harga(1)):
            self.xs.v2_siklus(self.gate, books, {}, FakePasar(), self.t0, AGENTS, hasil)
            batas = time.time() + 20
            while mode == "bayangan" and not selesai(hasil) and time.time() < batas:
                time.sleep(0.05)
        return hasil

    def test_the_f4_switch_off_has_zero_effect_and_shadow_mode_leaves_every_live_decision_identical(self):
        mati, bayangan, hidup = (self._siklus(m, {}) for m in (None, "bayangan", "hidup"))
        for h in (mati, hidup):
            time.sleep(0.3)
            self.assertNotIn("f4", h)                                                             # SK-M41: "hidup" bukan mode; = mati
        self.assertIn("f4", bayangan)
        for k in ("rek", "harga", "books", "ring"):                                              # keputusan, harga, buku, ringkasan hidup identik
            self.assertEqual(meja.canon(mati[k]), meja.canon(bayangan[k]), k)
        self.assertEqual(meja.root_of([r["hash"] for r in mati["rek"]]), meja.root_of([r["hash"] for r in bayangan["rek"]]))
        self.assertNotIn("_f4", bayangan["books"])                                                # state F4 tidak ikut buku v2
        books = {}
        self.xs.f4_gabung(self.gate, books, {**bayangan, "_digabung": False})                     # v2 siklus itu tidak masuk buku hidup
        self.assertEqual((books, self.simpan), ({}, []))
        self.xs.f4_gabung(self.gate, books, {**bayangan, "_digabung": True})
        self.assertEqual(books["_f4"]["terakhir"], self.t0)
        self.assertEqual(len(self.simpan), 1)
        self.assertTrue(self.simpan[0]["setia"])
        self.assertEqual(self.simpan[0]["siklus"], self.t0)
        self.assertEqual(me.mode(""), "mati")
        self.assertEqual(me.mode("LIVE"), "mati")
        self.assertEqual(me.mode(" Bayangan "), "bayangan")

    def test_a_failing_shadow_never_reaches_the_live_cycle(self):
        with mock.patch.object(me, "siklus_bayangan", side_effect=RuntimeError("boom")):
            log = []
            self.gate.log = log.append
            h = self._siklus("bayangan", {}, selesai=lambda h: any(m.startswith("f4 bayangan") for m in log))
        self.assertIn("rek", h)
        self.assertNotIn("f4", h)
        self.assertTrue(any(m.startswith("f4 bayangan gagal: RuntimeError") for m in log), log)  # SK-M39


class ArchiveCliTests(unittest.TestCase):
    """Siklus hidup asli + bayangan -> `Gate.meja_simpan` + `Gate.eval_simpan` -> server HTTP gerbang asli -> `meja_eval rapor` (gerbang + berkas)."""

    def setUp(self):
        import x402_sinyal as xs
        self.tmp = tempfile.mkdtemp()
        old, os.environ["ANALIS_DIR"] = os.environ.get("ANALIS_DIR"), os.path.join(self.tmp, "analis")
        self.addCleanup(lambda: os.environ.pop("ANALIS_DIR") if old is None else os.environ.update(ANALIS_DIR=old))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.g = xs.Gate(xs.Data(ROOT), "0xk", "https://g", "https://w", log=lambda m: None, now=lambda: T0 + 20 * 300 + xs.TUNDA_PUBLIK_S)
        books, ring, st = {}, {}, None
        for i in range(20):
            t0 = T0 + i * 300
            pra = me.pra_siklus(books)
            rek, harga = meja2.siklus2(t0, AGENTS, books, ring, jawab(i), SNAP, FakePasar(), get=get_harga(i), log=lambda m: None)
            st, ev = me.siklus_bayangan(st, pra, rek, harga, SNAP, FakePasar(), t0)
            self.g.meja_simpan(rek, {"siklus": t0, "daun": [r["hash"] for r in rek], "harga": {}, "harga_v2": harga, "root": meja.root_of([r["hash"] for r in rek]),
                                     "status": "dikomit", "n": len(rek)}, books, ring)
            self.g.eval_simpan(ev)
            self.g.data_simpan({"t": t0, "sha": f"0x{i:064x}", "durasi_s": 12.0, "kesehatan": {"binance": {"status": "ok", "cakupan": 1.0},
                                                                                       "fomo": {"status": "galat", "cakupan": 0.5 if i % 2 else 1.0}}})
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), xs.make_handler(self.g))
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.date = time.strftime("%Y-%m-%d", time.gmtime(T0))

    def _cli(self, *argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = me.main(list(argv))
        return code, buf.getvalue()

    def test_the_archive_serves_hashed_agent_and_evaluation_records_and_the_cli_prints_the_daily_tables(self):
        days = me.muat_arsip(self.date, self.date, self.url)
        a = days[0]
        self.assertEqual(len(a["records"]), 20)
        self.assertEqual(len(a["agent_records"]), 60)
        for r in a["agent_records"]:
            self.assertEqual(r["hash"], meja.sha({k: v for k, v in r.items() if k != "hash"}))     # rekaman agent apa adanya (bisa dibuktikan)
        self.assertEqual(len(a["evaluation"]), 20)
        self.assertTrue(all(e["setia"] for e in a["evaluation"]))
        code, teks = self._cli("rapor", "--dari", self.date, "--sampai", self.date, "--gerbang", self.url)
        self.assertEqual(code, 0)
        for kata in ("AGENT", "KALIBRASI 1j", "SUMBER", "ABLASI", "SETIA 20/20", "tanpa_sumber:fomo", "tanpa:a"):
            self.assertIn(kata, teks)
        lp = me.laporan(days)
        d = lp["hari"][self.date]
        self.assertEqual((d["agent"]["a"]["sah"], d["agent"]["c"]["sah"], d["agent"]["c"]["siklus"]), (20, 15, 20))
        self.assertEqual(d["agent"]["a"]["metrik"]["12"]["n"], 8)                                 # siklus 0-7 dinilai 1 jam kemudian
        self.assertEqual(d["sumber"]["binance"]["disitasi"], d["sumber"]["binance"]["dari"])
        self.assertEqual((d["sumber"]["fomo"]["cakupan"], d["sumber"]["fomo"]["snapshot"], d["sumber"]["binance"]["cakupan"]), (0.75, 20, 1.0))   # kesehatan F1 per hari
        self.assertEqual(len(a["data_health"]), 20)
        self.assertEqual(d["dunia"]["penuh"]["selisih_pp_vs_fabius"], 0.0)
        berkas = os.path.join(self.tmp, "arsip.json")
        with open(berkas, "w", encoding="utf-8") as f:
            json.dump({"days": days}, f)
        self.assertEqual(self._cli("rapor", "--berkas", berkas), (0, teks))                     # luring = lewat gerbang, karakter demi karakter
        code, js = self._cli("rapor", "--berkas", berkas, "--json")
        self.assertEqual(json.loads(js)["hari"][self.date]["setia"], 20)

    def test_without_f4_records_the_report_recomputes_values_from_daily_candles_with_the_same_functions(self):
        days = me.muat_arsip(self.date, self.date, self.url)
        tercatat = me.laporan(days)
        tanpa = [{**d, "evaluation": []} for d in days]
        self.assertTrue(me.laporan(tanpa)["asal_nilai"].startswith("tidak ada"))
        ulang = me.laporan(tanpa, pasar_pada=lambda t: FakePasar())
        self.assertEqual(ulang["asal_nilai"], "dihitung ulang dari arsip + candle harian")
        for s in ("a", "b", "c"):
            self.assertEqual(ulang["hari"][self.date]["agent"][s]["metrik"], tercatat["hari"][self.date]["agent"][s]["metrik"], s)

    def test_the_public_archive_hides_agent_and_evaluation_records_younger_than_24h(self):
        self.g.now = lambda: T0 + 10 * 300 + 86_400                                              # siklus 11-19 < 24 jam
        code, a = self.g.meja_archive(self.date, live=False)
        self.assertEqual(code, 200)
        self.assertEqual({r["siklus"] for r in a["agent_records"]} | {e["siklus"] for e in a["evaluation"]}, {T0 + i * 300 for i in range(11)})
        self.assertEqual(len(self.g.meja_archive(self.date, live=True)[1]["evaluation"]), 20)


class GovernanceTests(unittest.TestCase):
    KR = {"metrik": "selisih_pp_tanpa_sumber", "minimal_siklus": 288, "lulus_bila": "dunia tanpa fomo unggul >= 0,25 pp"}

    def _live(self):
        with open(os.path.join(ROOT, "config", "agents.json"), "rb") as f:
            cfg = f.read()
        return cfg, meja.sha(meja2.PARAMS2), meja.sha(meja2.PARAMS_KURSI), meja.sha(ms.PARAMS_SLOT), meja2.SYSTEM2, meja.sha(meja.PARAMS)

    def test_proposals_pass_only_through_a_shadow_with_prewritten_criteria_and_never_touch_live_config(self):
        sebelum = self._live()
        with self.assertRaisesRegex(ValueError, "SK-M13"):
            me.usulan_baru("fitur", "semua", {"buang_sumber": "fomo"}, "x", None, "evaluator-kode", T0)
        with self.assertRaisesRegex(ValueError, "minimal 288"):
            me.usulan_baru("fitur", "semua", {"buang_sumber": "fomo"}, "x", {**self.KR, "minimal_siklus": 100}, "evaluator-kode", T0)
        u = me.usulan_baru("fitur", "semua", {"buang_sumber": "fomo"}, "x", self.KR, "evaluator-kode", T0)
        self.assertEqual(u["status"], "usulan")
        for ke in ("lulus", "siap_kunci", "hidup", "aktif"):
            with self.assertRaisesRegex(ValueError, f"SK-M13: usulan -> {ke} tidak diizinkan"):
                me.ubah_status(u, ke, T0)                                                         # hanya lewat bayangan
        palsu = copy.deepcopy(u)
        palsu["kriteria_lulus"]["lulus_bila"] = "selalu lulus"
        with self.assertRaisesRegex(ValueError, "sha beda"):
            me.ubah_status(palsu, "bayangan", T0)                                                 # kriteria tidak bisa ditulis ulang sesudahnya
        b = me.ubah_status(u, "bayangan", T0, eq_mulai={"fabius": 10_000.0, "tanpa_sumber:fomo": 10_000.0})
        with self.assertRaisesRegex(ValueError, "baru 0 siklus"):
            me.ubah_status(b, "lulus", T0)
        b["bayangan"]["siklus"] = 288
        h = me.nilai_usulan(b, {"fabius": 10_010.0, "tanpa_sumber:fomo": 10_040.0})
        self.assertEqual((h["lulus"], h["selisih_pp"]), (True, 0.3))                             # (0,4 % - 0,1 %) >= 0,25 pp
        self.assertFalse(me.nilai_usulan({**b, "bayangan": {**b["bayangan"], "tidak_setia": 1}}, {"fabius": 10_010.0, "tanpa_sumber:fomo": 10_040.0})["lulus"])
        lulus = me.ubah_status(b, "lulus", T0 + 288 * 300, hasil=h)
        with self.assertRaisesRegex(ValueError, "kata builder"):
            me.ubah_status(lulus, "siap_kunci", T0, kata_builder="", sha_kunci="0x" + "1" * 64)
        siap = me.ubah_status(lulus, "siap_kunci", T0, kata_builder="Gas", sha_kunci="0x" + "1" * 64)
        self.assertEqual([x[2] for x in siap["riwayat"]], ["usulan", "bayangan", "lulus", "siap_kunci"])
        with self.assertRaisesRegex(ValueError, "SK-M13: siap_kunci -> hidup tidak diizinkan"):
            me.ubah_status(siap, "hidup", T0)                                                     # tidak ada jalur ke konfigurasi hidup
        p = me.usulan_baru("prompt", "agent:qwen", {"tambah_rapor": True}, "x", {**self.KR, "metrik": "ic_1j"}, "evaluator-kode", T0)
        with self.assertRaisesRegex(ValueError, "izin biaya"):
            me.ubah_status(p, "bayangan", T0)                                                     # bayangan prompt = panggilan model kedua
        self.assertEqual(me.ubah_status(p, "bayangan", T0, izin_biaya="builder 7 Okt")["status"], "bayangan")
        us = me.evaluator_aturan({"qwen": {"n_ic": 200, "ic": -0.05}, "glm": {"n_ic": 200, "ic": 0.1}, "baru": {"n_ic": 10, "ic": -0.5}},
                                 {"fomo": 0.8, "berita": 0.1, "rugcheck": None}, True, [], T0)
        self.assertEqual([(x["jenis"], x["sasaran"], x["isi"]) for x in us],
                         [("prompt", "agent:qwen", {"tambah_rapor": True}), ("fitur", "semua", {"buang_sumber": "fomo"})])
        self.assertEqual(me.evaluator_aturan({"qwen": {"n_ic": 200, "ic": -0.05}}, {"fomo": 0.8}, True, us, T0), [])   # tidak ganda
        self.assertEqual(len(me.evaluator_aturan({}, {"fomo": 0.8}, False, [], T0)), 0)            # dunia penuh tidak SETIA: tidak ada usulan sumber
        self.assertEqual(self._live(), sebelum)                                                   # konfigurasi hidup tidak berubah sebit pun

    def test_the_daily_evaluator_in_the_shadow_writes_proposals_and_starts_none_that_costs_or_goes_live(self):
        sebelum = self._live()
        P = copy.deepcopy(me.PARAMS_F4)
        P["usulan"].update(n_min=1)
        days = me.contoh_arsip(hari=1, siklus=30, t_awal=1_791_540_000 + 13 * 3600 - 300 * 12, P=P)   # 22:00Z -> 00:25Z
        us = [u for d in days for e in d["evaluation"] for u in e["usulan"]]
        self.assertEqual([e["siklus"] % 86_400 for d in days for e in d["evaluation"] if e["usulan"]], [0])   # siklus pertama hari UTC baru
        self.assertIn(("prompt", "agent:balik", "usulan"), [(u["jenis"], u["sasaran"], u["status"]) for u in us])   # IC -1: lampirkan rapor
        self.assertNotIn("agent:tajam", [u["sasaran"] for u in us])
        self.assertTrue(all(u["status"] == "usulan" for u in us if u["jenis"] == "prompt"))      # tanpa izin biaya: tidak dibayangkan
        self.assertEqual(self._live(), sebelum)

    def test_an_llm_proposal_that_targets_live_settings_is_rejected_and_recorded(self):
        teks = "here: " + json.dumps({"usulan": [
            {"jenis": "rumus", "sasaran": "semua", "isi": {"PARAMS2": {"hysteresis_poin": 0}}, "kriteria_lulus": self.KR},
            {"jenis": "fitur", "sasaran": "semua", "isi": {"aktifkan_bobot_hidup": True}, "kriteria_lulus": self.KR},
            {"jenis": "fitur", "sasaran": "semua", "isi": {"buang_sumber": "fomo"}},
            {"jenis": "prompt", "sasaran": "agent:glm", "isi": {"tambah_teks": "Weigh funding before trend."}, "alasan": "IC < 0",
             "kriteria_lulus": {**self.KR, "metrik": "ic_1j"}}]})
        sah, tolak = me.parse_usulan_llm(teks, T0)
        self.assertEqual([(u["jenis"], u["oleh"], u["status"]) for u in sah], [("prompt", "evaluator-llm", "usulan")])
        self.assertEqual(len(tolak), 3)
        self.assertIn("SK-M38", tolak[0]["galat"])                                                # jenis rumus = perubahan hidup
        self.assertIn("SK-M38", tolak[1]["galat"])                                                # isi di luar daftar
        self.assertIn("SK-M13", tolak[2]["galat"])                                                # tanpa kriteria tertulis
        self.assertEqual(me.parse_usulan_llm("no json", T0), ([], [{"galat": "tanpa JSON"}]))

    def test_report_cards_are_text_for_the_shadow_and_their_effect_is_measured_before_and_after(self):
        rows = [{"siklus": 300 * i, "k": 0.7, "hit": i % 2, "acak": 0.2, "ic": 0.05 if i < 288 else 0.2, "bot": "B1-TREND", "r_pilihan": 0.0,
                 "terbaik": "B5-CORE-RWA", "r_terbaik": 0.001 * (i == 5)} for i in range(576)]
        m = me.ringkas(rows[:288])
        teks = me.rapor_teks("qwen", m)
        self.assertTrue(teks.startswith("Your report card (qwen), last 24h at the 1h horizon, 288 cycles: rank IC"), teks)
        self.assertIn("Biggest miss", teks)
        self.assertLessEqual(len(teks), me.PARAMS_F4["rapor"]["maks_karakter"])
        self.assertEqual(me.prompt_dengan_rapor("P", teks), "P\n\n" + teks)
        e = me.efek_rapor(rows, 288 * 300)
        self.assertEqual((e["cukup"], e["selisih_ic"], e["sebelum"]["n_ic"], e["sesudah"]["n_ic"]), (True, 0.15, 288, 288))
        self.assertFalse(me.efek_rapor(rows[:400], 288 * 300)["cukup"])                          # sesudah < 288 siklus: belum bisa dinilai


class LockTests(unittest.TestCase):
    def test_the_f4_formula_is_pre_registered_by_hash_and_drift_or_overwrite_is_refused(self):
        s = me.status()
        self.assertEqual((s["state"], s["sha_berkas"]), ("USULAN", me.params_sha()))              # berkas usulan di repo = rumus di kode
        with open(me.USULAN_FILE, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["params"], me.PARAMS_F4)
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        us, lk = os.path.join(tmp, "u.json"), os.path.join(tmp, "k.json")
        kw = {"lock_path": lk, "usulan_path": us}
        self.assertEqual(me.status(**kw)["state"], "BELUM_DIUSULKAN")
        me.tulis_usulan("usulan P156", "2026-10-07T00:00:00Z", path=us, lock_path=lk)
        self.assertEqual(me.status(**kw)["state"], "USULAN")
        P2 = copy.deepcopy(me.PARAMS_F4)
        P2["bobot"]["kappa"] = 6.0
        self.assertEqual(me.status(P2, **kw)["state"], "MENYIMPANG")                              # angka digeser sesudah usulan = terlihat
        with self.assertRaises(ValueError):
            me.tulis_kunci("Gas", P=P2, path=lk, usulan_path=us)                                  # yang dikunci harus yang dipra-registrasi
        with self.assertRaises(ValueError):
            me.tulis_kunci("", path=lk, usulan_path=us)
        me.tulis_kunci("builder: Gas", "2026-10-08T00:00:00Z", path=lk, usulan_path=us)
        self.assertEqual(me.status(**kw)["state"], "TERKUNCI")
        with self.assertRaises(FileExistsError):
            me.tulis_kunci("lagi", path=lk, usulan_path=us)
        with self.assertRaises(FileExistsError):
            me.tulis_usulan("rumus baru", path=us, lock_path=lk)                                  # rumus baru = keputusan + kunci baru
        with open(lk, "w", encoding="utf-8") as f:
            f.write("{}")
        self.assertEqual(me.status(**kw)["state"], "RUSAK")


class ContohTests(unittest.TestCase):
    def test_the_synthetic_archive_is_deterministic_and_the_offline_report_prints_three_days(self):
        a = me.contoh_arsip(hari=1, siklus=14)
        self.assertEqual(meja.canon(a), meja.canon(me.contoh_arsip(hari=1, siklus=14)))         # model palsu dipanggil dari utas: tetap sama
        days = me.contoh_arsip(hari=3, siklus=16)
        self.assertEqual(len(days), 3)
        self.assertTrue(all(e["setia"] for d in days for e in d["evaluation"]))
        lp = me.laporan(days)
        self.assertEqual(len(lp["hari"]), 3)
        for d in lp["hari"].values():
            self.assertEqual((d["agent"]["tajam"]["metrik"]["12"]["ic"], d["agent"]["balik"]["metrik"]["12"]["ic"]), (1.0, -1.0))
            self.assertEqual(d["agent"]["tajam"]["metrik"]["12"]["hit"], 1.0)
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "f4.json")
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(me.main(["contoh", "--keluar", path, "--hari", "3", "--siklus", "16"]), 0)
            self.assertEqual(me.main(["rapor", "--berkas", path]), 0)
            self.assertEqual(me.main(["usulan", "--berkas", path]), 0)
        teks = buf.getvalue()
        self.assertEqual(teks.count("\n=== "), 3)
        self.assertIn("Tidak ada yang hidup disentuh", teks)


if __name__ == "__main__":
    unittest.main()

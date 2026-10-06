"""P154/P155 (F-D110 diubah F-D112): meja v2 - AI memilih bot + instrumen dalam format baku; rumus terkunci memilih bot dominan + instrumen;
ARAH dihitung aturan bot terkunci (engine.bots) pada candle harian, bukan oleh AI. Binance dan model dipalsukan."""
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, ROOT)

import meja                                                         # noqa: E402
import meja2                                                        # noqa: E402
from engine.series import Series                                    # noqa: E402

DAY = 86_400_000
NOW_MS = 1_791_200_100_000
UNI = ["BTCUSDT", "SOLUSDT", "NEARUSDT", "WIFUSDT", "PAXGUSDT", "NEWUSDT"]
FIT = ["r_1j", "r_4j", "breadth_naik_1j", "rug_bahaya"]


def seri(naik: bool, n: int = 100) -> Series:
    t0 = NOW_MS - (n + 1) * DAY
    return Series.from_rows([(t0 + i * DAY, c, c * 1.01, c * 0.99, c, 1e6) for i in range(n) for c in [(100 + i) if naik else (200 - i)]])


class FakePasar(meja2.Pasar2):
    def __init__(self):
        super().__init__(get=None, now=lambda: NOW_MS / 1000)
        self.s = {"SOLUSDT": seri(True), "NEARUSDT": seri(False), "WIFUSDT": seri(True), "BTCUSDT": seri(True), "PAXGUSDT": seri(True),
                  "NEWUSDT": Series.from_rows([(NOW_MS - 3 * DAY + i * DAY, 10, 10.1, 9.9, 10, 2e6) for i in range(2)])}

    def universe(self):
        return list(UNI)

    def tick(self):
        return {a: {"r_24j": 0.01, "volume_24j": 1} for a in UNI}

    def onboard(self):
        return {"NEWUSDT": NOW_MS - 3 * DAY, "SOLUSDT": NOW_MS - 900 * DAY}

    def harian(self, a):
        return self.s[a]


def out(bot="B1-TREND", skor=None, ins=(("SOLUSDT", 80), ("NEARUSDT", 60)), eks=80, faktor=("r_1j",), veto=()):
    skor = skor or {b: (90 if b == bot else 0) for b in meja2.BOTS}
    return json.dumps({"ringkasan": "trend", "bot": bot, "skor_bot": skor, "keyakinan": 70, "eksposur": eks,
                       "instrumen": [{"aset": a, "keyakinan": k, "faktor": ["r_1j"]} for a, k in ins], "veto_aset": list(veto),
                       "faktor": list(faktor), "alasan": "x"})


class FormatTests(unittest.TestCase):
    def test_v2_requires_every_bot_scored_the_top_bot_chosen_and_grounded_factors(self):
        d = meja2.parse2(out(ins=(("SOLUSDT", 80), ("DOGEUSDT", 50))), UNI, FIT)
        self.assertEqual([i["aset"] for i in d["instrumen"]], ["SOLUSDT"])
        self.assertIn({"aset": "DOGEUSDT", "galat": "outside universe"}, d["ditolak"])          # SK-M14
        bad = json.loads(out()); del bad["skor_bot"]["B6-BOUNCE"]
        with self.assertRaises(ValueError):
            meja2.parse2(json.dumps(bad), UNI, FIT)
        with self.assertRaises(ValueError):                                                     # bot bukan skor tertinggi
            meja2.parse2(out(bot="B1-TREND", skor={b: (90 if b == "B2-RS" else 10) for b in meja2.BOTS}), UNI, FIT)
        with self.assertRaises(ValueError):                                                     # faktor karangan semua
            meja2.parse2(out(faktor=("sentimen_bulan",)), UNI, FIT)


class ConsensusTests(unittest.TestCase):
    def test_dominant_bot_instruments_veto_and_hysteresis(self):
        a = meja2.parse2(out(ins=(("SOLUSDT", 80), ("NEARUSDT", 60)), veto=[{"aset": "WIFUSDT", "faktor": "rug_bahaya"}]), UNI, FIT)
        b = meja2.parse2(out(ins=(("SOLUSDT", 70), ("WIFUSDT", 90)), veto=[{"aset": "WIFUSDT", "faktor": "rug_bahaya"}]), UNI, FIT)
        state = {}
        k, why = meja2.konsensus2({"a": a, "b": b}, state, {"fitur_aset": {"NEARUSDT": {"rug_bahaya": True}}})
        self.assertEqual(k["bot"], "B1-TREND")
        self.assertEqual(k["instrumen"], ["SOLUSDT"])                                         # 2 agent; NEAR (0,6) & WIF (0,9) < ambang 1,2 dan 1 agent
        self.assertIn("WIFUSDT", k["veto"])                                                    # veto dari 2 agent
        k3, _ = meja2.konsensus2({"a": a, "b": a}, {}, {"fitur_aset": {"SOLUSDT": {"dex_likuiditas_usd": 20_000.0}, "NEARUSDT": {"rug_bahaya": True}}})
        self.assertEqual(k3["veto"], ["NEARUSDT", "SOLUSDT", "WIFUSDT"])                       # SK-M9: rug_bahaya + likuiditas DEX < 50 rb USD; WIF = veto 2 agent
        k1, why1 = meja2.konsensus2({"a": a}, {"bot": "B5-CORE-RWA", "pegang": 4, "instrumen": [], "eksposur": 0.3}, None)
        self.assertEqual((k1["bot"], k1["eksposur"]), ("B5-CORE-RWA", 0.3))                    # SK-M7: 1 agent sah < kuorum 2 -> tahan
        self.assertIn("quorum not reached", why1)
        c = meja2.parse2(out(bot="B6-BOUNCE", skor={b: (100 if b == "B6-BOUNCE" else 0) for b in meja2.BOTS}), UNI, FIT)
        k2, why2 = meja2.konsensus2({"a": c, "b": c}, state, None)
        self.assertEqual(k2["bot"], "B1-TREND")                                                # unggul tetapi baru dipegang 1 siklus: tahan
        self.assertIn("hysteresis", why2)
        self.assertEqual(k2["instrumen"], ["SOLUSDT"])                                        # instrumen pilihan B6 tidak dipakai untuk B1: tetap yang lama
        d = meja2.parse2(out(bot="B6-BOUNCE", skor={b: (100 if b == "B6-BOUNCE" else 0) for b in meja2.BOTS}, ins=(("NEARUSDT", 90),)), UNI, FIT)
        k3, _ = meja2.konsensus2({"a": d, "b": a, "c": b}, {}, None)
        self.assertEqual((k3["bot"], k3["instrumen"]), ("B1-TREND", ["SOLUSDT"]))             # NEAR dipilih untuk B6, bukan untuk B1
        ins8 = [("SOLUSDT", 90), ("NEARUSDT", 80), ("WIFUSDT", 70), ("BTCUSDT", 60), ("PAXGUSDT", 50), ("NEWUSDT", 40)]
        e = meja2.parse2(out(bot="B2-RS", skor={b: (90 if b == "B2-RS" else 0) for b in meja2.BOTS}, ins=ins8), UNI, FIT)
        self.assertIn({"bot": "B2-RS", "galat": "B2-RS needs >= 8 instruments, got 6"}, e["ditolak"])
        f = meja2.parse2(out(bot="B2-RS", skor={b: (90 if b == "B2-RS" else 0) for b in meja2.BOTS}, ins=ins8[:2]), UNI, FIT)
        k4, why4 = meja2.konsensus2({"e": e, "f": f}, {}, None)
        self.assertEqual(k4["bot"], "B2-RS")
        self.assertEqual(len(k4["instrumen"]), 6)                                             # 2 lolos ambang + 4 skor tertinggi pemilih B2 (semua yang ada)
        self.assertIn("minimum of 8", why4)


class RuleTests(unittest.TestCase):
    def test_direction_comes_from_the_locked_rule_and_unsupported_rules_are_flat_with_a_reason(self):
        p = FakePasar()
        w, why = meja2.arah("B1-TREND", ["SOLUSDT", "NEARUSDT"], p)
        self.assertEqual(set(w), {"SOLUSDT"})                                                  # NEAR turun 60 hari: datar menurut aturan B1
        self.assertIn("NEARUSDT", why)
        self.assertEqual(meja2.arah("B3-CARRY", ["SOLUSDT"], p)[0], {})                        # SK-M15
        self.assertIn("B4 applies only", meja2.arah("B4-LISTING-FADE", ["SOLUSDT"], p)[1]["SOLUSDT"])
        self.assertEqual(set(meja2.arah("B5-CORE-RWA", ["SOLUSDT"], p)[0]), {"BTCUSDT", "PAXGUSDT"})
        f = meja2.fitur_aturan(p, ["SOLUSDT", "NEARUSDT", "NEWUSDT"])
        self.assertEqual(f["SOLUSDT"]["tren_60h"], round(199 / 139 - 1, 4))                  # rumus sama dengan B1: c / c[-60] - 1
        self.assertLess(f["NEARUSDT"]["tren_60h"], 0)
        self.assertEqual((f["NEWUSDT"]["umur_listing_h"], f["NEWUSDT"]["hari_data"]), (3, 2))   # data kurang: tanpa tren, tidak dikarang
        self.assertNotIn("tren_60h", f["NEWUSDT"])
        self.assertIn("tren_60h", meja2.nama_fitur(None))
        tg, _ = meja2.posisi("B1-TREND", ["SOLUSDT", "WIFUSDT"], 0.8, ["WIFUSDT"], p)
        self.assertEqual(tg, {"SOLUSDT": {"w": 0.25, "k": 1.0}})                               # veto dibuang, maks 25 %


class CycleTests(unittest.TestCase):
    def test_a_v2_cycle_records_every_agent_and_the_consensus_with_hashes(self):
        def get(url):
            return [{"symbol": a, "markPrice": "100", "lastFundingRate": "0"} for a in UNI]
        agents = [{"slug": "a", "agent_id": 1, "model": "m"}, {"slug": "b", "agent_id": 2, "model": "m"}, {"slug": "c", "agent_id": 3, "model": "m"}]

        def call(ag, system, user):
            if ag["slug"] == "c":
                raise RuntimeError("429")
            return out(ins=(("SOLUSDT", 80), ("WIFUSDT", 70)))
        books, ring = {}, {}
        snap = {"sha": "0xabc", "fitur_aset": {"SOLUSDT": {"r_1j": 0.01}}, "fitur_bot": {"B1-TREND": {"breadth_naik_1j": 0.9}}}
        rek, harga = meja2.siklus2(1_791_200_100, agents, books, ring, call, snap, FakePasar(), get=get, log=lambda m: None)
        self.assertEqual(harga["SOLUSDT"], 100.0)
        by = {r["agent"]: r for r in rek}
        self.assertEqual((by["v2:a"]["status"], by["v2:c"]["status"]), ("ok", "gagal"))
        self.assertEqual(by["v2"]["bot"], "B1-TREND")
        self.assertEqual(sorted(by["v2"]["target"]), ["SOLUSDT", "WIFUSDT"])
        self.assertEqual(by["v2"]["data_sha"], "0xabc")
        for r in rek:
            self.assertEqual(r["hash"], meja.sha({k: v for k, v in r.items() if k != "hash"}))
        self.assertEqual([(x["aset"], x["bot"], x["arah"]) for x in by["v2"]["slot"]], [("SOLUSDT", "B1-TREND", 1), ("WIFUSDT", "B1-TREND", 1)])
        self.assertEqual({f["alasan"] for f in by["v2"]["isi"]}, {"open"})                       # r4: target aturan -> slot, bukan isi langsung
        self.assertIn("slot", meja2.PARAMS2)
        books["v2"]["saldo"] = books["_v2_state"]["ekuitas_awal_hari"] * 0.96                     # SK-M10: rugi hari ini -4 %
        rek, _ = meja2.siklus2(1_791_200_400, agents, books, ring, call, snap, FakePasar(), get=get, log=lambda m: None)
        self.assertEqual(rek[-1]["slot"], [])                                                    # rem menutup semua slot
        self.assertEqual({f["alasan"] for f in rek[-1]["isi"]}, {"daily loss brake"})
        self.assertEqual(sorted(rek[-1]["target"]), ["SOLUSDT", "WIFUSDT"])                      # target aturan tetap direkam (pembanding r3)
        self.assertIn("daily loss brake", rek[-1]["dasar"])

    def test_r4_prices_every_held_asset_closes_r3_positions_once_and_opens_only_on_a_valid_consensus(self):
        def get(url):                                                                            # OLDUSDT tidak ada di universe, tetap ada di premiumIndex
            return [{"symbol": a, "markPrice": "100", "lastFundingRate": "0"} for a in UNI + ["OLDUSDT"]]
        agents = [{"slug": s, "agent_id": i, "model": "m"} for i, s in enumerate("abc")]
        books = {"v2": meja.buku_baru()}
        books["v2"]["posisi"] = {"OLDUSDT": {"qty": 10.0, "masuk": 90.0}}                         # posisi buku r3 (tanpa metadata slot)
        snap = {"sha": "0xabc", "fitur_aset": {"SOLUSDT": {"r_1j": 0.01}}, "fitur_bot": {"B1-TREND": {"breadth_naik_1j": 0.9}}}
        rek, harga = meja2.siklus2(1_791_200_100, agents, books, {}, lambda ag, s_, u: out(ins=(("SOLUSDT", 80), ("WIFUSDT", 70))), snap,
                                   FakePasar(), get=get, log=lambda m: None)
        v2 = rek[-1] if rek[-1]["agent"] == "v2" else next(r for r in rek if r["agent"] == "v2")
        self.assertEqual(harga["OLDUSDT"], 100.0)
        self.assertEqual([(f["aset"], f["alasan"], f["pnl"]) for f in v2["isi"] if f["alasan"] == "r4 start"], [("OLDUSDT", "r4 start", 100.0)])
        self.assertEqual(sorted(x["aset"] for x in v2["slot"]), ["SOLUSDT", "WIFUSDT"])
        for x in v2["slot"]:
            self.assertLess(x["sl"], x["masuk"])
            self.assertGreater(x["tp"], x["masuk"])
            self.assertAlmostEqual(x["tp"] - x["masuk"], 2 * (x["masuk"] - x["sl"]))             # untung:rugi 2:1
        self.assertEqual(books["v2"]["target"], {x["aset"]: {"w": x["w"], "k": 1.0} for x in v2["slot"]})
        rek, _ = meja2.siklus2(1_791_200_400, agents, books, {}, lambda ag, s_, u: (_ for _ in ()).throw(RuntimeError("429")), snap,
                               FakePasar(), get=get, log=lambda m: None)
        v2 = next(r for r in rek if r["agent"] == "v2")
        self.assertIn("quorum not reached", v2["dasar"])
        self.assertEqual(v2["isi"], [])                                                          # tanpa konsensus sah: tidak membuka, slot tetap
        self.assertEqual(len(v2["slot"]), 2)

        class CandleRusak(FakePasar):                                                            # SK-M27: candle harian / aturan gagal dibaca
            def harian(self, a):
                raise OSError("klines 451")
        rek, _ = meja2.siklus2(1_791_200_700, agents, books, {}, lambda ag, s_, u: out(ins=(("SOLUSDT", 80), ("NEARUSDT", 70))), snap,
                               CandleRusak(), get=get, log=lambda m: None)
        v2 = next(r for r in rek if r["agent"] == "v2")
        self.assertEqual(v2["isi"], [])                                                          # tanpa konsensus sah: tidak membuka, slot tetap
        self.assertEqual(len(v2["slot"]), 2)



class KursiTests(unittest.TestCase):
    """P160 (F-D113): 7 aktif + 3 uji; agent baru uji/antre; konsensus hanya kursi aktif; kursi berubah hanya di evaluasi harian."""

    def test_new_agents_get_trial_seats_then_queue_and_thresholds_scale_with_active_seats(self):
        st = {}
        ev = meja2.kursi_daftar(st, ["a", "b", "c"], 1_791_200_100)
        self.assertEqual({e["ke"] for e in ev}, {"aktif"})                                       # agent awal meja v2
        ev = meja2.kursi_daftar(st, ["a", "b", "c", "d", "e", "f", "g"], 1_791_200_400)
        self.assertEqual([(e["agent"], e["ke"]) for e in ev], [("d", "uji"), ("e", "uji"), ("f", "uji"), ("g", "antre")])   # SK-M19
        st["kursi"]["d"]["status"] = "aktif"                                                      # satu kursi uji kosong
        self.assertEqual(meja2.kursi_daftar(st, ["g"], 1_791_200_700), [{"agent": "g", "dari": "antre", "ke": "uji", "alasan": "kursi uji kosong"}])
        self.assertEqual(meja2.ambang(3), {"kuorum": 2, "min_agent_instrumen": 2, "veto_min_agent": 2, "ambang_instrumen": 1.2})   # = nilai v1
        self.assertEqual(meja2.ambang(7), {"kuorum": 4, "min_agent_instrumen": 3, "veto_min_agent": 3, "ambang_instrumen": 2.8})

    def test_a_deactivated_agent_releases_its_seat_and_the_queue_moves_up(self):
        st = {"kursi": {"a": {"status": "aktif", "sejak": 0}, "m": {"status": "uji", "sejak": 0}, "q": {"status": "uji", "sejak": 0},
                        "g": {"status": "uji", "sejak": 0}, "f": {"status": "antre", "sejak": 1}, "w": {"status": "antre", "sejak": 2}}}
        ev = meja2.kursi_daftar(st, ["a", "m", "q", "f", "w"], 1_791_250_000, keluar=["g", "claude"])
        self.assertEqual([(e["agent"], e["dari"], e["ke"]) for e in ev], [("g", "uji", "keluar"), ("f", "antre", "uji")])   # SK-M23
        self.assertEqual(st["kursi"]["w"]["status"], "antre")                                      # kursi uji penuh lagi: tetap antre
        self.assertEqual(meja2.kursi_daftar(st, ["a", "m", "q", "f", "w"], 1_791_250_300, keluar=["g"]), [])   # tidak diulang
        st["kursi"]["m"]["status"] = "aktif"
        ev = meja2.kursi_daftar(st, ["a", "m", "q", "f", "w", "g"], 1_791_250_600)               # g diaktifkan lagi: masuk seperti agent baru
        self.assertEqual([(e["agent"], e["ke"]) for e in ev], [("g", "uji")])                         # w tetap antre (uji penuh)

    def test_builder_seat_decisions_apply_once_within_the_seat_limits(self):
        st = {"kursi": {f"a{i}": {"status": "aktif", "sejak": 0} for i in range(5)} | {"m": {"status": "uji", "sejak": 0}, "q": {"status": "uji", "sejak": 0},
                                                                                     "w": {"status": "antre", "sejak": 0}, "g": {"status": "keluar", "sejak": 0}}}
        paksa = [{"id": "d-1", "slug": "m", "ke": "aktif", "alasan": "isi slot"}, {"id": "d-2", "slug": "q", "ke": "aktif", "alasan": "isi slot"},
                 {"id": "d-3", "slug": "w", "ke": "aktif", "alasan": "isi slot"}, {"id": "d-4", "slug": "g", "ke": "aktif", "alasan": "x"}]
        ev = meja2.kursi_paksa(st, paksa, 1_791_250_000)
        self.assertEqual([(e["agent"], e["ke"]) for e in ev], [("m", "aktif"), ("q", "aktif"), ("w", "antre"), ("g", "keluar")])   # SK-M24: maks 7 aktif
        self.assertIn("kursi aktif penuh", ev[2]["alasan"])
        self.assertIn("tidak punya kursi", ev[3]["alasan"])
        self.assertEqual(meja2.kursi_paksa(st, paksa, 1_791_250_300), [])                           # sekali saja
        self.assertEqual(meja2.kursi_daftar(st, ["m", "q", "w"], 1_791_250_300), [{"agent": "w", "dari": "antre", "ke": "uji", "alasan": "kursi uji kosong"}])

    def test_daily_evaluation_promotes_swaps_and_demotes_on_measured_history(self):
        w = meja2.PARAMS_KURSI["jendela_siklus"]
        t0 = 1_791_244_800                                                                        # 00:00 UTC
        lama = t0 - (w + 1) * 300

        def hist(sah_rate, ret):
            n_ok = round(w * sah_rate)
            return {"sah": [1] * n_ok + [0] * (w - n_ok), "eq": [10_000.0] * w + [10_000.0 * (1 + ret)]}
        st = {"kursi": {f"a{i}": {"status": "aktif", "sejak": lama} for i in range(7)} | {"u1": {"status": "uji", "sejak": lama},
                                                                                         "u2": {"status": "uji", "sejak": t0 - 300}},
              "riwayat": {f"a{i}": hist(1.0, 0.001 * i) for i in range(7)} | {"u1": hist(0.99, 0.02), "u2": hist(1.0, 0.05)}}
        st["riwayat"]["a0"] = hist(0.5, 0.0)                                                      # SK-M22: sah 50 % -> turun
        ev = meja2.kursi_evaluasi(st, t0)
        moves = {(e["agent"], e["ke"]) for e in ev}
        self.assertIn(("a0", "uji"), moves)
        self.assertIn(("u1", "aktif"), moves)                                                    # kursi aktif kosong sesudah a0 turun
        self.assertNotIn(("u2", "aktif"), moves)                                                 # baru 1 siklus di kursi uji: belum boleh naik
        st2 = {"kursi": {f"a{i}": {"status": "aktif", "sejak": lama} for i in range(7)} | {"u1": {"status": "uji", "sejak": lama}},
               "riwayat": {f"a{i}": hist(1.0, 0.001 * i) for i in range(7)} | {"u1": hist(1.0, 0.004)}}
        self.assertEqual(meja2.kursi_evaluasi(st2, t0), [])                                       # unggul 0,4 pp dari a0 (0 %) < 0,5 pp: tidak tukar
        st2["riwayat"]["u1"] = hist(1.0, 0.02)
        moves = [(e["agent"], e["ke"]) for e in meja2.kursi_evaluasi(st2, t0)]
        self.assertEqual(moves, [("a0", "uji"), ("u1", "aktif")])                                 # tukar dengan aktif terburuk

    def test_seats_change_only_in_the_midnight_cycle(self):
        def get(url):
            return [{"symbol": a, "markPrice": "100", "lastFundingRate": "0"} for a in UNI]
        w = meja2.PARAMS_KURSI["jendela_siklus"]
        lama = 1_791_244_800 - (w + 1) * 300
        agents = [{"slug": s, "agent_id": i, "model": "m"} for i, s in enumerate(["a", "b", "u"], 1)]

        def books():
            hist = {"sah": [1] * w, "eq": [10_000.0] * w + [10_100.0]}
            return {"_v2_kursi": {"kursi": {"a": {"status": "aktif", "sejak": lama}, "b": {"status": "aktif", "sejak": lama}, "u": {"status": "uji", "sejak": lama}},
                                  "riwayat": {"a": dict(hist, eq=[10_000.0] * (w + 1)), "b": dict(hist, eq=[10_000.0] * (w + 1)), "u": hist}}}
        snap = {"sha": "0x1", "fitur_aset": {"SOLUSDT": {"r_1j": 0.01}}, "fitur_bot": {}}
        siang = books()
        rek, _ = meja2.siklus2(1_791_244_800 - 300, agents, siang, {}, lambda ag, sy, us: out(), snap, FakePasar(), get=get, log=lambda m: None)
        self.assertEqual(siang["_v2_kursi"]["kursi"]["u"]["status"], "uji")                    # SK-M21: syarat terpenuhi siang hari -> tunggu
        self.assertNotIn("kursi", {r["agent"] for r in rek})
        malam = books()
        rek, _ = meja2.siklus2(1_791_244_800, agents, malam, {}, lambda ag, sy, us: out(), snap, FakePasar(), get=get, log=lambda m: None)
        self.assertEqual(malam["_v2_kursi"]["kursi"]["u"]["status"], "aktif")                  # 00:00 UTC: naik
        self.assertEqual([e["ke"] for e in {r["agent"]: r for r in rek}["kursi"]["peristiwa"]], ["aktif"])

    def test_trial_seat_votes_are_recorded_but_not_counted_and_seat_changes_are_hashed(self):
        def get(url):
            return [{"symbol": a, "markPrice": "100", "lastFundingRate": "0"} for a in UNI]
        agents = [{"slug": s, "agent_id": i, "model": "m"} for i, s in enumerate(["a", "b", "c", "d"], 1)]
        books = {"_v2_kursi": {"kursi": {"a": {"status": "aktif", "sejak": 0}, "b": {"status": "aktif", "sejak": 0}, "c": {"status": "aktif", "sejak": 0}}}}

        def call(ag, system, user):
            if ag["slug"] == "d":                                                                # agent uji memilih B6 sangat yakin
                return out(bot="B6-BOUNCE", skor={b: (100 if b == "B6-BOUNCE" else -100) for b in meja2.BOTS}, ins=(("SOLUSDT", 100),))
            return out(ins=(("SOLUSDT", 80), ("WIFUSDT", 70)))
        snap = {"sha": "0xabc", "fitur_aset": {"SOLUSDT": {"r_1j": 0.01}}, "fitur_bot": {}}
        rek, _ = meja2.siklus2(1_791_200_100, agents, books, {}, call, snap, FakePasar(), get=get, log=lambda m: None)
        by = {r["agent"]: r for r in rek}
        self.assertEqual(by["v2:d"]["kursi"], "uji")
        self.assertEqual(by["v2:d"]["status"], "ok")                                             # rekamannya tetap ada + di-hash
        self.assertEqual((by["v2"]["bot"], by["v2"]["masuk"]), ("B1-TREND", ["a", "b", "c"]))   # SK-M20: suara uji tidak dihitung
        self.assertEqual(by["kursi"]["peristiwa"], [{"agent": "d", "dari": None, "ke": "uji", "alasan": "agent baru"}])
        self.assertEqual(by["kursi"]["hash"], meja.sha({k: v for k, v in by["kursi"].items() if k != "hash"}))


class LiveBookTests(unittest.TestCase):
    def test_live_book_stats_band_and_per_bot_attribution(self):
        def r(t, bot, eq, fees=(), target=True):
            return {"siklus": t, "bot": bot, "ekuitas": eq, "isi": [{"aset": "X", "dari": 0, "ke": 0.1, "harga": 1, "fee": f} for f in fees],
                    "target": {"X": {"w": 0.1}} if target else {}, "masuk": ["a", "b"], "hash": f"0x{t}"}
        recs = [r(300, "B2-RS", 9_990.0, (10.0,)), r(600, "B2-RS", 9_900.0, (5.0,)), r(900, "B1-TREND", 9_950.0, (2.0,)), r(1200, "B1-TREND", 10_050.0, (), False)]
        h = meja2.buku_hidup(list(reversed(recs)), agen=[{"agent": "v2:a", "status": "ok", "kursi": "aktif", "keputusan": {"bot": "B1-TREND"}}],
                             sik={"root": "0xr", "tx": "0xt", "status": "dikomit"})
        self.assertEqual((h["ekuitas"], h["hasil_pct"], h["fee"], h["transaksi"], h["siklus"], h["siklus_berposisi"]), (10_050.0, 0.5, 17.0, 3, 4, 3))
        self.assertEqual(h["drawdown_maks_pct"], -1.0)                                            # 10.000 -> 9.900
        self.assertEqual([(p["bot"], p["n"]) for p in h["pita"]], [("B2-RS", 2), ("B1-TREND", 2)])
        # pasar siklus i ke bot siklus i-1, fee ke bot siklus i: B2 = (9.900-9.990+5) + (9.950-9.900+2) - fee(10+5) = -48; B1 = (10.050-9.950+0) - 2 = 98
        self.assertEqual({b: x["hasil"] for b, x in h["per_bot"].items()}, {"B2-RS": -48.0, "B1-TREND": 98.0})
        self.assertAlmostEqual(sum(x["hasil"] for x in h["per_bot"].values()), 10_050.0 - 9_990.0 + 0 - 10.0 + (9_990.0 - 10_000.0) + 10.0)
        self.assertEqual(h["pita_keputusan"][0]["siklus"], 1200)                                  # terbaru dulu
        self.assertEqual((h["pipa"]["bot"], h["pipa"]["rumus"], h["pipa"]["tx"], h["pipa"]["agen"][0]["status"]), ("B1-TREND", "r4", "0xt", "ok"))
        self.assertEqual(meja2.buku_hidup([]), {"kosong": True})

    def test_r4_records_attribute_results_per_position_to_the_bot_that_opened_it(self):
        def s(a, bot, pnl, w=0.1):
            return {"aset": a, "bot": bot, "arah": 1, "w": w, "pnl": pnl}
        recs = [{"siklus": 300, "bot": "B2-RS", "ekuitas": 9_990.0, "isi": [{"aset": "X", "dari": 0, "ke": 0.1, "fee": 1.0, "alasan": "open", "bot": "B2-RS", "pnl": 0.0}],
                 "slot": [s("X", "B2-RS", 0.0)], "target": {"X": {"w": 0.2}}, "hash": "0x1"},
                {"siklus": 600, "bot": "B1-TREND", "ekuitas": 10_020.0, "isi": [{"aset": "Y", "dari": 0, "ke": 0.1, "fee": 2.0, "alasan": "open", "bot": "B1-TREND", "pnl": 0.0}],
                 "slot": [s("X", "B2-RS", 25.0), s("Y", "B1-TREND", 0.0)], "target": {}, "hash": "0x2"},
                {"siklus": 900, "bot": "B1-TREND", "ekuitas": 10_040.0, "isi": [{"aset": "X", "dari": 0.1, "ke": 0.0, "fee": 1.5, "alasan": "TP", "bot": "B2-RS", "pnl": 40.0}],
                 "slot": [s("Y", "B1-TREND", 5.0, 0.12)], "target": {}, "hash": "0x3"}]
        h = meja2.buku_hidup(recs)
        # B2: realisasi 40 - fee (1 + 1,5) = 37,5; B1: belum direalisasi 5 - fee 2 = 3; siklus = siklus bot itu memegang slot
        self.assertEqual({b: (x["hasil"], x["siklus"], x["isi"]) for b, x in h["per_bot"].items()}, {"B2-RS": (37.5, 2, 2), "B1-TREND": (3.0, 2, 1)})
        self.assertEqual(h["siklus_berposisi"], 3)
        self.assertEqual(h["pipa"]["target"], {"Y": 0.12})                                      # pipa = slot terbuka, bukan target aturan
        self.assertEqual((h["pipa"]["maks_slot"], [x["aset"] for x in h["pipa"]["slot"]]), (5, ["Y"]))


class GateTests(unittest.TestCase):
    def setUp(self):
        import x402_sinyal as xs
        self.tmp = tempfile.mkdtemp()
        old, os.environ["ANALIS_DIR"] = os.environ.get("ANALIS_DIR"), os.path.join(self.tmp, "analis")
        self.addCleanup(lambda: os.environ.pop("ANALIS_DIR") if old is None else os.environ.update(ANALIS_DIR=old))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.g = xs.Gate(xs.Data(ROOT), "0xk", "https://g", "https://w", log=lambda m: None, now=lambda: 1_791_200_100)

    def test_desk_view_shows_v2_books_with_their_own_prices_and_hides_internal_state(self):
        b2 = meja.buku_baru()
        b2["posisi"] = {"WIFUSDT": {"qty": 10.0, "masuk": 2.0}}
        books = {"konsensus": meja.buku_baru(), "v2": b2, "v2:glm": meja.buku_baru(), "_v2_state": {"bot": "B1-TREND", "pegang": 2}}
        rek = [{"siklus": 1_791_200_100, "agent": "v2", "dasar": "bot dominan B1-TREND (+63.0)", "bot": "B1-TREND", "instrumen": ["WIFUSDT"],
                "target": {"WIFUSDT": {"w": 0.25, "k": 1.0}}, "arah_alasan": {}, "ekuitas": 10_010.0, "hash": "0x1"}]
        sik = {"siklus": 1_791_200_100, "daun": ["0x1"], "harga": {"BTCUSDT": 1.0}, "harga_v2": {"WIFUSDT": 3.0}, "root": "0x1", "status": "dikomit", "n": 1}
        self.g.meja_simpan(rek, sik, books, {})
        v = self.g.meja_view()
        by = {b["agent"]: b for b in v["buku"]}
        self.assertNotIn("_v2_state", by)
        self.assertEqual(by["v2"]["nama"], "Fabius")                                             # F-D115: tanpa label v2
        self.assertNotIn("konsensus", by)                                                       # v1 tidak ditampilkan
        self.assertEqual(by["v2"]["versi"], 2)
        self.assertEqual(by["v2"]["ekuitas"], 10_010.0)                                        # WIF diberi harga dari harga_v2, bukan harga masuk
        self.assertEqual(by["v2"]["keputusan_terakhir"]["instrumen"], ["WIFUSDT"])
        self.assertFalse(by["v2:glm"]["nama"].startswith("v2"))
        self.assertEqual(v["params_v2"], meja2.PARAMS2)

    def test_with_v1_stopped_the_cycle_root_holds_only_v2_records_and_a_late_v2_commits_nothing(self):
        import x402_sinyal as xs
        self.assertFalse(xs.V1_JALAN)                                                            # F-D117: mesin v1 dihentikan
        r = {"siklus": 1_791_200_100, "agent": "v2", "ekuitas": 10_000.0, "hash": "0x" + "ab" * 32}
        books, ring = {}, {}
        rek, sik = xs.rakit_siklus(1_791_200_100, None, {"rek": [r], "harga": {"X": 1.0}, "books": {"v2": meja.buku_baru()}, "ring": {}}, books, ring,
                                   log=lambda m: None)
        self.assertEqual((rek, sik["daun"], sik["n"], sik["harga_v2"]), ([r], [r["hash"]], 1, {"X": 1.0}))
        self.assertEqual(sik["root"], meja.root_of([r["hash"]]))
        self.assertIn("v2", books)
        rek, sik = xs.rakit_siklus(1_791_200_400, None, {}, books, ring, log=lambda m: None)    # v2 terlambat, tanpa v1
        self.assertEqual((rek, sik["daun"], sik["root"], sik["n"]), ([], [], None, 0))
        self.assertTrue(sik["status"].startswith("kosong"))

    def test_live_book_endpoint_reads_every_day_file_and_only_fabius_records(self):
        t0 = 1_791_200_100
        rows = [{"siklus": t0 - 86_400, "agent": "v2", "ekuitas": 9_990.0, "bot": "B2-RS", "hash": "0xa"},
                {"siklus": t0 - 86_400, "agent": "konsensus", "ekuitas": 1.0, "hash": "0xk"},
                {"siklus": t0, "agent": "v2", "ekuitas": 9_980.0, "bot": "B1-TREND", "masuk": ["glm"], "hash": "0xb"},
                {"siklus": t0, "agent": "v2:glm", "status": "ok", "kursi": "aktif", "keputusan": {"bot": "B1-TREND"}, "hash": "0xc"}]
        for r in rows:
            self.g.meja_simpan([r], {"siklus": r["siklus"], "daun": [r["hash"]], "harga": {}, "root": "0xroot", "status": "dikomit", "tx": "0xtx", "n": 1}, {}, {})
        h = self.g.meja_fabius()
        self.assertEqual((h["siklus"], h["ekuitas"], h["mulai"]), (2, 9_980.0, t0 - 86_400))      # dua hari, v1 tidak ikut
        self.assertEqual(h["pipa"]["agen"], [{"slug": "glm", "status": "ok", "kursi": "aktif", "bot": "B1-TREND"}])
        self.assertEqual((h["pipa"]["root"], h["pipa"]["tx"]), ("0xroot", "0xtx"))

    def test_archive_returns_only_fabius_records_and_cycle_prices(self):
        t0 = 1_791_200_100
        for r in ({"siklus": t0, "agent": "v2", "ekuitas": 9_990.0, "target": {"X": {"w": 0.1}}, "hash": "0xa"},
                  {"siklus": t0, "agent": "konsensus", "ekuitas": 1.0, "hash": "0xk"}, {"siklus": t0, "agent": "v2:glm", "hash": "0xg"}):
            self.g.meja_simpan([r], {"siklus": t0, "daun": [r["hash"]], "harga": {"BTCUSDT": 1.0}, "harga_v2": {"XUSDT": 2.0}, "root": "0xr", "status": "dikomit", "n": 1}, {}, {})
        date = time.strftime("%Y-%m-%d", time.gmtime(t0))
        code, a = self.g.meja_archive(date)
        self.assertEqual(code, 200)
        self.assertEqual([r["hash"] for r in a["records"]], ["0xa"])                             # v1 + agent tidak ikut
        self.assertEqual(a["cycles"][0]["prices"], {"XUSDT": 2.0})
        self.assertEqual(a["cycles"][0]["cycle"], t0)
        self.assertNotIn("harga", a["cycles"][0])
        self.assertEqual(self.g.meja_archive("../etc")[0], 400)
        self.assertEqual(self.g.meja_archive("2020-01-01")[0], 404)

    def test_agent_detail_counts_measured_24h_stats_and_lists_history_newest_first(self):
        t0 = 1_791_200_100
        rek = [{"siklus": t0 - 300, "agent": "v2:glm", "status": "ok", "agent_id": 2558, "model": "deepseek", "keputusan": {"bot": "B1-TREND", "ringkasan": "a", "target": {}},
                "isi": [{"aset": "BTCUSDT", "dari": 0.0, "ke": 0.1, "harga": 100.0, "fee": 0.5}], "ekuitas": 9999.5, "hash": "0xa"},
               {"siklus": t0, "agent": "v2:glm", "status": "gagal", "galat": "429", "agent_id": 2558, "model": "deepseek", "ekuitas": 9999.5, "hash": "0xb"}]
        books = {"v2:glm": meja.buku_baru()}
        self.g.meja_simpan(rek, {"siklus": t0, "daun": ["0xa", "0xb"], "harga": {}, "root": "0x1", "status": "dikomit", "n": 2}, books, {})
        code, d = self.g.meja_agent("v2:glm")
        self.assertEqual(code, 200)
        self.assertEqual((d["statistik"]["ok"], d["statistik"]["gagal"], d["statistik"]["isi_24j"], d["statistik"]["bot_pilihan"]), (1, 1, 1, {"B1-TREND": 1}))
        self.assertEqual([r["hash"] for r in d["riwayat"]], ["0xb", "0xa"])                  # terbaru dulu
        self.assertEqual((d["agent_id"], d["buku"]["isi_terakhir"]), (2558, 0))               # rekaman terakhir gagal: tanpa isi
        self.assertEqual(self.g.meja_agent("tidak-ada")[0], 404)
        self.assertEqual(self.g.meja_view()["siklus_12"][-1]["status"], "dikomit")

    def test_a_late_v2_cycle_stays_out_of_the_root_and_leaves_the_v2_books_untouched(self):
        import x402_sinyal as xs
        rek, sik, books, ring = [{"hash": "0x01"}], {"daun": ["0x01"]}, {"v2": {"saldo": 1.0}}, {}
        self.assertFalse(xs.gabung_v2(rek, sik, books, ring, {}))                              # belum selesai: tidak digabung
        self.assertEqual((rek, sik["daun"], books), ([{"hash": "0x01"}], ["0x01"], {"v2": {"saldo": 1.0}}))
        h2 = {"rek": [{"hash": "0x02"}], "harga": {"WIFUSDT": 3.0}, "books": {"v2": {"saldo": 2.0}}, "ring": {"v2:a": "x"}}
        self.assertTrue(xs.gabung_v2(rek, sik, books, ring, h2))
        self.assertEqual((sik["daun"], books["v2"]["saldo"], sik["harga_v2"]), (["0x01", "0x02"], 2.0, {"WIFUSDT": 3.0}))

    def test_v2_waits_for_the_snapshot_of_its_own_cycle_then_falls_back_to_the_last_one(self):
        snap = {"v": 1, "t": 1_791_200_100, "sha": "0xs", "kesehatan": {}}
        threading.Timer(0.2, lambda: self.g.data_simpan(snap)).start()
        self.assertEqual(self.g.data_tunggu(1_791_200_100, time.time() + 5)["sha"], "0xs")
        mulai = time.time()
        self.assertEqual(self.g.data_tunggu(1_791_200_400, time.time() + 0.3)["sha"], "0xs")   # siklus berikut belum ada: snapshot terakhir
        self.assertLess(time.time() - mulai, 2)


if __name__ == "__main__":
    unittest.main()

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
    return Series.from_rows([(t0 + i * DAY, 1, 1, 1, (100 + i) if naik else (200 - i), 1e6) for i in range(n)])


class FakePasar(meja2.Pasar2):
    def __init__(self):
        super().__init__(get=None, now=lambda: NOW_MS / 1000)
        self.s = {"SOLUSDT": seri(True), "NEARUSDT": seri(False), "WIFUSDT": seri(True), "BTCUSDT": seri(True), "PAXGUSDT": seri(True),
                  "NEWUSDT": Series.from_rows([(NOW_MS - 3 * DAY + i * DAY, 1, 1, 1, 10, 2e6) for i in range(2)])}

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
        books["v2"]["saldo"] = books["_v2_state"]["ekuitas_awal_hari"] * 0.96                     # SK-M10: rugi hari ini -4 %
        rek, _ = meja2.siklus2(1_791_200_400, agents, books, ring, call, snap, FakePasar(), get=get, log=lambda m: None)
        self.assertEqual(rek[-1]["target"], {})
        self.assertIn("daily loss brake", rek[-1]["dasar"])



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
        self.assertEqual(by["v2"]["nama"], "Fabius v2 (bot + instruments)")
        self.assertEqual(by["v2"]["versi"], 2)
        self.assertEqual(by["v2"]["ekuitas"], 10_010.0)                                        # WIF diberi harga dari harga_v2, bukan harga masuk
        self.assertEqual(by["v2"]["keputusan_terakhir"]["instrumen"], ["WIFUSDT"])
        self.assertTrue(by["v2:glm"]["nama"].startswith("v2 · "))
        self.assertEqual(v["params_v2"], meja2.PARAMS2)

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

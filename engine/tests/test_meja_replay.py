"""P163: replay buku Fabius dari arsip - setia ke `meja.isi`, kebijakan perputaran hanya mengubah target, fee dipecah per sumber; tes integrasi
ujung ke ujung: siklus v2 asli -> simpan gerbang asli -> `GET /desk/archive/<date>` lewat server HTTP gerbang asli -> `meja_replay` (kriteria
keluar P163 di vault/08-Backlog/01 - Backlog.md)."""
import copy
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, "tools"), ROOT, HERE]

import meja                                                         # noqa: E402
import meja2                                                        # noqa: E402
import meja_replay as mr                                            # noqa: E402
from test_meja2 import UNI, FakePasar, out                          # noqa: E402


def rec(t, bot, target, dasar="dominant bot", instrumen=None, eks=0.8):
    return {"siklus": t, "bot": bot, "dasar": dasar, "eksposur": eks, "instrumen": sorted(target) if instrumen is None else instrumen,
            "target": {a: {"w": w, "k": 1.0} for a, w in target.items()}}


def isi(a, d0, d1, fee=1.0):
    return {"aset": a, "dari": d0, "ke": d1, "harga": 1, "fee": fee}


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.recs = [rec(300, "B1", {"A": 0.20, "B": 0.10}), rec(600, "B1", {"A": 0.17, "B": 0.10}), rec(900, "B1", {"A": 0.20}),
                     rec(1200, "B1", {"A": 0.20, "B": 0.10}), rec(1500, "B2", {"A": -0.10}), rec(1800, "B2", {}, dasar="daily loss brake -3.10%")]
        self.harga = {t: {"A": 100.0 + i, "B": 50.0} for i, t in enumerate(range(300, 2100, 300))}

    def test_r3_replay_matches_a_direct_fill_of_the_same_targets(self):
        b = meja.buku_baru()
        for r in self.recs:
            meja.isi(b, r["target"], self.harga[r["siklus"]])
        x = mr.replay(self.recs, self.harga, mr.r3)
        self.assertAlmostEqual(x["ekuitas"], round(meja.ekuitas(b, self.harga[1800]), 2), places=2)

    def test_policies_trade_less_and_never_invent_positions(self):
        base = mr.replay(self.recs, self.harga, mr.r3)
        dipegang = set()
        for nama, pol in mr.KEBIJAKAN.items():
            x = mr.replay(self.recs, self.harga, pol)
            self.assertLessEqual(x["isi"], base["isi"], nama)
            for r, fills in x["kirim"]:
                for f in fills:
                    self.assertTrue(f["aset"] in r["target"] or f["aset"] in dipegang or abs(f["ke"]) < 1e-9, (nama, f))
                    dipegang.add(f["aset"])
            self.assertTrue(x["kirim"][-1][1] and all(abs(f["ke"]) < 1e-9 for f in x["kirim"][-1][1]), nama)    # rem rugi tetap menutup
        sticky = mr.replay(self.recs, self.harga, mr.lekat_instrumen(3))
        self.assertNotIn("B", {f["aset"] for f in sticky["kirim"][2][1]})                                    # B keluar daftar -> tetap dipegang

    def test_sticky_instruments_never_override_a_rule_that_goes_flat(self):
        recs = [rec(300, "B1", {"A": 0.2, "B": 0.1}), rec(600, "B1", {"A": 0.2}, instrumen=["A", "B"])]                # B masih dipilih, aturan datar
        x = mr.replay(recs, {300: {"A": 100.0, "B": 50.0}, 600: {"A": 100.0, "B": 50.0}}, mr.lekat_instrumen(3))
        self.assertEqual([(f["aset"], f["ke"]) for f in x["kirim"][1][1]], [("B", 0.0)])

    def test_daily_loss_brake_is_recomputed_from_replay_equity(self):
        recs = [rec(t, "B1", {"A": 0.25}) for t in (300, 600, 900)]
        harga = {300: {"A": 100.0}, 600: {"A": 80.0}, 900: {"A": 80.0}}                                     # -20 % x 25 % = -5 % ekuitas
        x = mr.replay(recs, harga, mr.r3)
        self.assertEqual(x["rem_replay"], 2)
        self.assertEqual([f["ke"] for f in x["kirim"][1][1]], [0.0])                                        # siklus 600 ditutup oleh rem
        self.assertEqual(x["kirim"][2][1], [])                                                               # tetap datar sampai hari berganti

    def test_fee_sources_follow_the_p163_exit_criteria_and_add_up(self):
        recs = [dict(rec(300, "B1-TREND", {"A": 0.2}), isi=[isi("A", 0.0, 0.2)]),
                dict(rec(600, "B1-TREND", {"A": 0.2, "C": 0.1}), isi=[isi("C", 0.0, 0.1)]),                      # C masuk daftar
                dict(rec(900, "B1-TREND", {"A": 0.15, "C": 0.1}, eks=0.6), isi=[isi("A", 0.2, 0.15)]),            # eksposur 0,8 -> 0,6
                dict(rec(1200, "B1-TREND", {"A": 0.12, "C": 0.1}, eks=0.6), isi=[isi("A", 0.15, 0.12)]),          # eksposur sama
                dict(rec(1500, "B1-TREND", {"A": -0.1, "C": 0.1}, eks=0.6), isi=[isi("A", 0.12, -0.1)]),          # aturan B1 membalik
                dict(rec(1800, "B2-RS", {"A": 0.1, "C": 0.1}, eks=0.6), isi=[isi("A", -0.1, 0.1)]),               # ganti bot
                dict(rec(2100, "B2-RS", {"A": -0.1, "C": 0.1}, eks=0.6), isi=[isi("A", 0.1, -0.1)]),              # peringkat B2 berbalik
                dict(rec(2400, "B2-RS", {}, dasar="x; daily loss brake -3%", instrumen=["A", "C"], eks=0.6),
                     isi=[isi("A", -0.1, 0.0), isi("C", 0.1, 0.0)])]
        s = mr.sumber_fee(recs)
        self.assertEqual({k: v["isi"] for k, v in s.items()},
                         {"buka awal": 1, "ganti instrumen": 1, "ubah eksposur": 1, "geser bobot (harga/aturan)": 1,
                          "aturan buka/tutup/balik (bot lain)": 1, "ganti bot": 1, "pembalikan peringkat B2": 1, "rem rugi": 2})
        self.assertTrue(set(s) <= set(mr.SUMBER))
        self.assertAlmostEqual(sum(v["fee"] for v in s.values()), 9.0)
        lp = mr.lama_pegang(recs)                                    # A: buka 300 -> balik 1500 (4) -> balik 1800 (1) -> balik 2100 (1) -> tutup 2400 (1); C: 600 -> 2400 (6)
        self.assertEqual((lp["posisi"], lp["median_siklus"]), (5, 1))
        self.assertEqual(lp["maks_n_siklus_pct"], {1: 60.0, 2: 60.0, 6: 100.0, 12: 100.0})
        self.assertAlmostEqual(lp["fee_posisi_maks_2_siklus"], 6.0)


class PasarStore:
    """Candle harian replay = candle `FakePasar` yang dipakai siklus hidup (supaya replay slot bisa SETIA ke buku tercatat)."""
    def __init__(self):
        self._rows = {a: list(zip(x.t, x.o, x.h, x.l, x.c, x.v)) for a, x in FakePasar().s.items()}
        self.mulai = 0

    def rows(self, a):
        return self._rows.get(a, [])


class ArsipHTTP(unittest.TestCase):
    """Rantai produksi tanpa jaringan luar, TERMASUK transisi r3 -> r4 seperti 6 Okt: siklus 0-5 = rekaman r3 (target aturan diisi `meja.isi`),
    siklus 6-17 = `meja2.siklus2` hidup (r4 slot, model + Binance dipalsukan) pada buku + state yang sama -> `gabung_v2` + `Gate.meja_simpan`
    (seperti `meja_loop`) -> server HTTP gerbang (`make_handler`) -> `meja_replay.muat` lewat HTTP -> `meja_replay.laporan`."""
    T0 = 1_791_200_100                                                                                       # 11:35 UTC, 18 siklus tetap di hari yang sama
    R3 = [("B1-TREND", 0.8, {"SOLUSDT": 0.2, "NEARUSDT": 0.1})] * 3 + [
        ("B1-TREND", 0.8, {"SOLUSDT": 0.2, "NEARUSDT": 0.1, "WIFUSDT": 0.1}),                                 # WIF masuk = ganti instrumen
        ("B1-TREND", 0.6, {"SOLUSDT": 0.15, "NEARUSDT": 0.075, "WIFUSDT": 0.075}),                            # eksposur 0,8 -> 0,6
        ("B5-CORE-RWA", 0.7, {"BTCUSDT": 0.2, "PAXGUSDT": 0.1})]                                              # ganti bot

    def setUp(self):
        import x402_sinyal as xs
        self.xs = xs
        self.tmp = tempfile.mkdtemp()
        old, os.environ["ANALIS_DIR"] = os.environ.get("ANALIS_DIR"), os.path.join(self.tmp, "analis")
        self.addCleanup(lambda: os.environ.pop("ANALIS_DIR") if old is None else os.environ.update(ANALIS_DIR=old))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        # P165: jam gerbang sudah lewat TUNDA_PUBLIK_S sesudah siklus terakhir -> arsip publik (tanpa token) memuat semua rekaman tes
        self.g = xs.Gate(xs.Data(ROOT), "0xk", "https://g", "https://w", log=lambda m: None, now=lambda: self.T0 + 18 * 300 + xs.TUNDA_PUBLIK_S)
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), xs.make_handler(self.g))
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.date = time.strftime("%Y-%m-%d", time.gmtime(self.T0))
        self._run_cycles()

    def _run_cycles(self):
        """r4: agent memilih B5 (BTC + PAXG) di siklus 6-11 lalu B1 (SOL, NEAR, WIF); siklus ke-9 v2 terlambat (tidak digabung, tanpa harga v2)."""
        agents = [{"slug": s, "agent_id": i + 1, "model": "m"} for i, s in enumerate("abc")]
        snap = {"sha": "0xabc", "fitur_aset": {"SOLUSDT": {"r_1j": 0.01}}, "fitur_bot": {"B1-TREND": {"breadth_naik_1j": 0.9}}}
        books, ring = {"v2": meja.buku_baru(), "_v2_state": {"hari": self.date, "ekuitas_awal_hari": 10_000.0}}, {}   # state hari dari era r3
        for i in range(18):
            t0 = self.T0 + i * 300

            def get(url, i=i):
                return [{"symbol": a, "markPrice": str(100 + (j + 1) * 0.6 * i * (1 if j % 2 else -1)), "lastFundingRate": "0"} for j, a in enumerate(UNI)]

            def call(ag, system, user, i=i):
                if 6 <= i < 12:
                    return out(bot="B5-CORE-RWA", ins=(("BTCUSDT", 80), ("PAXGUSDT", 70)), eks=70)
                return out(ins=(("SOLUSDT", 80), ("NEARUSDT", 60), ("WIFUSDT", 70)), eks=60)
            rek = [{"v": 1, "siklus": t0, "agent": "konsensus", "ekuitas": 1.0}]                                # rekaman v1 di berkas yang sama
            rek[0]["hash"] = meja.sha(rek[0])
            sik = {"siklus": t0, "daun": [rek[0]["hash"]], "harga": {}, "root": f"0x{i:064x}", "status": "dikomit", "tx": "0xtx"}
            hasil = {}
            if i < len(self.R3):                                                                                # era r3: target aturan langsung diisi
                bot, eks, w = self.R3[i]
                h = meja.harga_isi(get, aset=UNI)
                tg = {a: {"w": x, "k": 1.0} for a, x in w.items()}
                rk = {"v": 2, "siklus": t0, "agent": "v2", "bot": bot, "eksposur": eks, "instrumen": sorted(w), "dasar": f"dominant bot {bot}",
                      "target": tg, "isi": meja.isi(books["v2"], tg, h)}
                rk["ekuitas"] = round(meja.ekuitas(books["v2"], h), 4)
                rk["hash"] = meja.sha(rk)
                books["_v2_state"]["bot"] = bot
                hasil.update(rek=[rk], harga=h, books={}, ring={})
            elif i != 8:
                b2 = copy.deepcopy({k: v for k, v in books.items() if k.startswith(("v2", "_v2"))})
                r2 = {k: v for k, v in ring.items() if k.startswith("v2")}
                rk, harga = meja2.siklus2(t0, agents, b2, r2, call, snap, FakePasar(), get=get, log=lambda m: None)
                hasil.update(rek=rk, harga=harga, books=b2, ring=r2)
            self.xs.gabung_v2(rek, sik, books, ring, hasil)
            sik["n"] = len(sik["daun"])
            self.g.meja_simpan(rek, sik, books, ring)
        self.book = books["v2"]

    def _get(self, path):
        try:
            with urllib.request.urlopen(self.url + path, timeout=30) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())


class ArchiveReplayIntegrationTests(ArsipHTTP):
    def test_archive_route_is_english_and_serves_the_hashed_fabius_records_and_cycle_prices(self):
        code, a = self._get(f"/desk/archive/{self.date}")
        self.assertEqual(code, 200)
        self.assertEqual(sorted(a), ["akses", "cycles", "date", "records"])                                     # publik; tambahan P156 hanya bila FABIUS_F4=bayangan
        self.assertFalse(a["akses"]["live"])
        self.assertEqual(len(a["records"]), 17)                                                              # 18 siklus - 1 terlambat, v1 tidak ikut
        self.assertEqual({r["agent"] for r in a["records"]}, {"v2"})
        for r in a["records"]:
            self.assertEqual(r["hash"], meja.sha({k: v for k, v in r.items() if k != "hash"}))                  # rekaman apa adanya (bukti utuh)
        self.assertEqual(sorted(a["cycles"][0]), ["cycle", "leaves", "prices", "root", "status", "tx"])
        self.assertEqual(len(a["cycles"]), 18)
        self.assertEqual(a["cycles"][8]["prices"], {})                                                        # siklus v2 terlambat: tanpa harga v2
        self.assertEqual(self._get(f"/desk/arsip/{self.date}")[0], 404)                                        # rute lama Indonesia tidak ada
        self.assertEqual(self._get("/desk/archive/2026-02-30"), (400, {"error": "date must be YYYY-MM-DD"}))
        self.assertEqual(self._get("/desk/archive/..%2Fetc")[0], 400)
        self.assertEqual(self._get("/desk/archive/2020-01-01"), (404, {"error": "no archive for 2020-01-01"}))

    def test_replay_over_http_meets_the_p163_exit_criteria_across_the_r3_to_r4_switch(self):
        prev = time.strftime("%Y-%m-%d", time.gmtime(self.T0 - 86_400))
        recs, harga = mr.muat(prev, self.date, self.url)                                                      # hari tanpa arsip (404) dilewati
        lp = mr.laporan(recs, harga, store=PasarStore())
        # (1) fee dipecah per sumber dengan angka dari arsip; jumlah sumber = total fee tercatat = biaya buku Fabius (r3 + r4 satu buku)
        self.assertTrue(set(lp["sumber"]) <= set(mr.SUMBER), lp["sumber"])
        self.assertGreaterEqual(set(lp["sumber"]), {"ganti bot", "ganti instrumen", "ubah eksposur", "r4 start", "buka slot"})
        self.assertAlmostEqual(sum(v["fee"] for v in lp["sumber"].values()), lp["fee_tercatat"], places=4)
        self.assertAlmostEqual(lp["fee_tercatat"], self.book["biaya"], places=4)
        # (2) replay deterministik pada siklus + harga yang sama: r3 SETIA ke ekuitas tercatat era r3, tiap kebijakan melaporkan fee/isi/ekuitas
        self.assertAlmostEqual(lp["replay"]["r3 (sekarang)"]["ekuitas"], lp["ekuitas_tercatat_r3"], places=2)
        self.assertEqual(set(lp["replay"]), set(mr.KEBIJAKAN))
        for nama, x in lp["replay"].items():
            self.assertTrue({"ekuitas", "fee", "isi", "dd_pct", "per_hari_pct"} <= set(x), nama)
        self.assertEqual(set(mr.laporan(recs, harga, kepekaan=True)["replay"]), set(mr.KEBIJAKAN) | set(mr.KEPEKAAN))
        # (4) r4 tercatat vs bayangan r3; replay slot yang dilanjutkan dari buku r3 SETIA ke buku tercatat (yang diuji = yang dijalankan)
        r4 = lp["r4"]
        self.assertEqual(r4["siklus"], 11)                                                                     # 12 siklus r4 - 1 terlambat
        self.assertTrue(r4["setia"], (r4["replay_slot_ekuitas"], r4["ekuitas_tercatat"]))
        self.assertTrue(lp["setia"])
        self.assertAlmostEqual(r4["ekuitas_tercatat"], meja.ekuitas(self.book, harga[max(harga)]), places=3)
        self.assertTrue({"ekuitas", "fee", "isi", "dd_pct", "sejak_r4_pct"} <= set(r4["bayangan_r3"]))


class SlotIntegrationTests(ArsipHTTP):
    """F-D116 di rekaman yang DIHASILKAN meja hidup (dibaca lewat arsip HTTP gerbang asli)."""

    def test_recorded_r4_cycles_obey_the_f_d116_limits(self):
        import meja_slot as ms
        recs, harga = mr.muat(self.date, self.date, self.url)
        r4 = [r for r in recs if "slot" in r]
        alasan_semua = set()
        for r in r4:
            self.assertLessEqual(len(r["slot"]), ms.PARAMS_SLOT["maks_posisi"])
            alasan = {f["alasan"] for f in r["isi"]}
            alasan_semua |= alasan
            self.assertTrue(alasan <= {"open", "SL", "TP", "daily loss brake", "r4 start"} | {f"exit rule {b}" for b in meja2.BOTS}, alasan)
            if alasan - {"open", "r4 start"}:
                self.assertNotIn("open", alasan)                                                                # jeda: siklus yang menutup tidak membuka
            for x in r["slot"]:
                self.assertIn(x["aset"], harga[r["siklus"]])                                                    # aset dipegang selalu diberi harga
                self.assertLessEqual(abs(x["qty"]) * x["masuk"], ms.PARAMS_SLOT["maks_per_posisi"] * 10_000 * 1.1)
                self.assertIn(x["bot"], meja2.BOTS)
        self.assertIn("r4 start", alasan_semua)                                                                # posisi r3 ditutup sekali saat r4 mulai
        self.assertIn("open", alasan_semua)
        bots = {x["bot"] for r in r4 for x in r["slot"]}
        self.assertGreaterEqual(bots, {"B5-CORE-RWA"})
        self.assertEqual(sum(1 for r in r4 for f in r["isi"] if f["alasan"] == "r4 start"), 2)                # BTC + PAXG era r3, sekali saja


if __name__ == "__main__":
    unittest.main()

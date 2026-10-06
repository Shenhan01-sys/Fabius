"""P165: halaman alpha berbayar. Yang bisa DITIRU (isi keputusan, posisi/slot, alasan agent, isi transaksi, pilihan analis bar terbuka) hanya untuk
anggota (login Privy + beli >= 1 sinyal dalam 7 hari, satu pemeriksa `Gate.akses`) atau sesudah TUNDA_PUBLIK_S; yang membuktikan KEJUJURAN
(ekuitas, hasil, fee, kurva, hasil per bot, status agent, root + tx) tetap langsung untuk semua orang."""
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
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "tools"), ROOT]

import meja                                                         # noqa: E402
import x402_sinyal as xs                                            # noqa: E402

T0 = 1_791_200_100


def rekaman():
    slot = [{"aset": "SOLUSDT", "bot": "B1-TREND", "arah": 1, "qty": 10.0, "masuk": 100.0, "harga": 101.0, "w": 0.1, "pnl": 10.0, "margin": 0.04,
             "leverage": 2.5, "sl": 97.0, "tp": 106.0, "atr": 0.03, "t": T0}]
    v2 = {"v": 2, "siklus": T0, "agent": "v2", "bot": "B1-TREND", "nilai_bot": {"B1-TREND": 60.0}, "dasar": "dominant bot B1-TREND (+60.0)",
          "instrumen": ["SOLUSDT"], "target": {"SOLUSDT": {"w": 0.2, "k": 1.0}}, "masuk": ["glm"], "aktif": ["glm"], "slot": slot,
          "isi": [{"aset": "SOLUSDT", "dari": 0.0, "ke": 0.1, "harga": 100.0, "fee": 0.5, "alasan": "open", "bot": "B1-TREND", "pnl": 0.0}],
          "ekuitas": 10_009.5}
    ag = {"v": 2, "siklus": T0, "agent": "v2:glm", "status": "ok", "kursi": "aktif", "ekuitas": 10_000.0,
          "keputusan": {"bot": "B1-TREND", "ringkasan": "trend up on SOL", "target": {"SOLUSDT": {"w": 0.25}}}}
    for r in (v2, ag):
        r["hash"] = meja.sha(r)
    return v2, ag


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        old, os.environ["ANALIS_DIR"] = os.environ.get("ANALIS_DIR"), os.path.join(self.tmp, "analis")
        self.addCleanup(lambda: os.environ.pop("ANALIS_DIR") if old is None else os.environ.update(ANALIS_DIR=old))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.t = T0 + 600
        self.g = xs.Gate(xs.Data(ROOT), "0xk", "https://g", "https://w", log=lambda m: None, now=lambda: self.t)
        self.v2, self.ag = rekaman()
        b = meja.buku_baru()
        b["posisi"] = {"SOLUSDT": {"qty": 10.0, "masuk": 100.0, "arah": 1, "bot": "B1-TREND"}}
        b["target"] = {"SOLUSDT": {"w": 0.1, "k": 1.0}}
        books = {"v2": b, "v2:glm": meja.buku_baru(), "_v2_kursi": {"kursi": {"glm": {"status": "aktif", "sejak": T0}}}}
        sik = {"siklus": T0, "daun": [self.v2["hash"], self.ag["hash"]], "harga": {}, "harga_v2": {"SOLUSDT": 101.0},
               "root": meja.root_of([self.v2["hash"], self.ag["hash"]]), "tx": "0xtx", "status": "dikomit", "n": 2}
        self.g.meja_simpan([self.v2, self.ag], sik, books, {})
        self.date = time.strftime("%Y-%m-%d", time.gmtime(T0))

    def lewat_24_jam(self):
        self.t = T0 + xs.TUNDA_PUBLIK_S + 600
        for k in ("_meja", "_fabius", "_fabius_pub"):
            self.g.__dict__.pop(k, None)


class GateTests(Base):
    def test_public_sees_honesty_numbers_live_but_no_copyable_content_younger_than_the_delay(self):
        pub, full = self.g.meja_view_publik(), self.g.meja_view()
        b_pub = next(b for b in pub["buku"] if b["agent"] == "v2")
        b_full = next(b for b in full["buku"] if b["agent"] == "v2")
        self.assertEqual((b_pub["posisi"], b_pub["target"], b_pub["keputusan_terakhir"], b_pub["n_posisi"]), ({}, {}, None, 1))
        self.assertEqual(b_pub["ekuitas"], b_full["ekuitas"])                                       # kejujuran: ekuitas langsung
        self.assertTrue(b_full["posisi"] and b_full["keputusan_terakhir"])
        self.assertEqual(pub["rekaman"], [])
        self.assertEqual((pub["akses"]["live"], pub["akses"]["isi_sampai"]), (False, self.t - xs.TUNDA_PUBLIK_S))
        code, a = self.g.meja_agent("v2:glm", live=False)
        self.assertEqual((code, a["riwayat"]), (200, []))
        self.assertNotIn("bot_pilihan", a["statistik"])
        self.assertEqual(len(self.g.meja_agent("v2:glm")[1]["riwayat"]), 1)
        self.assertEqual(self.g.meja_archive(self.date, live=False)[1]["records"], [])
        self.assertEqual(len(self.g.meja_archive(self.date)[1]["records"]), 1)

    def test_the_live_book_keeps_curve_stats_and_chain_public_and_hides_bot_slots_and_tape(self):
        full, pub = self.g.meja_fabius(), self.g.meja_fabius_publik()
        for k in ("ekuitas", "hasil_pct", "fee", "transaksi", "seri", "per_bot", "drawdown_maks_pct"):
            self.assertEqual(pub[k], full[k], k)
        p = pub["pipa"]
        self.assertEqual((p["bot"], p["skor_bot"], p["instrumen"], p["target"], p["slot"], p["slot_n"], p["terkunci"]), (None, None, [], {}, None, 1, True))
        self.assertEqual((p["root"], p["tx"], p["status"]), (full["pipa"]["root"], "0xtx", "dikomit"))
        self.assertEqual(p["agen"], [{"slug": "glm", "status": "ok", "kursi": "aktif"}])           # status terlihat, pilihan bot tidak
        self.assertEqual((pub["pita_keputusan"], pub["pita"]), ([], []))
        self.assertEqual(full["pipa"]["slot"][0]["aset"], "SOLUSDT")

    def test_a_proof_younger_than_the_delay_shows_the_commitment_and_opens_after_it(self):
        code, body = self.g.meja_proof(self.v2["hash"], live=False)
        self.assertEqual(code, 402)
        self.assertEqual((body["siklus"], body["terbuka_pada"], body["tx"]), (T0, T0 + xs.TUNDA_PUBLIK_S, "0xtx"))
        self.assertNotIn("rekaman", body)
        self.assertEqual(self.g.meja_proof(self.v2["hash"], live=True)[0], 200)
        self.lewat_24_jam()
        code, body = self.g.meja_proof(self.v2["hash"], live=False)
        self.assertEqual((code, body["rekaman"]["slot"][0]["aset"]), (200, "SOLUSDT"))
        self.assertEqual(len(self.g.meja_archive(self.date, live=False)[1]["records"]), 1)
        self.assertEqual(self.g.meja_fabius_publik()["pita_keputusan"][0]["hash"], self.v2["hash"])

    def test_open_bar_analyst_picks_are_sealed_for_the_public_only(self):
        r = {"agent": "glm", "bot": "B1-TREND", "keyakinan": 70, "reasonHash": "0xr", "alasan": {"bar_close": T0 + 3600}}
        self.assertEqual({k: v for k, v in xs.segel_pilihan(r, T0, False).items() if k in ("bot", "keyakinan", "tersegel", "reasonHash")},
                         {"bot": None, "keyakinan": None, "tersegel": True, "reasonHash": "0xr"})
        self.assertEqual(xs.segel_pilihan(r, T0, True), r)                                        # anggota
        self.assertEqual(xs.segel_pilihan(r, T0 + 7200, False), r)                                # bar sudah tutup


class FakePrivy:
    app_id = "app"

    def __init__(self):
        self.n_user = 0

    def verification_key(self):
        return "key"

    def user(self, sub):
        self.n_user += 1
        return {"sub": sub}


class AksesTests(Base):
    def test_one_access_check_with_a_cache_buyers_within_seven_days_pass(self):
        self.g.privy = FakePrivy()
        with mock.patch.object(xs.pv, "verify_access_token", return_value={"sub": "u1"}), \
                mock.patch.object(xs.pv.Privy, "wallet_addresses", staticmethod(lambda user: ["0xAbC"])):
            self.assertEqual(self.g.akses(None)[0], 401)
            code, a = self.g.akses("Bearer t1")
            self.assertEqual(code, 402)
            self.g.record_buy("B1-TREND", "2026-10-06", "0xabc", "0xbuy", 1000)                       # langsung terbaca: 402 tidak di-cache
            code, a = self.g.akses("Bearer t1")
            self.assertEqual((code, a["dompet"], a["berlaku_sampai"]), (200, "0xabc", self.t + xs.AKSES_HARI * 86400))
            n = self.g.privy.n_user
            self.assertEqual(self.g.akses("Bearer t1")[0], 200)
            self.assertEqual(self.g.privy.n_user, n)                                               # cache 60 s: Privy tidak dipanggil lagi
            self.assertTrue(self.g.live("Bearer t1"))
            self.assertFalse(self.g.live(None))


class HttpTests(Base):
    def setUp(self):
        super().setUp()
        self.g.akses = lambda auth: (200, {"dompet": "0xabc", "berlaku_sampai": T0 + 7 * 86400}) if auth == "Bearer anggota" else (401, {"error": "x"})
        srv = ThreadingHTTPServer(("127.0.0.1", 0), xs.make_handler(self.g))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        self.url = f"http://127.0.0.1:{srv.server_address[1]}"

    def get(self, path, token=None):
        req = urllib.request.Request(self.url + path, headers={"Authorization": f"Bearer {token}"} if token else {})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def test_the_access_route_tells_the_web_who_is_a_member(self):
        self.assertEqual(self.get("/access")[0], 401)
        code, a = self.get("/access", "anggota")
        self.assertEqual((code, a["live"], a["dompet"], a["tunda_s"], a["hari"]), (200, True, "0xabc", xs.TUNDA_PUBLIK_S, xs.AKSES_HARI))

    def test_members_get_live_content_on_every_desk_route_and_the_public_gets_the_delayed_view(self):
        _, pub = self.get("/desk")
        _, mem = self.get("/desk", "anggota")
        self.assertEqual((pub["akses"]["live"], mem["akses"]["live"]), (False, True))
        v2p, v2m = (next(b for b in d["buku"] if b["agent"] == "v2") for d in (pub, mem))
        self.assertEqual((v2p["posisi"], bool(v2m["posisi"])), ({}, True))
        self.assertEqual(self.get("/desk", "palsu")[1]["akses"]["live"], False)                    # token tidak sah = publik
        _, fp = self.get("/desk/fabius")
        _, fm = self.get("/desk/fabius", "anggota")
        self.assertEqual((fp["pipa"]["slot"], fp["pipa"]["slot_n"], fm["pipa"]["slot"][0]["aset"]), (None, 1, "SOLUSDT"))
        self.assertEqual(fp["ekuitas"], fm["ekuitas"])
        self.assertEqual(self.get(f"/desk/proof/{self.v2['hash']}")[0], 402)
        self.assertEqual(self.get(f"/desk/proof/{self.v2['hash']}", "anggota")[0], 200)
        self.assertEqual(self.get("/desk/agent/v2:glm")[1]["riwayat"], [])
        self.assertEqual(len(self.get("/desk/agent/v2:glm", "anggota")[1]["riwayat"]), 1)
        self.assertEqual(self.get(f"/desk/archive/{self.date}")[1]["records"], [])
        self.assertEqual(len(self.get(f"/desk/archive/{self.date}", "anggota")[1]["records"]), 1)


if __name__ == "__main__":
    unittest.main()

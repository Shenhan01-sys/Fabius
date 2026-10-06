"""P166 (F-D121) UJI PENERIMAAN + ALUR BISNIS. Kriteria keluar di `vault/08-Backlog/01 - Backlog.md` (baris P166) dijadikan satu tes per kriteria (nama tes memuat
nomor kriteria), ditambah alur bisnis LINTAS SIKLUS dengan tanda tangan nyata (eth-account): daftar -> kursi uji -> jawaban tercatat + dikomit -> evaluasi 00:00 UTC ->
naik aktif -> suara dihitung; dan jalur gagal: agent mati -> antre -> keluar -> tidak bisa daftar ulang. Binance, model, dan identitas ERC-8004 dipalsukan; waktu
siklus (t0) digeser tanpa menunggu, tenggat jawab memakai jam nyata."""
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

import agen_luar as al                                              # noqa: E402
import meja                                                         # noqa: E402
import meja2                                                        # noqa: E402
from engine import chain                                            # noqa: E402
from .test_agen_luar import (HAVE_ETH, KEY_A, KEY_B, KEY_C, addr, identitas, pulihkan_cek, tanda, tarik, url_tarik)   # noqa: E402
from .test_meja2 import UNI, FakePasar, out                         # noqa: E402

MIDNIGHT = 1_791_244_800            # habis dibagi 86 400: siklus 00:00 UTC (evaluasi kursi)
SNAP = {"sha": "0xabc", "fitur_aset": {"SOLUSDT": {"r_1j": 0.01}}, "fitur_bot": {}}
KEYS = {1: KEY_C, 7: KEY_A, 9: KEY_B, 11: KEY_C}
PETA = {7: (KEY_A, None, "Alpha"), 9: (KEY_B, None, "Beta"), 11: (KEY_C, None, "Gamma")}


def get(url):
    return [{"symbol": a, "markPrice": "100", "lastFundingRate": "0"} for a in UNI]


class Dunia:
    """Meja kecil: tiga agent rumah AKTIF (a, b, c) + agent luar yang terdaftar; `jalan(t0)` = satu siklus2 dengan buku yang dibawa antar siklus."""

    def __init__(self, tmp, klien=(), peta=PETA, rumah_aktif=("a", "b", "c")):
        self.books = {"_v2_kursi": {"kursi": {s: {"status": "aktif", "sejak": 0} for s in rumah_aktif}}}
        self.ring: dict = {}
        self.lx = al.Luar(os.path.join(tmp, "luar.json"), resolve=identitas(peta), status=self.status)
        self.rumah = [{"slug": s, "agent_id": i, "model": "m"} for i, s in enumerate(rumah_aktif, 1)]
        self.berhenti = threading.Event()
        self.jawaban = out(ins=(("SOLUSDT", 80), ("WIFUSDT", 70)))
        self.diminta: dict = {}
        self.klien = [threading.Thread(target=self._klien, args=(a,), daemon=True) for a in klien]
        self.kunci = {a: KEYS[a] for a in klien}

    def status(self, slug):
        kst = self.books.get("_v2_kursi") or {}
        e = (kst.get("kursi") or {}).get(slug)
        sah = ((kst.get("riwayat") or {}).get(slug) or {}).get("sah") or []
        return {"kursi": e["status"] if e else None, "gagal": bool(e and e.get("gagal")), "n": len(sah), "sah_pct": round(100 * sum(sah) / len(sah), 1) if sah else None}

    def daftar(self, aid):
        dl = int(time.time()) + 600
        return self.lx.join({"agent_id": aid, "deadline": dl, "signature": tanda(KEYS[aid], al.pesan_join(aid, dl))})

    def _klien(self, aid):
        """Proses agent luar: tarik -> tandatangani -> jawab, berulang sampai dihentikan."""
        while not self.berhenti.is_set():
            code, req = tarik(self.lx, aid, 1, KEYS[aid])
            if code != 200 or not req.get("siklus") or self.diminta.get(aid) == req["siklus"]:
                continue
            self.diminta[aid] = req["siklus"]
            asha = al.sha_bytes(self.jawaban.encode())
            self.lx.jawab({"agent_id": aid, "siklus": req["siklus"], "answer": self.jawaban,
                           "signature": tanda(KEYS[aid], al.pesan_jawab(aid, req["siklus"], req["prompt_sha"], asha))})

    def mulai(self):
        for aid in self.kunci:
            tarik(self.lx, aid, 0, KEYS[aid])                      # hadir sebelum siklus pertama
        for th in self.klien:
            th.start()

    def tutup(self):
        self.berhenti.set()

    def call(self, ag, system, user):
        if ag.get("luar"):
            return self.lx.minta(ag, system, user, ag["siklus"], ag["validasi"], ag.get("tenggat"))
        return self.jawaban

    def jalan(self, t0):
        rek, _ = meja2.siklus2(t0, self.rumah + self.lx.agents(), self.books, self.ring, self.call, SNAP, FakePasar(), get=get, log=lambda m: None,
                               bukti=self.lx.bukti)
        return {r["agent"]: r for r in rek}


@unittest.skipUnless(HAVE_ETH, "butuh eth-account")
class KriteriaTests(unittest.TestCase):
    """Satu tes per kriteria keluar P166 (vault/08-Backlog/01 - Backlog.md)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_criterion_1_external_page_lists_rules_limits_sha_message_formats_and_roster_with_seat(self):
        d = Dunia(self.tmp)
        d.daftar(7)
        d.books["_v2_kursi"]["kursi"]["x7"] = {"status": "uji", "sejak": 0}
        i = d.lx.info()
        self.assertEqual(i["params"], al.PARAMS_LUAR)
        self.assertEqual(i["params_sha"], al.sha_bytes(json.dumps(al.PARAMS_LUAR, sort_keys=True, separators=(",", ":")).encode()))
        for k in ("join_message", "pull_message", "answer_message", "answer_sha", "prompt_sha"):
            self.assertIn(k, i["sign"])
        self.assertEqual(sorted(i["endpoints"]), ["answer", "join", "pull"])
        self.assertEqual([(a["slug"], a["seat"], a["removed_for_failures"]) for a in i["agents"]], [("x7", "uji", False)])

    def test_criterion_2_join_rules_signer_one_per_agent_and_owner_cap_house_ids_and_removed_agents(self):
        d = Dunia(self.tmp, peta={**PETA, 1: (KEY_C, None, "House")})
        d.lx.rumah = lambda: {1}
        self.assertEqual(d.daftar(1)[0], 409)                                                    # id agent rumah
        self.assertEqual(d.daftar(7)[0], 201)
        self.assertEqual(d.daftar(7)[1]["already"], True)                                        # satu per agent (idempoten)
        dl = int(time.time()) + 60
        self.assertEqual(d.lx.join({"agent_id": 9, "deadline": dl, "signature": tanda(KEY_C, al.pesan_join(9, dl))})[0], 403)   # penanda tangan salah
        d.lx.P["maks_terdaftar"] = 1
        self.assertEqual(d.daftar(9)[0], 409)                                                    # penuh
        d.lx.P["maks_terdaftar"] = 10
        d.books["_v2_kursi"]["kursi"]["x7"] = {"status": "keluar", "sejak": 0, "gagal": True}    # keluar karena gagal (F-D119)
        code, b = d.daftar(7)
        self.assertEqual(code, 403)                                                              # ditolak, bukan "sudah terdaftar"
        self.assertIn("F-D119", b["error"])

    def test_criterion_3_only_active_and_trial_seats_are_asked_queued_and_removed_agents_are_told(self):
        d = Dunia(self.tmp)
        d.daftar(7)
        d.daftar(9)
        d.books["_v2_kursi"]["kursi"]["x7"] = {"status": "antre", "sejak": 0, "tunggu_sampai": MIDNIGHT + 10 ** 6}
        d.books["_v2_kursi"]["kursi"]["x9"] = {"status": "keluar", "sejak": 0, "gagal": True}
        tarik(d.lx, 7, 0)
        tarik(d.lx, 9, 0)
        dipanggil = []
        asli = d.call
        d.call = lambda ag, s, u: (dipanggil.append(ag["slug"]), asli(ag, s, u))[1]
        by = d.jalan(MIDNIGHT + 300)
        self.assertNotIn("x7", " ".join(dipanggil))
        self.assertNotIn("x9", " ".join(dipanggil))                                              # antre / keluar tidak pernah ditanya
        self.assertFalse([a for a in by if a in ("v2:x7", "v2:x9")])                             # dan tidak punya rekaman siklus
        code, b = tarik(d.lx, 7, 0)
        self.assertEqual((code, b["siklus"], b["seat"]), (200, None, "antre"))
        self.assertIn("antre", b["note"])
        self.assertIn("removed", tarik(d.lx, 9, 0, KEY_B)[1]["note"])

    def test_criterion_4_signed_answer_validated_now_first_valid_wins_late_refused_and_the_record_carries_the_proof(self):
        d = Dunia(self.tmp)
        d.daftar(7)
        tarik(d.lx, 7, 0)
        hasil = {}

        def siklus():
            try:
                hasil["raw"] = d.lx.minta(d.lx.agents()[0], "S", "U", MIDNIGHT, lambda raw: meja2.parse2(raw, UNI, ["r_1j"]), time.time() + 10)
            except Exception as e:  # noqa: BLE001
                hasil["galat"] = e
        th = threading.Thread(target=siklus, daemon=True)
        th.start()
        code, req = tarik(d.lx, 7, 3)
        self.assertEqual((code, req["siklus"]), (200, MIDNIGHT))

        def kirim(teks):
            asha = al.sha_bytes(teks.encode())
            return d.lx.jawab({"agent_id": 7, "siklus": MIDNIGHT, "answer": teks, "signature": tanda(KEY_A, al.pesan_jawab(7, MIDNIGHT, req["prompt_sha"], asha))})
        satu, dua = out(ins=(("SOLUSDT", 80),)), out(ins=(("WIFUSDT", 70),))
        self.assertEqual(kirim("{}")[0], 422)                                                    # format salah: ditolak saat itu juga
        kode = []
        ts = [threading.Thread(target=lambda t=t: kode.append(kirim(t)[0])) for t in (satu, dua)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        th.join(5)
        self.assertEqual(sorted(kode)[0], 200)                                                   # tepat satu yang menang
        self.assertTrue(all(c in (200, 409, 410) for c in kode) and kode.count(200) == 1, kode)
        self.assertIn(hasil["raw"], (satu, dua))
        self.assertEqual(kirim(satu)[0], 410)                                                    # sesudah siklus ditutup: ditolak
        b = d.lx.bukti("x7", MIDNIGHT)
        self.assertEqual(pulihkan_cek(7, MIDNIGHT, req["prompt_sha"], al.sha_bytes(hasil["raw"].encode()), b["tanda_tangan"]), addr(KEY_A))

    def test_criterion_5_a_dead_agent_never_delays_the_cycle_or_the_commit(self):
        d = Dunia(self.tmp)
        d.daftar(7)                                                                              # terdaftar tetapi tidak pernah menarik
        d.books["_v2_kursi"]["kursi"]["x7"] = {"status": "uji", "sejak": 0}
        t = time.time()
        by = d.jalan(MIDNIGHT + 300)
        self.assertLess(time.time() - t, 2.0)                                                    # tidak menunggu tenggat 210 s
        self.assertEqual(by["v2:x7"]["status"], "gagal")
        self.assertEqual(by["v2"]["masuk"], ["a", "b", "c"])                                     # konsensus tetap dari agent lain
        self.assertEqual(sorted(by["v2"]["aktif"]), ["a", "b", "c"])

    def test_criterion_3b_pull_is_authenticated_so_nobody_can_fake_presence_or_burn_an_agents_poll_slots(self):
        d = Dunia(self.tmp)
        d.daftar(7)
        self.assertEqual(d.lx.terlihat, {})
        self.assertEqual(tarik(d.lx, 7, 0, KEY_B)[0], 403)                                       # penanda tangan lain
        self.assertEqual(d.lx.tarik(7, 0, None, None)[0], 400)                                   # tanpa tanda tangan
        self.assertEqual(d.lx.tarik(7, 0, int(time.time()), "0xnope")[0], 400)
        self.assertEqual(tarik(d.lx, 7, 0, KEY_A, ts=int(time.time()) - 3600)[0], 401)           # tanda tangan basi (replay)
        self.assertEqual(tarik(d.lx, 7, 0, KEY_A, ts=int(time.time()) + 3600)[0], 401)
        self.assertEqual(d.lx.terlihat, {})                                                      # penolakan tidak memalsukan kehadiran
        self.assertEqual(d.lx.pengintai.get(7, 0), 0)                                            # dan tidak memakai slot long-poll
        self.assertEqual(tarik(d.lx, 7, 0, KEY_A)[0], 200)
        self.assertIn(7, d.lx.terlihat)


@unittest.skipUnless(HAVE_ETH, "butuh eth-account")
class AlurBisnisTests(unittest.TestCase):
    """Alur bisnis lintas siklus (waktu t0 digeser): sukses -> aktif, gagal -> antre -> keluar -> tidak bisa daftar ulang."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_trial_agent_that_answers_well_is_promoted_at_midnight_and_then_votes_while_a_dead_agent_goes_out_and_cannot_return(self):
        d = Dunia(self.tmp, klien=(7,))
        self.assertEqual(d.daftar(7)[0], 201)
        self.assertEqual(d.daftar(9)[0], 201)                                                    # agent 9 terdaftar tetapi tidak pernah hidup
        d.mulai()
        self.addCleanup(d.tutup)
        mulai = time.time()
        seri = []
        for k in range(289):                                                                     # hari 1 + siklus 00:00 UTC berikutnya
            by = d.jalan(MIDNIGHT + 300 * k)
            seri.append(by)
        hari1 = time.time() - mulai
        awal = seri[0]
        self.assertEqual({a: v["kursi"] for a, v in awal.items() if a.startswith("v2:x")}, {"v2:x7": "uji", "v2:x9": "uji"})
        self.assertEqual(awal["v2:x7"]["status"], "ok")
        self.assertEqual(awal["v2:x9"]["status"], "gagal")
        for by in seri[:288]:
            self.assertEqual(by["v2"]["masuk"], ["a", "b", "c"])                                 # selama uji: tidak ada suara agent luar
            self.assertEqual(by["v2:x7"]["status"], "ok")                                        # agent hidup menjawab TIAP siklus
        tengah = seri[288]                                                                        # siklus 00:00 UTC: evaluasi harian
        ev = {e["agent"]: (e["dari"], e["ke"]) for e in tengah["kursi"]["peristiwa"]}
        self.assertEqual(ev["x7"], ("uji", "aktif"))                                             # >= 288 siklus, sah 100 %, hasil >= median aktif
        self.assertEqual(ev["x9"], ("uji", "antre"))                                             # sah 0 % dari 288 siklus teramati: kegagalan 1
        self.assertEqual(sorted(tengah["v2"]["aktif"]), ["a", "b", "c", "x7"])
        self.assertIn("x7", tengah["v2"]["masuk"])                                               # sekarang suaranya dihitung
        self.assertEqual(d.status("x9")["kursi"], "antre")
        # hari 2: x9 dikembalikan ke uji sesudah masa tunggu (evaluasi 00:00 berikutnya), hari 3: gagal kedua -> keluar
        for k in range(289, 289 + 288 * 2):
            by = d.jalan(MIDNIGHT + 300 * k)
            if "kursi" in by:
                for e in by["kursi"]["peristiwa"]:
                    if e["agent"] == "x9":
                        seri.append(e)
        urutan = [(e["dari"], e["ke"]) for e in seri[289:] if isinstance(e, dict) and "ke" in e]
        self.assertEqual(urutan, [("antre", "uji"), ("uji", "keluar")])
        self.assertEqual(d.books["_v2_kursi"]["kursi"]["x9"]["gagal"], True)
        self.assertEqual(d.books["_v2_kursi"]["kursi"]["x7"]["status"], "aktif")
        code, b = d.daftar(9)
        self.assertEqual(code, 403)                                                              # tidak bisa daftar ulang
        self.assertTrue([a for a in d.lx.roster() if a["slug"] == "x9"][0]["removed_for_failures"])
        akhir = d.jalan(MIDNIGHT + 300 * (289 + 288 * 2))
        self.assertNotIn("v2:x9", akhir)                                                         # tidak otomatis masuk lagi
        self.assertLess(time.time() - mulai, 120.0, "seluruh alur 3 hari simulasi harus cepat: agent mati tidak boleh ditunggu")
        print(f"\n[alur bisnis] {289 + 288 * 2 + 1} siklus simulasi dalam {time.time() - mulai:.1f} s (hari 1: {hari1:.1f} s)")


@unittest.skipUnless(HAVE_ETH, "butuh eth-account")
class GerbangTests(unittest.TestCase):
    """Jalur gerbang sungguhan: `v2_siklus` (yang dipakai `meja_loop`) -> rekaman disimpan -> /desk/proof memulihkan penanda tangan dari rekaman."""

    def setUp(self):
        import x402_sinyal as xs
        self.xs = xs
        self.tmp = tempfile.mkdtemp()
        old, os.environ["ANALIS_DIR"] = os.environ.get("ANALIS_DIR"), os.path.join(self.tmp, "analis")
        self.addCleanup(lambda: os.environ.pop("ANALIS_DIR") if old is None else os.environ.update(ANALIS_DIR=old))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.t = MIDNIGHT + 300
        self.clock = self.t + 20
        self.g = xs.Gate(xs.Data(ROOT), "0xk", "https://g", "https://w", log=lambda m: None, now=lambda: self.clock)
        self.g.luar.resolve = identitas(PETA)
        self.g.luar.rumah = lambda: set()
        self.g.data_tunggu = lambda t0, sampai: SNAP
        srv = ThreadingHTTPServer(("127.0.0.1", 0), xs.make_handler(self.g))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        self.url = f"http://127.0.0.1:{srv.server_address[1]}"

    def http(self, path, body=None):
        req = urllib.request.Request(self.url + path, data=None if body is None else json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def test_the_gate_cycle_asks_the_external_agent_over_http_stores_the_record_and_the_proof_endpoint_verifies_the_signature(self):
        dl = int(self.g.luar.now()) + 600                                                        # jam gerbang (palsu), bukan jam nyata
        self.assertEqual(self.http("/desk/external/join", {"agent_id": 7, "deadline": dl, "signature": tanda(KEY_A, al.pesan_join(7, dl))})[0], 201)
        box = {}

        def klien():                                                                             # agent luar sepenuhnya lewat HTTP, seperti proses lain
            for _ in range(60):
                code, req = self.http(url_tarik(7, 1, ts=int(self.g.luar.now())))
                if code == 200 and req.get("siklus"):
                    jawab = out(ins=(("SOLUSDT", 80),))
                    asha = al.sha_bytes(jawab.encode())
                    box["jawab"] = self.http("/desk/external/answer", {"agent_id": 7, "siklus": req["siklus"], "answer": jawab,
                                                                       "signature": tanda(KEY_A, al.pesan_jawab(7, req["siklus"], req["prompt_sha"], asha))})
                    box["req"] = req
                    return
        self.assertEqual(self.http(url_tarik(7, 0, ts=int(self.g.luar.now())))[0], 200)           # hadir
        th = threading.Thread(target=klien, daemon=True)
        th.start()
        time.sleep(0.3)
        rumah = [{"slug": s, "agent_id": i, "model": "m", "name": s} for i, s in enumerate(["a", "b", "c"], 1)]
        books = {"_v2_kursi": {"kursi": {s: {"status": "aktif", "sejak": 0} for s in ("a", "b", "c")}}}
        ring, hasil = {}, {}
        with mock.patch.object(self.xs.an, "call_model", lambda ag, s, u, **k: out(ins=(("SOLUSDT", 80), ("WIFUSDT", 70)))), \
                mock.patch.object(meja, "_get_json", get), mock.patch.object(self.xs.an, "muat_kursi_builder", lambda *a, **k: []):
            self.xs.v2_siklus(self.g, books, ring, FakePasar(), self.t, rumah, hasil)
        th.join(10)
        self.assertEqual(box["jawab"][0], 200, box)
        self.assertIn("rek", hasil)                                                              # v2_siklus selesai (tidak jatuh ke `meja v2 gagal`)
        rek = hasil["rek"]
        ext = next(r for r in rek if r["agent"] == "v2:x7")
        self.assertEqual((ext["status"], ext["kursi"], ext["agent_id"]), ("ok", "uji", 7))
        sik = {"siklus": self.t, "daun": [r["hash"] for r in rek], "harga": {}, "harga_v2": hasil["harga"], "tx": "0xtx"}
        sik.update(root=meja.root_of(sik["daun"]), n=len(sik["daun"]), status="dikomit")
        self.g.meja_simpan(rek, sik, hasil["books"], hasil["ring"])
        code, tahan = self.http(f"/desk/proof/{ext['hash']}")
        self.assertEqual((code, tahan["root"], tahan["tx"]), (402, sik["root"], "0xtx"))                 # P165: isi < 24 jam tertutup untuk publik, komitmen terlihat
        self.assertNotIn("rekaman", tahan)
        self.clock = self.t + self.xs.TUNDA_PUBLIK_S + 600
        self.g.__dict__.pop("_meja", None)
        code, p = self.http(f"/desk/proof/{ext['hash']}")
        self.assertEqual(code, 200, p)                                                           # sesudah 24 jam: dibuktikan seperti rekaman lain
        r = p["rekaman"]
        self.assertEqual(p["hash_dihitung_ulang"], r["hash"])
        self.assertTrue(chain.merkle_verify([bytes.fromhex(x[2:]) for x in p["proof"]], bytes.fromhex(p["root"][2:]), bytes.fromhex(r["hash"][2:])))
        penanda = pulihkan_cek(r["agent_id"], r["siklus"], r["prompt_sha"], r["jawaban_sha"], r["luar"]["tanda_tangan"])
        self.assertEqual((penanda, r["luar"]["penanda_tangan"]), (addr(KEY_A), addr(KEY_A)))     # pihak ketiga: dari rekaman + proof saja
        by = {x["agent"]: x for x in rek}
        self.assertEqual(by["v2"]["masuk"], ["a", "b", "c"])                                     # suara uji tidak dihitung
        book = next(b for b in self.g.meja_view(max_age_s=0)["buku"] if b["agent"] == "v2:x7")    # /desk menamai dan menandai agent luar
        self.assertEqual((book["nama"], book["luar"], book["kursi"]), ("Alpha", True, "uji"))
        self.assertFalse(next(b for b in self.g.meja_view()["buku"] if b["agent"] == "v2:a")["luar"])


if __name__ == "__main__":
    unittest.main()

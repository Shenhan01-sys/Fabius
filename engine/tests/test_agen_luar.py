"""P166 (F-D121): agent LUAR ikut siklus meja dengan cara PULL. Identitas ERC-8004 + model dipalsukan; tanda tangan EIP-191 NYATA (eth-account)."""
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "tools"), ROOT]

import agen_luar as al                                              # noqa: E402
import meja                                                         # noqa: E402
import meja2                                                        # noqa: E402
from .test_meja2 import FakePasar, UNI, out                         # noqa: E402

try:
    from eth_account import Account
    from eth_account.messages import encode_defunct
    HAVE_ETH = True
except ImportError:                                                 # pragma: no cover
    HAVE_ETH = False

KEY_A, KEY_B, KEY_C = "0x" + "11" * 32, "0x" + "22" * 32, "0x" + "33" * 32


def tanda(key: str, pesan: str) -> str:
    return "0x" + Account.sign_message(encode_defunct(text=pesan), key).signature.hex().removeprefix("0x")


def addr(key: str) -> str:
    return Account.from_key(key).address


def identitas(peta):
    """resolve palsu: {agent_id: (pemilik_key, dompet_key|None, nama)}; id lain = tidak ada."""
    def resolve(aid):
        if aid not in peta:
            raise KeyError(aid)
        o, w, n = peta[aid]
        return {"owner": addr(o), "wallet": addr(w) if w else None, "nama": n}
    return resolve


@unittest.skipUnless(HAVE_ETH, "butuh eth-account")
class JoinTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = os.path.join(self.tmp, "luar.json")
        self.t = 1_791_200_000
        self.peta = {7: (KEY_A, KEY_B, "  Alpha <b>Agent</b> "), 8: (KEY_A, None, "Same Owner"), 9: (KEY_C, None, "Gamma"), 5: (KEY_C, None, "House")}
        self.lx = al.Luar(self.path, now=lambda: self.t, resolve=identitas(self.peta), rumah=lambda: {5})

    def join(self, aid, key, dl=None, lx=None):
        dl = dl if dl is not None else self.t + 600
        return (lx or self.lx).join({"agent_id": aid, "deadline": dl, "signature": tanda(key, al.pesan_join(aid, dl))})

    def test_only_the_agent_wallet_or_identity_owner_may_register_and_limits_hold(self):
        self.assertEqual(self.join(7, KEY_C)[0], 403)                                            # bukan dompet agent / pemilik
        self.assertEqual(self.join(99, KEY_A)[0], 404)                                           # identitas tidak ada
        self.assertEqual(self.join(7, KEY_A, dl=self.t - 1)[0], 401)                             # kedaluwarsa
        self.assertEqual(self.join(7, KEY_A, dl=self.t + 7200)[0], 400)                          # TTL terlalu jauh
        self.assertEqual(self.lx.join({"agent_id": 7, "deadline": self.t + 60, "signature": "0xnope"})[0], 400)
        self.assertEqual(self.lx.join({"agent_id": "x"})[0], 400)
        self.assertEqual(self.join(5, KEY_C)[0], 409)                                            # id agent rumah
        self.assertEqual(self.lx.agen, {})                                                       # semua penolakan: tidak ada yang tersimpan
        code, a = self.join(7, KEY_B)                                                            # dompet agent boleh
        self.assertEqual((code, a["slug"], a["name"]), (201, "x7", "Alpha bAgentb"))             # nama dibersihkan (tanpa < >)
        self.assertEqual(self.join(7, KEY_A)[:2], (200, {**self.join(7, KEY_A)[1]}))             # pemilik juga boleh; sudah terdaftar = idempoten
        self.assertTrue(self.join(7, KEY_A)[1]["already"])
        self.assertEqual(self.join(8, KEY_A)[0], 409)                                            # satu per pemilik
        self.assertEqual(self.join(9, KEY_C)[0], 201)
        # simpan + muat ulang
        lagi = al.Luar(self.path, now=lambda: self.t, resolve=identitas(self.peta))
        self.assertEqual(sorted(lagi.agen), ["x7", "x9"])
        self.assertEqual([a["slug"] for a in lagi.agents()], ["x7", "x9"])
        self.assertTrue(all(a["luar"] for a in lagi.agents()))

    def test_the_desk_has_a_cap_and_an_hourly_registration_limit(self):
        peta = {i: ("0x" + "%02x" % (40 + i) * 32, None, f"A{i}") for i in range(1, 6)}
        lx = al.Luar(os.path.join(self.tmp, "b.json"), now=lambda: self.t, resolve=identitas(peta), params={"maks_terdaftar": 2, "join_per_jam": 3})
        keys = {i: peta[i][0] for i in peta}
        self.assertEqual([self.join(i, keys[i], lx=lx)[0] for i in (1, 2)], [201, 201])
        self.assertEqual(self.join(3, keys[3], lx=lx)[0], 409)                                   # penuh
        lx.P["maks_terdaftar"] = 9
        self.assertEqual(self.join(3, keys[3], lx=lx)[0], 201)                                   # 3 pendaftaran dalam sejam
        self.assertEqual(self.join(4, keys[4], lx=lx)[0], 429)
        self.t += 3601
        self.assertEqual(self.join(4, keys[4], lx=lx)[0], 201)

    def test_info_lists_the_rules_message_formats_and_roster(self):
        self.join(7, KEY_A)
        lx = al.Luar(self.path, now=lambda: self.t, resolve=identitas(self.peta),
                     status=lambda s: {"kursi": "uji", "gagal": False, "n": 10, "sah_pct": 90.0})
        i = lx.info()
        self.assertEqual(i["params"]["maks_terdaftar"], 10)
        self.assertIn("Fabius desk answer v1", i["sign"]["answer_message"])
        self.assertEqual((i["agents"][0]["slug"], i["agents"][0]["seat"], i["agents"][0]["valid_pct"], i["agents"][0]["online"]), ("x7", "uji", 90.0, False))


@unittest.skipUnless(HAVE_ETH, "butuh eth-account")
class PullTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.lx = al.Luar(os.path.join(self.tmp, "luar.json"), resolve=identitas({7: (KEY_A, None, "Alpha")}), params={"pengintai_per_agen": 1})
        dl = int(time.time()) + 600
        self.assertEqual(self.lx.join({"agent_id": 7, "deadline": dl, "signature": tanda(KEY_A, al.pesan_join(7, dl))})[0], 201)
        self.ag = self.lx.agents()[0]
        self.siklus = int(time.time() // 300 * 300)

    def jalankan_minta(self, tenggat_s=6.0, validasi=None):
        hasil = {}

        def run():
            try:
                hasil["raw"] = self.lx.minta({**self.ag}, "SYS", "USER", self.siklus, validasi or (lambda raw: json.loads(raw)), time.time() + tenggat_s)
            except Exception as e:  # noqa: BLE001
                hasil["galat"] = e
        self.lx.tarik(7, 0)                                                                      # kehadiran
        th = threading.Thread(target=run, daemon=True)
        th.start()
        return th, hasil

    def kirim(self, req, jawaban, key=KEY_A):
        psha, asha = req["prompt_sha"], al.sha_bytes(jawaban.encode())
        return self.lx.jawab({"agent_id": 7, "siklus": req["siklus"], "answer": jawaban, "signature": tanda(key, al.pesan_jawab(7, req["siklus"], psha, asha))})

    def test_pull_gives_the_cycle_input_and_only_a_signed_valid_answer_ends_the_wait(self):
        th, hasil = self.jalankan_minta()
        code, req = self.lx.tarik(7, 3)
        self.assertEqual((code, req["siklus"], req["system"], req["prompt"]), (200, self.siklus, "SYS", "USER"))
        self.assertEqual(req["prompt_sha"], al.sha_masukan("SYS", "USER"))                       # sama dengan rumus `prompt_sha` di rekaman meja2
        self.assertEqual(self.kirim(req, "bukan json")[0], 422)                                  # salah format: ditolak SAAT ITU, boleh ulang
        self.assertEqual(self.kirim(req, '{"a": 1}', key=KEY_B)[0], 403)                          # bukan penanda tangan terdaftar
        self.assertTrue(th.is_alive())                                                           # belum ada jawaban sah: siklus masih menunggu
        code, ok = self.kirim(req, '{"a": 1}')
        self.assertEqual((code, ok["accepted"], ok["answer_sha"]), (200, True, al.sha_bytes(b'{"a": 1}')))
        th.join(5)
        self.assertEqual(hasil["raw"], '{"a": 1}')
        b = self.lx.bukti("x7", self.siklus)
        self.assertEqual(b["penanda_tangan"], addr(KEY_A))
        self.assertEqual(al.pulihkan(al.pesan_jawab(7, self.siklus, req["prompt_sha"], ok["answer_sha"]), b["tanda_tangan"]), addr(KEY_A))   # pihak ketiga bisa memeriksa
        self.assertIsNone(self.lx.bukti("x7", self.siklus + 300))
        self.assertEqual(self.kirim(req, '{"a": 2}')[0], 410)                                    # siklus sudah ditutup: jawaban kedua tidak punya rumah
        self.assertEqual(self.lx.tarik(7, 0)[1]["siklus"], None)

    def test_a_signature_for_another_prompt_or_answer_is_refused(self):
        th, hasil = self.jalankan_minta()
        _, req = self.lx.tarik(7, 3)
        salah = tanda(KEY_A, al.pesan_jawab(7, req["siklus"], "0x" + "00" * 32, al.sha_bytes(b"{}")))              # prompt lain
        self.assertEqual(self.lx.jawab({"agent_id": 7, "siklus": req["siklus"], "answer": "{}", "signature": salah})[0], 403)
        beda = tanda(KEY_A, al.pesan_jawab(7, req["siklus"], req["prompt_sha"], al.sha_bytes(b'{"x":1}')))        # jawaban lain
        self.assertEqual(self.lx.jawab({"agent_id": 7, "siklus": req["siklus"], "answer": "{}", "signature": beda})[0], 403)
        self.assertEqual(self.lx.jawab({"agent_id": 7, "siklus": req["siklus"] - 300, "answer": "{}", "signature": beda})[0], 410)   # siklus lain
        self.assertEqual(self.lx.jawab({"agent_id": 8, "siklus": req["siklus"], "answer": "{}", "signature": beda})[0], 403)          # tidak terdaftar
        self.assertEqual(self.lx.jawab({"agent_id": 7, "siklus": req["siklus"], "answer": 5, "signature": beda})[0], 400)
        self.assertEqual(self.lx.jawab({"agent_id": 7, "siklus": req["siklus"], "answer": "x" * 20_000, "signature": beda})[0], 413)
        self.assertTrue(th.is_alive())
        self.kirim(req, "{}")
        th.join(5)
        self.assertEqual(hasil["raw"], "{}")

    def test_an_offline_agent_fails_fast_and_a_silent_one_times_out_then_cannot_answer(self):
        t = time.time()
        with self.assertRaises(RuntimeError) as c:                                               # tidak pernah menarik: tidak ditunggu
            self.lx.minta({**self.ag}, "S", "U", self.siklus, lambda r: r, time.time() + 30)
        self.assertIn("not polling", str(c.exception))
        self.assertLess(time.time() - t, 1.0)
        self.lx.tarik(7, 0)
        t = time.time()
        with self.assertRaises(TimeoutError):                                                    # hadir tetapi diam: berhenti di tenggat, tidak lebih
            self.lx.minta({**self.ag}, "S", "U", self.siklus, lambda r: r, time.time() + 0.4)
        self.assertLess(time.time() - t, 2.0)
        psha = al.sha_masukan("S", "U")
        sig = tanda(KEY_A, al.pesan_jawab(7, self.siklus, psha, al.sha_bytes(b"{}")))
        self.assertEqual(self.lx.jawab({"agent_id": 7, "siklus": self.siklus, "answer": "{}", "signature": sig})[0], 410)

    def test_unregistered_agents_get_404_and_queued_ones_are_told_their_seat(self):
        self.assertEqual(self.lx.tarik(99, 0)[0], 404)
        self.lx.status = lambda slug: {"kursi": "antre"}
        code, b = self.lx.tarik(7, 0)
        self.assertEqual((code, b["siklus"], b["seat"]), (200, None, "antre"))
        self.assertIn("antre", b["note"])

    def test_open_polls_are_limited_per_agent(self):
        hasil = []
        th = threading.Thread(target=lambda: hasil.append(self.lx.tarik(7, 2)), daemon=True)
        th.start()
        time.sleep(0.3)
        self.assertEqual(self.lx.tarik(7, 0)[0], 429)                                            # batas 1 long-poll terbuka per agent
        th.join(5)
        self.assertEqual(hasil[0][0], 200)
        self.assertEqual(self.lx.tarik(7, 0)[0], 200)                                            # sesudah ditutup boleh lagi


@unittest.skipUnless(HAVE_ETH, "butuh eth-account")
class CycleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.lx = al.Luar(os.path.join(self.tmp, "luar.json"), resolve=identitas({7: (KEY_A, None, "Alpha")}))
        dl = int(time.time()) + 600
        self.lx.join({"agent_id": 7, "deadline": dl, "signature": tanda(KEY_A, al.pesan_join(7, dl))})
        self.agents = [{"slug": s, "agent_id": i, "model": "m"} for i, s in enumerate(["a", "b", "c"], 1)] + self.lx.agents()
        self.books = {"_v2_kursi": {"kursi": {s: {"status": "aktif", "sejak": 0} for s in ("a", "b", "c")}}}
        self.t0 = 1_791_200_100

    def call(self, ag, system, user):
        if ag.get("luar"):
            return self.lx.minta(ag, system, user, ag["siklus"], ag["validasi"], ag.get("tenggat"))
        return out(ins=(("SOLUSDT", 80), ("WIFUSDT", 70)))

    def siklus(self):
        get = lambda url: [{"symbol": a, "markPrice": "100", "lastFundingRate": "0"} for a in UNI]       # noqa: E731
        snap = {"sha": "0xabc", "fitur_aset": {"SOLUSDT": {"r_1j": 0.01}}, "fitur_bot": {}}
        rek, _ = meja2.siklus2(self.t0, self.agents, self.books, {}, self.call, snap, FakePasar(), get=get, log=lambda m: None, bukti=self.lx.bukti)
        return {r["agent"]: r for r in rek}

    def klien(self, jawaban):
        """Agent luar: tarik -> tandatangani -> jawab (di thread sendiri, seperti proses lain)."""
        hasil = {}

        def run():
            self.lx.tarik(7, 0)
            for _ in range(40):
                code, req = self.lx.tarik(7, 1)
                if req.get("siklus"):
                    asha = al.sha_bytes(jawaban.encode())
                    hasil["jawab"] = self.lx.jawab({"agent_id": 7, "siklus": req["siklus"], "answer": jawaban,
                                                    "signature": tanda(KEY_A, al.pesan_jawab(7, req["siklus"], req["prompt_sha"], asha))})
                    hasil["req"] = req
                    return
        th = threading.Thread(target=run, daemon=True)
        th.start()
        time.sleep(0.2)
        return th, hasil

    def test_an_external_answer_enters_the_hashed_record_with_a_verifiable_proof_but_does_not_vote(self):
        th, hasil = self.klien(out(bot="B6-BOUNCE", skor={b: (100 if b == "B6-BOUNCE" else -100) for b in meja2.BOTS}, ins=(("SOLUSDT", 100),)))
        by = self.siklus()
        th.join(5)
        self.assertEqual(hasil["jawab"][0], 200)
        r = by["v2:x7"]
        self.assertEqual((r["status"], r["kursi"], r["agent_id"], r["model"]), ("ok", "uji", 7, "external ERC-8004 #7"))
        self.assertEqual(r["prompt_sha"], meja.sha(meja2.SYSTEM2.encode() + b"\n" + hasil["req"]["prompt"].encode()))
        self.assertEqual(r["prompt_sha"], hasil["req"]["prompt_sha"])
        self.assertEqual(r["jawaban_sha"], hasil["jawab"][1]["answer_sha"])
        self.assertEqual(r["luar"]["penanda_tangan"], addr(KEY_A))
        # pihak ketiga: rekaman yang di-hash memuat semua yang perlu untuk memeriksa tanda tangan
        self.assertEqual(al.pulihkan(al.pesan_jawab(r["agent_id"], r["siklus"], r["prompt_sha"], r["jawaban_sha"]), r["luar"]["tanda_tangan"]), addr(KEY_A))
        self.assertEqual(r["hash"], meja.sha({k: v for k, v in r.items() if k != "hash"}))
        self.assertEqual((by["v2"]["bot"], by["v2"]["masuk"]), ("B1-TREND", ["a", "b", "c"]))       # SK-M20: suara uji (B6, yakin penuh) tidak dihitung
        self.assertEqual(by["kursi"]["peristiwa"], [{"agent": "x7", "dari": None, "ke": "uji", "alasan": "agent baru"}])

    def test_an_offline_external_agent_is_recorded_as_failed_without_delaying_the_cycle(self):
        t = time.time()
        by = self.siklus()
        self.assertLess(time.time() - t, 3.0)
        self.assertEqual(by["v2:x7"]["status"], "gagal")
        self.assertIn("not polling", by["v2:x7"]["galat"])
        self.assertNotIn("luar", by["v2:x7"])
        self.assertEqual(by["v2"]["masuk"], ["a", "b", "c"])

    def test_an_external_answer_with_a_bad_format_is_rejected_live_and_a_corrected_one_still_counts(self):
        self.books["_v2_kursi"]["kursi"]["x7"] = {"status": "uji", "sejak": 0}
        hasil = {}

        def run():
            self.lx.tarik(7, 0)
            for _ in range(40):
                _, req = self.lx.tarik(7, 1)
                if req.get("siklus"):
                    for jawaban in ('{"bot": "NOPE"}', out()):
                        asha = al.sha_bytes(jawaban.encode())
                        hasil.setdefault("kode", []).append(self.lx.jawab({"agent_id": 7, "siklus": req["siklus"], "answer": jawaban,
                                                                           "signature": tanda(KEY_A, al.pesan_jawab(7, req["siklus"], req["prompt_sha"], asha))})[0])
                    return
        th = threading.Thread(target=run, daemon=True)
        th.start()
        time.sleep(0.2)
        by = self.siklus()
        th.join(5)
        self.assertEqual(hasil["kode"], [422, 200])
        self.assertEqual(by["v2:x7"]["status"], "ok")


@unittest.skipUnless(HAVE_ETH, "butuh eth-account")
class HttpTests(unittest.TestCase):
    def setUp(self):
        import x402_sinyal as xs
        self.tmp = tempfile.mkdtemp()
        old, os.environ["ANALIS_DIR"] = os.environ.get("ANALIS_DIR"), os.path.join(self.tmp, "analis")
        self.addCleanup(lambda: os.environ.pop("ANALIS_DIR") if old is None else os.environ.update(ANALIS_DIR=old))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.g = xs.Gate(xs.Data(ROOT), "0xk", "https://g", "https://w", log=lambda m: None)
        self.g.luar.resolve = identitas({7: (KEY_A, None, "Alpha")})
        srv = ThreadingHTTPServer(("127.0.0.1", 0), xs.make_handler(self.g))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        self.url = f"http://127.0.0.1:{srv.server_address[1]}"

    def http(self, path, body=None):
        req = urllib.request.Request(self.url + path, data=None if body is None else json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def test_the_whole_pull_flow_over_http(self):
        code, info = self.http("/desk/external")
        self.assertEqual((code, info["agents"]), (200, []))
        self.assertIn("POST /desk/external/join", info["endpoints"]["join"])
        dl = int(time.time()) + 600
        sig = tanda(KEY_A, al.pesan_join(7, dl))
        self.assertEqual(self.http("/desk/external/join", {"agent_id": 7, "deadline": dl, "signature": tanda(KEY_B, al.pesan_join(7, dl))})[0], 403)
        code, j = self.http("/desk/external/join", {"agent_id": 7, "deadline": dl, "signature": sig})
        self.assertEqual((code, j["slug"]), (201, "x7"))
        self.assertEqual(self.http("/desk/external/pull?agent_id=abc")[0], 400)
        self.assertEqual(self.http("/desk/external/pull?agent_id=8")[0], 404)
        code, p = self.http("/desk/external/pull?agent_id=7&wait=0")
        self.assertEqual((code, p["siklus"]), (200, None))                                       # belum ada siklus terbuka
        self.assertEqual(self.http("/desk/external/answer", {"agent_id": 7, "siklus": 1, "answer": "{}", "signature": sig})[0], 410)
        self.assertEqual([a["slug"] for a in self.http("/desk/external")[1]["agents"]], ["x7"])
        self.assertTrue(self.http("/desk/external")[1]["agents"][0]["online"])
        self.assertEqual(self.http("/desk/external/join", [1])[0], 400)                           # bukan objek JSON

    def test_the_reference_client_runs_join_and_one_cycle_end_to_end(self):
        """Klien acuan (proses terpisah, tanda tangan nyata) mendaftar lalu menjawab satu siklus yang dijalankan `siklus2` di gerbang yang sama."""
        import subprocess
        env = {**os.environ, "AGENT_KEY": KEY_A, "PYTHONUTF8": "1"}
        klien = [sys.executable, "-X", "utf8", os.path.join(ROOT, "tools", "desk_agent_client.py"), "--gate", self.url, "--agent-id", "7"]
        r = subprocess.run(klien + ["join"], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("x7", r.stdout)
        jawab = os.path.join(self.tmp, "jawab.py")
        with open(jawab, "w", encoding="utf-8") as f:
            f.write("\n".join(["import sys, json", "req = json.load(sys.stdin)", "assert req['system'] and req['prompt'] and req['deadline']",
                               "print(%r)" % out(ins=(("SOLUSDT", 80),))]) + "\n")
        box = {}
        th = threading.Thread(target=lambda: box.update(r=subprocess.run(klien + ["run", "--once", "--answer-cmd", f'"{sys.executable}" "{jawab}"'], env=env,
                                                                         capture_output=True, text=True, timeout=120)), daemon=True)
        th.start()
        for _ in range(100):                                                                     # tunggu klien menarik pertama kali (hadir)
            if self.g.luar.terlihat:
                break
            time.sleep(0.1)
        self.assertTrue(self.g.luar.terlihat)

        def call(ag, system, user):
            if ag.get("luar"):
                return self.g.luar.minta(ag, system, user, ag["siklus"], ag["validasi"], ag.get("tenggat"))
            return out()
        agents = [{"slug": s_, "agent_id": i, "model": "m"} for i, s_ in enumerate(["a", "b", "c"], 1)] + self.g.luar.agents()
        books = {"_v2_kursi": {"kursi": {s_: {"status": "aktif", "sejak": 0} for s_ in ("a", "b", "c")}}}
        get = lambda url: [{"symbol": a, "markPrice": "100", "lastFundingRate": "0"} for a in UNI]       # noqa: E731
        rek, _ = meja2.siklus2(1_791_200_100, agents, books, {}, call, {"sha": "0x1", "fitur_aset": {"SOLUSDT": {"r_1j": 0.01}}, "fitur_bot": {}}, FakePasar(), get=get, log=lambda m: None,
                               bukti=self.g.luar.bukti)
        th.join(60)
        self.assertEqual(box["r"].returncode, 0, box["r"].stdout + box["r"].stderr)
        self.assertIn("HTTP 200", box["r"].stdout)
        x = next(r_ for r_ in rek if r_["agent"] == "v2:x7")
        self.assertEqual((x["status"], x["kursi"]), ("ok", "uji"))
        self.assertEqual(al.pulihkan(al.pesan_jawab(x["agent_id"], x["siklus"], x["prompt_sha"], x["jawaban_sha"]), x["luar"]["tanda_tangan"]), addr(KEY_A))


if __name__ == "__main__":
    unittest.main()

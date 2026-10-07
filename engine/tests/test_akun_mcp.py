"""P157 (F5, F-D111): akun MCP berbayar - buku besar berantai, kunci API dari tanda tangan dompet, deposit x402 sekali kredit, potong per panggilan
sekali per call_id, saldo kurang / kunci tidak sah tanpa data (SK-M11, SK-M12), sakelar FABIUS_F5 bawaan mati. Chain dipalsukan; tanda tangan EIP-191 /
EIP-712 sungguhan dari dompet buangan (eth-account)."""
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "tools"), ROOT]
try:
    from eth_account import Account
    HAVE_ACC = True
except ImportError:
    HAVE_ACC = False
try:
    import eth_abi                                                    # noqa: F401
    HAVE_ETH = True
except ImportError:
    HAVE_ETH = False

import akun_mcp as am                                                 # noqa: E402
import akun_uji_kering as uk                                          # noqa: E402

DOMPET = "0x" + "be" * 20
NOW = 1_791_540_700
NYALA = {"FABIUS_F5": "hidup"}


def stub_pulihkan(siapa=DOMPET):
    return lambda pesan, tanda_tangan: siapa


def kunci_baru(akun, dompet=DOMPET, ts=NOW):
    """Kunci lewat jalur sungguhan `buat_kunci` (pulihkan dipalsukan di akun ini)."""
    code, out = akun.buat_kunci({"wallet": dompet, "ts": ts, "signature": "0x" + "11" * 65})
    assert code == 201, out
    return out["key"]


def setor(akun, atomic, nonce="1", dompet=DOMPET, tx="0xtx1"):
    return akun.kredit(dompet, atomic, nonce, lambda: {"ok": True, "tx": tx, "payer": dompet})


class BukuTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="akun-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def akun(self, pulihkan=None):
        return am.Akun(self.tmp, now=lambda: NOW, pulihkan=pulihkan or stub_pulihkan())

    def test_prices_are_the_approved_table_and_public_data_tools_are_removed(self):
        self.assertEqual(am.HARGA, {"fabius_signal": 10_000, "fabius_signal_explain": 20_000, "fabius_data": 5_000})   # F-D111 #2
        self.assertEqual(set(am.GRATIS), {"fabius_pricing", "fabius_account"})
        for p140 in ("fabius_dexscreener", "fabius_rugcheck", "fabius_bubblemaps", "fabius_fomo"):                      # F-D111 #3
            self.assertIn(p140, am.DICABUT)
            self.assertNotIn(p140, am.HARGA_MCP)
        self.assertFalse(set(am.HARGA) & set(am.HARGA_MCP) or set(am.GRATIS) & (set(am.HARGA) | set(am.HARGA_MCP)))

    def test_the_switch_is_off_unless_set_to_an_exact_on_word(self):
        for v in ("", "mati", "true", "yes", "hidupkan", "0"):
            self.assertFalse(am.sakelar(v), v)
        for v in ("hidup", "nyala", "1", " HIDUP "):
            self.assertTrue(am.sakelar(v), v)
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(am.sakelar())

    def test_only_fabius_api_keys_are_read_from_headers(self):
        k = "fabk_" + "A" * 43
        self.assertEqual(am.kunci_dari({"Authorization": f"Bearer {k}"}), k)
        self.assertEqual(am.kunci_dari({"X-Api-Key": k}), k)
        self.assertIsNone(am.kunci_dari({"Authorization": "Bearer eyJhbGciOiJFUzI1NiJ9.privy.token"}))                # token Privy bukan kunci akun
        self.assertIsNone(am.kunci_dari({"Authorization": "Bearer fabk_pendek"}))

    def test_the_ledger_replays_to_the_same_balance_and_any_edit_stops_the_paid_service(self):
        a = self.akun()
        setor(a, 100_000)
        k = kunci_baru(a)
        self.assertEqual(a.potong(k, "fabius_verify", "c1", "0x" + "ab" * 32)[0], 200)
        b = self.akun()                                                                                 # mulai ulang: saldo dihitung ulang dari buku
        self.assertEqual((b.saldo[DOMPET], b.rusak, b.kepala_buku()), (95_000, [], a.kepala_buku()))
        saldo, masalah = am.periksa_rantai(b.recs)
        self.assertEqual((saldo, masalah), ({DOMPET: 95_000}, []))
        with open(a.path, encoding="utf-8") as f:
            rows = f.read().splitlines()
        for rusak in ([rows[0].replace('"atomic":100000', '"atomic":900000')] + rows[1:],                     # isi diubah -> h tidak cocok
                      [rows[0], rows[2]],                                                                        # rekaman dihapus -> n / prev putus
                      rows + [rows[-1]]):                                                                        # rekaman diulang
            with open(a.path, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(rusak) + "\n")
            c = self.akun()
            self.assertTrue(c.rusak)
            for code, _ in (c.akun(k), c.potong(k, "fabius_verify", "c9"), c.buat_kunci({"wallet": DOMPET, "ts": NOW, "signature": "0x" + "22" * 65}),
                            setor(c, 100_000, nonce="9")):
                self.assertEqual(code, 503)                                                              # berhenti, tidak menebak saldo

    def test_records_chain_per_wallet_and_hash_their_own_content(self):
        a = self.akun()
        setor(a, 100_000)
        setor(a, 50_000, nonce="2", dompet="0x" + "cd" * 20, tx="0xtx2")
        setor(a, 50_000, nonce="3", tx="0xtx3")
        r = a.recs
        self.assertEqual([x["n"] for x in r], [0, 1, 2])
        self.assertEqual((r[0]["prev"], r[1]["prev"], r[2]["prev"]), (am.NOL, am.NOL, r[0]["h"]))                # prev = rekaman terakhir DOMPET yang sama
        for x in r:
            self.assertEqual(x["h"], am.hash_rekaman(x))


class KunciTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="akun-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.now = NOW
        self.a = am.Akun(self.tmp, now=lambda: self.now)                                               # pulihkan ASLI (EIP-191, eth-account)

    @unittest.skipUnless(HAVE_ACC, "eth-account tidak terpasang")
    def test_a_wallet_signed_message_issues_a_key_shown_once_and_stored_only_as_its_hash(self):
        w = Account.create()
        code, out = self.a.buat_kunci({"wallet": w.address, "ts": NOW, "signature": uk.tanda_pesan(w, am.pesan_kunci(w.address, NOW))})
        self.assertEqual(code, 201, out)
        self.assertRegex(out["key"], am.KUNCI_RE)
        with open(self.a.path, encoding="utf-8") as f:
            buku = f.read()
        self.assertNotIn(out["key"], buku)                                                              # hanya sha256
        self.assertIn(out["record"]["kunci_sha"], buku)
        self.assertEqual(self.a.pemilik(out["key"])["dompet"], w.address.lower())
        self.assertEqual(self.a.akun(out["key"])[1]["balance_atomic"], 0)

    @unittest.skipUnless(HAVE_ACC, "eth-account tidak terpasang")
    def test_replayed_expired_foreign_or_malformed_signatures_get_no_key(self):
        w, lain = Account.create(), Account.create()
        pesan = am.pesan_kunci(w.address, NOW)
        ok = {"wallet": w.address, "ts": NOW, "signature": uk.tanda_pesan(w, pesan)}
        self.assertEqual(self.a.buat_kunci(ok)[0], 201)
        self.assertEqual(self.a.buat_kunci(ok)[0], 409)                                                 # pesan bertanda tangan dipakai ulang
        lama = NOW - am.PARAMS_AKUN["pesan_ttl_s"] - 1
        self.assertEqual(self.a.buat_kunci({"wallet": w.address, "ts": lama, "signature": uk.tanda_pesan(w, am.pesan_kunci(w.address, lama))})[0], 401)
        self.assertEqual(self.a.buat_kunci({"wallet": w.address, "ts": NOW + 1, "signature": uk.tanda_pesan(lain, am.pesan_kunci(w.address, NOW + 1))})[0], 401)
        for rusak in ({"wallet": "bukan", "ts": NOW, "signature": ok["signature"]}, {"wallet": w.address, "ts": "1", "signature": ok["signature"]},
                      {"wallet": w.address, "ts": NOW + 2, "signature": "0x1234"}, {"wallet": w.address, "ts": True, "signature": ok["signature"]}):
            self.assertEqual(self.a.buat_kunci(rusak)[0], 400, rusak)
        self.assertEqual(self.a.buat_kunci({"wallet": w.address, "ts": NOW + 3, "signature": "0x" + "00" * 65})[0], 401)   # tidak bisa dipulihkan
        for i in range(4, 6):
            self.assertEqual(self.a.buat_kunci({"wallet": w.address, "ts": NOW + i, "signature": uk.tanda_pesan(w, am.pesan_kunci(w.address, NOW + i))})[0], 201)
        code, out = self.a.buat_kunci({"wallet": w.address, "ts": NOW + 9, "signature": uk.tanda_pesan(w, am.pesan_kunci(w.address, NOW + 9))})
        self.assertEqual((code, len(out["keys"])), (409, am.PARAMS_AKUN["kunci_maks"]))                 # maks 3 kunci aktif

    @unittest.skipUnless(HAVE_ACC, "eth-account tidak terpasang")
    def test_revoked_keys_stop_working_whether_the_wallet_or_the_key_holder_revokes(self):
        w = Account.create()
        k1 = self.a.buat_kunci({"wallet": w.address, "ts": NOW, "signature": uk.tanda_pesan(w, am.pesan_kunci(w.address, NOW))})[1]
        k2 = self.a.buat_kunci({"wallet": w.address, "ts": NOW + 1, "signature": uk.tanda_pesan(w, am.pesan_kunci(w.address, NOW + 1))})[1]
        pesan = am.pesan_cabut(w.address, k1["key_id"], NOW + 2)
        self.assertEqual(self.a.cabut_kunci({"wallet": w.address, "key_id": k1["key_id"], "ts": NOW + 2, "signature": uk.tanda_pesan(w, pesan)}, None)[0], 200)
        self.assertIsNone(self.a.pemilik(k1["key"]))
        self.assertEqual(self.a.akun(k1["key"])[0], 401)
        self.assertEqual(self.a.cabut_kunci({}, k2["key"])[0], 200)                                     # pemegang kunci mencabut sendiri
        self.assertEqual(self.a.potong(k2["key"], "fabius_verify", "c1")[0], 401)
        ulang = am.Akun(self.tmp, now=lambda: NOW)                                                      # cabut bertahan sesudah mulai ulang
        self.assertEqual((ulang.pemilik(k1["key"]), ulang.pemilik(k2["key"])), (None, None))


class PotongTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="akun-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.a = am.Akun(self.tmp, now=lambda: NOW, pulihkan=stub_pulihkan())
        self.k = kunci_baru(self.a)
        self.dipanggil = []

    def bangun(self, alat, args):
        self.dipanggil.append(alat)
        return {"alat": alat, "args": args, "isi": [1, 2, 3]}

    def test_insufficient_balance_is_refused_with_a_deposit_hint_and_changes_nothing(self):          # SK-M11
        n = len(self.a.recs)
        code, out = self.a.panggil(self.k, "fabius_signal", None, "c1", self.bangun)
        self.assertEqual(code, 402)
        self.assertIn("deposit", out)
        self.assertNotIn("data", out)
        self.assertEqual((self.dipanggil, len(self.a.recs), self.a.saldo.get(DOMPET, 0)), ([], n, 0))   # data tidak dibangun, tidak ada rekaman
        setor(self.a, 50_000)
        self.assertEqual(self.a.potong(self.k, "fabius_verify", "c2")[0], 200)
        for _ in range(9):
            self.a.potong(self.k, "fabius_verify", None)
        code, out = self.a.potong(self.k, "fabius_verify", "c3", cek=True)
        self.assertEqual((code, self.a.saldo[DOMPET]), (402, 0))

    def test_an_invalid_or_revoked_key_gets_no_data(self):                                              # SK-M12
        setor(self.a, 100_000)
        for k in (None, "fabk_" + "x" * 43, "bukan-kunci"):
            self.assertEqual(self.a.panggil(k, "fabius_signal", None, "c1", self.bangun)[0], 401)
            self.assertEqual(self.a.potong(k, "fabius_verify", "c1")[0], 401)
            self.assertEqual(self.a.akun(k)[0], 401)
        self.assertEqual(self.dipanggil, [])
        self.a.cabut_kunci({}, self.k)
        self.assertEqual(self.a.panggil(self.k, "fabius_signal", None, "c1", self.bangun)[0], 401)
        self.assertEqual((self.dipanggil, self.a.saldo[DOMPET]), ([], 100_000))

    def test_one_call_id_is_charged_once_and_a_retry_gets_the_same_answer(self):
        setor(self.a, 50_000)
        c1, o1 = self.a.panggil(self.k, "fabius_signal", {"x": 1}, "uji-1", self.bangun)
        c2, o2 = self.a.panggil(self.k, "fabius_signal", {"x": 1}, "uji-1", self.bangun)
        self.assertEqual((c1, c2, o2.get("repeat"), o1["response_sha"] == o2["response_sha"]), (200, 200, True, True))
        self.assertEqual((self.a.saldo[DOMPET], len(self.dipanggil)), (40_000, 1))
        self.assertEqual(o1["response_sha"], am.sha_json(o1["data"]))
        ulang = am.Akun(self.tmp, now=lambda: NOW, pulihkan=stub_pulihkan())                            # sesudah mulai ulang: tidak dipotong lagi
        code, out = ulang.panggil(self.k, "fabius_signal", {"x": 1}, "uji-1", self.bangun)
        self.assertEqual((code, ulang.saldo[DOMPET]), (409, 40_000))
        self.assertEqual(self.a.potong(self.k, "fabius_verify", "m-1", "0x" + "cd" * 32)[0], 200)
        self.assertTrue(self.a.potong(self.k, "fabius_verify", "m-1", "0x" + "cd" * 32)[1]["repeat"])
        self.assertEqual(sum(1 for r in self.a.recs if r["jenis"] == "potong"), 2)

    def test_data_that_cannot_be_built_is_not_charged(self):
        setor(self.a, 50_000)

        def rusak(alat, args):
            raise RuntimeError("berkas meja hilang")

        def belum(alat, args):
            raise am.TidakAda("the desk has no v2 cycle yet")

        def salah(alat, args):
            raise am.MasukanSalah("assets must be a list")
        self.assertEqual(self.a.panggil(self.k, "fabius_signal", None, "a", rusak)[0], 503)
        self.assertEqual(self.a.panggil(self.k, "fabius_signal", None, "b", belum)[0], 404)
        self.assertEqual(self.a.panggil(self.k, "fabius_data", {"assets": "x"}, "c", salah)[0], 400)
        self.assertEqual((self.a.saldo[DOMPET], sum(1 for r in self.a.recs if r["jenis"] == "potong")), (50_000, 0))

    def test_parallel_calls_never_overspend(self):
        setor(self.a, 50_000)                                                                          # cukup untuk tepat 5 sinyal
        hasil, kunci = [], threading.Lock()

        def satu(i):
            code, _ = self.a.panggil(self.k, "fabius_signal", None, f"par-{i}", self.bangun)
            with kunci:
                hasil.append(code)
        ts = [threading.Thread(target=satu, args=(i,)) for i in range(20)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        self.assertEqual((hasil.count(200), hasil.count(402), self.a.saldo[DOMPET]), (5, 15, 0))
        self.assertEqual(am.periksa_rantai(self.a.recs), ({DOMPET: 0}, []))

    def test_endpoints_only_charge_the_tools_they_serve(self):
        setor(self.a, 50_000)
        self.assertEqual(self.a.potong(self.k, "fabius_signal", "x")[0], 400)                           # alat gerbang lewat /account/call saja
        self.assertEqual(self.a.panggil(self.k, "fabius_verify", None, "x", self.bangun)[0], 400)       # alat MCP lewat /account/charge saja
        for alat in ("fabius_pricing", "fabius_dexscreener", "bukan", None):
            self.assertEqual(self.a.potong(self.k, alat, "x")[0], 400)
        self.assertEqual(self.a.potong(self.k, "fabius_verify", "spasi tidak boleh")[0], 400)
        self.assertEqual(self.a.potong(self.k, "fabius_verify", "ok-1", "bukan-sha")[0], 400)
        code, out = self.a.potong(self.k, "fabius_verify", "ok-2", cek=True)
        self.assertEqual((code, out["enough"], self.a.saldo[DOMPET]), (200, True, 50_000))               # cek tidak memotong


def kontribusi_contoh():
    rec = lambda s, k, skor, bot, kursi="aktif", status="ok": {"agent": f"v2:{s}", "kursi": kursi, "status": status,  # noqa: E731
                                                              "keputusan": {"k": k, "skor_bot": {"B1-TREND": skor, "B2-RS": -skor}, "bot": bot}}
    return [rec("a", 0.8, 60, "B1-TREND"), rec("b", 0.5, 20, "B1-TREND"), rec("c", 0.9, -40, "B2-RS"),
            rec("uji", 1.0, 100, "B1-TREND", kursi="uji"), rec("gagal", 1.0, 100, "B1-TREND", status="gagal")]


class DataTests(unittest.TestCase):
    def test_contribution_follows_the_r4_consensus_formula_and_counts_only_active_valid_seats(self):
        k = am.kontribusi(kontribusi_contoh(), "B1-TREND")
        self.assertEqual([x["agent"] for x in k], ["a", "b", "c"])                                     # kursi uji + jawaban gagal tidak dihitung
        self.assertEqual([x["points"] for x in k], [round(0.8 * 60 / 3, 4), round(0.5 * 20 / 3, 4), round(0.9 * -40 / 3, 4)])
        self.assertAlmostEqual(sum(x["points"] for x in k), (0.8 * 60 + 0.5 * 20 - 0.9 * 40) / 3, places=3)   # = nilai bot di konsensus2
        self.assertAlmostEqual(sum(x["share"] for x in k), 1.0, places=3)
        self.assertEqual(am.kontribusi(kontribusi_contoh(), None), [])

    def test_paid_tools_read_the_committed_desk_cycle_and_its_proof(self):
        tmp = tempfile.mkdtemp(prefix="akun-meja-")
        self.addCleanup(shutil.rmtree, tmp, True)
        g, _ = uk.gerbang_lokal(os.path.join(tmp, "repo"), 0)
        t = uk.isi_meja_contoh(g.meja_dir)
        g.now = lambda: t + 60
        s = am.bangun_data(g, "fabius_signal", {})
        self.assertEqual(s["cycle"], t)
        self.assertTrue(s["dominant_bot"] and s["proof"]["root"].startswith("0x") and s["record_hash"])
        e = am.bangun_data(g, "fabius_signal_explain", {})
        self.assertEqual((e["cycle"], e["dominant_bot"], e["features"]["snapshot_matches_cycle"]), (t, s["dominant_bot"], True))
        self.assertTrue(all(a["record_hash"] for a in e["agents"]))
        self.assertAlmostEqual(sum(x["share"] for x in e["contribution"]), 1.0, places=3)
        d = am.bangun_data(g, "fabius_data", {"assets": ["BTCUSDT"]})
        self.assertEqual(sorted(d["asset_features"]), ["BTCUSDT"])
        with self.assertRaises(am.MasukanSalah):
            am.bangun_data(g, "fabius_data", {"assets": ["btc; drop"]})
        kosong, _ = uk.gerbang_lokal(os.path.join(tmp, "kosong"), t + 60)
        with self.assertRaises(am.TidakAda):
            am.bangun_data(kosong, "fabius_signal", {})


class GerbangTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="akun-gerbang-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.g, self.rantai = uk.gerbang_lokal(os.path.join(self.tmp, "repo"), NOW)
        self.g.akun = am.Akun(os.path.join(self.tmp, "akun"), now=lambda: NOW, pulihkan=stub_pulihkan())

    def bayar(self, atomic, **over):
        import x402_sinyal as xs
        from engine.tests.test_x402_sinyal import payment
        p = payment(**{"a__permitted": {"token": uk.TOKEN, "amount": str(atomic)}, "e__amount": str(atomic), "e__asset": uk.TOKEN,
                       "a__witness": {"to": uk.PAYTO, "validAfter": str(NOW - 15)}, "a__deadline": str(NOW + 60), "e__deadline": str(NOW + 60), **over})
        self.assertEqual(p["payload"]["permit2Authorization"]["spender"], xs.PROXY)
        return base64.b64encode(json.dumps(p).encode()).decode()

    def test_every_account_route_is_hidden_while_the_switch_is_off(self):
        with mock.patch.dict(os.environ, {"FABIUS_F5": ""}):
            for parts in (["account"], ["account", "pricing"], ["account", "deposit", "100000"]):
                self.assertEqual(am.rute_get(self.g, self.g.akun, parts, {}, "x")[0], 404)
            for path in ("/account/key", "/account/call", "/account/charge", "/account/key/revoke"):
                self.assertEqual(am.rute_post(self.g, self.g.akun, path, {}, {})[0], 404)
        self.assertEqual((self.rantai.sent, self.g.akun.recs), ([], []))
        self.assertIsNone(am.rute_get(self.g, self.g.akun, ["desk"], {}, None))                        # rute lain tidak disentuh

    def test_a_deposit_without_payment_gets_402_for_exactly_that_amount(self):
        with mock.patch.dict(os.environ, NYALA):
            code, body, hdr = am.rute_get(self.g, self.g.akun, ["account", "deposit", "100000"], {}, None)
        self.assertEqual(code, 402)
        acc = json.loads(base64.b64decode(hdr["PAYMENT-REQUIRED"]).decode())["accepts"][0]
        self.assertEqual((acc["amount"], acc["asset"], acc["payTo"]), ("100000", uk.TOKEN, uk.PAYTO))
        self.assertTrue(acc["resource"].endswith("/account/deposit/100000"))
        for jumlah in ("49999", "1000001", "abc", "-5"):
            with mock.patch.dict(os.environ, NYALA):
                self.assertEqual(am.rute_get(self.g, self.g.akun, ["account", "deposit", jumlah], {}, None)[0], 400)

    @unittest.skipUnless(HAVE_ETH, "eth-abi tidak terpasang")
    def test_a_settled_deposit_is_credited_once_even_if_the_same_authorization_comes_again(self):
        hdr = self.bayar(100_000)
        with mock.patch.dict(os.environ, NYALA):
            c1, b1, h1 = am.rute_get(self.g, self.g.akun, ["account", "deposit", "100000"], {}, hdr)
            c2, b2, _ = am.rute_get(self.g, self.g.akun, ["account", "deposit", "100000"], {}, hdr)
        self.assertEqual((c1, b1["balance_atomic"], len(self.rantai.sent)), (200, 100_000, 1))
        self.assertIn("PAYMENT-RESPONSE", h1)
        self.assertEqual((c2, b2["repeat"], b2["balance_atomic"], len(self.rantai.sent)), (200, True, 100_000, 1))   # tanpa settle kedua
        self.assertEqual(self.g.akun.recs[0]["tx"], self.rantai.sent[0])

    @unittest.skipUnless(HAVE_ETH, "eth-abi tidak terpasang")
    def test_bad_deposits_credit_nothing(self):
        kasus = [("100000", self.bayar(100_000, a__witness={"to": DOMPET, "validAfter": str(NOW)}), 402),
                 ("100000", self.bayar(50_000), 402),                                                     # otorisasi untuk jumlah lain
                 ("100000", "bukan-base64", 400)]
        with mock.patch.dict(os.environ, NYALA):
            for jumlah, hdr, harap in kasus:
                self.assertEqual(am.rute_get(self.g, self.g.akun, ["account", "deposit", jumlah], {}, hdr)[0], harap)
        self.assertEqual((self.rantai.sent, self.g.akun.saldo), ([], {}))                                  # ditolak SEBELUM tx
        self.g.ev = type("TanpaTransfer", (), {"rpc": lambda s, m, p: "0x", "send": lambda s, pk, to, data, gas=None: {"status": "0x1", "transactionHash": "0xt", "logs": []}})()
        with mock.patch.dict(os.environ, NYALA):
            code, body, _ = am.rute_get(self.g, self.g.akun, ["account", "deposit", "100000"], {}, self.bayar(100_000))
        self.assertEqual((code, self.g.akun.saldo), (402, {}))                                              # tx tanpa Transfer = tidak dikreditkan
        self.assertIn("Transfer", json.dumps(body))


@unittest.skipUnless(HAVE_ACC and HAVE_ETH, "eth-account / eth-abi tidak terpasang")
class UjiKeringTests(unittest.TestCase):
    def test_deposit_key_paid_calls_and_balance_end_to_end_over_the_real_gate_handler(self):
        out = []
        self.assertEqual(uk.jalankan(out.append), 0, json.dumps(out, indent=1)[:3000])
        lap = out[0]
        self.assertTrue(lap["semua_sesuai"])
        self.assertEqual(lap["buku"]["masalah"], [])
        langkah = {x["langkah"]: x for x in lap["langkah"]}
        self.assertEqual(langkah["otorisasi sama dikirim ulang -> tidak dikreditkan lagi"]["tx_palsu"], 1)
        self.assertFalse(langkah["kunci API dari tanda tangan EIP-191"]["kunci_di_buku"])
        self.assertTrue(langkah["call_id sama -> jawaban sama, tanpa potongan kedua"]["sha_sama"])
        self.assertFalse(langkah["panggil sampai saldo kurang -> 402 + petunjuk deposit (SK-M11)"]["ada_data"])


def _ada_node() -> bool:
    try:
        v = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=20).stdout.strip().lstrip("v").split(".")
        return (int(v[0]), int(v[1])) >= (22, 6)
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return False


@unittest.skipUnless(_ada_node(), "Node >= 22.6 tidak ada: kontrak web tidak bisa dijalankan di mesin ini")
class WebContractTests(unittest.TestCase):
    def test_the_web_mcp_server_uses_the_same_prices_tool_lists_and_key_messages_as_the_gate(self):
        prog = ("import {HARGA, HARGA_MCP, GRATIS, DICABUT, FMT_KUNCI, FMT_CABUT, pesanKunci, pesanCabut, KUNCI_RE} from "
                + json.dumps("file:///" + os.path.join(ROOT, "web", "src", "lib", "akun.ts").replace(os.sep, "/")) + ";"
                "console.log(JSON.stringify({HARGA, HARGA_MCP, GRATIS, DICABUT, FMT_KUNCI, FMT_CABUT, k: pesanKunci('0xAbCd000000000000000000000000000000000001', 1791540700),"
                "c: pesanCabut('0xAbCd000000000000000000000000000000000001', 'k_0123456789ab', 7), re: KUNCI_RE.test('fabk_' + 'A'.repeat(43))}));")
        r = subprocess.run(["node", "--experimental-strip-types", "--no-warnings", "--input-type=module", "-e", prog], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        w = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual((w["HARGA"], w["HARGA_MCP"], sorted(w["GRATIS"]), sorted(w["DICABUT"])), (am.HARGA, am.HARGA_MCP, sorted(am.GRATIS), sorted(am.DICABUT)))
        self.assertEqual((w["FMT_KUNCI"], w["FMT_CABUT"]), (am.FMT_KUNCI, am.FMT_CABUT))
        self.assertEqual(w["k"], am.pesan_kunci("0xAbCd000000000000000000000000000000000001", 1791540700))
        self.assertEqual(w["c"], am.pesan_cabut("0xAbCd000000000000000000000000000000000001", "k_0123456789ab", 7))
        self.assertTrue(w["re"])


if __name__ == "__main__":
    unittest.main()

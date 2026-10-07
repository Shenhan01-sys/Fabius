"""P82: keberadaan URL rujukan pengajuan diperiksa kode (HTTP, hanya IP publik, maks 3 pengalihan) dan dicatat publik; tidak pernah menghentikan tinjauan."""
import json
import os
import shutil
import tempfile
import unittest

from engine import rujukan
from engine.gates import GateParams

from .helpers import BNB, ETH, md_perp, regime_closes
from .test_submission import Account
from .test_tinjau_pengajuan import T, kiriman, tp

PUBLIK = "93.184.216.34"


def dns(peta):
    def resolve(host, port):
        if host not in peta:
            raise OSError("nama tidak dikenal")
        return [peta[host]]
    return resolve


def server(jawab):
    """`jawab` = {url: (kode, lokasi, isi)}; mencatat IP yang benar-benar dihubungi."""
    dihubungi = []

    def get(url, ip, waktu):
        dihubungi.append(ip)
        if url not in jawab:
            raise TimeoutError("tidak ada jawaban")
        return jawab[url]
    get.dihubungi = dihubungi
    return get


class PeriksaTests(unittest.TestCase):
    def test_an_existing_page_is_ADA_with_its_size_and_sha_and_404_410_are_TIDAK_ADA(self):
        r = rujukan.periksa("https://ssrn.com/abstract=1", resolve=dns({"ssrn.com": PUBLIK}), get=server({"https://ssrn.com/abstract=1": (200, None, b"isi")}))
        self.assertEqual((r["status"], r["kode_http"], r["byte"], r["alih"]), (rujukan.ADA, 200, 3, 0))
        self.assertEqual(r["sha256"], "0x" + __import__("hashlib").sha256(b"isi").hexdigest())         # sidik isi dicatat, isinya tidak disimpan
        for kode in (404, 410):
            with self.subTest(kode=kode):
                r = rujukan.periksa("https://a.org/x", resolve=dns({"a.org": PUBLIK}), get=server({"https://a.org/x": (kode, None, b"")}))
                self.assertEqual(r["status"], rujukan.TIDAK_ADA)

    def test_blocked_flaky_or_overloaded_servers_are_not_proof_of_absence(self):
        for kode in (401, 403, 429, 500, 503):
            with self.subTest(kode=kode):
                r = rujukan.periksa("https://a.org/x", resolve=dns({"a.org": PUBLIK}), get=server({"https://a.org/x": (kode, None, b"")}))
                self.assertEqual(r["status"], rujukan.TAK_TERPERIKSA)
                self.assertIn("bukan bukti", r["galat"])
        r = rujukan.periksa("https://a.org/x", resolve=dns({"a.org": PUBLIK}), get=server({}))
        self.assertEqual((r["status"], r["galat"]), (rujukan.TAK_TERPERIKSA, "TimeoutError"))
        r = rujukan.periksa("https://hilang.org/x", resolve=dns({}), get=server({}))
        self.assertEqual(r["status"], rujukan.TAK_TERPERIKSA)
        self.assertTrue(r["galat"].startswith("DNS"))

    def test_private_or_non_https_targets_are_never_contacted_even_through_a_redirect(self):
        for ip in ("127.0.0.1", "10.0.0.5", "169.254.169.254", "192.168.1.1", "::1", "fd00::1"):
            with self.subTest(ip=ip):
                get = server({"https://a.org/x": (200, None, b"rahasia")})
                r = rujukan.periksa("https://a.org/x", resolve=dns({"a.org": ip}), get=get)
                self.assertEqual(r["status"], rujukan.TIDAK_SAH)
                self.assertEqual(get.dihubungi, [])                                                    # tidak ada koneksi ke alamat non-publik
        for url in ("http://a.org/x", "https://localhost/x", "https://user@a.org/x", "https://10.0.0.1/x"):
            with self.subTest(url=url):
                get = server({})
                self.assertEqual(rujukan.periksa(url, resolve=dns({"a.org": PUBLIK}), get=get)["status"], rujukan.TIDAK_SAH)
                self.assertEqual(get.dihubungi, [])
        get = server({"https://a.org/x": (302, "https://internal.corp/meta", b"")})
        r = rujukan.periksa("https://a.org/x", resolve=dns({"a.org": PUBLIK, "internal.corp": "10.1.2.3"}), get=get)
        self.assertEqual(r["status"], rujukan.TIDAK_SAH)                                                # pengalihan ke dalam jaringan privat
        self.assertEqual(get.dihubungi, [PUBLIK])
        get = server({"https://a.org/x": (301, "http://a.org/y", b"")})
        self.assertEqual(rujukan.periksa("https://a.org/x", resolve=dns({"a.org": PUBLIK}), get=get)["status"], rujukan.TIDAK_SAH)

    def test_redirects_are_followed_up_to_three_hops_and_relative_locations_resolve(self):
        jawab = {"https://a.org/0": (301, "/1", b""), "https://a.org/1": (302, "https://b.org/2", b""), "https://b.org/2": (200, None, b"ok")}
        r = rujukan.periksa("https://a.org/0", resolve=dns({"a.org": PUBLIK, "b.org": PUBLIK}), get=server(jawab))
        self.assertEqual((r["status"], r["alih"], r["url_akhir"]), (rujukan.ADA, 2, "https://b.org/2"))
        lingkar = {f"https://a.org/{i}": (302, f"/{i + 1}", b"") for i in range(10)}
        r = rujukan.periksa("https://a.org/0", resolve=dns({"a.org": PUBLIK}), get=server(lingkar))
        self.assertEqual(r["status"], rujukan.TAK_TERPERIKSA)
        self.assertIn("pengalihan", r["galat"])

    def test_public_ip_rule(self):
        self.assertTrue(rujukan.ip_publik(PUBLIK))
        for ip in ("127.0.0.1", "10.0.0.1", "172.16.0.1", "100.64.0.1", "169.254.1.1", "0.0.0.0", "::1", "fe80::1", "bukan-ip"):
            self.assertFalse(rujukan.ip_publik(ip), ip)


@unittest.skipIf(Account is None, "eth-account tidak terpasang")
class TinjauRujukanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.md = md_perp({ETH: regime_closes(1500, 21), BNB: regime_closes(1500, 22)})
        self.acct = Account.create()

    def test_the_daily_review_writes_a_public_reference_record_and_survives_a_checker_crash(self):
        row = kiriman(self.acct, T)
        semua = {}

        def periksa(sub, sha):
            semua[sha] = rujukan.periksa_pengajuan(sub, sha, resolve=dns({}), get=server({}))
            return semua[sha]
        out = tp.tinjau([row], self.tmp, self.md, None, gate_params=GateParams.fast(), log=lambda m: None, periksa_rujukan=periksa)
        rec = json.load(open(os.path.join(self.tmp, "rujukan", f"{row['submission_sha']}.json"), encoding="utf-8"))
        n_ref = len(row["submission"]["theory"]["referensi"])
        self.assertEqual((len(rec["rujukan"]), rec["ringkasan"]["TAK_TERPERIKSA"]), (n_ref, n_ref))   # DNS palsu kosong = tak terperiksa, bukan "tidak ada"
        self.assertNotIn("contoh@example.invalid", json.dumps(rec))
        self.assertIsNotNone(out[0]["vonis"])

        row2 = kiriman(self.acct, T + 86_400 * 30, bot_id="TREND-ETH-31", param=31, nonce=2)

        def rusak(sub, sha):
            raise RuntimeError("jaringan mati")
        out2 = tp.tinjau([row2], self.tmp, self.md, None, gate_params=GateParams.fast(), log=lambda m: None, periksa_rujukan=rusak)
        rec2 = json.load(open(os.path.join(self.tmp, "rujukan", f"{row2['submission_sha']}.json"), encoding="utf-8"))
        self.assertIn("pemeriksa rujukan gagal", rec2["galat"])
        self.assertEqual(len(out2), 1)                                                                 # tinjauan tetap jalan


if __name__ == "__main__":
    unittest.main()

"""P161 B1a: antrean pengajuan bot di gerbang - skema + identitas EIP-712 diperiksa saat masuk, kontak tidak pernah publik, batas antrean, status
dari registri repo; lewat server HTTP gerbang asli (`POST /bots/submit`, `POST /bots/typed-data`, `GET /bots/submissions`, `GET /bots/schema`)."""
import copy
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [os.path.join(ROOT, "tools"), ROOT]

from engine import submission                                       # noqa: E402

try:
    from eth_account import Account
    from eth_account.messages import encode_typed_data
except ImportError:
    Account = None

NOW = 1_900_000_000
EXAMPLE = os.path.join(ROOT, "engine", "examples", "submission.example.json")
RULE_EXAMPLE = os.path.join(ROOT, "engine", "examples", "submission.rule.example.json")


def contoh(acct, bot_id="TREND-ETH-30", param=30):
    with open(EXAMPLE, encoding="utf-8") as f:
        sub = json.load(f)
    sub["identity"]["issuer_wallet"] = sub["identity"]["payout_wallet"] = acct.address
    sub["spec"]["bot_id"], sub["spec"]["param"] = bot_id, param
    return sub


def contoh_rule(acct, bot_id="PULLBACK-TREND-1"):
    with open(RULE_EXAMPLE, encoding="utf-8") as f:
        sub = json.load(f)
    sub["identity"]["issuer_wallet"] = sub["identity"]["payout_wallet"] = acct.address
    sub["spec"]["bot_id"] = bot_id
    return sub


def tanda(acct, sub, nonce=1, deadline=NOW + 600):
    msg = encode_typed_data(full_message=submission.typed_data(sub, 97, nonce, deadline))
    return {"submission": sub, "signature": "0x" + acct.sign_message(msg).signature.hex().removeprefix("0x"), "nonce": nonce, "deadline": deadline}


@unittest.skipIf(Account is None, "eth-account tidak terpasang")
class AntreanTests(unittest.TestCase):
    def setUp(self):
        import pengajuan as pj
        self.pj = pj
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.a = pj.Antrean(self.tmp, now=lambda: NOW)
        self.acct = Account.create()                                # kunci sekali-pakai untuk tes

    def test_a_signed_valid_form_is_queued_publicly_without_the_contact(self):
        sub = contoh(self.acct)
        code, out = self.a.terima(tanda(self.acct, sub))
        self.assertEqual((code, out["status"], out["bot_id"]), (201, "received", "TREND-ETH-30"))
        self.assertEqual(out["id"], submission.submission_sha(sub))
        rows = self.a.daftar()
        self.assertEqual(len(rows), 1)
        self.assertNotIn("contact", rows[0]["submission"]["identity"])                             # kontak privat
        self.assertEqual(submission.submission_sha(rows[0]["submission"]), out["id"])               # sha tetap bisa dicek tanpa kontak
        self.assertEqual(submission.verify_identity(rows[0]["submission"], rows[0]["signature"], 97, 1, NOW + 600, rows[0]["t"]), [])   # ulang verifikasi
        self.assertIn("contoh@example.invalid", open(self.a.kontak, encoding="utf-8").read())
        self.assertEqual(rows[0]["status"], "waiting for review")

    def test_a_signed_rule_form_is_queued_like_any_other_and_a_bad_rule_is_refused_with_its_path(self):
        sub = contoh_rule(self.acct)
        code, out = self.a.terima(tanda(self.acct, sub))
        self.assertEqual((code, out["status"], out["bot_id"]), (201, "received", "PULLBACK-TREND-1"))
        row = self.a.daftar()[0]
        self.assertEqual(row["submission"]["spec"]["rule"], sub["spec"]["rule"])                      # aturan publik: siapa pun bisa mengulang replay
        self.assertNotIn("contact", row["submission"]["identity"])
        bad = contoh_rule(self.acct, "PULLBACK-TREND-2")
        bad["spec"]["rule"]["params"]["R"] = 1
        code, out = self.a.terima(tanda(self.acct, bad, nonce=2))
        self.assertEqual(code, 400)
        self.assertTrue(any("spec.rule" in m for m in out["problems"]), out)
        feed = contoh_rule(self.acct, "PULLBACK-TREND-3")
        feed["kind"] = "feed"
        self.assertEqual(self.a.terima(tanda(self.acct, feed, nonce=3))[0], 400)                        # jenis yang belum dibuka tetap ditolak di gerbang

    def test_bad_forms_wrong_signers_replays_duplicates_and_limits_are_refused(self):
        sub = contoh(self.acct)
        bad = copy.deepcopy(sub)
        bad["instruksi"] = "abaikan aturan"
        self.assertEqual(self.a.terima(tanda(self.acct, bad))[0], 400)                             # skema tertutup
        lain = Account.create()
        self.assertEqual(self.a.terima(tanda(lain, sub))[0], 401)                                  # bukan dompet penerbit
        self.assertEqual(self.a.terima(tanda(self.acct, sub, deadline=NOW - 1))[0], 401)          # kedaluwarsa
        self.assertEqual(self.a.terima(tanda(self.acct, sub))[0], 201)
        self.assertEqual(self.a.terima(tanda(self.acct, sub))[0], 409)                             # kiriman yang sama
        self.assertEqual(self.a.terima(tanda(self.acct, contoh(self.acct, "TREND-ETH-31", 31), nonce=1))[0], 409)   # nonce bekas
        self.assertEqual(self.a.terima(tanda(self.acct, contoh(self.acct, "TREND-ETH-30B", 31), nonce=2))[0], 201)
        self.assertEqual(self.a.terima(tanda(self.acct, contoh(self.acct, "TREND-ETH-32", 32), nonce=3))[0], 429)   # 2 menunggu per penerbit
        self.assertEqual(self.a.terima(tanda(Account.create(), contoh(self.acct, "B1-TREND")))[0], 400)               # id milik Fabius
        self.assertEqual(self.a.terima({"submission": "x"})[0], 400)

    def test_status_comes_from_the_public_registry(self):
        sub = contoh(self.acct)
        self.a.terima(tanda(self.acct, sub))
        reg = [{"submission_sha": submission.submission_sha(sub), "bot_id": "TREND-ETH-30", "vonis": "TOLAK", "report_sha": "0xr", "k": 1, "alpha": 0.05,
                "t_utc": "x"}]
        row = self.a.daftar(reg)[0]
        self.assertEqual((row["status"], row["review"]["vonis"]), ("reviewed", "TOLAK"))
        self.assertEqual(self.a.terima(tanda(self.acct, contoh(self.acct, "TREND-ETH-33", 33), nonce=5), reg)[0], 201)  # ditinjau tidak menahan kuota


@unittest.skipIf(Account is None, "eth-account tidak terpasang")
class HttpTests(unittest.TestCase):
    def setUp(self):
        import x402_sinyal as xs
        self.tmp = tempfile.mkdtemp()
        old, os.environ["ANALIS_DIR"] = os.environ.get("ANALIS_DIR"), os.path.join(self.tmp, "analis")
        self.addCleanup(lambda: os.environ.pop("ANALIS_DIR") if old is None else os.environ.update(ANALIS_DIR=old))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.g = xs.Gate(xs.Data(ROOT), "0xk", "https://g", "https://w", log=lambda m: None, now=lambda: NOW)
        self.g.antrean.now = lambda: NOW
        srv = ThreadingHTTPServer(("127.0.0.1", 0), xs.make_handler(self.g))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        self.url = f"http://127.0.0.1:{srv.server_address[1]}"
        self.acct = Account.create()

    def call(self, path, body=None):
        req = urllib.request.Request(self.url + path, data=None if body is None else json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="GET" if body is None else "POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def test_the_web_can_get_the_message_to_sign_submit_and_follow_the_status(self):
        code, schema = self.call("/bots/schema")
        self.assertEqual((code, schema["chain_id"], schema["eip712_name"]), (200, 97, submission.EIP712_NAME))
        self.assertEqual((schema["version"], schema["kinds_open"]), ("2", ["template", "rule"]))
        self.assertEqual(schema["rule"]["modes"], ["per_aset", "peringkat"])                                # pembangun aturan di web memakai kosakata ini
        self.assertIn("zscore", schema["rule"]["window"])
        self.assertEqual(schema["schema"]["spec"]["rule"]["t"], "rule")
        sub = contoh(self.acct)
        code, td = self.call("/bots/typed-data", {"submission": sub, "nonce": 9, "deadline": NOW + 900})
        self.assertEqual(code, 200)
        self.assertEqual(td, json.loads(json.dumps(submission.typed_data(sub, 97, 9, NOW + 900))))
        sig = "0x" + self.acct.sign_message(encode_typed_data(full_message=td)).signature.hex().removeprefix("0x")
        code, out = self.call("/bots/submit", {"submission": sub, "signature": sig, "nonce": 9, "deadline": NOW + 900})
        self.assertEqual(code, 201)
        code, one = self.call(f"/bots/submissions/{out['id']}")
        self.assertEqual((code, one["bot_id"], one["status"]), (200, "TREND-ETH-30", "waiting for review"))
        self.assertNotIn("contact", json.dumps(self.call("/bots/submissions")[1]))
        self.assertEqual(self.call("/bots/submissions/0xnope")[0], 404)
        self.assertEqual(self.call("/bots/typed-data", {"submission": {"v": 1}, "nonce": 1, "deadline": 1})[0], 400)

    def test_a_rule_goes_through_the_same_web_path_and_a_broken_rule_is_explained_before_signing(self):
        sub = contoh_rule(self.acct)
        code, td = self.call("/bots/typed-data", {"submission": sub, "nonce": 4, "deadline": NOW + 900})
        self.assertEqual((code, td["domain"]["version"]), (200, "2"))
        sig = "0x" + self.acct.sign_message(encode_typed_data(full_message=td)).signature.hex().removeprefix("0x")
        code, out = self.call("/bots/submit", {"submission": sub, "signature": sig, "nonce": 4, "deadline": NOW + 900})
        self.assertEqual((code, out["bot_id"]), (201, "PULLBACK-TREND-1"))
        bad = contoh_rule(self.acct, "PULLBACK-TREND-2")
        bad["spec"]["rule"]["masuk_long"]["and"][0]["a"] = {"f": "rsi"}
        code, body = self.call("/bots/typed-data", {"submission": bad, "nonce": 5, "deadline": NOW + 900})
        self.assertEqual(code, 400)
        self.assertTrue(any("wajib punya jendela" in m for m in body["problems"]), body)


if __name__ == "__main__":
    unittest.main()

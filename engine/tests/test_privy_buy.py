"""P138e (F-D101): /buy langsung dari chat - dompet Privy user menandatangani lewat API server Privy (session signer); tools/privy_server.py +
tools/x402_sinyal.py::tg_buy_privy. HTTP Privy, chain, dan Telegram dipalsukan."""
import base64
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
try:
    import cryptography                                             # noqa: F401
    import eth_abi                                                  # noqa: F401
    HAVE = True
except ImportError:
    HAVE = False

import privy_server as pv                                           # noqa: E402
import x402_sinyal as xs                                            # noqa: E402

TOKEN, PAYTO, ADDR = "0x" + "fa" * 20, "0x" + "fc" * 20, "0x" + "ab" * 20
NOW = 1_791_200_000
DAY = 86_400_000
T0 = 1_790_812_800_000


def keypair():
    from cryptography.hazmat.primitives import serialization as s
    from cryptography.hazmat.primitives.asymmetric import ec
    k = ec.generate_private_key(ec.SECP256R1())
    return "wallet-auth:" + base64.b64encode(k.private_bytes(s.Encoding.DER, s.PrivateFormat.PKCS8, s.NoEncryption())).decode(), k.public_key()


def verify(pub, sig_b64: str, payload: bytes) -> bool:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    try:
        pub.verify(base64.b64decode(sig_b64), payload, ec.ECDSA(hashes.SHA256()))
        return True
    except InvalidSignature:
        return False


@unittest.skipUnless(HAVE, "cryptography/eth-abi tidak terpasang")
class PrivyClientTests(unittest.TestCase):
    def test_typed_data_signing_carries_a_verifiable_authorization_signature_over_the_canonical_request(self):
        key, pub = keypair()
        calls = []

        def http(method, url, headers, body):
            calls.append((method, url, headers, body))
            return 200, {"method": "eth_signTypedData_v4", "data": {"signature": "0x" + "11" * 64 + "00", "encoding": "hex"}}
        p = pv.Privy("app", "secret", key, http=http)
        typed = {"domain": {"name": "Permit2"}, "types": {"X": []}, "primaryType": "X", "message": {"a": "1"}}
        self.assertTrue(p.sign_typed_data("wal1", typed).startswith("0x11"))
        method, url, h, body = calls[0]
        self.assertEqual((method, url), ("POST", "https://api.privy.io/v1/wallets/wal1/rpc"))
        self.assertEqual(body["params"]["typed_data"]["primary_type"], "X")
        self.assertEqual(h["Authorization"], "Basic " + base64.b64encode(b"app:secret").decode())
        self.assertTrue(h["User-Agent"].startswith("fabius-x402/"))                   # tanpa ini: Cloudflare 403 "error code: 1010"
        payload = pv.canonical({"version": 1, "method": "POST", "url": url, "body": body, "headers": {"privy-app-id": "app"}})
        self.assertTrue(verify(pub, h["privy-authorization-signature"], payload))
        self.assertFalse(verify(pub, h["privy-authorization-signature"], payload + b" "))

    def test_unknown_telegram_users_are_none_and_errors_carry_the_status(self):
        p = pv.Privy("app", "s", None, http=lambda *a: (404, {}))
        self.assertIsNone(p.user_by_telegram(7))
        p = pv.Privy("app", "s", None, http=lambda *a: (500, {"error": "x"}))
        with self.assertRaises(pv.PrivyError):
            p.user_by_telegram(7)
        self.assertEqual(pv.Privy.embedded_wallet({"linked_accounts": [{"type": "email"}, {"type": "wallet", "id": "w", "address": ADDR, "chain_type": "ethereum",
                                                                                         "wallet_client_type": "privy"}]}), ("w", ADDR))


class FakePrivy:
    def __init__(self, user=True, deny=False):
        self.user, self.deny, self.signed = user, deny, []

    def user_by_telegram(self, uid):
        return {"linked_accounts": [{"type": "wallet", "id": "wal1", "address": ADDR, "chain_type": "ethereum", "wallet_client_type": "privy"}]} if self.user else None

    def sign_typed_data(self, wid, typed):
        if self.deny:
            raise pv.PrivyError(403, {"error": "not authorized"}, "tanda tangan")
        self.signed.append(typed)
        return "0x" + "22" * 64 + "01"                                                   # v = 1 -> harus jadi 28


class FakeEv:
    def __init__(self, bal):
        self.bal = bal

    def call_decode(self, to, sig, types, values, out):
        return (self.bal,) if sig.startswith("balanceOf") else (3,)


@unittest.skipUnless(HAVE, "cryptography/eth-abi tidak terpasang")
class DirectBuyTests(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.repo, "ledger", "paper"))
        os.makedirs(os.path.join(self.repo, "deployments"))
        with open(os.path.join(self.repo, "ledger", "paper", "B1-TREND.jsonl"), "w", encoding="utf-8") as f:
            print(json.dumps({"type": "genesis", "bot_id": "B1-TREND"}), file=f)
            print(json.dumps({"type": "tick", "asof": T0, "asof_date": "2026-10-01", "signal_ids": [], "targets": {"XRPUSDT": 1.0}}), file=f)
        with open(os.path.join(self.repo, "deployments", "97.json"), "w", encoding="utf-8") as f:
            json.dump({"x402_sinyal": {"token": TOKEN, "facilitator": PAYTO}, "m3": {"committer": "0x" + "11" * 20},
                       "contracts": {"SignalAnchor": "0x" + "a1" * 20, "LockRegistry": "0x" + "a2" * 20}}, f)
        self.sent = []

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def gate(self, privy, bal):
        g = xs.Gate(xs.Data(self.repo), "0xk", "https://g", "https://w", ev=FakeEv(bal), tg_token="t", log=lambda m: None, now=lambda: NOW)
        g.privy = privy
        g.deliver_tg = lambda chat, body: self.sent.append((chat, body))
        return g

    def test_a_consented_wallet_pays_the_exact_bill_from_chat_and_receives_the_package(self):
        got = {}
        g = self.gate(FakePrivy(), 10 ** 6)

        def handle(bot, bar, hdr, tg):
            pay = json.loads(base64.b64decode(hdr))
            got["pay"], got["why"] = pay, xs.check_payment(pay, TOKEN, PAYTO, 10_000, NOW)
            return 200, {"bot": bot, "bar": bar, "targets": {}}, {}
        g.handle_signal = handle
        txt, button = xs.tg_reply(g, 99, "/buy", True, 42)
        self.assertEqual((txt, button), (None, None))
        self.assertIsNone(got["why"])                                                      # lolos pemeriksaan gerbang yang sama dengan pembeli HTTP
        self.assertEqual(got["pay"]["payload"]["signature"][-2:], "1c")                    # v 1 -> 28
        self.assertEqual(self.sent[0][0], 99)
        self.assertEqual(g.privy.signed[0]["message"]["witness"]["to"], PAYTO)             # dibangun gerbang, bukan input user

    def test_no_wallet_low_balance_and_missing_consent_each_say_what_to_do(self):
        txt, button = xs.tg_reply(self.gate(FakePrivy(user=False), 10 ** 6), 99, "/buy", True, 42)
        self.assertIn("not linked to a Fabius wallet", txt)
        self.assertEqual(button[0], "Open Fabius")
        txt, _ = xs.tg_reply(self.gate(FakePrivy(), 5), 99, "/buy", True, 42)
        self.assertIn("/topup", txt)
        txt, button = xs.tg_reply(self.gate(FakePrivy(deny=True), 10 ** 6), 99, "/buy", True, 42)
        self.assertIn("not allowed", txt)
        self.assertTrue(button[1].endswith("?izin=1"))
        self.assertEqual(self.sent, [])


def jwt(key, claims: dict) -> str:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec, utils
    enc = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()                    # noqa: E731
    h, p = enc(json.dumps({"alg": "ES256", "typ": "JWT"}).encode()), enc(json.dumps(claims).encode())
    r, s_ = utils.decode_dss_signature(key.sign(f"{h}.{p}".encode(), ec.ECDSA(hashes.SHA256())))
    return f"{h}.{p}." + enc(r.to_bytes(32, "big") + s_.to_bytes(32, "big"))


def p256():
    from cryptography.hazmat.primitives import serialization as ser
    from cryptography.hazmat.primitives.asymmetric import ec
    k = ec.generate_private_key(ec.SECP256R1())
    return k, k.public_key().public_bytes(ser.Encoding.PEM, ser.PublicFormat.SubjectPublicKeyInfo).decode()


CLAIMS = {"iss": "privy.io", "aud": "app", "sub": "did:privy:u1", "exp": NOW + 600, "iat": NOW}


@unittest.skipUnless(HAVE, "cryptography/eth-abi tidak terpasang")
class AccessTokenTests(unittest.TestCase):
    def test_only_an_unexpired_privy_token_for_this_app_signed_by_its_key_is_accepted(self):
        k, pem = p256()
        self.assertEqual(pv.verify_access_token(jwt(k, CLAIMS), "app", pem, NOW)["sub"], "did:privy:u1")
        other, _ = p256()
        for tok in (jwt(other, CLAIMS), jwt(k, {**CLAIMS, "aud": "app-lain"}), jwt(k, {**CLAIMS, "exp": NOW}),
                    jwt(k, {**CLAIMS, "iss": "evil"}), "bukan.jwt", jwt(k, CLAIMS)[:-4] + "AAAA"):
            with self.assertRaises(pv.PrivyError):
                pv.verify_access_token(tok, "app", pem, NOW)


@unittest.skipUnless(HAVE, "cryptography/eth-abi tidak terpasang")
class ReasoningAccessTests(unittest.TestCase):
    """P145 (F-D104): alasan lengkap agent analis di web = login Privy + >= 1 sinyal dibeli dalam 7 hari dari dompet akun itu."""

    def setUp(self):
        from engine.tests.test_x402_sinyal import tulis_pilihan
        self.repo = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.repo, "ledger", "paper"))
        os.makedirs(os.path.join(self.repo, "deployments"))
        with open(os.path.join(self.repo, "deployments", "97.json"), "w", encoding="utf-8") as f:
            json.dump({"x402_sinyal": {"token": TOKEN, "facilitator": PAYTO}, "m3": {"committer": "0x" + "11" * 20},
                       "contracts": {"SignalAnchor": "0x" + "a1" * 20, "LockRegistry": "0x" + "a2" * 20, "SelectionAnchor": "0x" + "a3" * 20}}, f)
        self.key, pem = p256()
        self.t = NOW
        user = {"id": "did:privy:u1", "linked_accounts": [{"type": "google_oauth"}, {"type": "wallet", "address": "0xAbAb" + "ab" * 18, "chain_type": "ethereum"}]}

        def http(method, url, headers, body):
            if url.endswith("/api/v1/apps/app"):
                return 200, {"verification_key": pem}
            if url.endswith("/v1/users/did:privy:u1"):
                return 200, user
            return 404, {}
        self.g = xs.Gate(xs.Data(self.repo), "0xk", "https://g", "https://w", log=lambda m: None, now=lambda: self.t)
        self.g.privy = pv.Privy("app", "s", None, http=http)
        self.g.analis_dir = os.path.join(self.repo, "data", "analis")
        self.g.buys_path = os.path.join(self.repo, "data", "pembelian.jsonl")
        tulis_pilihan(self.g.analis_dir, NOW + 3600)

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def test_signed_in_buyers_get_the_full_reasoning_and_everyone_else_is_told_what_to_do(self):
        bearer = "Bearer " + jwt(self.key, CLAIMS)
        self.assertEqual(self.g.analis_lengkap(None)[0], 401)
        code, body = self.g.analis_lengkap(bearer)
        self.assertEqual(code, 402)                                                       # login tapi belum pernah beli
        self.assertEqual(body["beli"], "https://w/buy")
        self.assertNotIn("RAHASIA", json.dumps(body))
        self.g.record_buy("B1-TREND", "2026-10-05", ADDR, "0xtx", 10_000)                  # ADDR = alamat user (huruf besar/kecil beda)
        code, body = self.g.analis_lengkap(bearer)
        self.assertEqual(code, 200)
        self.assertIn("RAHASIA-ALASAN glm", json.dumps(body))
        self.assertEqual(body["akses"]["pembelian_terakhir"]["tx"], "0xtx")
        self.assertEqual(body["selection_anchor"], "0x" + "a3" * 20)
        self.t = NOW + 8 * 86_400                                                          # > 7 hari sesudah beli: akses habis
        self.assertEqual(self.g.analis_lengkap("Bearer " + jwt(self.key, {**CLAIMS, "exp": self.t + 600}))[0], 402)


if __name__ == "__main__":
    unittest.main()

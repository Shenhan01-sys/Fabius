"""P138a (F-D100): gerbang x402 per sinyal (tools/x402_sinyal.py) + harga terkunci (engine/harga.py). Chain, tx, dan Telegram dipalsukan."""
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
    import eth_abi                                                  # noqa: F401
    HAVE_ETH = True
except ImportError:
    HAVE_ETH = False

import x402_sinyal as xs                                            # noqa: E402
from engine import harga                                            # noqa: E402
from engine.tests.test_fd16 import ledger as fd16_ledger, wobble    # noqa: E402

TOKEN = "0x" + "fa" * 20
PAYTO = "0x" + "fc" * 20
PAYER = "0x" + "be" * 20
NOW = 1_791_200_000
DAY = 86_400_000
T0 = 1_790_812_800_000                                              # 2026-10-01T00:00Z


def payment(**over):
    a = {"permitted": {"token": TOKEN, "amount": "10000"}, "from": PAYER, "spender": xs.PROXY, "nonce": "7", "deadline": str(NOW + 60),
         "witness": {"to": PAYTO, "validAfter": str(NOW - 15)}}
    ext = {"from": PAYER, "asset": TOKEN, "spender": xs.PERMIT2, "amount": "10000", "nonce": "0", "deadline": str(NOW + 60),
           "signature": "0x" + "11" * 64 + "1b", "version": "1"}
    for k, v in over.items():
        tgt, key = k.split("__")
        (a if tgt == "a" else ext)[key] = v
    return {"x402Version": 2, "payload": {"signature": "0x" + "22" * 64 + "1c", "permit2Authorization": a},
            "extensions": {"eip2612GasSponsoring": {"info": ext}}}


def transfer_log(token=TOKEN, frm=PAYER, to=PAYTO, amount=10000):
    pad = lambda x: "0x" + "0" * 24 + x[2:]                         # noqa: E731
    return {"address": token, "topics": [xs.TRANSFER_TOPIC, pad(frm), pad(to)], "data": hex(amount)}


class FakeEv:
    def __init__(self, logs=None, status="0x1", bal=0):
        self.logs = [transfer_log()] if logs is None else logs
        self.status, self.bal, self.sent = status, bal, []

    def rpc(self, method, params):
        return "0x"

    def send(self, pk, to, data, gas=None):
        self.sent.append((to, data))
        return {"status": self.status, "transactionHash": "0xtx", "logs": self.logs}

    def call_decode(self, to, sig, types, values, out):
        return (self.bal,)


class PureTests(unittest.TestCase):
    @unittest.skipUnless(HAVE_ETH, "eth-abi tidak terpasang")
    def test_settle_selector_is_the_one_read_from_the_proven_chain_transaction(self):
        import x402_gate as xg
        from eth_utils import keccak
        self.assertEqual("0x" + keccak(text=xs.SETTLE_SIG)[:4].hex(), "0xfa340378")                  # input tx 0xb6093e59 (dibaca 5 Okt)
        self.assertEqual(xg.settle_selector(), "0xfa340378")
        self.assertEqual(xs.settle_calldata(payment())[:4].hex(), "fa340378")

    def test_payment_is_checked_on_the_signed_authorization_not_on_what_the_client_echoes(self):
        ok = lambda p: xs.check_payment(p, TOKEN, PAYTO, 10000, NOW)    # noqa: E731
        self.assertIsNone(ok(payment()))
        cases = {"token bukan FAB": payment(a__permitted={"token": "0x" + "ab" * 20, "amount": "10000"}),
                 "jumlah": payment(a__permitted={"token": TOKEN, "amount": "1"}),
                 "witness.to": payment(a__witness={"to": PAYER, "validAfter": str(NOW)}),        # membayar diri sendiri
                 "spender": payment(a__spender="0x" + "cd" * 20),
                 "berbeda": payment(e__from="0x" + "ee" * 20),
                 "kedaluwarsa": payment(a__deadline=str(NOW - 1))}
        for want, p in cases.items():
            self.assertIn(want, ok(p) or "", want)

    def test_only_a_transfer_of_the_exact_price_to_pay_to_counts_as_paid(self):
        self.assertTrue(xs.paid_in_receipt({"logs": [transfer_log()]}, TOKEN, PAYER, PAYTO, 10000))
        for bad in (transfer_log(amount=9999), transfer_log(to=PAYER), transfer_log(token="0x" + "ab" * 20)):
            self.assertFalse(xs.paid_in_receipt({"logs": [bad]}, TOKEN, PAYER, PAYTO, 10000))

    def test_telegram_links_are_signed_and_expire(self):
        s = b"s" * 32
        t = xs.tg_link(s, 42, "B1-TREND", "2026-10-03", NOW)
        self.assertEqual(xs.tg_parse(s, t, NOW + 10)["c"], 42)
        self.assertIsNone(xs.tg_parse(s, t[:-1] + ("0" if t[-1] != "0" else "1"), NOW))
        self.assertIsNone(xs.tg_parse(b"x" * 32, t, NOW))
        self.assertIsNone(xs.tg_parse(s, t, NOW + xs.TG_TTL_S + 1))


class ClientTests(unittest.TestCase):
    @unittest.skipUnless(HAVE_ETH, "eth-account tidak terpasang")
    def test_the_client_reads_payment_headers_case_insensitively(self):
        """5 Okt: edge Railway menulis `payment-required` huruf kecil; klien dengan dict biasa tidak melihat tagihan sama sekali."""
        import email.message
        import urllib.error
        from unittest import mock
        import x402_client as xc
        h = email.message.Message()
        h["payment-required"] = "abc"
        err = urllib.error.HTTPError("https://x/sinyal/B1", 402, "Payment Required", h, None)
        err.read = lambda: b"{}"
        with mock.patch("urllib.request.urlopen", side_effect=err):
            code, hdr, _ = xc.http("https://x/sinyal/B1")
        self.assertEqual((code, hdr.get("PAYMENT-REQUIRED")), (402, "abc"))


class PriceTests(unittest.TestCase):
    def test_the_locked_table_matches_the_code_and_early_numbers_never_raise_the_price(self):
        self.assertEqual(harga.status()["state"], "TERKUNCI")
        led = {"X": fd16_ledger(wobble(8, 0.003, 0.0005), n_signals=8)}
        for r in led["X"]:
            if r.get("type") == "tick":
                r["asof_date"] = f"2026-10-{1 + (int(r['asof']) - int(led['X'][1]['asof'])) // DAY:02d}"
        last = [r["asof_date"] for r in led["X"] if r.get("type") == "tick"][-1]
        q = harga.harga_bar("X", last, led, {}, {})
        self.assertEqual(q["teaser"]["label"], "awal - belum bermakna")
        self.assertEqual(q["atomic"], 10_000)                                                  # angka awal tinggi tetap harga dasar

    def test_the_table_steps_for_measured_bots(self):
        t = lambda pct, fd="TIDAK LOLOS": {"confidence_pct": pct, "label": "terukur", "fd16": fd}   # noqa: E731
        got = [harga.harga_dari_teaser(t(p))[0] for p in (55, 60, 74, 75, 89, 95)]
        self.assertEqual(got, [10_000, 50_000, 50_000, 250_000, 250_000, 250_000])
        self.assertEqual(harga.harga_dari_teaser(t(95, "LOLOS"))[0], 1_000_000)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.repo, "ledger", "paper"))
        os.makedirs(os.path.join(self.repo, "deployments"))
        with open(os.path.join(self.repo, "ledger", "paper", "B1-TREND.jsonl"), "w", encoding="utf-8") as f:
            print(json.dumps({"type": "genesis", "bot_id": "B1-TREND"}), file=f)
            for i in range(2):
                print(json.dumps({"type": "tick", "asof": T0 + i * DAY, "asof_date": f"2026-10-0{i + 1}", "signal_ids": ["0xs1"],
                                  "targets": {"XRPUSDT": 0.0625, "BTCUSDT": 0.0625}}), file=f)
        with open(os.path.join(self.repo, "deployments", "97.json"), "w", encoding="utf-8") as f:
            json.dump({"x402_sinyal": {"token": TOKEN, "facilitator": PAYTO}, "m3": {"committer": "0x" + "11" * 20},
                       "contracts": {"SignalAnchor": "0x" + "a1" * 20, "LockRegistry": "0x" + "a2" * 20}}, f)
        self.logs, self.tg = [], []

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def gate(self, ev):
        g = xs.Gate(xs.Data(self.repo), "0xkunci", "https://gerbang.example", "https://web.example", ev=None, tg_token="t",
                    log=self.logs.append, now=lambda: NOW)
        g.ev = ev
        g.views = lambda cfg: (None, None)
        g.tg_send = lambda chat, text, button=None: self.tg.append((chat, text))
        return g

    def test_no_payment_gets_402_with_the_frozen_price_and_a_teaser_without_details(self):
        code, body, hdr = self.gate(FakeEv()).handle_signal("B1-TREND", None, None, None)
        self.assertEqual(code, 402)
        req = json.loads(base64.b64decode(hdr["PAYMENT-REQUIRED"]).decode())
        acc = req["accepts"][0]
        self.assertEqual((acc["amount"], acc["asset"], acc["payTo"], acc["extra"]["name"]), ("10000", TOKEN, PAYTO, "Fabius Credit"))
        self.assertIn("/sinyal/B1-TREND/2026-10-02", acc["resource"])
        self.assertNotIn("XRPUSDT", json.dumps(body))

    @unittest.skipUnless(HAVE_ETH, "eth-abi tidak terpasang")
    def test_a_valid_payment_is_settled_proven_from_the_receipt_and_the_package_delivered_also_to_telegram(self):
        ev = FakeEv()
        g = self.gate(ev)
        link = xs.tg_link(g.tg_secret, 99, "B1-TREND", "2026-10-02", NOW)
        b64 = base64.b64encode(json.dumps(payment()).encode()).decode()
        code, body, hdr = g.handle_signal("B1-TREND", None, b64, link)
        self.assertEqual(code, 200, body)
        self.assertEqual(body["targets"], {"XRPUSDT": 0.0625, "BTCUSDT": 0.0625})
        self.assertEqual(body["pembayaran"]["tx"], "0xtx")
        self.assertEqual(len(ev.sent), 1)
        self.assertEqual(self.tg[0][0], 99)
        self.assertIn("XRPUSDT", self.tg[0][1])

    @unittest.skipUnless(HAVE_ETH, "eth-abi tidak terpasang")
    def test_a_paid_package_is_still_delivered_when_the_details_cannot_be_read(self):
        g = self.gate(FakeEv())
        g.data.series = lambda bot: (_ for _ in ()).throw(OSError("bar hilang"))
        code, body, _ = g.handle_signal("B1-TREND", None, base64.b64encode(json.dumps(payment()).encode()).decode(), None)
        self.assertEqual(code, 200)
        self.assertNotIn("rincian", body)
        self.assertEqual(body["targets"], {"XRPUSDT": 0.0625, "BTCUSDT": 0.0625})
        self.assertTrue(any("tak terbaca" in x for x in self.logs))

    @unittest.skipUnless(HAVE_ETH, "eth-abi tidak terpasang")
    def test_bad_payments_and_receipts_without_the_transfer_deliver_nothing(self):
        b64 = base64.b64encode(json.dumps(payment(a__witness={"to": PAYER, "validAfter": str(NOW)})).encode()).decode()
        ev = FakeEv()
        code, body, _ = self.gate(ev).handle_signal("B1-TREND", None, b64, None)
        self.assertEqual((code, ev.sent), (402, []))                                            # ditolak SEBELUM tx
        ev2 = FakeEv(logs=[])
        code, body, _ = self.gate(ev2).handle_signal("B1-TREND", None, base64.b64encode(json.dumps(payment()).encode()).decode(), None)
        self.assertEqual(code, 402)
        self.assertIn("Transfer", json.dumps(body))
        self.assertNotIn("targets", body)

    @unittest.skipUnless(HAVE_ETH, "eth-abi tidak terpasang")
    def test_the_faucet_relays_fab_once_a_day_only_to_wallets_that_need_it(self):
        cfg = {"token": TOKEN}
        self.assertEqual(self.gate(FakeEv()).faucet("bukan-alamat", cfg)[0], 400)
        rich = self.gate(FakeEv(bal=xs.FAUCET_IF_BELOW))
        self.assertEqual(rich.faucet(PAYER, cfg)[1]["dikirim"], 0)
        g = self.gate(FakeEv(bal=0))
        self.assertEqual(g.faucet(PAYER, cfg)[0], 200)
        self.assertEqual(g.faucet(PAYER, cfg)[0], 429)

    def test_the_telegram_teaser_opens_the_mini_app_with_a_signed_link_and_no_signal_details(self):
        g = self.gate(FakeEv())
        txt, button = xs.tg_reply(g, 7, "/signal b1-trend")
        self.assertIn("0.01 FAB", txt)
        self.assertNotIn("XRPUSDT", txt)
        self.assertTrue(button[1].startswith("https://web.example/beli/B1-TREND?tg="))
        self.assertEqual(xs.tg_parse(g.tg_secret, button[1].split("?tg=")[1], NOW)["c"], 7)
        txt, button = xs.tg_reply(g, -100, "/buy B1-TREND", private=False)                        # grup: tanpa tombol Mini App
        self.assertIsNone(button)
        self.assertIn("private chat", txt)
        self.assertEqual(xs.tg_reply(g, 7, "/help")[0], xs.HELP)


if __name__ == "__main__":
    unittest.main()

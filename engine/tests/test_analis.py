"""P141-P142 (F-D102): agent analis rumah (tools/analis.py) - masukan deterministik, jawaban tervalidasi, komit sekali per bar, hash alasan cocok.
Model, chain, dan tx dipalsukan; tidak ada panggilan jaringan."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
try:
    import eth_abi                                                  # noqa: F401
    from eth_account import Account
    HAVE_ETH = True
except ImportError:
    HAVE_ETH = False

import analis as an                                                 # noqa: E402

NOW = 1_791_170_000                                                 # 2026-10-05 ±03:13Z
SEL = "0x" + "c0" * 20


class ParseTests(unittest.TestCase):
    def test_a_valid_pick_is_extracted_from_surrounding_text(self):
        c = an.parse('thinking... {"bot": "b1-trend", "keyakinan": 62, "alasan": "trend", "risiko": "reversal"} done', ["B1-TREND", "B3-CARRY"])
        self.assertEqual((c["bot"], c["keyakinan"]), ("B1-TREND", 62))

    def test_unknown_bots_and_bad_confidence_are_refused_not_guessed(self):
        for txt in ('{"bot": "B9", "keyakinan": 50}', '{"bot": "B1-TREND", "keyakinan": 101}', "no json at all"):
            with self.assertRaises((ValueError, TypeError)):
                an.parse(txt, ["B1-TREND"])

    def test_the_input_is_deterministic_and_the_prompt_lists_only_forward_bots(self):
        m1, m2 = an.masukan(ROOT, an.next_close(NOW)), an.masukan(ROOT, an.next_close(NOW))
        self.assertEqual(an.sha(m1), an.sha(m2))
        p = an.prompt(m1)
        for b in m1["bot"]:
            self.assertIn(b, p)
        self.assertEqual(an.next_close(NOW) % 86_400, 0)
        self.assertGreater(an.next_close(NOW), NOW)


class FakeEv:
    def __init__(self, picked=False, ok=True):
        self.picked, self.ok, self.sent = picked, ok, []

    def call_decode(self, to, sig, types, values, out):
        return ((b"B1-TREND".ljust(32, b"\0"), 50, b"\x01" * 32, 1 if self.picked else 0),)

    def send(self, pk, to, data, gas=None, value=0):
        self.sent.append((to, data))
        return {"status": "0x1" if self.ok else "0x0", "transactionHash": "0xtx"}


@unittest.skipUnless(HAVE_ETH, "eth-abi/eth-account tidak terpasang")
class RoundTests(unittest.TestCase):
    def setUp(self):
        self.acct = Account.create()
        k = self.acct.key.hex()
        self.env = {"QWENCLOUD_API_KEY": "kunci-uji", "ANALIS_GLM_PRIVATE_KEY": k if k.startswith("0x") else "0x" + k}
        self.cfg = {"selection": SEL, "agents": {"glm": {"agent_id": 2558, "wallet": self.acct.address}}}
        self.out = tempfile.mkdtemp()
        self.logs = []

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def post(self, reply):
        def f(url, headers, body, timeout):
            self.body = body
            return {"choices": [{"message": {"content": reply}}]}
        return f

    def run_(self, ev, reply):
        with mock.patch.dict(os.environ, self.env), mock.patch.object(an, "ANALIS_ENV", os.path.join(self.out, "tidak-ada.env")):
            return an.run_round(ROOT, self.cfg, ev, NOW, True, log=self.logs.append, post=self.post(reply), out_dir=self.out)

    def test_a_pick_is_committed_once_with_the_hash_of_the_published_reasoning(self):
        ev = FakeEv()
        res = self.run_(ev, '{"bot": "B1-TREND", "keyakinan": 62, "alasan": "trend", "risiko": "reversal"}')
        r = [x for x in res if x["agent"] == "glm"][0]
        self.assertEqual((r["status"], r["bot"], r["keyakinan"]), ("dikomit", "B1-TREND", 62))
        self.assertEqual(r["reasonHash"], an.sha(r["alasan"]))
        self.assertEqual((self.body["model"], self.body["reasoning_effort"]), ("deepseek-v4.1-flash", "high"))   # slot glm: builder 5 Okt
        self.assertEqual((r["alasan"]["model"], r["alasan"]["nama"]), ("deepseek-v4.1-flash", "Fabius Analyst · DeepSeek V4.1 Flash"))
        to, data = ev.sent[0]
        self.assertEqual(to, SEL)
        from eth_abi import decode
        aid, close, bot, conf, rh = decode(["uint256", "uint64", "bytes32", "uint8", "bytes32"], bytes(data[4:]))
        self.assertEqual((aid, close, bot.rstrip(b"\0"), conf, "0x" + rh.hex()), (2558, an.next_close(NOW), b"B1-TREND", 62, r["reasonHash"]))
        saved = [json.loads(x) for x in open(os.path.join(self.out, f"{an.next_close(NOW)}.jsonl"), encoding="utf-8")]
        self.assertEqual(an.records([self.out])[0]["reasonHash"], saved[0]["reasonHash"])
        ev2 = FakeEv(picked=True)
        self.assertEqual([x["status"] for x in self.run_(ev2, "{}") if x["agent"] == "glm"], ["sudah"])
        self.assertEqual(ev2.sent, [])

    def test_a_bad_answer_means_no_pick_for_that_bar_and_nothing_is_sent(self):
        ev = FakeEv()
        res = self.run_(ev, "I think B1 is fine")
        self.assertEqual([x["status"] for x in res if x["agent"] == "glm"], ["gagal"])
        self.assertEqual(ev.sent, [])
        self.assertTrue(any("tidak memilih" in x for x in self.logs))

    def test_agents_outside_active_desk_seats_do_not_pick(self):
        ev = FakeEv()
        with mock.patch.dict(os.environ, self.env), mock.patch.object(an, "ANALIS_ENV", os.path.join(self.out, "tidak-ada.env")):
            res = an.run_round(ROOT, self.cfg, ev, NOW, True, log=self.logs.append, post=self.post("{}"), out_dir=self.out, boleh=lambda s: False)
        self.assertEqual([x["status"] for x in res if x["agent"] == "glm"], ["kursi uji"])                 # P162: tidak ada panggilan model, tidak ada tx
        self.assertEqual(ev.sent, [])

    def test_inactive_or_unregistered_agents_never_run(self):
        names = [a["slug"] for a in an.active_agents({"selection": SEL, "agents": {"claude": {"agent_id": 1, "wallet": "0x" + "11" * 20}}})]
        self.assertEqual(names, [])


if __name__ == "__main__":
    unittest.main()

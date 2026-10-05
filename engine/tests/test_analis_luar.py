"""P151 (F-D107): agent analis LUAR - ditemukan dari event Picked SelectionAnchor, kartu ERC-8004 (tokenURI), alasan diambil sesudah bar tutup dan
disimpan hanya bila hash + skema cocok; dinilai + tampil di papan tetapi TIDAK ikut menentukan bot aktif. Chain dan HTTP dipalsukan."""
import base64
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import analis as an                                                 # noqa: E402
import x402_sinyal as xs                                            # noqa: E402

SEL, IDN = "0x" + "5e" * 20, "0x" + "1d" * 20
DAY = 86_400
B = 1_791_331_200                                                   # 2026-10-07T00:00Z
NOW = B - 3_600                                                     # bar B masih terbuka


def b32(s: str) -> bytes:
    return s.encode().ljust(32, b"\0")


def data_uri(o: dict) -> str:
    return "data:application/json;base64," + base64.b64encode(json.dumps(o).encode()).decode()


class Chain:
    """SelectionAnchor + IdentityRegistry palsu: picks = {(agent, close): (bot, keyakinan, reasonHash)}, cards = {agent: tokenURI}."""

    def __init__(self, picks, cards, latest=1_000, max_range=None):
        self.picks, self.cards, self.latest, self.max_range, self.calls = picks, cards, latest, max_range, []

    def rpc(self, method, params):
        if method == "eth_blockNumber":
            return hex(self.latest)
        f = params[0]
        lo, hi = int(f["fromBlock"], 16), int(f["toBlock"], 16)
        self.calls.append((lo, hi))
        if self.max_range and hi - lo + 1 > self.max_range:
            raise RuntimeError("query returned more than 10000 results")
        out = []
        for i, (aid, close) in enumerate(sorted(self.picks)):
            blk = 150 + i * 10
            if lo <= blk <= hi:
                out.append({"topics": [an.PICKED_TOPIC, hex(aid), hex(close), "0x" + b32(self.picks[(aid, close)][0]).hex()], "blockNumber": hex(blk)})
        return out

    def call_decode(self, to, sig, types, values, out):
        if sig == "tokenURI(uint256)":
            return (self.cards[values[0]],)
        mine = sorted(c for (a, c) in self.picks if a == values[0])
        if sig == "barCount(uint256)":
            return (len(mine),)
        if sig == "barAt(uint256,uint256)":
            return (mine[values[1]],)
        if sig == "getPick(uint256,uint64)":
            bot, k, rh = self.picks[(values[0], values[1])]
            return ((b32(bot), k, bytes.fromhex(rh[2:]), values[1] - 7_200),)
        raise AssertionError(sig)


def alasan(aid: int, close: int, bot: str, **extra) -> dict:
    return {"agent_id": aid, "bar_close": close, "nama": f"Ext {aid}", "pilihan": {"bot": bot, "keyakinan": 55, "alasan": "trend", "risiko": "reversal"}, **extra}


class DiscoveryAndCardTests(unittest.TestCase):
    def test_agents_are_found_from_picked_events_incrementally_and_a_too_wide_range_is_split(self):
        ch = Chain({(7001, B): ("B3-CARRY", 50, "0x" + "aa" * 32), (2558, B): ("B1-TREND", 60, "0x" + "bb" * 32)}, {}, max_range=500)
        state = {}
        self.assertEqual(an.temukan_agent(ch, SEL, 100, state, step=2_000), [2558, 7001])
        self.assertEqual(state["blok"], 1_001)
        self.assertTrue(all(hi - lo + 1 <= 500 for lo, hi in ch.calls if (lo, hi) != ch.calls[0]))     # dipecah sampai RPC menerima
        n = len(ch.calls)
        an.temukan_agent(ch, SEL, 100, state)
        self.assertEqual(len(ch.calls), n)                                                              # tidak ada blok baru: tidak dipindai ulang

    def test_the_card_gives_the_name_and_an_https_reasons_template_and_anything_else_is_reported_not_trusted(self):
        good = data_uri({"name": "Ext One", "fabius": {"reasons": "https://ext.example/r/{bar_close}.json"}})
        ch = Chain({}, {1: good, 2: data_uri({"name": "No URL"}), 3: "http://plain.example/card.json",
                        4: data_uri({"name": "Bad", "fabius": {"reasons": "http://x/{bar_close}"}})})
        c = an.kartu_luar(ch, IDN, 1)
        self.assertEqual((c["nama"], c["alasan_url"], c["galat"]), ("Ext One", "https://ext.example/r/{bar_close}.json", None))
        c = an.kartu_luar(ch, IDN, 2)
        self.assertEqual((c["nama"], c["alasan_url"]), ("No URL", None))
        self.assertIn("fabius.reasons", c["galat"])
        self.assertIn("https", an.kartu_luar(ch, IDN, 3)["galat"])
        self.assertIsNone(an.kartu_luar(ch, IDN, 4)["alasan_url"])


class ReasoningTests(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.out, ignore_errors=True)

    def test_reasoning_is_kept_only_after_the_close_and_only_when_hash_and_content_match_the_on_chain_pick(self):
        closed = B - DAY
        ok = alasan(7001, closed, "B3-CARRY")
        lie = alasan(7002, closed, "B1-TREND")                                       # hash cocok dengan dirinya, tetapi bot != pilihan on-chain
        picks = [{"agent": "x7001", "agent_id": 7001, "bar_close": closed, "bot": "B3-CARRY", "keyakinan": 55, "reasonHash": an.sha(ok)},
                 {"agent": "x7002", "agent_id": 7002, "bar_close": closed, "bot": "B3-CARRY", "keyakinan": 55, "reasonHash": an.sha(lie)},
                 {"agent": "x7003", "agent_id": 7003, "bar_close": closed, "bot": "B3-CARRY", "keyakinan": 55, "reasonHash": "0x" + "cc" * 32},
                 {"agent": "x7001", "agent_id": 7001, "bar_close": B, "bot": "B3-CARRY", "keyakinan": 55, "reasonHash": an.sha(alasan(7001, B, "B3-CARRY"))}]
        served = {7001: ok, 7002: lie, 7003: alasan(7003, closed, "B3-CARRY")}
        fetched, logs = [], []

        def fetch(url):
            fetched.append(url)
            return json.dumps(served[int(url.split("/")[3])]).encode()
        kartu = {i: {"alasan_url": f"https://ext.example/{i}/{{bar_close}}.json"} for i in (7001, 7002, 7003)}
        self.assertEqual(an.alasan_luar(picks, kartu, self.out, NOW, fetch=fetch, log=logs.append), 1)
        self.assertNotIn(f"https://ext.example/7001/{B}.json", fetched)                # bar terbuka: tidak diambil
        recs = an.records([self.out])
        self.assertEqual([(r["agent"], r["luar"], r["alasan"]["pilihan"]["alasan"]) for r in recs], [("x7001", True, "trend")])
        self.assertTrue(any("x7002" in m and "DITOLAK" in m for m in logs))
        self.assertTrue(any("x7003" in m and "reasonHash" in m for m in logs))
        self.assertEqual(an.alasan_luar(picks, kartu, self.out, NOW, fetch=fetch, log=logs.append), 0)    # gagal tidak dicoba lagi sebelum jeda


class GateTests(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        for d in ("ledger/paper", "ledger/bars", "deployments"):
            os.makedirs(os.path.join(self.repo, d))
        with open(os.path.join(self.repo, "ledger", "paper", "B1-TREND.jsonl"), "w", encoding="utf-8") as f:
            print(json.dumps({"type": "genesis", "bot_id": "B1-TREND"}), file=f)
            print(json.dumps({"type": "tick", "asof": (B - DAY) * 1000, "asof_date": "2026-10-06", "signal_ids": [], "targets": {"XRPUSDT": 1.0}}), file=f)
        with open(os.path.join(self.repo, "deployments", "97.json"), "w", encoding="utf-8") as f:
            json.dump({"contracts": {"SelectionAnchor": SEL}, "erc8004": {"identity": IDN, "selection": {"block": 100}},
                       "analis": {"agents": {"glm": {"agent_id": 2558, "wallet": "0x" + "11" * 20}}}}, f)
        rh = "0x" + "ab" * 32
        self.chain = Chain({(2558, B): ("B1-TREND", 60, rh), (7001, B): ("B3-CARRY", 90, rh), (7002, B): ("B3-CARRY", 90, rh),
                            (7001, B - DAY): ("B3-CARRY", 70, rh)},
                           {7001: data_uri({"name": "Ext One"}), 7002: data_uri({"name": "Ext Two"})})
        self.g = xs.Gate(xs.Data(self.repo), "0xk", "https://g", "https://w", ev=self.chain, log=lambda m: None, now=lambda: NOW)
        self.g.analis_dir = os.path.join(self.repo, "data", "analis")
        self.g.luar_dir = os.path.join(self.g.analis_dir, "luar")

    def tearDown(self):
        shutil.rmtree(self.repo, ignore_errors=True)

    def test_external_agents_are_ranked_but_a_sybil_majority_cannot_change_the_bot_fabius_trades(self):
        ak = self.g.aktif_now()
        self.assertEqual((ak["bar_close"], ak["bot"], ak["pilihan"]), (B, "B1-TREND", {2558: "B1-TREND"}))   # 2 suara luar B3 diabaikan
        papan = {r["agent_id"]: r for r in self.g.analis_view(max_age_s=0)["papan"]}
        self.assertEqual(set(papan), {2558, 7001, 7002})
        self.assertEqual((papan[7001]["nama"], papan[7001]["luar"], papan[2558]["luar"]), ("Ext One", True, False))

    def test_public_records_show_every_on_chain_pick_sealed_when_open_and_flagged_when_reasoning_was_never_published(self):
        recs = {(r["agent"], r["alasan"]["bar_close"]): r for r in self.g.analis_records()}
        self.assertIn("terkunci", recs[("x7002", B)]["alasan"])
        self.assertIn("not published", recs[("x7001", B - DAY)]["alasan"]["tidak_terbit"])
        self.assertTrue(recs[("x7001", B)]["luar"])
        self.assertEqual(recs[("x7001", B)]["alasan"]["nama"], "Ext One")
        txt, _ = xs.tg_reply(self.g, 7, "/analysts")
        self.assertIn("Ext One [external]", txt)
        self.assertIn("Ext Two, external", txt)


if __name__ == "__main__":
    unittest.main()

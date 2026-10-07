"""P81 (C-H): prediksi alamat `RevenueSplitter` di Python == alamat klon yang di-deploy `BotRegistry` di EVM, dan vektor bagi hasil == engine.

Arah lintas bahasa:
  - EVM -> Python: bagian `evm` di `test/fixtures/splitter_vectors.json` DICETAK FORGE dari klon yang benar-benar di-deploy
    (`tools/gen_splitter_vectors.py --evm`); tes di sini menghitung ulang alamatnya dengan `engine/splitter.py`.
  - Python -> EVM: bagian split / share / skenario / create2 dihasilkan engine; `forge test --match-contract "RevenueSplitterTest|BotRegistryTest"`
    memeriksanya di kontrak. Tes di sini menjaga fixture tetap sama dengan engine sekarang.
"""
import json
import os
import sys
import unittest

from engine import chain, economics, splitter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import gen_splitter_vectors as gsv                                   # noqa: E402

A = "0x" + "11" * 20
B = "0x" + "22" * 20
C = "0x" + "33" * 20
D = "0x" + "44" * 20
SPEC = "0x" + "ab" * 32


def _fixture() -> dict:
    with open(gsv.OUT, encoding="utf-8") as f:
        return json.load(f)


class PredictTests(unittest.TestCase):
    def test_prediction_matches_the_clone_forge_actually_deployed(self):
        evm = _fixture()["evm"]
        self.assertIn("forge test", evm["_sumber"])
        got = splitter.predict_splitter(evm["registry"], evm["implementation"], evm["botIdText"], evm["issuer"], evm["issuerPayee"],
                                        evm["specSha"])
        self.assertEqual(got, evm["deployed"])                                    # EIP-55 sama persis, bukan hanya huruf kecil
        self.assertEqual(chain.hex0x(splitter.splitter_salt(evm["botIdText"], evm["issuer"], evm["issuerPayee"], evm["specSha"])),
                         evm["salt"])
        self.assertEqual(chain.hex0x(splitter.bot_id_bytes(evm["botIdText"])), evm["botId"])
        self.assertEqual(gsv.evm_problems(evm), [])

    def test_create2_matches_the_eip1014_examples(self):
        z = "0x" + "00" * 20
        cases = [(z, bytes(32), b"\x00", "0x4D1A2e2bB4F88F0250f26Ffff098B0b30B26BF38"),
                 ("0xdeadbeef00000000000000000000000000000000", bytes(32), b"\x00", "0xB928f69Bb1D91Cd65274e3c79d8986362984fDA3"),
                 ("0x00000000000000000000000000000000deadbeef", bytes.fromhex("00" * 28 + "cafebabe"), bytes.fromhex("deadbeef" * 11),
                  "0x1d8bfDC5D46DC4f61D6b6115972536eBE6A8854C"),
                 (z, bytes(32), b"", "0xE33C0C7F7df4809055C3ebA6c09CFe4BaF1BD9e0")]
        for deployer, salt, code, want in cases:
            self.assertEqual(splitter.create2_address(deployer, salt, code), want)

    def test_clone_init_code_is_the_55_byte_eip1167_creation_code(self):
        code = splitter.clone_init_code(A)
        self.assertEqual(len(code), 55)
        self.assertEqual(code[20:40], bytes.fromhex("11" * 20))

    def test_salt_binds_issuer_payout_spec_and_bot(self):
        base = splitter.predict_splitter(A, B, "B1-TREND", C, D, SPEC)
        others = {splitter.predict_splitter(A, B, "B1-TREND", D, D, SPEC), splitter.predict_splitter(A, B, "B1-TREND", C, C, SPEC),
                  splitter.predict_splitter(A, B, "B1-TREND", C, D, "0x" + "cd" * 32), splitter.predict_splitter(A, B, "B2-RS", C, D, SPEC),
                  splitter.predict_splitter(B, B, "B1-TREND", C, D, SPEC), splitter.predict_splitter(A, C, "B1-TREND", C, D, SPEC)}
        self.assertNotIn(base, others)
        self.assertEqual(len(others), 6)

    def test_inputs_the_contract_rejects_never_get_an_address(self):
        z = "0x" + "00" * 20
        bad = [(z, B, "B1-TREND", C, D, SPEC), (A, z, "B1-TREND", C, D, SPEC), (A, B, "B1-TREND", z, D, SPEC), (A, B, "B1-TREND", C, z, SPEC),
               (A, B, "B1-TREND", C, D, "0x" + "00" * 32), (A, B, "", C, D, SPEC), (A, B, "X" * 33, C, D, SPEC), (A, B, "B1-TRÉND", C, D, SPEC),
               ("0x1234", B, "B1-TREND", C, D, SPEC), (A, B, "B1-TREND", C, D, "0xabc")]
        for args in bad:
            with self.assertRaises(ValueError, msg=repr(args)):
                splitter.predict_splitter(*args)


class VectorTests(unittest.TestCase):
    def test_fixture_matches_the_engine(self):
        on_disk = _fixture()
        self.assertEqual({k: v for k, v in on_disk.items() if k != "evm"}, gsv.build())
        self.assertIn("evm", on_disk)

    def test_split_vectors_sum_to_the_amount_with_dust_to_fabius(self):
        sp = _fixture()["split"]
        self.assertEqual(len(sp["amount"]), 98)
        for amount, bps, iss, fab in zip(sp["amount"], sp["issuerBps"], sp["issuer"], sp["fabius"]):
            amount, iss, fab = int(amount), int(iss), int(fab)
            self.assertEqual(iss + fab, amount)
            self.assertEqual(iss, amount * bps // economics.BPS)
        self.assertIn(2**256 - 1, [int(x) for x in sp["amount"]])

    def test_partial_releases_end_where_one_split_of_the_total_ends(self):
        sc = {s["nama"]: s for s in _fixture()["skenario"]}
        s = sc["rilis_bertahap_sama_dengan_satu_split"]
        total = sum(int(v) for op, v in zip(s["op"], s["nilai"]) if op == gsv.SETOR)
        self.assertEqual((int(s["issuerTotal"][-1]), int(s["fabiusTotal"][-1])), economics.split(total))
        cp, nocp = sc["turun_dengan_checkpoint"], sc["turun_tanpa_checkpoint"]
        self.assertEqual(int(cp["issuerTotal"][-1]), economics.split(1_001 + 333, 6_000)[0] + economics.split(999, 7_500)[0])
        self.assertEqual(int(nocp["issuerTotal"][-1]), economics.split(1_001, 6_000)[0] + economics.split(333 + 999, 7_500)[0])

    def test_share_vectors_follow_share_change_allowed(self):
        sh = _fixture()["share"]
        self.assertEqual(len(sh["old"]), 70)
        for old, new, ok in zip(sh["old"], sh["new"], sh["allowed"]):
            self.assertEqual(ok, new <= old)

    def test_scenario_that_raises_the_fabius_share_is_refused_by_the_model(self):
        m = gsv.SegmentModel(4_000)
        with self.assertRaises(ValueError):
            m.step(gsv.TURUN, 4_001)

    def test_generation_is_deterministic(self):
        self.assertEqual(json.dumps(gsv.build(), sort_keys=True), json.dumps(gsv.build(), sort_keys=True))


if __name__ == "__main__":
    unittest.main()

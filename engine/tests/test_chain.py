import hashlib
import random
import unittest

from engine import chain

try:
    from eth_utils import keccak as eth_keccak
except ImportError:                                    # tes pembanding opsional; vektor tetap di bawah
    eth_keccak = None

# Vektor diturunkan dari `cast keccak` (Foundry 1.5.1) dan eth_utils.keccak, 2 Okt 2026.
KECCAK_VECTORS = {
    b"": "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
    b"abc": "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45",
    b"The quick brown fox jumps over the lazy dog": "4d741b6f1eb29cb2a9b9911c82f56fa8d73b04959d3d9d222895df6c0b28aa15",
    b"a" * 135: "34367dc248bbd832f4e3e69dfaac2f92638bd0bbd18f2912ba4ef454919cf446",     # batas rate - 1 (padding 0x01 dan 0x80 bertemu)
    b"a" * 136: "a6c4d403279fe3e0af03729caada8374b5ca54d8065329a3ebcaeb4b60aa386e",     # tepat satu blok
    b"a" * 137: "d869f639c7046b4929fc92a4d988a8b22c55fbadb802c0c66ebcd484f1915f39",
    b"a" * 272: "cf7fcd4f705ee749930d19ca84561a9bf62516bd90a471545fa2f49fdc7e63c8",     # dua blok penuh
}

STRUCT_TYPES = ["uint8", "bytes32", "bytes32", "uint64", "bytes32", "uint8", "int256", "int256", "uint256", "bytes32"]


class KeccakTests(unittest.TestCase):
    def test_vectors(self):
        for msg, hx in KECCAK_VECTORS.items():
            self.assertEqual(chain.keccak256(msg).hex(), hx, msg[:20])

    def test_is_not_nist_sha3(self):
        self.assertNotEqual(chain.keccak256(b"abc"), hashlib.sha3_256(b"abc").digest())

    @unittest.skipIf(eth_keccak is None, "eth_utils tidak terpasang")
    def test_matches_eth_utils_for_all_lengths_up_to_300(self):
        for n in range(301):
            self.assertEqual(chain.keccak256(b"\xab" * n), eth_keccak(b"\xab" * n), n)


class AbiTests(unittest.TestCase):
    def struct_values(self):
        return [1, chain.ascii32("B1-TREND"), b"\x11" * 32, 1788220800, chain.ascii32("BTCUSDT"), 3, 62500000, -125000000,
                7763460000000, b"\x22" * 32]

    def test_struct_encoding_and_hashes_match_cast(self):
        enc = chain.abi_encode(STRUCT_TYPES, self.struct_values())
        self.assertEqual(len(enc), 320)
        self.assertEqual(chain.keccak256(enc).hex(), "5a83096b3448fa07904631e0d7f83808ed65b3adf0e2a87cba28266944da5352")
        self.assertEqual(chain.keccak256(enc + b"\x33" * 32).hex(), "c36a0eb7648a4f52159a28b02ad9f83039ea00231d46d27f7dc3e8f39b317057")

    def test_negative_int_is_twos_complement(self):
        self.assertEqual(chain.abi_encode(["int256"], [-1]).hex(), "ff" * 32)
        self.assertEqual(chain.abi_encode(["int256"], [1]).hex(), "00" * 31 + "01")

    def test_address_is_left_padded(self):
        w = chain.abi_encode(["address"], ["0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"])
        self.assertEqual(w.hex(), "000000000000000000000000" + "5aaeb6053f3e94c9b9a09f33669435e7ef1beaed")

    def test_rejects_out_of_range_dynamic_and_bad_lengths(self):
        for types, vals in ((["uint8"], [256]), (["uint64"], [-1]), (["int256"], [1 << 255]), (["bytes32"], [b"\x00" * 31]),
                            (["string"], ["x"]), (["bool", "bool"], [True]), (["uint8"], [True])):
            with self.assertRaises(ValueError, msg=str(types)):
                chain.abi_encode(types, vals)

    def test_ascii32(self):
        self.assertEqual(chain.ascii32("BTC").hex(), "425443" + "00" * 29)
        for bad in ("", "x" * 33, "é"):
            with self.assertRaises((ValueError, UnicodeEncodeError)):
                chain.ascii32(bad)

    def test_from_hex_is_strict(self):
        self.assertEqual(chain.from_hex("0x" + "ab" * 32), b"\xab" * 32)
        for bad in ("0x" + "ab" * 31, "ab" * 33, "0xzz", "0x" + "ab" * 31 + "  ", "0x" + "ab" * 31 + "\n\n", "0x" + " " * 64):
            with self.assertRaises(ValueError, msg=repr(bad)):          # bytes.fromhex diam-diam melewati spasi: harus ditolak di sini
                chain.from_hex(bad)


class ChecksumTests(unittest.TestCase):
    EIP55 = ["0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed", "0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359",
             "0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB", "0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb"]

    def test_eip55_vectors(self):
        for a in self.EIP55:
            self.assertEqual(chain.to_checksum_address(a.lower()), a)
            self.assertTrue(chain.is_checksum_address(a))

    def test_strict_rejects_wrong_case_lowercase_and_malformed(self):
        a = self.EIP55[0]
        swapped = a[:-1] + a[-1].swapcase()
        for bad in (a.lower(), swapped, a[2:], a + "00", "0x", "", None):
            self.assertFalse(chain.is_checksum_address(bad), bad)


def oz_verify(proof, root, leaf, keccak):
    """Pembanding mandiri: persis `MerkleProof.verify` OpenZeppelin (pasangan terurut)."""
    h = leaf
    for p in proof:
        h = keccak(h + p if h <= p else p + h)
    return h == root


class MerkleTests(unittest.TestCase):
    def leaves(self, n, seed=1):
        r = random.Random(seed)
        return [chain.keccak256(r.randbytes(16)) for _ in range(n)]

    def test_every_leaf_verifies_for_all_sizes(self):
        for n in range(1, 18):
            lv = self.leaves(n, n)
            root = chain.merkle_root(lv)
            for lf in lv:
                pr = chain.merkle_proof(lv, lf)
                self.assertTrue(chain.merkle_verify(pr, root, lf), (n, lf.hex()))
                self.assertTrue(oz_verify(pr, root, lf, chain.keccak256))

    def test_single_leaf_root_is_leaf_with_empty_proof(self):
        lv = self.leaves(1)
        self.assertEqual(chain.merkle_root(lv), lv[0])
        self.assertEqual(chain.merkle_proof(lv, lv[0]), [])

    def test_empty_is_zero_root(self):
        self.assertEqual(chain.merkle_root([]), b"\x00" * 32)

    def test_order_independent(self):
        lv = self.leaves(7)
        self.assertEqual(chain.merkle_root(lv), chain.merkle_root(list(reversed(lv))))

    def test_tamper_detected(self):
        lv = self.leaves(6)
        root = chain.merkle_root(lv)
        pr = chain.merkle_proof(lv, lv[2])
        self.assertFalse(chain.merkle_verify(pr, root, chain.keccak256(b"palsu")))
        self.assertFalse(chain.merkle_verify(pr[:-1], root, lv[2]))
        self.assertFalse(chain.merkle_verify(pr, chain.keccak256(b"akar lain"), lv[2]))
        with self.assertRaises(ValueError):
            chain.merkle_proof(lv, chain.keccak256(b"bukan daun"))

    def test_two_leaf_root_is_sorted_pair_hash(self):
        a, b = chain.keccak256(b"1"), chain.keccak256(b"2")
        lo, hi = sorted((a, b))
        self.assertEqual(chain.merkle_root([a, b]), chain.keccak256(lo + hi))


if __name__ == "__main__":
    unittest.main()

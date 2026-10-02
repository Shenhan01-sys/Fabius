"""Primitif on-chain tanpa dependensi: keccak256, penyandian ABI statis, pohon Merkle, checksum alamat EIP-55.

Kenapa ada di sini (keputusan 2 Okt 2026, "terapkan yang menurutmu bagus"): komit sinyal harus bisa DIVERIFIKASI di dalam
kontrak. Itu menuntut `keccak256` atas `abi.encode(struct, salt)` dan bukti Merkle bergaya OpenZeppelin (`MerkleProof.verify`),
bukan sha256 atas JSON. Hash spesifikasi bot (`BotSpec.sha`) tetap sha256 JSON kanonik (paritas dengan `tools/direction.py`;
orang bisa memeriksanya dengan `sha256sum`); ia hanya dibandingkan kesamaannya sebagai bytes32 dan tidak perlu keccak.

PERINGATAN: `hashlib.sha3_256` BUKAN keccak256 Ethereum (padding berbeda). Modul ini mengimplementasikan Keccak asli (padding
0x01). Diuji terhadap `cast keccak` (Foundry 1.5.1) dan `eth_utils.keccak` (tes melompati yang tak terpasang).
"""
from __future__ import annotations

from typing import List, Sequence

_MASK = (1 << 64) - 1
_RC = (
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
)
_ROT = ((0, 36, 3, 41, 18), (1, 44, 10, 45, 2), (62, 6, 43, 15, 61), (28, 55, 25, 21, 56), (27, 20, 39, 8, 14))
_RATE = 136                                   # byte; keccak256 = kapasitas 512 bit


def _rol(v: int, n: int) -> int:
    n %= 64
    return ((v << n) | (v >> (64 - n))) & _MASK if n else v


def _keccak_f(a: List[int]) -> None:
    for rc in _RC:
        c = [a[x] ^ a[x + 5] ^ a[x + 10] ^ a[x + 15] ^ a[x + 20] for x in range(5)]
        d = [c[(x - 1) % 5] ^ _rol(c[(x + 1) % 5], 1) for x in range(5)]
        for i in range(25):
            a[i] ^= d[i % 5]
        b = [0] * 25
        for x in range(5):
            for y in range(5):
                b[y + 5 * ((2 * x + 3 * y) % 5)] = _rol(a[x + 5 * y], _ROT[x][y])
        for y in range(5):
            row = b[5 * y:5 * y + 5]
            for x in range(5):
                a[x + 5 * y] = row[x] ^ ((~row[(x + 1) % 5]) & row[(x + 2) % 5])
        a[0] ^= rc


def keccak256(data: bytes) -> bytes:
    msg = bytearray(data)
    msg.append(0x01)                          # padding Keccak asli (SHA3 NIST memakai 0x06)
    while len(msg) % _RATE:
        msg.append(0)
    msg[-1] |= 0x80
    st = [0] * 25
    for off in range(0, len(msg), _RATE):
        for i in range(_RATE // 8):
            st[i] ^= int.from_bytes(msg[off + 8 * i:off + 8 * i + 8], "little")
        _keccak_f(st)
    return b"".join(st[i].to_bytes(8, "little") for i in range(4))


def hex0x(b: bytes) -> str:
    return "0x" + b.hex()


def from_hex(s: str, n: int = 32) -> bytes:
    """'0x...' atau '...' -> tepat n byte; selain itu ValueError (tidak diam-diam memotong atau mengisi)."""
    h = s[2:] if s[:2] in ("0x", "0X") else s
    if len(h) != 2 * n:
        raise ValueError(f"butuh {n} byte hex ({2 * n} karakter), dapat {len(h)} karakter")
    if any(c not in "0123456789abcdefABCDEF" for c in h):       # bytes.fromhex diam-diam melewati spasi
        raise ValueError("bukan hex murni")
    return bytes.fromhex(h)


# ---------------------------------------------------------------- ABI (hanya tipe statis)

def _uint(v: int, bits: int) -> bytes:
    if not isinstance(v, int) or isinstance(v, bool) or not 0 <= v < (1 << bits):
        raise ValueError(f"uint{bits} di luar rentang: {v!r}")
    return v.to_bytes(32, "big")


def _int(v: int, bits: int) -> bytes:
    if not isinstance(v, int) or isinstance(v, bool) or not -(1 << (bits - 1)) <= v < (1 << (bits - 1)):
        raise ValueError(f"int{bits} di luar rentang: {v!r}")
    return (v % (1 << 256)).to_bytes(32, "big")


def abi_encode(types: Sequence[str], values: Sequence[object]) -> bytes:
    """`abi.encode` untuk tipe STATIS saja: uintN, intN, bool, address, bytes32. Tipe dinamis ditolak (tak ada diam-diam salah)."""
    if len(types) != len(values):
        raise ValueError("jumlah tipe dan nilai berbeda")
    out = bytearray()
    for t, v in zip(types, values):
        if t.startswith("uint"):
            out += _uint(v, int(t[4:] or 256))
        elif t.startswith("int"):
            out += _int(v, int(t[3:] or 256))
        elif t == "bool":
            out += _uint(1 if v else 0, 256)
        elif t == "address":
            raw = from_hex(v, 20) if isinstance(v, str) else bytes(v)
            if len(raw) != 20:
                raise ValueError("address harus 20 byte")
            out += b"\x00" * 12 + raw
        elif t == "bytes32":
            b = from_hex(v, 32) if isinstance(v, str) else bytes(v)
            if len(b) != 32:
                raise ValueError("bytes32 harus 32 byte")
            out += b
        else:
            raise ValueError(f"tipe tidak didukung (hanya statis): {t}")
    return bytes(out)


def ascii32(s: str) -> bytes:
    """String ASCII -> bytes32 rata-kiri berisi nol di kanan (seperti `bytes32("BTCUSDT")` di Solidity)."""
    b = s.encode("ascii")
    if not 0 < len(b) <= 32:
        raise ValueError(f"ascii32: panjang 1..32, dapat {len(b)}")
    return b + b"\x00" * (32 - len(b))


# ---------------------------------------------------------------- EIP-55

def to_checksum_address(addr: str) -> str:
    h = from_hex(addr, 20).hex()
    dig = keccak256(h.encode("ascii")).hex()
    return "0x" + "".join(c.upper() if int(dig[i], 16) >= 8 else c for i, c in enumerate(h))


def is_checksum_address(addr: str) -> bool:
    """Ketat: bentuk `0x` + 40 hex DAN huruf besar-kecilnya sama persis dengan checksum EIP-55 (identitas harus jelas)."""
    try:
        return isinstance(addr, str) and addr[:2] == "0x" and addr == to_checksum_address(addr)
    except ValueError:
        return False


# ---------------------------------------------------------------- Merkle (cocok dengan OpenZeppelin MerkleProof)

def hash_pair(a: bytes, b: bytes) -> bytes:
    """keccak256 atas pasangan TERURUT (sama dengan `commutativeKeccak256` OZ): bukti tak perlu menyimpan kiri/kanan."""
    return keccak256(a + b if a <= b else b + a)


def _levels(leaves: Sequence[bytes]) -> List[List[bytes]]:
    level = sorted(leaves)
    levels = [level]
    while len(level) > 1:
        nxt = [hash_pair(level[i], level[i + 1]) for i in range(0, len(level) - 1, 2)]
        if len(level) % 2:
            nxt.append(level[-1])                # simpul ganjil naik tanpa di-hash; verifier OZ tidak peduli bentuk pohon
        levels.append(nxt)
        level = nxt
    return levels


def merkle_root(leaves: Sequence[bytes]) -> bytes:
    """Akar pohon atas daun (diurutkan: tak bergantung urutan masuk). Tanpa daun -> 32 byte nol ('bot diam' yang dikomit)."""
    if not leaves:
        return b"\x00" * 32
    return _levels(leaves)[-1][0]


def merkle_proof(leaves: Sequence[bytes], leaf: bytes) -> List[bytes]:
    levels = _levels(leaves)
    try:
        idx = levels[0].index(leaf)
    except ValueError:
        raise ValueError("daun tidak ada di pohon") from None
    proof: List[bytes] = []
    for level in levels[:-1]:
        sib = idx ^ 1
        if sib < len(level):
            proof.append(level[sib])
        idx //= 2
    return proof


def merkle_verify(proof: Sequence[bytes], root: bytes, leaf: bytes) -> bool:
    h = leaf
    for p in proof:
        h = hash_pair(h, p)
    return h == root

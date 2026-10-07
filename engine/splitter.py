"""Prediksi alamat `RevenueSplitter` (P81, C-H): `payTo` x402 untuk sinyal satu bot, dihitung SEBELUM klonnya dipasang.

Rumus yang sama dengan `contracts/BotRegistry.sol` + OpenZeppelin `Clones.predictDeterministicAddress` (EIP-1167 lewat CREATE2):
    salt      = keccak256(abi.encode(bytes32 botId, address issuer, address issuerPayee, bytes32 specSha))
    init_code = 3d602d80600a3d3981f3363d3d373d3d3d363d73 ‖ implementation ‖ 5af43d82803e903d91602b57fd5bf3   (55 byte)
    alamat    = keccak256(0xff ‖ registry ‖ salt ‖ keccak256(init_code))[12:]
`registry` = alamat BotRegistry (pabrik), `implementation` = `BotRegistry.implementation()`. Salt mengikat penerbit, dompet payout, dan
spesifikasi: alamat yang ditawarkan gerbang tidak bisa ditempati klon untuk penerbit lain.

Diuji terhadap vektor yang DICETAK FORGE dari klon yang benar-benar di-deploy (`test/fixtures/splitter_vectors.json` -> `evm`,
`tools/gen_splitter_vectors.py --evm`) dan terhadap contoh EIP-1014. Tanpa jaringan, tanpa dependensi (keccak dari `engine/chain.py`).

Masukan yang tidak akan pernah bisa di-deploy kontrak (alamat nol, botId kosong / > 32 byte, specSha nol) DITOLAK (ValueError), bukan diberi
alamat: dana yang dikirim ke alamat yang tidak bisa ditempati klon hilang selamanya (T8 SK-H1).
"""
from __future__ import annotations

from . import chain

CLONE_PREFIX = bytes.fromhex("3d602d80600a3d3981f3363d3d373d3d3d363d73")
CLONE_SUFFIX = bytes.fromhex("5af43d82803e903d91602b57fd5bf3")
ZERO32 = b"\x00" * 32
ZERO20 = b"\x00" * 20


def _addr(name: str, a: str) -> bytes:
    raw = chain.from_hex(a, 20)
    if raw == ZERO20:
        raise ValueError(f"{name} alamat nol: kontrak menolaknya, alamat payTo tidak akan pernah bisa di-deploy")
    return raw


def bot_id_bytes(bot_id: str) -> bytes:
    """botId seperti di LockRegistry/SignalAnchor: ASCII rata-kiri jadi bytes32 (`chain.ascii32`)."""
    return chain.ascii32(bot_id)


def clone_init_code(implementation: str) -> bytes:
    return CLONE_PREFIX + _addr("implementation", implementation) + CLONE_SUFFIX


def create2_address(deployer: str, salt: bytes, init_code: bytes) -> str:
    """EIP-1014: keccak256(0xff ‖ deployer ‖ salt ‖ keccak256(init_code))[12:], dikembalikan sebagai EIP-55."""
    if len(salt) != 32:
        raise ValueError("salt harus 32 byte")
    h = chain.keccak256(b"\xff" + chain.from_hex(deployer, 20) + salt + chain.keccak256(init_code))
    return chain.to_checksum_address(chain.hex0x(h[12:]))


def splitter_salt(bot_id: str, issuer: str, issuer_payee: str, spec_sha: str) -> bytes:
    """`BotRegistry.splitterSalt(botId, issuer, issuerPayee, specSha)`."""
    spec = chain.from_hex(spec_sha, 32)
    if spec == ZERO32:
        raise ValueError("specSha nol: kontrak menolaknya, alamat payTo tidak akan pernah bisa di-deploy")
    return chain.keccak256(chain.abi_encode(("bytes32", "address", "address", "bytes32"),
                                            (bot_id_bytes(bot_id), _addr("issuer", issuer), _addr("issuer_payee", issuer_payee), spec)))


def predict_splitter(registry: str, implementation: str, bot_id: str, issuer: str, issuer_payee: str, spec_sha: str) -> str:
    """Alamat klon `RevenueSplitter` untuk bot ini (= `BotRegistry.predictSplitter`), EIP-55. Masukan yang akan ditolak kontrak = ValueError:
    tidak ada alamat yang dihitung untuk klon yang tidak akan pernah bisa di-deploy."""
    salt = splitter_salt(bot_id, issuer, issuer_payee, spec_sha)
    return create2_address(chain.hex0x(_addr("registry", registry)), salt, clone_init_code(implementation))

"""EVM minimal untuk alat M3 (komit sinyal `tools/signal_commit.py`, setup `tools/m3_setup.py`, worker Railway): JSON-RPC dengan rotasi endpoint,
panggilan baca, estimasi gas, kirim + tunggu receipt, deploy.

Beda penting dengan `tools/verify_deploy.py`: modul ini TIDAK membaca berkas apa pun saat diimpor (verify_deploy membaca `.env` saat impor). Kunci selalu
diberikan pemanggil, dan tidak pernah dicetak atau dimasukkan ke pesan error.

Pelajaran yang diwarisi dari `verify_deploy.rpc` (terukur 25 Sep): (1) drpc/publicnode menolak User-Agent bawaan urllib (Cloudflare 1010) -> UA eksplisit;
(2) endpoint yang gagal diingat dan dilewati sisa proses; (3) error JSON-RPC (revert, hash tak dikenal) adalah JAWABAN server, bukan endpoint mati.
"""
from __future__ import annotations

import json
import time
import urllib.request
from typing import List, Optional, Sequence

from eth_abi import decode, encode
from eth_account import Account

DEFAULT_RPCS = ("https://bsc-testnet.publicnode.com", "https://bsc-testnet-rpc.publicnode.com", "https://bsc-testnet.drpc.org")
HEADERS = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Mozilla/5.0 (compatible; fabius-m3/1.0)"}
MIN_GAS_PRICE = 10**9          # sama dengan verify_deploy.send: BSC testnet kadang menjawab eth_gasPrice di bawah minimum validator
GAS_HEADROOM = 1.25


class RpcError(RuntimeError):
    """Server menjawab dengan error JSON-RPC (mis. revert pada eth_call/eth_estimateGas). `data` = data revert bila ada."""

    def __init__(self, msg: str, data: Optional[str] = None):
        super().__init__(msg)
        self.data = data


def keccak(b: bytes) -> bytes:
    from engine.chain import keccak256         # impor malas: modul ini bisa dipakai tanpa sys.path engine di pemanggil yang tidak butuh selector
    return keccak256(b)


def selector(sig: str) -> bytes:
    return keccak(sig.encode("ascii"))[:4]


def calldata(sig: str, types: Sequence[str] = (), values: Sequence[object] = ()) -> bytes:
    return selector(sig) + (encode(list(types), list(values)) if types else b"")


def error_name(data: Optional[str], errors: Sequence[str]) -> Optional[str]:
    """Nama custom error dari data revert (4 byte pertama), dicocokkan dengan daftar tanda tangan error kontrak."""
    if not data or len(data) < 10:
        return None
    head = data[2:10].lower()
    for e in errors:
        if selector(e).hex() == head:
            return e
    return None


class Evm:
    def __init__(self, urls: Sequence[str], chain_id: int, timeout: float = 15.0, receipt_wait_s: float = 120.0, poll_s: float = 2.0):
        self.urls: List[str] = [u for u in urls if u]
        if not self.urls:
            raise ValueError("tidak ada endpoint RPC")
        self.chain_id = chain_id
        self.timeout = timeout
        self.receipt_wait_s = receipt_wait_s
        self.poll_s = poll_s
        self._bad: set = set()
        self._cur = 0

    # ------------------------------------------------------------ JSON-RPC
    def rpc(self, method: str, params: list):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        order = [self.urls[self._cur]] + [u for i, u in enumerate(self.urls) if i != self._cur]
        order = [u for u in order if u not in self._bad] or list(self.urls)
        last = None
        for u in order:
            req = urllib.request.Request(u, data=body, headers=HEADERS)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    d = json.loads(r.read().decode())
            except Exception as e:  # noqa: BLE001 - jaringan/HTTP: endpoint ini dilewati, coba berikutnya
                last = e
                self._bad.add(u)
                continue
            if "error" in d:
                err = d["error"] or {}
                raise RpcError(str(err.get("message", err))[:220], err.get("data") if isinstance(err.get("data"), str) else None)
            self._cur = self.urls.index(u)
            return d["result"]
        raise RuntimeError(f"RPC {method} gagal di {len(self.urls)} endpoint: {type(last).__name__}: {str(last)[:120]}")

    @staticmethod
    def num(h) -> int:
        return int(h, 16) if h and h != "0x" else 0

    def chain_check(self) -> None:
        got = self.num(self.rpc("eth_chainId", []))
        if got != self.chain_id:
            raise RuntimeError(f"chainId RPC {got} != {self.chain_id}: berhenti sebelum mengirim apa pun")

    def call(self, to: str, data: bytes) -> bytes:
        out = self.rpc("eth_call", [{"to": to, "data": "0x" + data.hex()}, "latest"])
        return bytes.fromhex(out[2:]) if out and out != "0x" else b""

    def call_decode(self, to: str, sig: str, types: Sequence[str], values: Sequence[object], out_types: Sequence[str]):
        raw = self.call(to, calldata(sig, types, values))
        if not raw:
            raise RuntimeError(f"{sig}: jawaban kosong dari {to} (alamat salah / bukan kontrak?)")
        return decode(list(out_types), raw)

    def balance(self, addr: str) -> int:
        return self.num(self.rpc("eth_getBalance", [addr, "latest"]))

    def code_size(self, addr: str) -> int:
        c = self.rpc("eth_getCode", [addr, "latest"])
        return (len(c) - 2) // 2 if c else 0

    def code(self, addr: str) -> bytes:
        c = self.rpc("eth_getCode", [addr, "latest"])
        return bytes.fromhex(c[2:]) if c and c != "0x" else b""

    def nonce(self, addr: str, block: str = "pending") -> int:
        return self.num(self.rpc("eth_getTransactionCount", [addr, block]))

    def has_pending(self, addr: str) -> bool:
        """True bila ada transaksi dari `addr` yang belum masuk blok (jangan kirim yang baru: nonce bertumpuk = transaksi ganda)."""
        return self.nonce(addr, "pending") > self.nonce(addr, "latest")

    def gas_price(self) -> int:
        return max(self.num(self.rpc("eth_gasPrice", [])), MIN_GAS_PRICE)

    def block_timestamp(self) -> int:
        return self.num(self.rpc("eth_getBlockByNumber", ["latest", False])["timestamp"])

    def estimate(self, frm: str, to: Optional[str], data: bytes, value: int = 0) -> int:
        tx = {"from": frm, "data": "0x" + data.hex(), "value": hex(value)}
        if to:
            tx["to"] = to
        return self.num(self.rpc("eth_estimateGas", [tx]))

    # ------------------------------------------------------------ kirim
    def send(self, pk: str, to: Optional[str], data: bytes = b"", value: int = 0, gas: Optional[int] = None) -> dict:
        """Tanda tangani + kirim satu transaksi legacy (chainId), tunggu receipt. `to=None` = deploy. Mengembalikan receipt (dict RPC).
        Gas = estimasi x1,25 (revert ketahuan SEBELUM mengirim: RpcError dari estimateGas, nol gas terbakar)."""
        acct = Account.from_key(pk)
        if gas is None:
            gas = int(self.estimate(acct.address, to, data, value) * GAS_HEADROOM) + 10_000
        tx = {"chainId": self.chain_id, "nonce": self.nonce(acct.address), "gas": gas, "gasPrice": self.gas_price(), "value": value,
              "data": data}
        if to:
            from eth_utils import to_checksum_address   # eth-account menolak `to` huruf kecil semua (pelajaran verify_deploy.send)
            tx["to"] = to_checksum_address(to)
        signed = Account.sign_transaction(tx, pk)
        raw = signed.raw_transaction if hasattr(signed, "raw_transaction") else signed.rawTransaction
        h = self.rpc("eth_sendRawTransaction", ["0x" + bytes(raw).hex()])
        deadline = time.time() + self.receipt_wait_s
        while time.time() < deadline:
            r = self.rpc("eth_getTransactionReceipt", [h])
            if r:
                return r
            time.sleep(self.poll_s)
        raise RuntimeError(f"tx {h} belum masuk blok dalam {self.receipt_wait_s:.0f} detik (mempool/RPC?) - periksa sebelum mengirim ulang")


def address_of(pk: str) -> str:
    return Account.from_key(pk).address


def receipt_ok(r: dict) -> bool:
    return Evm.num(r.get("status")) == 1

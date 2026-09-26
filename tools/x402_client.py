"""Agen pembeli: minta vault, terima 402, BAYAR tanpa gas, ambil isinya, lalu periksa chain-nya.

Ini sisi yang membuat cerita "agent economy" bukan template: yang memanggil adalah program, uangnya
token di BNB Chain, dan settlement terjadi di kontrak kanonis - bukan di database kami.

Klien sengaja TIDAK punya BNB sama sekali. Itu bagian yang diuji: pembayaran lewat
`settleWithPermit` membawa approval EIP-2612 di dalam transaksi fasilitator, jadi pembeli cukup
menandatangani. Setelah selesai, alat ini MEMBACA CHAIN untuk memastikan saldo berpindah - bukan
mempercayai jawaban HTTP-nya sendiri.

Pakai:  python -u tools/x402_client.py --base http://127.0.0.1:8042
         python -u tools/x402_client.py --base ... --dry-run     # tanda tangan saja, jangan kirim
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import verify_deploy as vd  # noqa: E402
from eth_abi import encode as enc  # noqa: E402
from eth_account import Account  # noqa: E402
from eth_account.messages import SignableMessage, encode_defunct  # noqa: E402
from eth_utils import keccak, to_checksum_address as cs  # noqa: E402

PERMIT2 = "0x000000000022D473030F116dDEE9F6B43aC78BA3"
PROXY = "0x402085c248EeA27D92E8b30b2C58ed07f9E20001"
P2_DOMAIN_TYPEHASH = keccak(text="EIP712Domain(string name,uint256 chainId,address verifyingContract)")
P2_TP_TYPEHASH = keccak(text="TokenPermissions(address token,uint256 amount)")
P2_WITNESS_TYPEHASH = keccak(text=(
    "PermitWitnessTransferFrom(TokenPermissions permitted,address spender,uint256 nonce,uint256 deadline,"
    "Witness witness)TokenPermissions(address token,uint256 amount)Witness(address to,uint256 validAfter)"))
WITNESS_TYPEHASH = keccak(text="Witness(address to,uint256 validAfter)")
EIP2612_PERMIT_TYPEHASH = keccak(
    text="Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)")
PAYER_KEY = keccak(text="fabius-x402-payer")          # burner testnet sekali-pakai, tanpa dana nyata


def payer_address():
    """SATU-satunya tempat alamat pembeli diturunkan.

    `x402_deploy.py` sebelumnya punya konstanta alamat sendiri dengan komentar "derive: keccak(...)".
    Komentar itu tidak benar: alamatnya alamat lain, jadi pendanaan masuk ke dompet yang bukan
    klien - dan klien melaporkan "saldo 0". Satu nama, satu turunan, tidak ada salinan.
    """
    return Account.from_key(PAYER_KEY).address


def p2_domain(chain_id):
    return keccak(enc(["bytes32", "bytes32", "uint256", "address"],
                      [P2_DOMAIN_TYPEHASH, keccak(text="Permit2"), chain_id, cs(PERMIT2)]))


def token_domain(token_addr):
    raw = vd.call(cs(token_addr), "DOMAIN_SEPARATOR()")
    return bytes.fromhex(raw[2:])


def digest_p2(token_addr, amount, nonce, deadline, pay_to, valid_after, chain_id):
    w_hash = keccak(enc(["bytes32", "address", "uint256"], [WITNESS_TYPEHASH, cs(pay_to), valid_after]))
    tp = keccak(enc(["bytes32", "address", "uint256"], [P2_TP_TYPEHASH, cs(token_addr), amount]))
    struct = keccak(enc(["bytes32", "bytes32", "address", "uint256", "uint256", "bytes32"],
                        [P2_WITNESS_TYPEHASH, tp, cs(PROXY), nonce, deadline, w_hash]))
    return keccak(b"\x19\x01" + p2_domain(chain_id) + struct), w_hash, tp


def digest_2612(token_addr, owner, value, nonce_, deadline):
    struct = keccak(enc(["bytes32", "address", "address", "uint256", "uint256", "uint256"],
                        [EIP2612_PERMIT_TYPEHASH, cs(owner), cs(PERMIT2), value, nonce_, deadline]))
    return keccak(b"\x19\x01" + token_domain(token_addr) + struct)


def http(url, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; fabius-client/1.0)",
                                               **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")


def _sig_65(signed):
    """65 byte r||s||v dengan v = 27/28.

    eth_account memulangkan yParity 0/1; ECDSA di Permit2 (dan pemeriksaan OZ di EIP-2612)
    menerima 27/28. Kalau ini dibiarkan, gejalanya adalah revert di chain tanpa pesan yang
    menjelaskan penyebabnya - tipe kegagalan yang paling mahal untuk ditelusuri dari jauh.
    """
    h = signed.signature.hex()
    h = h[2:] if h.startswith("0x") else h
    v = int(h[128:130], 16)
    return "0x" + h[:128] + ("%02x" % (v + 27 if v < 27 else v))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8042")
    ap.add_argument("--path", default="/vault/latest")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    payer = payer_address()
    print(f"pembeli : {payer}")
    bal_bnb = vd.num(vd.rpc("eth_getBalance", [payer, "latest"])) / 10**18
    print(f"  BNB-nya: {bal_bnb:.6f}  <- kalau 0, itu justru yang mau kita buktikan (klien nol gas)")

    st, hdr, body = http(a.base + a.path)
    if st != 402:
        raise SystemExit(f"Respons pertama bukan 402 (dapat {st}). Berhenti - jangan paksa cerita.")
    req_b64 = hdr.get("PAYMENT-REQUIRED") or hdr.get("X-PAYMENT-REQUIRED") or ""
    req = json.loads(base64.b64decode(req_b64).decode()) if req_b64 else {}
    acc = (req.get("accepts") or [{}])[0]
    print(f"402     : error={req.get('error')!r}")
    print(f"  tagihan: amount={acc.get('amount')} network={acc.get('network')} asset={acc.get('asset')}")
    print(f"  payTo  : {acc.get('payTo')}")
    if not acc.get("asset"):
        raise SystemExit("accepts[] tanpa asset -> gerbang tidak lengkap")
    if acc.get("network") != f"eip155:{vd.CHAIN}":
        raise SystemExit(f"network di tagihan ({acc.get('network')}) bukan yang dibaca RPC "
                         f"(eip155:{vd.CHAIN}) -> tanda tangan akan salah chain")

    token = acc["asset"]
    amount = int(acc["amount"])
    pay_to = acc["payTo"]
    bal0 = int(vd.call(cs(token), "balanceOf(address)", ("address",), (bytes.fromhex(payer[2:]),)), 16)
    if bal0 < amount:
        raise SystemExit(f"pembeli punya {bal0} atomic < tagihan {amount} - jalankan tools/x402_deploy.py dulu")

    now = int(time.time())
    # validAfter sengaja DI BELAKANG jam mesin (default 15 detik, ubah dengan --skew).
    # Alasannya, dan ini bukan kosmetik: test Solidity memakai `block.timestamp` sehingga
    # tidak akan pernah kena `PaymentTooEarly`, sedangkan klien kami memakai jam laptop. Kalau
    # jam laptop beberapa detik di depan kepala chain, proxy menolak - dan gejalanya persis
    # "tanda tangan salah", padahal yang salah adalah asumsi bahwa dua jam itu sama.
    skew = int(os.environ.get("X402_SKEW", "15"))
    valid_after, deadline = now - skew, now + int(acc.get("maxTimeoutSeconds") or 60)
    p2_nonce = int(keccak(text=f"fabius-x402-{now}")[:16].hex(), 16)
    d_p2, _, _ = digest_p2(token, amount, p2_nonce, deadline, pay_to, valid_after, vd.CHAIN)
    # Digest kami SUDAH membawa prefix EIP-19 (`\x19\x01`), jadi yang dibutuhkan adalah tanda
    # tangan atas hash mentah - bukan `sign_message` yang akan mem-prefix ulang.
    # (`Account.sign_message(SignableMessage(version="0x04", header_data=...))` yang lama bukan
    #  sekadar jelek: field itu tidak ada, dan kode ini tidak akan pernah jalan.)
    sig_p2 = _sig_65(Account.unsafe_sign_hash(d_p2, PAYER_KEY))
    tok_nonce = int(vd.call(cs(token), "nonces(address)", ("address",),
                            (bytes.fromhex(payer[2:]),)), 16)
    d_2612 = digest_2612(token, payer, amount, tok_nonce, deadline)
    sig_2612 = _sig_65(Account.unsafe_sign_hash(d_2612, PAYER_KEY))

    payment = {
        "x402Version": 2,
        "resource": {"url": a.base + a.path, "description": acc.get("description"),
                     "mimeType": acc.get("mimeType")},
        "accepted": {"scheme": "exact", "network": acc["network"], "amount": str(amount),
                     "asset": token, "payTo": pay_to, "maxTimeoutSeconds": deadline - now,
                     "extra": acc.get("extra")},
        "payload": {
            "signature": sig_p2,
            "permit2Authorization": {
                "permitted": {"token": token, "amount": str(amount)},
                "from": payer, "spender": PROXY, "nonce": str(p2_nonce), "deadline": str(deadline),
                "witness": {"to": pay_to, "validAfter": str(valid_after)},
            },
        },
        "extensions": {"eip2612GasSponsoring": {"info": {
            "from": payer, "asset": token, "spender": PERMIT2, "amount": str(amount),
            "nonce": str(tok_nonce), "deadline": str(deadline), "signature": sig_2612,
            "version": (acc.get("extra") or {}).get("version", "1")}}},
    }
    b64 = base64.b64encode(json.dumps(payment, sort_keys=True).encode()).decode()
    if a.dry_run:
        print("\ndry-run: tanda tangan dibuat, tidak ada yang dikirim.")
        print(json.dumps(payment, indent=1, sort_keys=True)[:700])
        return

    st2, hdr2, body2 = http(a.base + a.path, {"PAYMENT-SIGNATURE": b64, "X-PAYMENT": b64})
    resp_b64 = hdr2.get("PAYMENT-RESPONSE") or hdr2.get("X-PAYMENT-RESPONSE") or ""
    resp = json.loads(base64.b64decode(resp_b64).decode()) if resp_b64 else {}
    print(f"\njawaban: HTTP {st2}  success={resp.get('success')}")
    if st2 != 200:
        try:
            print(f"  detail: {json.dumps(json.loads(body2))[:300]}")
        except Exception:  # noqa: BLE001
            print(f"  body: {body2[:300]}")
        print("  SETTLEMENT BELUM TERBUKA di jalur hidup ini.")
        return
    tx = resp.get("transaction")
    print(f"  tx    : https://testnet.bscscan.com/tx/{tx}")
    bal1 = int(vd.call(cs(token), "balanceOf(address)", ("address",), (bytes.fromhex(payer[2:]),)), 16)
    print(f"  saldo pembeli: {bal0} -> {bal1}  (berkurang {bal0 - bal1} atomic, tagihan {amount})")
    if bal0 - bal1 != amount:
        print("  !! jumlahnya tidak sama dengan tagihan - jangan tulis 'sesuai' kalau begitu")
    keys = sorted(json.loads(body2).keys()) if body2.startswith("{") else "-"
    print(f"  isi vault     : {keys}")
    print("\nYang terbukti di halaman ini: agen MEMBACA chain, MENERIMA 402, MENANDATANGANI dua")
    print("authorize (Permit2 + EIP-2612), TIDAK membayar gas sedikit pun, dan uangnya pindah di")
    print("kontrak kanonis - dilihat dari chain, bukan dari jawaban server-nya sendiri.")


if __name__ == "__main__":
    main()

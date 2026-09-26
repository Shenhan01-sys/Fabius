"""Gerbang x402: jual ringkasan vault + statistik Fabius, dibayar lewat proxy kanonis di chain 97.

Ini kaki yang selama ini BELUM pernah dieksekusi. Settlement-nya sudah 8 test Solidity buktikan;
yang belum pernah terjadi adalah permintaan HTTP sungguhan yang pulang dengan 402, membayar, lalu
menerima isi. File ini menutup itu - dan kalau ia lulus, klaimnya berubah dari "kami bisa settle"
jadi "sebuah agen bisa MEMBELI keluaran kami di BNB Chain".

Bentuk wire diambil dari SPEC pada commit yang sama dengan vendor kami
(`coinbase/x402 @ dd927a26`): header `PAYMENT-REQUIRED` / `PAYMENT-SIGNATURE` /
`PAYMENT-RESPONSE` (v2; v1 memakai `X-PAYMENT*`, keduanya diterima di sini supaya klien lama
tidak buta), dan `extensions.eip2612GasSponsoring` untuk jalur nol-gas klien.

Satu tempat di mana contoh spec dan kontrak yang benar-benar ada BERTENTANGAN, dan kontrak yang
menang: contoh ekstensi menulis `amount: MaxUint256` untuk EIP-2612, sementara
`settleWithPermit` kita me-revert kalau `permit2612.value != permitted.amount`
(`Permit2612AmountMismatch`, dan test fork kita membuktikan itu). Jadi permit yang kita tanda-
tangani memakai jumlah yang PERSIS sama dengan tagihan - nol gas klien tetap terpenuhi, dan kita
tidak perlu mengarang bahwa MaxUint aman.

Fasilitator = server ini (memakai kunci agen). Klien = `x402_client.py`, keduanya bisa dijalan-
kan orang lain; tidak ada pihak ketiga yang dibutuhkan, tidak ada dana nyata.

Pakai:  python tools/x402_deploy.py                      # sekali saja: deploy + danai klien
         python -u tools/x402_gate.py --port 8042         # jalankan gerbang
         python -u tools/x402_client.py --base http://127.0.0.1:8042   # agen pembeli bayar & ambil
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import verify_deploy as vd  # noqa: E402  (rpc/cd/call/send + rotasi endpoint + User-Agent)

try:
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
except ImportError:  # pragma: no cover
    raise SystemExit("butuh http.server (stdlib)")

DEPLOY = os.path.join(ROOT, "data", "x402", "deploy.json")
NETWORK = "eip155:97"
PROXY = "0x402085c248EeA27D92E8b30b2C58ed07f9E20001"   # x402ExactPermit2Proxy kanonis (56 & 97)
PRICE_ATOMIC = 1000                                     # 0,001 token - sama dengan test Solidity
TOKEN_NAME, TOKEN_VERSION = "X402 Demo USD", "1"        # domain EIP-2612 token kita
GAS_CAP = 900_000


def load_state():
    if not os.path.exists(DEPLOY):
        raise SystemExit(f"belum ada {os.path.relpath(DEPLOY, ROOT)} - jalankan tools/x402_deploy.py dulu")
    return json.load(open(DEPLOY, encoding="utf-8"))


def agent_key_and_addr():
    k = {}
    for path in (os.path.join(ROOT, ".agent.env"), os.path.expanduser("~/.config/fabius/agent.env")):
        try:
            for ln in open(path, encoding="utf-8"):
                ln = ln.strip()
                if ln and not ln.startswith("#") and "=" in ln:
                    a, b = ln.split("=", 1)
                    k.setdefault(a.strip(), b.strip())
        except OSError:
            continue
    if not k.get("AGENT_PRIVATE_KEY"):
        raise SystemExit(".agent.env tidak berisi AGENT_PRIVATE_KEY - fasilitator tidak bisa menandatangani")
    return k["AGENT_PRIVATE_KEY"], k["AGENT_ADDRESS"]


def vault_payload():
    """Isi yang dijual. Sumbernya berkas yang sudah ada di repo - tidak ada angka yang dikarang di sini."""
    out = {"kind": "fabius-vault", "as_of_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    latest = None
    dpath = os.path.join(ROOT, "decisions")
    files = sorted([f for f in os.listdir(dpath) if f.startswith("direction-")],
                   key=lambda f: os.path.getmtime(os.path.join(dpath, f)))
    for f in reversed(files):
        for ln in open(os.path.join(dpath, f), encoding="utf-8"):
            ln = ln.strip()
            if ln:
                latest = json.loads(ln)
        if latest:
            break
    out["last_decision"] = None
    if latest:
        d = latest.get("decision") or {}
        out["last_decision"] = {"symbol": latest.get("symbol"), "side": d.get("side"),
                                "regime": d.get("regime"), "sellability": d.get("sellability"),
                                "seat_eligible": d.get("seat_eligible"),
                                "decisionHash": latest.get("decisionHash"),
                                "gatesHash": latest.get("gatesHash"),
                                "snapshotHash": latest.get("snapshotHash")}
    try:
        sb = json.load(open(os.path.join(ROOT, "decisions", "smartmoney-10d-500.json"), encoding="utf-8"))
        out["smart_money"] = {"paired_windows": (sb.get("paired_test") or {}).get("windows_paired"),
                              "mean_diff_net_bps": (sb.get("paired_test") or {}).get("mean_diff_net_bps"),
                              "p_sign_flip": (sb.get("paired_test") or {}).get("p_sign_flip"),
                              "verdict": "tidak berbeda dari kerumunan"}
    except OSError:
        pass
    try:
        for ln in open(os.path.join(ROOT, "universe", "wallet-flow-manifest.txt"), encoding="utf-8"):
            if ln.startswith("baris_transaksi:"):
                out["wallet_flow_rows"] = ln.split(":", 1)[1].strip()
    except OSError:
        pass
    return out


def accepts_for(base_url, token, pay_to):
    return [{
        "scheme": "exact", "network": NETWORK, "amount": str(PRICE_ATOMIC),
        "asset": token, "payTo": pay_to, "maxTimeoutSeconds": 60,
        "resource": base_url, "description": "Fabius vault: keputusan terakhir + statistik ⑦",
        "mimeType": "application/json",
        "extra": {"name": TOKEN_NAME, "version": TOKEN_VERSION,
                  "assetTransferMethod": "permit2", "maxAmountRequired": str(PRICE_ATOMIC)},
    }]


def decode_payment(hdr):
    for part in hdr.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            obj = json.loads(base64.b64decode(part).decode())
        except Exception:  # noqa: BLE001
            continue
        if isinstance(obj, dict) and obj.get("payload"):
            return obj
    return None


def settle(st, pay, pk, facilitator):
    """Terjemahkan PAYMENT-SIGNATURE -> `settleWithPermit` di proxy kanonis. Return dict hasil."""
    from eth_abi import encode as enc
    p = pay["payload"]
    auth = p["permit2Authorization"]
    ext = ((pay.get("extensions") or {}).get("eip2612GasSponsoring") or {}).get("info") or {}
    if not ext:
        return {"ok": False, "why": "ekstensi eip2612GasSponsoring tidak ada -> klien minta nol-gas "
                                    "tapi tidak membawa permit EIP-2612"}
    r, s, v = _rs_v(ext["signature"])
    permit2612 = (int(ext["amount"]), int(ext["deadline"]), _b32(r), _b32(s), v)
    permitted = ((auth.get("permitted") or {}).get("token"), int(auth["permitted"]["amount"]))
    if permitted[1] != int(ext["amount"]):
        return {"ok": False, "why": f"jumlah permit ({permitted[1]}) != tagihan ({ext['amount']}) "
                                    "-> proxy akan revert Permit2612AmountMismatch"}
    witness = auth["witness"]
    calldata = _settle_calldata(permit2612, permitted, auth, witness, p["signature"])
    # `eth_call` dulu, sebelum transaksi nyata. Alasannya bukan hemat gas (gas testnet murah):
    # tanpa langkah ini satu-satunya jejak kegagalan adalah `status=0` + angka gas, dan kita
    # terpaksa menerka penyebabnya dari luar. Dengan ini data revert ikut sampai ke laporan.
    from eth_utils import to_checksum_address as cs
    try:
        vd.rpc("eth_call", [{"from": cs(facilitator), "to": cs(PROXY), "data": calldata}, "latest"])
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "why": "eth_call menolak sebelum kirim", "detail": str(e)[:260],
                "selector": calldata[:10], "calldata_bytes": max(0, len(calldata) // 2 - 1)}
    bal_before = _bal(st, facilitator)
    h, status, blk, gas, rec = vd.send(pk, PROXY, calldata, gas=GAS_CAP)
    if status == 0:
        return {"ok": False, "why": "settle revert", "tx": h, "gas": gas,
                "out_of_gas": gas >= GAS_CAP}
    bal_after = _bal(st, facilitator)
    return {"ok": True, "tx": h, "block": blk, "gas": gas,
            "payer": auth["from"], "moved_to_payTo": (bal_after or 0) - (bal_before or 0)}


def _b32(x):
    return bytes.fromhex(x[2:] if str(x).startswith("0x") else x).ljust(32, b"\0")[:32]


def _rs_v(sig):
    sig = sig[2:] if sig.startswith("0x") else sig
    return "0x" + sig[:64], "0x" + sig[64:128], int(sig[128:130], 16)


# SATU sumber kebenaran: tipe per-PARAMETER, selector diturunkan dari gabungannya.
# Sejarah bugnya (26 Sep, terukur): ABI proxy berbunyi `settleWithPermit(tuple,tuple,address,
# tuple,bytes)` = LIMA parameter, sedangkan string kami membungkus kelimanya jadi satu tuple
# bersarang. Efek berantai: eth_abi menolak ("value has 5 items when 1 were expected"), lalu
# setelah "dibuat lolos" selector-nya 0xfa340378 - bukan 0x914533e2 yang asli - dan setiap
# kegagalan berikutnya tampak seperti tanda tangan klien yang salah, padahal calldata kitalah
# yang cacat. Itu sebabnya selector tidak boleh ditulis tangan: ia harus DITURUNKAN.
SETTLE_PARAMS = [
    "(uint256,uint256,bytes32,bytes32,uint8)",   # EIP2612Permit{value,deadline,r,s,v}
    "((address,uint256),uint256,uint256)",       # PermitTransferFrom{permitted{token,amount},nonce,deadline}
    "address",                                   # owner
    "(address,uint256)",                         # Witness{to,validAfter}
    "bytes",                                     # signature
]
SETTLE_SIG = "settleWithPermit(" + ",".join(SETTLE_PARAMS) + ")"


def settle_selector():
    from eth_utils import keccak
    return "0x" + keccak(text=SETTLE_SIG)[:4].hex()


def _settle_calldata(permit2612, permitted, auth, witness, signature):
    """Calldata untuk proxy KANONIS yang sudah ter-deploy.

    Tipe per-parameter DIPASTIKAN terhadap artifact hasil kompilasi, bukan dari tebakan:
    `_research/diag_x402_selector.py` membandingkan ABI proxy dengan string kami dan menulis
    verdiknya. Versi yang gagal membungkus LIMA parameter jadi satu tuple bersarang, sehingga
    selector yang lahir 0xfa340378 - bukan 0x914533e2 yang asli.
    """
    from eth_abi import encode as enc
    from eth_utils import keccak, to_checksum_address as cs
    vals = [permit2612,
            ((cs(permitted[0]), permitted[1]), int(auth["nonce"]), int(auth["deadline"])),
            cs(auth["from"]),
            (cs(witness["to"]), int(witness["validAfter"])),
            bytes.fromhex(signature[2:] if signature.startswith("0x") else signature)]
    return "0x" + keccak(text=SETTLE_SIG)[:4].hex() + enc(SETTLE_PARAMS, vals).hex()


def _bal(st, addr):
    """Saldo `addr` pada TOKEN.

    Versi pertama memanggil `balanceOf` pada ALAMAT DOMPET itu sendiri (bukan pada kontrak token) -
    pemeriksaan yang seharusnya membuktikan "uangnya benar-benar pindah" justru akan selalu salah.
    """
    from eth_utils import to_checksum_address as cs
    try:
        raw = vd.call(cs(st["token"]), "balanceOf(address)", ("address",),
                      (bytes.fromhex(addr[2:]),))
        return int(raw, 16) if raw and raw != "0x" else None
    except Exception as e:  # noqa: BLE001
        print(f"  balanceOf gagal: {type(e).__name__}: {str(e)[:90]}")
        return None


class Handler(BaseHTTPRequestHandler):
    st = None
    pk = None
    facilitator = None

    def log_message(self, fmt, *a):
        print(f"  [{time.strftime('%H:%M:%S')}] {self.command} {self.path} -> {a[1] if len(a) > 1 else ''}")

    def _send(self, code, body, extra=None):
        raw = json.dumps(body, sort_keys=True).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        base = f"http://127.0.0.1:{self.server.server_address[1]}{self.path}"
        hdr = self.headers.get("PAYMENT-SIGNATURE") or self.headers.get("X-PAYMENT")
        if not hdr:
            req = {"x402Version": 2, "error": "PAYMENT-SIGNATURE header is required",
                   "resource": {"url": base, "description": "Fabius vault", "mimeType": "application/json"},
                   "accepts": accepts_for(base, self.st["token"], self.facilitator)}
            b64 = base64.b64encode(json.dumps(req, sort_keys=True).encode()).decode()
            self._send(402, {}, {"PAYMENT-REQUIRED": b64, "X-PAYMENT-REQUIRED": b64})
            return
        pay = decode_payment(hdr)
        if not pay:
            self._send(400, {"error": "PAYMENT-SIGNATURE tidak bisa didekode"})
            return
        acc = pay.get("accepted") or {}
        if str(acc.get("amount")) != str(PRICE_ATOMIC) or acc.get("network") != NETWORK:
            self._send(402, {"error": "pembayaran tidak cocok dengan tagihan",
                             "expected": {"amount": str(PRICE_ATOMIC), "network": NETWORK}})
            return
        res = settle(self.st, pay, self.pk, self.facilitator)
        if not res.get("ok"):
            self._send(402, {"error": "settlement gagal", "detail": res})
            return
        body = vault_payload()
        resp = {"success": True, "transaction": res["tx"], "network": NETWORK, "payer": res["payer"]}
        b64 = base64.b64encode(json.dumps(resp, sort_keys=True).encode()).decode()
        self._send(200, body, {"PAYMENT-RESPONSE": b64, "X-PAYMENT-RESPONSE": b64})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8042)
    a = ap.parse_args()
    st = load_state()
    pk, facilitator = agent_key_and_addr()
    Handler.st, Handler.pk, Handler.facilitator = st, pk, facilitator
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    srv.allow_reuse_address = True
    print(f"gerbang x402 di http://127.0.0.1:{a.port}/vault/latest")
    print(f"  token   : {st['token']}  (network {NETWORK}, harga {PRICE_ATOMIC} atomic = 0,001)")
    print(f"  payTo   : {facilitator}")
    print(f"  proxy   : {PROXY}  (kanonis, verifikasi: tools/x402_gate.py memakai yang ter-deploy)")
    print("  Ctrl+C untuk berhenti\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nberhenti.")


if __name__ == "__main__":
    main()

"""Klien server Privy minimal (P138e, F-D101): `/buy` di Telegram dibayar LANGSUNG dari dompet Privy user, ditandatangani di enclave Privy atas nama
user yang SUDAH memberi izin (session signer = key quorum `PRIVY_KEY_QUORUM_ID`). Kunci dompet tidak pernah dipegang Fabius.

Dibuat dari SDK resmi `privy-client` 0.7.0 (dibaca 5 Okt), bukan tebakan:
  - cari user:  POST https://api.privy.io/v1/users/telegram/telegram_user_id  {"telegram_user_id": "<id>"}  (Basic app_id:app_secret + privy-app-id)
  - tanda tangan: POST https://api.privy.io/v1/wallets/{wallet_id}/rpc  {"method": "eth_signTypedData_v4", "chain_type": "ethereum",
                  "params": {"typed_data": {domain, types, primary_type, message}}}  + `privy-authorization-signature`
  - `privy-authorization-signature` = base64 ECDSA-P256-SHA256 (DER) atas JSON kanonis {"version": 1, "method", "url", "body",
    "headers": {"privy-app-id"}} (kunci urut, tanpa spasi, UTF-8); kunci = base64 DER PKCS#8, awalan dashboard `wallet-auth:` dibuang.
Yang ditandatangani SELALU dibangun gerbang sendiri (Permit2 witness + EIP-2612 untuk tepat tagihan FAB ke payTo gerbang) - bukan input user.
Kunci otorisasi yang dipakai sekarang TERBUKA di chat 5 Okt (keputusan builder: pakai dulu, migrasi sesudah hackathon; cadangan di `.privy.env`).
"""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from typing import Callable, Optional, Tuple

BASE = "https://api.privy.io"


def canonical(o) -> bytes:
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def auth_signature(private_key: str, payload: bytes) -> str:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    k = private_key.strip()
    if k.startswith("wallet-auth:"):
        k = k[len("wallet-auth:"):]
    key = serialization.load_der_private_key(base64.b64decode(k), password=None)
    if not isinstance(key, ec.EllipticCurvePrivateKey) or not isinstance(key.curve, ec.SECP256R1):
        raise ValueError("kunci otorisasi Privy harus P-256 PKCS#8")
    return base64.b64encode(key.sign(payload, ec.ECDSA(hashes.SHA256()))).decode("ascii")


def _http(method: str, url: str, headers: dict, body: Optional[dict]) -> Tuple[int, dict]:
    req = urllib.request.Request(url, method=method, headers=headers, data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except ValueError:
            return e.code, {}


class PrivyError(RuntimeError):
    def __init__(self, status: int, body: dict, what: str):
        super().__init__(f"{what}: HTTP {status} {str(body.get('error') or body.get('message') or body)[:160]}")
        self.status, self.body = status, body


class Privy:
    def __init__(self, app_id: str, app_secret: str, auth_key: Optional[str], http: Callable = _http, base: str = BASE):
        self.app_id, self.app_secret, self.auth_key, self.http, self.base = app_id, app_secret, auth_key, http, base

    def _headers(self) -> dict:
        basic = base64.b64encode(f"{self.app_id}:{self.app_secret}".encode()).decode("ascii")
        # User-Agent WAJIB: tanpa itu Cloudflare di depan api.privy.io menjawab 403 "error code: 1010" (UA Python-urllib diblokir) - diukur 5 Okt.
        return {"Authorization": f"Basic {basic}", "privy-app-id": self.app_id, "Content-Type": "application/json",
                "User-Agent": "fabius-x402/1.0 (+https://fabius-one.vercel.app)"}

    def user_by_telegram(self, telegram_user_id: int) -> Optional[dict]:
        st, body = self.http("POST", f"{self.base}/v1/users/telegram/telegram_user_id", self._headers(), {"telegram_user_id": str(telegram_user_id)})
        if st == 404:
            return None
        if st != 200:
            raise PrivyError(st, body, "cari user Telegram")
        return body

    @staticmethod
    def embedded_wallet(user: dict) -> Optional[Tuple[str, str]]:
        """(wallet_id, address) dompet embedded Ethereum milik user (yang dibuat Privy saat login)."""
        for a in user.get("linked_accounts") or []:
            if a.get("type") == "wallet" and a.get("id") and a.get("chain_type", "ethereum") == "ethereum" and a.get("wallet_client_type", "privy") == "privy":
                return a["id"], a["address"]
        return None

    def sign_typed_data(self, wallet_id: str, typed: dict) -> str:
        if not self.auth_key:
            raise PrivyError(0, {"error": "PRIVY_AUTH_PRIVATE_KEY tidak ada"}, "tanda tangan")
        url = f"{self.base}/v1/wallets/{wallet_id}/rpc"
        body = {"method": "eth_signTypedData_v4", "chain_type": "ethereum",
                "params": {"typed_data": {"domain": typed["domain"], "types": typed["types"], "primary_type": typed["primaryType"], "message": typed["message"]}}}
        h = self._headers()
        payload = canonical({"version": 1, "method": "POST", "url": url, "body": body, "headers": {"privy-app-id": self.app_id}})
        h["privy-authorization-signature"] = auth_signature(self.auth_key, payload)
        st, resp = self.http("POST", url, h, body)
        if st != 200:
            raise PrivyError(st, resp, "tanda tangan dompet")
        sig = (resp.get("data") or {}).get("signature")
        if not sig:
            raise PrivyError(st, resp, "tanda tangan kosong")
        return sig

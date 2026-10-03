"""Adaptor Binance USDⓈ-M futures (P118, epik 10 "Eksekusi Venue"; prioritas 1 menurut F-D91: lewat sub-akun Agentic Binance Agent OS).

Stdlib. Kunci dibaca dari env `BINANCE_API_KEY` / `BINANCE_SECRET_KEY` (nama sama dengan `binance-cli` resmi), dipasang builder di variabel
Railway - tidak pernah di chat, repo, atau log. Lingkungan (`BINANCE_API_ENV`): `testnet` (bawaan; testnet.binancefuture.com), `demo` (Demo Trading,
demo-fapi.binance.com; kunci dibuat di demo.binance.com), `prod` (fapi.binance.com + api.binance.com).
Dari jaringan builder domain prod Binance terblokir (2 Okt); jalankan dari Railway (Singapura) - akses endpoint trading dari sana diukur di E2.

Yang ada (4 Okt): tanda tangan HMAC-SHA256 (diuji dengan vektor resmi dokumen Binance), filter + harga publik, cek izin kunci (PRD R-E6:
tarik HARUS mati, futures HARUS hidup), posisi, dan order pasar IDEMPOTEN (cari `origClientOrderId` dulu; ada = tidak dikirim lagi, R-E2).
Tidak ada yang mengirim order sampai eksekutor memanggilnya dalam mode testnet/live (P118/P120).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Dict, Iterable, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from engine.eksekusi import Filter, Order                                      # noqa: E402

# Alamat = konstanta SDK resmi `binance-connector-python` (common/constants.py, commit 2026-09-23). Sejak 2026 web testnet futures DIALIHKAN ke
# Demo Trading (demo.binance.com, butuh akun Binance); kunci demo bekerja di demo-fapi. Testnet API lama tetap ada untuk kunci testnet lama.
BASE = {"prod": {"fapi": "https://fapi.binance.com", "sapi": "https://api.binance.com"},
        "demo": {"fapi": "https://demo-fapi.binance.com", "sapi": None},
        "testnet": {"fapi": "https://testnet.binancefuture.com", "sapi": None}}
RECV_WINDOW = 5000


class VenueError(Exception):
    """Venue tak terjangkau / balasan tak terbaca: TUNDA, posisi tidak ditebak (T8 SK-E2)."""


class KeyPermissionError(Exception):
    """Izin kunci tidak aman: eksekutor tidak start (T8 SK-E4)."""


def sign(query: str, secret: str) -> str:
    return hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()


def _http(method: str, url: str, headers: Dict[str, str], timeout: float = 15.0) -> Tuple[int, dict]:
    req = urllib.request.Request(url, method=method, headers=dict(headers, **{"User-Agent": "fabius-exec/1.0"}))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:  # noqa: BLE001
            return e.code, {}


def parse_filters(info: dict, symbols: Iterable[str]) -> Dict[str, Filter]:
    rows = {s["symbol"]: s for s in info.get("symbols", [])}
    out = {}
    for sym in symbols:
        s = rows.get(sym)
        if not s:
            continue
        f = {x["filterType"]: x for x in s.get("filters", [])}
        lot = f.get("MARKET_LOT_SIZE") or f.get("LOT_SIZE") or {}
        mn = f.get("MIN_NOTIONAL") or f.get("NOTIONAL") or {}
        step = float(lot.get("stepSize") or 0)
        if step <= 0:
            step = float((f.get("LOT_SIZE") or {}).get("stepSize") or 0)
        out[sym] = Filter(step=step, min_qty=float(lot.get("minQty") or 0), min_notional=float(mn.get("notional") or mn.get("minNotional") or 0))
    return out


def check_no_withdraw(r: dict) -> None:
    """GET /sapi/v1/account/apiRestrictions: tarik harus mati DAN futures harus hidup. Medan hilang = tidak aman (gagal tertutup)."""
    if r.get("enableWithdrawals") is not False:
        raise KeyPermissionError("kunci Binance punya izin tarik (atau izinnya tak terbaca): eksekutor tidak start")
    if r.get("enableFutures") is not True:
        raise KeyPermissionError("kunci Binance tanpa izin futures: tidak bisa mengeksekusi B1")


class BinanceFutures:
    def __init__(self, env: Optional[str] = None, key: Optional[str] = None, secret: Optional[str] = None,
                 http: Callable[..., Tuple[int, dict]] = _http, now_ms: Callable[[], int] = lambda: int(time.time() * 1000)):
        # env dari argumen, lalu variabel `BINANCE_API_ENV` (nama sama dengan binance-cli), bawaan testnet: prod tidak pernah jadi bawaan
        env = env or (os.environ.get("BINANCE_API_ENV") or "testnet").strip().lower()
        if env not in BASE:
            raise ValueError(f"BINANCE_API_ENV tidak dikenal: {env} (pilihan: {', '.join(BASE)})")
        self.env, self.http, self.now_ms = env, http, now_ms
        self.key = key if key is not None else (os.environ.get("BINANCE_API_KEY") or "").strip()
        self.secret = secret if secret is not None else (os.environ.get("BINANCE_SECRET_KEY") or "").strip()

    def _clean(self, s: str) -> str:
        for x in (self.key, self.secret):
            if x:
                s = s.replace(x, "<rahasia>")
        return s

    def _get_public(self, path: str, params: Optional[dict] = None) -> dict:
        url = BASE[self.env]["fapi"] + path + ("?" + urllib.parse.urlencode(params) if params else "")
        try:
            code, body = self.http("GET", url, {})
        except Exception as e:  # noqa: BLE001
            raise VenueError(f"{path}: tak terjangkau ({type(e).__name__})") from None
        if code != 200:
            raise VenueError(f"{path}: HTTP {code} {str(body)[:120]}")
        return body

    def _signed(self, method: str, base: str, path: str, params: Optional[dict] = None) -> Tuple[int, dict]:
        if not (self.key and self.secret):
            raise KeyPermissionError("BINANCE_API_KEY / BINANCE_SECRET_KEY tidak ada di lingkungan ini")
        q = urllib.parse.urlencode(dict(params or {}, recvWindow=RECV_WINDOW, timestamp=self.now_ms()))
        url = f"{base}{path}?{q}&signature={sign(q, self.secret)}"
        try:
            return self.http(method, url, {"X-MBX-APIKEY": self.key})
        except Exception as e:  # noqa: BLE001
            raise VenueError(self._clean(f"{path}: tak terjangkau ({type(e).__name__})")) from None

    # ---------------------------------------------------------------- publik
    def filters(self, symbols: Iterable[str]) -> Dict[str, Filter]:
        return parse_filters(self._get_public("/fapi/v1/exchangeInfo"), symbols)

    def book(self, symbols: Iterable[str]) -> Dict[str, Tuple[float, float]]:
        want = set(symbols)
        rows = self._get_public("/fapi/v1/ticker/bookTicker")
        return {r["symbol"]: (float(r["bidPrice"]), float(r["askPrice"])) for r in rows if r["symbol"] in want} if isinstance(rows, list) else {}

    # ---------------------------------------------------------------- privat (kunci)
    def assert_safe_key(self) -> None:
        """PRD R-E6. Testnet/demo tidak punya endpoint izin: di sana hanya kunci uji yang dipakai (saldo virtual, tanpa dana nyata)."""
        if self.env in ("testnet", "demo"):
            return
        code, body = self._signed("GET", BASE["prod"]["sapi"], "/sapi/v1/account/apiRestrictions")
        if code != 200:
            raise KeyPermissionError(f"izin kunci tak terbaca (HTTP {code}): eksekutor tidak start")
        check_no_withdraw(body)

    def positions(self) -> Dict[str, float]:
        code, body = self._signed("GET", BASE[self.env]["fapi"], "/fapi/v2/positionRisk")
        if code != 200 or not isinstance(body, list):
            raise VenueError(f"positionRisk: HTTP {code} {self._clean(str(body)[:120])}")
        return {r["symbol"]: float(r["positionAmt"]) for r in body if float(r.get("positionAmt") or 0) != 0}

    def order_by_client_id(self, symbol: str, cid: str) -> Optional[dict]:
        code, body = self._signed("GET", BASE[self.env]["fapi"], "/fapi/v1/order", {"symbol": symbol, "origClientOrderId": cid})
        if code == 200:
            return body
        if isinstance(body, dict) and body.get("code") == -2013:          # Order does not exist
            return None
        raise VenueError(f"query order {cid}: HTTP {code} {self._clean(str(body)[:120])}")

    def place(self, o: Order) -> dict:
        """Order pasar idempoten: id yang sama sudah ada = kembalikan yang lama, TIDAK mengirim lagi (T8 SK-E6)."""
        old = self.order_by_client_id(o.asset, o.client_id)
        if old is not None:
            return dict(old, _fabius="sudah ada (idempoten)")
        params = {"symbol": o.asset, "side": o.side, "type": "MARKET", "quantity": f"{o.qty:.10g}", "newClientOrderId": o.client_id}
        if o.reduce_only:
            params["reduceOnly"] = "true"
        code, body = self._signed("POST", BASE[self.env]["fapi"], "/fapi/v1/order", params)
        if code != 200:
            raise VenueError(f"order {o.client_id} ditolak: HTTP {code} {self._clean(str(body)[:160])}")
        return body

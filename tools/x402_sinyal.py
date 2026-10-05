"""Gerbang x402 per sinyal Fabius (P138a, F-D98/F-D99/F-D100): service Railway `fabius-x402`, testnet 97, token Fabius Credit (FAB).

Yang dijual (F-D99): paket sinyal SIAP PAKAI untuk satu (bot, bar) - niat posisi dari tick ledger + bukti (commitId, waktu komit, status ungkap,
validasi ERC-8004) - segera sesudah komit. Bukan rahasia: bot B1-B6 deterministik dan terbuka, siapa pun bisa menghitung ulang isinya.
Harga per (bot, bar) = `engine/harga.py` (tabel terkunci, dari confidence P137), beku per bar.

Rute:
  GET  /                      info: token, proxy, payTo, harga tiap bot, cara bayar
  GET  /teaser/<bot>          gratis: teaser confidence + harga bar terakhir (tanpa aset/arah/ukuran)
  GET  /sinyal/<bot>[/<bar>]  402 + PAYMENT-REQUIRED; dengan PAYMENT-SIGNATURE (x402 v2, exact, permit2 + eip2612GasSponsoring) -> settle -> paket
                              `?tg=<tautan bertanda>` (dari bot Telegram): sesudah settle, paket juga dikirim ke chat itu
  POST /faucet                {"address": "0x.."} -> gerbang mengirim FAB (pembeli tidak butuh tBNB sama sekali); berbatas per alamat + harian
Pemeriksaan pembayaran (celah gate lama `x402_gate.py` yang hanya mencocokkan `accepted` dari klien): token, jumlah, penerima (`witness.to`),
spender, deadline diperiksa pada otorisasi yang DITANDATANGANI; `eth_call` dulu; sesudah tx, log Transfer pembeli -> payTo sejumlah harga harus ada.

Lingkungan: X402_FACILITATOR_PRIVATE_KEY (kunci BARU, bukan committer/agen/validator) · PORT (Railway) · TELEGRAM_SIGNAL_BOT_TOKEN (opsional, P138d)
· X402_PUBLIC_URL (URL publik gerbang ini) · WEB_URL (bawaan https://fabius-one.vercel.app).
    python -X utf8 tools/x402_sinyal.py --port 8050            # lokal (kunci dari .x402.env)
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Dict, Optional, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from engine import book as bookmod, chain, data as datamod, harga, ledger, rincian   # noqa: E402
from engine.spec import SPECS                                                 # noqa: E402
import signal_commit as sc                                                    # noqa: E402

NETWORK = "eip155:97"
PROXY = "0x402085c248EeA27D92E8b30b2C58ed07f9E20001"      # x402ExactPermit2Proxy kanonis (56 & 97)
PERMIT2 = "0x000000000022D473030F116dDEE9F6B43aC78BA3"
TOKEN_NAME, TOKEN_VERSION = "Fabius Credit", "1"          # domain EIP-712 FabiusCredit
KEY_VAR = "X402_FACILITATOR_PRIVATE_KEY"
KEY_ENV = os.path.join(ROOT, ".x402.env")
GAS_CAP = 900_000
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
FAUCET_ATOMIC = 500_000                                     # 0,5 FAB = 50 sinyal pada harga dasar
FAUCET_IF_BELOW = 100_000                                   # hanya bila saldo < 0,1 FAB
FAUCET_DAILY_MAX = 200                                      # kiriman faucet per hari (semua alamat)
TG_TTL_S = 24 * 3600
ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

# Salinan calldata `settleWithPermit` dari `x402_gate.py`; selector 0xfa340378 = input tx sukses 0xb6093e59 (dibaca dari chain 5 Okt). Tes menjaga
# keduanya sama dan sama dengan angka itu.
SETTLE_PARAMS = [
    "(uint256,uint256,bytes32,bytes32,uint8)",   # EIP2612Permit{value,deadline,r,s,v}
    "((address,uint256),uint256,uint256)",       # PermitTransferFrom{permitted{token,amount},nonce,deadline}
    "address",                                   # owner
    "(address,uint256)",                         # Witness{to,validAfter}
    "bytes",                                     # signature
]
SETTLE_SIG = "settleWithPermit(" + ",".join(SETTLE_PARAMS) + ")"


def facilitator_key() -> Optional[str]:
    return os.environ.get(KEY_VAR) or sc.read_env_file(KEY_ENV, KEY_VAR)


def load_cfg(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    x = d.get("x402_sinyal") or {}
    return {"token": x.get("token"), "facilitator": x.get("facilitator"), "committer": (d.get("m3") or {}).get("committer"),
            "anchor": (d.get("contracts") or {}).get("SignalAnchor"), "registry": (d.get("contracts") or {}).get("LockRegistry"),
            "erc8004": d.get("erc8004") or {}}


# ---------------------------------------------------------------- pembayaran (murni; diuji tanpa jaringan)

def decode_payment(hdr: str) -> Optional[dict]:
    for part in (hdr or "").split(","):
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


def accepts_for(resource: str, token: str, pay_to: str, atomic: int, desc: str) -> list:
    return [{"scheme": "exact", "network": NETWORK, "amount": str(atomic), "asset": token, "payTo": pay_to, "maxTimeoutSeconds": 120,
             "resource": resource, "description": desc, "mimeType": "application/json",
             "extra": {"name": TOKEN_NAME, "version": TOKEN_VERSION, "assetTransferMethod": "permit2", "maxAmountRequired": str(atomic)}}]


def check_payment(pay: dict, token: str, pay_to: str, atomic: int, now_s: int) -> Optional[str]:
    """Alasan menolak, atau None. Semua dari otorisasi yang DITANDATANGANI pembeli, bukan dari `accepted` yang bisa ditulis apa saja."""
    p = pay.get("payload") or {}
    a = p.get("permit2Authorization") or {}
    ext = ((pay.get("extensions") or {}).get("eip2612GasSponsoring") or {}).get("info") or {}
    low = lambda x: str(x or "").lower()                                      # noqa: E731
    try:
        if not p.get("signature") or not a or not ext:
            return "payload/permit2Authorization/eip2612GasSponsoring tidak lengkap"
        if low((a.get("permitted") or {}).get("token")) != low(token) or low(ext.get("asset")) != low(token):
            return "token bukan FAB"
        if int((a.get("permitted") or {}).get("amount")) != atomic or int(ext.get("amount")) != atomic:
            return f"jumlah bukan tagihan {atomic}"
        if low((a.get("witness") or {}).get("to")) != low(pay_to):
            return "penerima (witness.to) bukan payTo gerbang ini"
        if low(a.get("spender")) != low(PROXY) or low(ext.get("spender")) != low(PERMIT2):
            return "spender bukan proxy x402 / Permit2 kanonis"
        if low(a.get("from")) != low(ext.get("from")) or not ADDR_RE.match(str(a.get("from"))):
            return "pemilik Permit2 dan EIP-2612 berbeda"
        if int(a.get("deadline")) < now_s or int(ext.get("deadline")) < now_s:
            return "otorisasi kedaluwarsa"
    except (TypeError, ValueError) as e:
        return f"angka otorisasi tak terbaca: {type(e).__name__}"
    return None


def _b32(x) -> bytes:
    return bytes.fromhex(x[2:] if str(x).startswith("0x") else x).ljust(32, b"\0")[:32]


def settle_calldata(pay: dict) -> bytes:
    from eth_abi import encode
    from eth_utils import keccak, to_checksum_address as cs
    p, ext = pay["payload"], pay["extensions"]["eip2612GasSponsoring"]["info"]
    a = p["permit2Authorization"]
    s = ext["signature"][2:] if ext["signature"].startswith("0x") else ext["signature"]
    permit2612 = (int(ext["amount"]), int(ext["deadline"]), _b32("0x" + s[:64]), _b32("0x" + s[64:128]), int(s[128:130], 16))
    vals = [permit2612, ((cs(a["permitted"]["token"]), int(a["permitted"]["amount"])), int(a["nonce"]), int(a["deadline"])), cs(a["from"]),
            (cs(a["witness"]["to"]), int(a["witness"]["validAfter"])), bytes.fromhex(p["signature"][2:] if p["signature"].startswith("0x") else p["signature"])]
    return keccak(text=SETTLE_SIG)[:4] + encode(SETTLE_PARAMS, vals)


def paid_in_receipt(rcpt: dict, token: str, payer: str, pay_to: str, atomic: int) -> bool:
    """Bukti dari chain, bukan dari jawaban kontrak: log Transfer(payer -> payTo, harga) pada token FAB di receipt settle."""
    pad = lambda a: "0x" + "0" * 24 + a.lower()[2:]                          # noqa: E731
    for lg in rcpt.get("logs") or []:
        t = [x.lower() for x in lg.get("topics") or []]
        if (str(lg.get("address", "")).lower() == token.lower() and len(t) == 3 and t[0] == TRANSFER_TOPIC and t[1] == pad(payer)
                and t[2] == pad(pay_to) and int(lg.get("data") or "0x0", 16) == atomic):
            return True
    return False


# ---------------------------------------------------------------- tautan Telegram bertanda (tanpa penyimpanan)

def tg_link(secret: bytes, chat_id: int, bot: str, bar: str, now_s: int) -> str:
    body = base64.urlsafe_b64encode(json.dumps({"c": int(chat_id), "b": bot, "r": bar, "e": now_s + TG_TTL_S}, separators=(",", ":")).encode()).decode().rstrip("=")
    return body + "." + hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()[:32]


def tg_parse(secret: bytes, token: str, now_s: int) -> Optional[dict]:
    try:
        body, mac = token.split(".", 1)
        if not hmac.compare_digest(mac, hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()[:32]):
            return None
        d = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)).decode())
        return d if int(d["e"]) >= now_s else None
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------- data (klon repo yang sama dengan worker)

class Data:
    def __init__(self, workdir: str, sync: Optional[Callable[[str], str]] = None):
        self.workdir, self.sync_fn, self.last_sync, self.head = workdir, sync, 0.0, None
        self.lock = threading.Lock()

    def refresh(self, every_s: int = 120) -> None:
        if self.sync_fn is None or time.time() - self.last_sync < every_s:
            return
        with self.lock:
            if time.time() - self.last_sync >= every_s:
                self.head = self.sync_fn(self.workdir)
                self.last_sync = time.time()

    def ledgers(self) -> Dict[str, list]:
        d = os.path.join(self.workdir, "ledger", "paper")
        return {b: ledger.load(os.path.join(d, f"{b}.jsonl")) for b in bookmod.FORWARD_BOTS if os.path.exists(os.path.join(d, f"{b}.jsonl"))}

    def series(self, bot: str) -> Dict[str, tuple]:
        """Bar harian publik universe bot (`ledger/bars/fut_<SYM>_1d.csv`) -> {aset: (t, c)} untuk rincian paket."""
        uni = [a for a in SPECS[bot].universe if os.path.exists(os.path.join(self.workdir, "ledger", "bars", f"fut_{a}_1d.csv"))]
        if not uni:
            return {}
        md = datamod.load_csv_dir(os.path.join(self.workdir, "ledger", "bars"), uni)
        return {a: (md.perp[a].t, md.perp[a].c) for a in md.perp}

    def cfg(self) -> dict:
        return load_cfg(os.path.join(self.workdir, "deployments", "97.json"))


def last_bar(recs) -> Optional[str]:
    ticks = [r for r in recs if r.get("type") == "tick"]
    return max(ticks, key=lambda r: r["asof"])["asof_date"] if ticks else None


def quote(led: Dict[str, list], bot: str, bar: Optional[str] = None) -> dict:
    if bot not in led:
        raise KeyError(f"bot {bot} tidak berjam maju")
    bar = bar or last_bar(led[bot])
    if bar is None:
        raise KeyError(f"{bot} belum punya tick")
    return harga.harga_bar(bot, bar, led, bookmod.STATUS, bookmod.GATE_V1)


def package(led: Dict[str, list], bot: str, bar: str, cfg: dict, cv=None, reg=None, series: Optional[Dict[str, tuple]] = None) -> dict:
    """Paket sinyal yang dibeli: niat posisi tick + bukti. `cv`/`reg` = pembaca chain (None = tanpa bagian chain)."""
    ticks = [r for r in led[bot] if r.get("type") == "tick"]
    k = next(j for j, r in enumerate(ticks) if r.get("asof_date") == bar)
    tk = ticks[k]
    cid = sc.commit_id(cfg["committer"], bot, SPECS[bot].sha(), sc.asof_s_of(tk))
    out = {"bot": bot, "bar": bar, "status": bookmod.STATUS.get(bot), "targets": tk.get("targets", {}), "signal_ids": tk.get("signal_ids", []),
           "emitted_utc": tk.get("emitted_utc"), "close_utc": tk.get("close_utc"), "ledger_h": tk.get("h"), "commitId": chain.hex0x(cid),
           "signal_anchor": cfg["anchor"], "catatan": "paper: niat posisi, bukan order; bot deterministik + terbuka (F-D99) - bisa dihitung ulang dari repo"}
    if series is not None:
        g = next((r for r in led[bot] if r.get("type") == "genesis"), {})
        out["rincian"] = rincian.rincian(bot, SPECS[bot].metode, SPECS[bot].param, tk.get("targets", {}), ticks[k - 1].get("targets", {}) if k > 0 else None,
                                         int(tk["asof"]), series, g.get("first_asof"))
        out["rincian"]["aturan_en"] = RULE_EN.get(bot)
    if cv is not None:
        c = cv.get_commit(cid)
        on = int(str(c["committer"]), 16) != 0
        out["komit"] = {"ada": on, "committedAt": int(c["committedAt"]) if on else None, "n": int(c["n"]) if on else None,
                        "terungkap": int(c["revealed"]) if on else None}
    if reg is not None:
        s = reg.status(cid)
        out["validasi_erc8004"] = None if s is None else {"validator": s["validator"], "skor": int(s["response"]),
                                                          "dijawab": int.from_bytes(bytes(s["responseHash"]), "big") != 0}
    return out


# ---------------------------------------------------------------- HTTP

class Gate:
    """Keadaan gerbang (satu proses). `send`/`call` disuntik supaya tes tidak butuh jaringan."""

    def __init__(self, data: Data, pk: Optional[str], public_url: str, web_url: str, ev=None, tg_token: Optional[str] = None,
                 log: Callable[[str], None] = print, now: Callable[[], float] = time.time):
        self.data, self.pk, self.public_url, self.web_url, self.ev, self.tg_token, self.log, self.now = data, pk, public_url.rstrip("/"), web_url.rstrip("/"), ev, tg_token, log, now
        self.tx_lock = threading.Lock()
        self.faucet_seen: Dict[str, float] = {}
        self.faucet_day, self.faucet_count = "", 0
        self.tg_secret = hashlib.sha256(b"fabius-tg-link|" + (pk or "tanpa-kunci").encode()).digest()


    # -- pembaca chain (None tanpa ev)
    def views(self, cfg):
        if self.ev is None:
            return None, None
        import erc8004_validasi as v8
        cv = sc.AnchorView(self.ev, cfg["anchor"], cfg["registry"])
        reg = v8.RegistryView(self.ev, cfg["erc8004"]) if cfg["erc8004"].get("validation") else None
        return cv, reg

    def settle(self, pay: dict, cfg: dict, atomic: int) -> dict:
        from evm import receipt_ok
        to = PROXY
        data = settle_calldata(pay)
        payer = pay["payload"]["permit2Authorization"]["from"]
        with self.tx_lock:
            try:
                self.ev.rpc("eth_call", [{"from": cfg["facilitator"], "to": to, "data": "0x" + data.hex()}, "latest"])
            except Exception as e:  # noqa: BLE001
                return {"ok": False, "why": f"eth_call menolak sebelum kirim: {str(e)[:200]}"}
            r = self.ev.send(self.pk, to, data, gas=GAS_CAP)
        if not receipt_ok(r):
            return {"ok": False, "why": "settle revert", "tx": r.get("transactionHash")}
        if not paid_in_receipt(r, cfg["token"], payer, cfg["facilitator"], atomic):
            return {"ok": False, "why": "tx sukses tetapi Transfer pembeli -> payTo sejumlah tagihan tidak ada di receipt", "tx": r.get("transactionHash")}
        return {"ok": True, "tx": r["transactionHash"], "payer": payer}

    def faucet(self, addr: str, cfg: dict) -> Tuple[int, dict]:
        from evm import calldata, receipt_ok
        if not ADDR_RE.match(addr or ""):
            return 400, {"error": "alamat tidak sah"}
        day = time.strftime("%Y-%m-%d", time.gmtime(self.now()))
        if day != self.faucet_day:
            self.faucet_day, self.faucet_count = day, 0
        a = addr.lower()
        if self.now() - self.faucet_seen.get(a, 0) < 24 * 3600:
            return 429, {"error": "alamat ini sudah diisi dalam 24 jam terakhir"}
        if self.faucet_count >= FAUCET_DAILY_MAX:
            return 429, {"error": "batas faucet harian tercapai"}
        bal = self.ev.call_decode(cfg["token"], "balanceOf(address)", ("address",), (addr,), ("uint256",))[0]
        if bal >= FAUCET_IF_BELOW:
            return 200, {"dikirim": 0, "saldo_atomic": int(bal), "catatan": "saldo sudah cukup (>= 0,1 FAB)"}
        with self.tx_lock:
            r = self.ev.send(self.pk, cfg["token"], calldata("transfer(address,uint256)", ("address", "uint256"), (addr, FAUCET_ATOMIC)))
        if not receipt_ok(r):
            return 502, {"error": "kirim FAB gagal", "tx": r.get("transactionHash")}
        self.faucet_seen[a] = self.now()
        self.faucet_count += 1
        return 200, {"dikirim_atomic": FAUCET_ATOMIC, "tx": r["transactionHash"], "token": cfg["token"]}

    def tg_send(self, chat_id: int, text: str, button: Optional[Tuple[str, str]] = None) -> None:
        """`button` = (label, url) -> tombol Mini App (`web_app`) di bawah pesan: halaman web Fabius terbuka DI DALAM Telegram."""
        if not self.tg_token:
            return
        msg = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
        if button:
            msg["reply_markup"] = {"inline_keyboard": [[{"text": button[0], "web_app": {"url": button[1]}}]]}
        body = json.dumps(msg).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{self.tg_token}/sendMessage", data=body, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=15).read()
        except Exception as e:  # noqa: BLE001
            self.log(f"telegram sendMessage gagal: {type(e).__name__}")

    def handle_signal(self, path_bot: str, path_bar: Optional[str], hdr: Optional[str], tg: Optional[str]) -> Tuple[int, dict, dict]:
        self.data.refresh()
        led, cfg = self.data.ledgers(), self.data.cfg()
        if not (cfg["token"] and cfg["facilitator"]):
            return 503, {"error": "gerbang belum dikonfigurasi (deployments/97.json x402_sinyal)"}, {}
        try:
            q = quote(led, path_bot, path_bar)
        except KeyError as e:
            return 404, {"error": str(e)}, {}
        resource = f"{self.public_url}/sinyal/{q['bot']}/{q['bar']}"
        desc = f"Fabius {q['bot']} bar {q['bar']}: niat posisi + bukti komit/validasi ({q['fab']:g} FAB, harga {q['alasan']})"
        if not hdr:
            req = {"x402Version": 2, "error": "PAYMENT-SIGNATURE header is required", "resource": {"url": resource, "description": desc, "mimeType": "application/json"},
                   "accepts": accepts_for(resource, cfg["token"], cfg["facilitator"], q["atomic"], desc), "teaser": q["teaser"], "harga": {k: q[k] for k in ("atomic", "fab", "alasan")}}
            b64 = base64.b64encode(json.dumps(req, sort_keys=True).encode()).decode()
            return 402, {"teaser": q["teaser"], "harga": req["harga"], "bayar": "x402 v2 exact, permit2 + eip2612GasSponsoring (pembeli nol gas)"}, \
                {"PAYMENT-REQUIRED": b64, "X-PAYMENT-REQUIRED": b64}
        pay = decode_payment(hdr)
        if not pay:
            return 400, {"error": "PAYMENT-SIGNATURE tidak bisa didekode"}, {}
        why = check_payment(pay, cfg["token"], cfg["facilitator"], q["atomic"], int(self.now()))
        if why:
            return 402, {"error": f"pembayaran ditolak: {why}", "expected": {"amount": str(q["atomic"]), "asset": cfg["token"], "payTo": cfg["facilitator"]}}, {}
        res = self.settle(pay, cfg, q["atomic"])
        if not res.get("ok"):
            return 402, {"error": "settlement gagal", "detail": res}, {}
        cv, reg = self.views(cfg)
        try:
            ser = self.data.series(q["bot"])
        except Exception as e:  # noqa: BLE001 - rincian gagal dibaca tidak boleh membatalkan paket yang sudah DIBAYAR
            self.log(f"rincian {q['bot']} tak terbaca: {type(e).__name__}: {str(e)[:120]}")
            ser = None
        body = package(led, q["bot"], q["bar"], cfg, cv, reg, ser)
        body["pembayaran"] = {"tx": res["tx"], "payer": res["payer"], "atomic": q["atomic"], "token": cfg["token"]}
        self.log(f"TERJUAL {q['bot']} {q['bar']} {q['fab']:g} FAB pembeli {res['payer']} tx {res['tx']}")
        if tg:
            t = tg_parse(self.tg_secret, tg, int(self.now()))
            if t and t["b"] == q["bot"]:
                self.tg_send(int(t["c"]), fmt_package(body))
        resp = {"success": True, "transaction": res["tx"], "network": NETWORK, "payer": res["payer"]}
        b64 = base64.b64encode(json.dumps(resp, sort_keys=True).encode()).decode()
        return 200, body, {"PAYMENT-RESPONSE": b64, "X-PAYMENT-RESPONSE": b64}


RULE_EN = {   # terjemahan TAMPILAN; teks yang dikunci (spec `metode`, Indonesia) tetap ikut di paket sebagai `rincian.aturan`
    "B1-TREND": "long when the daily close is above the close N days earlier, otherwise flat (time-series momentum, long/flat)",
    "B2-RS": "long the top k and short the bottom k by L-day return (relative-strength rotation, dollar-neutral); 7 sub-books rotated weekly on different UTC days",
    "B3-CARRY": "long spot + short perp while the 7-day average funding (annualised) is above theta, otherwise flat",
    "B4-LISTING-FADE": "short newly listed perps at the close of day 1; close after H days; small size, isolated margin",
    "B5-CORE-RWA": "BTC and gold weighted by 1/sigma (std of daily returns over L days); rebalanced monthly",
    "B6-BOUNCE": "buy when the price z-score (N-day mean and std) is below -z_entry; exit when z >= 0 (long/flat)",
}


def _px(x: float) -> str:
    return f"{x:,.2f}" if x >= 100 else (f"{x:.4f}" if x >= 1 else f"{x:.6f}")


def fmt_package(p: dict) -> str:
    r = p.get("rincian") or {}
    lines = [f"Fabius {p['bot']} · bar {p['bar']} (paper position intents, not orders)"]
    if r:
        lines.append(f"Rule: {RULE_EN.get(p['bot'], r['aturan'])} (param {r['param']}). No TP/SL outside the rule; judged on the daily close.")
        ch = r.get("perubahan") or {}
        lines.append(f"Changes vs previous bar: enter {', '.join(ch.get('masuk') or []) or '-'} · exit {', '.join(ch.get('keluar') or []) or '-'}")
    aset = (r.get("aset") or {}) if r else {}
    if aset and any("keluar_berikut" in d for d in aset.values()):
        lines.append("asset · side · weight · entry (date @ price, PnL) · exit next bar if close <= level (distance)")
        for a, d in sorted(aset.items(), key=lambda kv: kv[1].get("keluar_berikut", {}).get("jarak", -9), reverse=True):
            e = d.get("masuk")
            ent = f"{e['bar']} @ {_px(e['harga'])} ({e['pnl'] * 100:+.1f}%)" if e else f"enters if close > {_px(d['masuk_bila']['di_atas'])}"
            k = d["keluar_berikut"]
            lines.append(f"  {a} · {d['sisi']} · {d['bobot'] * 100:.2f}% · {ent} · {_px(k['level'])} ({k['jarak'] * 100:+.1f}%)")
        if r.get("terdekat_keluar"):
            lines.append(f"Closest to exit: {r['terdekat_keluar']}. Exit levels move every day (60-day window) = a trailing stop on the daily close.")
    else:
        tg = sorted(p.get("targets", {}).items(), key=lambda kv: -abs(float(kv[1])))
        lines += [f"  {a}: {float(w):+.4f}" for a, w in tg[:16]] or ["  flat (no positions)"]
    k = p.get("komit") or {}
    v = p.get("validasi_erc8004")
    lines.append(f"commitId {p['commitId'][:18]}… · committed on-chain: {'yes' if k.get('ada') else 'not yet'}"
                 + (f" · ERC-8004 validation: {v['skor']}" if v and v.get("dijawab") else ""))
    if p.get("pembayaran"):
        lines.append(f"paid {p['pembayaran']['atomic'] / 1e6:g} FAB · tx {p['pembayaran']['tx']}")
    lines.append("Paper position intents at 1x; not investment advice. Testnet only.")
    return "\n".join(lines)


def make_handler(gate: Gate):
    class H(BaseHTTPRequestHandler):
        def log_message(self, fmt, *a):
            gate.log(f"{self.command} {self.path.split('?')[0]} -> {a[1] if len(a) > 1 else ''}")

        def _send(self, code: int, body: dict, extra: Optional[dict] = None) -> None:
            raw = json.dumps(body, ensure_ascii=False, sort_keys=True).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Expose-Headers", "PAYMENT-REQUIRED, X-PAYMENT-REQUIRED, PAYMENT-RESPONSE, X-PAYMENT-RESPONSE")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(raw)

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, PAYMENT-SIGNATURE, X-PAYMENT")
            self.send_header("Access-Control-Max-Age", "600")
            self.end_headers()

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            parts = [x for x in u.path.split("/") if x]
            qs = urllib.parse.parse_qs(u.query)
            try:
                if not parts:
                    gate.data.refresh()
                    led, cfg = gate.data.ledgers(), gate.data.cfg()
                    prices = {}
                    for b in sorted(led):
                        try:
                            q = quote(led, b)
                            prices[b] = {"bar": q["bar"], "atomic": q["atomic"], "fab": q["fab"], "confidence": q["teaser"]["confidence_pct"], "label": q["teaser"]["label"]}
                        except KeyError:
                            continue
                    return self._send(200, {"nama": "Fabius x402 - paket sinyal terverifikasi (testnet 97)", "token": cfg["token"], "simbol": "FAB", "proxy": PROXY,
                                            "payTo": cfg["facilitator"], "network": NETWORK, "harga": prices, "harga_kunci": harga.status()["state"],
                                            "rute": ["/teaser/<bot>", "/sinyal/<bot>[/<bar>]", "POST /faucet"], "repo_head": gate.data.head})
                if parts[0] == "teaser" and len(parts) == 2:
                    gate.data.refresh()
                    q = quote(gate.data.ledgers(), parts[1])
                    return self._send(200, {"teaser": q["teaser"], "harga": {k: q[k] for k in ("bar", "atomic", "fab", "alasan")}})
                if parts[0] == "sinyal" and len(parts) in (2, 3):
                    hdr = self.headers.get("PAYMENT-SIGNATURE") or self.headers.get("X-PAYMENT")
                    code, body, extra = gate.handle_signal(parts[1], parts[2] if len(parts) == 3 else None, hdr, (qs.get("tg") or [None])[0])
                    return self._send(code, body, extra)
                return self._send(404, {"error": "rute tidak dikenal"})
            except KeyError as e:
                return self._send(404, {"error": str(e)})
            except Exception as e:  # noqa: BLE001
                gate.log(f"GALAT {type(e).__name__}: {str(e)[:200]}")
                return self._send(500, {"error": f"{type(e).__name__}"})

        def do_POST(self):
            if urllib.parse.urlparse(self.path).path.rstrip("/") != "/faucet":
                return self._send(404, {"error": "rute tidak dikenal"})
            try:
                n = min(int(self.headers.get("Content-Length") or 0), 4096)
                addr = (json.loads(self.rfile.read(n) or b"{}") or {}).get("address", "")
                code, body = gate.faucet(addr, gate.data.cfg())
                return self._send(code, body)
            except Exception as e:  # noqa: BLE001
                gate.log(f"GALAT faucet {type(e).__name__}: {str(e)[:200]}")
                return self._send(500, {"error": f"{type(e).__name__}"})
    return H


# ---------------------------------------------------------------- bot Telegram (P138d, F-D101): perintah Inggris, dompet = Privy (Mini App)
# Dompet TIDAK dibuat di sini (keputusan F-D101: opsi custodial dibatalkan). Membeli dan melihat dompet terjadi di halaman web `/beli/<bot>` yang dibuka
# sebagai Telegram Mini App: Privy login otomatis lewat Telegram, akun Google yang ditautkan memakai dompet yang SAMA. Tautan `?tg=` bertanda membuat
# paket juga dikirim ke chat sesudah settle. Beli otomatis dari chat (session signer Privy) = tahap berikutnya.

HELP = ("Fabius - verified trading signals, paid per signal with x402 on BNB testnet (chain 97). FAB is a test token with no value.\n\n"
        "/bots - bots, prices, confidence\n/signal <BOT> - free teaser (no assets, no direction)\n"
        "/buy <BOT> - open the Fabius app inside Telegram and pay with x402 (sign in with Telegram or Google, no gas)\n"
        "/wallet - your wallet (same wallet as on the Fabius website when you link Google)\n\n"
        "Every signal is committed on-chain before the market moves; anyone can verify it.")
COMMANDS = [("bots", "bots, prices, confidence"), ("signal", "free teaser: /signal B1-TREND"), ("buy", "buy with x402: /buy B1-TREND"),
            ("wallet", "your wallet"), ("help", "how it works")]


def _teaser_en(q: dict) -> str:
    t = q["teaser"]
    conf = "not measured yet" if t["confidence_pct"] is None else f"{t['confidence_pct']}% ({'early, not meaningful yet' if t['fd16'] == 'BELUM CUKUP DATA' else 'measured'})"
    k = t["kematangan"]
    return (f"{q['bot']} · bar {q['bar']}\nConfidence (forward record): {conf}\nRole: {t.get('status') or '-'} · locked backtest gate: {t.get('gerbang_v1') or '-'}"
            f" · forward test F-D16: {t['fd16']}\nProgress: signals {k['sinyal'][0]}/{k['sinyal'][1]}, settled days {k['hari'][0]}/{k['hari'][1]}, "
            f"months {k['bulan'][0]}/{k['bulan'][1]}\nPrice: {q['fab']:g} FAB ({'base price' if q['atomic'] == harga.HargaParams().dasar else 'confidence tier'}, locked table)")


def tg_reply(gate: "Gate", chat_id: int, text: str, private: bool = True) -> Tuple[str, Optional[Tuple[str, str]]]:
    """-> (teks, tombol Mini App atau None)."""
    cmd, _, arg = text.partition(" ")
    cmd = cmd.split("@")[0].lower()
    bot = arg.strip().upper()
    gate.data.refresh()
    led = gate.data.ledgers()
    if cmd in ("/start", "/help"):
        return HELP, None
    if cmd == "/bots":
        rows = []
        for b in sorted(led):
            try:
                q = quote(led, b)
                c = q["teaser"]["confidence_pct"]
                rows.append(f"{b}: {q['fab']:g} FAB · confidence {'not measured yet' if c is None else f'{c}%'}")
            except KeyError:
                continue
        return "Bots with a forward clock (latest bar):\n" + "\n".join(rows) + "\n\n/signal <BOT> for the teaser, /buy <BOT> to buy.", None
    if cmd in ("/signal", "/buy"):
        if bot not in led:
            return f"Usage: {cmd} <BOT>. Bots: {', '.join(sorted(led))}", None
        q = quote(led, bot)
        link = f"{gate.web_url}/beli/{bot}?tg={tg_link(gate.tg_secret, chat_id, bot, q['bar'], int(gate.now()))}"
        head = _teaser_en(q) if cmd == "/signal" else f"{bot} · bar {q['bar']} · {q['fab']:g} FAB"
        if not private:
            return head + f"\n\nBuy in a private chat with me, or on the web: {gate.web_url}/beli/{bot}", None
        return head + "\n\nTap the button: sign in with Telegram (or Google), get free FAB, pay with x402 (no gas). The signal is also sent here.", \
            (f"Buy {bot} · {q['fab']:g} FAB", link)
    if cmd == "/wallet":
        b = sorted(led)[0] if led else "B1-TREND"
        return ("Your wallet lives in the Fabius app (Privy): open it below and sign in with Telegram. Link your Google account there and the "
                "website uses the SAME wallet. Testnet only; you need no tBNB."), (("Open my wallet", f"{gate.web_url}/beli/{b}") if private else None)
    return "Unknown command. /help", None


def telegram_loop(gate: "Gate", stop: threading.Event) -> None:
    offset = 0
    base = f"https://api.telegram.org/bot{gate.tg_token}"
    try:
        body = json.dumps({"commands": [{"command": c, "description": d} for c, d in COMMANDS]}).encode()
        urllib.request.urlopen(urllib.request.Request(f"{base}/setMyCommands", data=body, headers={"Content-Type": "application/json"}), timeout=15).read()
    except Exception as e:  # noqa: BLE001
        gate.log(f"telegram setMyCommands gagal: {type(e).__name__}")
    while not stop.is_set():
        try:
            with urllib.request.urlopen(f"{base}/getUpdates?timeout=25&offset={offset}", timeout=40) as r:
                ups = json.loads(r.read().decode()).get("result", [])
        except Exception as e:  # noqa: BLE001
            gate.log(f"telegram getUpdates gagal: {type(e).__name__}")
            stop.wait(10)
            continue
        for u in ups:
            offset = max(offset, int(u["update_id"]) + 1)
            m = u.get("message") or {}
            chat, text = m.get("chat") or {}, (m.get("text") or "").strip()
            if not chat.get("id") or not text.startswith("/"):
                continue
            try:
                msg, button = tg_reply(gate, int(chat["id"]), text, chat.get("type") == "private")
                gate.tg_send(int(chat["id"]), msg, button)
            except Exception as e:  # noqa: BLE001
                gate.log(f"telegram balasan gagal: {type(e).__name__}: {str(e)[:120]}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Gerbang x402 per sinyal Fabius (P138a).")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8050")))
    ap.add_argument("--local", action="store_true", help="pakai repo lokal ini (tanpa klon/sinkron)")
    a = ap.parse_args()
    import evm as evmmod
    pk = facilitator_key()
    if not pk:
        print(f"{KEY_VAR} tidak ada - gerbang hanya bisa menjawab 402/teaser, tidak bisa settle")
    if a.local:
        data = Data(ROOT)
    else:
        import operator_loop as ol
        data = Data(os.environ.get("WORKDIR_X402", "/tmp/fabius-x402"), ol.sync)
        data.refresh(every_s=0)
    ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
    ev.chain_check()
    public = os.environ.get("X402_PUBLIC_URL") or (f"https://{os.environ['RAILWAY_PUBLIC_DOMAIN']}" if os.environ.get("RAILWAY_PUBLIC_DOMAIN") else f"http://127.0.0.1:{a.port}")
    gate = Gate(data, pk, public, os.environ.get("WEB_URL", "https://fabius-one.vercel.app"), ev, os.environ.get("TELEGRAM_SIGNAL_BOT_TOKEN"),
                log=lambda m: print(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {m}", flush=True))
    cfg = data.cfg()
    gate.log(f"gerbang x402 mulai | port {a.port} | publik {public} | token {cfg['token']} | payTo {cfg['facilitator']} | kunci {'ADA' if pk else 'TIDAK'} | "
             f"harga {harga.status()['state']} | telegram {'nyala' if gate.tg_token else 'mati'} | repo {data.head}")
    if pk and cfg["facilitator"] and evmmod.address_of(pk).lower() != cfg["facilitator"].lower():
        gate.log(f"PERINGATAN: kunci fasilitator {evmmod.address_of(pk)} != x402_sinyal.facilitator {cfg['facilitator']} - settle akan ditolak")
    stop = threading.Event()
    if gate.tg_token:
        threading.Thread(target=telegram_loop, args=(gate, stop), daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", a.port), make_handler(gate)).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

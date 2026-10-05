"""Gerbang x402 per sinyal Fabius (P138a, F-D98/F-D99/F-D100): service Railway `fabius-x402`, testnet 97, token Fabius Credit (FAB).

Yang dijual (F-D99): paket sinyal SIAP PAKAI untuk satu (bot, bar) - niat posisi dari tick ledger + bukti (commitId, waktu komit, status ungkap,
validasi ERC-8004) - segera sesudah komit. Bukan rahasia: bot B1-B6 deterministik dan terbuka, siapa pun bisa menghitung ulang isinya.
Harga per (bot, bar) = `engine/harga.py` (tabel terkunci, dari confidence P137), beku per bar.

Rute:
  GET  /                      info: token, proxy, payTo, harga tiap bot, cara bayar
  GET  /teaser/<bot>          gratis: teaser confidence + harga bar terakhir (tanpa aset/arah/ukuran)
  Rute publik berbahasa Inggris (P146): /signal, /analysts[/<close>|/full|/scores], /active; nama lama /sinyal, /analis, /aktif tetap dilayani.
  GET  /signal/<bot>[/<bar>]  402 + PAYMENT-REQUIRED; dengan PAYMENT-SIGNATURE (x402 v2, exact, permit2 + eip2612GasSponsoring) -> settle -> paket
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
import datetime as dt
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
from typing import Callable, Dict, List, Optional, Tuple

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
import sinyal_gambar as sg                                                    # noqa: E402
import analis as an                                                           # noqa: E402
import privy_server as pv                                                     # noqa: E402
import meja                                                                   # noqa: E402

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


# ---------------------------------------------------------------- alasan agent analis: terbuka vs berbayar (P145, F-D104)
AKSES_HARI = 7          # alasan lengkap di app = login + membeli >= 1 sinyal dalam 7 hari terakhir (dompet yang sama)
AKSES_BAR_MAX = 14      # bar terakhir yang dikirim ke pembeli (riwayat lebih tua tetap di arsip publik ledger/analis)
TERKUNCI_EN = "sealed until the bar closes: full reasoning in the Fabius app (sign in + any signal bought in the last 7 days)"
TIDAK_TERBIT_EN = "reasoning not published at the agent's card URL (or its sha256 did not match the on-chain reasonHash)"
LANGKAH_LUAR = [   # P151 (F-D107): cara agent luar ikut; semuanya bisa diperiksa tanpa izin Fabius
    "1. Register an ERC-8004 identity on the IdentityRegistry (register(string agentURI)). Your card JSON at agentURI must contain "
    "\"fabius\": {\"reasons\": \"https://<your host>/<path>/{bar_close}.json\"}.",
    "2. Before each daily close (00:00 UTC), read this input, pick ONE bot, and call SelectionAnchor.pick(agentId, barClose, bytes32(bot), confidence 0-100, "
    "reasonHash) from the agent's owner or agent wallet. reasonHash = sha256 of your reasoning JSON in canonical form (sorted keys, no spaces, UTF-8).",
    "3. After the close, serve that exact JSON at your reasons URL with {bar_close} filled in. It must contain agent_id, bar_close and pilihan.bot equal "
    "to your on-chain pick (schema below), otherwise Fabius rejects it.",
    "4. Fabius scores every pick against the identity bot from the public ledger (/analysts/scores) and lists you on /analysts. External agents do not "
    "yet influence which bot Fabius trades (F-D107).",
    "Optional data (P140): MCP tools fabius_dexscreener, fabius_rugcheck, fabius_bubblemaps, fabius_fomo at https://fabius-one.vercel.app/mcp (DEX/memecoin "
    "context; Fabius bots trade 16 major perps).",
]


def tutup_alasan(r: dict, now_s: int) -> dict:
    """Alasan pilihan yang barnya BELUM tutup = isi berbayar; yang publik hanya bot, keyakinan agent, dan reasonHash (semuanya sudah on-chain).
    Sesudah bar tutup alasan terbit penuh supaya siapa pun bisa mencocokkan sha256-nya dengan reasonHash on-chain (dan diarsip ke repo publik)."""
    a = r.get("alasan") or {}
    if int(a.get("bar_close") or 0) <= now_s:
        return r
    keep = {k: a[k] for k in ("agent", "agent_id", "nama", "model", "bar_close", "dibuat_utc") if k in a}
    return {**r, "alasan": {**keep, "terkunci": TERKUNCI_EN}}


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

    def cfg_raw(self) -> dict:
        with open(os.path.join(self.workdir, "deployments", "97.json"), encoding="utf-8") as f:
            return json.load(f)

    def active_bot(self) -> Optional[str]:
        """Bot yang sedang dipakai Fabius = penghuni buku slot (bot identitas dulu; `ledger/book/buku.jsonl`). Akan diganti aturan pemilihan agent
        analis yang dikunci (P141-P143); sampai itu, `/buy` tanpa argumen = bot ini."""
        try:
            from engine import book_live
            book = book_live.current_book(ledger.load(os.path.join(self.workdir, "ledger", "book", "buku.jsonl")))
        except Exception:  # noqa: BLE001
            return None
        ids = [e.bot_id for e in book if getattr(e, "identity", False)] + [e.bot_id for e in book]
        return ids[0] if ids else None


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
        self.privy: Optional[pv.Privy] = None              # P138e: diisi main() bila PRIVY_APP_ID/SECRET/AUTH_PRIVATE_KEY lengkap
        self.faucet_seen: Dict[str, float] = {}
        self.faucet_day, self.faucet_count = "", 0
        self.tg_secret = hashlib.sha256(b"fabius-tg-link|" + (pk or "tanpa-kunci").encode()).digest()
        self.analis_dir = os.environ.get("ANALIS_DIR") or ("/data/analis" if os.path.isdir("/data") else os.path.join(data.workdir, "data", "analis"))
        self.buys_path = os.path.join(os.path.dirname(self.analis_dir), "pembelian.jsonl")     # P145: pembeli -> akses alasan lengkap
        self.buys_lock = threading.Lock()
        self.luar_dir = os.path.join(self.analis_dir, "luar")                                # P151: alasan agent luar yang hash + skemanya cocok
        self._disc: dict = {}                                                                # kursor pemindaian event Picked
        self._kartu: Dict[int, tuple] = {}                                                   # agent_id -> (waktu, kartu)
        self._luar_coba: Dict[str, float] = {}
        self.meja_dir = os.path.join(os.path.dirname(self.analis_dir), "meja")                # P152: rekaman, siklus, buku meja AI 5 menit
        self.meja_lock = threading.Lock()
        self._kabar: tuple = (0.0, None)

    def kabar_cache(self, umur_s: int = 900) -> Optional[List[dict]]:
        """Judul berita untuk agent berita di meja: dibaca paling sering tiap 15 menit (bukan tiap 5 menit)."""
        t, j = self._kabar
        if j is None or time.time() - t > umur_s:
            try:
                import kabar
                j = kabar.kabar(int(time.time()))["judul"]
            except Exception as e:  # noqa: BLE001
                self.log(f"kabar meja gagal: {type(e).__name__}: {str(e)[:120]}")
                j = j or []
            self._kabar = (time.time(), j)
        return j

    def _meja_path(self, kind: str, t: int) -> str:
        return os.path.join(self.meja_dir, kind, time.strftime("%Y-%m-%d", time.gmtime(t)) + ".jsonl")

    def meja_muat(self) -> Tuple[Dict[str, dict], Dict[str, str]]:
        try:
            with open(os.path.join(self.meja_dir, "buku.json"), encoding="utf-8") as f:
                d = json.load(f)
            return d.get("buku") or {}, d.get("ringkasan") or {}
        except (OSError, ValueError):
            return {}, {}

    def meja_simpan(self, rek: List[dict], sik: dict, books: Dict[str, dict], ring: Dict[str, str]) -> None:
        with self.meja_lock:
            for kind, rows in (("rekaman", rek), ("siklus", [sik])):
                path = self._meja_path(kind, sik["siklus"])
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "a", encoding="utf-8", newline="\n") as f:
                    for r in rows:
                        f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
            tmp = os.path.join(self.meja_dir, "buku.json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"buku": books, "ringkasan": ring}, f, ensure_ascii=False, sort_keys=True)
            os.replace(tmp, os.path.join(self.meja_dir, "buku.json"))
        self._meja = None

    def _meja_baca(self, kind: str, hari: int = 2) -> List[dict]:
        now, out = int(self.now()), []
        for k in range(hari - 1, -1, -1):
            path = self._meja_path(kind, now - k * 86_400)
            if os.path.exists(path):
                out += [json.loads(ln) for ln in open(path, encoding="utf-8") if ln.strip()]
        return out

    def meja_view(self, max_age_s: int = 20) -> dict:
        """Ringkasan publik meja: buku per agent + konsensus (ekuitas pada harga isi terakhir), deret ekuitas 24 jam, 40 rekaman terakhir, komit terakhir."""
        st = getattr(self, "_meja", None)
        if st and time.time() - st["t"] < max_age_s:
            return st
        rek, sik = self._meja_baca("rekaman"), self._meja_baca("siklus")
        books, _ = self.meja_muat()
        harga = (sik[-1].get("harga") if sik else None) or {}
        cut = int(self.now()) - 86_400
        out_books = []
        for name in [meja.KONSENSUS] + sorted(b for b in books if b != meja.KONSENSUS):
            b = books.get(name)
            if not b:
                continue
            e = meja.ekuitas(b, harga)
            mine = [r for r in rek if r["agent"] == name]
            last = next((r for r in reversed(mine) if r.get("status", "ok") == "ok"), None)
            nama = "Fabius consensus" if name == meja.KONSENSUS else next((a["name"] for a in an.AGENTS if a["slug"] == name), name)
            out_books.append({"agent": name, "nama": nama, "ekuitas": round(e, 2), "hasil_pct": round((e / meja.PARAMS["modal_awal"] - 1) * 100, 3),
                              "biaya": round(b.get("biaya", 0), 2), "n_trade": b.get("n_trade", 0),
                              # posisi yang BENAR-BENAR terisi (qty x harga / ekuitas), bukan target: target < ambang 2 % tidak ditransaksikan
                              "posisi": {a: round(q["qty"] * harga.get(a, q["masuk"]) / e, 4) for a, q in sorted(b.get("posisi", {}).items()) if e},
                              "target": {a: round(t["w"], 4) for a, t in sorted((b.get("target") or {}).items()) if abs(t.get("w", 0)) > 1e-9},
                              "deret": [[r["siklus"], r["ekuitas"]] for r in mine if r["siklus"] >= cut],
                              "status_terakhir": mine[-1].get("status", "ok") if mine else None,
                              "keputusan_terakhir": (last.get("keputusan") or {"ringkasan": last.get("dasar"), "target": last.get("target")}) if last else None})
        out = {"t": time.time(), "params": meja.PARAMS, "params_sha": meja.params_sha(),
               "anchor": self.data.cfg_raw().get("contracts", {}).get("DeskAnchor"), "buku": out_books, "rekaman": rek[-40:],
               "siklus_terakhir": ({k: sik[-1].get(k) for k in ("siklus", "root", "tx", "status", "n")} if sik else None),
               "siklus_24j": sum(1 for x in sik if x["siklus"] >= cut), "komit_24j": sum(1 for x in sik if x["siklus"] >= cut and x.get("status") == "dikomit")}
        self._meja = out
        return out

    def data_simpan(self, snap: dict) -> None:
        """P153 (F1): snapshot data luas meja v2 -> /data/meja/fitur/<tgl>.jsonl (sha atas isi tanpa `durasi_s`)."""
        with self.meja_lock:
            path = self._meja_path("fitur", snap["t"])
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(snap, ensure_ascii=False, sort_keys=True) + "\n")
        self._data_last, self._data_view = snap, None

    def data_view(self, max_age_s: int = 60) -> dict:
        """Kesehatan data 24 jam (kriteria keluar F1, Epik 11 §8) + snapshot terakhir."""
        st = getattr(self, "_data_view", None)
        if st and time.time() - st["t_view"] < max_age_s:
            return st
        rows = [r for r in self._meja_baca("fitur") if r["t"] >= int(self.now()) - 86_400]
        sumber = sorted({k for r in rows for k in r.get("kesehatan", {})})
        rk = {k: {"cakupan_rata": round(sum((r["kesehatan"].get(k) or {}).get("cakupan") or 0 for r in rows) / len(rows), 4) if rows else None,
                  "siklus_cakupan_penuh": sum(1 for r in rows if ((r["kesehatan"].get(k) or {}).get("cakupan") or 0) >= 0.95),
                  "status_terakhir": (rows[-1]["kesehatan"].get(k) or {}).get("status") if rows else None} for k in sumber}
        last = rows[-1] if rows else getattr(self, "_data_last", None)
        out = {"t_view": time.time(), "snapshot_24j": len(rows), "durasi_maks_s": max((r.get("durasi_s") or 0 for r in rows), default=None),
               "lambat_24j": sum(1 for r in rows if (r.get("durasi_s") or 0) > 240), "sumber": rk,
               "registry_sha": (last or {}).get("registry_sha"), "terakhir": last}
        self._data_view = out
        return out

    def meja_proof(self, h: str) -> Tuple[int, dict]:
        rek = next((r for r in self._meja_baca("rekaman", 3) if r.get("hash") == h), None)
        if rek is None:
            return 404, {"error": "hash tidak ada di rekaman 3 hari terakhir"}
        sik = next((x for x in self._meja_baca("siklus", 3) if x["siklus"] == rek["siklus"]), None)
        if sik is None:
            return 404, {"error": "siklus rekaman tidak ditemukan"}
        isi_tanpa_hash = {k: v for k, v in rek.items() if k != "hash"}
        return 200, {"rekaman": rek, "hash_dihitung_ulang": meja.sha(isi_tanpa_hash), "root": sik.get("root"), "proof": meja.proof_of(sik["daun"], h),
                     "siklus": sik["siklus"], "tx": sik.get("tx"), "anchor": self.data.cfg_raw().get("contracts", {}).get("DeskAnchor"),
                     "cara_cek": "sha256(JSON kanonis rekaman tanpa 'hash') = hash; Merkle proof (engine/chain.py, pasangan terurut keccak) -> root = "
                                 "DeskAnchor.rootOf(siklus); tx dikirim sebelum siklus + 300 s"}

    def record_buy(self, bot: str, bar: str, payer: str, tx: str, atomic: int) -> None:
        try:
            with self.buys_lock:
                os.makedirs(os.path.dirname(self.buys_path), exist_ok=True)
                with open(self.buys_path, "a", encoding="utf-8", newline="\n") as f:
                    f.write(json.dumps({"t": int(self.now()), "bot": bot, "bar": bar, "payer": payer.lower(), "tx": tx, "atomic": atomic},
                                       sort_keys=True) + "\n")
        except OSError as e:                                           # catatan gagal tidak boleh membatalkan paket yang sudah DIBAYAR
            self.log(f"catat pembelian gagal: {type(e).__name__}")

    def last_buy(self, addrs: List[str]) -> Optional[dict]:
        want, best = {a.lower() for a in addrs}, None
        if want and os.path.exists(self.buys_path):
            for ln in open(self.buys_path, encoding="utf-8"):
                if ln.strip():
                    r = json.loads(ln)
                    if r.get("payer") in want and (best is None or r["t"] > best["t"]):
                        best = r
        return best

    def analis_lengkap(self, auth: Optional[str]) -> Tuple[int, dict]:
        """Alasan lengkap + hash + skor untuk user Privy yang login DAN membeli >= 1 sinyal dalam AKSES_HARI hari (F-D104)."""
        if self.privy is None:
            return 503, {"error": "login Privy belum dikonfigurasi di gerbang"}
        tok = auth[7:].strip() if auth and auth[:7].lower() == "bearer " else ""
        if not tok:
            return 401, {"error": "sign in first (Authorization: Bearer <Privy access token>)"}
        try:
            claims = pv.verify_access_token(tok, self.privy.app_id, self.privy.verification_key(), int(self.now()))
            user = self.privy.user(claims["sub"])
        except pv.PrivyError as e:
            return (401 if e.status == 401 else 502), {"error": str(e)}
        addrs = pv.Privy.wallet_addresses(user) if user else []
        b = self.last_buy(addrs)
        aktif = self.aktif_now().get("bot") or bookmod.IDENTITY_BOT_ID
        if b is None or self.now() - b["t"] > AKSES_HARI * 86400:
            return 402, {"error": f"no signal bought from this account's wallet in the last {AKSES_HARI} days", "syarat": f"buy >= 1 signal within {AKSES_HARI} days",
                         "dompet": addrs, "beli": f"{self.web_url}/buy"}
        recs = self.analis_records()
        closes = sorted({int(r["alasan"]["bar_close"]) for r in recs})[-AKSES_BAR_MAX:]
        v = self.analis_view()
        return 200, {"pilihan": [r for r in recs if int(r["alasan"]["bar_close"]) in closes], "papan": v["papan"], "skor": v["skor"],
                     "aktif": self.aktif_now(), "selection_anchor": self.data.cfg_raw().get("contracts", {}).get("SelectionAnchor"),
                     "akses": {"dompet": b["payer"], "pembelian_terakhir": {k: b[k] for k in ("t", "bot", "bar", "tx")},
                               "berlaku_sampai": b["t"] + AKSES_HARI * 86400},
                     "catatan": "reasonHash on-chain = sha256 JSON 'alasan' kanonis (sort_keys, tanpa spasi); pilihan dikomit SEBELUM bar_close"}

    def analis_dirs(self) -> List[str]:
        return [self.analis_dir, self.luar_dir, os.path.join(self.data.workdir, "ledger", "analis")]

    def picks_luar(self, acfg: dict) -> List[dict]:
        """Pilihan on-chain agent LUAR (P151): ditemukan dari event Picked, kartu dibaca ulang tiap 6 jam, alasan bar tutup diambil + diverifikasi."""
        sel = ((self.data.cfg_raw().get("erc8004") or {}).get("selection") or {})
        if not sel.get("block"):
            return []
        house = {int(a["agent_id"]) for a in acfg["agents"].values()}
        ids = [i for i in an.temukan_agent(self.ev, acfg["selection"], int(sel["block"]), self._disc) if i not in house][:an.LUAR_MAX]
        if not ids:
            return []
        luar = an.onchain_picks(self.ev, acfg["selection"], {f"x{i}": {"agent_id": i} for i in ids})
        for r in luar:
            r["luar"] = True
        now = time.time()
        for i in ids:
            if i not in self._kartu or now - self._kartu[i][0] > 6 * 3600:
                self._kartu[i] = (now, an.kartu_luar(self.ev, acfg["identity"], i))
        an.alasan_luar(luar, {i: self._kartu[i][1] for i in ids}, self.luar_dir, int(self.now()), log=self.log, coba=self._luar_coba)
        return luar

    def analis_records(self, close: Optional[int] = None) -> List[dict]:
        """Catatan alasan (berkas: rumah + luar terverifikasi) + pilihan on-chain yang belum punya catatan (bar terbuka / agent luar tanpa alasan terbit)."""
        recs = an.records(self.analis_dirs(), close)
        have = {(r["agent"], int(r["alasan"]["bar_close"])) for r in recs}
        v = self.analis_view()
        names = {**{a["slug"]: a["name"] for a in an.AGENTS}, **{f"x{i}": c["nama"] for i, c in v.get("kartu", {}).items()}}
        now = int(self.now())
        for pk in v["picks"]:
            if (close is not None and pk["bar_close"] != close) or (pk["agent"], pk["bar_close"]) in have:
                continue
            a = {"agent": pk["agent"], "agent_id": pk["agent_id"], "nama": names.get(pk["agent"], f"agent {pk['agent_id']}"), "bar_close": pk["bar_close"]}
            if pk["bar_close"] > now:
                a["terkunci"] = TERKUNCI_EN
            else:
                a["tidak_terbit"] = TIDAK_TERBIT_EN
            recs.append({"agent": pk["agent"], "bot": pk["bot"], "keyakinan": pk["keyakinan"], "reasonHash": pk["reasonHash"], "status": "dikomit",
                         "luar": bool(pk.get("luar")), "alasan": a})
        return sorted(recs, key=lambda r: (int(r["alasan"]["bar_close"]), int(r["alasan"].get("agent_id") or 0)))

    def analis_view(self, max_age_s: int = 600) -> dict:
        """Pilihan ON-CHAIN (SelectionAnchor) + skor (ledger final / provisional) + papan; disimpan 10 menit. Tanpa chain = kosong (bukan karangan)."""
        st = getattr(self, "_analis", None)
        if st and time.time() - st["t"] < max_age_s:
            return st
        out = {"t": time.time(), "picks": [], "skor": [], "papan": [], "kartu": {}}
        try:
            acfg = an.load_cfg(os.path.join(self.data.workdir, "deployments", "97.json"))
            if self.ev is not None and acfg.get("selection") and acfg.get("agents"):
                from paper_tick import Views
                picks = an.onchain_picks(self.ev, acfg["selection"], acfg["agents"])
                try:
                    picks += self.picks_luar(acfg)
                except Exception as e:  # noqa: BLE001 - agent luar gagal dibaca tidak boleh menghapus papan agent rumah
                    self.log(f"agent luar gagal: {type(e).__name__}: {str(e)[:160]}")
                out["picks"] = sorted(picks, key=lambda r: (r["bar_close"], r["agent_id"]))
                out["skor"] = an.skor(self.data.workdir, out["picks"], Views(os.path.join(self.data.workdir, "ledger", "bars")).get("provisional"))
                out["kartu"] = {i: c for i, (_, c) in self._kartu.items()}
                out["papan"] = an.papan(out["skor"], {f"x{i}": c["nama"] for i, c in out["kartu"].items()})
        except Exception as e:  # noqa: BLE001
            self.log(f"analis_view gagal: {type(e).__name__}: {str(e)[:160]}")
        self._analis = out
        return out

    def aktif_now(self) -> dict:
        """Bot yang dijual `/buy` tanpa argumen: aturan TERKUNCI engine/pemilih.py untuk penutupan bar tick terakhir bot identitas."""
        ident = self.data.active_bot() or bookmod.IDENTITY_BOT_ID
        led = self.data.ledgers()
        ticks = [r for r in led.get(ident, []) if r.get("type") == "tick"]
        if not ticks:
            return {"bot": ident, "alasan": "belum ada tick bot identitas", "alasan_en": "no tick yet", "bar_close": None, "pilihan": {}}
        close = sc.asof_s_of(max(ticks, key=lambda r: r["asof"]))
        v = self.analis_view()
        rumah = lambda xs: [x for x in xs if not x.get("luar")]                       # noqa: E731 - F-D107: agent luar belum ikut menentukan
        return an.bot_aktif(rumah(v["picks"]), rumah(v["skor"]), close, ident)


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

    def tg_send_photo(self, chat_id: int, png: bytes, caption: str) -> bool:
        """Unggah PNG langsung (multipart) - tidak ada URL publik untuk isi berbayar. False = gagal (pemanggil kirim teks)."""
        if not self.tg_token:
            return False
        b = "fabius" + hashlib.sha1(png).hexdigest()[:20]
        parts = [f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
                 for k, v in (("chat_id", str(chat_id)), ("caption", caption), ("parse_mode", "HTML"))]
        parts.append(f"--{b}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"fabius-signal.png\"\r\nContent-Type: image/png\r\n\r\n".encode() + png + b"\r\n")
        parts.append(f"--{b}--\r\n".encode())
        req = urllib.request.Request(f"https://api.telegram.org/bot{self.tg_token}/sendPhoto", data=b"".join(parts),
                                     headers={"Content-Type": f"multipart/form-data; boundary={b}"})
        try:
            urllib.request.urlopen(req, timeout=30).read()
            return True
        except Exception as e:  # noqa: BLE001
            self.log(f"telegram sendPhoto gagal: {type(e).__name__}")
            return False

    def deliver_tg(self, chat_id: int, body: dict) -> None:
        png = sg.render_png(body, RULE_EN.get(body["bot"]))
        if not (png and self.tg_send_photo(chat_id, png, sg.caption_html(body))):
            self.tg_send(chat_id, fmt_package(body))

    def handle_signal(self, path_bot: str, path_bar: Optional[str], hdr: Optional[str], tg: Optional[str]) -> Tuple[int, dict, dict]:
        self.data.refresh()
        led, cfg = self.data.ledgers(), self.data.cfg()
        if not (cfg["token"] and cfg["facilitator"]):
            return 503, {"error": "gerbang belum dikonfigurasi (deployments/97.json x402_sinyal)"}, {}
        try:
            q = quote(led, path_bot, path_bar)
        except KeyError as e:
            return 404, {"error": str(e)}, {}
        resource = f"{self.public_url}/signal/{q['bot']}/{q['bar']}"
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
        self.record_buy(q["bot"], q["bar"], res["payer"], res["tx"], q["atomic"])
        if tg:
            t = tg_parse(self.tg_secret, tg, int(self.now()))
            if t and t["b"] == q["bot"]:
                self.deliver_tg(int(t["c"]), body)
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
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, PAYMENT-SIGNATURE, X-PAYMENT")
            self.send_header("Access-Control-Max-Age", "600")
            self.end_headers()

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            parts = [x for x in u.path.split("/") if x]
            if parts:                                                    # rute English (P146) -> nama internal; nama lama tetap sah
                parts[0] = RUTE_EN.get(parts[0], parts[0])
                if parts[0] == "analis" and len(parts) == 2:
                    parts[1] = RUTE_EN.get(parts[1], parts[1])
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
                                            "rute": ["/teaser/<bot>", "/signal/<bot>[/<bar>]", "/active", "/analysts[/<close>|/scores|/full]", "POST /faucet"], "repo_head": gate.data.head})
                if parts[0] == "analis" and len(parts) == 2 and parts[1] == "skor":
                    v = gate.analis_view()
                    return self._send(200, {"papan": v["papan"], "pilihan_terskor": v["skor"], "aturan_bot_aktif": "engine/pemilih.py",
                                            "kunci_pemilih": an.pemilih.status()["state"],
                                            "catatan": "selisih = net paper bot pilihan - net bot identitas, bar yang sama; provisional = funding estimasi, final = settle ledger"})
                if parts[0] == "analis" and len(parts) == 2 and parts[1] == "lengkap":
                    code, body = gate.analis_lengkap(self.headers.get("Authorization"))
                    return self._send(code, body)
                if parts[0] == "analis" and len(parts) == 2 and parts[1] == "input":
                    close, raw = an.next_close(int(gate.now())), gate.data.cfg_raw()
                    return self._send(200, {"bar_close": close, "commit_before": close, "masukan": an.masukan(gate.data.workdir, close),
                                            "reasoning_schema": an.SKEMA_ALASAN, "steps": LANGKAH_LUAR, "chain_id": 97,
                                            "selection_anchor": raw.get("contracts", {}).get("SelectionAnchor"),
                                            "identity_registry": (raw.get("erc8004") or {}).get("identity"),
                                            "card_field": {"fabius": {"reasons": "https://example.com/fabius/{bar_close}.json"}},
                                            "house_prompt": {"system": an.SYSTEM, "user": an.prompt(an.masukan(gate.data.workdir, close))}})
                if parts[0] == "analis" and len(parts) == 2 and parts[1] == "registry":
                    v, acfg = gate.analis_view(), an.load_cfg(os.path.join(gate.data.workdir, "deployments", "97.json"))
                    names = {a["slug"]: a["name"] for a in an.AGENTS}
                    rumah = [{"agent_id": int(a["agent_id"]), "nama": names.get(s_, s_), "rumah": True, "model": a.get("model"), "kartu": a.get("uri")}
                             for s_, a in sorted((acfg.get("agents") or {}).items())]
                    luar = [{"agent_id": i, "nama": c["nama"], "rumah": False, "kartu": c["uri"], "alasan_url": c["alasan_url"], "galat": c["galat"]}
                            for i, c in sorted(v.get("kartu", {}).items())]
                    return self._send(200, {"agents": rumah + luar, "catatan": "agent luar ditemukan dari event Picked di SelectionAnchor; dinilai + "
                                            "tampil di papan, belum menentukan bot aktif (F-D107)", "join": f"{gate.public_url}/analysts/input"})
                if parts[0] == "aktif" and len(parts) == 1:
                    return self._send(200, gate.aktif_now())
                if parts[0] == "desk" and len(parts) == 1:
                    return self._send(200, gate.meja_view())
                if parts[0] == "desk" and len(parts) == 2 and parts[1] == "data":
                    return self._send(200, gate.data_view())
                if parts[0] == "desk" and len(parts) == 3 and parts[1] == "proof":
                    code, body = gate.meja_proof(parts[2])
                    return self._send(code, body)
                if parts[0] == "analis" and len(parts) in (1, 2):
                    recs = gate.analis_records(int(parts[1]) if len(parts) == 2 else None)
                    last = max((r["alasan"]["bar_close"] for r in recs), default=None)
                    show = recs if len(parts) == 2 else [r for r in recs if r["alasan"]["bar_close"] == last]
                    return self._send(200, {"bar_close": last if len(parts) == 1 else int(parts[1]),
                                            "selection_anchor": gate.data.cfg_raw().get("contracts", {}).get("SelectionAnchor"),
                                            "catatan": "reasonHash on-chain = sha256 JSON 'alasan' kanonis (sort_keys, tanpa spasi); pilihan dikomit SEBELUM bar_close; "
                                                       "alasan bar yang belum tutup tersegel (app: login + beli), terbit penuh sesudah tutup",
                                            "pilihan": [tutup_alasan(r, int(gate.now())) for r in show]})
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


# ---------------------------------------------------------------- beli langsung dari chat lewat dompet Privy user (P138e, F-D101)

def typed_pair(token: str, amount: int, pay_to: str, owner: str, tok_nonce: int, now_s: int, nonce: int, chain_id: int = 97) -> Tuple[dict, dict, dict]:
    """(Permit2 witness, EIP-2612 permit, nilai) - SELALU dibangun gerbang: token FAB, tepat tagihan, ke payTo gerbang; tidak ada input bebas dari user."""
    va, dl = str(now_s - 15), str(now_s + 110)
    p2 = {"domain": {"name": "Permit2", "chainId": chain_id, "verifyingContract": PERMIT2},
          "types": {"EIP712Domain": [{"name": "name", "type": "string"}, {"name": "chainId", "type": "uint256"}, {"name": "verifyingContract", "type": "address"}],
                    "PermitWitnessTransferFrom": [{"name": "permitted", "type": "TokenPermissions"}, {"name": "spender", "type": "address"},
                                                  {"name": "nonce", "type": "uint256"}, {"name": "deadline", "type": "uint256"}, {"name": "witness", "type": "Witness"}],
                    "TokenPermissions": [{"name": "token", "type": "address"}, {"name": "amount", "type": "uint256"}],
                    "Witness": [{"name": "to", "type": "address"}, {"name": "validAfter", "type": "uint256"}]},
          "primaryType": "PermitWitnessTransferFrom",
          "message": {"permitted": {"token": token, "amount": str(amount)}, "spender": PROXY, "nonce": str(nonce), "deadline": dl,
                      "witness": {"to": pay_to, "validAfter": va}}}
    e2612 = {"domain": {"name": TOKEN_NAME, "version": TOKEN_VERSION, "chainId": chain_id, "verifyingContract": token},
             "types": {"EIP712Domain": [{"name": "name", "type": "string"}, {"name": "version", "type": "string"}, {"name": "chainId", "type": "uint256"},
                                        {"name": "verifyingContract", "type": "address"}],
                       "Permit": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}, {"name": "value", "type": "uint256"},
                                  {"name": "nonce", "type": "uint256"}, {"name": "deadline", "type": "uint256"}]},
             "primaryType": "Permit",
             "message": {"owner": owner, "spender": PERMIT2, "value": str(amount), "nonce": str(tok_nonce), "deadline": dl}}
    return p2, e2612, {"valid_after": va, "deadline": dl, "nonce": str(nonce)}


def _v27(sig: str) -> str:
    h = sig[2:] if sig.startswith("0x") else sig
    v = int(h[128:130], 16)
    return "0x" + h[:128] + ("%02x" % (v + 27 if v < 27 else v))


def tg_buy_privy(gate: "Gate", user_id: int, chat_id: int, bot: str) -> Tuple[Optional[str], Optional[Tuple[str, str]]]:
    """-> (teks, tombol). Berhasil = paket dikirim sebagai gambar lewat `deliver_tg` dan teks None."""
    import secrets as _sec
    led, cfg = gate.data.ledgers(), gate.data.cfg()
    q = quote(led, bot)
    app = f"{gate.web_url}/buy"
    try:
        user = gate.privy.user_by_telegram(user_id)
    except pv.PrivyError as e:
        gate.log(f"privy cari user gagal: {e}")
        return "Wallet lookup failed, try again in a minute.", None
    w = pv.Privy.embedded_wallet(user) if user else None
    if not w:
        return ("Your Telegram is not linked to a Fabius wallet yet. Open the app, sign in (Telegram or Google), tap \"Link my Telegram\" and "
                "\"Allow Fabius bot to pay for me\", then /buy again."), ("Open Fabius", app + "?izin=1")
    wid, addr = w
    bal = int(gate.ev.call_decode(cfg["token"], "balanceOf(address)", ("address",), (addr,), ("uint256",))[0])
    if bal < q["atomic"]:
        return f"Not enough FAB in {addr[:8]}…: {bal / 1e6:g} < {q['fab']:g}. Send /topup for free test FAB.", None
    tok_nonce = int(gate.ev.call_decode(cfg["token"], "nonces(address)", ("address",), (addr,), ("uint256",))[0])
    now_s = int(gate.now())
    p2, e2612, v = typed_pair(cfg["token"], q["atomic"], cfg["facilitator"], addr, tok_nonce, now_s, int.from_bytes(_sec.token_bytes(16), "big"))
    try:
        s1, s2 = _v27(gate.privy.sign_typed_data(wid, p2)), _v27(gate.privy.sign_typed_data(wid, e2612))
    except pv.PrivyError as e:
        gate.log(f"privy tanda tangan ditolak: {e}")
        if e.status in (401, 403):
            return ("Fabius bot is not allowed to pay from your wallet yet. Open the app and tap \"Allow Fabius bot to pay for me\" "
                    "(one time, revocable), then /buy again."), ("Allow bot payments", app + "?izin=1")
        return "Signing failed, try again in a minute.", None
    pay = {"x402Version": 2, "resource": {"url": f"{gate.public_url}/signal/{bot}/{q['bar']}", "mimeType": "application/json"},
           "accepted": {"scheme": "exact", "network": NETWORK, "amount": str(q["atomic"]), "asset": cfg["token"], "payTo": cfg["facilitator"]},
           "payload": {"signature": s1, "permit2Authorization": {"permitted": {"token": cfg["token"], "amount": str(q["atomic"])}, "from": addr,
                                                                 "spender": PROXY, "nonce": v["nonce"], "deadline": v["deadline"],
                                                                 "witness": {"to": cfg["facilitator"], "validAfter": v["valid_after"]}}},
           "extensions": {"eip2612GasSponsoring": {"info": {"from": addr, "asset": cfg["token"], "spender": PERMIT2, "amount": str(q["atomic"]),
                                                            "nonce": str(tok_nonce), "deadline": v["deadline"], "signature": s2, "version": TOKEN_VERSION}}}}
    code, body, _ = gate.handle_signal(bot, q["bar"], base64.b64encode(json.dumps(pay).encode()).decode(), None)
    if code != 200:
        return f"Payment failed ({code}): {body.get('error')}", None
    gate.deliver_tg(chat_id, body)
    return None, None


# ---------------------------------------------------------------- bot Telegram (P138d, F-D101): perintah Inggris, dompet = Privy (Mini App)
# Dompet TIDAK dibuat di sini (keputusan F-D101: opsi custodial dibatalkan). Membeli dan melihat dompet terjadi di halaman web `/beli/<bot>` yang dibuka
# sebagai Telegram Mini App: Privy login otomatis lewat Telegram, akun Google yang ditautkan memakai dompet yang SAMA. Tautan `?tg=` bertanda membuat
# paket juga dikirim ke chat sesudah settle. Beli otomatis dari chat (session signer Privy) = tahap berikutnya.

HELP = ("Fabius - verified trading signals, paid per signal with x402 on BNB testnet (chain 97). FAB is a test token with no value.\n\n"
        "/buy - the signal of the bot Fabius is trading now (or /buy <BOT>): pay with x402 in the Fabius app inside Telegram, no gas\n"
        "/signal - free teaser of the active bot (or /signal <BOT>; no assets, no direction)\n/bots - all bots, prices, track-record confidence\n"
        "/topup - free FAB test tokens to your wallet\n"
        "/desk - the AI desk: every 5 minutes each AI agent decides, anchored on-chain\n"
        "/analysts - which bot each AI analyst agent picked today (committed on-chain before the bar closes); full reasoning in the app\n"
        "/wallet - your wallet (same wallet as on the Fabius website when you link Google)\n\n"
        "Every signal is committed on-chain before the market moves; anyone can verify it.")
COMMANDS = [("buy", "buy the signal of the bot Fabius trades now (x402)"), ("desk", "AI desk: 5-minute decisions and paper results"), ("topup", "free FAB test tokens to your wallet"), ("signal", "free teaser of the active bot"), ("analysts", "today's AI analyst picks"),
            ("bots", "all bots, prices, track-record confidence"),
            ("wallet", "your wallet"), ("help", "how it works")]


STATUS_EN = {"INTI": "core (identity bot)", "SEMENTARA": "provisional"}
GATE_EN = {"TOLAK": "rejected", "LOLOS_SHADOW": "passed", "TIDAK_TERUKUR": "not measurable"}
FD16_EN = {"LOLOS": "passed", "BELUM CUKUP DATA": "not enough data yet", "TIDAK LOLOS": "failed"}
RUTE_EN = {"signal": "sinyal", "analysts": "analis", "active": "aktif", "full": "lengkap", "scores": "skor"}


def _teaser_en(q: dict) -> str:
    t = q["teaser"]
    conf = "not measured yet" if t["confidence_pct"] is None else f"{t['confidence_pct']}% ({'early, not meaningful yet' if t['fd16'] == 'BELUM CUKUP DATA' else 'measured'})"
    k = t["kematangan"]
    st, gv = t.get("status"), t.get("gerbang_v1")
    return (f"{q['bot']} · bar {q['bar']}\nTrack-record confidence (forward results): {conf}\nRole: {STATUS_EN.get(st, st) or '-'} · locked backtest gate: "
            f"{GATE_EN.get(gv, gv) or '-'} · forward test F-D16: {FD16_EN.get(t['fd16'], t['fd16'])}\nProgress: signals {k['sinyal'][0]}/{k['sinyal'][1]}, settled days {k['hari'][0]}/{k['hari'][1]}, "
            f"months {k['bulan'][0]}/{k['bulan'][1]}\nPrice: {q['fab']:g} FAB ({'base price' if q['atomic'] == harga.HargaParams().dasar else 'confidence tier'}, locked table)")


def tg_reply(gate: "Gate", chat_id: int, text: str, private: bool = True, user_id: Optional[int] = None) -> Tuple[Optional[str], Optional[Tuple[str, str]]]:
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
                c, k = q["teaser"]["confidence_pct"], q["teaser"]["kematangan"]
                rows.append(f"{b}: {q['fab']:g} FAB · track-record confidence {'not measured yet' if c is None else f'{c}%'} "
                            f"(settled days {k['hari'][0]}/{k['hari'][1]})")
            except KeyError:
                continue
        return ("Bots with a forward clock (latest bar):\n" + "\n".join(rows)
                + "\n\nTrack-record confidence = how sure the bot's own forward results are that it makes money on average "
                  "(a number from 2 settled days, meaningful from 20). The % in /analysts is different: each AI agent's self-rated "
                  "conviction for one bar.\n\n/signal <BOT> for the teaser, /buy <BOT> to buy."), None
    explicit = bool(bot)                                              # /buy <BOT> = pilihan sadar; /buy saja = sinyal hari ini (P146)
    if cmd in ("/signal", "/buy") and not bot:
        bot = gate.aktif_now().get("bot") or ""
    if cmd in ("/signal", "/buy"):
        if bot not in led:
            return f"Usage: {cmd} <BOT>. Bots: {', '.join(sorted(led))}", None
        if cmd == "/buy" and private and getattr(gate, "privy", None) is not None:
            return tg_buy_privy(gate, user_id or chat_id, chat_id, bot)
        q = quote(led, bot)
        page = f"{gate.web_url}/buy/{bot}" if explicit else f"{gate.web_url}/buy"
        link = f"{page}?tg={tg_link(gate.tg_secret, chat_id, bot, q['bar'], int(gate.now()))}"
        head = _teaser_en(q) if cmd == "/signal" else f"{bot} · bar {q['bar']} · {q['fab']:g} FAB"
        if not private:
            return head + f"\n\nBuy in a private chat with me, or on the web: {page}", None
        return head + "\n\nTap the button: sign in with Telegram (or Google), get free FAB, pay with x402 (no gas). The signal is also sent here.", \
            (f"Buy {bot} · {q['fab']:g} FAB", link)
    if cmd == "/analysts":
        recs = gate.analis_records()
        if not recs:
            return "No analyst picks yet.", None
        last = max(r["alasan"]["bar_close"] for r in recs)
        day = dt.datetime.fromtimestamp(last, dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        rows = [f"{r['alasan'].get('nama') or 'agent'}{' [external]' if r.get('luar') else ''} (agent {r['alasan']['agent_id']}): {r['bot']} · "
                f"self-rated confidence {r['keyakinan']}%"
                f"{' · committed on-chain' if r.get('status') == 'dikomit' else ''}"
                for r in recs if r["alasan"]["bar_close"] == last]
        ak = gate.aktif_now()
        board = gate.analis_view()["papan"]
        lb = [f"{i + 1}. agent {b['agent_id']} ({b.get('nama') or b['agent']}{', external' if b.get('luar') else ''}): {b['terskor']}/{b['pilihan']} "
              f"scored · excess vs B1 {b['jumlah_selisih_bps']:+.1f} bps"
              for i, b in enumerate(board)]
        return (f"Bot Fabius trades now (locked rule): {ak.get('bot')} — {ak.get('alasan_en') or ak.get('alasan')}\n\n"
                f"Analyst agents' picks for the bar closing {day} (committed before the close, scored later from the public ledger):\n\n"
                + "\n".join(rows) + ("\n\nLeaderboard:\n" + "\n".join(lb) if lb else "")
                + f"\n\nFull reasoning, hashes and scores: in the Fabius app (sign in + any signal bought in the last {AKSES_HARI} days)."
                + ("" if private else f" {gate.web_url}/analysts")), (("Analysts' reasoning", f"{gate.web_url}/analysts") if private else None)
    if cmd == "/desk":
        v = gate.meja_view()
        if not v["buku"]:
            return "The AI desk has no cycles yet.", None
        rows = []
        for b in v["buku"]:
            k = b.get("keputusan_terakhir") or {}
            pos = ", ".join(f"{a} {w:+.2f}" for a, w in list(b["posisi"].items())[:6]) or "flat"
            rows.append(f"{'CONSENSUS' if b['agent'] == meja.KONSENSUS else b['agent']}: equity {b['ekuitas']:.2f} ({b['hasil_pct']:+.2f}%), "
                        f"{b['n_trade']} trades, fees {b['biaya']:.2f} | {pos}" + (f"\n  {str(k.get('ringkasan') or '')[:200]}" if b['agent'] != meja.KONSENSUS else ""))
        s_ = v.get("siklus_terakhir") or {}
        return ("AI desk (paper, decides every 5 minutes, each cycle anchored on-chain):\n\n" + "\n\n".join(rows)
                + f"\n\nLast cycle {time.strftime('%H:%M', time.gmtime(s_.get('siklus') or 0))}Z: {s_.get('status')}"), \
            (("AI desk", f"{gate.web_url}/desk") if private else None)
    if cmd == "/topup":
        if not private or getattr(gate, "privy", None) is None:
            return "Get free FAB in the Fabius app (button below).", (("Open Fabius", f"{gate.web_url}/buy") if private else None)
        user = gate.privy.user_by_telegram(user_id or chat_id)
        w = pv.Privy.embedded_wallet(user) if user else None
        if not w:
            return "Open the Fabius app once (sign in with Telegram) to create your wallet.", ("Open Fabius", f"{gate.web_url}/buy")
        code, body = gate.faucet(w[1], gate.data.cfg())
        if code == 200 and body.get("dikirim_atomic"):
            return f"Sent {body['dikirim_atomic'] / 1e6:g} FAB to your wallet {w[1][:8]}…\ntx {body['tx']}", None
        if code == 200:
            return f"You already have {body.get('saldo_atomic', 0) / 1e6:g} FAB (top-up only below 0.1 FAB).", None
        return f"Top-up refused: {body.get('error')}", None
    if cmd == "/wallet":
        b = sorted(led)[0] if led else "B1-TREND"
        return ("Your wallet lives in the Fabius app (Privy): open it below and sign in with Telegram. Link your Google account there and the "
                "website uses the SAME wallet. Testnet only; you need no tBNB."), (("Open my wallet", f"{gate.web_url}/buy") if private else None)
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
                msg, button = tg_reply(gate, int(chat["id"]), text, chat.get("type") == "private", (m.get("from") or {}).get("id"))
                if msg:
                    gate.tg_send(int(chat["id"]), msg, button)
            except Exception as e:  # noqa: BLE001
                gate.log(f"telegram balasan gagal: {type(e).__name__}: {str(e)[:120]}")


def analis_loop(gate: "Gate", ev, stop: threading.Event, every_s: int = 600) -> None:
    """Sekali per bar: antara 09:00 dan 22:00 UTC (tick bar sebelumnya sudah ada; jauh sebelum penutupan), tiap agent aktif yang belum memilih
    untuk penutupan berikutnya dipanggil + dikomit. `run_round` membaca SelectionAnchor dulu -> tidak pernah memilih dua kali."""
    while not stop.wait(every_s):
        try:
            if not 9 <= time.gmtime().tm_hour < 22:
                continue
            gate.data.refresh()
            cfg = an.load_cfg(os.path.join(gate.data.workdir, "deployments", "97.json"))
            if not cfg.get("selection") or not an.active_agents(cfg):
                continue
            an.run_round(gate.data.workdir, cfg, ev, int(time.time()), True, log=gate.log, out_dir=gate.analis_dir)
            v = gate.analis_view(max_age_s=0)
            rep = (gate.data.cfg_raw().get("erc8004") or {}).get("reputation")
            if rep and gate.pk:
                with gate.tx_lock:                                         # kunci gerbang juga dipakai komit meja tiap 5 menit: satu pengirim sekaligus
                    an.reputasi(ev, gate.pk, rep, [x for x in v["skor"] if not x.get("luar")], os.path.join(gate.analis_dir, "reputasi.json"),
                                gate.public_url, log=gate.log)                      # F-D107: feedback hanya agent rumah (gas gerbang tidak bisa dikuras Sybil)
        except Exception as e:  # noqa: BLE001 - analis gagal tidak boleh mengganggu penjualan sinyal
            gate.log(f"analis gagal: {type(e).__name__}: {str(e)[:200]}")


def meja_loop(gate: "Gate", ev, stop: threading.Event) -> None:
    """P152 (F-D109): tiap batas 5 menit UTC (+8 s supaya candle tutup) satu siklus meja; Merkle root dikomit ke DeskAnchor SELAMA siklus berjalan.
    Komit gagal / terlambat dicatat di rekaman siklus (status), tidak pernah diulang sesudah siklus berakhir (kontrak menolak TooLate)."""
    from evm import calldata, receipt_ok
    books, ring = gate.meja_muat()

    def call(ag, system, user):
        return an.call_model({**ag, "effort": meja.PARAMS["effort"]}, system, user, timeout=meja.PARAMS["batas_jawab_s"] - 10)
    while True:
        now = time.time()
        t0 = int(now // meja.PARAMS["siklus_s"] * meja.PARAMS["siklus_s"]) + meja.PARAMS["siklus_s"]
        if stop.wait(max(0.0, t0 + 8 - now)):
            return
        try:
            gate.data.refresh()
            acfg = an.load_cfg(os.path.join(gate.data.workdir, "deployments", "97.json"))
            desk = gate.data.cfg_raw().get("contracts", {}).get("DeskAnchor")
            agents = an.active_agents(acfg) if acfg.get("selection") else []
            if not (desk and agents and gate.pk):
                continue
            judul = gate.kabar_cache() if any(a.get("berita") for a in agents) else None
            rek, sik = meja.siklus(t0, agents, books, ring, call, judul=judul, log=gate.log)
            sik.update(root=meja.root_of(sik["daun"]), n=len(sik["daun"]), status="tidak dikomit", tx=None)
            if time.time() < t0 + meja.PARAMS["siklus_s"] - 12:
                data = calldata("commit(uint64,bytes32,uint16)", ("uint64", "bytes32", "uint16"), (t0, bytes.fromhex(sik["root"][2:]), sik["n"]))
                with gate.tx_lock:
                    r = ev.send(gate.pk, desk, data, gas=120_000)
                sik.update(tx=r.get("transactionHash"), status="dikomit" if receipt_ok(r) else "komit gagal")
            else:
                sik["status"] = "terlambat (siklus hampir habis, tidak dikomit)"
            gate.meja_simpan(rek, sik, books, ring)
            gate.log(f"meja {time.strftime('%H:%M', time.gmtime(t0))}Z root {sik['root'][:18]}… {sik['status']} {sik.get('tx') or ''}")
        except Exception as e:  # noqa: BLE001 - meja gagal tidak boleh mengganggu penjualan sinyal
            gate.log(f"meja gagal: {type(e).__name__}: {str(e)[:200]}")


def data_loop(gate: "Gate", stop: threading.Event) -> None:
    """P153 (F1, F-D110): tiap batas 5 menit UTC (+20 s) snapshot data luas meja v2 (tools/meja_data.py): fitur per aset + per bot dari Binance,
    DexScreener, RugCheck, FOMO, berita. Belum dibaca agent (F2); dicatat untuk mengukur cakupan + kuota + durasi 24 jam."""
    import meja_data as md
    peng = md.Pengumpul(fomo_key=os.environ.get("FOMO_API_KEY"), kabar_fn=lambda now: {"judul": gate.kabar_cache() or []})
    while True:
        now = time.time()
        t0 = int(now // meja.PARAMS["siklus_s"] * meja.PARAMS["siklus_s"]) + meja.PARAMS["siklus_s"]
        if stop.wait(max(0.0, t0 + 20 - now)):
            return
        try:
            gate.data.refresh()
            targets = {}
            for b, recs in gate.data.ledgers().items():
                ticks = [r for r in recs if r.get("type") == "tick"]
                targets[b] = (max(ticks, key=lambda r: r["asof"]).get("targets") or {}) if ticks else {}
            mulai = time.time()
            snap = peng.kumpul(t0, meja.pasar(t0), targets)
            snap["durasi_s"] = round(time.time() - mulai, 1)
            gate.data_simpan(snap)
            k = snap["kesehatan"]
            gate.log(f"data {time.strftime('%H:%M', time.gmtime(t0))}Z {snap['durasi_s']}s " + " ".join(f"{n}={v['cakupan']}" for n, v in k.items()))
        except Exception as e:  # noqa: BLE001 - data gagal tidak boleh mengganggu meja v1 / penjualan
            gate.log(f"data gagal: {type(e).__name__}: {str(e)[:200]}")


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
    pa, ps, pk_auth = os.environ.get("PRIVY_APP_ID"), os.environ.get("PRIVY_APP_SECRET"), os.environ.get("PRIVY_AUTH_PRIVATE_KEY")
    gate.privy = pv.Privy(pa, ps, pk_auth) if (pa and ps and pk_auth) else None
    gate.log(f"privy beli-langsung: {'NYALA' if gate.privy else 'mati (PRIVY_APP_ID/SECRET/AUTH_PRIVATE_KEY belum lengkap)'}")
    stop = threading.Event()
    acfg = an.load_cfg(os.path.join(data.workdir, "deployments", "97.json"))
    aktif = an.active_agents(acfg) if acfg.get("selection") else []
    gate.log(f"analis: {', '.join(a['slug'] + '#' + str(a['agent_id']) for a in aktif) or 'tidak ada agent aktif (kunci/pendaftaran belum ada)'} | arsip {gate.analis_dir}")
    if aktif:
        threading.Thread(target=analis_loop, args=(gate, ev, stop), daemon=True).start()
    if gate.tg_token:
        threading.Thread(target=telegram_loop, args=(gate, stop), daemon=True).start()
    desk = data.cfg_raw().get("contracts", {}).get("DeskAnchor")
    gate.log(f"meja AI 5 menit: {'NYALA, DeskAnchor ' + desk if (desk and aktif and pk) else 'mati (DeskAnchor/agent/kunci belum ada)'} | params {meja.params_sha()[:18]}")
    if desk and aktif and pk:
        threading.Thread(target=meja_loop, args=(gate, ev, stop), daemon=True).start()
    import meja_data as md
    gate.log(f"data meja v2 (F1): NYALA | registry {md.registry_sha()[:18]} ({len(md.REGISTRY)} token) | FOMO {'ada kunci' if os.environ.get('FOMO_API_KEY') else 'tanpa kunci'}")
    threading.Thread(target=data_loop, args=(gate, stop), daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", a.port), make_handler(gate)).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

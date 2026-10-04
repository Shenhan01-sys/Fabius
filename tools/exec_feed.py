"""Umpan laporan eksekusi (P119, F-D94): eksekutor di Railway -> Gist publik -> rantai GitHub (penulis tunggal `ledger/eksekusi/`).

Kenapa jalan memutar: runner GitHub mendapat HTTP 451 dari `demo-fapi.binance.com` dan `fapi.binance.com` (terukur 4 Okt, run egress-probe
37190705904), jadi rantai GitHub tidak bisa membaca riwayat order Binance sendiri. Eksekutor (IP Singapura) membacanya, lalu MENAMBAHKAN satu baris JSON
ke Gist publik milik builder. Tokennya hanya-Gist (fine-grained, izin akun "Gists: Read and write"): tidak bisa menyentuh repo, jadi rantai GitHub tetap
satu-satunya penulis ledger. Riwayat revisi Gist (bercap waktu GitHub) menjadi jejak kedua.

Laporan disusun ULANG dari venue, bukan dari memori proses: order dicari lewat `clientOrderId` deterministik `ex.client_id(venue, bot, bar, aset, sisi)`
untuk setiap aset universe x dua sisi. Restart worker tidak mengubah isi laporan; rantai GitHub menghitung ulang id yang sama untuk memeriksanya.

Dua jenis baris (v1):
  eksekusi  satu per (venue, bot, bar): order yang benar-benar ada di venue (harga rata-rata, qty terisi, waktu kirim/isi, fee nyata), posisi + ekuitas
            sesudahnya, `dilewati` dari rencana, `komit_s` yang dilihat eksekutor.
  tanda     satu per (venue, tanggal): ekuitas + posisi akun pada putaran pertama sesudah 00:00Z (<= 30 menit) - bahan tracking error harian.
Gagal (token tidak ada, Gist/venue tak terjangkau) = baris tertunda dan dicoba lagi putaran berikut; eksekutor tidak terganggu (T8 SK-E14).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Callable, Dict, Iterable, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from engine import eksekusi as ex                                              # noqa: E402

FEED_DESC = "fabius-exec feed v1"
API = "https://api.github.com"
SIDES = ("BUY", "SELL")
MARK_WINDOW_S = 1800              # tanda ekuitas hanya dalam 30 menit pertama sesudah 00:00Z (penutupan bar); restart siang hari tidak menulis tanda palsu
README = ("# Fabius - umpan laporan eksekusi\n\nDitulis oleh eksekutor Fabius (Railway). Satu baris JSON per eksekusi (venue, bot, bar) dan per tanda ekuitas harian.\n"
          "Rantai GitHub di repo Shenhan01-sys/Fabius memeriksa setiap baris lalu menulisnya ke `ledger/eksekusi/` (berantai hash). Mode demo: saldo virtual.\n")


class FeedError(Exception):
    """Gist tak terjangkau / ditolak / terlalu besar: baris tetap tertunda (SK-E14)."""


def feed_file(day: str) -> str:
    """Satu berkas per bulan: isi API Gist terpotong di atas 1 MB, satu bulan B1 ±100 KB."""
    return f"fabius-exec-{day[:7]}.jsonl"


def key_of(rec: dict) -> str:
    if rec.get("type") == "tanda":
        return f"tanda|{rec.get('venue')}|{rec.get('tanggal')}"
    return f"{rec.get('type')}|{rec.get('venue')}|{rec.get('bot')}|{rec.get('bar')}"


def day_of(rec: dict) -> str:
    return rec.get("bar") or rec.get("tanggal") or ""


def line_of(rec: dict) -> str:
    return json.dumps(rec, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# ---------------------------------------------------------------- isi laporan (dari venue, tanpa memori proses)

def build_report(v, venue: str, mode: str, bot: str, bar: str, universe: Iterable[str], komit_s: int, modal: float,
                 dilewati: Sequence[Tuple[str, str]], now_ms: int, px_rencana: Optional[Dict[str, float]] = None, susulan: bool = False) -> dict:
    """`px_rencana` = harga tengah buku saat rencana (dari eksekutor; tidak ada sesudah restart) -> slippage sejati di rantai GitHub.
    `susulan` = bar lama yang dieksekusi SEBELUM umpan menyala: posisi + ekuitas sekarang BUKAN milik bar itu, jadi dikosongkan (None)."""
    uni = sorted(universe)
    orders = []
    for a in uni:
        for side in SIDES:
            cid = ex.client_id(venue, bot, bar, a, side)
            o = v.order_by_client_id(a, cid)
            if o is None:
                continue
            filled = float(o.get("executedQty") or 0)
            fills = v.user_trades(a, int(o["orderId"])) if filled > 0 else []
            orders.append({"id": cid, "aset": a, "sisi": side, "order_id": int(o["orderId"]), "status": o.get("status"),
                           "qty": filled, "px": float(o.get("avgPrice") or 0), "t_kirim": int(o.get("time") or 0), "t_isi": int(o.get("updateTime") or 0),
                           "fee": round(sum(float(t.get("commission") or 0) for t in fills), 10),
                           "fee_aset": ",".join(sorted({str(t["commissionAsset"]) for t in fills if t.get("commissionAsset")})) or None,
                           "isi": len(fills), "reduce": bool(o.get("reduceOnly")), "px_rencana": (px_rencana or {}).get(a)})
    keep = set(uni)
    rec = {"v": 1, "type": "eksekusi", "venue": venue, "mode": mode, "bot": bot, "bar": bar, "modal": float(modal), "komit_s": int(komit_s),
           "orders": orders, "dilewati": [list(x) for x in dilewati], "posisi": None, "ekuitas": None, "dibuat_ms": int(now_ms)}
    if susulan:
        rec["susulan"] = True
    else:
        rec.update(posisi={a: q for a, q in sorted(v.positions().items()) if a in keep}, ekuitas=round(float(v.equity()), 8))
    return rec


def build_mark(v, venue: str, mode: str, tanggal: str, now_ms: int) -> dict:
    return {"v": 1, "type": "tanda", "venue": venue, "mode": mode, "tanggal": tanggal, "t_ms": int(now_ms),
            "ekuitas": round(float(v.equity()), 8), "posisi": dict(sorted(v.positions().items()))}


# ---------------------------------------------------------------- Gist

def _http(method: str, url: str, headers: Dict[str, str], body: Optional[bytes] = None, timeout: float = 20.0) -> Tuple[int, dict]:
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:  # noqa: BLE001
            return e.code, {}


class GistFeed:
    def __init__(self, token: str, http: Callable[..., Tuple[int, object]] = _http, gist_id: Optional[str] = None, log: Callable[[str], None] = print):
        if not token:
            raise FeedError("EXEC_FEED_TOKEN tidak ada")
        self.token, self.http, self.gist_id, self.log = token, http, gist_id, log

    def _req(self, method: str, path: str, body: Optional[dict] = None) -> Tuple[int, object]:
        h = {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
             "User-Agent": "fabius-exec-feed/1.0"}
        if body is not None:
            h["Content-Type"] = "application/json"
        try:
            return self.http(method, API + path, h, json.dumps(body).encode() if body is not None else None)
        except Exception as e:  # noqa: BLE001
            raise FeedError(f"{method} {path}: tak terjangkau ({type(e).__name__})") from None

    def locate(self) -> str:
        """Gist umpan milik pemegang token (deskripsi tetap); belum ada = dibuat SEKALI, publik."""
        if self.gist_id:
            return self.gist_id
        code, body = self._req("GET", "/gists?per_page=100")
        if code != 200 or not isinstance(body, list):
            raise FeedError(f"daftar gist: HTTP {code}")
        for g in body:
            if g.get("description") == FEED_DESC:
                self.gist_id = str(g["id"])
                return self.gist_id
        code, body = self._req("POST", "/gists", {"description": FEED_DESC, "public": True, "files": {"README.md": {"content": README}}})
        if code != 201 or not isinstance(body, dict) or "id" not in body:
            raise FeedError(f"buat gist: HTTP {code}")
        self.gist_id = str(body["id"])
        self.log(f"umpan eksekusi: gist BARU {self.gist_id} ({body.get('html_url', '')})")
        return self.gist_id

    def append(self, rec: dict) -> bool:
        """True = baris ditambahkan; False = kunci (jenis, venue, bot, bar/tanggal) sudah ada (idempoten, restart aman)."""
        gid = self.locate()
        name = feed_file(day_of(rec))
        code, g = self._req("GET", f"/gists/{gid}")
        if code != 200 or not isinstance(g, dict):
            raise FeedError(f"baca gist {gid}: HTTP {code}")
        f = (g.get("files") or {}).get(name) or {}
        if f.get("truncated"):
            raise FeedError(f"{name} terpotong (> 1 MB): butuh berkas baru")
        content = f.get("content") or ""
        if key_of(rec) in {key_of(json.loads(x)) for x in content.splitlines() if x.strip()}:
            return False
        code, _ = self._req("PATCH", f"/gists/{gid}", {"files": {name: {"content": content + line_of(rec) + "\n"}}})
        if code != 200:
            raise FeedError(f"tulis gist {gid}: HTTP {code}")
        return True

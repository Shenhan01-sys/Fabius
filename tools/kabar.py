"""Kabar untuk agent analis berita (P139, F-D108): judul berita kripto + pengumuman Binance dari sumber PUBLIK tanpa kunci, dibaca sekali per putaran.

Daftar judul DISALIN ke JSON alasan agent yang di-hash (reasonHash on-chain di SelectionAnchor): siapa pun bisa memeriksa berita apa yang dibaca agent
sebelum bar tutup - berita "dikomit sebelum dipakai" (rancangan P139). Akses diukur 5 Okt: Cointelegraph / Decrypt / The Block RSS 200, Binance CMS
(listing 48, delisting 161, berita 49) 200; CoinDesk RSS 308 (dilewati). Sumber gagal dicatat per sumber, tidak pernah diam-diam dianggap kosong.
Pengurai XML: ukuran dibatasi + DOCTYPE dibuang sebelum parse (tanpa entitas = tanpa ledakan entitas).
"""
from __future__ import annotations

import email.utils
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import Callable, Dict, List

SUMBER_RSS = {"cointelegraph": "https://cointelegraph.com/rss", "decrypt": "https://decrypt.co/feed", "theblock": "https://www.theblock.co/rss.xml"}
BINANCE = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query?type=1&pageNo=1&pageSize=15"
BINANCE_KATALOG = {48: "binance-listing", 161: "binance-delisting", 49: "binance-news"}
JENDELA_S = 36 * 3600              # berita 36 jam terakhir sebelum putaran
JENDELA_BINANCE_S = 7 * 86_400     # listing / delisting jarang tetapi relevan beberapa hari (B4 = listing baru)
MAKS_PER_SUMBER = 12
MAKS_TOTAL = 40
BATAS_BYTE = 2 * 1024 * 1024
UA = "fabius-analis/1.0 (+https://fabius-one.vercel.app)"


def ambil(url: str, timeout: int = 15) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
        raw = r.read(BATAS_BYTE + 1)
    if len(raw) > BATAS_BYTE:
        raise ValueError(f"lebih dari {BATAS_BYTE} byte")
    return raw


def _bersih(t: str, n: int = 200) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t or "")).strip()[:n]


def parse_rss(raw: bytes, sumber: str) -> List[dict]:
    """RSS 2.0 -> [{sumber, judul, waktu (unix detik), url}]. Item tanpa judul / tanggal dilewati."""
    txt = re.sub(r"<!DOCTYPE\s[^\[>]*(\[.*?\]\s*)?>", "", raw.decode("utf-8", "replace"), flags=re.S | re.I)    # termasuk blok entitas [ ... ]
    out = []
    for it in ET.fromstring(txt).iter("item"):
        t_el = it.find("title")
        judul, tgl = _bersih("".join(t_el.itertext()) if t_el is not None else ""), it.findtext("pubDate") or ""
        if not judul or not tgl:
            continue
        try:
            waktu = int(email.utils.parsedate_to_datetime(tgl.strip()).timestamp())
        except (TypeError, ValueError):
            continue
        out.append({"sumber": sumber, "judul": judul, "waktu": waktu, "url": (it.findtext("link") or "").strip()[:300]})
    return out


def parse_binance(raw: bytes) -> List[dict]:
    """Binance CMS -> pengumuman listing / delisting / berita."""
    out = []
    for c in ((json.loads(raw).get("data") or {}).get("catalogs") or []):
        nama = BINANCE_KATALOG.get(c.get("catalogId"))
        if not nama:
            continue
        for a in c.get("articles") or []:
            if a.get("title") and a.get("releaseDate"):
                out.append({"sumber": nama, "judul": _bersih(a["title"]), "waktu": int(a["releaseDate"]) // 1000,
                            "url": f"https://www.binance.com/en/support/announcement/{a.get('code', '')}"})
    return out


def kabar(now_s: int, fetch: Callable[[str], bytes] = ambil) -> dict:
    """-> {"judul": [...] (terbaru dulu; jendela 36 jam, Binance 7 hari; maks 12 per sumber / 40 total), "status": {sumber: "ok N" | "galat ..."}}."""
    semua: List[dict] = []
    status: Dict[str, str] = {}
    tugas = [(n, u, parse_rss) for n, u in SUMBER_RSS.items()] + [("binance", BINANCE, None)]
    for nama, url, rss in tugas:
        try:
            items = rss(fetch(url), nama) if rss else parse_binance(fetch(url))
        except Exception as e:  # noqa: BLE001 - satu sumber gagal tidak menghentikan yang lain; dicatat
            status[nama] = f"galat {type(e).__name__}: {str(e)[:100]}"
            continue
        jendela = JENDELA_BINANCE_S if nama == "binance" else JENDELA_S
        baru = [x for x in items if now_s - jendela <= x["waktu"] <= now_s]
        per: Dict[str, int] = {}
        for x in sorted(baru, key=lambda x: -x["waktu"]):
            if per.get(x["sumber"], 0) < MAKS_PER_SUMBER:
                per[x["sumber"]] = per.get(x["sumber"], 0) + 1
                semua.append(x)
        status[nama] = f"ok {sum(per.values())}"
    semua.sort(key=lambda x: (-x["waktu"], x["sumber"], x["judul"]))
    return {"judul": semua[:MAKS_TOTAL], "status": status}

"""P82: KEBERADAAN URL rujukan pengajuan (`theory.referensi[*].url`) diperiksa kode, bukan dipercaya.

Dijalankan oleh tinjauan harian (`tools/tinjau_pengajuan.py`, GitHub Actions), BUKAN di dalam `review()`: hasil jaringan bergantung waktu, sedangkan
laporan gerbang harus bisa dihitung ulang siapa pun. Hasil dicatat publik (`ledger/pengajuan/rujukan/<submission_sha>.json`) dengan waktu periksa.

Status per rujukan:
  ADA            jawaban akhir HTTP 2xx (isi dibaca <= BATAS_BYTE, sha256 + jumlah byte dicatat; isi tidak disimpan)
  TIDAK_ADA      jawaban akhir 404 / 410 (halaman tidak ada)
  TAK_TERPERIKSA galat jaringan / DNS, batas waktu, 401 / 403 / 429 / 5xx, terlalu banyak pengalihan - BUKAN bukti tidak ada
  TIDAK_SAH      URL menunjuk tempat yang tidak boleh dihubungi: bukan https, host lokal / non-publik, atau nama yang di-resolve ke IP non-publik
                 (termasuk di tengah pengalihan) - pengaman SSRF
Vonis gerbang TIDAK diubah oleh pemeriksaan ini (USULAN builder: rujukan TIDAK_ADA / TIDAK_SAH -> TOLAK_FORMULIR).
Stdlib saja.
"""
from __future__ import annotations

import hashlib
import http.client
import ipaddress
import socket
import ssl
import time
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urljoin, urlsplit

from .submission import _url_problem

V = 1
BATAS_BYTE = 256 * 1024
MAKS_ALIH = 3
WAKTU_S = 15.0
UA = "Fabius-reference-check/1 (+https://fabius-one.vercel.app)"
ADA, TIDAK_ADA, TAK_TERPERIKSA, TIDAK_SAH = "ADA", "TIDAK_ADA", "TAK_TERPERIKSA", "TIDAK_SAH"


def ip_publik(ip: str) -> bool:
    """Hanya alamat yang bisa dirute di internet publik (bukan loopback, privat, link-local, multicast, cadangan)."""
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


def _resolve(host: str, port: int) -> List[str]:
    return sorted({ai[4][0] for ai in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)})


def _get(url: str, ip: str, waktu: float) -> tuple:
    """Satu GET ke `ip` yang SUDAH diperiksa (bukan nama yang di-resolve ulang = tanpa celah DNS rebinding); SNI + Host = nama asli."""
    u = urlsplit(url)
    host, port = u.hostname, u.port or 443
    ctx = ssl.create_default_context()
    raw = socket.create_connection((ip, port), timeout=waktu)
    try:
        sock = ctx.wrap_socket(raw, server_hostname=host)
    except Exception:
        raw.close()
        raise
    conn = http.client.HTTPSConnection(host, port, timeout=waktu, context=ctx)
    conn.sock = sock
    try:
        path = (u.path or "/") + (f"?{u.query}" if u.query else "")
        conn.request("GET", path, headers={"User-Agent": UA, "Accept": "*/*"})
        r = conn.getresponse()
        body = r.read(BATAS_BYTE) if 200 <= r.status < 300 else b""
        return r.status, r.getheader("Location"), body
    finally:
        conn.close()


def periksa(url: str, *, resolve: Callable[[str, int], List[str]] = _resolve, izin_ip: Callable[[str], bool] = ip_publik,
            get: Optional[Callable[[str, str, float], tuple]] = None, waktu: float = WAKTU_S, now: Optional[Callable[[], float]] = None) -> Dict[str, Any]:
    """Periksa satu URL. Tidak pernah melempar; tiap lompatan pengalihan diperiksa ulang (bentuk URL + IP publik)."""
    get = get or _get
    now = now or time.time
    out: Dict[str, Any] = {"url": url, "status": TAK_TERPERIKSA, "kode_http": None, "url_akhir": None, "byte": None, "sha256": None,
                           "alih": 0, "galat": None, "t": int(now())}
    cur = url
    for lompat in range(MAKS_ALIH + 1):
        prob = _url_problem(cur) if isinstance(cur, str) else "URL bukan teks"
        if prob:
            return {**out, "status": TIDAK_SAH, "url_akhir": cur, "galat": prob}
        u = urlsplit(cur)
        try:
            ips = resolve(u.hostname, u.port or 443)
        except OSError as e:
            return {**out, "url_akhir": cur, "galat": f"DNS: {type(e).__name__}"}
        if not ips:
            return {**out, "url_akhir": cur, "galat": "DNS: tidak ada alamat"}
        bukan = [ip for ip in ips if not izin_ip(ip)]
        if bukan:
            return {**out, "status": TIDAK_SAH, "url_akhir": cur, "galat": f"host di-resolve ke alamat non-publik ({bukan[0]})"}
        try:
            kode, lokasi, body = get(cur, ips[0], waktu)
        except Exception as e:  # noqa: BLE001 - jaringan / TLS / batas waktu: tidak membuktikan rujukan tidak ada
            return {**out, "url_akhir": cur, "galat": f"{type(e).__name__}"}
        out.update(kode_http=kode, url_akhir=cur, alih=lompat)
        if kode in (301, 302, 303, 307, 308) and lokasi:
            cur = urljoin(cur, lokasi)
            continue
        if 200 <= kode < 300:
            return {**out, "status": ADA, "byte": len(body), "sha256": "0x" + hashlib.sha256(body).hexdigest()}
        if kode in (404, 410):
            return {**out, "status": TIDAK_ADA}
        return {**out, "galat": f"HTTP {kode} (bukan bukti tidak ada)"}
    return {**out, "galat": f"lebih dari {MAKS_ALIH} pengalihan"}


def periksa_pengajuan(sub: Dict[str, Any], submission_sha: str, **kw) -> Dict[str, Any]:
    """Semua rujukan satu pengajuan -> catatan publik {v, submission_sha, t, rujukan: [...], ringkasan}."""
    refs = ((sub.get("theory") or {}).get("referensi") or []) if isinstance(sub, dict) else []
    hasil = [{"judul": r.get("judul"), **periksa(r.get("url"), **kw)} for r in refs if isinstance(r, dict)]
    jumlah = {s: sum(1 for h in hasil if h["status"] == s) for s in (ADA, TIDAK_ADA, TAK_TERPERIKSA, TIDAK_SAH)}
    return {"v": V, "submission_sha": submission_sha, "t": max([h["t"] for h in hasil], default=int(time.time())), "rujukan": hasil, "ringkasan": jumlah,
            "catatan": "keberadaan diperiksa kode (HTTP GET, hanya IP publik, maks 3 pengalihan); vonis gerbang tidak diubah oleh catatan ini"}

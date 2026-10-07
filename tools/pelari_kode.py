"""P167b: PELARI kode `kind=code` - layanan Railway TERPISAH, TANPA rahasia (image `railway/pelari/Dockerfile`, pengguna non-root).

Menerima kode privat + bar publik dari gerbang lewat jaringan privat Railway, menjalankannya di sandbox berlapis (`engine/kode.py::jalankan`: analisis
statis daftar-izin -> proses anak berbatas CPU / memori / waktu dinding / langkah, builtins terbatas -> dua proses PYTHONHASHSEED berbeda -> uji
kausalitas namespace segar) dan mengembalikan DATA berbatas saja: bobot per bar per varian + hasil uji. Tidak menyimpan kode, tidak menulis berkas,
tidak memanggil jaringan; gerbang G1-G11 + komit dijalankan pihak tepercaya atas DATA ini (`kode.PelariData` memvalidasinya lagi).

Rute:
  POST /run     {kode, bars: {aset: {t,o,h,l,c,v}}, varian: {label: params}, sampel: [t], dasar: label}  -> DATA (`kode.jalankan`)
  GET  /health  {ok, tanpa_rahasia, batas}
Penjaga: menolak MULAI bila lingkungan memuat variabel bernama seperti rahasia (KEY / SECRET / TOKEN / PASSW / MNEMONIC); satu pekerjaan sekaligus
(429 bila sibuk); badan <= 16 MB. Layanan ini tidak punya domain publik (hanya `*.railway.internal`); penyiapan Railway = langkah builder.

Pakai:  python -X utf8 tools/pelari_kode.py [--host ::] [--port 8090]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from engine import kode                                                   # noqa: E402

MAX_BODY = 16 * 1024 * 1024
RAHASIA = re.compile(r"(KEY|SECRET|TOKEN|PASSW|MNEMONIC|PRIVATE_K)", re.I)


def rahasia_di_env(env: Optional[Dict[str, str]] = None) -> List[str]:
    """Nama variabel lingkungan yang tampak seperti rahasia (pelari harus tanpa rahasia: kode asing berjalan di sini)."""
    env = os.environ if env is None else env
    return sorted(k for k in env if RAHASIA.search(k) and not k.startswith("PYTHON"))


def kerjakan(body: object) -> tuple:
    if not isinstance(body, dict):
        return 400, {"error": "body must be {kode, bars, varian, sampel, dasar}"}
    src, bars, varian = body.get("kode"), body.get("bars"), body.get("varian")
    if not isinstance(src, str) or not isinstance(bars, dict) or not isinstance(varian, dict):
        return 400, {"error": "kode (text), bars (object) and varian (object) are required"}
    for a, cols in bars.items():
        if not isinstance(a, str) or not isinstance(cols, dict) or set(cols) != {"t", "o", "h", "l", "c", "v"}:
            return 400, {"error": "bars must be {symbol: {t,o,h,l,c,v}}"}
        n = len(cols["t"]) if isinstance(cols["t"], list) else -1
        if n < 0 or any(not isinstance(cols[k], list) or len(cols[k]) != n for k in cols):
            return 400, {"error": "bars columns must be lists of equal length"}
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) for k in cols for x in cols[k]):
            return 400, {"error": "bars values must be numbers"}
    sampel = body.get("sampel") or []
    if not isinstance(sampel, list) or len(sampel) > 64 or any(isinstance(t, bool) or not isinstance(t, int) for t in sampel):
        return 400, {"error": "sampel must be a list of <= 64 integer bar times"}
    out = kode.jalankan(src, bars, varian, sampel, body.get("dasar") if isinstance(body.get("dasar"), str) else None)
    return 200, out


def make_handler(sibuk: threading.Lock):
    class H(BaseHTTPRequestHandler):
        def log_message(self, fmt, *a):                                       # tanpa isi permintaan di log (kode privat)
            sys.stdout.write(f"{self.command} {self.path.split('?')[0]} {a[1] if len(a) > 1 else ''}\n")

        def _send(self, code: int, obj: dict) -> None:
            raw = json.dumps(obj, separators=(",", ":"), allow_nan=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if self.path.rstrip("/") == "/health":
                return self._send(200, {"ok": True, "tanpa_rahasia": not rahasia_di_env(), "batas": kode.LIMITS, "modul": list(kode.MODUL)})
            return self._send(404, {"error": "unknown route"})

        def do_POST(self):
            if self.path.rstrip("/") != "/run":
                return self._send(404, {"error": "unknown route"})
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                return self._send(413, {"error": f"body larger than {MAX_BODY} bytes"})
            if not sibuk.acquire(blocking=False):
                return self._send(429, {"error": "busy: one job at a time"})
            try:
                try:
                    body = json.loads(self.rfile.read(n) or b"{}")
                except ValueError:
                    return self._send(400, {"error": "body is not valid JSON"})
                code, out = kerjakan(body)
                return self._send(code, out)
            except Exception as e:                                             # noqa: BLE001 - tanpa teks galat (bisa memuat isi kode)
                return self._send(500, {"error": type(e).__name__})
            finally:
                sibuk.release()
    return H


class Server6(ThreadingHTTPServer):
    address_family = socket.AF_INET6


def serve(host: str, port: int) -> None:
    cls = Server6 if ":" in host else ThreadingHTTPServer
    cls((host, port), make_handler(threading.Lock())).serve_forever()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default=os.environ.get("PELARI_HOST", "::"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8090")))
    a = ap.parse_args()
    bad = rahasia_di_env()
    if bad:
        print(f"MENOLAK MULAI: pelari harus tanpa rahasia, lingkungan memuat {bad}")
        return 3
    print(f"pelari kode mulai {a.host}:{a.port} | batas {json.dumps(kode.LIMITS, sort_keys=True)}", flush=True)
    serve(a.host, a.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

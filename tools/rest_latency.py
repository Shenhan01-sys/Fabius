"""P98: jeda terbit REST Binance sesudah penutupan bar harian (00:00Z) dan finalitas nilai di menit-menit pertama - syarat terakhir tahap 3
(tick dari REST segera sesudah penutupan, F-D83).

Yang diukur, untuk 16 perp universe bot:
  perp     fapi /fapi/v1/klines 1d     : detik pertama bar hari kemarin terlihat TERTUTUP, dan apakah o/h/l/c/v-nya berubah sesudah itu
  spot     api  /api/v3/klines 1d      : sama
  funding  fapi /fapi/v1/fundingRate   : detik pertama peristiwa funding 00:00Z terlihat, dan apakah rate-nya berubah sesudah itu
Polling tiap --every detik dari 30 detik sebelum 00:00Z sampai --window menit sesudahnya, lalu satu pembacaan ulang di +30 dan +60 menit (finalitas).
Jam: selisih jam lokal vs `serverTime` Binance dicatat di awal; jeda dilaporkan relatif terhadap 00:00:00Z menurut jam server.

Hanya membaca, tanpa kunci. Harus dijalankan dari tempat yang bisa menjangkau fapi (Railway Singapura, service `fabius-probe`):
  FABIUS_JOB=rest_latency  FABIUS_ARGS="--exit-zero"          (job menunggu sampai ±23:59:30Z lalu mengukur; selesai ±01:01Z)
Bila dimulai di dalam jendela (00:00-00:<window>Z) ia langsung mengukur sisa jendela; bila sesudahnya, ia menunggu tengah malam berikutnya.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import statistics
import sys
import time
from typing import Callable, Dict, List, Optional, Sequence, Tuple

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from engine.series import DAY_MS               # noqa: E402
from engine.spec import PERP_UNIVERSE          # noqa: E402

FAPI = "https://fapi.binance.com"
SPOT = "https://api.binance.com"
KINDS = ("perp", "spot", "funding")


def utc(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- pencatat (murni; diuji tanpa jaringan)
class Tracker:
    """Untuk tiap (jenis, simbol): kapan nilai pertama terlihat (ms jam server) dan setiap perubahan sesudahnya."""

    def __init__(self, close_ms: int):
        self.close_ms = close_ms
        self.first: Dict[Tuple[str, str], Tuple[int, tuple]] = {}
        self.last: Dict[Tuple[str, str], tuple] = {}
        self.changes: List[Tuple[str, str, int, tuple, tuple]] = []

    def see(self, kind: str, sym: str, value: Optional[tuple], t_server_ms: int) -> None:
        if value is None:
            return
        key = (kind, sym)
        if key not in self.first:
            self.first[key] = (t_server_ms, value)
        elif value != self.last[key]:
            self.changes.append((kind, sym, t_server_ms, self.last[key], value))
        self.last[key] = value

    def latency_s(self, kind: str) -> List[float]:
        return sorted((t - self.close_ms) / 1000 for (k, _), (t, _) in self.first.items() if k == kind)

    def missing(self, kind: str, symbols: Sequence[str]) -> List[str]:
        return [s for s in symbols if (kind, s) not in self.first]

    def digest(self, kind: str) -> str:
        body = {s: list(v) for (k, s), v in sorted(self.last.items()) if k == kind}
        return "0x" + hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def summary(self, symbols: Sequence[str]) -> List[str]:
        out = []
        for kind in KINDS:
            lat = self.latency_s(kind)
            miss = self.missing(kind, symbols)
            if lat:
                out.append(f"{kind:7s}: terlihat {len(lat)}/{len(symbols)} | jeda sesudah 00:00:00Z (detik, jam server) min {lat[0]:.1f} "
                           f"median {statistics.median(lat):.1f} maks {lat[-1]:.1f}" + (f" | TIDAK terlihat: {miss}" if miss else "")
                           + f" | sidik akhir {self.digest(kind)[:18]}…")
            else:
                out.append(f"{kind:7s}: TIDAK satu pun terlihat dalam jendela ({len(miss)} simbol)")
        n = len(self.changes)
        out.append(f"perubahan nilai sesudah pertama terlihat: {n}" + ("" if not n else " ->"))
        for kind, sym, t, a, b in self.changes[:20]:
            out.append(f"   {kind} {sym} @{(t - self.close_ms) / 1000:.1f}s: {a} -> {b}")
        return out


# ---------------------------------------------------------------- REST
class Rest:
    def __init__(self, get: Callable[[str], object]):
        self._get = get
        self.calls = 0
        self.errors = 0

    def get(self, url: str):
        self.calls += 1
        try:
            return self._get(url)
        except Exception as e:  # noqa: BLE001 - satu panggilan gagal = tidak terlihat di putaran ini, bukan berhenti
            self.errors += 1
            if self.errors <= 5:
                print(f"  ! {type(e).__name__}: {str(e)[:100]} ({url.split('?')[0]})")
            return None

    def closed_kline(self, base: str, path: str, sym: str, open_ms: int, now_server_ms: int) -> Optional[tuple]:
        rows = self.get(f"{base}{path}?symbol={sym}&interval=1d&startTime={open_ms}&limit=1")
        if not rows or int(rows[0][0]) != open_ms or int(rows[0][6]) >= now_server_ms:
            return None
        return tuple(float(x) for x in rows[0][1:6])

    def funding_at(self, sym: str, close_ms: int) -> Optional[tuple]:
        rows = self.get(f"{FAPI}/fapi/v1/fundingRate?symbol={sym}&startTime={close_ms - 60_000}&endTime={close_ms + 60_000}&limit=5")
        if not rows:
            return None
        ev = [r for r in rows if abs(int(r["fundingTime"]) - close_ms) <= 60_000]
        return (int(ev[0]["fundingTime"]), float(ev[0]["fundingRate"])) if ev else None

    def server_time(self) -> Optional[int]:
        r = self.get(f"{FAPI}/fapi/v1/time")
        return int(r["serverTime"]) if r else None


def http_json(url: str):
    import urllib.request
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; fabius-rest-latency/1.0)"}), timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def poll_once(rest: Rest, tr: Tracker, symbols: Sequence[str], open_ms: int, server_now: Callable[[], int], want_funding: bool = True) -> None:
    for sym in symbols:
        tr.see("perp", sym, rest.closed_kline(FAPI, "/fapi/v1/klines", sym, open_ms, server_now()), server_now())
        tr.see("spot", sym, rest.closed_kline(SPOT, "/api/v3/klines", sym, open_ms, server_now()), server_now())
        if want_funding and ("funding", sym) not in tr.first:                 # batas 500/5 menit untuk fundingRate: berhenti bertanya sesudah terlihat
            tr.see("funding", sym, rest.funding_at(sym, open_ms + DAY_MS), server_now())


def next_close(now_ms: int, window_min: int) -> int:
    """Penutupan (00:00Z) yang diukur: hari ini bila masih di dalam jendela, selain itu tengah malam berikutnya."""
    today = (now_ms // DAY_MS) * DAY_MS
    return today if now_ms - today <= window_min * 60_000 else today + DAY_MS


def main() -> int:
    ap = argparse.ArgumentParser(description="Jeda terbit REST Binance sesudah 00:00Z + finalitas (P98). Hanya membaca.")
    ap.add_argument("--symbols", default=",".join(PERP_UNIVERSE))
    ap.add_argument("--every", type=float, default=15.0, help="detik antar putaran polling")
    ap.add_argument("--window", type=int, default=10, help="menit polling sesudah 00:00Z")
    ap.add_argument("--exit-zero", action="store_true")
    a = ap.parse_args()
    syms = [s.strip() for s in a.symbols.split(",") if s.strip()]
    rest = Rest(http_json)
    try:
        st = rest.server_time()
        off = (st - int(time.time() * 1000)) if st else 0
        server_now = lambda: int(time.time() * 1000) + off                      # noqa: E731
        close_ms = next_close(server_now(), a.window)
        open_ms = close_ms - DAY_MS
        print(f"mulai {utc(server_now())} | region {os.environ.get('RAILWAY_REPLICA_REGION', '?')} | selisih jam server-lokal {off} ms | "
              f"mengukur bar {utc(open_ms)[:10]} (tutup {utc(close_ms)}) | {len(syms)} simbol, tiap {a.every:.0f} s, jendela {a.window} menit")
        start = close_ms - 30_000
        while server_now() < start:
            left = (start - server_now()) / 1000
            if left > 3600:
                print(f"  menunggu {left / 3600:.1f} jam")
            time.sleep(min(left, 3600))
        tr = Tracker(close_ms)
        end = close_ms + a.window * 60_000
        k = 0
        while server_now() < end:
            t0 = time.time()
            poll_once(rest, tr, syms, open_ms, server_now)
            k += 1
            seen = {kind: sum(1 for (kk, _) in tr.first if kk == kind) for kind in KINDS}
            print(f"  putaran {k} @{(server_now() - close_ms) / 1000:+.0f}s: terlihat perp {seen['perp']} spot {seen['spot']} funding {seen['funding']} | "
                  f"perubahan {len(tr.changes)}")
            time.sleep(max(0.0, a.every - (time.time() - t0)))
        for plus in (30, 60):
            while server_now() < close_ms + plus * 60_000:
                time.sleep(min(60.0, (close_ms + plus * 60_000 - server_now()) / 1000 + 0.5))
            poll_once(rest, tr, syms, open_ms, server_now)
            print(f"  baca ulang +{plus} menit: perubahan total {len(tr.changes)}")
        print("\nRINGKASAN P98")
        for line in tr.summary(syms):
            print("  " + line)
        print(f"  {rest.calls} panggilan REST, {rest.errors} gagal")
        print("VONIS: " + ("NILAI FINAL SEJAK PERTAMA TERLIHAT" if not tr.changes else "ADA NILAI YANG BERUBAH SESUDAH TERLIHAT - lihat daftar di atas"))
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"GAGAL: {type(e).__name__}: {str(e)[:200]}")
        return 0 if a.exit_zero else 1


if __name__ == "__main__":
    raise SystemExit(main())

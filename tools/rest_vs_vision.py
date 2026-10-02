"""Uji kesamaan REST Binance vs `ledger/bars` (zip Vision + funding zip bulanan) - prasyarat tahap 3 (F-D82): kalau SAMA PERSIS, tick bisa dibuat dari REST
segera sesudah penutupan bar tanpa mengubah satu bit pun dari yang dihitung ulang `engine.cli ledger verify` dari berkas Vision.

Per simbol (16 perp di engine/spec.py):
  perp     fapi /fapi/v1/klines 1d      vs  fut_<SYM>_1d.csv    (t,o,h,l,c,v sama persis sebagai float)
  spot     api  /api/v3/klines 1d       vs  spot_<SYM>_1d.csv
  funding  fapi /fapi/v1/fundingRate    vs  fund_<SYM>.csv      (waktu +-60 detik, rate sama persis) + jumlah per hari UTC (yang dipakai engine)
Plus: bar tertutup terakhir yang sudah ada di REST saat dijalankan vs baris terakhir CSV (Vision terbit ±9 jam sesudah penutupan).

Hanya membaca, tanpa kunci. fapi ditolak dari runner GitHub (451) dan dari laptop builder; dijangkau dari Railway Singapura. Di Railway dijalankan sebagai
service terpisah `fabius-probe` (tanpa variabel rahasia; BUKAN shell ke worker produksi):
  FABIUS_JOB=rest_vs_vision  FABIUS_ARGS="--from-github --exit-zero"     lalu   railway logs --service fabius-probe --lines 200
Lokal (uji kecil): python -X utf8 tools/rest_vs_vision.py --bars ledger/bars --symbols BTCUSDT --since 2026-09-01
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

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
UA = {"User-Agent": "Mozilla/5.0 (compatible; fabius-rest-check/1.0)"}
FIELDS = ("o", "h", "l", "c", "v")
FUND_TOL_MS = 60_000
Kl = Dict[int, Tuple[float, float, float, float, float]]


# ---------------------------------------------------------------- berkas
def read_klines_csv(path: str) -> Kl:
    out: Kl = {}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.reader(f):
            if r and r[0].strip().isdigit():
                out[int(r[0])] = tuple(float(x) for x in r[1:6])
    return out


def read_funding_csv(path: str) -> List[Tuple[int, float]]:
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.reader(f):
            if r and r[0].strip().isdigit():
                out.append((int(r[0]), float(r[1])))
    return sorted(out)


# ---------------------------------------------------------------- perbandingan (murni; diuji tanpa jaringan)
def compare_klines(csv_rows: Kl, rest_rows: Kl, t_from: int, t_to: int) -> dict:
    """Baris CSV dan REST dalam [t_from, t_to] (waktu buka). Sama = kelima kolom identik sebagai float."""
    a = {t: v for t, v in csv_rows.items() if t_from <= t <= t_to}
    b = {t: v for t, v in rest_rows.items() if t_from <= t <= t_to}
    both = sorted(set(a) & set(b))
    diff = []
    for t in both:
        for i, name in enumerate(FIELDS):
            if a[t][i] != b[t][i]:
                diff.append((t, name, a[t][i], b[t][i]))
    bad_t = {d[0] for d in diff}
    return {"n": len(both), "equal": len(both) - len(bad_t), "diff": diff, "only_csv": sorted(set(a) - set(b)), "only_rest": sorted(set(b) - set(a))}


def compare_funding(csv_ev: Sequence[Tuple[int, float]], rest_ev: Sequence[Tuple[int, float]], t_from: int, t_to: int,
                    tol_ms: int = FUND_TOL_MS) -> dict:
    """Pasangkan peristiwa funding (waktu +-tol); rate harus identik. Lalu jumlah per hari UTC (yang dipakai engine) dibandingkan."""
    a = [e for e in csv_ev if t_from <= e[0] <= t_to]
    b = [e for e in rest_ev if t_from - tol_ms <= e[0] <= t_to + tol_ms]
    i = j = 0
    pairs, only_a, only_b = [], [], []
    while i < len(a) and j < len(b):
        if abs(a[i][0] - b[j][0]) <= tol_ms:
            pairs.append((a[i], b[j]))
            i += 1
            j += 1
        elif a[i][0] < b[j][0]:
            only_a.append(a[i][0])
            i += 1
        else:
            only_b.append(b[j][0])
            j += 1
    only_a += [e[0] for e in a[i:]]
    only_b += [e[0] for e in b[j:] if e[0] <= t_to]
    rate_diff = [(x[0], x[1], y[1]) for x, y in pairs if x[1] != y[1]]
    da, db = defaultdict(float), defaultdict(float)
    for x, y in pairs:
        da[(x[0] // DAY_MS) * DAY_MS] += x[1]
        db[(x[0] // DAY_MS) * DAY_MS] += y[1]
    day_diff = [(d, da[d], db[d]) for d in sorted(da) if da[d] != db[d]]
    return {"n_csv": len(a), "matched": len(pairs), "rate_diff": rate_diff, "only_csv": only_a, "only_rest": only_b,
            "days": len(da), "day_diff": day_diff, "max_dt_ms": max((abs(x[0] - y[0]) for x, y in pairs), default=0)}


# ---------------------------------------------------------------- REST
class Rest:
    def __init__(self, pause_s: float = 0.25):
        self.pause_s = pause_s
        self.calls = 0

    def get(self, url: str):
        for attempt in range(5):
            self.calls += 1
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                    data = json.loads(r.read().decode("utf-8"))
                time.sleep(self.pause_s)
                return data
            except urllib.error.HTTPError as e:
                if e.code in (418, 429):
                    wait = int(e.headers.get("Retry-After") or 30)
                    print(f"  ! HTTP {e.code} - tunggu {wait} s")
                    time.sleep(wait)
                    continue
                raise
            except (urllib.error.URLError, TimeoutError):
                time.sleep(2 + 2 * attempt)
        raise RuntimeError(f"gagal 5x: {url.split('?')[0]}")

    def klines(self, base: str, path: str, sym: str, t0: int, now_ms: int, limit: int) -> Kl:
        out: Kl = {}
        cur = t0
        while True:
            rows = self.get(f"{base}{path}?symbol={sym}&interval=1d&startTime={cur}&limit={limit}")
            if not rows:
                break
            for r in rows:
                if int(r[6]) < now_ms:                       # hanya bar yang SUDAH tertutup
                    out[int(r[0])] = tuple(float(x) for x in r[1:6])
            if len(rows) < limit:
                break
            cur = int(rows[-1][0]) + 1
        return out

    def funding(self, sym: str, t0: int, now_ms: int) -> List[Tuple[int, float]]:
        out = []
        cur = t0
        while True:
            rows = self.get(f"{FAPI}/fapi/v1/fundingRate?symbol={sym}&startTime={cur}&limit=1000")
            if not rows:
                break
            out += [(int(r["fundingTime"]), float(r["fundingRate"])) for r in rows if int(r["fundingTime"]) < now_ms]
            if len(rows) < 1000:
                break
            cur = int(rows[-1]["fundingTime"]) + 1
        return sorted(out)


# ---------------------------------------------------------------- laporan
def d(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).strftime("%Y-%m-%d")


def run(bars: str, symbols: Sequence[str], since_ms: int, rest: Rest, now_ms: int) -> dict:
    tot = {"perp": [0, 0, 0, 0], "spot": [0, 0, 0, 0], "fund": [0, 0, 0, 0, 0]}
    lag = []
    for sym in symbols:
        for kind, fname, base, path, limit in (("perp", f"fut_{sym}_1d.csv", FAPI, "/fapi/v1/klines", 1500),
                                               ("spot", f"spot_{sym}_1d.csv", SPOT, "/api/v3/klines", 1000)):
            p = os.path.join(bars, fname)
            if not os.path.isfile(p):
                continue
            a = read_klines_csv(p)
            t0 = max(min(a), since_ms)
            b = rest.klines(base, path, sym, t0, now_ms, limit)
            c = compare_klines(a, b, t0, max(a))
            t = tot[kind]
            t[0] += c["n"]
            t[1] += c["equal"]
            t[2] += len(c["only_csv"])
            t[3] += len({x[0] for x in c["diff"]})
            ok = c["equal"] == c["n"] and not c["only_csv"] and not c["only_rest"]
            line = f"{kind:4s} {sym:9s} {d(t0)}..{d(max(a))}: {c['equal']}/{c['n']} sama persis"
            if c["only_csv"] or c["only_rest"]:
                line += f" | hanya CSV {len(c['only_csv'])} (mis. {[d(x) for x in c['only_csv'][:3]]}) | hanya REST {len(c['only_rest'])} (mis. {[d(x) for x in c['only_rest'][:3]]})"
            for t_, f_, x, y in c["diff"][:3]:
                line += f" | BEDA {d(t_)} {f_}: csv {x!r} rest {y!r}"
            print(("  " if ok else "! ") + line)
            if kind == "perp" and b:
                lag.append((sym, d(max(a)), d(max(b))))
        p = os.path.join(bars, f"fund_{sym}.csv")
        if os.path.isfile(p):
            a = read_funding_csv(p)
            t0 = max(a[0][0], since_ms)
            b = rest.funding(sym, t0 - FUND_TOL_MS, now_ms)
            c = compare_funding(a, b, t0, a[-1][0])
            t = tot["fund"]
            t[0] += c["n_csv"]
            t[1] += c["matched"] - len(c["rate_diff"])
            t[2] += len(c["only_csv"])
            t[3] += len(c["day_diff"])
            t[4] = max(t[4], c["max_dt_ms"])
            ok = not c["rate_diff"] and not c["only_csv"] and not c["only_rest"] and not c["day_diff"]
            line = (f"fund {sym:9s} {d(t0)}..{d(a[-1][0])}: {c['matched'] - len(c['rate_diff'])}/{c['n_csv']} peristiwa sama persis, "
                    f"{c['days'] - len(c['day_diff'])}/{c['days']} hari jumlahnya sama, selisih waktu maks {c['max_dt_ms']} ms")
            if c["only_csv"] or c["only_rest"]:
                line += f" | hanya CSV {len(c['only_csv'])} | hanya REST {len(c['only_rest'])} (mis. {[d(x) for x in c['only_rest'][:3]]})"
            for t_, x, y in c["rate_diff"][:3]:
                line += f" | BEDA {d(t_)}: csv {x!r} rest {y!r}"
            print(("  " if ok else "! ") + line)
    print("\nRINGKASAN")
    for kind in ("perp", "spot"):
        n, eq, oc, bad = tot[kind]
        print(f"  {kind}: {eq}/{n} bar sama persis (5 kolom); bar beda {bad}; bar hanya di CSV {oc}")
    n, eq, oc, bd, mx = tot["fund"]
    print(f"  funding: {eq}/{n} peristiwa sama persis; hari dengan jumlah beda {bd}; peristiwa hanya di CSV {oc}; selisih waktu maks {mx} ms")
    if lag:
        print(f"  bar perp tertutup terakhir: CSV {lag[0][1]} | REST {lag[0][2]} (saat ini {dt.datetime.fromtimestamp(now_ms / 1000, dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ})")
    return tot


def main() -> int:
    ap = argparse.ArgumentParser(description="Uji kesamaan REST Binance vs ledger/bars (hanya membaca).")
    ap.add_argument("--bars", help="folder ledger/bars")
    ap.add_argument("--from-github", action="store_true", help="ambil ledger/bars segar dari GitHub (clone sparse, seperti worker)")
    ap.add_argument("--symbols", default=",".join(PERP_UNIVERSE))
    ap.add_argument("--since", default="2000-01-01", help="hanya bar >= tanggal ini (YYYY-MM-DD)")
    ap.add_argument("--exit-zero", action="store_true", help="selalu keluar 0 (job sekali jalan di Railway: jangan dimulai ulang)")
    a = ap.parse_args()
    t_start = time.time()
    bars = a.bars
    if a.from_github:
        import operator_loop
        wd = os.path.join(tempfile.gettempdir(), "fabius-rest-check")
        head = operator_loop.sync(wd)
        bars = os.path.join(wd, "ledger", "bars")
        print(f"ledger/bars dari GitHub @ {head[:10]}")
    if not bars or not os.path.isdir(bars):
        print("butuh --bars DIR atau --from-github")
        return 0 if a.exit_zero else 2
    since_ms = int(dt.datetime.fromisoformat(a.since).replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
    now_ms = int(time.time() * 1000)
    print(f"mulai {dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ} | region {os.environ.get('RAILWAY_REPLICA_REGION', '?')} | simbol {a.symbols}")
    rest = Rest()
    try:
        tot = run(bars, [s.strip() for s in a.symbols.split(",") if s.strip()], since_ms, rest, now_ms)
    except Exception as e:  # noqa: BLE001 - job sekali jalan: gagal dicatat jelas, bukan dimulai ulang 10x oleh Railway
        print(f"GAGAL sesudah {rest.calls} panggilan: {type(e).__name__}: {str(e)[:200]}")
        return 0 if a.exit_zero else 1
    print(f"  {rest.calls} panggilan REST, {time.time() - t_start:.0f} s")
    all_ok = all(tot[k][0] == tot[k][1] and tot[k][2] == 0 for k in ("perp", "spot")) and tot["fund"][0] == tot["fund"][1] and tot["fund"][3] == 0
    print("VONIS: " + ("SAMA PERSIS" if all_ok else "ADA BEDA - lihat baris bertanda !"))
    return 0 if (all_ok or a.exit_zero) else 1


if __name__ == "__main__":
    raise SystemExit(main())

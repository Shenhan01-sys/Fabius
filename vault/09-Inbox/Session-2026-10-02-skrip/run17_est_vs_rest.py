# EKSPLORATIF - sesi 2 Okt 2026 (P92; lihat vault/00-Overview/03 - Decisions.md F-D76/F-D77).
# Bukan alat resmi. Hanya stdlib. Membaca REST publik Binance (tanpa kunci) bila terjangkau dari jaringan ini; tidak menulis apa pun ke repo.
"""Bandingkan estimasi funding yang SUDAH dikomit (ledger/bars/fund_est_<SYM>.csv) dengan funding aktual dari REST untuk satu hari.

    python -X utf8 run17_est_vs_rest.py --day 2026-10-01

REST `fapi.binance.com` terjangkau atau tidak tergantung jaringan dan waktu (2 Okt: laptop builder TLS terpotong ±08:5xZ tetapi 200 pada ±09:58Z; runner GitHub 451).
Bila tidak terjangkau, skrip berhenti dengan pesan - tidak menebak. Satuan galat: 1e-6 = 0,01 bps per peristiwa.
"""
import argparse
import csv
import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from engine.series import DAY_MS              # noqa: E402
from engine.spec import PERP_UNIVERSE         # noqa: E402

BARS = REPO / "ledger" / "bars"


def est_rows(sym, day_ms):
    p = BARS / f"fund_est_{sym}.csv"
    out = {}
    if p.exists():
        with open(p, newline="") as f:
            rd = csv.reader(f)
            next(rd, None)
            for r in rd:
                t = int(float(r[0]))
                if day_ms <= t < day_ms + DAY_MS:
                    out[t] = float(r[1])
    return out


def rest_rows(sym, day_ms):
    url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={sym}&startTime={day_ms - 3_600_000}&endTime={day_ms + DAY_MS - 1}&limit=10"
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (fabius-research/1.0)"}), timeout=30) as r:
        data = json.loads(r.read().decode())
    return {(int(x["fundingTime"]) // 60_000) * 60_000: float(x["fundingRate"]) for x in data if day_ms <= int(x["fundingTime"]) < day_ms + DAY_MS}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--day", required=True)
    a = ap.parse_args()
    day = int(dt.datetime.strptime(a.day, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
    errs = []
    for sym in PERP_UNIVERSE:
        e = est_rows(sym, day)
        try:
            r = rest_rows(sym, day)
        except Exception as ex:  # noqa: BLE001
            print(f"REST tidak terjangkau ({type(ex).__name__}): berhenti, tidak menebak")
            return 2
        pairs = [(t, e[t], r[t]) for t in sorted(e) if t in r]
        if len(pairs) != 3:
            print(f"{sym:9} pasangan est/aktual = {len(pairs)} (harus 3); est {len(e)}, aktual {len(r)}")
            continue
        d = [x[1] - x[2] for x in pairs]
        errs += d
        print(f"{sym:9} est {[round(x[1], 8) for x in pairs]}  aktual {[round(x[2], 8) for x in pairs]}  galat(1e-6) {[round(x * 1e6, 2) for x in d]}")
    if errs:
        ae = sorted(abs(x) for x in errs)
        print(f"\n{len(errs)} peristiwa: MAE {sum(ae) / len(ae) * 1e6:.2f}  median {ae[len(ae) // 2] * 1e6:.2f}  maks {ae[-1] * 1e6:.2f}  bias {sum(errs) / len(errs) * 1e6:+.2f}  (1e-6 = 0,01 bps)")
    print("Estimasi dikomit SEBELUM funding aktual dibaca (dibekukan di ledger/bars); satu hari = sampel kecil.")


if __name__ == "__main__":
    sys.exit(main())

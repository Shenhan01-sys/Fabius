"""Alat yang membatalkan klaim kami sendiri: efek K>=2 adalah artefak harga masuk, bukan edge.

Ditemukan 28 Sep 09:3xZ. Runtutannya:
  1. `px` bukan ticker: 71,7 % barisnya mengulang nilai sebelumnya (umur median harga 8,7 menit).
  2. Kejadian BERKERUMUN punya lebih banyak transaksi -> deret harganya lebih segar daripada kejadian
     sepi. Padahal outcome kami dihitung dari deret itu.
  3. Jadi "K>=2 mengalahkan K=1 di token yang sama" sebagian besar mengukur **segar tidaknya
     pengamatan kami**, bukan apa yang terjadi di pasar.

Uji yang memutuskan: kejadian yang sama, pairing yang sama, hanya SUMBER HARGA yang diganti.
  A masuk=px  keluar=px   -> yang kami terbitkan (+393,4 / +334,8)
  B masuk=tx  keluar=tx   -> kedua ujung harga peristiwa (yang benar-benar bisa didapat)
  C masuk=px  keluar=tx   -> isolasi sisi keluar
  D masuk=tx  keluar=px   -> isolasi sisi masuk
Hasilnya (557 kejadian, 58 token berpasangan, n=178): A **+93,0** (p=0,0066) -> D **+0,1**
(p=0,53); B **+0,3** (p=0,35). Efeknya hilang ketika harga masuk menjadi harga transaksi itu sendiri.

Alat ini TIDAK mengubah alat uji lain: ia hanya membaca, membandingkan, dan menulis artefak.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import evidence_stack as ES  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import prices as PR  # noqa: E402
import tx_prices as TP  # noqa: E402

MIN = 60
OUT_DIR = os.path.join(ROOT, "decisions")
ASPEK = ["cluster_ge2", "cluster_ge3", "repeat_maker", "money_spread", "buy_usd_ge_1k",
         "no_exit_flow", "fresh_token", "wide_flow"]
KOMB = ["A_px_px", "D_tx_px", "C_px_tx", "B_tx_tx"]

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def net(p0, p1, rt):
    return round(10000.0 * (p1 - p0) / p0 - rt, 1)


def build(horizon, window, maxage, tol):
    """Kejadian yang punya EMPAT harga; fitur dihitung seperti di `evidence_stack` (point-in-time)."""
    tx, pxs = ES.load()
    txs = TP.load_tx_series()["rows"]
    rt = costs.rt_cost()
    ev, drop = [], {"tanpa_masuk_px": 0, "tanpa_keluar_px": 0, "tanpa_masuk_tx": 0,
                    "tanpa_keluar_tx": 0}
    for tk, rows in tx.items():
        ps, ts = pxs.get(tk), txs.get(tk)
        if not ps or not ts:
            continue
        taken = []
        for b in [r for r in rows if r["buy"]]:
            t = b["t"]
            if any(abs(t - x) < horizon * MIN for x in taken):
                continue
            a0, a1 = PR.pre(ps, t, maxage), PR.exit_median(ps, t, horizon, tol)
            b0, b1 = PR.pre(ts, t, maxage), PR.exit_median(ts, t, horizon, tol)
            if a0 is None:
                drop["tanpa_masuk_px"] += 1
                continue
            if a1 is None:
                drop["tanpa_keluar_px"] += 1
                continue
            if b0 is None:
                drop["tanpa_masuk_tx"] += 1
                continue
            if b1 is None:
                drop["tanpa_keluar_tx"] += 1
                continue
            win = [r for r in rows if t - window * MIN <= r["t"] <= t]
            wb = [r for r in win if r["buy"]]
            wsn = [r for r in win if not r["buy"]]
            makers = {r["m"] for r in wb if r["m"]}
            usd_b = sum(r["u"] for r in wb)
            usd_s = sum(r["u"] for r in wsn)
            top = max((r["u"] for r in wb), default=0.0)
            first = rows[0]["t"]
            ev.append({"tk": tk, "t": t, "n_maker": len(makers),
                       "A_px_px": net(a0, a1, rt), "D_tx_px": net(b0, a1, rt),
                       "C_px_tx": net(a0, b1, rt), "B_tx_tx": net(b0, b1, rt),
                       "umur_masuk_px_s": t - max([x[0] for x in ps if x[0] <= t], default=t),
                       "cluster_ge2": len(makers) >= 2, "cluster_ge3": len(makers) >= 3,
                       "repeat_maker": len(wb) > len(makers),
                       "money_spread": usd_b > 0 and (top / usd_b) <= 0.6,
                       "buy_usd_ge_1k": usd_b >= 1000.0, "no_exit_flow": usd_s < usd_b,
                       "fresh_token": (t - first) <= 2 * window * MIN,
                       "wide_flow": len(makers) >= 2 and usd_b >= 500.0 and usd_s < 0.5 * usd_b})
            taken.append(t)
    return ev, drop


def paired(ev, fitur, key):
    on, off = {}, {}
    for e in ev:
        (on if e.get(fitur) else off).setdefault(e["tk"], []).append(e[key])
    d, toks = [], set()
    for tk, ons in on.items():
        offs = off.get(tk) or []
        if not offs:
            continue
        base = FC.med(offs)
        d.extend([x - base for x in ons])
        toks.add(tk)
    if len(d) < 12:
        return {"aspek": fitur, "harga": key, "token": len(toks), "n": len(d),
                "status": "SAMPEL TIDAK CUKUP"}
    lo, hi = FC.boot_median(d)
    wins = sum(1 for v in d if v > 0)
    return {"aspek": fitur, "harga": key, "token": len(toks), "n": len(d),
            "median_selisih_bps": round(FC.med(d), 1),
            "ci_lo": None if lo is None else round(lo, 1),
            "ci_hi": None if hi is None else round(hi, 1),
            "proporsi_positif": round(100.0 * wins / len(d), 1),
            "p": round(FC.sign_p(wins, len(d)), 4)}


def self_test():
    """Yang tidak boleh berubah: `net` memotong ongkos, dan A/B pakai kejadian yang sama."""
    rt = 59.0
    assert net(1.0, 1.0, rt) == -59.0
    assert abs(net(1.0, 1.01, rt) - 41.0) < 1e-6
    # 12 token, masing-masing 1 kejadian berkerumun + 1 tidak -> n pas di ambang "cukup sampel"
    ev = []
    for i in range(12):
        ev.append({"tk": "t%02d" % i, "A_px_px": 10.0, "B_tx_tx": 8.0, "cluster_ge2": True})
        ev.append({"tk": "t%02d" % i, "A_px_px": 0.0, "B_tx_tx": 0.0, "cluster_ge2": False})
    ra = paired(ev, "cluster_ge2", "A_px_px")
    rb = paired(ev, "cluster_ge2", "B_tx_tx")
    assert ra.get("status") is None and rb.get("status") is None, (ra, rb)
    assert ra["n"] == rb["n"] == 12, (ra, rb)
    assert ra["median_selisih_bps"] == 10.0 and rb["median_selisih_bps"] == 8.0, (ra, rb)
    assert abs(ra["ci_lo"] - 10.0) < 1e-9 and ra["p"] == round(1.0 / 4096.0, 4), ra
    print("self-test OK: net(1.0->1.0)=%.1f | pairing identik kedua sumur (n=%d) | A-B = %+0.1f "
          "= persis selisih harga masuk | p=%.6f"
          % (net(1.0, 1.0, rt), ra["n"], ra["median_selisih_bps"] - rb["median_selisih_bps"],
             ra["p"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--window", type=int, default=15)
    ap.add_argument("--maxage", type=int, default=PR.MAX_STALE_MIN)
    ap.add_argument("--tol", type=int, default=15)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        self_test()
        return
    ev, drop = build(a.horizon, a.window, a.maxage, a.tol)
    umur = sorted(e["umur_masuk_px_s"] for e in ev)
    print("kejadian dengan EMPAT harga: %d pada %d token | sensor %s"
          % (len(ev), len({e["tk"] for e in ev}), drop))
    print("umur harga masuk px pada himpunan ini: median %d s | p90 %d s"
          % (FC.med(umur), umur[int(0.9 * (len(umur) - 1))]))
    print("\nA=px->px (terbit)  D=tx->px (masuk jujur)  C=px->tx  B=tx->tx (paling jujur)")
    print("   %-15s %-9s %6s %6s %11s %-20s %8s %8s" % ("aspek", "harga", "token", "n",
                                                        "med selisih", "CI 95 %", "% positif", "p"))
    rows = []
    for f in ASPEK:
        for k in KOMB:
            r = paired(ev, f, k)
            rows.append(r)
            if r.get("status"):
                print("   %-15s %-9s %6d %6d   %s" % (f, k, r["token"], r["n"], r["status"]))
            else:
                print("   %-15s %-9s %6d %6d %+11.1f [%+6.0f; %+8.0f] %7.1f%% %8.4f"
                      % (f, k, r["token"], r["n"], r["median_selisih_bps"], r["ci_lo"], r["ci_hi"],
                         r["proporsi_positif"], r["p"]))
        print()
    ps_a = FC.bh([(r["aspek"], r["p"]) for r in rows if r["harga"] == "A_px_px" and r.get("p")])
    ps_b = FC.bh([(r["aspek"], r["p"]) for r in rows if r["harga"] == "B_tx_tx" and r.get("p")])
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "horizon_menit": a.horizon, "window_menit": a.window, "maxage_menit": a.maxage,
           "cost_bps_rt": costs.rt_cost(), "kejadian": len(ev),
           "token": len({e["tk"] for e in ev}), "sensor": drop,
           "rows": rows, "lolos_bh_A_px_px": sorted(ps_a), "lolos_bh_B_tx_tx": sorted(ps_b),
           "simpulan": ("efek positif pada A tidak bertahan ketika harga masuk = harga transaksi "
                        "itu sendiri (B/D); yang kami terbitkan mengukur kesegaran pengamatan, "
                        "bukan pasar"),
           "batas": ["hanya kejadian yang punya kedua sumur (bias selektif: token yang cukup panas "
                     "untuk muncul di px DAN punya transaksi di jendela keluar)",
                     "satu jendela ~49 jam, satu rezim", "belum ada fill nyata; harga peristiwa "
                     "bukan harga yang kami dapat untuk ukuran posisi apa pun"]}
    out["rows_sha256"] = "0x" + hashlib.sha256(canon(rows).encode()).hexdigest()
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, "entry-decomposition-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True,
              ensure_ascii=False)
    print("BH pada A(px->px)      : %s" % (sorted(ps_a) or "-"))
    print("BH pada B(tx->tx)      : %s" % (sorted(ps_b) or "-"))
    print("artefak: decisions/%s rows_sha256=%s..." % (os.path.basename(p),
                                                      out["rows_sha256"][:16]))


if __name__ == "__main__":
    main()

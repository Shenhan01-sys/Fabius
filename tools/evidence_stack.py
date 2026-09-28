"""Stack bukti (P19) - aspek-aspek yang boleh menambah kepercayaan, diuji SATU PER SATU.

Kenapa alat ini ada, semuanya terukur 28 Sep:
  - kerumunan maker (K>=2) memisahkan hasil 30 menit **dalam token yang sama**: median +363,6 bps,
    CI [+0; +772], lolos BH (`tools/flow_cluster_test.py`). Sendirian itu tipis.
  - data struktural universe (top10/lock/bundler/likuiditas) cuma ada untuk **13,3 %** peristiwa
    beli kami (208 dari 1.561 token pernah muncul di snapshot) -> tidak bisa jadi tulang punggung.
  - jalur harga pantau (`universe/record_watch_prices.py`) menjawab 123 dari 136 token (90 %) dan
    memberi likuiditas/FDV/volum/jumlah beli-jual per jam dari venue - tapi baru mulai hari ini.

Aturan main yang tidak boleh tawar-menawar: **setiap aspek diuji seperti kerumunan diuji**, bukan
diberi manfaat dari keraguan.
  acuan     = kejadian pada TOKEN YANG SAMA yang TIDAK memicu fitur itu
  outcome   = net bps pada horison H; harga dari `px` di KEDUA ujung; ongkos dari `tools/costs.py`
  statistik = median selisih + bootstrap 4.000 (seed tetap) + tanda-uji eksak + BH alpha 0,10
  hasil     = mana yang memisahkan; yang tidak memisahkan ditulis sebagai TIDAK, tidak dihapus
Lalu aspek yang lulus ditumpuk dan tumpukannya diuji sebagai hipotesis sendiri ("komponen >=2").
Itu satu-satunya bentuk "compounding" yang boleh dipercaya: tumpukan harus membuktikan dirinya,
bukan mewarisi bukti bagiannya.

Pakai:  python -X utf8 tools/evidence_stack.py
       python -X utf8 tools/evidence_stack.py --horizon 30 --window 15
Artefak: decisions/evidence-stack-<UTC>.json (+ rows_sha256)
"""
from __future__ import annotations

import argparse
import bisect
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
import prices as PR  # noqa: E402  (satu tempat untuk deret harga &
#                                          aturan SATU sumber per kejadian)
import flow_cluster_test as FC  # noqa: E402  (satu definisi outcome + statistik untuk semua uji aliran)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

OUT_DIR = os.path.join(ROOT, "decisions")
FLOW = os.path.join(ROOT, "universe", "wallet-flow.jsonl")
MIN = 60
FEATURES = ["cluster_ge2", "cluster_ge3", "repeat_maker", "money_spread", "buy_usd_ge_1k",
            "no_exit_flow", "fresh_token", "wide_flow"]
ORDER = {"gmgn": (PR.SRC_GMGN,), "both": (PR.SRC_GMGN, PR.SRC_WATCH)}


def canon(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load():
    """Per token: daftar transaksi (beli/jual) dan daftar harga `px`, keduanya terurut waktu."""
    tx, pxs = {}, {}
    if not os.path.exists(FLOW):
        raise SystemExit("tidak ada %s - jalankan universe/record_wallet_flow.py dulu" % FLOW)
    for ln in io.open(FLOW, encoding="utf-8", errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        d = json.loads(ln)
        tk = str(d.get("tk") or "").lower()
        t = int(d.get("t") or 0)
        if not tk or not t:
            continue
        if d.get("k") == "px":
            p = float(d.get("p") or 0.0)
            if p > 0:
                pxs.setdefault(tk, []).append((t, p))
            continue
        if d.get("k") not in ("tx", "txc"):
            continue
        u = float(d.get("u") or 0.0)
        p = float(d.get("p") or 0.0)
        if u <= 0 or p <= 0:
            continue
        tx.setdefault(tk, []).append({"t": t, "m": str(d.get("m") or "").lower(),
                                      "u": u, "buy": bool(d.get("b"))})
    for d in (tx, pxs):
        for tk in d:
            d[tk].sort(key=lambda r: (r["t"] if isinstance(r, dict) else r[0]))
    # kanonik SATU kali: same-timestamp px dilebur di FC.dedupe_px, bukan dibiarkan bergantung
    # pada urutan berkas - itulah penyebab dua alat kami memberi outcome beda untuk kejadian sama
    pxs = {tk: FC.dedupe_px(s) for tk, s in pxs.items()}
    return tx, pxs


def window_slice(rows, ts, lo, hi):
    return [rows[i] for i in range(bisect.bisect_left(ts, lo), bisect.bisect_right(ts, hi))]


def build_events(tx, sources, horizon, window, order):
    """Kejadian yang bisa dinilai: SATU sumber untuk kedua ujung (lihat tools/prices.py).

    Corongnya dicetak lengkap tiga-tiganya, karena versi pertama alat ini menyembunyikan yang
    paling besar: kejadian yang dibuang karena BELI-nya berdekatan (< horison) dengan beli lain
    pada token yang sama. Itu bukan "tidak ada sinyal", itu belum sempat jadi uji.
    """
    H, W = horizon * MIN, window * MIN
    ev, dropped = [], {"tumpang_tindih_j": 0, "tanpa_px_masuk": 0, "tanpa_px_keluar": 0,
                       "tidak_ada_px_sama_sekali": 0}
    for tk, rows in tx.items():
        ada = any(sources.get(nm, {}).get("rows", {}).get(tk) for nm in order)
        if not ada:
            for b in rows:
                if b["buy"]:
                    dropped["tidak_ada_px_sama_sekali"] += 1
            continue
        buys = [r for r in rows if r["buy"]]
        taken = []
        for b in buys:
            t = b["t"]
            if any(abs(t - x) < H for x in taken):
                dropped["tumpang_tindih_j"] += 1
                continue
            nm, p0, p1 = PR.pick_source(sources, tk, t, horizon, order)
            if nm is None:
                # bedakan sebabnya: tidak ada harga SEBELUM beli, atau tidak ada harga KELUAR
                pre_ok = any(PR.pre(sources[nm2]["rows"].get(tk) or [], t) is not None
                             for nm2 in order if sources.get(nm2, {}).get("rows", {}).get(tk))
                dropped["tanpa_px_masuk" if not pre_ok else "tanpa_px_keluar"] += 1
                continue
            net = round(10000.0 * (p1 - p0) / p0 - costs.rt_cost(), 1)
            win = window_slice(rows, [r["t"] for r in rows], t - W, t)
            wb = [r for r in win if r["buy"]]
            wsn = [r for r in win if not r["buy"]]
            makers = {r["m"] for r in wb if r["m"]}
            usd_b = sum(r["u"] for r in wb)
            usd_s = sum(r["u"] for r in wsn)
            top = max((r["u"] for r in wb), default=0.0)
            first = rows[0]["t"]
            ev.append({"tk": tk, "t": t, "net_bps": net, "sumber": nm, "n_maker": len(makers),
                       "usd_b": round(usd_b, 2), "usd_s": round(usd_s, 2),
                       "cluster_ge2": len(makers) >= 2,
                       "cluster_ge3": len(makers) >= 3,
                       "repeat_maker": len(wb) > len(makers),
                       "money_spread": usd_b > 0 and (top / usd_b) <= 0.6,
                       "buy_usd_ge_1k": usd_b >= 1000.0,
                       "no_exit_flow": usd_s < usd_b,
                       "fresh_token": (t - first) <= 2 * W,
                       "wide_flow": len(makers) >= 2 and usd_b >= 500.0 and usd_s < 0.5 * usd_b})
            taken.append(t)
    return ev, dropped


def _pair(ev, pred, label):
    on, off = {}, {}
    for e in ev:
        (on if pred(e) else off).setdefault(e["tk"], []).append(e["net_bps"])
    d, toks = [], set()
    for tk, ons in on.items():
        offs = off.get(tk) or []
        if not offs:
            continue
        base = FC.med(offs)
        d.extend([x - base for x in ons])
        toks.add(tk)
    if len(d) < 12:
        return {"fitur": label, "token": len(toks), "n": len(d), "status": "SAMPEL TIDAK CUKUP"}
    lo, hi = FC.boot_median(d)
    wins = sum(1 for v in d if v > 0)
    return {"fitur": label, "token": len(toks), "n": len(d),
            "median_selisih_bps": round(FC.med(d), 1),
            "ci_lo": None if lo is None else round(lo, 1),
            "ci_hi": None if hi is None else round(hi, 1),
            "proporsi_positif": round(100.0 * wins / len(d), 1),
            "mean_selisih_bps": round(sum(d) / len(d), 1),
            "p": round(FC.sign_p(wins, len(d)), 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--window", type=int, default=15)
    ap.add_argument("--px", default="gmgn", choices=("gmgn", "both"), help="gmgn = hanya harga rekaman sendiri (baku); both = pantau DexScreener boleh jadi cadangan (tetap satu sumber per kejadian)")
    a = ap.parse_args()
    rt = costs.rt_cost()
    tx, _ = load()
    sources = PR.load_all()
    order = ORDER[a.px]
    ev, dropped = build_events(tx, sources, a.horizon, a.window, order)
    ntok = len({e["tk"] for e in ev})
    print("bahan: %d kejadian terukur pada %d token | ongkos %.1f bps (%s) | horison %d m | jendela %d m"
          % (len(ev), ntok, rt, costs.cost_basis(), a.horizon, a.window))
    print("sensor: %s   (periksa satuan: jam rekaman %.1f)"
          % (dropped, (max(e["t"] for e in ev) - min(e["t"] for e in ev)) / 3600.0))
    assert (max(e["t"] for e in ev) - min(e["t"] for e in ev)) / 3600.0 > 1.0, "satuan waktu salah"
    print("\nfrekuensi fitur di antara kejadian yang bisa dinilai:")
    for f in FEATURES:
        c = sum(1 for e in ev if e.get(f))
        print("   %-14s %5d  %5.1f %%" % (f, c, 100.0 * c / max(len(ev), 1)))
    print("\nberpasangan DALAM TOKEN (median selisih net bps; bootstrap 4.000; BH alpha 0,10):")
    rows = [_pair(ev, (lambda e, f=f: bool(e.get(f))), f) for f in FEATURES]
    ps = [(r["fitur"], r["p"]) for r in rows if r.get("p") is not None]
    lulus = FC.bh(ps)
    print("   %-15s %6s %6s %11s %-19s %8s %9s %s"
          % ("fitur", "token", "n", "med selisih", "CI 95 %", "positif", "p", "BH"))
    for r in rows:
        if r.get("status"):
            print("   %-15s %6d %6d   %s" % (r["fitur"], r["token"], r["n"], r["status"]))
            continue
        print("   %-15s %6d %6d %11.1f %-19s %7.1f%% %9.4f %s"
              % (r["fitur"], r["token"], r["n"], r["median_selisih_bps"],
                 "[%+.0f; %+.0f]" % (r["ci_lo"], r["ci_hi"]), r["proporsi_positif"], r["p"],
                 "LOLOS" if r["fitur"] in lulus else "-"))
    print("\nsumur harga (satu kejadian = satu sumber, `tools/prices.py`):")
    for nm in sorted({e.get("sumber") for e in ev}):
        one = [e for e in ev if e.get("sumber") == nm]
        r = _pair(one, lambda e: e.get("cluster_ge2"), "K>=2 @%s" % nm)
        if r.get("status"):
            print("   %-6s %7d kejadian  token=%d n=%d  %s"
                  % (nm, len(one), r["token"], r["n"], r["status"]))
        else:
            print("   %-6s %7d kejadian  token=%-4d n=%-4d med %+9.1f CI [%+.0f; %+.0f] p=%.4f"
                  % (nm, len(one), r["token"], r["n"], r["median_selisih_bps"], r["ci_lo"],
                     r["ci_hi"], r["p"]))
    dl = PR.delta_report(sources)
    print("   selisih dua sumber pada menit yang sama: %s" % (json.dumps(dl, sort_keys=True)
          if dl.get("n") else "belum ada pasangan cukup"))
    st = _pair(ev, lambda e: sum(1 for f in lulus if e.get(f)) >= 2, "stack>=2")
    print("\ntumpukan aspek yang LULUS uji sendiri (>=2 menyala bersamaan), vs 0-1 di token sama:")
    if st.get("status"):
        print("   %s - token=%d n=%d" % (st["status"], st["token"], st["n"]))
    else:
        print("   token=%d n=%d median %+.1f bps CI [%+.0f; %+.0f] positif %.1f%% p=%.4f -> %s"
              % (st["token"], st["n"], st["median_selisih_bps"], st["ci_lo"], st["ci_hi"],
                 st["proporsi_positif"], st["p"],
                 "LOLOS BH" if st["fitur"] in FC.bh([(st["fitur"], st["p"])]) else "tidak"))
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "horizon_menit": a.horizon, "window_menit": a.window, "sumber_px": list(order),
           "cost_bps_rt": rt,
           "cost_basis": costs.cost_basis(), "kejadian": len(ev), "token": ntok, "sensor": dropped,
           "frekuensi": {f: sum(1 for e in ev if e.get(f)) for f in FEATURES},
           "rows": rows, "lulus_bh": sorted(lulus), "stack": st,
           "batas": ["satu jendela rekaman (~43 jam), satu rezim - hari kedua belum ada",
                     "kelas bersarang (cluster_ge3 di dalam cluster_ge2): bukan uji bebas",
                     "maker = yang tampil di feed vendor; kerumunan yang tidak terekam tidak terlihat,"
                     " jadi semua angka kerumunan adalah batas BAWAH",
                     "token yang hilang dari sorotan sebelum horison TIDAK DIUJI, bukan dinilai nol",
                     "belum ada fill nyata, biaya keluar, atau ukuran posisi - ini probabilitas, "
                     "bukan PnL"]}
    out["rows_sha256"] = "0x" + hashlib.sha256(canon(rows).encode()).hexdigest()
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, "evidence-stack-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True,
              ensure_ascii=False)
    print("\nartefak: decisions/%s rows_sha256=%s..." % (os.path.basename(p), out["rows_sha256"][:16]))


if __name__ == "__main__":
    main()

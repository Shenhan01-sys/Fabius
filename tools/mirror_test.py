"""Uji cermin: kalau kerumunan BELI meramalkan TURUN, apa kerumunan JUAL meramalkan NAIK?

Ini pertanyaan yang benar untuk agen long-only di spot memecoin: kita tidak bisa short, jadi
"tahu kapan jangan masuk" baru berguna kalau (a) dia juga berarti "jual saat kerumunan masuk"
(mengunci +491 bps yang sekarang kami buang), atau (b) ada sisi lain yang boleh dibeli.

Semua pakai harga PERISTIWA (`tx.t`, `tx.p`) supaya tidak mengulang kesalahan F-D30:
  - harga masuk = harga transaksi pada detik t (umur 0) -> yang benar-benar bisa kita dapat
  - harga keluar = median harga peristiwa pada t+[H-15, H+15] menit
  - pairing = kejadian pada TOKEN yang sama yang tidak memicu aspek
  - statistik = median + bootstrap 4.000 (seed tetap) + tanda-uji eksak + BH alpha 0,10
  - ongkos 59 bps round-trip (measured-own-venue) sudah dipotong dari setiap net
"""
import bisect
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import tx_prices as TP  # noqa: E402

MIN = 60
rt = costs.rt_cost()

# muat transaksi per token (maker, sisi, usd, waktu) + deret harga peristiwa
txs, series = {}, {}
for ln in io.open(R + r"\universe\wallet-flow.jsonl", encoding="utf-8", errors="replace"):
    ln = ln.strip()
    if not ln or ln.startswith("#"):
        continue
    d = json.loads(ln)
    if d.get("k") not in ("tx", "txc"):
        continue
    tk = str(d.get("tk") or "").lower()
    t = int(d.get("t") or 0)
    p = float(d.get("p") or 0)
    if not tk or not t or p <= 0:
        continue
    txs.setdefault(tk, []).append({"t": t, "m": str(d.get("m") or "").lower(),
                                   "buy": bool(d.get("b")), "u": float(d.get("u") or 0)})
    series.setdefault(tk, []).append((t, p))
for tk in txs:
    txs[tk].sort(key=lambda r: r["t"])
series = {tk: TP.FC.dedupe_px(sorted(v, key=lambda r: r[0])) for tk, v in series.items()}


def pre_exit(tk, t, H, tol=15):
    s = series.get(tk) or []
    lo, hi = t + (H - tol) * MIN, t + (H + tol) * MIN
    w = [p for tt, p in s if lo <= tt <= hi]
    return FC.med(w) if w else None


def pre_entry(tk, t):
    s = series.get(tk) or []
    i = bisect.bisect_right([x[0] for x in s], t) - 1
    return s[i][1] if i >= 0 else None


def bangun(H, W):
    """Satu kejadian per token per <H menit; fitur dihitung hanya dari data <= t."""
    ev, taken_all = [], {}
    for tk, rows in txs.items():
        taken = []
        for r in rows:
            t = r["t"]
            if any(abs(t - x) < H * MIN for x in taken):
                continue
            win = [q for q in rows if t - W * MIN <= q["t"] <= t]
            wb = [q for q in win if q["buy"]]
            ws = [q for q in win if not q["buy"]]
            mb = {q["m"] for q in wb if q["m"]}
            ms = {q["m"] for q in ws if q["m"]}
            usd_b = sum(q["u"] for q in wb)
            usd_s = sum(q["u"] for q in ws)
            p0, p1 = pre_entry(tk, t), pre_exit(tk, t, H)
            if p0 and p1:
                net = round(10000.0 * (p1 - p0) / p0 - rt, 1)
                # seberapa jauh harga kini di bawah puncak 60 menit terakhir (0 = di puncak)
                hi60 = max([p for tt, p in (series.get(tk) or []) if t - 60 * MIN <= tt <= t],
                           default=p0)
                ev.append({"tk": tk, "t": t, "net": net, "p0": p0, "p1": p1,
                           "horizon_m": H, "usd_b": usd_b, "usd_s": usd_s, "n_maker": len(mb),
                           "beli_2": len(mb) >= 2, "beli_3": len(mb) >= 3,
                           "jual_2": len(ms) >= 2, "jual_3": len(ms) >= 3,
                           "jual_bersih": len(ms) >= 2 and usd_s >= 1.5 * usd_b,
                           "sepi_beli": len(mb) <= 1 and usd_b < 100.0,
                           "tarik_dari_puncak": p0 < 0.7 * hi60,
                           "jatuh_dalam": p0 < 0.85 * max(
                               [p for tt, p in (series.get(tk) or [])
                                if t - 15 * MIN <= tt <= t], default=p0),
                           "usd_s": usd_s, "usd_b": usd_b})
                taken.append(t)
    return ev


def berpasangan(ev, fitur):
    on, off = {}, {}
    for e in ev:
        (on if e.get(fitur) else off).setdefault(e["tk"], []).append(e["net"])
    d, toks = [], set()
    for tk, ons in on.items():
        offs = off.get(tk) or []
        if not offs:
            continue
        base = FC.med(offs)
        d.extend([x - base for x in ons])
        toks.add(tk)
    if len(d) < 12:
        return {"aspek": fitur, "token": len(toks), "n": len(d), "status": "SAMPEL KECIL"}
    lo, hi = FC.boot_median(d)
    wins = sum(1 for v in d if v > 0)
    return {"aspek": fitur, "token": len(toks), "n": len(d), "med": round(FC.med(d), 1),
            "lo": None if lo is None else round(lo, 1), "hi": None if hi is None else round(hi, 1),
            "pos": round(100.0 * wins / len(d), 1), "p": round(FC.sign_p(wins, len(d)), 4)}


ASPEK = ["beli_2", "beli_3", "jual_2", "jual_3", "jual_bersih", "sepi_beli",
         "tarik_dari_puncak", "jatuh_dalam"]
# bisa diimpor (alat lain pakai `bangun()`/`ASPEK`) tanpa mengulang seluruh uji di bawah
RUN = __name__ == "__main__"
for H in ((30, 60) if RUN else ()):
    ev = bangun(H, 15)
    print("\n=== horison %d m | %d kejadian pada %d token (harga peristiwa, ongkos %.0f bps) ==="
          % (H, len(ev), len({e["tk"] for e in ev}), rt))
    print("   frekuensi: %s" % " ".join("%s=%d" % (f, sum(1 for e in ev if e[f])) for f in ASPEK))
    rows = []
    for f in ASPEK:
        r = berpasangan(ev, f)
        rows.append(r)
        if r.get("status"):
            print("   %-18s %s" % (f, r["status"]))
        else:
            print("   %-18s token=%-4d n=%-5d med %+9.1f CI [%+8.1f; %+9.1f] %5.1f%% positif p=%.4f"
                  % (f, r["token"], r["n"], r["med"], r["lo"], r["hi"], r["pos"], r["p"]))
    lulus = FC.bh([(r["aspek"], r["p"]) for r in rows if r.get("p") is not None])
    print("   BH alpha 0,10 lolos (satu arah 'lebih baik'): %s" % (sorted(lulus) or "-"))
    semua = [e["net"] for e in ev]
    print("   baseline SEMUA kejadian: median %+8.1f bps | %d dari %d positif (%.1f %%)"
          % (FC.med(semua), sum(1 for x in semua if x > 0), len(semua),
             100.0 * sum(1 for x in semua if x > 0) / len(semua)))
    # aturan keluar: jual SAAT kerumunan beli, bukan 30 menit sesudahnya
    on = [e["net"] for e in ev if e["beli_2"]]
    off = [e["net"] for e in ev if not e["beli_2"]]
    print("   NET absolut: beli_2 %+8.1f (n=%d) | bukan %+8.1f (n=%d) | selisih %+8.1f bps"
          % (FC.med(on), len(on), FC.med(off), len(off), FC.med(on) - FC.med(off)))
    hold = [e["net"] for e in ev if e["beli_3"]]
    print("   beli_3             %+8.1f (n=%d) -> keluar sekarang vs 30 m lagi = %+0.1f bps"
          % (FC.med(hold), len(hold), FC.med(hold) - FC.med(off)))
    # apakah ada CELAH positif sama sekali? lihat desil terbaik dari net
    q = sorted(semua)
    print("   desil net: p10 %+8.1f | p25 %+8.1f | p50 %+8.1f | p75 %+8.1f | p90 %+9.1f | p99 %+9.1f"
          % (q[int(.10 * len(q))], q[int(.25 * len(q))], FC.med(q), q[int(.75 * len(q))],
             q[int(.90 * len(q))], q[int(.99 * len(q))]))
    for f in ASPEK:
        xs = [e["net"] for e in ev if e[f]]
        if len(xs) >= 20:
            print("   absolut %-18s n=%-5d med %+9.1f | %4.1f%% positif"
                  % (f, len(xs), FC.med(xs), 100.0 * sum(1 for x in xs if x > 0) / len(xs)))

"""E21 (P45) - mengukur `i`: seberapa jauh harga SUDAH LEWAT level saat kami sempat melihatnya.

Semua klaim stop-loss di repo ini bertumpu pada satu variabel yang selama ini cuma diasumsikan.
Penurunan di [[06-Results/23 - Gerbang Trailing]]:

    PnL = pi - d - s - i - C        `s` = spread   `i` = jarak antara "menyentuh level" dan "terisi"

Osler (NY Fed SR150) sudah memberi alasan kenapa `i` bukan nol: pergerakan jadi *\x22unusually
rapid\x22* tepat di level tempat stop menumpuk. Tapi angka literatur itu bukan angka venue kami, dan
kita **tidak** bisa mengukurnya sebagai slippage order nyata (belum pernah ada order stop nyata) -
yang BISA diukur dari rekaman adalah **batas bawah**-nya: pada cadence kami, berapa sering level
dilewati *di antara dua rekaman*, dan seberapa jauh harga sudah lewat saat bar berikutnya terlihat.
Itu `i` dalam bentuk yang paling jujur: bukan angka realisasi, tapi angka kebutaan alat kami.

Dua sumber, dua pertanyaan berbeda:
  ⑨ `book-depth.jsonl`  -> bid/ask sungguhan di venue tempat kami bisa berdiri (perp).
  `watch-prices.jsonl`  -> harga ticker di substrate tempat kabar hidup (spot). Di sini `s` tidak
                           terukur, jadi yang dilaporkan hanya gap lewati level.

Yang TIDAK alat ini lakukan: mengklaim fill nyata. `i` dari data pasif adalah **batas bawah** -
saat order sungguhan datang, likuiditas yang tersisa biasanya lebih tipis daripada yang terekam
(`realized = 0,42 + 1,12 x predicted` di arXiv:2603.09164 - status dibaca-agen, belum diverifikasi).

Pakai:  python -X utf8 tools/fill_gap.py --self-test
       python -X utf8 tools/fill_gap.py --levels 25,50,100,200
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import flow_cluster_test as FC  # noqa: E402
import prices as PR  # noqa: E402

BUKU = os.path.join(ROOT, "universe", "book-depth.jsonl")
WP = os.path.join(ROOT, "universe", "watch-prices.jsonl")


def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * (len(xs) - 1)))]


def deret_buku(min_jeda=60):
    per = {}
    if os.path.exists(BUKU):
        for ln in io.open(BUKU, encoding="utf-8", errors="replace"):
            if not ln.startswith("{"):
                continue
            try:
                d = json.loads(ln)
            except ValueError:
                continue
            if d.get("k") != "bd" or not d.get("bids"):
                continue
            per.setdefault(d["sym"], []).append((int(d["detik"]), float(d["bids"][0][0]),
                                                 float(d["mid"]), float(d["spread_bps"])))
    for k in per:
        per[k].sort()
        per[k] = [x for x in per[k] if x[1] > 0]
    return {k: v for k, v in per.items() if len(v) >= 2}


def gap_lewati(deret, levels, satuan_bps=True):
    """Untuk tiap level di bawah harga kini: apakah bar berikutnya sudah DI BAWAH level itu?"""
    keluar = {}
    for x in levels:
        lompat, overshoot, jeda = 0, [], []
        for (t0, p0, mid0, _s0), (t1, p1, _m1, _s1) in zip(deret, deret[1:]):
            if t1 <= t0:
                continue
            lvl = mid0 * (1 - x / 10000.0) if satuan_bps else p0 * (1 - x / 10000.0)
            if p0 >= lvl and p1 < lvl:
                lompat += 1
                overshoot.append(10000.0 * (lvl - p1) / lvl)
                jeda.append(t1 - t0)
        n_pair = max(1, len(deret) - 1)
        keluar[x] = {"n_peluang": n_pair, "lompat": lompat,
                    "persen_lompat": round(100.0 * lompat / n_pair, 1),
                    "i_median_bps": round(FC.med(overshoot), 1) if overshoot else None,
                    "i_p90_bps": round(pct(overshoot, 0.9), 1) if overshoot else None,
                    "i_maks_bps": round(max(overshoot), 1) if overshoot else None,
                    "jeda_median_d": int(statistics.median(jeda)) if jeda else None}
    return keluar


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", default="25,50,100,200,400")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    lv = [int(x) for x in a.levels.split(",") if x.strip()]
    if a.self_test:
        return self_test()
    buku = deret_buku()
    if not buku:
        raise SystemExit("⑨ belum punya dua rekaman per simbol - ini BELUM TERUKUR, bukan 'i = 0'")
    wp = PR.load(WP, "wp")["rows"]
    print("E21 mengukur `i` sebagai gap-lewati-level | ⑨ %d simbol | ticker `wp` %d simbol | "
          "level uji %s bps" % (len(buku), len(wp), lv))
    print("\n   === ⑨ buku order venue (bid sungguhan) ===")
    print("   %-14s %6s %6s %12s %12s %12s %10s"
          % ("simbol", "level", "pasang", "% lompat", "i median", "i p90", "jeda d"))
    ringkas = {}
    for sym in sorted(buku, key=lambda s: -len(buku[s]))[:10]:
        g = gap_lewati(buku[sym], lv)
        for x in lv:
            r = g[x]
            ringkas.setdefault(x, []).append(r)
            print("   %-14s %6d %6d %11.1f%% %12s %12s %10s"
                  % (sym[:14], x, r["n_peluang"], r["persen_lompat"],
                     "-" if r["i_median_bps"] is None else "%+.1f" % r["i_median_bps"],
                     "-" if r["i_p90_bps"] is None else "%+.1f" % r["i_p90_bps"],
                     "-" if r["jeda_median_d"] is None else r["jeda_median_d"]))
    print("\n   === gabungan per level ===")
    print("   %-8s %10s %12s %14s %16s %12s" % ("level", "n pasang", "% lompat",
                                                 "median dr median", "p90 antar simbol", "maks"))
    print("   (kolom 'i' di bawah ini agregat LINTAS SIMBOL dari median tiap simbol - bukan"
          "\n    distribusi satu peristiwa; yang mendistribusikan kejadian per baris adalah"
          " baris per simbol)")
    per_level = {}
    for x in lv:
        rs = ringkas.get(x, [])
        n = sum(r["n_peluang"] for r in rs)
        lp = sum(r["lompat"] for r in rs)
        os_ = [v for r in rs for v in ([r["i_median_bps"]] if r["i_median_bps"] is not None else [])]
        p90 = [r["i_p90_bps"] for r in rs if r["i_p90_bps"] is not None]
        mx = [r["i_maks_bps"] for r in rs if r["i_maks_bps"] is not None]
        per_level[x] = {"n_pasangan": n, "persen_lompat": round(100.0 * lp / max(1, n), 1),
                        "i_median_dari_median_simbol": round(FC.med(os_), 1) if os_ else None,
                        "i_p90_antar_simbol": round(pct(p90, 0.9), 1) if p90 else None,
                        "i_maks_antar_simbol": round(max(mx), 1) if mx else None}
        e = per_level[x]
        print("   %-8d %10d %11.1f%% %14s %16s %12s"
              % (x, e["n_pasangan"], e["persen_lompat"],
                 "-" if e["i_median_dari_median_simbol"] is None
                 else "%+.1f" % e["i_median_dari_median_simbol"],
                 "-" if e["i_p90_antar_simbol"] is None
                 else "%+.1f" % e["i_p90_antar_simbol"],
                 "-" if e["i_maks_antar_simbol"] is None
                 else "%+.1f" % e["i_maks_antar_simbol"]))

    print("\n   === ticker `wp` (substrat kabar, harga saja, tanpa bid) ===")
    sample = [k for k, v in wp.items() if len(v) >= 8][:40]
    tot = {"n": 0, "lompat": 0}
    ov = []
    for tk in sample:
        ser = [(t, p) for t, p in wp[tk] if p > 0]
        for x in lv:
            g = gap_lewati([(t, p, p, 0.0) for t, p in ser], [x], satuan_bps=False)[x]
            tot["n"] += g["n_peluang"]
            tot["lompat"] += g["lompat"]
            if g["i_median_bps"] is not None:
                ov.append(g["i_median_bps"])
    print("   %d simbol, %d pasangan bar-berikutnya: **%0.1f %% melewati level di antara dua rekaman**;"
          % (len(sample), tot["n"], 100.0 * tot["lompat"] / max(1, tot["n"])))
    if ov:
        print("   gap saat terlihat: median %+0.1f bps | p90 %+0.1f | maks %+0.1f"
              % (FC.med(ov), pct(ov, 0.9), max(ov)))
    print("\nVONIS:")
    x0 = min(lv)
    e0 = per_level.get(x0, {})
    wpx = out_wp if False else None
    print("   - `i` BUKAN nol dan bukan konstanta. Pada level %d bps saja, %0.1f %% pasangan bar di ⑨"
          " sudah melewati level sebelum sempat terlihat." % (x0, e0.get("persen_lompat", 0.0)))
    print("   - artinya semua angka 'net of biaya' di repo ini masih kurang satu komponen, dan E17"
          "\n     tetap TIDAK BISA DINILAI dengan cadence ini (F-D49): bukan karena stop-nya salah,"
          " tapi karena\n     kami tidak pernah melihatnya tersentuh.")
    print("   - batas yang menempel: ini **batas bawah** dari slippage stop - order nyata memakan"
          "\n     likuiditas yang bahkan tidak sempat terekam; dan satu level diukur terhadap mid"
          " (⑨) / harga (wp), bukan terhadap order yang dikirim.")
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "levels_bps": lv, "buku_simbol": len(buku), "wp_simbol": len(sample),
           "buku_per_level": per_level,
           "wp_gabungan": {"n_pasangan": tot["n"], "persen_lompat":
                           round(100.0 * tot["lompat"] / max(1, tot["n"]), 1),
                           "i_median_lintasan_per_simbol": round(FC.med(ov), 1) if ov else None,
                           "i_p90_lintasan_per_simbol": round(pct(ov, 0.9), 1) if ov else None},
           "perintah": "python -X utf8 tools/fill_gap.py --levels %s" % a.levels}
    out["sha"] = "0x" + hashlib.sha256(json.dumps(out["buku_per_level"], sort_keys=True)
                                        .encode()).hexdigest()
    p = os.path.join(ROOT, "decisions", "fill-gap-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


def self_test():
    # harga: 100 -> 100 -> 90 (level 99 dilewati di antara dua rekaman -> lompat, overshoot ~1%)
    der = [(1000, 100.0, 100.0, 0.0), (1300, 100.0, 100.0, 0.0), (1600, 90.0, 95.0, 0.0),
           (1900, 99.9, 99.95, 0.0)]
    g = gap_lewati(der, [100.0])
    assert g[100.0]["lompat"] == 1, g
    # level = 100 x (1 - 100/1e4) = 99,00; bar berikutnya 90,00 -> gap = (99-90)/99 = 909,1 bps
    assert abs(g[100.0]["i_median_bps"] - 909.1) < 1, g
    assert g[100.0]["persen_lompat"] > 0, g
    # level yang tidak pernah dilewati tidak boleh menghasilkan angka
    g2 = gap_lewati([(1000, 100.0, 100.0, 0.0), (1300, 101.0, 101.0, 0.0)], [50.0])
    assert g2[50.0]["lompat"] == 0 and g2[50.0]["i_median_bps"] is None, g2
    # dan tanpa pasangan sama sekali -> None, BUKAN 0 bps
    assert gap_lewati([(1000, 100.0, 100.0, 0.0)], [50.0])[50.0]["i_median_bps"] is None
    print("self-test E21 OK: lompat terdeteksi, gap terukur, tidak-ada-lompat != nol")


if __name__ == "__main__":
    utama()

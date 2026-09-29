"""E8 diuji lawan kontrol yang benar: "keluar LEBIH AWAL kapan pun", bukan "keluar saat kerumunan".

Kenapa alat ini ada (29 Sep 2026, F-D39 sore): `tools/topk_test.py` melaporkan E8 - keluar saat
kerumunan beli datang - sebagai perbaikan **+116,5 bps (median) pada POSISI YANG SAMA**, 69 menolong
vs 45 merugikan. Itu dibandingkannya dengan MENAHAN sampai horison 30 menit. Tapi di kolam yang mean
pool-nya **-183,7 bps** dan medannya -123,8, ada penjelasan alternatif yang jauh lebih murah:
**"apa pun yang membuatmu keluar lebih awal akan terlihat lebih baik"**. Kalau begitu, yang terukur bukan
sinyal kerumunan, cuma kecepatan.

Karena itu kontrolnya sekarang: untuk tiap posisi yang sama, keluar di waktu **ACAK di jendela yang
sama** (200 undian per posisi, hanya dari titik `wp` yang benar-benar ada). Pertanyaannya bukan
"lebih baik dari menahan" - itu sudah dipastikan kalah oleh dekay pool - tapi
**"lebih baik dari keluar acak"**. Tiga angka yang harus dibaca bersama:

  delta_kerumunan  = (harga di saat kerumunan kedua - harga horison) / harga masuk
  delta_acak       = distribusi hal yang sama untuk waktu keluar acak dalam jendela yang sama
  vonis            = median/mean winso delta_kerumunan HARUS melewati persentil-97,5 delta_acak

Seperti E7, mean-nya dilaporkan sebagai MEDIAN dari banyak pengulangan (F-D39): satu undian
bukan hasil. Kalau ini gugur, satu-satunya perilaku yang tersisa di Fabius adalah rem (`jual_*`),
dan itu harus ditulis apa adanya - bukan dibungkus jadi "manajemen posisi".

Pakai:  python -X utf8 tools/exit_control.py --draws 200
       python -X utf8 tools/exit_control.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import flow_cluster_test as FC  # noqa: E402
import topk_test as TK  # noqa: E402

MIN = 60
WINS = 2000.0


def w(x):
    return max(-WINS, min(WINS, x))


def kumpulkan(hor):
    """Per posisi: (delta saat kerumunan, daftar indeks `wp` yang sah sebagai alternatif acak)."""
    txs, wp = TK.muat()
    out = []
    for tk, rows in txs.items():
        rows.sort(key=lambda r: r["t"])
        s = wp.get(tk)
        if not s:
            continue
        st = [x[0] for x in s]
        taken = -10 ** 15
        for r in [x for x in rows if x["buy"] and x["t"] <= TK.T_BATAS]:
            t = r["t"]
            if t - taken < hor * MIN:
                continue
            i = TK.bisect.bisect_right(st, t) - 1
            a = TK.bisect.bisect_left(st, t + (hor - 15) * MIN)
            b = TK.bisect.bisect_right(st, t + (hor + 15) * MIN)
            if i < 0 or a >= b:
                continue
            taken = t
            p0, p_hold = s[i][1], FC.med([s[j][1] for j in range(a, b)])
            if p0 <= 0:
                continue
            tc = TK.waktu_kluster(rows, t, hor)
            if not tc:
                continue
            j = TK.bisect.bisect_right(st, tc + 3 * MIN) - 1
            if j <= i:
                continue
            Sah = [k for k in range(i + 1, len(s))
                   if t + 5 * MIN <= s[k][0] <= t + hor * MIN]
            if len(Sah) < 3:
                continue
            out.append({"tk": tk, "t": t, "p0": p0, "p_hold": p_hold,
                        "d_kerumunan": (s[j][1] - p_hold) / p0 * 10000.0,
                        "indeks_acak": Sah})
    return out


def uji(pos, rnd, draws):
    """Dua lengan pada POSISI YANG SAMA: keluar saat kerumunan vs keluar di waktu acak."""
    ak = []
    for _ in range(draws):
        tot = 0.0
        for p in pos:
            k = rnd.choice(p["indeks_acak"])
            d = (TK.WP_CACHE[p["tk"]][k][1] - p["p_hold"]) / p["p0"] * 10000.0
            tot += w(d)
        ak.append(tot / len(pos))
    ak.sort()
    ker = [w(p["d_kerumunan"]) for p in pos]
    seeds = []
    for _ in range(40):
        tot = 0.0
        for p in pos:
            k = rnd.choice(p["indeks_acak"])
            tot += w((TK.WP_CACHE[p["tk"]][k][1] - p["p_hold"]) / p["p0"] * 10000.0)
        seeds.append(tot / len(pos))
    seeds.sort()
    return {"posisi": len(pos),
            "kerumunan_mean_winso": round(sum(ker) / len(ker), 1),
            "kerumunan_median_bps": round(FC.med(ker), 1),
            "kerumunan_p_menang": round(100.0 * sum(1 for x in ker if x > 1) / len(ker), 1),
            "acak_mean": round(sum(ak) / len(ak), 1),
            "acak_ci_atas": round(ak[int(0.975 * len(ak))], 1),
            "sebar_seed_acak": [round(seeds[0], 1), round(seeds[-1], 1)],
            "median_seed_acak": round(seeds[len(seeds) // 2], 1),
            "di_atas_acak": (sum(ker) / len(ker)) > ak[int(0.975 * len(ak))],
            "menang_vs_acak_per_posisi": None}


def menang_kalah(pos, rnd, draws):
    """Berapa sering kerumunan mengalahkan UNDIAN acak pada posisi yang sama (per posisi)."""
    lebih = kalah = sama = 0
    for p in pos:
        ds = []
        for _ in range(40):
            k = rnd.choice(p["indeks_acak"])
            ds.append((TK.WP_CACHE[p["tk"]][k][1] - p["p_hold"]) / p["p0"] * 10000.0)
        m = FC.med(ds)
        if p["d_kerumunan"] > m + 1:
            lebih += 1
        elif p["d_kerumunan"] < m - 1:
            kalah += 1
        else:
            sama += 1
    return {"menang": lebih, "kalah": kalah, "seri": sama,
            "p_tanda_eksak": FC.sign_p(lebih, lebih + kalah) if (lebih + kalah) else None}


def self_test():
    # posisi buatan: kerumunan terjadi SEBELUM puncak acak -> harus menolong
    TK.WP_CACHE = {"0xa": [(1000, 1.0), (1100, 1.0), (1200, 1.05), (1300, 1.05), (1400, 1.05),
                           (1500, 1.0), (1600, 1.0), (1700, 1.0), (1800, 1.0)]}
    p = {"tk": "0xa", "t": 1000, "p0": 1.0, "p_hold": 1.0, "d_kerumunan": 500.0,
         "indeks_acak": [4, 5, 6, 7, 8]}
    rnd = random.Random(7)
    u = uji([p] * 30, rnd, 200)
    assert u["di_atas_acak"] and u["kerumunan_mean_winso"] > u["acak_ci_atas"], u
    # posisi buatan II: kerumunan terjadi SESUDAH harga jatuh - acak harus lebih baik
    p2 = dict(p, d_kerumunan=-900.0)
    u2 = uji([p2] * 30, rnd, 200)
    assert not u2["di_atas_acak"], u2
    mk = menang_kalah([p] * 10 + [p2] * 10, rnd, 200)
    assert mk["menang"] == 10 and mk["kalah"] == 10, mk
    print("self-test keluar lawan acak OK: kerumunan awal menolong, kerumunan telat kalah, "
          "per-posisi tercatat")


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        TK.WP_CACHE = {}
        return self_test()
    TK.WP_CACHE = TK.wp_map() if hasattr(TK, "wp_map") else \
        __import__("prices").load(os.path.join(ROOT, "universe", "watch-prices.jsonl"), "wp")["rows"]
    pos = kumpulkan(a.horizon)
    print("E8 vs kontrol yang benar | %d posisi | horison %d m | harga `wp` | batas jelajah %s"
          % (len(pos), a.horizon, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(TK.T_BATAS))))
    if len(pos) < 20:
        raise SystemExit("posisi cuma %d - belum bisa memutus apa pun (ini BUKAN 'tidak ada efek')"
                         % len(pos))
    rnd = random.Random(20260929)
    u = uji(pos, rnd, a.draws)
    mk = menang_kalah(pos, rnd, a.draws)
    print("   kerumunan: mean winso %+0.1f | median %+0.1f | %s%% posisi di atas horison"
          % (u["kerumunan_mean_winso"], u["kerumunan_median_bps"], u["kerumunan_p_menang"]))
    print("   acak     : mean %+0.1f | CI atas %+0.1f | median seed %+0.1f | sebar seed %s"
          % (u["acak_mean"], u["acak_ci_atas"], u["median_seed_acak"], u["sebar_seed_acak"]))
    print("   per posisi vs undian acaknya sendiri: menang %d | kalah %d | seri %d | p=%s"
          % (mk["menang"], mk["kalah"], mk["seri"], mk["p_tanda_eksak"]))
    print("\nVONIS: %s" % ("keluar saat kerumunan MELEWATI keluar di waktu acak - aturan ini punya isi"
                           if u["di_atas_acak"] else
                           "TIDAK melewati keluar di waktu acak - yang diukur E8 adalah KELUAR LEBIH "
                           "AWAL, bukan sinyal kerumunan; aturan `exit_policy.py` harus diturunkan "
                           "statusnya jadi 'potong umur posisi', bukan 'baca pasar'"))
    out = {"dibuat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "posisi": len(pos), "horizon_menit": a.horizon, "draws": a.draws,
           "batas_jelajah_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(TK.T_BATAS)),
           "kerumunan_vs_acak": u, "per_posisi": mk}
    out["sha"] = "0x" + hashlib.sha256(json.dumps([u, mk], sort_keys=True).encode()).hexdigest()
    p = os.path.join(ROOT, "decisions", "exit-control-%s.json"
                     % time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    json.dump(out, io.open(p, "w", encoding="utf-8", newline="\n"), indent=1, sort_keys=True)
    print("artefak: decisions/%s" % os.path.basename(p))


if __name__ == "__main__":
    utama()

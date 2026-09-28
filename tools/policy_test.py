"""Tiga kebijakan, bukan dua - dan apa bedanya angka di antaranya.

Pertanyaan yang harus dijawab alat ini (pertanyaan builder, 28 Sep sore):
  "kalau Fabius cuma tahu kapan JANGAN masuk, apa bedanya dengan orang yang tidak berani masuk?"

Bedanya ada di tabel ini. Yang dibandingkan bukan "Fabius vs tidak trading", tapi tiga kebijakan
di universe yang sama, pada harga peristiwa, dengan ongkos round-trip 59 bps SUDAH dipotong:

  A  tidak pernah masuk                 -> 0,000 bps (ini "orang penakut")
  B  masuk SEMUA kejadian dari feed     -> baseline; ekornya yang menggendong harapan
  C  masuk semua KECUALI kerumunan jual -> yang kami BUKTIKAN bisa disaring
  D  C + keluar saat kerumunan beli     -> tidak bisa diukur dari tabel kejadian (butuh tick),
                                          jadi ditulis sebagai `TIDAK DIUJI`, bukan dikarang

Semua angka di bawah adalah rata-rata winsoresed (+-2.000 bps) per kejadian 30 menit, dengan
bootstrap 4.000 seed tetap, plus berapa kejadian yang dibuang kebijakan itu - karena rem yang tidak
membuang apa pun itu hiasan.

Pakai:  python -X utf8 tools/policy_test.py
       python -X utf8 tools/policy_test.py --horizon 60
"""
from __future__ import annotations

import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import mirror_test as MT  # noqa: E402  (SATU definisi kejadian + harga peristiwa)

WINS = 2000.0


def w(x):
    return min(max(x, -WINS), WINS)


def ringkas(xs, label, draws=4000):
    if not xs:
        return {"kebijakan": label, "n": 0}
    ms = [w(x) for x in xs]
    rnd = random.Random(20260928)
    n = len(ms)
    boots = []
    for _ in range(draws):
        s = [ms[rnd.randrange(n)] for _ in range(n)]
        boots.append(sum(s) / n)
    boots.sort()
    return {"kebijakan": label, "n": n, "share_kejadian": round(100.0 * n, 1),
            "mean_winso_bps": round(sum(ms) / n, 1),
            "ci_lo": round(boots[int(0.025 * draws)], 1),
            "ci_hi": round(boots[int(0.975 * draws)], 1),
            "median_bps": round(FC.med(xs), 1),
            "p_ge_500": round(100.0 * sum(1 for x in xs if x >= 500) / n, 1),
            "p_positif": round(100.0 * sum(1 for x in xs if x > 0) / n, 1),
            "total_bps": round(sum(ms), 0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--window", type=int, default=15)
    a = ap.parse_args()
    rt = costs.rt_cost()
    ev = MT.bangun(a.horizon, a.window)
    net = [e["net"] for e in ev]
    veto = [e for e in ev if not (e["jual_2"] or e["jual_bersih"])]
    print("harga peristiwa | horison %d m | ongkos %.1f bps (measured-own-venue) | %d kejadian "
          "pada %d token" % (a.horizon, rt, len(ev), len({e["tk"] for e in ev})))
    rows = [
        {"kebijakan": "A tidak pernah masuk", "n": 1, "mean_winso_bps": 0.0, "ci_lo": 0.0,
         "ci_hi": 0.0, "median_bps": 0.0, "p_ge_500": 0.0, "p_positif": 0.0, "total_bps": 0.0,
         "share_kejadian": 0.0},
        ringkas(net, "B masuk semua kejadian feed"),
        ringkas([e["net"] for e in veto], "C + veto kerumunan jual"),
        {"kebijakan": "D C + keluar saat kerumunan beli", "status": "TIDAK DIUJI - butuh harga per "
         "detik saat keluar, bukan horison tetap"},
    ]
    print("\n%-34s %6s %11s %-19s %9s %8s %9s" % ("kebijakan", "n", "mean winso", "CI 95 %",
                                                 "median", "P>=500", "total bps"))
    for r in rows:
        if r.get("status"):
            print("%-34s %s" % (r["kebijakan"], r["status"]))
            continue
        print("%-34s %6d %+11.1f [%+8.1f; %+9.1f] %+9.1f %7.1f%% %9.0f"
              % (r["kebijakan"], r["n"], r["mean_winso_bps"], r["ci_lo"], r["ci_hi"],
                 r["median_bps"], r["p_ge_500"], r["total_bps"]))
    b = rows[1]["mean_winso_bps"]
    c = rows[2]["mean_winso_bps"]
    print("\nC vs B : %+0.1f bps/kejadian (dibayar dengan %d kejadian yang dilewati, %.1f %% dari "
          "semua)" % (c - b, len(net) - len(veto), 100.0 * (len(net) - len(veto)) / len(net)))
    print("A vs B : %+0.1f bps/kejadian - ini harga 'tidak berani masuk', dan ia BUKAN nol yang "
          "netral" % (-b))
    print("\nYang TIDAK claimed alat ini: +B itu milik universe feed, bukan alpha kami; dan tanpa "
          "kedalaman/fill, mean winso tidak otomatis bisa diambil dengan ukuran posisi apa pun.")


if __name__ == "__main__":
    main()

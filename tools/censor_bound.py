"""Berapa banyak "+450,8 bps di kohort token muda" yang bertahan kalau yang MENGHILANG dihitung?

Alat sebelumnya (`technic_lab`, `sweep_kandidat`) MEMBUANG kejadian yang tidak punya baris harga di
jendela keluar. Untuk memecoin, "tidak ada transaksi lagi 30 menit kemudian" itu BUKAN ketiadaan
data - itu sering berarti tokennya mati. Membuangnya = menghitung hanya yang selamat.

Ini mengukur sisanya, bukan menebaknya:
  1. berapa kejadian punya baris keluar, per kohort (deret < 30 baris = "muda"),
  2. mean kohort kalau yang hilang diberi: (a) hanya yang teramati, (b) persentil-5 teramati,
     (c) -2.000 bps (winsor floor: "habis"), (d) break-even - berapa persen yang hilang harus
     habis supaya mean kohort muda jatuh ke nol.

Tidak ada klaim arah di sini. Ini alat untuk tahu apakah sebuah angka layak diperjuangkan atau
sudah mati sebelum lahir.
"""
from __future__ import annotations

import argparse
import bisect
import io
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import tx_prices as TP  # noqa: E402

MIN = 60
WINS = 2000.0


def w(x):
    return max(-WINS, min(WINS, x))


def bangun(hor, jendela_min=15):
    txs = {}
    for ln in io.open(os.path.join(ROOT, "universe", "wallet-flow.jsonl"), encoding="utf-8",
                      errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        d = json.loads(ln)
        if d.get("k") not in ("tx", "txc"):
            continue
        tk = str(d.get("tk") or "").lower()
        t, p = int(d.get("t") or 0), float(d.get("p") or 0)
        if tk and t and p > 0:
            txs.setdefault(tk, []).append({"t": t, "buy": bool(d.get("b"))})
    ser = TP.load_tx_series()["rows"]
    muda, dewasa = [], []
    for tk, rows in txs.items():
        ss = ser.get(tk) or []
        st = [x[0] for x in ss]
        taken = -10 ** 15
        for r in [x for x in rows if x["buy"]]:
            t = r["t"]
            if t - taken < hor * MIN:
                continue
            i = bisect.bisect_right(st, t) - 1
            if i < 0:
                continue
            p0 = ss[i][1]
            a = bisect.bisect_left(st, t + (hor - jendela_min) * MIN)
            b = bisect.bisect_right(st, t + (hor + jendela_min) * MIN)
            ex = [ss[j][1] for j in range(a, b)]
            taken = t
            cukup = len(ss[:i + 1]) >= 30
            net = (round(10000.0 * (FC.med(ex) - p0) / p0 - costs.rt_cost(), 1) if ex else None)
            rec = {"tk": tk, "t": t, "net": net, "ada_keluar": bool(ex), "panjun": len(ss)}
            (dewasa if cukup else muda).append(rec)
    return muda, dewasa


def laporan(nama, xs):
    ada = [e["net"] for e in xs if e["net"] is not None]
    hilang = [e for e in xs if e["net"] is None]
    if not ada:
        print("%-22s tidak ada yang teramati" % nama)
        return
    v = [w(x) for x in ada]
    mean = sum(v) / len(v)
    urut = sorted(v)
    p05 = urut[int(0.05 * (len(urut) - 1))]
    rnd = random.Random(20260928)
    n = len(v)
    bm = sorted(sum([v[rnd.randrange(n)] for _ in range(n)]) / n for _ in range(2000))
    lo, hi = bm[int(0.05 * 2000)], bm[int(0.95 * 2000)]
    m_hilang = len(hilang)
    tot = n + m_hilang
    mean_p05 = (sum(v) + m_hilang * p05) / tot
    mean_buruk = (sum(v) + m_hilang * (-WINS)) / tot
    # break-even: berapa dari yang hilang harus -2.000 supaya mean jatuh ke 0
    butuh = 0
    for k in range(tot + 1):
        if (sum(v) + k * (-WINS) + (m_hilang - k) * p05) / tot <= 0:
            butuh = k
            break
    print("%-22s teramati %4d (%5.1f %%) | hilang %4d (%5.1f %%)" % (nama, n, 100.0 * n / tot,
                                                                      m_hilang, 100.0 * m_hilang / tot))
    print("   mean hanya-yang-teramati : %+8.1f bps  CI90 [%+.1f; %+.1f]  P>=500 %.1f %%"
          % (mean, lo, hi, 100.0 * sum(1 for x in v if x >= 500) / n))
    print("   mean + yang hilang=-p05  : %+8.1f bps   (persentil 5 teramati = %+.1f)"
          % (mean_p05, p05))
    print("   mean + yang hilang=-2000 : %+8.1f bps   (skenario 'habis semua')" % mean_buruk)
    if m_hilang:
        print("   break-even           : %d dari %d yang hilang harus dianggap -2.000 bps supaya "
              "mean jadi 0" % (butuh, m_hilang))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--horizon", type=int, default=30)
    a = ap.parse_args()
    rt = costs.rt_cost()
    muda, dewasa = bangun(a.horizon)
    print("horison %d m | harga peristiwa | ongkos %.1f bps dipotong | winsor +-%.0f"
          % (a.horizon, rt, WINS))
    laporan("KOHORT MUDA (deret<30)", muda)
    print()
    laporan("KOHORT MATANG (>=30)", dewasa)
    print("\nYang TIDAK diklaim alat ini: bahwa mean yang teramati itu salah. Yang diklaim: kalau"
          "\nseperempat sampai separuh kejadian tidak punya harga keluar, angka manapun yang"
          "\ndipakai untuk menjual 'kapan boleh masuk' wajib menyebut berapa yang hilang itu.")


if __name__ == "__main__":
    main()

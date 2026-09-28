"""Penyortiran TANPA budget harian: kuintil fitur pada semua kejadian yang boleh (n ~1.014).

`tools/select_test.py` membentur tembok daya: 15 posisi tidak bisa memutuskan apa pun. Tapi budget
5 posisi/hari adalah batas EKSEKUSI kontrak, bukan batas pengukuran. Di sini setiap kejadian yang
lolos gerbang diperlakukan sama dan dikelompokkan ke KUINTIL fitur - ~200 kejadian per kuintil,
cukup untuk melihat kemiringan yang tidak kelihatan di 15 posisi.

Ini pertanyaan "kapan boleh masuk" dalam bentuk yang masih bisa dijawab sebelum 30 Sep:
apakah ada fitur siklus hidup pool yang menaikkan P(net >= +500 bps) atau harapan winso ketika
kita naik dari kuintil terbawah ke teratas?

Aturan yang tidak tawar-menawar:
  - harga = PERISTIWA (tx.t, tx.p), bukan `px` beku - lihat F-D30
  - fitur hanya dari snapshot dengan `epoch <= t` (point-in-time)
  - kerumunan jual sudah diveto di gerbang, jadi yang diuji adalah sisa dunia yang boleh dibeli
  - tren kuintil diuji dengan Mann-Whitney (teratas vs terbawah) + BH alpha 0,10, dan arah
    dilaporkan apa adanya - kalau turun, itu pun jawaban
"""
from __future__ import annotations

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import costs  # noqa: E402
import flow_cluster_test as FC  # noqa: E402
import mirror_test as MT  # noqa: E402

WINS = 2000.0
FITUR = ["volume_24h", "liquidity", "age_sec", "price_change_24h", "smart_degen_count",
         "sniper_count", "holder_count", "top_10_holder_rate", "lock_percent", "bundler_rate",
         "usd_b_jendela", "n_maker_jendela"]
Q = 5


def w(x):
    return min(max(x, -WINS), WINS)


def snapshots():
    out = []
    for ln in io.open(os.path.join(ROOT, "universe", "bsc-universe.jsonl"), encoding="utf-8",
                      errors="replace"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        d = json.loads(ln)
        ep = int(d.get("epoch") or 0)
        if not ep:
            continue
        m = {}
        for r in d.get("rows") or []:
            tk = str(r.get("base_token") or "").lower()
            if tk:
                m[tk] = {k: r.get(k) for k in FITUR[:10]}
        out.append((ep, m))
    out.sort()
    return out


def ambil(snap, tk, t):
    pilih = None
    for ep, m in snap:
        if ep > t:
            break
        if tk in m:
            pilih = m[tk]
    return pilih


def ekor_hipergeo(a_pos, a_n, b_pos, b_n):
    """p SATU ARAH: P(X >= a_pos) bila a_pos sukses itu sebenarnya terdistribusi acak di kedua grup.

    Hipergeometrik dengan N=a_n+b_n, K=a_pos+b_pos, n=a_n. Eksak lewat lgamma (tanpa `math.comb`
    yang meluap pada n ribuan), dan arahnya eksplisit: kecil = kuintil teratas memang lebih banyak
    jackpot; besar = tidak (termasuk kalau dia lebih BURUK - yang pada fungsi dua-arah terbaca
    sebagai p ~ 0).
    """
    from math import exp, lgamma

    def lchoose(n, k):
        if k < 0 or k > n:
            return float("-inf")
        return lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1)

    N, K, n = a_n + b_n, a_pos + b_pos, a_n
    if N <= 0 or K <= 0 or n <= 0 or K >= N:
        return None
    lo, hi = max(0, K - (N - n)), min(n, K)
    den = lchoose(N, K)
    pk = [exp(lchoose(n, k) + lchoose(N - n, K - k) - den) for k in range(lo, hi + 1)]
    if not pk or sum(pk) <= 0:
        return None
    return min(1.0, sum(pk[a_pos - lo:]) if a_pos >= lo else 1.0)


def main():
    rt = costs.rt_cost()
    ev = MT.bangun(30, 15)
    boleh = [e for e in ev if not (e["jual_2"] or e["jual_bersih"])]
    snap = snapshots()
    berfitur, tanpa = [], 0
    for e in boleh:
        f = ambil(snap, e["tk"], e["t"])
        if not f:
            tanpa += 1
            continue
        e["f"] = dict(f)
        e["f"]["usd_b_jendela"] = e.get("usd_b")
        e["f"]["n_maker_jendela"] = e.get("n_maker")
        berfitur.append(e)
    print("harga peristiwa | ongkos %.1f bps | kejadian %d | lolos gerbang %d | dengan fitur "
          "point-in-time %d (%.1f %%) | tanpa snapshot %d"
          % (rt, len(ev), len(boleh), len(berfitur), 100.0 * len(berfitur) / max(len(boleh), 1),
             tanpa))
    net = [e["net"] for e in berfitur]
    base500 = sum(1 for x in net if x >= 500)
    print("baseline (hanya yang boleh + berfitur): mean winso %+0.1f | P>=+500 %.1f %% | median %+0.1f"
          % (sum(w(x) for x in net) / len(net), 100.0 * base500 / len(net), FC.med(net)))
    print("\n%-22s %s" % ("fitur", " ".join("%9s" % ("Q%d" % (i + 1)) for i in range(Q))
                          + " | kemiringan MW (teratas vs terbawah)      BH"))
    hasil = []
    for feat in FITUR:
        xs = [(e["f"].get(feat), e["net"]) for e in berfitur
              if isinstance(e["f"].get(feat), (int, float))]
        if len(xs) < Q * 20:
            print("%-22s SAMPEL < %d per kuintil - tidak diuji (%d)" % (feat, Q * 20, len(xs)))
            continue
        xs.sort(key=lambda p: p[0])
        bagian = [xs[i * len(xs) // Q:(i + 1) * len(xs) // Q] for i in range(Q)]
        sel = []
        for b in bagian:
            nn = [x[1] for x in b]
            sel.append("%+9.1f" % (sum(w(x) for x in nn) / len(nn)))
        bawah = [x[1] for x in bagian[0]]
        atas = [x[1] for x in bagian[-1]]
        pmw = FC.mann_whitney_p([w(x) for x in atas], [w(x) for x in bawah])
        pa5 = sum(1 for x in atas if x >= 500) / max(len(atas), 1)
        pb5 = sum(1 for x in bawah if x >= 500) / max(len(bawah), 1)
        # SATU ARAH "kuintil teratas lebih banyak jackpot". `flow_cluster_test.fisher_p` tidak bisa
        # dipakai di sini: ia membandingkan probabilitas tabel dengan yang TERAMATI (ekor dua-arah
        # gaya Fisher), jadi kuintil yang justru JAUH LEBIH BURUK juga mengembalikan p ~ 0. Terjadi
        # pada percobaan pertama alat ini dan ketahuan karena angkanya menentang arah kolomnya.
        pf = ekor_hipergeo(sum(1 for x in atas if x >= 500), len(atas),
                           sum(1 for x in bawah if x >= 500), len(bawah))
        hasil.append((feat, pmw, pf, pa5, pb5))
        print("%-22s %s | Q%d %+0.1f vs Q1 %+0.1f  mean-winso MW p=%-7s | P>=500 %.1f%% vs %.1f%% "
              "Fisher p=%-7s %s"
              % (feat, " ".join(sel), Q, sum(w(x) for x in atas) / len(atas),
                 sum(w(x) for x in bawah) / len(bawah),
                 ("%.4f" % pmw) if pmw is not None else "-", 100.0 * pa5, 100.0 * pb5,
                 ("%.4f" % pf) if pf is not None else "-",
                 "n=%d/%d" % (len(atas), len(bawah))))
    lulus_mw = FC.bh([(f, pmw_) for f, pmw_, pfi, a, b in hasil if pmw_ is not None])
    lulus_fi = FC.bh([(f, pfi) for f, pmw_, pfi, a, b in hasil if pfi is not None])
    print("\nBH alpha 0,10 - kuintil teratas mengalahkan terbawah:")
    print("   pada harapan winso (Mann-Whitney): %s" % (sorted(lulus_mw) or "TIDAK ADA"))
    print("   pada P(net >= +500 bps) (Fisher)  : %s" % (sorted(lulus_fi) or "TIDAK ADA"))
    print("\nSetelah ini, kalau kedua baris kosong: tidak ada fitur siklus hidup pool yang kami punya"
          "\nmenaikan 'kapan boleh masuk' - pada n yang cukup untuk memutuskannya, bukan pada 15 "
          "posisi.")


if __name__ == "__main__":
    main()

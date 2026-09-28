"""Ukuran yang BENAR untuk payoff miring ke kanan: probabilitas masuk ekor, bukan median.

Kesalahan strukturalku (terlihat 28 Sep sore): semua angka yang kutulis memakai MEDIAN. Untuk
memecoin spot, distribusi net itu sangat miring ke kanan - pada dataset ini:
    p50 -58,9 | p75 +1.368 | p90 +8.854 | p99 +105.639 (bps)
median yang negatif tidak berarti harapan negatif, dan median yang positif tidak berarti bisa
diambil: yang menentukan apakah sebuah kondisi LAYAK DIBUKA adalah probabilitas masuk ekor atas,
dengan outsiz yang winso (dibatasi) supaya satu pool $6k yang naik 10x tidak menyamar jadi strategi.

Ini bukan mengganti metode karena hasilnya tidak disukai - ini memakai ukuran yang cocok ke bentuk
datanya, dan FD5 di lapisan pengetahuan kami sendiri sudah bilang begitu ("Expectancy Bukan Win Rate").

Yang dilaporkan per aspek:
  - P(net >= +500 bps) dan P(net >= p75) vs baseline, Fisher eksak satu arah + BH alpha 0,10
  - mean winsoresed +-2.000 bps dengan bootstrap 4.000 (harapan yang bisa diambil dengan posisi kecil)
  - n, supaya SAMPLE KECIL terlihat, bukan tersembunyi
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import flow_cluster_test as FC  # noqa: E402
import mirror_test as U  # noqa: E402  (satu definisi kejadian & harga peristiwa)

MIN = 60
ev = U.bangun(30, 15)
net = [e["net"] for e in ev]
q = sorted(net)
p75 = q[int(0.75 * (len(q) - 1))]
WINS = 2000.0
print("n=%d kejadian | baseline P(>=+500bps)=%.1f %% | P(>=%.0f)=%.1f %% | mean winso %+0.1f bps"
      % (len(ev), 100.0 * sum(1 for x in net if x >= 500) / len(net), p75,
         100.0 * sum(1 for x in net if x >= p75) / len(net),
         FC.med([min(max(x, -WINS), WINS) for x in net]) * 0 +
         sum(min(max(x, -WINS), WINS) for x in net) / len(net)))


def boot_mean(xs, draws=4000):
    import random
    rnd = random.Random(20260928)
    n = len(xs)
    out = []
    for _ in range(draws):
        out.append(sum(xs[rnd.randrange(n)] for _ in range(n)) / n)
    out.sort()
    return out[int(0.025 * draws)], out[int(0.975 * draws)]


BASE500 = sum(1 for x in net if x >= 500)
BASEP75 = sum(1 for x in net if x >= p75)
print("\n%-20s %6s %8s %-19s %8s %-19s %8s %8s"
      % ("aspek", "n", "P>=500", "Fisher vs baseline", "p", "mean winso", "CI 95 %", "BH"))
rows = []
for f in U.ASPEK:
    sub = [e for e in ev if e[f]]
    if len(sub) < 20:
        print("%-20s %6d  SAMPEL KECIL (<20) - tidak diuji" % (f, len(sub)))
        continue
    xs = [e["net"] for e in sub]
    a5 = sum(1 for x in xs if x >= 500)
    p5 = FC.fisher_p(a5, len(xs), BASE500, len(net))
    ap = sum(1 for x in xs if x >= p75)
    pp = FC.fisher_p(ap, len(xs), BASEP75, len(net))
    w = [min(max(x, -WINS), WINS) for x in xs]
    m = sum(w) / len(w)
    lo, hi = boot_mean(w)
    rows.append((f, p5, pp))
    print("%-20s %6d %7.1f %%  P>=500: %5.1f%% p=%-7s | P>=p75: %5.1f%% p=%-7s | %+8.1f [%+7.0f; %+8.0f]"
          % (f, len(xs), 100.0 * a5 / len(xs), 100.0 * a5 / len(xs),
             ("%.4f" % p5) if p5 is not None else "-", 100.0 * ap / len(xs),
             ("%.4f" % pp) if pp is not None else "-", m, lo, hi))

lulus5 = FC.bh([(f, p) for f, p, q2 in rows if p is not None])
lulus75 = FC.bh([(f, q2) for f, p, q2 in rows if q2 is not None])
print("\nBH alpha 0,10 - P(>=+500 bps) di atas baseline: %s" % (sorted(lulus5) or "TIDAK ADA"))
print("BH alpha 0,10 - P(>=p75) di atas baseline      : %s" % (sorted(lulus75) or "TIDAK ADA"))

# gabungan aspek yang sama-sama menaikkan ekor
naik = sorted(lulus5 | lulus75)
if len(naik) >= 2:
    for i in range(len(naik)):
        for j in range(i + 1, len(naik)):
            a, b = naik[i], naik[j]
            sub = [e["net"] for e in ev if e[a] and e[b]]
            if len(sub) >= 20:
                print("  %s DAN %s: n=%d P>=500=%.1f%% mean winso=%+.1f"
                      % (a, b, len(sub), 100.0 * sum(1 for x in sub if x >= 500) / len(sub),
                         sum(min(max(x, -WINS), WINS) for x in sub) / len(sub)))
else:
    print("\n(tidak ada sepasang aspek pun yang menaikkan ekor di atas baseline -> tidak ada yang "
          "digabungkan)")

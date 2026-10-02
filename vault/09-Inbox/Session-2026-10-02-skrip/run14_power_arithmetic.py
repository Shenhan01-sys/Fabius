# EKSPLORATIF - sesi 2 Okt 2026 (lihat vault/08-Backlog/08 - Riset Optimasi Ambang.md §1).
# Aritmetika, bukan simulasi dan bukan klaim: batas bawah seberapa kecil edge yang MUNGKIN terdeteksi dari riwayat sependek ini. Hanya stdlib.
"""Daya pendekatan uji Sharpe satu-sisi pada riwayat T tahun (data harian, hasil iid, satu uji saja - tanpa gerbang lain).

    python -X utf8 run14_power_arithmetic.py

Model: Sharpe tahunan sebenarnya s; taksiran S ~ Normal(s, (1 + s^2/2)/T) (Lo 2002, hasil iid normal). Ambang uji "persentil-5 bootstrap > 0"
dalam pendekatan: S > 1,645/sqrt(T) (galat baku di bawah nol = 1/sqrt(T)). Daya = P(S > ambang | s).
Ini PLAFON, bukan perkiraan: gerbang lain (G4-G10, K1-K3) hanya dapat MENURUNKAN daya; ekor tebal dan autokorelasi menambah galat.
"""
import math
from statistics import NormalDist

nd = NormalDist()
Z95, Z80 = nd.inv_cdf(0.95), nd.inv_cdf(0.80)
YEARS = (2.0, 3.0, 3.8, 5.0, 6.7)       # 3,0 th = 1095 hari = syarat minimum G2; 3,8 th = 1400 hari = dunia sintetik run13; 6,7 th = 2434 hari = riwayat B1 nyata (G2)
SHARPES = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0)


def power(s: float, t: float) -> float:
    return 1.0 - nd.cdf((Z95 - s * math.sqrt(t)) / math.sqrt(1.0 + s * s / 2.0))


def years_for_power(s: float, target_z: float = Z80) -> float:
    return ((Z95 + target_z * math.sqrt(1.0 + s * s / 2.0)) / s) ** 2


print("daya (%) uji satu-sisi 5% pada Sharpe tahunan sebenarnya s, riwayat T tahun")
print("s \\ T   " + "  ".join(f"{t:>5.1f}" for t in YEARS))
for s in SHARPES:
    print(f"{s:>5.2f}   " + "  ".join(f"{100 * power(s, t):>5.1f}" for t in YEARS))
print("\ntahun riwayat yang dibutuhkan untuk daya 80%:")
for s in SHARPES:
    print(f"  s = {s:>4.2f} -> {years_for_power(s):>6.1f} tahun")
print("\nPembacaan: plafon. Edge sedang (s <= 0,5) tidak mungkin dipisahkan dari noise dengan riwayat beberapa tahun; ini sebabnya data maju (shadow) dibutuhkan.")

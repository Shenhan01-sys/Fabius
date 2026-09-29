"""Dua fungsi, satu data: membuktikan bahwa `p` dari alat kami sendiri harus diuji sebelum dikutip.

Kenapa alat ini ada (29 Sep 2026, F-D37): `mann_whitney_p` kami menyusun peringkat dengan
`sorted(a) + sorted(b)` - dua kelompok terurut yang ditempel, bukan ditempel lalu diurut - dan
menjumlah ties sebagai rata-rata peringkat x ukuran kelompok. Pada dua kelompok yang jelas terpisah
(A = +120..+144, B = -300..-324) alat lama mengembalikan **p = 1,0** (arah terbalik). Angka itu sempat
masuk vault sebagai "lolos dua uji berbeda" untuk `lock_percent`.

Cara membungkam perdebatan bukan dengan alasan, tapi dengan menjalankan DATA YANG SAMA lewat kedua
fungsi dan mencetak bedanya. Versi lama fungsi ini sengaja disalin di sini (tidak diimpor dari mana
pun) supaya alat ini tetap membuktikan sejarah, bukan ikut memperbaiki diam-diam.

Pakai:  python -X utf8 tools/instrument_proof.py
       python -X utf8 tools/instrument_proof.py --kuincian   # hanya tabel kasus
"""
from __future__ import annotations

import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import flow_cluster_test as FC  # noqa: E402

WINS = 2000.0


def lama(a, b):
    """Salinan persis `mann_whitney_p` sebelum perbaikan 29 Sep - jangan "dibersihkan"."""
    na, nb = len(a), len(b)
    if na < 5 or nb < 5:
        return None
    allv = sorted((x, 0) for x in a) + sorted((x, 1) for x in b)
    ranks, i, tie_groups = {}, 0, []
    vals = [v for v, _ in allv]
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[j + 1] == vals[i]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks.setdefault(vals[k], []).append(avg)
        if j > i:
            tie_groups.append(j - i + 1)
        i = j + 1
    ra = sum(sum(ranks[v]) for v in a)
    mu = na * (na + nb + 1) / 2.0
    n = na + nb
    tie_corr = sum(t ** 3 - t for t in tie_groups) / 12.0
    var = na * nb / 12.0 * ((n + 1) - tie_corr / (n * (n - 1.0)))
    if var <= 0:
        return None
    z = (ra - mu) / math.sqrt(var)
    return 0.5 * math.erfc(z / math.sqrt(2.0)) if z > 0 else 1.0 - 0.5 * math.erfc(-z / math.sqrt(2.0))


KASUS = [
    ("A terpisah MENANG telak (+120..+144 vs -300..-324)",
     [120.0 + i for i in range(25)], [-300.0 - i for i in range(25)]),
    ("A terpisah KALAH (posisi dibalik)",
     [-300.0 - i for i in range(25)], [120.0 + i for i in range(25)]),
    ("A lebih tinggi tapi TUMPANG TINDIH ringan",
     [float(x) for x in range(25)], [float(x) + 12 for x in range(25)]),
    ("TIES penuh (20x1,0 + 5x2,0 vs 20x1,0 + 5x0,0)",
     [1.0] * 20 + [2.0] * 5, [1.0] * 20 + [0.0] * 5),
    ("Dua distribusi IDENTIK (tidak boleh ada pemenang)",
     [float(x) for x in range(20)] * 2, [float(x) for x in range(20)] * 2),
]


def tabel():
    print("%-52s %12s %12s %s" % ("kasus", "p LAMA", "p BENAR", "beda arah?"))
    salah = 0
    for nm, a, b in KASUS:
        pl, pb = lama(a, b), FC.mann_whitney_p(a, b)
        arah = ""
        if pl is not None and pb is not None:
            if (pl < 0.05) != (pb < 0.05):
                arah = "YA - vonis berbeda"
                salah += 1
            elif pl > 0.9 and pb < 0.05:
                arah = "YA - terbalik"
                salah += 1
        print("%-52s %12s %12s %s" % (nm[:52], "%.6f" % pl if pl is not None else "-",
                                      "%.6f" % pb if pb is not None else "-", arah))
    print("\n%d dari %d kasus: fungsi lama mengubah VONIS, bukan cuma angka (data yang sama, "
          "satu-satunya perbedaan = fungsi)." % (salah, len(KASUS)))
    return salah


def utama():
    ap = argparse.ArgumentParser()
    ap.add_argument("--penuh", action="store_true",
                    help="jalankan quintile_test dengan fungsi LAMA lalu bandingkan kolom MW "
                         "artefak terbaru (lama: 4000 bootstrap x 12 fitur)")
    a = ap.parse_args()
    salah = tabel()
    FC.mw_self_test()
    if a.penuh:
        import io
        import random
        import quintile_test as QT
        baru = FC.mann_whitney_p
        buf = io.StringIO()
        out, sys.stdout = sys.stdout, buf
        FC.mann_whitney_p = lama
        try:
            QT.main()
        finally:
            sys.stdout = out
            FC.mann_whitney_p = baru
        teks = buf.getvalue()
        for baris in teks.splitlines():
            if re.search(r"lock_percent|n_maker_jendela|holder_count", baris):
                print("LAMA>", " ".join(baris.split())[:170])
    print("\nKesimpulan yang dipakai vault: setiap `p` dari fungsi ini yang dikutip sebelum 29 Sep "
          "05:00Z dianggap BELUM terverifikasi sampai alatnya dijalankan lagi.")


if __name__ == "__main__":
    utama()

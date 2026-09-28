"""Sekali-jalan: naikkan tingkat bukti yang kini punya alamat literatur (28 Sep).

Enam rujukan dipanggil dan metadatenya dicocokkan sendiri hari ini (daftar lengkap di
[[Sumber dan Jangkauan]]). Yang berubah: kalimat "dipakai luas, tidak kami uji" (`T1`) di titik
yang ternyata punya uji terkenal menjadi "`T2` - ada literatur, tidak kami reproduksi" + alamatnya.

Yang TIDAK naik: tidak ada satu pun `T3` baru. `T3` butuh run kita sendiri, dan satu-satunya run
baru hari ini (carry) justru NEGATIF. Jadi upgrade ini memperbaiki atribusi, bukan membuat metode
apa pun jadi terbukti.

Assert per aturan: fragmen harus ada persis satu kali di satu berkas, tidak lebih tidak kurang.

    python -X utf8 vault/scripts/patch_reference_levels.py          # jalankan
    python -X utf8 vault/scripts/patch_reference_levels.py --check   # laporkan
"""
import io
import os
import sys

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TK = os.path.join(VAULT, "TradingKnowledge")
CHECK_ONLY = "--check" in sys.argv

RULES = [
    ("05-Quant/QT4 - Overfitting dan Validasi.md",
     "`T1` untuk konsep N_eff / DSR / PBO (nama dari literatur, tidak kami reproduksi) · `T3` untuk",
     "`T2` untuk konsep N_eff / DSR / PBO - ada literaturnya dan metadatenya kami cocokkan 28 Sep: "
     "Bailey & L\u00f3pez de Prado, *The Deflated Sharpe Ratio*, SSRN `10.2139/ssrn.2460551` "
     "([[Sumber dan Jangkauan]] #3); tidak kami reproduksi \u00b7 `T3` untuk"),
    ("05-Quant/QT6 - Funding dan Basis Arbitrage.md",
     "`T1` untuk kerangka cash-and-carry/basis (pengetahuan standar pasar) \u00b7 **belum diuji sebagai",
     "`T2` untuk kerangka cash-and-carry/basis di crypto: Schmeling/Schrimpf/Todorov, *Crypto Carry*, "
     "BIS WP 1087 (2023) - metadatanya dan abstraknya dibaca 28 Sep ([[Sumber dan Jangkauan]] #1); "
     "angka mereka (basis >10%/tahun) BUKAN angka kita (funding kita 1,3\u20132,2 bps/hari, "
     "[[06-Results/08 - Carry Study]] \u00a7C) \u00b7 **belum teruji sebagai"),
    ("03-Sinyal/Turunan/U2 - Funding Rate dan Basis.md",
     "`T0` untuk \"funding ekstrem\nmemprediksi reversal\"",
     "`T2` untuk \"carry tinggi memprediksi penurunan\" sebagai klaim literatur (*Crypto Carry*, BIS "
     "WP 1087, [[Sumber dan Jangkauan]] #1) \u00b7 `T0` untuk funding ekstrem sebagai pemicu reversal "
     "per-bar"),
    ("03-Sinyal/Turunan/U2 - Funding Rate dan Basis.md",
     "harga, dan hasilnya negatif 12/12 (\u00a7F) \u2014 gerbang funding tidak ikut diuji karena historinya tidak\nada. Status gerbang carry: **ADA tapi belum diuji** \u2014 bukan lolos, bukan gagal: belum.",
     "harga, dan hasilnya negatif 12/12 (\u00a7F). Gerbang funding sudah ikut diuji 28 Sep begitu "
     "historinya punya kita: **0 dari 2.963** settlement melewatinya, dan **0 dari 12** uji arah 24 "
     "jam lolos BH \u2192 [[06-Results/08 - Carry Study]]. Status gerbang carry: diuji, belum "
     "memberi apa pun \u2014 dan ambangnya sendiri mungkin tidak akan pernah menyala di aset ini."),
    ("03-Sinyal/Narasi/M2 - Sentimen Sosial dan Ekstraksi LLM.md",
     "`T0` untuk klaim vendor bahwa skor sentimen memprediksi harga \u00b7 `T1` untuk pola kerja",
     "`T0` untuk klaim vendor bahwa skor sentimen memprediksi harga \u00b7 `T2` untuk klaim \"mood "
     "sosial punya isi prediktif\" di pasar lain: Bollen/Mao/Zeng, *Twitter mood predicts the stock "
     "market*, arXiv `1010.3003` (J. Computational Science 2011) \u2014metadata dicocokkan 28 Sep, "
     "efeknya kecil dan tidak pernah kami replikasi ([[Sumber dan Jangkauan]] #2) \u00b7 `T1` untuk pola kerja"),
    ("02-Fondasi/FD6 - Ukuran Posisi.md",
     "`T1` untuk fixed fractional / Kelly fraksional /\nvol targeting sebagai kerangka",
     "`T2` untuk fixed fractional / Kelly fraksional / vol targeting sebagai kerangka - ada "
     "literaturnya dan metadatanya dicocokkan 28 Sep: Carta & Conversano 2020, DOI "
     "`10.3389/fams.2020.577050`; MacLean/Thorp/Zhao/Ziemba 2011, DOI `10.3905/jpm.2011.37.4.096`; "
     "Busseti/Ryu/Boyd 2016, DOI `10.3905/joi.2016.25.3.118` ([[Sumber dan Jangkauan]] #5-6)"),
    ("03-Sinyal/Struktur/S2 - Chart Patterns.md",
     "`T2` untuk klaim \"pernah diukur secara algoritmik di pasar lain\" (ada literatur, tidak kami\nreproduksi, tidak kami kutip angkanya)",
     "`T2` untuk klaim \"pernah diukur secara algoritmik di pasar lain\" - alamatnya: Park & Irwin, "
     "*What do we know about the profitability of technical analysis?*, J. Economic Surveys 2007, DOI "
     "`10.1111/j.1467-6419.2007.00519.x`, dan kawannya yang bebas-snooping SSRN `10.2139/ssrn.722264` "
     "([[Sumber dan Jangkauan]] #4); metadatanya kami cocokkan, kesimpulannya tidak kami kutip "
     "kata-per-kata dan tidak kami reproduksi"),
    ("03-Sinyal/Indikator/I1 - Moving Average.md",
     "`T1` untuk MA sebagai peringkas tren dan filter rezim\n(dipakai luas, tidak kami uji dalam peran itu)",
     "`T2` untuk MA sebagai peringkas tren dan filter rezim - disurvei di literatur (Park & Irwin 2007, "
     "DOI `10.1111/j.1467-6419.2007.00519.x`, [[Sumber dan Jangkauan]] #4) dan tidak kami reproduksi "
     "dalam peran itu"),
]


def main():
    done = bad = 0
    for rel, old, new in RULES:
        p = os.path.join(TK, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            print("TIDAK ADA:", rel)
            bad += 1
            continue
        t = io.open(p, encoding="utf-8").read()
        if t.count(old) != 1:
            print("FRAGMEN %dx: %s :: %s" % (t.count(old), rel, old[:56]))
            bad += 1
            continue
        done += 1
        if CHECK_ONLY:
            print("akan dinaikkan  %s" % rel)
            continue
        io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(old, new))
        print("dinaikkan       %s" % rel)
    print("\n%d aturan · %d diterapkan · %d bermasalah." % (len(RULES), done, bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

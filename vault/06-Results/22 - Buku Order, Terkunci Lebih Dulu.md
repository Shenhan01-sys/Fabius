---
tags: [hasil, "pra-registrasi", "E16", "buku-order"]
---

# 22 - Buku Order, Terkunci Lebih Dulu

**Bagian dari:** [[06-Results/00 - Hub Results]] · [[08-Backlog/03 - Epik Teori Baru.md|Epik Teori Baru]]
**Alat:** `tools/book_prereg.py` · **Perekam:** `universe/record_book_depth.py` (⑨, jalan di loop ⑦)
**Status:** TERKUNCI sebelum ada satu pun pasangan prediktif

## 1. Teori yang dibawa builder (29 Sep)

Dari seorang trader yang builder hormati: **jumlahkan total variasi harga di sisi beli, kurangi
total di sisi jual. Positif → harga memantul naik; negatif → whale/smart money ikut jual karena
mereka tidak kuat mengangkat harga.** Lalu: TP/SL dinamis, SL jadi **trailing** yang "pokoknya
jangan sampai rugi", dengan jarak trailing sudah menghitung spread + fee.

Dua hal dari kalimat itu bisa diuji, dan keduanya kami uji di alat yang berbeda:
**arah** (imbalance buku → return) di halaman ini, **dinamika exit** (trailing yang mengunci) di
[[08-Backlog/03 - Epik Teori Baru]] §4 dengan aritmatika biaya yang jujur.

## 2. Kenapa halaman ini ditulis sebelum ada datanya

Endpoint buku order kami baru diverifikasi hidup siang ini (`/fapi/v1/depth`, 611 simbol).
Riwayatnya **nol**. Teori buku order tanpa riwayat tidak bisa diuji, dan riwayat tidak bisa
diciptakan setelah fakta - jadi yang bisa dikerjakan hari ini cuma menulis aturannya dengan tegas
lalu menjalankan jamnya. Semua yang kami lihat sekarang baru satu hal, dan itu sudah cukup untuk
membuat satu rumus saja jadi keliru:

```
   ETHUSDT   bi1 -0,651   bi20 +0,525     <- imbalance BERBALIK tanda tergantung kedalaman
   BTCUSDT   bi20 -0,010  util20 -0,707   <- dan tergantung pembobotan (kuantitas vs jarak)
```

Perekam karena itu mencatat **lima** pembacaan (`bi1/bi5/bi20/mi20/util20`) dan tidak memilih
salah satunya. Yang dipilih di sini - `bi5` sebagai primer - dipilih karena paling dekat dengan
teks teorinya, **sebelum** ada angka prediktif apa pun; sisanya sekunder dengan Benjamini-Hochberg,
dan kalau yang lolos justru yang sekunder, dia tidak boleh dijual sebagai penemuan (aturan
F-D39: satu pemenang dari beberapa uji adalah kandidat, bukan hasil).

## 3. Spesifikasi yang dikunci

```text
E16 - buku order sebagai prediktor, terkunci sebelum historinya ada.

sumber_teori  : builder (29 Sep), dari trader yang dia hormati: 'total variasi harga beli - jual'
hipotesis_primer : kuantil-atas `bi5` (imbalance kuantitas 5 level) menghasilkan return-ahead
                   5 menit lebih tinggi dari kuantil-bawah, pada simbol yang sama
hipotesis_sekunder : bi1, bi20, mi20, util20 - masing-masing diuji, Benjamini-Hochberg alpha 0,10
return_ahead  : 10000 * (mid(t+300s) - mid(t)) / mid(t), mid dari snapshot berikutnya yang
                |t' - t - 300s| <= 150s; kalau tidak ada -> TIDAK DIHITUNG, bukan nol
biaya         : dikurangi setengah spread (bps) pada snapshot t - syarat (4) vonis adalah
                net-of-cost, bukan gross
perhitungan   : HANYA snapshot dengan detik > t_kunci; jangkar likuid (BTC/ETH/SOL) dilaporkan
                TERPISAH dari simbol kabar - menggabungkannya akan menyembunyikan bentuknya
vonis_layak   : (1) n >= 40 DAN (2) median > 0 DAN CI bawah bootstrap 4000 (seed 20260929) > 0
                DAN (3) Mann-Whitney satu arah atas-vs-bawah p < 0,05 DAN (4) mean net-of-cost > 0
kalau_kecil   : 'BELUM BISA DIUJI' - ambang tidak diturunkan, horison tidak diperpanjang diam-diam
kalau_gagal   : buku order ditutup sebagai jalur prediksi pada cadence kami; TIDAK dibalik
                jadi 'contra-imbalance' tanpa kunci baru
cadence_batas : ~200 s/simbol dari loop ⑦; E11 mengukur kabar hidup ±2 menit, jadi uji ini tidak
                bisa memalsukan versi CEPAT dari teori - hanya versi lambatnya
```

## 4. Soal timeframe yang builder bilang bingung

Jawaban kami datang dari pengukuran, bukan selera, dan ada tiga lapis:

| lapis | angka | dari mana |
|---|---|---|
| kabar ⑦ (transaksi smart money) hidup | **±2 menit** | E11: +192,7 bps @2m → +45,0 @10m → −182,5 @30m |
| buku order kami bisa **diamati** setiap | **±200 detik** (satu siklus ⑦) | cadence loop, bukan pilihan teori |
| horizon prediksi yang diuji di sini | **5 menit** (3 snapshot) | kompromi jujur: lebih pendek dari ini kami tidak punya data; lebih panjang sudah terbukti bocor |

Konsekuensinya harus ditulis terang: **pada cadence 200 detik, uji ini tidak bisa memalsukan versi
cepat dari teori itu.** Kalau hasilnya nol, yang gugur adalah "buku order pada resolusi 3-4 menit",
bukan klaim trader bahwa imbalance di bawah satu menit itu nyata - dan di literatur memang
horison tempat efek ini paling kuat jauh di bawah itu. Untuk menutup jarak ini butuh streaming,
yang tidak kami punya. Bukan berarti kita tidak mencoba: coba dulu pada resolusi yang ada, lalu
putuskan apakah layak membeli resolusi yang lebih tinggi.

## 5. Cara menjalankan

```bash
python -X utf8 universe/record_book_depth.py --self-test   # arah 5 pembacaan + buku tak sehat -> None
python -X utf8 tools/book_prereg.py --self-test            # edge buatan terdeteksi; n kecil != gagal
python -X utf8 tools/book_prereg.py --lock                 # sekali; menolak dobel
python -X utf8 tools/book_prereg.py --status               # umur kunci + jumlah snapshot
python -X utf8 tools/book_prereg.py                        # vonis (menolak sebelum matang)
```

## 6. Hasil

_kosong sampai umur kunci cukup - dan kekosongan ini bagian dari spesifikasinya._

**Terkait:** [[06-Results/19 - Umur Posisi]] · [[06-Results/21 - Rem di Horison Cepat]] ·
[[08-Backlog/03 - Epik Teori Baru]] · [[00-Overview/03 - Decisions]] F-D43/F-D46/F-D47 ·
[[Concepts/Unmeasured Is Not Clean]]

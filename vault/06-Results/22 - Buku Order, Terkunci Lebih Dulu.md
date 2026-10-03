---
tags: [hasil, "pra-registrasi", "E16", "buku-order"]
---

# 22 - Buku Order, Terkunci Lebih Dulu

**Bagian dari:** [[06-Results/00 - Hub Results]] · [[08-Backlog/03 - Epik Teori Baru]]
**Alat:** `tools/book_prereg.py` · **Perekam:** `universe/record_book_depth.py` (⑨, jalan di loop ⑦)
**Status:** TERKUNCI sebelum ada satu pun pasangan prediktif

## 1. Teori yang dibawa builder (29 Sep)

Dari seorang trader yang builder hormati: **jumlahkan total variasi harga di sisi beli, kurangi
total di sisi jual. Positif → harga memantul naik; negatif → whale/smart money ikut jual karena
mereka tidak kuat mengangkat harga.** Lalu: TP/SL dinamis, SL jadi **trailing** yang "pokoknya
jangan sampai rugi", dengan jarak trailing sudah menghitung spread + fee.

Dua hal dari kalimat itu bisa diuji, dan keduanya kami uji di alat yang berbeda:
**arah** (imbalance buku → return) di halaman ini, **dinamika exit** (trailing yang mengunci) di
[[08-Backlog/03 - Epik Teori Baru]] §3 dengan aritmatika biaya yang jujur.

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

Satu lapis lagi, karena pertanyaan "timeframe" sebenarnya pertanyaan uang:
`tools/cost_budget.py` menghitungnya sebagai anggaran - ongkos tetap 59,0 bps RT **plus** spread
penuh dua kaki, melawan harapan MEDIAN terkecil yang pernah kami ukur (+79,8 bps, E13 `BOLEH` menit
ke-5). Artinya **ambang spread ≈ 21 bps**: di atas itu strategi 5 menit kalah oleh biaya sebelum
pasar bergerak. Mean +285,5 bps memberi ruang sampai ~226 bps, tapi mean itu ditopang ekor kanan
(P(≥+500) 37-40 %), jadi memakainya sebagai anggaran = berharap undian, bukan menghitung edge.
Run pertama: 5/5 simbol lolos - dan itu **belum menjawab apa pun**, yang direkam baru
BTC/ETH/SOL/BNB/CAKE.

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

## 5b. Empat batas yang ditulis literatur **sebelum** vonis kami keluar

Bukan supaya hasilnya sudah tahu lebih dulu - aturan vonisnya tidak berubah - tapi supaya nol tidak
dibaca sebagai pembuktian dan positif tidak dibaca sebagai penemuan (lihat
[[08-Backlog/04 - Riset Teori (Sitasi)]] S1-S4, semuanya diakses 29 Sep 2026):

1. **Kami mengukur STATE, bukan OFI.** OFI (Cont-Kukanov-Stoikov, arXiv:1011.6402v3) adalah jumlah
   atas *event* dan **tidak dapat dipulihkan dari dua endpoint**. R² 65 % yang sering dikutip itu
   adalah kecocokan **kontemporer** pada Δt = 10 detik, bukan kemampuan meramal; dan "fit-nya
   meningkat dengan Δt" berarti makin panjang interval makin cocok dengan pergerakan yang *sudah*
   terjadi.
2. **Horison literatur bukan jam dinding.** Queue imbalance (arXiv:1512.03492v1) memprediksi
   **pergerakan mid-price berikutnya** (AUC out-of-sample 0,752-0,805 large-tick vs 0,581-0,642
   small-tick; null 0,5), dengan imbalance diambil pada waktu acak **di antara dua pergerakan harga**.
   Kami mengambil satu snapshot per ±200 detik: kami tidak sedang mengukur sinyal yang sama lebih
   pelan, kami mengukur agregat yang berbeda.
3. **Di horison satu menit pun angka OOS bisa negatif.** arXiv:2112.13213v4 melapor R² out-of-sample
   1-minute-ahead **negatif** (−0,37 s/d −0,36) di S&P 100. Dan SSRN 7053198 (preprint, tidak
   peer-review) menunjukkan Sharpe **gross +0,981 → net −1,726** pada bar 10 detik karena biaya
   ±164× edge-nya. E19 kami memberi versi lokalnya: ruang spread ≈ **21 bps** di horison 5 menit.
4. **Ada bukti arah "kontra".** arXiv:2502.18625v2 mencatat maker yang layak justru bergerak
   **melawan** imbalance dominan di beberapa rezim. Kalau vonis kami datang dengan tanda terbalik,
   itu **bukan** penemuan baru: itu arah yang sudah diduga dari literatur, dan tetap butuh kunci
   sendiri (aturan halaman 12/22: tidak membalik arah demi hasil).

Konsekuensi operasional: E16 tetap diuji apa adanya (n≥40, median>0 dengan CI bawah>0, MW satu arah,
net-of-spread>0). Yang berubah adalah **cara membacanya**: nol = sesuai dugaan; positif = curig dulu,
placebo dan grid dulu, baru klaim.

## 5c. Pengakuan cakupan (ditulis 09:5xZ, sebelum vonis, supaya tidak perlu ditulis sesudah)

Kunci dipasang 09:37:45Z. Sampai ±09:5xZ, hampir semua snapshot pasca-kunci adalah **jangkar likuid**
(BTC/ETH/SOL/BNB) - simbol kabar ditolak API karena daftar kami berisi basis aset, bukan simbol
kuotasi (F-D47; 110 baris `400 Invalid symbol` vs 20 baris data). Daftar sudah dibetulkan dan
validasi sekarang berjalan tiap siklus, tapi **jendelanya sudah tidak homogen**.

Maka vonis E16 nanti **tidak sah** kalau datang tanpa komposisi. Yang wajib ikut dicetak:
jumlah pasangan per simbol, berapa pasangan dari sebelum/sesudah 09:5xZ, dan berapa persen dari
`n` datang dari jangkar. Kalau ternyata jangkar-dominan, kalimatnya adalah *"uji ini sebenarnya
menguji BTC/ETH/SOL, bukan simbol kabar"* - bukan "imbalance buku tidak bekerja di micro-cap".
Kunci tidak digeser dan data tidak dibuang: keduanya akan jadi goalpost-moving, dan itu justru yang
kami hindari sejak halaman 12.

**Status jam (diperbarui 10:0xZ, akan diperbarui lagi sesudah vonis - bukan sebelumnya).** Run 10:0xZ:
41 snapshot `bd` (14 simbol) + 176 baris `bdx` gagal, dan **hanya BTC/ETH/SOL yang bertambah**
(10 masing-masing; sisanya 1). Sebabnya mekanis, bukan pasar: rantai ⑦ yang **sedang berjalan**
melakukan checkout pada 05:00Z, jadi ia memakai kode perekam **versi lama** sampai run berikutnya
memuat kode yang sudah dibetulkan. Artinya cakupan E16 baru melebar di tengah jendela, dan itu
justru alasan komposisi dicetak: vonis nanti dibaca bersama `share jangkar`, bukan tanpanya.
Baris `bdx` lama tidak punya `msg` (kode lama) - itu bukan data yang hilang, itu bukti bahwa
laporan kegagalan tanpa penyebab tidak bisa dijawab nanti.



## 5d. Satu keputusan prosedur: daftar pantau TIDAK kulebarkan malam ini

E16 berdiri di 26 simbol (median 16 snapshot/simbol), dan itu tipis. Godaannya jelas: tulis ulang
`universe/book-venue.txt` jadi 40 simbol teratas dari irisan (kabar ⑦ × venue - hitungannya sudah
ada: 90 simbol irisan) supaya malam ini juga sampelnya melompat, dan vonis 21:37:45Z jadi lebih
berkuasa.

Aku tidak melakukannya, dan ini bukan formalitas kosong: **E16 di-sha dengan frame sampel yang
berjalan saat itu**, dan memperluas frame di tengah jendela = mengubah ujiannya, bukan sekadar
mengisi kolom. Persis gerakan yang kami hukum sepekan ini di bentuk lain: F-D32 (control
mempromosikan dirinya), F-D47 (cakupan berubah di tengah jendela dan harus kami akui), F-D51
(peringkat berbalik saat budget diganti). Kalau angkanya butuh lebih banyak simbol, yang jujur
dilakukan adalah **menggembirakan daftarnya setelah vonis, lalu membuka kunci berikutnya** atas
frame baru itu - bukan memperluas frame di tengah jalan.

Jadi: dijadwalkan sebagai **P54** (eksekusi setelah 21:37:45Z), dan E16 tetap pada 26 simbolnya.
Kemungkinan besar hasilnya “BELUM BISA DIUJI” karena n - dan itu jawaban yang sah, bukan kegagalan.

## 6. Hasil

**Dibaca 29 Sep 2026 21:46:56Z** oleh `python -X utf8 tools/book_prereg.py` (kunci `09:37:45Z`,
syarat umur **12,12/12 jam**; `spec_sha256=0xeba3e0c510cb8470…` - blok §2 tidak kusentuh). Artefak:
`decisions/book-prereg-20260929T214656Z.json`.

## Vonis primer (`bi5`): **GAGAL**

```text
snapshot: semua 4.294 di 26 simbol | PASCA-KUNCI 4.289 di 25 simbol | sensor {bdx 198, pra_kunci 5}
pasangan yang dinilai: n=4.255
komposisi pasangan   : 25 simbol | teratas BTCUSDT=179, ETHUSDT=179, SOLUSDT=179, 0GUSDT=169,
                       4USDT=169 | share 4 jangkar likuid = 13 %
bi5   n=4255 | ret atas -1,45 (net -62,23) | bawah +0,00 | selisih -0,72 | p=0,06024
        syarat: (1) n>=40 LOLOS | (2) median>0 & CI bawah>0 GAGAL | (3) MW p<0,05 GAGAL |
                (4) mean net-of-cost > 0 GAGAL
sekunder (semua GAGAL, tidak ada yang lolos BH alpha 0,10):
   bi1 n=4255 selisih -1,25 p=0,220 | bi20 selisih -2,13 p=0,166 | mi20 selisih -0,91 p=0,169 |
   util20 selisih -3,23 p=0,443
```

**Reproduksi 22:3xZ sesudah `book_prereg.py` diberi dukungan dua ujian (E16/E25):** vonisnya tetap
**GAGAL**, tapi angkanya bergeser karena jendela 12 jam-nya bertambah tua - jangkar n=537 → **567**
(selisih +1,45 → **+1,47**, net +0,03 → **+0,14**), kabar n=3.718 → **3.938** (selisih −0,95 →
**−0,33**). Bukan kontradiksi: E16 adalah pembacaan pada **21:46:56Z**, dan itu tertulis di kepalanya.
Yang tidak boleh dilakukan seseorang sekarang adalah mengambil salah satu dari dua angka itu tanpa
jamnya - itu persis penyakit yang baru kubunuh di F-D68.

## Kelompok terpisah - dan inilah alasan clauses itu ada di spesifikasi

Spesifikasi E16 mewajibkan jangkar likuid dilaporkan **terpisah** dari simbol kabar. Saat cetakan
pertama hanya menampilkan `share 13 %`, aku menambahkan pemisahan itu ke alatnya (murni pelaporan -
aturan vonisnya tidak berubah) dan ternyata di situlah bentuk aslinya kelihatan:

```text
jangkar (BTC/ETH/SOL/BNB) n=  537 | ret atas +0,22 (net +0,03) | selisih +1,45 | p=0,104 | GAGAL
kabar (simbol berita ⑦)   n= 3.718 | ret atas -1,65 (net -69,62) | selisih -0,95 | p=0,075 | GAGAL
```

Dua hal yang bila digabung saling menihilkan:

1. **Di buku yang benar-benar hidup, arah teorinya terlihat - tapi besarnya +1,45 bps**, dan
   net-of-cost **+0,03 bps**. Itu tiga perempat dari satu basis point, atau 1/40 dari ongkos
   round-trip kami (59 bps). Bukan "hampir signifikan secara ekonomi" - tidak signifikan secara
   ekonomi sama sekali; p=0,104 juga tidak lolos.
2. **Di simbol kabar - bagian yang 87 % dan yang sebenarnya kami inginkan - arahnya terbalik**
   (imbalance tinggi memberi return lebih rendah). Sesuai `kalau_gagal` di spesifikasi: **tidak
   dibalik** jadi "contra-imbalance". Itu akan jadi hipotesis baru dengan kuncinya sendiri, bukan
   penafsiran ulang halaman ini.

## Batas yang tidak boleh hilang bersama vonisnya

- **n=4.255 bukan 4.255 observasi bebas - tapi selisihnya kecil, dan itu kuukur, bukan
  kuperkirakan.** Horison 300 d pada snapshot yang berjarak **median 244 d** (p90 248 d,
  min 32 d; 4.318 jarak antar-snapshot dalam 26 simbol ⑨) membuat **99,7 %** pasangan
  beririsan - namun irisan per pasangan hanya **56 d, 19 % dari jendela**, sehingga
  observasi efektif kira-kira 4.255 x 244/300 **~3.460**. Deflasi 1,23x ini TIDAK mengubah
  vonis (hasilnya nol, bukan positif tipis yang selamat) dan tidak membuat p=0,060 di arah
  yang salah jadi berarti; ia hanya membuat CI bootstrap dan p MW sedikit lebih optimis dari
  yang terlihat. Perbaikan masuk **P66** (jendela non-overlap di kunci berikutnya).
- **Versi CEPAT dari teori ini tidak pernah bisa dipalsukan di sini** - itu tertulis di spesifikasi
  (`cadence_batas`) dan E11 (kabar hidup ±2 m) menjadikannya fakta, bukan kekhawatiran. Yang
  dijatuhkan vonis ini adalah versi lambat dari "baca orderbook", pada cadence kami.
- **Cakupan jendela berubah di tengah jalan (F-D47)**: daftar pantau baru dibetulkan 09:5xZ, dan
  pembacaan pagi (10:0xZ) masih 100 % jangkar; sekarang 13 %. Jadi komposisi di atas bukan
  hiasan - ia menjelaskan kenapa angka gabungannya tidak boleh dibandingkan dengan mana pun.
- **Daftar pantau TIDAK kulebarkan untuk menyelamatkan ini** (F-D53). Pelebaran itu **P54/E25**,
  sesudah vonis ini tercatat - yang barusan terjadi, jadi P54 kini boleh jalan.

## Yang ditutup halaman ini

Buku order **pada cadence kami** ditutup sebagai jalur prediksi: `bi5`, `bi1`, `bi20`, `mi20`,
`util20` semuanya GAGAL, tidak ada satu pun lolos BH, dan satu-satunya kelompok dengan arah benar
adalah kelompok yang sudah likuid tempat efeknya +0,03 bps net. Lihat keputusan **F-D67** dan
penutupan T1 di [[08-Backlog/03 - Epik Teori Baru]].

> **Koreksi 3 Okt (P105b):** "net-of-cost" di halaman ini = return dikurangi SETENGAH spread pada snapshot t, persis seperti teks kuncinya. Ini BUKAN ongkos tetap 59 bps pulang-pergi ([[Concepts/Cost Is Fixed]]). Vonis tidak berubah: syarat (4) sudah gagal dengan ongkos yang lebih ringan. Lihat [[00-Overview/05 - Corrections]].

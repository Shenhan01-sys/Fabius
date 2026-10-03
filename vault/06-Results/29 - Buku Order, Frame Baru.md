---
tags: [hasil, "pra-registrasi", "E25", "buku-order", "non-overlap"]
---

# 29 - Buku Order, Frame Baru (E25)

**Bagian dari:** [[06-Results/00 - Hub Results]] · [[06-Results/22 - Buku Order, Terkunci Lebih Dulu]] ·
[[08-Backlog/03 - Epik Teori Baru]] (T1) · [[08-Backlog/01 - Backlog]] (P54, P66)
**Alat:** `tools/book_prereg.py --kunci-nama E25` · **Kunci:** `decisions/prereg-book2-lock.json`

## 1. Kenapa ini ujian baru, bukan E16 yang dibaca ulang

E16 jatuh 29 Sep 21:46:56Z pada 25 simbol. F-D53 melarang frame-nya diubah di tengah jendela - jadi
pelebaran daftar pantau ⑨ **tidak boleh** dipakai untuk mengampuni atau membatalkan E16. Yang dilakukan
sebagai gantinya: ujian BARU, kunci BARU, sha BARU, di berkas kunci yang sendiri
(`prereg-book2-lock.json`; `prereg-book-lock.json` milik E16 tidak disentuh - `--lock` menolak
menimpa dan itu keluar dengan kode bukan nol).

Dua hal yang membedakan E25 dari E16, keduanya ditulis sebelum kuncinya dipasang:

1. **Frame.** `universe/book-venue.txt` diperluas 22:2xZ ke **40 simbol kabar teratas** dari irisan
   (kabar ⑦ × venue perp - terukur **102 simbol irisan** malam ini), plus 3 jangkar yang selalu
   direkam perekam. Validasi ke `exchangeInfo`: **43 dikenal, 0 dibuang**.
2. **Jendela non-overlap (P66).** Jarak antar-snapshot dalam satu simbol terukur **median 244 d**
   pada horison 300 d → 99,7 % pasangan E16 beririsan (n efektif ~3.460, bukan 4.255). E25 hanya
   mengambil snapshot yang berjarak ≥ horison dari snapshot terpilih terakhir.

## 2. Spesifikasi yang dikunci

```text
E25 - buku order sebagai prediktor, atas frame yang diperluas DAN jendela non-overlap.

sumber_teori  : builder (29 Sep), dari trader yang dia hormati: 'total variasi harga beli - jual'
warisan       : E16 GAGAL 29 Sep 21:46:56Z pada 25 simbol (bi5 selisih -0,72 bps, p=0,060; BH alpha
                0,10 nol lulus). Keputusan F-D53 melarang frame E16 diubah di tengah jendelanya, jadi
                pelebaran itu menjadi UJIAN BARU dengan kunci sendiri - bukan E16 yang dibaca ulang.
perubahan_dari_E16 : (1) frame: daftar pantau ⑩ diperluas ke 40 simbol kabar teratas (irisan ⑦ x venue,
                         diukur 22:2xZ: 102 simbol irisan) + 3 jangkar yang selalu direkam perekam;
                     (2) jendela non-overlap (P66, ditulis SEBELUM kunci dipasang): jarak antar
                         snapshot dalam satu simbol terukur median 244 d pada horison 300 d, sehingga
                         99,7 % pasangan E16 beririsan (deflasi n efektif ~1,23x). E25 hanya
                         mengambil snapshot yang berjarak >= horison dari snapshot terpilih terakhir.
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
kalau_gagal   : buku order ditutup sebagai jalur prediksi pada cadence kami, untuk kedua kalinya,
                dan pada frame yang lebih luas; TIDAK dibalik jadi 'contra-imbalance' tanpa kunci baru
kalau_layak   : yang boleh dikatakan adalah 'imbalance memprediksi pada cadence 5 menit di frame 40
                simbol' - BUKAN 'Fabius bisa trading': E24 menunjukkan masuk kita tidak di atas acak,
                dan E12 tetap satu-satunya perilaku yang lulus prospectif
cadence_batas : ~244 s/simbol terukur; E11 mengukur kabar hidup +-2 menit, jadi uji ini tetap tidak
                bisa memalsukan versi CEPAT dari teori - hanya versi lambatnya
```

## 3. Empat syarat, dan apa yang boleh dikatakan kalau lolos

Syarat vonis identik dengan E16 (n≥40; median > 0 dan CI bawah bootstrap 4.000 > 0; Mann-Whitney satu
arah p < 0,05; **mean net-of-cost > 0**), plus kewajiban melaporkan **komposisi pasangan** dan
**jangkar terpisah dari simbol kabar** - clauses yang justru menyelamatkan pembacaan E16, karena tanpanya
"selisih −0,72" akan tampak seperti teori yang mati, padahal isinya: jangkar **+1,45 (net +0,03)** dan
simbol kabar **−0,95**.

Kalau **LAYAK**, kalimat yang diizinkan hanya sampai *"imbalance memprediksi pada cadence 5 menit di
frame 40 simbol"*. Yang TIDAK boleh: menyebutnya alasan masuk - E24 sudah menunjukkan seleksi kami tidak
di atas masuk acak (median −59,0 vs −62,2; p=0,208), dan **E12 tetap satu-satunya perilaku yang lulus
prospectif**.

Kalau **GAGAL** untuk kedua kalinya, buku order ditutup sebagai jalur prediksi pada cadence kami - dan
tetap **tidak** dibalik jadi "contra-imbalance": itu hipotesis baru dengan kunci dan n sendiri.

## 4. Hasil

**Dibaca 30 Sep 2026 10:43:24Z** oleh `python -X utf8 tools/book_prereg.py --kunci-nama E25`
(kunci `22:29:37Z`, umur **12,23/12 jam**, `spec_sha256=0x8353a2984b403393…` - §2 tidak kusentuh).
Artefak: `decisions/book-prereg-20260930T104324Z.json`.

## Vonis primer (`bi5`): **GAGAL** - dan ini kegagalan yang paling menarik sejauh ini

```text
snapshot   semua 7.116 di 42 simbol | PASCA-KUNCI 2.547 di 41 simbol | sensor {bdx 301, pra_kunci 4.569}
pasangan   n=1.249 jendela TIDAK-BERIRISAN (aturan non-overlap memotong 2.547 -> 1.249, ~1 dari 2)
komposisi  41 simbol | teratas BTC/ETH/SOL/4STOCK/AI = 52 each | share 4 jangkar likuid 12 %

bi5     n=1249 | ret atas +5,33 (net -45,12) | bawah -0,54 | selisih +11,63 bps | p=0,00118
        syarat: (1) n>=40 LOLOS | (2) median>0 & CI bawah>0 GAGAL | (3) MW p<0,05 LOLOS |
                (4) mean net-of-cost>0 GAGAL
sekunder: bi1 +7,68 p=0,0083 LOLOS-BH | bi20 +4,09 p=0,0317 LOLOS-BH | mi20 +2,69 p=0,122 gagal |
          util20 -2,55 p=0,874 gagal            -> BH alpha 0,10: 2 lulus (bi1, bi20)
kelompok: jangkar n= 156 selisih +0,67 p=0,511   |   kabar n=1.093 selisih +13,03 p=0,0014
```

## 4b. Yang berbeda dari semua vonis sebelumnya: prediksi hidupnya nyata, dan tidak bisa dipakai

Untuk pertama kalinya di proyek ini, sebuah fitur pasar **lolos uji prospectif dengan jendela
non-overlap dan menembus BH pada sekundernya**: kuantil-atas imbalance 5 level memberi
**+11,63 bps** lebih tinggi dari kuantil-bawah, pada **1.249 jendela independen**, p=0,00118 - dan
di kelompok yang benar-benar diincar teori ini (simbol kabar ⑦) **+13,03 bps, p=0,0014**.

Tapi `bi5` tetap GAGAL, dan bukan karena statistiknya: **setelah ongkos, sisanya −45,12 bps.**
Syarat (4) - "mean net-of-cost > 0" - adalah satu-satunya yang membedakan "melihat sesuatu" dari
"bisa menjualnya", dan malam ini dia bekerja persis seperti yang kami dirancang untuk lakukan.

**Kalimat yang boleh dipakai:** *imbalance orderbook memprediksi lima menit berikutnya di venue kami
sebesar ~12 bps, dan ongkos kami ~57 bps - jadi teorinya benar dan tidak bisa ditradekan.*
**Kalimat yang tidak boleh:** apa pun yang mengatakannya "edge". E24 sudah menjatuhkan masuk kita vs
masuk acak; E12 tetap satu-satunya perilaku yang lulus prospectif.

## 4c. Dua pembacaan yang harus dilaporkan berdua, bukan dipilih

Pembacaan pertama (10:38:46Z, `decisions/book-prereg-20260930T103846Z.json`) dilakukan dengan
implementasi `non_overlap` yang **salah** - aku menyetel `bebas` ke waktu *baris keluar* (sering
hanya ~245 d sesudah t) alih-alih `t + horison`, jadi aturan itu nyaris tidak memotong jendela yang
bertumpang tindih dan alatku melanggar teks yang dikuncinya sendiri:

```text
                 non-overlap salah (10:38Z)   non-overlap benar (10:43Z)
pasangan         n=2.482                      n=1.249
bi5 selisih      +7,39 bps p=0,00013          +11,63 bps p=0,00118
sekunder         BH lulus 3 (bi1, bi20, mi20) BH lulus 2 (bi1, bi20)
VONIS PRIMER     GAGAL                         GAGAL
```

Yang penting: **vonisnya tidak berubah oleh bug-ku** - keduanya GAGAL, dan arah effect-nya sama;
yang berubah hanya besaran dan seberapa banyak jendela yang boleh dihitung. Itu ujian yang
sebenarnya untuk setiap "perbaikan alat": apakah ia membalikkan kesimpulan, atau hanya memperbaiki
angka? Di sini: tidak membalikkan. Yang membunuhnya tetap syarat (4), pada kedua pembacaan.

Kenanya ketahuan bukan karena aku membaca hasilnya lebih dulu, tapi karena **n yang keluar tidak
cocok dengan pengurangan yang dijanjikan aritmetika** (cadence 245 d vs horison 300 d harusnya
memotong ~setengah; yang terpotong cuma 2,5 %). Aturan yang naik, keempat kalinya hari ini:
**kalau alatmu menghapus sesuatu, cek bahwa jumlah yang dihapus seukuran dengan yang ia klaim.**
Self-test sekarang menuntut invariant itu langsung: `39 -> 20 pasangan, jarak antar jendela
terkecil 490 d (>= 300 d)`.

## 4d. Replikasi: T1 ditutup sebagai jalur TRADE, dibuka sebagai pengukuran

Vonis GAGAL kedua untuk T1 (E16 pada 26 simbol dengan jendela beririsan; E25 pada 41 simbol dengan
jendela jujur). Yang ditutup: **jalur masuk berbasis buku order untuk trading**. Yang justru
**hidup** dan belum pernah kita punya: efek prediktif yang lolos BH dan bertahan di jendela
non-overlap - bahan untuk keputusan berikutnya (ongkos lebih rendah? ukuran lebih kecil? venue lain?
proksi ke jangkar yang likuid?), bukan untuk klaim submission malam ini.

**Dan satu peringatan yang tidak boleh hilang:** tanda `selisih` untuk kelompok simbol kabar adalah
**−0,95 di jendela E16** (pagi-sore, 25 simbol, beririsan) dan **+13,03 di jendela E25** (malam-pagi,
41 simbol, non-overlap). Itu bukan "teorinya berganti arah" - itu **populasi yang berganti wajah**,
penyakit yang sama yang baru kubunuh di F-D68 lewat P67. Angka kelompok dari halaman ini tidak boleh
dipakai untuk membatalkan angka kelompok dari halaman 22 maupun sebaliknya, dan yang boleh dijual
hanya yang **net-of-cost**, yang di kedua jendela sama-sama kalah.

Lihat juga: [[06-Results/22 - Buku Order, Terkunci Lebih Dulu]] §6 ·
[[06-Results/27 - Masuk Terpilih vs Masuk Acak]] §6 · [[03-Sinyal/Volume/V4 - Order Book dan Liquidity Heatmap]] · `00-Overview/03 - Decisions.md` F-D53, F-D66, F-D68.

> **Koreksi 3 Okt (P105b):** "net-of-cost" di halaman ini = return dikurangi SETENGAH spread pada snapshot t, persis seperti teks kuncinya. Ini BUKAN ongkos tetap 59 bps pulang-pergi ([[Concepts/Cost Is Fixed]]). Vonis tidak berubah: syarat (4) sudah gagal dengan ongkos yang lebih ringan. Lihat [[00-Overview/05 - Corrections]].

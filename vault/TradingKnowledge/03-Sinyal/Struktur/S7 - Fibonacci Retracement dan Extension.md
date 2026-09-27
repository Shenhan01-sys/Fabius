---
tags: [tk, tk-sinyal, "S7"]
---

# S7 - Fibonacci Retracement dan Extension

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Jelaskan cara pakai Fibonacci" dan
§"Buatkan panduan prioritas belajar SMC" ("Fibonacci Retracement (terutama 0.618 & 0.705)") —
klaim komunitas, tanpa pemilik hasil ukur

**Ringkas:** Ambillah dua titik, tarik grid pada pecahan jaraknya, tunggu harga menyentuh salah
satunya. Secara geometri ini jelas dan murah. Secara bukti, ini **contoh terbaik di seluruh subtree
untuk apa artinya "uji terhadap null"**: setiap ayunan menghasilkan enam level, sentuhan salah satu
dari enam level itu praktis dijamin oleh volatilitas biasa, dan karena itu "harga memantul di 0,618"
bukan penemuan — itu peristiwa yang kamu produksi sendiri dengan memilih kisi yang padat. Yang boleh
diklaim hanya yang bisa mengalahkan kisi acak dengan jumlah pemicu yang sama.

## Definisi yang bisa dihitung

```
ayunan naik  : A = swing_low, B = swing_high, L = B - A          # siapa A/B? -> parameter, lihat bawah
retracement(r) : B - r * L        r in {0.236, 0.382, 0.5, 0.618, 0.705, 0.786}
extension(x)   : B + x * L        x in {0.618, 1.272, 1.618, 2.618}
band(r, w)     : [retracement(r) - w*ATR, retracement(r) + w*ATR]   # tanpa w, "tepat di level" tak pernah terjadi
touch(t, r)    : low[t] <= band.atas(r) DAN high[t-1] >= band.atas(r)   # sentuhan pertama dari atas
hasil(t, H)    : close[t+H] / close[t] - 1, dan jarak kena stop lebih dulu
```

Asal rasio: bertetangga pada barisan Fibonacci → 0,618 = 1/φ, 0,382 = 1/φ², 0,236 = 1/φ³, dan
0,786 = √0,618. **Dua angka yang dipakai komunitas bukan turunan barisan itu**: 0,5 (tidak ada
hubungannya dengan φ) dan 0,705 (konvensi, bukan aritmetika barisan). Ini bukan cacat arithmetic —
itu tanda bahwa kisi ini dipilih karena hasilnya, bukan karena rumusnya.

## Cara pakai yang diklaim

Beli di retracement 0,618/0,705 searah tren, target di extension 1,272/1,618; digabung dengan
zona order block sebagai "confluence" (`Plan.txt` §"Detailkan Kombinasi All Rounder"). Pemilik
klaim: buku teks retail dan komunitas. Estetika "rasio yang sama ada di alam" adalah alasan
psikologis orang mempercayainya, dan itu bukan bukti; deret harga punya struktur serupa-diri di
banyak skala tanpa memerlukan φ untuk itu.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam untuk ayunan & level | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari, hanya aset ber-perp ([[Fakta Terukur]] §A) |
| ATR untuk lebar pita `w` | `ADA-TAPI` | `tools/direction.py` menyimpan rata-rata 24 TR (bukan Wilder) — lihat [[I6 - ATR dan Jarak Ternormalisasi]] |
| penentu ayunan point-in-time | `TIDAK-ADA` | tidak ada alat Fabius yang memilih Ayunan A/B; tidak ada pula penghitung level |
| data apa pun selain `(o,h,l,c)` | tidak dibutuhkan | dan itu justru poinnya: metode ini tidak menambahkan informasi baru |

## Uji di Fabius

Ini rancangan uji yang membuatnya jadi pertanyaan, bukan kepercayaan. Tiga lengan, satu deret,
horizon tetap:

1. **Lengan F** — level Fibonacci pada ayunan yang dipilih secara rule-based point-in-time
   (mis. ekstrem `N` bar terakhir yang sah, [[S3 - Market Structure BOS dan ChoCH]]), pita `w·ATR`.
2. **Lengan R** — **level acak**: sama banyaknya, pita sama lebarnya, pada rentang retracement yang
   sama. Ini null yang benar. "Tidak ada sinyal" bukan null, karena sentuhan selalu terjadi.
3. **Lengan C** — satu level tetap per ayunan (mis. median), supaya lengan F tidak menang hanya
   karena punya lebih banyak kesempatan menyentuh.
4. Hasil = return bersih per peristiwa pada `--horizon 4` dan `--horizon 24` (bentuk yang sudah
   ada di `tools/backtest.py`, jalurnya belum). Menang = F > R dengan `n >= 20` non-overlap,
   gross di atas **59 bps** terukur (§D), bertahan setelah fold terbaik dibuang, lolos BH α 0,10
   (§E). Kalau F ≈ R: rasio tidak membawa informasi; yang kamu lihat adalah bentuk deretnya.

Laporan tambahan yang wajib: **berapa banyak sentuhan per 100 bar** dan **berapa besar gabungan
pita menutupi rentang retracement**. Dua angka ini (belum diukur) biasanya sudah mengakhiri diskusi.

## Batas dan mode gagal

- **Kisi yang padat + ayunan yang bebas dipilih.** Enam level × ribuan ayunan × beberapa timeframe =
  hampir pasti ada level yang cocok di suatu tempat; ini bukan prediksi, ini penambatan pasca-hoc
  ([[EV3 - Signifikansi dan Multiple Testing]]).
- **Pemilihan ayunan adalah parameter tersembunyi yang paling besar.** Ayunan mana pun boleh
  dideklarasikan ulang setelah hasilnya mengecewakan ("yang ini bukan ayunan yang benar") —
  persis alasan keluarga ini tidak bisa disalahkan oleh data apa pun.
- **Konfluensi menggandakan tuas.** FVG + OB + Fib pada ayunan yang sama adalah satu peristiwa
  dengan tiga nama ([[S5 - Fair Value Gap]], [[S4 - Order Block dan Breaker]]).
- **Korupsi notasi kecil berakibat besar.** 0,618 vs 0,6180 vs 0,705 dibulatkan pada harga token
  berdesimal banyak mengubah level berapa puluh bps; pada kandidat dengan ongkos keluar 59 bps,
  itu seukuran edge yang diklaim.
- **Tidak ada jalur ke kandidat yang paling dijual.** Cerita Fibonacci untuk memecoin baru;
  `MIN_BARS_TINY=720` dan pool berumur ±30 bar membuat mayoritas kandidat BSC tidak punya ayunan
  yang berarti (§A).
- **Deret yang sama, informasi yang sama.** Grid ini fungsi murni dari dua angka; ia tidak menambah
  apa pun yang tidak ada di `(o,h,l,c)` (bandingkan [[I3 - MACD]] untuk kasus yang sama di indikator).

## Tingkat bukti

`T0` untuk klaim bahwa rasio ini punya isi prediktif (tidak ada pemilik hasil ukur yang bisa kami
periksa, dan uji di atas belum pernah dijalankan) · `T1` untuk aritmetika kerapatannya — itu hanya
matematika, dan ia bekerja **melawan** klaim komunitas · untuk Fabius: **belum diuji**.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fibonacci adalah kandidat uji null paling bersih di keluarga struktur: kisi acak
  dengan jumlah pemicu sama adalah pesaing yang sangat kuat, dan kami belum pernah menjalankan
  perbandingan itu."
- **Dilarang:** "harga menghormati 0,618" · "0,705 adalah level institusional" · "Fabius memakai
  fibonacci retracement" · angka akurasi apa pun yang tidak dihasilkan dari deret kami
  *(belum diukur)*.

**Terkait:** [[S3 - Market Structure BOS dan ChoCH]] · [[S5 - Fair Value Gap]] ·
[[S9 - Elliott Wave dan Harmonic]] · [[I6 - ATR dan Jarak Ternormalisasi]] ·
[[FD2 - Support Resistance dan Level Psikologis]] · [[EV6 - Kalibrasi Ambang Terhadap Hasil]] ·
[[Fakta Terukur]]

---
tags: [tk, tk-sinyal, "I3"]
---

# I3 - MACD

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"metode trading itu ada apa aja sih?" (MACD disebut
sebagai satu dari indikator standar) — klaim komunitas; tidak ada pemilik hasil ukur yang bisa kami
periksa dari repo ini

**Ringkas:** MACD adalah selisih dua EMA dari penutupan yang sama, ditambah EMA kesembilan dari
selisih itu sebagai "signal", dan histogram sebagai selisih keduanya. Ia bukan pengukuran baru: ia
filter ber-pass-band dari deret yang sudah dibaca [[I1 - Moving Average]]. Yang dibawa bukan
informasi tambahan, melainkan **dua konstanta smoothing ekstra** yang bisa disetel — dan setiap
konstanta ekstra adalah kesempatan ekstra untuk menemukan hasil yang sudah kamu cari.

## Definisi yang bisa dihitung

```
macd[t]      : EMA(c, f, t) - EMA(c, s, t)                 # default (f, s) = (12, 26)
signal[t]    : EMA(macd, g, t)                             # default g = 9
hist[t]      : macd[t] - signal[t]                         # "momentum dari momentum"
cross_up(t)  : macd[t-1] <= signal[t-1] DAN macd[t] > signal[t]
hist_peak(t) : hist[t] = max(hist[t-m .. t])               # "pelemahan" -> butuh m, itu parameter
div_bull     : dua pivot-up pada c dengan macd lebih rendah  # -> masalah pivot yang sama dgn I2
```

EMA bergantung pada seed awal, jadi nilai MACD pada bar ke-`i` berubah sedikit tergantung berapa
banyak bar historis yang dibaca lebih dulu; pada deret pendek (MARSCOIN 1.224 bar pada jendela
25 Sep, tabel siklus di [[01-Agent/01 - Asset Classes and Seats]]; dibaca ulang 28 Sep lewat
`python -X utf8 tools/bars.py MARSCOINUSDT --days 60` = **1.297 bar / 54,0 hari**) efeknya tidak
bisa dianggap nol. Konvensi `hist = macd − signal` dan
`hist = 2·(macd − signal)` dipakai bergantian antar-platform: angka berbeda, kesimpulan orang sama.

## Cara pakai yang diklaim

Beli saat MACD menyilang signal ke atas di bawah nol; jual saat silang turun; histogram yang
mengecil dibaca sebagai "tren kehilangan tenaga"; divergensi MACD sebagai pembalikan. Pemilik klaim:
buku indikator dan komunitas (`Plan.txt` menempatkannya sebagai opsional di lapisan konfirmasi).
Yang tidak pernah menyertai klaim itu: berapa banyak silang palsu per 100 bar pada aset yang mau
diperdagangkan — dan angka itu bisa dihitung dari data yang sudah ada di repo ini *(belum diukur)*.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| penutupan 1 jam | `ADA` | `tools/bars.py`; 9.599 bar untuk aset ber-perp (§A) |
| penghitung EMA/MACD | `TIDAK-ADA` | tidak ada satu pun alat Fabius yang menghitung MACD |
| konstanta `(f,s,g)` yang dibakukan | `TIDAK-ADA` | belum ada; dan tanpa itu tidak ada yang bisa direproduksi |
| jalur uji silang-vs-hasil | `ADA-TAPI` | `tools/backtest.py` menjalankan aturan arah, tapi hanya satu aturan (SMA/ret24); fitur baru harus ditulis |
| aset non-perp (memecoin C2/D) | `TIDAK-ADA` | deret mentok 1.000 bar, 0 bar untuk token gas; `MIN_BARS_TINY=720` (§A/§E) |

## Uji di Fabius

Uji yang benar bukan "MACD jalan atau tidak", tapi **apa yang ditambahkan MACD di atas saudaranya**:

1. **Baseline**: aturan dua-MA sederhana (silang `f` vs `s`) → ini pesaing terdekat, dan sudah dekat
   dengan aturan kami yang diuji di §F.
2. Perlakuan: silang MACD dan silang histogram sebagai peristiwa terpisah; hasil = return bersih
   horizon 4 j/24 j dengan `tools/backtest.py --horizon`, plus jalur kena stop.
3. Uji **tumpang-tindih**: korelasi peristiwa MACD dengan `gap(24)`/`ret24` kami. Kalau hampir semua
   pemicu MACD adalah pemicu yang sudah kami miliki, tidak ada hal baru yang perlu ditambahkan ke
   pipeline — ini hasil yang sah meskipun hasilnya "positif".
4. Null: arah acak pada simbol & jam yang sama ([[Fakta Terukur]] §B).
5. Gerbang: `n >= 20` non-overlap, gross di atas **59 bps** terukur (§D), tetap positif setelah fold
   terbaik dibuang, BH α 0,10 (§E). Perlu dicatat untuk semua keluarga indikator: pada §F, aturan
   yang **sudah** kami uji punya gross hanya +1,5 … +4,0 bps — MACD harus menjelaskan dari mana
   tambahan puluhan bps itu datang, karena deretnya sama.

## Batas dan mode gagal

- **Tidak ada informasi baru.** Tiga konstanta EMA adalah tiga tuas di atas deret yang sama; ini
  penyakit semua indikator linier dari penutupan ([[I1 - Moving Average]], [[I4 - Bollinger Bands]]).
- **Histogram = turunan kedua.** Ia memperbesar noise, bukan memperbesar sinyal; puncak histogram
  paling sering adalah tempat volatilitas sedang tinggi, bukan tempat tren "kelelahan".
- **Silang di rezim datar** = whipsaw dengan frekuensi penuh; 59 bps per putaran (§D) membuat
  frekuensi sebagai kerugian, bukan sebagai peluang.
- **Tertinggal dua lapis.** MACD tertinggal karena smoothing; silang signal tertinggal lagi; dan
  divergensi tertinggal karena butuh pivot yang sah `N` bar kemudian ([[I2 - RSI dan Divergence]]).
- **Korelasi antar-sinyal tidak dibetulkan.** Menguji MACD, RSI, dan gap SMA pada 12 aset yang
  bergerak dengan satu pasar yang sama bukan 36 percobaan bebas — persis batas yang sudah dicatat
  di [[06-Results/04 - Negative Results]].
- **Aset yang diklaim ≠ aset yang bisa diuji.** MACD dijual untuk memecoin berumur beberapa jam;
  yang bisa kami hargai sendiri hanya 608 kontrak perp (§A).

## Tingkat bukti

`T1` sebagai ringkasan momentum (perhitungan baku, dipakai luas) · `T0` untuk klaim prediktif silang
dan divergensi MACD · untuk Fabius: **belum diuji**; dan klaim "menambahkan sesuatu" bahkan belum
dirumuskan dengan benar (langkah 3 di atas belum ada jalurnya).

## Boleh dibaca, dilarang dibaca

- **Boleh:** "MACD adalah dua-MA dengan dua konstanta ekstra; sebelum menambahnya ke pipeline kami
  harus membuktikan ia pemicu yang berbeda dari yang sudah kami punya — belum."
- **Dilarang:** "MACD crossover memberi titik masuk yang terkonfirmasi" · "Fabius memakai MACD" ·
  membaca tiga indikator dari deret yang sama sebagai tiga konfirmasi.

**Terkait:** [[I1 - Moving Average]] · [[I2 - RSI dan Divergence]] · [[I4 - Bollinger Bands]] ·
[[I5 - Ichimoku Cloud]] · [[QT3 - Data Fitur dan Label]] · [[EV3 - Signifikansi dan Multiple Testing]] · [[Fakta Terukur]]

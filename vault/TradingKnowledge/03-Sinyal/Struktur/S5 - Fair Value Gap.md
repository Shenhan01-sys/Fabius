---
tags: [tk, tk-sinyal, "S5"]
---

# S5 - Fair Value Gap

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Bedah detail SMC & Order Block" — klaim komunitas;
istilah *imbalance* / *inefficiency* adalah nama lain dari keluarga yang sama

**Ringkas:** FVG adalah tiga bar: kalau sumbu bar ketiga tidak menyentuh kembali rentang bar
pertama, ada rentang harga yang "hanya diperdagangkan satu arah". Secara geometri jelas dan bisa
dihitung tanpa data tambahan apa pun — itu keunggulannya atas [[S4 - Order Block dan Breaker]].
Ceritanya tidak: bahwa rentang itu "belum selesai" dan karena itu akan didatangi kembali. Klaim itu
tidak butuh mistik untuk diuji dan justru karena itu harus diuji — karena **mean reversion biasa
sudah memprediksi sebagian besar "gap terisi"**, tanpa perlu ada order yang tertinggal.

## Definisi yang bisa dihitung

```
bullish_gap(i) : low[i+2] > high[i]    -> zona = [high[i], low[i+2]]     # bar i+1 = bar impuls
bearish_gap(i) : high[i+2] < low[i]    -> zona = [high[i+2], low[i]]
wide_gap(i)    : gap && (low[i+2]-high[i]) >= k * ATR(t)   # tanpa k, noise 1 jam juga "gap"
sentuh_pertama : bar pertama setelah i+2 dengan low <= zona.atas
tertutup_sebagian : ada bar dengan low <= titik tengah zona
tertutup_penuh    : ada bar dengan low < zona.bawah (atau high > zona.atas untuk bearish)
waktu_isi         : tau = bar sampai tertutup_penuh, Sensor pada horizon H  # wajib disebut H-nya
frekuensi         : jumlah gap / jumlah bar, per simbol dan per rezim volatilitas
```

Dua ambiguitas yang harus diputuskan sebelum klaim apa pun: **"terisi" sebagian atau penuh**, dan
**horizon** pengukurannya. Keduanya mengubah kesimpulan secara besar, dan komunitas memakainya
bergantian tergantung mana yang cocok.

## Cara pakai yang diklaim

Harga "kembali" ke FVG, reaksi di sana jadi entry dengan stop di luar impuls; FVG yang ditembus
tanpa reaksi dibaca sebagai bukti arah (dan dipakai sebagai pembatas zona berikutnya). Klaim
kausalnya: order besar yang belum terisi menunggu di rentang itu. Pemilik klaim: praktisi
SMC/ICT (di `Plan.txt` disebut satu napas dengan order block dan likuiditas). Rasio risiko-imbalan
yang baik di klaim itu **geometris benar** — zona sempit, stop pendek — dan geometri bukan edge.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam ≥ 2.400 bar | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari, hanya aset ber-perp ([[Fakta Terukur]] §A) |
| ATR untuk ambang `k` | `ADA-TAPI` | `tools/direction.py` menyimpan rata-rata 24 TR terakhir (bukan Wilder) |
| jejak order / quote yang tinggal di rentang itu | `TIDAK-ADA` | tidak ada L2/tick di repo ([[Fakta Terukur]] §C) |
| volum bar impuls (untuk menyaring gap "asli") | `ADA` | `v` per bar di cache `tools/bars.py`; belum pernah dipakai |
| penghitung gap & waktu isi | `TIDAK-ADA` | tidak ada satu pun alat Fabius yang menghitung zona |
| kandidat berumur jam | `TIDAK-ADA` | `MIN_BARS_TINY=720` → tidak layak dinilai (§A/§E) |

## Uji di Fabius

Uji yang membuatnya jadi sains dan bukan cerita, semuanya dari deret yang sudah ada:

1. Hitung **frekuensi** gap per bar per simbol per rezim. Angka ini belum pernah kami hitung
   *(belum diukur)* dan ia sudah membunuh sebagian klaim: kalau gap terjadi puluhan kali per
   ratus bar, "harga datang ke zona saya" tidak istimewa.
2. Ukur distribusi **waktu isi** untuk tiga kelompok, dengan horizon sama `H`: (a) gap nyata;
   (b) pita selebar sama yang dipasang di **ketinggian acak** dalam rentang swing yang sama;
   (c) pita selebar sama di ketinggian tetap (persentil harga). Kalau (a) ≈ (b), selesai: yang
   terukur adalah mean reversion + aritmetika jendela, bukan order yang tertinggal.
3. Perlakukan pemotongan (*censoring*) dengan benar: "95 % gap terisi" hampir pasti benar kalau `H` besar, dan itu
   bukan prediksi. Laporkan pada 4 j dan 24 j seperti `tools/backtest.py --horizon 4` dan
   `--horizon 24`.
4. Kalau (a) terbukti lebih cepat/isinya lebih sering: baru layak uji sebagai sinyal — `n >= 20`
   non-overlap, gross di atas **59 bps** (§D), tetap positif setelah fold terbaik dibuang, BH
   α 0,10 (§E). Jalur kodenya belum ditulis.

## Batas dan mode gagal

- **Horizon menentukan kesimpulan.** Dalam jendela cukup panjang, hampir semua level di antara
  ekstrem akan dikunjungi. Klaim "gap pasti terisi" adalah klaim tentang jendela, bukan pasar.
- **Definisi tiga-bar bergantung interval.** Gap 1 jam ≠ 4 jam; keduanya bisa disebut "FVG" oleh
  orang yang sama pada jam yang sama, dan itu membuat klaim tidak bisa dibuktikan salah.
- **Korelasi struktural dengan S4 dan S6.** Zona order block biasanya berdampingan dengan gap dari
  impuls yang sama; konfluensi keduanya bukan dua bukti, tapi satu bukti yang dihitung dua kali
  ([[FD11 - Aturan Mengalahkan Intuisi]]).
- **Sebab yang tidak teramati.** Mekanisme "order menunggu" butuh order book; kami tidak punya
  (§C). Yang kami punya adalah bentuk lilin — dan bentuk lilin dimiliki semua turunan harga lain.
- **Gap di tren besar tidak pernah kembali**, persis pada kasus yang paling ingin kamu tangkap;
  yang kembali adalah gap di pasar menyamping, tempat kamu tidak butuh zona untuk untung.
- **Ongkos dan ketipisan.** Stop di luar impuls = stop yang bisa ditembus sumbu; di kandidat
  BSC, keluar lebih sering gagal daripada zona menahan harga
  ([[FD3 - Likuiditas dan Dampak Harga]], [[FD7 - Invalidation Stop dan Time-Stop]]).
- **Deret yang sama, informasi yang sama.** Seperti saudaranya, ia tidak menambah apa pun di luar
  `(o,h,l,c)` — pembanding yang jujur adalah pita acak (langkah 2), bukan "tanpa sinyal"
  ([[I3 - MACD]] menjelaskan bentuk duplikasi yang sama di keluarga indikator).

## Tingkat bukti

`T1` untuk geometri dan statistik frekuensinya (dipakai luas; belum kami hitung) · `T0` untuk
klaim kausal "order belum terisi sehingga harga ditarik kembali" · untuk Fabius: **belum diuji** —
tidak ada satu baris pun di `tools/` yang menghitung zona.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "gap tiga-bar terdefinisi presisi, gratis secara data, dan hipotesis 'harga kembali ke
  gap' bisa dibunuh dengan membandingkannya ke pita acak selebar sama; kami belum menjalankan
  perbandingan itu."
- **Dilarang:** "FVG biasanya terisi, jadi tempat itu punya probabilitas" (tanpa horizon dan tanpa
  base rate) · " Fabius menandai fair value gap" · "imbalance = jejak institusi".

**Terkait:** [[S4 - Order Block dan Breaker]] · [[S6 - Likuiditas Stop Hunt dan Inducement]] ·
[[S3 - Market Structure BOS dan ChoCH]] · [[I6 - ATR dan Jarak Ternormalisasi]] ·
[[FD8 - Volatilitas]] · [[EV6 - Kalibrasi Ambang Terhadap Hasil]] · [[Fakta Terukur]]

---
tags: [tk, tk-sinyal, "I6"]
---

# I6 - ATR dan Jarak Ternormalisasi

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** keputusan ([[PL4 - Memutuskan]])
**Sumber:** bukan dari `Plan.txt` — ATR tidak disebut di daftar topik transkrip itu.
**pengetahuan standar pasar — tidak ada rujukannya di repo ini.** Yang berasal dari repo ini
hanya satu hal, dan itu bagian terpenting: `tools/direction.py` sudah menghitungnya.

**Ringkas:** ATR bukan sinyal arah; ia satuan. Fungsinya mengubah "0,5 dollar" dan "0,5 % dari
normal hari ini" jadi kalimat yang bisa dibandingkan antar-aset — dan untuk Fabius itu bukan
kemewahan: kandidat kami bisa berupa token yang baru berumur satu jam, dengan harga beberapa orden
di bawah BNB (mark 778,45 dari §A vs entri MARSCOIN 0,11605 dari
`06-Results/04 - Negative Results` §4b). Catatan ini juga
menandai tiga ketidakcocokan nyata di kode kami sendiri: ATR kami bukan Wilder, ia dihitung di bawah
24 bar tanpa peringatan eksplisit, dan jarak stop belum pernah bertemu rumus ukuran posisi.

## Definisi yang bisa dihitung

```
TR[i]   : max( h[i]-l[i], |h[i]-c[i-1]|, |l[i]-c[i-1]| )
ATR_w(n): RMA(TR, n):  a[t] = a[t-1] + (TR[t]-a[t-1])/n        # Wilder, a[0] = rata-rata n pertama
ATR_s(n): mean(TR[t-n+1 .. t])                                  # <- yang dipakai direction.py
ATR_pct : ATR / close                                           # ini yang lintas-aset, bukan ATR
jarak_stop  : ATR_MULT_STOP * ATR = 1,5 * ATR     target = 3,0 * ATR     # konstanta di kode kami
ukuran      : equity * risk_pct / jarak_stop                            # TIDAK ada di kode kami
```

Tiga fakta terverifikasi dari `tools/direction.py` (`feats()`, `decide_one()`), dan bukan tafsiran:
`atr = sum(tr[-24:]) / min(24, len(tr))` → **bukan** Wilder RMA, dan `min(24, ...)` berarti deret
pendek diam-diam memakai jendela lebih kecil; `feats()` mengembalikan `ok: False` di bawah 25
penutupan, jadi ATR tak terdefinisi untuk pool berumur beberapa jam; dan tidak ada satu baris pun di
`tools/` yang membagi `risk_pct` dengan jarak stop untuk menghasilkan jumlah.

## Cara pakai yang diklaim

Stop `k·ATR` di luar harga masuk, target `m·ATR`, ukuran posisi = risiko dibagi jarak stop
("risk-based sizing"), vol-targeting sebagai filter rezim, dan ATR sebagai pembanding jarak antar-aset
sebelum membandingkan apa pun. Semua ini adalah **penggunaan jarak**, bukan penggunaan arah — dan
itu satu-satunya penggunaan yang tidak menuntut bukti prediktif.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| `h,l,c` 1 jam | `ADA` | `tools/bars.py`; 9.599 bar pada aset ber-perp ([[Fakta Terukur]] §A) |
| ATR itu sendiri | `ADA` | dihitung `tools/direction.py`; keluarannya `atr` dan `atr_pct` ikut di-hash |
| ATR Wilder (RMA) | `TIDAK-ADA` | yang ada rata-rata sederhana 24 TR; dua angka berbeda, bukan gaya |
| ATR untuk kandidat < 720 bar | `ADA-TAPI` | terhitung, tapi `MIN_BARS_TINY` menolak kursinya; jangan dipakai sebagai pembanding (§A/§E) |
| distribusi `atr_pct` per kelas aset | `TIDAK-ADA` | belum pernah diringkas *(belum diukur)* — padahal ini pertanyaan pertama kami |
| ukuran posisi dari jarak | `TIDAK-ADA` | tiket dieksekusi pada notional tetap (`maxPositionQuote`, §E) |

## Uji di Fabius

Yang bisa dijalankan hari ini tanpa alat baru (semuanya deskriptif, dan itu penting):

1. Cetak distribusi `atr_pct` per simbol per rezim dari cache yang ada. Angka ini menentukan berapa
   besar pita apa pun yang "masuk akal" di [[S5 - Fair Value Gap]], [[S7 - Fibonacci Retracement dan Extension]],
   [[S6 - Likuiditas Stop Hunt dan Inducement]] — tanpa dia, semua `b·ATR` di subtree ini memakai ATR
   yang belum kita kenali distribusinya.
2. Uji sensitivitas aturan arah terhadap definisi ATR (rata-rata 24 vs RMA Wilder) dengan
   `python -X utf8 tools/backtest.py --cost 59 --mom-only` sebagai kerangka: hasilnya sudah negatif
   (§F), jadi yang diukur di sini adalah **seberapa besar kesimpulan bergeser** karena satu baris
   rumus — itu tes ketahanan, bukan jalan mencari untung.
3. Lengkapi satu-satunya lubang yang benar-benar menghalangi klaim: tuliskan
   `ukuran = equity * risk_pct / (k * ATR)` di satu tempat dan uji terhadap F-D16
   (`n >= 20` non-overlap, net > 0 setelah ongkos **59 bps** terukur, fold terbaik dibuang, BH
   α 0,10 — §D/§E). Sampai itu ada, `risk_pct` di keputusan kami adalah angka yang belum dibayar
   oleh jarak stopnya.

## Batas dan mode gagal

- **ATR tidak mengatakan arah** — dan orang memakainya seolah mengatakan: ATR tinggi berarti gerakan besar dua arah. Di aset tempat kami benar-benar bisa kehilangan seluruh posisi, itu peringatan, bukan peluang ([[FD8 - Volatilitas]]).
- **Seleksi pada peristiwa.** Bar pertama sebuah pool adalah bar dengan TR terbesar; token menjadi
  kandidat **karena** lonjakan itu. Menyetel stop dari ATR yang berisi lonjakannya sendiri =
  mengondisikan pada hasil (lookahead lunak, [[Concepts/Lookahead Bound]]).
- **Satu-satunya normalisasi yang sah antar-aset adalah rasio** (`ATR_pct`), bukan selisih harga.
  Kami punya keduanya di keluaran, dan `stop`/`target` dihitung dalam satuan harga — jadi banding
  "jarak stop 0,004" antar BNB dan token pecahan tidak berarti apa-apa.
- **Risiko tak tersadari oleh notional tetap.** Dengan ukuran tetap dan jarak stop yang berbeda-beda
  dalam %, satu "unit" di aset ber-ATR 8 % bisa memukul ekuitas berkali lipat dibanding aset 1 %
  ([[FD6 - Ukuran Posisi]]).
- **Jendela pendek diam-diam.** `min(24, len(tr))` berarti deret 26 bar menghasilkan "ATR 24" yang
  sebenarnya ATR-2-bar untuk sebagian besar nilainya; tidak ada peringatan di layar untuk ini.
- **Ongkos tetap lebih besar dari banyak ATR.** Pada kandidat paling tipis, 59 bps round-trip (§D)
  bisa menjadi sebagian kecil dari satu ATR — itu membuat rasio target/ongkos menipu: terlihat
  banyak ruang, padahal setiap putaran membayar.

## Tingkat bukti

`T1` untuk ATR sebagai satuan jarak (baku, dipakai luas) dan untuk penggunaannya di stop/target kami
sendiri — itu **ada di kode**, bukan klaim: `ATR_MULT_STOP = 1,5` dan `ATR_MULT_TP = 3,0` di
`tools/direction.py`. Yang **sudah diuji** di sekitarnya hanyalah aturan arah yang memakai jarak
ini, dan hasilnya negatif di 12/12 ([[Fakta Terukur]] §F, lihat [[I1 - Moving Average]]): ATR tidak
membuat aturan itu benar dan tidak membuatnya salah. `T0` untuk klaim komunitas bahwa "ATR tinggi =
harga akan bergerak besar ke arah tertentu".

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami menormalkan jarak dengan ATR karena harga kandidat berbeda beberapa orden; ATR
  kami rata-rata sederhana 24 TR, bukan Wilder, dan ukuran posisi belum dihubungkan ke jarak stop."
- **Dilarang:** "Fabius menghitung risiko dengan ATR" (ia menghitung **jarak** dengan ATR) ·
  menyebut ATR sebagai sinyal arah · menganggap `atr_pct` lintas aset sudah kami petakan
  *(belum diukur)*.

**Terkait:** [[FD8 - Volatilitas]] · [[FD6 - Ukuran Posisi]] ·
[[FD7 - Invalidation Stop dan Time-Stop]] · [[S7 - Fibonacci Retracement dan Extension]] ·
[[I4 - Bollinger Bands]] · [[I1 - Moving Average]] · [[Fakta Terukur]]

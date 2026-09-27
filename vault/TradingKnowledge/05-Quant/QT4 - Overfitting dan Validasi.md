---
tags: [tk, tk-quant, "QT4"]
---

# QT4 - Overfitting dan Validasi

**Keluarga:** [[00 - Hub Quant]] · **Tahap:** penilaian ([[PL6 - Menilai Hasil]])
**Sumber:** `vault/TradingKnowledge/QuantTrading/Info1.txt` §"Kelebihan & Kekurangan" (daftar
topik) · mekanisme yang benar-benar dipakai: `tools/backtest.py`, [[Fakta Terukur]] §E/§F ·
`vault/06-Results/05 - Pre-registration Flow.md`

**Ringkas:** dengan cukup tuas, data historis apa pun bisa dibuat menguntungkan. Overfitting bukan
kesalahan aritmetika — ia hasil dari memilih konfigurasi terbaik dari banyak konfigurasi, lalu
melaporkan yang terbaik itu seolah-olah ia satu-satunya yang dicoba. Karena itu yang divalidasi
bukan angkanya, tapi **jumlah percobaan yang ada di belakang angka itu**. Kami belum punya
perhitungan formalnya; yang kami punya adalah satu aturan yang ditegakkan: ambang tidak disetel
setelah hasil dilihat.

## Definisi yang bisa dihitung

```
N_eff  = jumlah konfigurasi (parameter x horizon x universe) yang pernah dijalankan pada data yang sama
risiko overfit ~ naik bersama N_eff dan bersama rasio (jumlah parameter bebas) / (jumlah sampel independen)
```

Dua kontrol formal yang namanya beredar di literatur dan **tidak** kami hitung di repo ini:

| kontrol | apa yang ia tanyakan | status |
|---|---|---|
| Deflated Sharpe Ratio (diklaim literatur ML finansial — `Info1.txt` §"Buku", tidak kami reproduksi) | Sharpe berapa yang masih mustahil datang dari kebetulan, setelah N_eff percobaan diperhitungkan | `TIDAK ADA` kodenya |
| Probability of Backtest Overfitting (PBO) | kalau konfigurasi dipilih di-sample, berapa peluang dia jadi terburuk di luar-sample | `TIDAK ADA` kodenya |
| uji arah acak pada (token, jam) | apakah **arah** aturan kita lebih baik dari lemparan koin di titik yang sama | **sudah dipakai** sebagai pembanding (§B/§F) |
| uji parameter acak | ambang diacak N kali; kalau pengacakan secanggih pilihan manual, tidak ada informasi di pilihannya | belum ditulis |

Yang bisa dibaca langsung dari lembar angka: `NEED_BARS=2400` (§A) dan `MIN_SAMPLES=20` non-overlap
(§E). Satu aturan arah kami saja sudah punya ≥ 4 tuas bebas (gap SMA, ret24, ambang `|acf|`,
funding), sementara sampel non-overlap per aset dibatasi horizon dan panjang deret yang sama — jadi
rasio parameter terhadap sampel ada di wilayah yang akan berkata "belum tahu", bukan "edge", pada
uji statistik mana pun.

## Cara pakai yang diklaim

Praktik yang dijual: grid search + walk-forward + regularisasi, atau "model yang lebih rumit akan
memilih dirinya sendiri". Klaim itu bukan milik kami dan tidak ada buktinya di repo ini. Yang kami
lakukan sebagai gantinya adalah versi murah dari disiplin yang sama: **satu** spesifikasi dibekukan
lebih dulu, dijalankan sebagai **satu** varian yang sudah dinyatakan, dan varian lain dinyatakan
sebagai varian (`--mom-only`, `--flip`, `--horizon 24`), bukan sebagai hasil baru.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| deret cukup panjang untuk 5 fold | `ADA` | Aster 9.599 bar ≈ 400 hari — §A |
| ambang yang tercatat asal-usulnya sebelum hasil | `ADA` | §E: `NEED_BARS=2400`, `MIN_SAMPLES=20`, BH α 0,10, drop-best-fold |
| log N_eff (semua percobaan, termasuk yang gagal) | `TIDAK-ADA` | tanpa ini tidak ada satu pun koreksi multiple testing yang bisa dipercaya |
| data baru untuk konfirmasi siklus berikutnya | `ADA-TAPI` | prospektif: butuh kalender, dan §F hanya mewakili satu rezim |
| uji resampling yang sah (block bootstrap waktu) | `TIDAK-ADA` | `tools/backtest.py` memakai segmen waktu + sign-flip, bukan bootstrap lintas aset |

## Uji di Fabius

```
python -X utf8 tools/backtest.py --mom-only            # siapa yang memproduksi nol: gerbang atau isinya
python -X utf8 tools/backtest.py --mom-only --flip     # aturan sama, arah dibalik
python -X utf8 tools/backtest.py --mom-only --horizon 24
```

Yang sudah terukur (§F): tanpa gerbang, net −27,9 … −0,8 bps/trade dan **negatif di 12/12**;
dibalik **tetap kalah** (−39,2 … −12,1); horizon 24 jam **0/12 lolos** — dan satu-satunya `net`
positif yang bertahan setelah fold terbaik dibuang adalah satu aset dengan `t` yang bahkan tidak
mendekati berarti. Itu justru bukti bahwa pagarnya bekerja, bukan bahwa ada edge di balik pintu.

Aturan kami, yang berlaku untuk semua catatan di subtree ini: **ambang tidak boleh disetel setelah
hasil dilihat.** Kalau ia harus berubah, itu entri keputusan baru dengan tanggal, bukan suntingan
pada run yang sama ([[06-Results/02 - Thresholds]]).

## Batas dan mode gagal

- **Data snooping lintas halaman.** Empat varian di atas memakai deret yang sama; membacanya
  sebagai empat konfirmasi = menghitung satu percobaan sebanyak empat kali.
- **korelasi antar-tes.** "0 dari 12" bukan dua belas percobaan bebas — kedua belas aset bergerak
  dengan satu pasar yang sama (batas yang ditulis sendiri oleh `vault/06-Results/04 - Negative
  Results.md`).
- **p yang terlalu kecil.** Aproksimasi normal yang kami pakai pada n=20–40 menghasilkan p
  **sistematis terlalu kecil** (§E) — bentuknya diwarisi supaya sebanding dengan kode rujukan, dan
  kelemahannya ditulis, bukan dipoles.
- **Fold terbaik = topeng.** Drop-best-folding ada karena satu segmen baik bisa menyamar sebagai
  aturan baik; itu terukur di sini (BNB +14,9 bps → −8,7 setelah fold terbaik dibuang — baris 74 di
  [[06-Results/04 - Negative Results]]).
- **Zona abu-abu bukan kegagalan.** `|acf|` 0,05–0,10 artinya belum tahu, dan membacanya sebagai
  "hampir lolos" adalah pintu masuk overfitting yang paling sopan.

## Tingkat bukti

`T1` untuk konsep N_eff / DSR / PBO (nama dari literatur, tidak kami reproduksi) · `T3` untuk
praktik "ambang diimpor, bukan di-fit" plus tiga varian kontrol yang benar-benar dijalankan dan
angkanya ada di §F · flag `NEGATIF` untuk hasil instance itu.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami menyetel nol parameter setelah melihat hasil; empat varian dijalankan pada deret
  yang sama dan dilaporkan sebagai varian, dan semuanya tetap rugi setelah ongkos."
- **Dilarang:** "hasil kami sudah dikoreksi untuk multiple testing secara formal (DSR/PBO)" ·
  "0/12 lolos berarti edge tinggal selangkah" · "karena kami tidak men-fit, hasil kami pasti benar".

**Terkait:** [[QT1 - Dari Ide ke Strategi yang Bisa Diuji]] · [[QT2 - Backtesting yang Jujur]] ·
[[EV3 - Signifikansi dan Multiple Testing]] · [[EV6 - Kalibrasi Ambang Terhadap Hasil]] ·
[[GAP2 - Uji Setiap Veto Terhadap Hasil]] · [[Concepts/Lookahead Bound]]

---
tags: [tk, tk-quant, "QT8"]
---

# QT8 - Machine Learning untuk Trading

**Keluarga:** [[00 - Hub Quant]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/QuantTrading/Info1.txt` §"Pelajari machine learning untuk
trading" (daftar topik) · batas data/angka: [[Fakta Terukur]] §A/§C/§E/§F ·
`vault/06-Results/04 - Negative Results.md`

**Ringkas:** machine learning untuk trading biasanya berarti satu hal: latih regresi/klassifikasi
untuk memprediksi return masa depan dari fitur saat ini. Di data harga, sinyal yang bisa dipelajari
sangat kecil dibanding noise, sampel independennya sedikit, dan distribusinya pindah-pindah — tiga
kondisi yang paling mudah menghasilkan model yang kelihatan akurat dan sebenarnya menghafal.
Status Fabius harus ditulis tanpa euphemisme: **tidak ada satu pun model terlatih di repo ini** —
tidak ada bobot, tidak ada training loop, tidak ada holdout. Yang ada hanya aturan linear dengan
ambang tetap, dan aturan itu sudah kalah ongkos.

## Definisi yang bisa dihitung

```
X[t]  = fitur(t)          # semua bahan hitungnya <= t  (lihat [[QT3 - Data Fitur dan Label]])
y[t]  = sign(r[t,h])      # label: arah return pada horizon tetap h, atau return itu sendiri
model := f: X -> {long, flat, short}  (atau skor)
uji   = akurasi TANPA arti; yang ditanya = expectancy bersih setelah ongkos, pada data yang tidak pernah dilihat
```

Tiga penyakit yang menentukan segalanya:

| penyakit | bentuk konkretnya | pager |
|---|---|---|
| **SNR rendah** | gross aturan linear kami saja +1,5 … +4,0 bps melawan ongkos 20 bps (§F); model apa pun yang belajar dari fitur yang sama memulai dari defisit itu | laporan selalu `net`, tidak pernah `accuracy` |
| **feature leakage** | satu fitur yang diam-diam memakai masa depan (label GMGN hari ini, baris Dune yang bisa di-update retro) | fitur point-in-time, lihat [[QT3 - Data Fitur dan Label]] |
| **non-stasioner** | 400 hari = satu sejarah; rezim yang melahirkan pola bisa berhenti melahirkan apa pun | konfirmasi di jendela **baru**, bukan fold acak |

**Purging & embargo** (pengetahuan standar, dipopulerkan literatur ML finansial yang namanya
didaftar di `Info1.txt` §"Buku" — tidak kami reproduksi): sampel yang jendelanya
`t … t+h` tumpang tindih dengan train/test harus dibuang, ditambah jarak pengaman. Cross-validation
acak pada data urutan melanggar ini dan tetap menghasilkan angka bagus.

## Cara pakai yang diklaim

Klaim pemilik praktik (vendor platform ML, dana yang mempekerjakan ML sebagai faktor): model bisa
menangkap interaksi non-linear antar-ratusan indikator dan on-chain. Kami tidak menguji klaim itu
dan tidak punya bahan untuk mengujinya: dengan `MIN_SAMPLES=20` non-overlap per aturan (§E), ruang
hipotesis model mana pun jauh lebih besar daripada data yang membatasinya.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| fitur numerik pada jam keputusan | `ADA-TAPI` | hanya rasio yang kami punya (`ret24_pct`, `atr_pct`, `acf_abs`, `funding_4h`) — `tools/direction.py`; kolom volum belum pernah dipakai jadi fitur |
| label horizon tetap | `ADA` | `tools/backtest.py` menghitung forward return 4/24 bar (§F) |
| sampel independen dalam jumlah memadai | `ADA-TAPI` | 12 aset ber-kontrak perp dengan `n>=20` per aturan — §E/§F; untuk model beratus parameter, ini bukan sampel, ini anekdot |
| histori funding/OI sebagai fitur | `ADA-TAPI` | Bybit `/v5/market/funding/history` **200 baris = 66,3 hari** dan OKX `funding-rate-history` **33,0 hari**, dua-duanya tanpa kunci, interval **8 jam** — [[Fakta Terukur]] §A.5 (diukur 28 Sep dari laptop ini, BELUM dari runner). 8 jam bukan fitur per-bar: tetap veto rezim, bukan sinyal |
| tick/L2 untuk fitur mikrostruktur | `TIDAK-ADA` | §C |
| jalur latih-evaluasi (split, simpan bobot, reproduksi) | `TIDAK-ADA` | tidak ada satu pun baris kode latih di repo ini |

## Uji di Fabius

Tidak ada perintah ML yang boleh dikutip dari catatan ini. Kalau jalur itu dibuka, urutan yang sah
(pra-registrasi lebih dulu, seperti `vault/06-Results/05 - Pre-registration Flow.md`):

1. features-only + label yang sudah dibekukan (`tools/bars.py` sebagai sumber harga);
2. split waktu dengan purge/embargo, satu sampel per (token, jam) non-overlap (§E);
3. baseline = **arah acak pada token dan jam yang sama** (§B), bukan "tidak ada model";
4. naik tingkat bukti hanya lewat gerbang yang sudah ada: `n >= 20`, net > 0 setelah ongkos,
   tetap positif setelah fold terbaik dibuang, lolos BH α 0,10, dan **konfirmasi di siklus data
   baru**.

Perintah yang dibutuhkan: `tools/ml_holdout.py` — **belum ditulis**.

## Batas dan mode gagal

- **Model besar di sampel kecil** menghasilkan angka yang tidak bisa dibedakan dari keberuntungan;
  tanpa log percobaan ([[QT4 - Overfitting dan Validasi]]) kita tidak tahu berapa banyak kegagalan
  yang tidak dilaporkan.
- **Akurasi 60 % bukan apa-apa** di kelas yang tidak seimbang — dan win rate 69,8 % dengan hasil
  minus sudah pernah kami ukur (§F).
- **LLM di dalam fitur** = dua sumber noise digabung; kalau itu dilakukan, ia hanya boleh berdiri
  **di bawah** data ([[QT9 - LLM sebagai Pembaca Narasi]]).
- **Hasil negatif bukan bukti "ML tidak jalan"** — yang dibunuh ongkos adalah aturan linear kami,
  bukan seluruh kelas model. Klaim "crypto tidak bisa dipelajari" melebihi yang diukur.
- **Non-stationarity** membuat retrain wajib; dan retrain tanpa data baru = memilih ulang parameter
  pada sejarah yang sama.

## Tingkat bukti

`T1` untuk kerangka supervised prediction dan tiga penyakitnya (pengetahuan standar pasar) · `T2`
untuk purging/embargo sebagai rujukan literatur yang tidak kami reproduksi · untuk Fabius:
**belum ada apa pun diuji** — tidak ada model, jadi tidak ada tingkat bukti untuk model. Angka §F
yang relevan hanyalah batas bawah yang harus dikalahkan sebuah model.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius tidak menjalankan model ML; ia menjalankan aturan linear yang diuji dengan
  ambang diimpor, dan model ML apa pun di sini harus mengalahkan hasil minus itu lebih dulu."
- **Dilarang:** "agen kami belajar dari data" · "FreqAI/qlib sudah terpasang" (belum diverifikasi
  di mesin ini) · "akurasi tinggi berarti untung" · "karena aturan linear kalah, ML pasti kalah".

**Terkait:** [[QT3 - Data Fitur dan Label]] · [[QT4 - Overfitting dan Validasi]] ·
[[QT9 - LLM sebagai Pembaca Narasi]] · [[EV2 - Jebakan Backtest]] · [[FD8 - Volatilitas]] ·
[[PL3 - Menganalisis]]

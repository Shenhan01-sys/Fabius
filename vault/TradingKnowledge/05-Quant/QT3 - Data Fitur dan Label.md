---
tags: [tk, tk-quant, "QT3"]
---

# QT3 - Data Fitur dan Label

**Keluarga:** [[00 - Hub Quant]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/QuantTrading/Info1.txt` §"Komponen Utama Quant Trading" /
§"Pelajari machine learning untuk trading" (daftar topik) · fitur yang benar-benar ada:
`tools/direction.py` · [[Fakta Terukur]] §A/§C/§E/§F

**Ringkas:** fitur adalah apa yang terlihat pada jam keputusan; label baru bisa ditulis setelah jam
itu lewat; horizon adalah batas di antara keduanya. Campur ketiganya dan sebuah uji akan selalu
menemukan apa yang sudah ada di file. Catatan ini memisahkan tiga kata yang di praktik dipakai
bergantian, dan menyebut label tiga-barrier sebagai **label yang belum bisa kami hitung dengan benar**.

## Definisi yang bisa dihitung

```
fitur(t)   : nilai yang seluruh bahan perhitungan waktu-nya <= t   # termasuk waktu terbit sumbernya
label(t,h) : return dari entry(t) sampai t+h, atau hasil barrier pertama sebelum t+h
horizon(h) : tetap, dinyatakan dalam bar; keluar sebelum h hanya lewat aturan yang juga tetap
```

Dua bentuk label yang sah:

| bentuk | definisi | bisa dihitung di Fabius? |
|---|---|---|
| horizon tetap | `r = px[t+h] / entry - 1`, keluar di `t+h` apa pun yang terjadi | **ya** — inilah yang dipakai §F (time-stop) |
| tiga-barrier | `r` ditentukan barrier mana (profit / stop / waktu) yang tersentuh duluan | **tidak bersih**: satu bar 1 jam hanya memberi `high` dan `low`; urutan sentuh di dalam bar tidak teramati, jadi barrier mana yang duluan **tidak bisa** dipastikan tanpa tick |

Label tiga-barrier adalah pengetahuan standar (populer lewat literatur ML finansial yang didaftar
di `Info1.txt` §"Buku") — di repo ini **tidak ada satu pun baris kode** yang memproduksinya.

**Fitur harus tersedia pada waktu keputusan.** Ini bukan soal rumus, tapi soal jadwal terbit: baris
Dune punya `_updated_at` (boleh jadi statistik, tidak boleh jadi saksi waktu), dan keanggotaan panel
GMGN adalah label **hari ini** tentang transaksi **minggu lalu** — yang terakhir sudah membunuh satu
pembacaan: panel whale 69,8 % menang namun tetap −10,4 bps terhadap kerumunan, dan itu pun batas atas
yang ramah ke panel (§B/§F).

## Cara pakai yang diklaim

Praktik standar: bangun matriks fitur point-in-time, tempel label dari masa depan, latih/evaluasi
pada potongan waktu yang tidak tumpang tindih, dan bekukan definisi fitur sebelum hasil. Kami
memakai bagian "fitur point-in-time"-nya saja di `tools/direction.py` — yang keluar sebagai fitur
terukur adalah `ret24_pct`, `atr_pct`, `acf_abs` (lag 1/6/24), `funding_4h`, `oi`, likuiditas pool,
`bundler_rate`, dan jumlah bar. Tidak ada pelatih, tidak ada bobot, tidak ada model.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLCV 1 jam ≥ 2.400 bar | `ADA` | Aster 9.599 bar ≈ 400 hari, dijawab sendiri lewat `tools/bars.py` — §A |
| fitur yang tersedia di waktu keputusan | `ADA-TAPI` | `acf_abs`/`ret24_pct`/`atr_pct` dihitung dari bar `<= t`; funding & OI hanya **terkini** — §A |
| histori funding/OI per aset | `TIDAK-ADA` | tidak bisa ditarik mundur (§C) → fitur carry tidak bisa jadi label-uji |
| urutan sentuh dalam bar (untuk tiga-barrier) | `TIDAK-ADA` | tidak ada tick/L2 (§C) |
| volum per bar | `ADA-TAPI` | ikut `klines`; belum pernah dipakai sebagai fitur apa pun (§A) |
| normalisasi lintas aset | `ADA-TAPI` | semua fitur kami berupa rasio/return; **tidak** ada fitur berbentuk harga absolut |
| aliran dompet sebagai fitur point-in-time | `ADA-TAPI` | 100 tx/panggilan, jendela lihat 8–13 menit, tanpa riwayat (§B) — fitur yang hilang permanen kalau perekam bolong |

## Uji di Fabius

Yang bisa dijalankan sekarang (label horizon tetap, fitur live):

```
python -X utf8 tools/backtest.py --horizon 4
python -X utf8 tools/backtest.py --horizon 24 --mom-only
```

Yang harus ada sebelum label tiga-barrier boleh disebut: alat yang merekonstruksi urutan sentuh di
dalam bar — `tools/labels.py`, **belum ditulis**; tanpa tick dia hanya menghasilkan pendekatan yang
harus dinyatakan sebagai pendekatan. Uji kesehatan fitur yang kami lakukan manual dan wajib
dibakukan: (a) tiap fitur punya nilai `None` yang tertangani
([[Concepts/Unmeasured Is Not Clean]]), (b) tidak ada fitur memakai baris `> t`, (c) satu sampel per
(token, jam) — §E.

## Batas dan mode gagal

- **Harga absolut lintas aset = kebocoran skala.** Tingkat harga antar aset di universe kami berbeda
  beberapa orden (satu-satunya harga absolut di lembar angka ini mark BNB 778,45 — §A; sisanya
  *(belum diukur)*); fitur berupa level harga membuat model belajar "siapa ini", bukan apa yang terjadi.
- **Class imbalance dua arah.** Kelas "flat" mendominasi karena gerbang menolak hampir semuanya (§F:
  nol trade di enam aset terdalam), dan di sisi label trade rugi lebih jarang dari "tidak ada
  kejadian". Akurasi tidak berarti di keadaan ini; yang dipakai expectancy ([[FD5 - Expectancy Bukan Win Rate]]).
- **Label yang terbit belakangan** (sentimen, artikel, tag panel) = prediksi masa depan yang
  disusupkan ke fitur.
- **Fitur dari sumber yang bisa di-update retro** mengubah hasil hari ini kalau kueri diulang
  besok — dan itu bukan reproduksibilitas ([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]).
- **Kolom volum boleh jadi sampah**: wash trading di chain spot adalah risiko nyata, dan kami belum
  pernah mengujinya *(belum diukur)*.

## Tingkat bukti

`T1` untuk pemisahan fitur/label/horizon sebagai praktik standar · `T2` untuk label tiga-barrier
(literatur yang namanya disebut di `Info1.txt`, tidak kami reproduksi, dan tidak bisa dihitung
benar dengan OHLC saja) · `T3` untuk satu hal saja: horizon-tetap dengan fitur point-in-time
sudah dijalankan di data kami dan hasilnya tercatat di §F (`NEGATIF`).

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius menghitung fitur rasio dari bar yang sudah ada pada jam keputusan dan melabeli
  dengan horizon tetap; label berbasis barrier belum bisa dihitung karena urutan sentuh dalam bar
  tidak teramati."
- **Dilarang:** "kami memakai three-bar labeling" · "dataset fitur kami siap dilatih" ·
  "fitur on-chain kami point-in-time" (aliran dompet ya; label panel GMGN tidak).

**Terkait:** [[QT2 - Backtesting yang Jujur]] · [[QT8 - Machine Learning untuk Trading]] ·
[[QT12 - Stack Data dan Perkakas]] · [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] ·
[[FD9 - Horizon Waktu dan Multi-Timeframe]] · [[Concepts/Point-in-Time vs Retro-updatable]]

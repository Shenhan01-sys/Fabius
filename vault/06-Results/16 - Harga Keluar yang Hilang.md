---
tags: [hasil]
---

# 16 - Harga Keluar yang Hilang

**Sumber:** `tools/censor_bound.py` · horison 30 menit · harga peristiwa · 28 Sep ±15:5xZ
**Alat pembanding:** `tools/technic_lab.py` (halaman 15) memakai pool yang sama TANPA memperbaiki ini

**Ringkas:** halaman 15 menemukan bahwa harapan positif universe ini tinggal di kohort token **muda**
(deret < 30 baris: mean **+450,8 bps**, P(≥+500) 47,5 %) sementara kohort matang negatif (−67,9).
Pertanyaan yang harus diajukan ke angka seperti itu bukan "cara apa yang menungganginya", tapi
**"berapa yang tidak kembali"**. Jawabannya: di kohort muda, **80,6 % kejadian tidak punya satu pun
baris harga dalam jendela keluar** (2.267 dari 2.814). Dan persentil-5 dari yang *kembali* sudah
menyentuh lantai winsor (−2.000 bps). Jadi +450,8 itu bukan temuan - itu **angka korban selamat**.

## 1. Bound, bukan tebakan

| kohort | teramati keluar | hilang | mean hanya-yang-teramati (CI 90 %) | mean bila yang hilang = p05 teramati | break-even |
|---|---|---|---|---|---|
| **MUDA** (deret < 30 baris) | 547 (**19,4 %**) | **2.267 (80,6 %)** | **+249,3** [+146,8; +354,8] · P≥500 42,4 % | **−1.562,8** | **0** dari 2.267 |
| **MATANG** (deret ≥ 30) | 476 (59,8 %) | 320 (40,2 %) | −86,6 [−189,7; +16,5] · P≥500 30,0 % | −855,8 | 0 dari 320 |

`break-even = 0` bukan typo: karena persentil-5 yang teramati sudah **di** lantai (−2.000 bps),
memberi harga "seburuk yang kita pernah lihat" ke kejadian yang hilang sudah cukup untuk membalik
mean kohort muda dari +249 ke −1.563. Tidak perlu mengarang skenario buruk - distribusi kita
sendoh sudah menyimpannya.

## 2. Kenapa kejadian bisa tidak punya harga keluar

`px`/deret peristiwa kita bergerak **hanya saat ada transaksi** (§B lembar fakta: 71,7 % barisnya
bahkan hanya pengulangan nilai). Untuk token yang ditinggalkan pembeli dalam 30 menit, "tidak ada
baris keluar" itu bukan lubang data - itu **beritanya**: tidak ada yang membeli lagi. Membuangnya
sama dengan menghitung hanya pool yang masih hidup dan menyebut hasilnya harapan.

Dua jalan keluar yang jujur, dan belum satu pun kita punya:
1. **Survival-pull**: pantau pool tempat kita membuka posisi sampai horison lewat sumber yang tidak
   bergantung pada transaksi (cadangan pool / `is_stopped` / kehadiran pair), sehingga "pool hilang"
   tercatat sebagai kejadian, bukan sebagai baris yang tidak ada. `wp` (P17) adalah fondasinya tapi
   jendela pantau kita 2 jam dan ditarik **seragam** - ia belum menyimpan token yang kita
   *beli secara keputusan*.
2. **Bound yang dilaporkan**: setiap kali menyebut mean, sebut juga `P(ada harga keluar)`. Alat ini
   sudah mencetaknya; sekarang tinggal kewajiban menuliskannya di tiap halaman hasil.

## 2b. Tahap 2: mana yang benar-benar mati, mana yang cuma tidak kami tanya

Bound di §1 masih buta - ia memberi nilai terburuk ke SEMUA kejadian tanpa harga keluar.
`tools/presence_ledger.py` memisahkan keduanya, dan perjalanannya membuka tiga lapis kesalahanku
sendiri:

1. **Jendela pantau dipakai sebagai bukti kematian.** Versi pertama menyebut 74 % token HILANG -
   padahal jendela perekam 120 menit, jadi absen di siklus ke-40 artinya keluar dari DAFTAR KAMI.
   Aturan diperbaiki: bukti hanya dari siklus di dalam `(last_seen, last_seen + jendela]`.
2. **Kami tidak mencatat apa yang kami tanyakan - jadi pemangkasan batch tidak akan kelihatan.**
   Kekhawatiran awalnya salahukur: daftar pantau nyata = 161-165 token dan 6 batch = 180 alamat,
   jadi saat ini tidak ada yang terpotong. Yang benar-benar salah adalah ketiadaan catatan: tanpa
   `wpc` kami tidak akan pernah bisa membedakan keduanya, dan aku sudah terlanjur menyimpulkan
   '55 % pool mati'. Sekarang perekam menulis `wpc` (n_tanya/n_batch) dan `--max-batches` naik ke 40
   sebagai asuransi - bukan sebagai perbaikan bug yang sedang terjadi. Pembacaan origin pertama:
   6 siklus `wpc`, semuanya `n_tanya > n_jawab` (161 ditanya, 136 terjawab).
3. **Perekam melapor "mencatat" tanpa mencatat.** Guard dedupe memanggil `r["tk"]` buta; baris buku
   tidak punya `tk` -> `KeyError` -> siklus selesai dengan konsol *kehilangan tercatat 11* sementara
   berkas tidak bertambah. Ketahuan bukan dari error, tapi dari angka konsol yang tidak muncul di
   berkas. Guard kini tahan semua jenis baris dan tiap siklus mencetak komposisinya
   (`{'wpc':1,'wp':136,'wp0':11}`).

Klasifikasi (28 Sep 22:1xZ; 1.439 kejadian lolos veto, harga peristiwa):

| status kehadiran | n | mean winso | median | P(≥+500) |
|---|---|---|---|---|
| ADA | 489 | +141,3 | −58,9 | 29,9 % |
| **HILANG** | 375 | +140,5 | −15,7 | 38,1 % |
| TIDAK-JELAS (tidak pernah lewat pantau) | 575 | +229,0 | −11,0 | 41,7 % |

**Bound dengan bukti:** 1.064 kejadian teramati (mean **+188,7**) + 375 token HILANG dihitung rugi
penuh = **−381,7 bps/posisi**. Pembacaan ulang 24 menit kemudian (206 siklus, 1.484 kejadian):
1.055 teramati (+170,7) + 429 HILANG = **−456,8 bps/posisi** - bound ini bergerak karena datanya
bertambah, dan itu alasan ia ditulis sebagai bound, bukan sebagai hasil. Jadi "+249 di kohort muda" bertahan hanya kalau kita rela berkata
375 token yang berhenti dijawab venue itu tidak apa-apa.

Yang tersisa sebagai batas: bukti langsung (`answered-no-pair`) baru 8 token sejauh ini - mayoritas
status HILANG masih **inferensi jendela**. Yang mengubahnya jadi bukti adalah rantai menjalankan
perekam baru, dan itu butuh commit ini sampai ke default branch.

## 3. Konsekuensinya untuk tiga kandidat fine-tuning (P32)

- **Volatilitas terealisasi** tetap kandidat terkuat - tapi alasannya berubah: ia satu-satunya fitur
  yang justru *mendeteksi* penyakit ini. Kuintil terbawah (median 0,079 %/bar) punya
  **P(≥+500) = 0,0 % dan P(≤−500) = 0,0 %**: tidak bergerak sama sekali, dan sebagian besarnya pasti
  tidak punya baris keluar. Fitur ini memisahkan "hidup" dari "kosong" sebelum kita bertanya arah.
- **Jarak dari puncak (breakout)** tetap masuk sebagai rem, bukan gas.
- **RSI** turun prioritas: di kohort tempat ia bisa dihitung (matang), mean-nya negatif dan
  tanda-nya berubah tiap horison.
- Dan yang paling penting: **teknik klasik tidak akan pernah teruji di kohort tempat harapan
  tinggal**, sampai pengukuran keluar diperbaiki. Urutan kerjanya jadi P33 → P32, bukan sebaliknya.

Baca ulang: `python -X utf8 tools/censor_bound.py` · `python -X utf8 tools/censor_bound.py --horizon 60` ·
`python -X utf8 tools/presence_ledger.py` (buku kehadiran) · `python -X utf8 universe/record_watch_prices.py --watch-min 120 --max-batches 40`

**Terkait:** [[06-Results/15 - Teknikal Klasik Diuji]] · [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] · [[06-Results/04 - Negative Results]] · [[03-Data/D2 - Wallet Flow]] ·
[[TradingKnowledge/EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] ·
[[TradingKnowledge/EV2 - Jebakan Backtest]] · [[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]]


---
tags: [tk-peta, hub]
---

# 00 - Hub Peta Fabius

**Sumber:** `vault/TradingKnowledge/07-Peta-Fabius/`

Lapisan tempat pengetahuan berubah jadi keputusan — atau berhenti. Enam lapisan lain boleh salah
hitung; halaman-halaman di sini tidak boleh, karena isinya dipakai untuk memilih pekerjaan
berikutnya dan untuk menolak pekerjaan yang menarik. Semua angkanya menunjuk
[[Fakta Terukur]]; semua nomor pekerjaannya menunjuk [[08-Backlog/01 - Backlog]].

Satu hal yang harus diketahui pembaca baru: **tenggat proyek ini 30 Sep 23:59 WIB.** Itu membuat
peran utama lapisan ini bukan "apa yang bisa kita bangun", tapi "apa yang harus kita tahan".

## Bagian

- [[GAP1 - Matriks Metode x Tahap]] — satu tabel untuk semua pertanyaan "metode X boleh dipakai
  Fabius tidak?", dengan kolom bayar (`nol`/`jam-proses`/`kalender`/`uang`/`mustahil`)
- [[GAP2 - Uji Setiap Veto Terhadap Hasil]] — tujuh ambang penyaring universe kita **diputuskan,
  bukan diuji**; rancangan uji yang menutup lubang itu tanpa beli data
- [[GAP3 - Yang Punya Data Tapi Belum Diuji]] — enam bahan yang sudah menetes di repo dan belum
  pernah ditanya apa pun; ini lubang malapraktik, bukan kekurangan data
- [[GAP4 - Yang Tidak Bisa Diuji Karena Data]] — mana yang terkunci oleh bidang/histori/definisi
  (T1/T2/T3), harganya, dan apakah menutupnya mengubah sebuah keputusan
- [[GAP5 - Urutan Kerja dan Bayarnya]] — P10 → P15, aturan pembagiannya, dan mana yang boleh
  dijanjikan dalam dua hari

## Bagaimana lapisan ini dipakai

1. Ambil sebuah ide metode → cari barisnya di [[GAP1 - Matriks Metode x Tahap]].
2. Kalau `Data: ADA` dan `Diuji: BELUM` → ia calon kerja nyata ([[GAP3 - Yang Punya Data Tapi Belum Diuji]]).
3. Kalau `TIDAK-ADA` → baca [[GAP4 - Yang Tidak Bisa Diuji Karena Data]] dulu; kebanyakan jalurnya
   `uang` atau `mustahil`, dan tidak satu pun mengubah keputusan arah.
4. Apa pun hasilnya, masuk backlog lewat [[GAP5 - Urutan Kerja dan Bayarnya]] — bukan lewat
   percakapan.

## Terkait

- [[00 - Hub Trading Knowledge]] · [[Fakta Terukur]] · [[Aturan Subtree]]
- [[08-Backlog/01 - Backlog]] (P10–P15) · [[00-Overview/06 - Roadmap]] ·
  [[00-Overview/03 - Decisions]] (`F-D##` untuk tiap perubahan urutan)
- [[06-Results/00 - Hub Results]] — tempat hasil uji mendarat, bukan di sini

```dataview
LIST FROM #tk-peta SORT file.name ASC
```

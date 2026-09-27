---
tags: [tk, tk-bukti, "EV4"]
---

# EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan

**Keluarga:** [[00 - Hub Bukti]] · **Tahap:** fetching ([[PL1 - Mengumpulkan Data]])
**Sumber:** perluasan [[Concepts/Point-in-Time vs Retro-updatable]] · [[03-Data/D2 - Wallet Flow]] · pengukuran di [[Fakta Terukur]] §B/§G

**Ringkas:** Halaman konsep menggambar garisnya; catatan ini menarik konsekuensi yang tidak disukai siapa pun: **sebagian metode trading tidak akan pernah bisa diuji surut di repo ini** — bukan karena kita belum sempat, tapi karena inputnya menguap sebelum "menyusulkan" punya arti. Bidang ⑦ adalah kasusnya: jendela lihat 8–13 menit, 100 transaksi per panggilan, paging diabaikan server. Yang lewat hilang, selamanya, tanpa alarm.

## Definisi yang bisa dihitung

| kelas | terkunci saat direkam? | peran dalam uji | contoh di repo |
|---|---|---|---|
| point-in-time | ya — commit server pihak ketiga, anchor chain, sha256 manifest | **boleh** jadi saksi waktu | ekor `universe/wallet-flow.jsonl` + manifest-nya |
| retro-updatable | tidak — baris bisa berubah saat diambil ulang | statistik boleh, saksi waktu **tidak** | Dune (`_updated_at`), API yang bisa di-rerun |
| tanpa riwayat | tidak ada rekaman = tidak ada kelas | tidak bisa diuji surut, selamanya | ⑦ sebelum 26 Sep 08:01Z; order book L2; funding historis |

```
uji-surut(metode m, waktu t) sah :=
    setiap field input m punya rekaman point-in-time dengan timestamp <= t
kalau tidak -> verdiknya "prospektif sejak <tanggal>", BUKAN "belum diuji"
```

Kenapa ⑦ tidak bisa disusulkan, semuanya terukur ([[Fakta Terukur]] §B): satu panggilan = 100 transaksi dalam jendela 8–13 menit; `offset`/`page`/`end_ts` diabaikan server (head sama, overlap 98/100). Tidak ada mekanisme "ambil kemarin". Satu jam tanpa perekam = satu jam riwayat yang tidak akan pernah ada.

Umur snapshot **ikut ter-hash**: "sedata-apa kita saat memutus" tersimpan di dalam `snapshotHash`, bukan cuma tercetak di layar ([[04-Tools/TL2 - direction]]) — keputusan di atas snapshot yang berumur **jam, bukan menit** tidak bisa kemudian diklaim seolah data segar. Manifest ⑦ mencatat `usia_aliran_jam` bersama sha256 berkas dan hash baris terakhir; umur ikut jadi bagian bukti, bukan catatan kaki ([[03-Data/D2 - Wallet Flow]]).

## Cara pakai yang diklaim

Cara mesin memakai lapisan ini: setiap field `## Butuh data` di catatan `03-Sinyal` dinilai lewat filter kelas ini — `ADA` tanpa kelas itu belum lengkap. Metode yang seluruh inputnya kelas "tanpa riwayat" tidak boleh dicatat sebagai PR ("belum diuji") — itu memalsukan janji bahwa kapan pun ada tangan, uji itu bisa jalan. Yang sah hanya: "prospektif sejak <tanggal>, verdik <tanggal>".

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| riwayat aliran ⑦ sebelum 26 Sep | `TIDAK-ADA` | terstruktur: jendela 8–13 menit, paging diabaikan ([[Fakta Terukur]] §B) |
| aliran ke depan | `ADA-TAPI` | point-in-time via `.github/workflows/`; tapi populasinya = pilihan pelabelan GMGN (0 dari 607 tx pertama bertag — §B) |
| L2, tick, funding historis, unlock/vesting, MVRV/SOPR/NUPL, exchange reserve | `TIDAK-ADA` | daftar tertutup di [[Fakta Terukur]] §C — keluarga V3/V4, U2/U3, O1/O2/O7 berhenti di T1 sampai ada rekaman |
| riwayat 90 hari whale untuk uji horison | `ADA-TAPI` | kelas retro (Dune): boleh jadi statistik, tidak jadi saksi waktu ([[Concepts/Point-in-Time vs Retro-updatable]]) |
| jsonl lokal sebagai keadaan sistem | `ADA-TAPI` | `git fetch` dulu — terukur lokal pernah 169 commit tertinggal, lalu 188 pada pembacaan berikutnya (§G menyimpan yang terakhir; riwayat angkanya ada di `09-Inbox/Session-2026-09-28`) |

## Uji di Fabius

Pemeriksaan kelas untuk sumber mana pun (dua pertanyaan, tanpa alat baru): (1) kalau kueri yang sama dijalankan besok bisa menghasilkan baris yang BERBEDA — itu kelas 2; (2) siapa yang men-stamp timestamp-nya — kalau bukan jam kita (commit `.github/workflows/`, blok chain), itu kelas 1. Orde rekaman vs hasil dibaca ulang dari chain tanpa kunci oleh `tools/anchor.py --verify` ([[Concepts/Anchored Before Outcome]]). Template uji-surut yang sah sudah ada: Uji A di [[06-Results/06 - Pre-registration Horizon]] — keanggotaan dicatat sebelum transaksinya, verdik terjadwal; satu-satunya jalur ke sana adalah perekam yang terus berdetak.

## Batas dan mode gagal

- **Merekam ≠ memahami:** 50.285 baris di ekor yang terukur bercerita tentang apa yang GMGN pilih tampilkan, bukan tentang pasar. Bias cakupan tidak bisa dikoreksi surut — justru sisi kontrasnya yang tidak pernah terekam.
- Rantai bisa putus tanpa bunyi: umur, ekor, dan `gap_since_prev_h` dicetak di manifest supaya diamnya perekam menjadi temuan, bukan asumsi ([[03-Data/D2 - Wallet Flow]]).
- Makin lama kita menunggu, makin kecil masa uji yang tersisa untuk kelas 1 — biaya penundaan perekaman tidak terlihat di PnL siapa pun, dan itulah kenapa ia gampang ditunda.
- Bahasa halus yang harus diwaspadai: "data nanti juga terkumpul" benar untuk kelas 2 dan salah total untuk kelas 1.

## Tingkat bukti

`T3` untuk semua angka di catatan ini (jendela, paging, overlap, ekor, umur snapshot — semua terukur oleh run kami sendiri, [[Fakta Terukur]] §B/§G). Ironi yang sengaja: catatan tentang keterbatasan riwayat ini berdiri di tangga tertinggi justru karena ia hanya menukil run — dan satu-satunya cara menaikkan apa pun darinya adalah menjalankan perekamnya, bukan menulis lebih banyak tentangnya.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "aliran yang kita rekam hari ini adalah satu-satunya riwayat aliran yang akan pernah ada di repo ini" · "metode yang butuh L2/tick/funding historis tidak akan pernah bisa diuji surut di sini — titik".
- **Dilarang:** "kami punya riwayat whale 90 hari" (90 hari itu Dune, kelas 2; riwayat kami sendiri mulai 26 Sep) · "pakai Dune saja buat merekonstruksi masa lalu, kan sama angkanya" · "angka di jsonl lokal adalah keadaan sistem" ([[Concepts/Stale Local Copy]]).

**Terkait:** [[Concepts/Point-in-Time vs Retro-updatable]] · [[Concepts/Stale Local Copy]] · [[Concepts/Anchored Before Outcome]] · [[03-Data/D2 - Wallet Flow]] · [[EV2 - Jebakan Backtest]] · [[EV5 - Reproduksibilitas dan Pra-Registrasi]] · [[GAP4 - Yang Tidak Bisa Diuji Karena Data]]

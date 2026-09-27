---
tags: [reference]
---

# Conventions

Aturan menulis & merawat vault ini. Strukturasnya meniru vault Lencana (`app/vault/Conventions.md`)
karena pola itu terbukti menahan kami dari klaim yang terlalu besar — **isinya** sama sekali tidak
ditiru.

## Dua aturan yang mengalahkan sisanya

1. **Satu angka hanya boleh masuk kalau ada perintah yang mencetaknya.** Tiap "lulus", jumlah,
   alamat, gas, atau tanggal harus bisa direproduksi dari dalam repo ini (`Fabius/`). Kalau
   halaman dan run terbaru berbeda, **run yang menang**: perbaiki halamannya, jangan kutip
   halamannya. Angka yang cuma bisa dibuktikan dari luar repo (laptop pribadi, folder riset lain)
   bukan klaim produk ini — dia masuk `09-Inbox/` dengan sumbernya, atau tidak masuk sama sekali.
2. **Tidak ada klaim yang boleh melebihi yang diukur.** [[10-Submissions/01 - Claims Cheat Sheet]]
   berisi kalimat yang kami larang untuk diri sendiri beserta pengganti jujurnya. Sebelum
   menulis README, slide, atau caption video, cek ke sheet itu.

## Turunan dari dua aturan itu

- **Setiap perintah Python di vault ditulis `python -X utf8 …`.** Bukan gaya: beberapa string yang
  dicetak perkakas (`①④⑥` di `direction.py`) ikut terserap `decisionHash`, jadi glyph-nya tidak
  boleh diganti, sementara cp1252 tidak mengenalnya. Tanpa mode utf8, `print` bisa melempar
  `UnicodeEncodeError` **di tengah** laporan — separuh tabel sudah tercetak dan terbaca sebagai hasil
  penuh. Lihat [[04-Tools/TL2 - direction]].
- **Perintah yang ditulis vault harus bisa dijalankan dari dalam clone.** Alat yang hidup di
  workspace (`_research/`) ditandai eksplisit sebagai *(workspace)* dan tidak dipakai sebagai bukti.
  Contoh nyata 27 Sep: audit vendor pindah dari `_research/vendored_x402.py` ke
  `tools/verify_vendor.py` supaya klaim "verifiable tanpa kami" tidak putus di jalur itu.
- **Skrip sekali-jalan diberi label di docstring-nya** (`migrate_vault.py`, `add_part_notes.py`,
  `archive_stubs.py`, `restore_hub_glosses.py`, `fix_mappings.py`). Dijalankan ulang di vault yang
  sudah rapi, skrip-skrip itu harus berhenti dengan peringatan — bukan menghasilkan duplikat.
- **Skrip perawatannya sendiri tunduk pada aturan yang sama.** `sync_vault.py` versi pertama
  menulis ulang daftar `## Bagian` dari nol dan menghapus penjelasan buatan tangan di 9 hub. Sejak
  itu ia append-only, dan pemulihannya tercatat di `scripts/restore_hub_glosses.py` supaya
  "alat kami merusak dokumen kami sendiri" tidak perlu ditemukan dua kali.

- **Gerbang bentuk, bukan hanya gerbang tautan.** `check_links.py` tetap melaporkan `Broken: 0` ketika `sync_vault.py` sedang menelan heading `## Terkait` di 11 hub: tautannya valid, tempatnya yang pindah. Karena itu ada `scripts/hub_shape.py` (exit non-zero kalau hub kehilangan `## Bagian` / `## Terkait` / `**Sumber:**` / blok dataview, atau ada baris tautan murni terseret ke daftar bagian) dan ia dijalankan setelah setiap perubahan alat.

## Beda sadar dari vault Lencana (dan alasannya)

| Lencana | Fabius | kenapa |
|---|---|---|
| catatan berbahasa Inggris | **berbahasa Indonesia**, istilah teknis/ID/nama error tetap Inggris | pembaca utama vault ini builder + agen sesi berikutnya, dan repo Fabius sendiri berbahasa Indonesia; memecah bahasa catatan dari bahasa repo membuat keduanya lebih sulit dibaca |
| `scripts/*.ps1` | `scripts/*.py` | PowerShell 5.1 di mesin ini pernah menanam BOM ke berkas Solidity dan solc menolaknya tanpa menyebut "BOM"; Python + `.gitattributes` lebih tahan |
| `D##` (keputusan) | `F-D##` | nomor dipakai bersama antar-proyek di workspace yang sama; tabrakan nomor sudah terjadi |

ID lain: `P#` backlog · `A#` agen · `C#` kontrak · `D#` data · `TL#` perkakas · `E#` ekosistem ·
`R#` hasil · `T#` testing · `OI-#` open item. **ID yang sudah dipakai tidak diganti**; bikin ID baru
tanpa menambah baris ke peta dokumen = cacat.

## Struktur

```
00-Overview/   produk, proses bisnis, keputusan, koreksi, cara menjalankan
01-Agent/      apa yang agen putuskan; gerbang; kelas aset; kursi
02-Contracts/  satu catatan per kontrak yang ter-deploy / akan di-deploy
03-Data/       perekam, kedalaman harga, Dune, integritas dataset
04-Tools/      satu catatan per perkakas + apa yang ia TIDAK boleh lakukan
05-Ecosystem/  identitas 8004, pembayaran x402, penemuan antar-agen
06-Results/    ambang, angka, hasil negatif, pra-registrasi
07-Testing/    rumah semua angka: perintah + keluaran
08-Backlog/    sisa kerja + acceptance criteria per item
09-Inbox/      catatan sesi bertanggal (mentah, belum terstruktur)
10-Submissions/ kalimat klaim, alamat, angka publik
Concepts/      catatan konsep atomik (#concept)
Templates/     kerangka halaman
scripts/       sync_vault.py, check_links.py, new_note.py
```

## Penamaan

- folder modul: `NN-Nama`; hub: `NN - Judul.md`; part note: `<Prefix><k> - Judul.md`
  (nomor urut **per kelompok**, jangan direset per berkas).
- nama berkas tanpa `: \ / | ? * " < >`, tanpa emoji (tautan & git rusak); emoji di heading boleh.
- **`[[wikilink]]`** untuk antar-halaman; **inline code path** untuk kode/konfig/out-build;
  markdown biasa untuk URL eksternal. Repo-relative, jangan absolut (`C:\...` hanya bekerja di
  satu mesin di dunia).

## Format part note

Frontmatter `tags` (kategori + identitas, mis. `tags: [kontrak, "C2"]`), lalu
`**Bagian dari:**`, `**Sumber:**`, `**Ringkasan:**`, `**Poin kunci:**`, `**Detail:**`,
`**Terkait:**`. Untuk dokumen per-item wajib ada **baris peta** yang menunjuk saudaranya.

## Perawatan

- Setelah menambah/mengganti nama halaman: `python -X utf8 -u scripts/sync_vault.py` lalu
  `python -X utf8 -u scripts/check_links.py` → target **`Broken: 0`**.
- `_Auto-Index.md` jangan disunting manual (dibangkitkan).
- Halaman lama yang digantikan tidak dihapus diam-diam: dipindah + banner
  `⚠️ DIARSIPKAN — lihat <halaman baru>` di kepala, atau isinya dipindah di commit yang sama.
- Koreksi tetap terlihat. Kalau ada klaim sebelumnya yang salah, tulis apa yang salah dan apa yang
  membuktikannya ([[00-Overview/05 - Corrections]]) — jangan sunting sejarah jadi rapi.
- Catatan sementara masuk `09-Inbox/` dengan awalan tanggal
  (`Session-2026-09-27.md`, `Status-2026-09-27.md`).
- Jebakan yang sudah menghantam vault ini (kode yang tertulis sebagai fakta tapi tidak diverifikasi,
  salinan lokal dianggap keadaan sistem) dicatat di [[Concepts/Stale Local Copy]] — baca sebelum
  menyimpulkan "mati" dari satu sumber.

Lihat: [[Index]] · [[Quick-Reference]] · [[Dashboard]] · [[START-HERE]]

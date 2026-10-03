---
tags: [perkakas, "TL16"]
---

# TL16 - pin_book

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/pin_book.py`

**Ringkas:** mem-pin `book_sha` epoch terakhir buku slot hidup ([[03-Data/D8 - Buku Slot Hidup]]) ke [[02-Contracts/C6 - LockRegistry]] dengan label
`FABIUS-BUKU-E<epoch>`. Jam blok membuktikan susunan buku pada epoch itu sudah ada saat itu.

**Poin kunci:**
- Buku diverifikasi dulu (rantai + keputusan dihitung ulang); buku yang tidak sah tidak di-pin.
- Bawaan rencana; `--verify` membaca ulang; `--send` SATU `lock()` dari committer (alamat harus `m3.committer`); idempoten.
- uri = berkas buku pada commit HEAD - push dulu.

**Yang ia TOLAK lakukan:** mem-pin buku tanpa catatan epoch atau buku yang tidak sah; mengirim dari alamat selain committer; mencetak kunci.

**Detail:** epoch 690: tx `0x2d6b96726f…`, blok 134477804, gas 122.954, `lockedAt` 2026-10-02T17:26:09Z (F-D85).

**Sejak 3 Okt (P108):** fungsi `last_epoch` / `locked_at` / `lock_calldata` / `book_uri` dipakai juga oleh worker Railway (`operator_loop.Worker.book_pin`), yang mem-pin epoch baru sendiri. CLI ini tetap dipakai untuk pin manual, `--verify`, dan mencatat `m3.pins` (worker tidak bisa menulis repo). Log worker sesudah deploy: 05:34:08Z `buku FABIUS-BUKU-E690 sudah di-pin (lockedAt 2026-10-02T17:26:09Z, book_sha 0xfe37d7595644…)`, nol transaksi; detak `repo cccbc3cef4 | saldo committer 0.049508 tBNB`.

**Terkait:** [[TL15 - lock_spec]] · [[TL8 - engine]] · [[00-Overview/03 - Decisions]] F-D85

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

**Terkait:** [[TL15 - lock_spec]] · [[TL8 - engine]] · [[00-Overview/03 - Decisions]] F-D85

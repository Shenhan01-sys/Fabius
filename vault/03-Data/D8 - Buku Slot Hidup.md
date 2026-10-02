---
tags: [data, "D8"]
---

# D8 - Buku Slot Hidup

**Bagian dari:** [[03-Data/00 - Hub Data]]
**Sumber:** `ledger/book/buku.jsonl`, `ledger/book/laporan/*.json`, `engine/book_live.py`, `engine.cli book epoch|verify`

**Ringkas:** siapa memegang slot paper Fabius, dan kenapa, per epoch 30 hari. Append-only, berantai hash; tiap catatan epoch membawa semua masukan keputusannya
sehingga keputusan bisa dihitung ulang siapa pun tanpa data pasar.

**Poin kunci:**
- **Isi:** `genesis` (buku awal B1-TREND identitas; sha kunci v1) lalu `epoch`: skor maju penghuni, penantang (shadow, berpasangan, vonis gerbang + `report_sha`),
  status pembunuh, keputusan, buku hasil, `book_sha`.
- **Siapa yang bisa membantah:** `python -X utf8 -m engine.cli book verify` (keputusan dihitung ulang dari masukan); laporan gerbang di `laporan/` dapat dihitung
  ulang dari `ledger/bars` dengan `engine.cli gate`; `book_sha` tiap epoch di-pin di chain ([[04-Tools/TL16 - pin_book]]).
- **Keadaan 3 Okt WIB:** 2 catatan (genesis + epoch 690); buku = B1-TREND saja; B3-CARRY ditolak karena shadow 0 hari < 60; `book_sha` `0xfe37d7595644fd7e…`.

**Detail:** penulis sementara manual (P108 = jadwal bulanan); pembunuh bot Fabius masih teks (P107).

**Terkait:** [[03-Data/D7 - Ledger Bars]] · [[04-Tools/TL8 - engine]] · [[00-Overview/03 - Decisions]] F-D85

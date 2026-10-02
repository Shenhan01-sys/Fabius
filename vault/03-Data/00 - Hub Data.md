---
tags: [data, hub]
---

# Data

**Sumber:** `03-Data/`

Sumber data dan batas masing-masing. Yang membedakan vault ini: setiap halaman data menyebut
**kedalaman** (bisa ditarik mundur berapa lama?) dan **siapa yang bisa membantahnya**. Data yang
hanya maju (aliran wallet) diperlakukan sebagai aset yang bisa hilang — karena memang bisa.

## Bagian

- [[D2 - Wallet Flow]] — ⑦: jendela 8–13 menit, tanpa paging, rantai dispatch-diri (**DIHENTIKAN 2 Okt, F-D81**)
- [[D3 - Price Depth]] — Aster 9.599 bar vs GMGN 41,6 hari vs GeckoTerminal
- [[D4 - Dune]] — dialek Trino, kredit terukur, lag BSC ±1 jam
- [[01 - Dataset]] — universe point-in-time, sha256 per baris, manifest & gap
- [[D5 - Record Schemas]] — field tiap rekaman + riwayat skema 1→4; tanpa ini hash tidak bisa dihitung ulang orang lain
- [[D6 - Funding and OI History]] — histori funding (OKX 97,7 hari · Bybit 66,3, per 8 jam) + OI
  Binance 20,8 hari per 1 jam, 5.963 baris tanpa kunci; ini yang membuat veto funding bisa diuji
- [[D7 - Ledger Bars]] — bar harian Binance (perp + spot) + funding 16 aset untuk ledger paper; REST = Vision untuk harga dan funding (F-D83)
- [[D8 - Buku Slot Hidup]] — siapa memegang slot paper per epoch 30 hari, keputusan dapat dihitung ulang; `book_sha` di-pin LockRegistry (F-D85)

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #data SORT file.name ASC
```

## Terkait

- [[Quick-Reference]] · [[Index]] · [[Conventions]]


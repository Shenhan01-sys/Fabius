---
tags: [data, hub]
---

# Data

**Sumber:** `03-Data/`

Sumber data dan batas masing-masing. Yang membedakan vault ini: setiap halaman data menyebut
**kedalaman** (bisa ditarik mundur berapa lama?) dan **siapa yang bisa membantahnya**. Data yang
hanya maju (aliran wallet) diperlakukan sebagai aset yang bisa hilang — karena memang bisa.

## Bagian

- [[D2 - Wallet Flow]] — ⑦: jendela 8–13 menit, tanpa paging, rantai dispatch-diri
- [[D3 - Price Depth]] — Aster 9.599 bar vs GMGN 41,6 hari vs GeckoTerminal
- [[D4 - Dune]] — dialek Trino, kredit terukur, lag BSC ±1 jam
- [[01 - Dataset]] — universe point-in-time, sha256 per baris, manifest & gap
- [[D5 - Record Schemas]] — field tiap rekaman + riwayat skema 1→4; tanpa ini hash tidak bisa dihitung ulang orang lain
- [[D6 - Funding and OI History]] — histori funding (OKX 97,7 hari · Bybit 66,3, per 8 jam) + OI
  Binance 20,8 hari per 1 jam, 5.963 baris tanpa kunci; ini yang membuat veto funding bisa diuji

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #data SORT file.name ASC
```

## Terkait

- [[Quick-Reference]] · [[Index]] · [[Conventions]]


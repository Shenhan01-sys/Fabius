---
tags: [data, hub]
---

# Data

Sumber data dan batas masing-masing. Yang membedakan vault ini: setiap halaman data menyebut
**kedalaman** (bisa ditarik mundur berapa lama?) dan **siapa yang bisa membantahnya**. Data yang
hanya maju (aliran wallet) diperlakukan sebagai aset yang bisa hilang — karena memang bisa.

## Bagian

- [[D2 - Wallet Flow]] — ⑦: jendela 8–13 menit, tanpa paging, rantai dispatch-diri
- [[D3 - Price Depth]] — Aster 9.599 bar vs GMGN 41,6 hari vs GeckoTerminal
- [[D4 - Dune]] — dialek Trino, kredit terukur, lag BSC ±1 jam
- [[01 - Dataset]] — universe point-in-time, sha256 per baris, manifest & gap
- [[D5 - Record Schemas]] — field tiap rekaman + riwayat skema 1→4; tanpa ini hash tidak bisa dihitung ulang orang lain

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->

```dataview
LIST FROM #data SORT file.name ASC
```


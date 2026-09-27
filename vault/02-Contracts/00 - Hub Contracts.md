---
tags: [kontrak, hub]
---

# Contracts

**Sumber:** `02-Contracts/`

Kontrak yang benar-benar ada (atau akan di-deploy) di BNB Chain testnet 97. Satu catatan per
kontrak: apa yang ia tegakkan di byte-code, apa yang ia **tolak** lakukan, dan perintah untuk
membacanya sendiri. Angka gas di sini berasal dari receipt, bukan dari perkiraan.

## Bagian

- [[C3 - ExecutionVault]] — posisi nyata: plafon $5/hari, hash wajib, realized PnL
- [[C5 - Vendored x402 Sources]] — verbatim + sha256, dan kenapa tidak dikompilasi
- [[01 - DecisionAnchor]] — roster agen, verdict, hash; 21 test
- [[02 - Deployed on 97]] — alamat, biaya nyata, verifikasi chain, trail 17 anchor
- [[C4 - DemoPair and DemoAsset]] — venue x·y=k dan kenapa kami bikin sendiri

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #kontrak SORT file.name ASC
```

## Terkait


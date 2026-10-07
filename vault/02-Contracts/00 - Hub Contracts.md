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
- [[C6 - LockRegistry]] — pra-registrasi spesifikasi per pengunci, ditulis sekali; ter-deploy 2 Okt (M3)
- [[C7 - SignalAnchor]] — komit-ungkap sinyal per bot per bar; ter-deploy 2 Okt, menunggu komit pertama
- [[C8 - ExecutionAnchor]] — catatan isi order venue (uang nyata) per komit SignalAnchor; menolak order yang mengaku dikirim sebelum komit (R-E1 di chain)
- [[C9 - BotRegistry]] — daftar bot penerbit + pabrik splitter (CREATE2); transisi status wajib menunjuk laporan yang di-pin; ditulis + diuji lokal, BELUM di-deploy (P81)
- [[C10 - RevenueSplitter]] — `payTo` per bot, bagi hasil 60/40 persis `economics.split`, pull, bagian Fabius hanya turun; ditulis + diuji lokal, BELUM di-deploy (P81)

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #kontrak SORT file.name ASC
```

## Terkait


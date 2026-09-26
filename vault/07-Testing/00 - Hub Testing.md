---
tags: [testing, hub]
---

# 07 - Testing

**Sumber:** `test/`, `tools/`, `vault/scripts/`

Rumah resmi setiap angka. Empat hal yang membuat folder ini bukan brosur: tiap angka menyebut
**perintah** yang mencetaknya, tiap halaman menulis **apa yang tidak dibuktikannya**, keluaran
ditempel mentah (tidak dirapikan), dan tidak ada halaman yang boleh menyebut "lulus" tanpa run
tanggal yang sama. Kalau run hari ini berbeda dari halaman kemarin, **run hari ini yang benar** —
halaman itu yang diperbaiki.

Yang tidak tinggal di sini: keputusan produk (`00-Overview`) dan hasil pasar (`06-Results`). Halaman
hasil boleh **mengutip** angka dari sini, tidak pernah menghitung ulang.

## Bagian

- [[01 - Test Commands]] — registry 8 perintah + jumlah terukur 27 Sep (39 default / 63 fork)
- [[T2 - Anchor Verify]] — trail dibaca ulang dari chain tanpa kunci & tanpa gas: 11/11 cocok
- [[T3 - Execution Suite]] — 18 test jalur eksekusi: plafon dipotong, bukan diminta izin
- [[T4 - x402 Fork Suite]] — 9 test terhadap proxy kanonis yang ter-deploy di 97
- [[T5 - Integrity Harness]] — check_links / vendor / manifest / check_garbled: kesehatan dokumen
- [[06-Results/00 - Hub Results]] · [[Quick-Reference]] · [[Conventions]]

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->

```dataview
LIST FROM #testing SORT file.name ASC
```


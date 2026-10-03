---
tags: [ekosistem, hub]
---

# BNB Ecosystem

**Sumber:** `05-Ecosystem/`

Jawaban atas pertanyaan "di mana BNB-nya?" — bukan "kita pakai data BSC", tapi partisipasi di rel
agen BNB Chain: identitas (ERC-8004), pembayaran (x402), dan eksekusi (kontrak kami di 97).
Setiap halaman di sini menyebut apa yang **belum**: hosting endpoint, penemuan oleh agen asing.

## Bagian

- [[01 - ERC-8004 Identity]] — tokenId 2494, diverifikasi dengan membaca registry
- [[02 - x402 Payment]] — transaksi nyata, klien nol gas, saldo dibaca dari chain
- [[03 - Discovery Gap]] — bagaimana agen lain menemukan kami (dan apa yang belum bisa)
- [[04 - Alchemy]] — dinilai 4 Okt: RPC chain 97 cadangan (getLogs gratis hanya 10 blok), dompet pintar + sponsor gas BNB untuk kelak; sisanya tidak dibutuhkan

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #ekosistem SORT file.name ASC
```

## Terkait

- [[Quick-Reference]] · [[Index]] · [[Conventions]]


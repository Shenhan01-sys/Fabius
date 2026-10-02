---
tags: [agen, hub]
---

# Agent

> **BN-PIVOT - 2 Okt 2026.** Arah proyek bergeser: Fabius menjadi **operator pemilih bot** yang kelak menjual **sinyal
> berbukti** dan membuka slot bot untuk penerbit luar ([[00-Overview/03 - Decisions]] F-D70 dan F-D71). Halaman ini
> menggambarkan keadaan **sebelum** pivot dan tetap benar untuk apa yang **sudah dibangun**; arah baru masih **usulan dan kode
> awal** ([[08-Backlog/05 - Epik Enam Bot]], [[08-Backlog/06 - Epik Gerbang Sinyal]], [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]]).
> Jangan memakai halaman ini untuk menyangkal arah baru, dan jangan menyebut arah baru sebagai fitur yang sudah ada.

**Sumber:** `01-Agent/`

Alur keputusan agen: rekam → saring → putuskan → anchor → nilai. Prinsip yang menahan semuanya:
**gerbang hanya boleh mengurangi** — tidak ada komponen (model, ④, kursi) yang bisa membuka posisi
yang ditolak gerbang lain. Yang TIDAK dilakukan agen: menyimpan dana siapa pun, menandatangani
order nyata ke venue utama, menjanjikan return.

## Bagian

- [[A2 - Decision Spine]] — rekam → gerbang → hash → anchor → ledger
- [[A3 - One-Way Gates]] — doktrin satu-arah dan di mana saja ia ditegakkan
- [[01 - Asset Classes and Seats]] — 7 bidang data, 8 kelas aset, 5 kursi + rotasi
- [[A4 - Trust Gating and Real-Money Rules]] — kapan agen boleh menyentuh uang, berapa, dan kenapa metriknya harapan bersih bukan win-streak

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #agen SORT file.name ASC
```

## Terkait

- [[Quick-Reference]] · [[Index]] · [[Conventions]]


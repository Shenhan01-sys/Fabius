---
tags: [perkakas, hub]
---

# Tools

**Sumber:** `04-Tools/`

Satu catatan per perkakas: apa yang ia cetak, apa yang ia **tolak** lakukan, dan bug yang sudah
pernah ia hasilkan. Kaidah yang diulang di semua halaman sini: alat yang gagal diam-diam lebih
berbahaya dari alat yang gagal keras.

## Bagian

- [[TL1 - judge]] — penilai LLM, veto satu-arah, `ask_jev`
- [[TL2 - direction]] — side/entry/stop/ukuran/horizon; dua rezim keluar
- [[TL3 - security_gate]] — 4 status; `UNMEASURED` bukan `bersih`
- [[TL4 - anchor and verify]] — trail on-chain; `getAnchor` kembalikan struct nol
- [[TL5 - ledger]] — event-level dedupe, `AMBIGU`, belum jatuh tempo ≠ hasil
- [[TL6 - x402 gate and client]] — bentuk wire dari specs, status lokal
- [[TL7 - measurement harness]] — backtest · whale_sweep · flow_test, dan pager statistik
- [[TL8 - engine]] — mesin bot operator (M1): enam bot, spesifikasi ber-sha, sinyal = niat posisi, keccak/Merkle stdlib
- [[TL9 - ledger paper maju]] — M2: tick ex-ante ≤ 12 jam, gap tidak diisi, settle lewat replay yang sama; rantai GitHub penulis tunggal
- [[TL10 - kunci dan anchor kunci]] — kunci ambang v1 + satu baris DecisionAnchor; `--verify` tanpa kunci
- [[TL11 - komit sinyal M3]] — worker Railway: hitung ulang tick dari bar, komit akar Merkle, ungkap; menolak yang tak bisa direproduksi
- [[TL12 - m3_setup]] — deploy M3 + committer + kunci spesifikasi; dijalankan builder; gladi di anvil
- [[TL13 - rest_vs_vision]] — uji kesamaan REST Binance vs `ledger/bars` dari Singapura (job `fabius-probe`)

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #perkakas SORT file.name ASC
```

## Terkait


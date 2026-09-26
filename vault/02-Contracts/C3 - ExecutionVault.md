---
tags: [kontrak, "C3"]
---

# C3 - ExecutionVault

**Bagian dari:** [[02-Contracts/00 - Hub Contracts]]
**Sumber:** `contracts/ExecutionVault.sol`, `test/ExecutionVault.t.sol` (18 test lulus)

**Ringkas:** pencatat posisi yang **dieksekusi** lewat pool. Harga masuk/keluar datang dari hasil
swap, bukan dari angka yang agen tulis; PnL dibukukan di kontrak dan boleh negatif.

**Poin kunci:**
- `openLong(asset, quoteIn, decisionHash, snapshotHash)` / `openShort(asset, assetQty, …)` /
  `close(asset)`; posisi keyed per aset token; satu posisi per aset (`AlreadyOpen`).
- Hanya `agent` yang bisa buka/tutup → `NotAgent`; **owner tidak punya jalan pintas** (teruji).
- Plafon: `dailyCap` (default 5 unit), `maxPositionQuote` (1 unit), `HARD_CEILING = 10` — owner
  menaikkan ke 1.000 tetap dipotong ke 10 (teruji: `dailyCap() == 10`).
- `NoAnchorHash`: posisi **tidak bisa lahir** dari keputusan yang tidak di-anchor.
- Short = jual inventaris sendiri, beli kembali saat menutup → `NeedInventory` kalau tidak ada.
  Konsekuensi: saldo quote vault memang **turun** saat menutup short yang untung; ukuran PnL adalah
  `realizedQuote`, bukan saldo (kesalahan konsep yang sempat bikin tesku salah, lalu kucatat).
- Gas dipakai per panggilan dihitung di kontrak (`startGas - gasleft()`) dan ikut di event
  `Closed` — bukan `gasleft()` mentah yang bukan biaya.
- Reset plafon harian terjadi **sebelum** pemeriksaan budget. Bug urut ini ditemukan test, dan
  sekarang ada test sendiri yang memegangnya.

**Detail:** bug yang sudah dikoreksi dicatat di komentar kontrak (bukan dihapus) supaya pembaca
mengerti kenapa urutannya penting. Deploy & posisi nyata: [[08-Backlog/01 - Backlog]] P1.

**Terkait:** [[02-Contracts/C4 - DemoPair and DemoAsset]] · [[Quick-Reference]]

---
tags: [ekosistem, "E2"]
---

# 02 - x402 Payment

**Bagian dari:** [[05-Ecosystem/00 - Hub BNB Ecosystem]]
**Sumber:** `04-Tools/TL6`, `07-Testing/T4`, `docs/upstream-x402/`

**Ringkas:** agen membayar agen lain di BNB Chain lewat relasi pembayaran kanonis — dan bukti yang
kita punya adalah transaksi, bukan screenshot.

**Poin kunci:**
- Terjadi nyata di 97: tx `0xb6093e59…` `status=1`, gas 114.930; klien (0 BNB) menandatangani,
  fasilitator membayar gas, token demo `0xB11D9021…` berpindah **tepat** 1.000 atomic = tagihan.
- Sifat paksaannya dibuktikan di level kontrak (**9 fork test** terhadap proxy ter-deploy,
  [[07-Testing/T4 - x402 Fork Suite]]): pemanggil
  `settle()` tidak bisa memindahkan dana ke alamat lain, tidak bisa melebihkan jumlah, dan nonce
  tidak bisa dipakai ulang.
- Yang **belum**: jalur HTTP-nya berjalan di mesin kami dan hanya pelanggan kami sendiri program
  kami. Tidak ada pelanggan eksternal; jangan tulis "sudah dipakai agen lain".
- Perbandingan dengan proyek lain kami tidak dilakukan: Lencana memakai x402 untuk hal yang
  berbeda; keduanya sah, dan tidak saling meminjam klaim.

**Terkait:** [[04-Tools/TL6 - x402 gate and client]] · [[08-Backlog/01 - Backlog]] P2

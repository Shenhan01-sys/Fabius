---
tags: [perkakas, "TL6"]
---

# TL6 - x402 gate dan client

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/x402_gate.py`, `tools/x402_client.py`, `tools/x402_deploy.py`

**Ringkas:** server yang menagih dan klien agen yang membayar — keduanya milik kami, dan itu
dinyatakan sebagai bagian dari klaim, bukan disembunyikan.

**Poin kunci:**
- Bentuk wire diambil dari **specs pada commit yang sama dengan vendor kami** (`dd927a26…`), bukan
  dari tebakan: v2 memakai header `PAYMENT-REQUIRED` / `PAYMENT-SIGNATURE` / `PAYMENT-RESPONSE`
  (v1 `X-PAYMENT*`; keduanya diterima supaya klien lama tidak buta).
- Klien menandatangani **dua** EIP-712 authorization (Permit2 witness + EIP-2612 permit) dan tidak
  pernah mengirim transaksi; fasilitator (server) yang memanggil `settleWithPermit` di proxy
  kanonis `0x402085c2…`.
- Satu tempat contoh spec dan kontrak kanonis **bertentangan**: spec menulis `MaxUint256` untuk
  EIP-2612, sementara `settleWithPermit` me-revert `Permit2612AmountMismatch` kalau jumlah permit ≠
  tagihan. Perilaku kontrak yang menang, dan alasannya ditulis.
- Pembuktian bukan dari log server: tx, `status`, dan `balanceOf` dibaca ulang dari chain
  (pembeli 5.000.000 → 4.999.000 atomic = tepat tagihan; `payTo` 999.990,001 = 1.000.000 − 10 + 0,001).
- Jam: `validAfter` memakai jam laptop, proxy membandingkan ke `block.timestamp` → revert tanpa
  pesan. Perbaikan `now - X402_SKEW` (15 s) dengan alasannya, bukan angka keberuntungan.
- **Status sekarang: endpoint di `127.0.0.1`, dan `agent-card.json` menuliskannya apa adanya.**
  Lihat [[05-Ecosystem/03 - Discovery Gap]].

**Terkait:** [[05-Ecosystem/02 - x402 Payment]] · [[02-Contracts/C5 - Vendored x402 Sources]]

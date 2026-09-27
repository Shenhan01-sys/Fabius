---
tags: [concept, "cost-is-fixed"]
---

# Cost Is Fixed — ongkos tidak ikut mengecil saat modalmu mengecil

**Ringkas.** Fee, gas, dan slippage itu **per transaksi**. Kalau posisi diperkecil, biaya tidak
mengecil — porsinya **membesar**. Ini alasan ukuran $0,5–1 kalah sebelum sinyalnya dinilai.

**Angka yang kami punya (terukur, bukan estimasi):**

| hal | angka | dari |
|---|---|---|
| biaya round-trip venue demo, posisi 1 unit | **59 bps** | `test_round_trip_...` (forge) |
| ongkos yang dipakai semua uji kami | **20 bps RT** (5,5 taker + 4,5 spread/slip per sisi) | `06-Results/02` |
| gate kasar | gross harus > **40 bps** supaya net > 0 | `06-Results/02` |
| gas nyata `openLong` di 97 | **258.008 / 295.443 gas** (±0,00003 tBNB @ 0,1 gwei) | `execute_live.py --open-long` |
| gas nyata `close` di 97 | **123.216 / 150.576**; kontrak membukukan `gasUnitsPaid` 127.213 / 161.413 di event | `execute_live.py --close` |
| realized round-trip nyata | **−59 bps** per putaran, pada posisi 1 unit | event `Closed` (bukan hitungan kami) |

**Konsekuensi yang kami ambil.** Karena biaya tetap, pertanyaan pertama sebelum membicarakan sinyal
adalah "pada ukuran berapa ongkos masih masuk akal". Menjalankan $5/hari di atas sinyal yang kami
sendiri ukur negatif akan menghasilkan kurva kerugian yang rapi, bukan bukti.

Lihat: [[02-Contracts/C4 - DemoPair and DemoAsset]] · [[06-Results/02 - Thresholds]]

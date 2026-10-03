---
tags: [concept, "cost-is-fixed"]
---

# Cost Is Fixed — ongkos tidak ikut mengecil saat modalmu mengecil

> **BN-ONGKOS - 3 Okt 2026 (P76).** "59 bps" = ongkos pulang-pergi yang kami UKUR di pool demo kami sendiri (DemoPair: fee 30 bps/sisi + dampak
> x·y=k, `tools/costs.py`). Itu BUKAN ongkos venue perp: bot operator memakai penggaris spesifikasinya (mis. B1: 7 bps/sisi + funding nyata;
> penggaris per venue = P69, belum). Dan "gross harus > 118 bps" (2x ongkos) adalah salah turunan: 59 bps pulang-pergi SUDAH memuat kaki masuk
> DAN keluar, jadi net > 0 cukup dengan gross > 59. Angka 2x tetap dipakai alat lama supaya uji yang sudah dikunci tidak bergeser ([[00-Overview/05 - Corrections]]).

**Ringkas.** Fee, gas, dan slippage itu **per transaksi**. Kalau posisi diperkecil, biaya tidak
mengecil — porsinya **membesar**. Ini alasan ukuran $0,5–1 kalah sebelum sinyalnya dinilai.

**Angka yang kami punya (terukur, bukan estimasi):**

| hal | angka | dari |
|---|---|---|
| biaya round-trip venue demo, posisi 1 unit | **59 bps** | `test_round_trip_...` (forge) |
| **ongkos yang dipakai semua uji kami sekarang** | **59 bps RT** — default `tools/costs.py`, override tercatat `cli-override` | `python -X utf8 tools/costs.py` (P10 ditutup 28 Sep) |
| ongkos yang dipakai uji sebelum 28 Sep | 20 bps RT (5,5 taker + 4,5 spread/slip per sisi) — **asumsi warisan**, kini tinggal label | `06-Results/02`, [[06-Results/04 - Negative Results]] §5b |
| gate kasar | gross harus > **118 bps** (= 2 × 59) supaya net > 0; dulu > 40 bps pada asumsi 20 | `tools/costs.py::gate_gross_bps` |
| gas nyata `openLong` di 97 | **258.008 / 295.443 gas** (±0,00003 tBNB @ 0,1 gwei) | `execute_live.py --open-long` |
| gas nyata `close` di 97 | **123.216 / 150.576**; kontrak membukukan `gasUnitsPaid` 127.213 / 161.413 di event | `execute_live.py --close` |
| realized round-trip nyata | **−59 bps** per putaran, pada posisi 1 unit | event `Closed` (bukan hitungan kami) |

**Konsekuensi yang kami ambil.** Karena biaya tetap, pertanyaan pertama sebelum membicarakan sinyal
adalah "pada ukuran berapa ongkos masih masuk akal". Menjalankan $5/hari di atas sinyal yang kami
sendiri ukur negatif akan menghasilkan kurva kerugian yang rapi, bukan bukti.

Lihat: [[02-Contracts/C4 - DemoPair and DemoAsset]] · [[06-Results/02 - Thresholds]]

---
tags: [data, "D4"]
---

# D4 - Dune (riwayat wallet & agregat aliran)

**Bagian dari:** [[03-Data/00 - Hub Data]]
**Sumber:** `tools/whale_sweep.py`, `_research/probe_dune_*.py`, `_research/diag_*.py`

**Ringkas:** Dune memberi kami hal yang GMGN tidak bisa: **masa lalu**. Dan mengambil kredit sebagai
gantinya. Halaman ini berisi angka API yang terukur, karena tiga asumsiku tentang API ini salah.

**Poin kunci:**
- Populasi terukur: `dex.trades` `blockchain='bnb'` = **5.274.783 swap dalam 1 jam terakhir**;
  205.875 swap / 20.607 wallet di jam penuh terakhir.
- **Lag ±1 jam** (jam berjalan cuma 18 swap vs jam penuh 205.875) → Dune **bukan** jalur keputusan
  untuk horizon 4 jam; dia jalur sejarah/kelompok.
- Kredit **bisa dibaca**: `execution_cost_credits` di endpoint status. Terukur: agregat 90 hari
  dengan join `tokens.erc20` = **1,259 kredit / ±11 detik**. Bandingkan dengan kueri yang
  **mengirim baris**: 10 hari = 503 detik — yang mahal itu mengangkut baris, bukan berpikir.
- Dialek = **Trino**: `now()` ya; `current_timestamp()` **tidak**; `INTERVAL '1' DAY` (berkutip).
- **`from_hex('0x…')` tidak error — hanya tidak pernah cocok.** Ini yang membuat kueri pertamaku
  membalas 0 baris dan nyaris kusimpulkan "whale tidak trading". Semua sisi heks dinormalisasi +
  assert panjang 40.
- Paginasi: **tidak ada `next_offset`**; geser `offset` sendiri dan berhenti pada
  `total_row_count`. `limit=5000` membuat respons tanpa `rows` (kubaca salah sebagai
  "[TERPOTONG]"); pakai 1000.
- Kolom: `token_bought_address`/`token_sold_address`/`taker` (varbinary), `amount_usd`,
  `block_time`, plus join `tokens.erc20.symbol`. Nama yang kukarang (`token_bought`) tidak ada.
- Batas metodologis: barisnya punya `_updated_at` → masa lalunya bisa disusulkan. Jadi Dune sah
  untuk **statistik**, tidak sah jadi **saksi waktu** (saksi waktu tetap commit Actions + anchor).

**Terkait:** [[06-Results/06 - Pre-registration Horizon]] · [[Concepts/Point-in-Time vs Retro-updatable]]

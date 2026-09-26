---
tags: [data, "D3"]
---

# D3 - Price Depth per Sumber

**Bagian dari:** [[03-Data/00 - Hub Data]]
**Sumber:** `tools/bars.py`, `universe/record_bsc_universe.py`

**Ringkas:** "seberapa jauh ke belakang kita bisa menghargai sebuah aset sendiri" menentukan apa
yang boleh diuji sama sekali. Angkanya diukur dengan menarik, bukan membaca dokumen.

**Poin kunci:**

| sumber | kedalaman | kunci | peran |
|---|---|---|---|
| Aster `fapi/v1/klines` (BNB-native perp) | **9.599 bar 1 jam ≈ 400 hari** | tanpa API key | harga forward untuk backtest & penilaian ⑦ |
| Hyperliquid `candleSnapshot` | 5.001 bar ≈ 208 hari | tanpa key | pembanding silang (chain sendiri, bukan BNB) |
| GMGN `token_kline` | mentok 1.000 bar ≈ 41,6 hari; **0 bar untuk token gas** | privat | tidak cukup untuk walk-forward |
| GeckoTerminal pools | 1.000 bar; pool baru ±30 bar | demo/privat | universe & likuiditas, bukan deret |

- Kapasitas server: **1.500 bar/panggilan** (limit 3.000/5.000 ditolak `code -1130`); kedalaman
  didapat dari **paging**, bukan dari satu permintaan besar.
- Cache per (simbol, interval) + meta (endpoint, halaman, sha256) supaya "data dari mana" bukan
  pertanyaan terbuka. `save()` memaksa meta lengkap **dan menandai pertentangan internal**
  (pernah: klaim `pages: 1` untuk deret 7 halaman).
- Ambang yang mengikat: `NEED_BARS=2400` (5-fold walk-forward), `MIN_BARS_TINY=720` (30 hari =
  layak dinilai, tidak layak diklaim sebagai edge).
- Batas yang harus ikut disebut: yang bisa kami hargai sendiri cuma aset **ber-kontrak perp** →
  ada survivorship di setiap uji ⑦ (lihat `06-Results/06`).

**Terkait:** [[06-Results/02 - Thresholds]] · [[03-Data/D4 - Dune]]

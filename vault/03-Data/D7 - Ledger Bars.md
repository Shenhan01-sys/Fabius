---
tags: [data, "D7"]
---

# D7 - Ledger Bars

**Bagian dari:** [[03-Data/00 - Hub Data]]
**Sumber:** `ledger/bars/` (64 berkas: `fut_<SYM>_1d.csv`, `spot_<SYM>_1d.csv`, `fund_<SYM>.csv`, `fund_est_<SYM>.csv`), `tools/feed_bars.py`, `tools/rest_vs_vision.py`

**Ringkas:** bar harian Binance (perp + spot) dan funding untuk 16 aset universe bot, di-commit bersama ledger paper supaya siapa pun bisa menghitung ulang
setiap tick dan settle (`python -X utf8 -m engine.cli ledger verify`).

**Poin kunci:**
- **Kedalaman:** perp sejak 2020-01-01 (BTC), spot sejak 2019-09-01 (BTC), funding sejak 2020-01-01; estimasi funding (P92) sejak 2026-10-01.
- **Siapa yang bisa membantah:** siapa pun lewat REST Binance - dan itu sudah dilakukan 2 Okt 16:00Z: harga 0 beda, funding 114.228/114.228 identik; volume beda
  di 52 bar perp + 88 bar spot, berkumpul di tanggal koreksi bursa (F-D83). Engine tidak membaca volume.
- **Lubang yang diketahui:** perp SOL/XRP/LTC/TRX/NEAR mulai 2022-02-26 (5 hari) tidak ada di seed Vision tetapi ada di REST (koreksi K-3).
- **Aturan:** append-only; bar baru harus tepat hari berikutnya, bolong tidak diloncati; funding hanya hari lengkap; LF dipaku (`.gitattributes`).

**Detail:** penulisnya rantai GitHub `paper-ledger` (`tools/paper_tick.py --feed`), bersama tick. Tahap 3 (bar dari REST segera sesudah penutupan) menunggu
pengukuran jeda terbit REST (P98).

**Terkait:** [[04-Tools/TL9 - ledger paper maju]] · [[04-Tools/TL13 - rest_vs_vision]] · [[03-Data/D6 - Funding and OI History]]

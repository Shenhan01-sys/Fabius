---
tags: [perkakas, "TL13"]
---

# TL13 - rest_vs_vision

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/rest_vs_vision.py`; tes `engine/tests/test_rest_vs_vision.py` (8)

**Ringkas:** uji kesamaan bar harian (perp + spot) dan funding dari REST Binance terhadap `ledger/bars` (zip Vision). Dijalankan sebagai job sekali jalan di Railway `fabius-probe` (Singapura, tanpa variabel rahasia; `FABIUS_JOB=rest_vs_vision`, `FABIUS_ARGS=--from-github --exit-zero`).

**Poin kunci:**
- Hasil 2 Okt 16:00Z: harga (o/h/l/c) 0 beda dari 38.030 bar perp + 39.827 bar spot; volume beda 52 / 88 bar; funding 114.228/114.228 identik, selisih waktu 0 ms.
- Baca: `railway logs --service fabius-probe --lines 400`.

**Yang ia TOLAK lakukan:** menyebut "sama" bila volume beda (vonis umum tetap ADA BEDA); vonis untuk engine hanya mencakup harga + funding (yang memang dipakai engine).

**Detail:** fapi ditolak dari runner GitHub (HTTP 451) dan dari laptop builder (TLS hostname mismatch); dari Singapura 200 (F-D80 #7).

**Terkait:** [[03-Data/D7 - Ledger Bars]] · [[00-Overview/03 - Decisions]] F-D83

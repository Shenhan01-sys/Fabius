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

**Alat kembar (P98):** `tools/rest_latency.py` (tes `engine/tests/test_rest_latency.py`, 5) mengukur kapan bar yang baru tertutup dan funding 00:00Z pertama kali terlihat di REST, dan apakah nilainya berubah sesudah itu (poll tiap 15 detik dari 23:59:30Z sampai 00:10Z, baca ulang +30 dan +60 menit). Dijalankan di `fabius-probe` dengan `FABIUS_JOB=rest_latency FABIUS_ARGS=--exit-zero`; terpasang 2 Okt 16:27Z, menunggu 7,5 jam. Resolusi jeda = interval polling.

**Terkait:** [[03-Data/D7 - Ledger Bars]] · [[00-Overview/03 - Decisions]] F-D83

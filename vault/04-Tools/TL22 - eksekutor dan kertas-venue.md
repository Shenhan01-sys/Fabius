---
tags: [perkakas, "TL22"]
---

# TL22 - eksekutor dan kertas-venue (epik 10)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `engine/eksekusi.py` (inti, murni) · `tools/venue_binance.py` (adaptor Binance USDⓈ-M) · `tools/kertas_eksekusi.py` (kertas-venue) · snapshot filter
`ledger/kertas/filter/<venue>.json` · ledger `ledger/kertas/<venue>/<bot>-<modal>-<jadwal>.jsonl` · uji `engine/tests/test_eksekusi.py` (13)
**PRD:** [[08-Backlog/10 - Epik Eksekusi Venue]] · F-D91 / F-D92

**Ringkas:** jalur dari target bot ke order venue, dibangun lebih dulu dalam bentuk yang tidak butuh akun, kunci, atau uang:

- **Inti (`engine/eksekusi.py`):** rencana order = bobot x ekuitas / harga, dibulatkan ke lot. Posisi di bawah min notional atau di bawah satu lot TIDAK
  dibuka dan alasannya dicatat; ubah kecil dilewati; menutup selalu dikirim (`reduce_only`). Ada juga client id deterministik (idempoten), pagar (universe,
  long-only, notional <= modal x 1), rekonsiliasi (> setengah lot = selisih), isi kertas (slippage searah order + fee), dan batas rugi harian.
- **Adaptor Binance (`tools/venue_binance.py`):** tanda tangan HMAC (sama persis dengan vektor resmi dokumen Binance), filter + harga publik, cek izin
  kunci (tarik HARUS mati, futures HARUS hidup; medan hilang = tidak aman), posisi, order pasar idempoten (id yang sudah ada tidak dikirim lagi). Kunci dari
  env `BINANCE_API_KEY` / `BINANCE_SECRET_KEY`, disamarkan di setiap pesan galat. **Belum pernah mengirim order** (butuh kunci testnet, langkah builder).
- **Kertas-venue (`tools/kertas_eksekusi.py`):** keputusan B1 dari ledger resmi dieksekusi di atas kertas.
  - Harga eksekusi = pembukaan kline 1m perp Vision pada 2 menit sesudah komit di SignalAnchor (jadwal `komit` = kenyataan), atau 10 menit sesudah bar tutup
    (jadwal `p99` = andaian bila tick + komit dibuat dari REST, P99).
  - Filter lot/min notional venue dari snapshot di repo; fee taker venue (Binance 5 bps, Aster 4 bps) + slippage 1 bps; cadangan 0,2 % ekuitas.
  - Modal 2.000 USDT virtual (B1 penuh bisa dibuka) dan 10 USDT (modal nyata builder, F-D92).
  - Pembanding: return paper hari yang sama dari target yang sama -> **tracking error** harian, **geser harga** (eksekusi vs harga acuan penutupan),
    **bobot terpenuhi**.
  - Dijalankan rantai GitHub `paper-ledger` sesudah tick (penulis tunggal `ledger/kertas/`); bahan belum ada = TUNDA, tick tidak dilompati.

**Yang ia TOLAK lakukan (T8 SK-E1..SK-E9):** mengeksekusi tick yang komitnya belum ada (atau lebih tua dari kunci); menebak posisi saat venue tak terbaca;
start dengan kunci yang bisa menarik dana; membuka posisi di bawah min notional diam-diam; mengirim order ganda untuk tick yang sama; memakai kas negatif.

**Hasil pertama (4 Okt ±01:2x WIB):** 8 ledger kertas (2 venue x 2 modal x 2 jadwal): bar 2026-10-01 = SEBELUM_KUNCI (tick lebih tua dari kunci, tidak
dieksekusi); bar 2026-10-02 = TUNDA (`kline 1m ... 2026-10-03 belum terbit`). Catatan eksekusi pertama menyusul sesudah Vision menerbitkan 1m 3 Okt.
Snapshot filter (4 Okt): Binance USDⓈ-M TESTNET min notional maks 50 USDT -> B1 penuh >= 800 USDT; Aster prod 5 USDT -> >= 80 USDT.

**Cara menjalankan:**
`python -X utf8 tools/kertas_eksekusi.py filters` (perbarui snapshot filter) · `... run` (tambah catatan) · `... ringkas` (metrik vs ambang PRD §6).

**Belum:** eksekutor live/testnet (saklar `EXEC_MODE`, turun ke dry saat selisih/rugi, P118); adaptor Aster (P121); ledger eksekusi dari riwayat trade venue
(P119 sisa); metrik slippage nyata (butuh order sungguhan).

**Terkait:** [[TL18 - worker_watch]] · [[TL14 - verify_signals]] · [[07-Testing/T8 - Semantik Kegagalan Operator]] · [[08-Backlog/05 - Epik Enam Bot]] §6 §7

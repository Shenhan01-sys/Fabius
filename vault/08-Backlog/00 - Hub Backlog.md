---
tags: [backlog, hub]
---

# Backlog & Epik

**Sumber:** `08-Backlog/`

Satu indeks kerja (P1..P49), dua epik, satu halaman sitasi. Folder ini sebelumnya **tidak punya hub** -
artinya dua epik dan sembilan item hari ini (P41-P49) hanya bisa ditemukan kalau orang sudah tahu
nama filenya. Itu lubang navigasi, bukan lubang data; sekarang ditutup, dan gerbang bentuk
(`hub_shape.py`) ikut memeriksa keempat unsur hub ini supaya tidak kembali bolong.

**Sejak 2 Okt 2026:** indeks kerja AKTIF = [[01 - Backlog]] bagian *Arah operator* (P68-P106, satu baris status per item: ✅ / 🟡 / ⏳ / ⬜ / 🟠 / 🚫). Epik tetap tempat rincian dan alasan; status tidak lagi ditulis di kolom catatan epik.

## Bagian

- [[01 - Backlog]] - indeks P1..P49 + status. **Berubah hari ini:** P41 (jembatan substrat - cakupan
  **3,1 %** terukur), P42 (satuan dampak; **sengaja ditunda** sampai vonis jatuh), P43 (E17 trailing),
  P44 (**E18 diuji: NOL**), P45 (E19 anggaran biaya - ambang spread ~21 bps), P46 (E20 slope
  kedalaman), **P47** (⑨ perekam buku + bug daftar pantau, F-D47), P48 (T5 microprice: tidak terukur,
  ditulis sebagai "belum"), P49 (E17: vonis wajib berupa bentuk distribusi, bukan untung/rugi)
- [[02 - Epik Alasan Masuk]] - epik jantung. §3d (E7/E8/E9 + pencabutannya F-D39/F-D40), §3e (E11
  umur posisi), §3f (E13/E14 rem di horison cepat)
- [[03 - Epik Teori Baru]] - **T1-T7** dari teori builder (order book + trailing stop): tiap teori
  dengan rumus, status data, desain uji, dan apa yang akan membunuhnya. §3 = aritmatika trailing yang
  sudah diukur (F-D48)
- [[04 - Riset Teori (Sitasi)]] - S1-S9 dengan URL + tanggal akses; tiga kutipan dibaca langsung dari
  halaman penerbit (Lei & Li 2009; Osler 2002; Ke & Lin 2017), plus daftar **tidak terverifikasi**
  dan satu sitasi yang **ditarik** ("Gu & Kelly 2014")
- [[05 - Epik Enam Bot]] - **USULAN** konsep operator pemilih bot (2 Okt; **M1 + M2 sudah jalan** - status per item di [[01 - Backlog]] *Arah operator*): enam bot = satu metode + satu parameter
  (TREND, RS, CARRY, LISTING-FADE, CORE-RWA, BOUNCE), yang ditolak, aturan lapisan operator, jalur venue/paper (Binance
  Agentic Wallet, testnet), konflik dengan klaim vault, dan P68-P76. Semua angka eksploratif, bukan klaim.
  **Berisi KOREKSI K1-K3 (2 Okt malam):** B2 1,29 = undian fase (0,85 tanpa pilihan hari), gabungan 2025-26 = 0,071, bolong data;
  §14 = mesin `engine/` (M1, belum di-commit)
- [[06 - Epik Gerbang Sinyal]] - **USULAN rancangan** (C-A `LockRegistry` + C-B `SignalAnchor` **ter-deploy 2 Okt**, F-D80) kirim sinyal lewat x402 V2 + MCP (+ email), tiga tingkat produk, dan jawaban
  "kontrak selain anchor tiap sinyal": `LockRegistry`, komit-ungkap v2, `OperatorGuard`, rekam jejak/siklus hidup, pass, escrow/bond,
  reputasi ERC-8004; benturan dengan "kami tidak menjual sinyal" dan F-D16/17/18; P77-P80
- [[07 - Epik Kolaborasi Bot Terbuka]] - **USULAN rancangan + kode awal** program penerbit bot luar (F-D71, F-D72): formulir skema tertutup (hanya `template`), **peninjau = bot
  deterministik, bukan agen** (gerbang G1-G11 + KPI K1-K5), sepuluh slot (≥ 1 bot identitas Fabius), rolling berbasis PnL net, bagi hasil **60/40 dari pendapatan penjualan sinyal**;
  tinjauan keamanan independen (12 temuan, status per temuan); **hasil dogfood terbaru:** hanya B3 lolos (B5 kini tolak), B1/B2/B6 tolak, B4 tak terukur; P81-P89
- [[08 - Riset Optimasi Ambang]] - **USULAN agenda riset** untuk mengoptimalkan ambang kunci v1 (F-D73: *"sementara ini oke, nanti riset lagi"*; v1 **terkunci sementara**, **ter-anchor 2026-10-02T08:17:48Z**, F-D74): **aturan anti-snooping dipasang
  sebelum riset** (enam bot Fabius bukan target), anggaran positif-palsu/daya yang usulannya menunggu builder, plafon daya aritmetika (edge Sharpe ≤ 0,5 tak terpisahkan dari noise oleh riwayat beberapa tahun),
  garis dasar kalibrasi nol (`run13_null_calibration.py`: penambang diam lolos 4 dari 340, percobaan diakui 0 dari 340), pertanyaan R1-R11, urutan kerja, jalur ke kunci v2; P90-P91
- [[09 - Usulan P107 Pembunuh Terstruktur]] — terjemahan mesin untuk kalimat pembunuh B1/B3, kunci terpisah dari spesifikasi; 4 pilihan tafsir menunggu builder

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
## Yang menunggu di folder ini

**Sekarang (2-3 Okt):**

| apa | kapan (UTC) | bukti yang dicari | item |
|---|---|---|---|
| tick bar 2026-10-02 B1 + B3 tanpa tangan manusia | 3 Okt 08:40-12:00Z | commit runner `paper-ledger`; `engine.cli ledger verify` SAH | P93 |
| komit + ungkap pertama di SignalAnchor | ±5 menit sesudah tick itu | `commitCount()` 0 -> 2; log worker `terkirim: 2 komit` | P94 |
| vonis publik pertama atas komit itu | sesudah komit | `python -X utf8 tools/verify_signals.py` -> SAH untuk B1 + B3 bar 2026-10-02, ALARM 0 | P106 |
| vonis bayangan pertama (bar 2026-10-02) | sesudah tick resmi rantai GitHub (P93) | `railway logs --service fabius-probe --lines 80`: `VONIS bayangan` IDENTIK untuk B1 dan B3, `VONIS baris REST` SAMA | P100 / F-D86 |
| epoch buku 691 (keputusan slot berikutnya) | 4 Okt ±09-12Z, sesudah tick rantai GitHub (OTOMATIS sejak P108) | commit `buku slot epoch …` di master; log worker `pin buku FABIUS-BUKU-E691: tx …`; `python -X utf8 tools/pin_book.py --verify` -> lockedAt | P108 |
| jeda terbit REST sesudah 00:00Z | 3 Okt 00:00-00:10Z (+30/+60 menit) | detik pertama bar + funding 00:00Z terlihat di REST; VONIS finalitas | P98 - **SELESAI: hadir <= 11 s (funding <= 15,5 s); 3 bar perp berubah di +15 s (BTC close +0,1), stabil sesudah +18 s** |

**Riwayat (29 Sep, sudah divonis):**

| kunci | alat | vonis (UTC) | dibaca sebagai |
|---|---|---|---|
| halaman 17 (watch) | `tools/day2_replicate.py --halaman 17` | ±14:59Z 29 Sep | replikasi kerumunan maker di `wp` |
| **E9** (lengan vol) | `tools/vol_ab.py` | **17:13:25Z** | tiga syarat + komposisi 25/25 slot |
| **E12** (5 m vs 30 m) | `tools/hold_ab.py` | **20:04:56Z** | empat syarat, termasuk umur baris harga keluar |
| **E16** (buku order) | `tools/book_prereg.py` | **21:37:45Z** | **WAJIB** bersama komposisi simbol (jangkar vs kabar, F-D47) |

Keempatnya tidak bisa dibaca sebelum jamnya - dan itu perilaku alat (`--status` menolak memvonis),
bukan disiplin hati.

```dataview
LIST FROM "08-Backlog" SORT file.name ASC
```

## Terkait

- [[00-Overview/00 - Hub Overview]] · [[00-Overview/05 - Corrections]] · [[00-Overview/06 - Roadmap]]
- [[06-Results/00 - Hub Results]] · [[07-Testing/01 - Test Commands]] · [[Concepts/One-Way Gate]]

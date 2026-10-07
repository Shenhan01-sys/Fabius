---
tags: [perkakas, hub]
---

# Tools

**Sumber:** `04-Tools/`

Satu catatan per perkakas: apa yang ia cetak, apa yang ia **tolak** lakukan, dan bug yang sudah
pernah ia hasilkan. Kaidah yang diulang di semua halaman sini: alat yang gagal diam-diam lebih
berbahaya dari alat yang gagal keras.

## Bagian

- [[TL1 - judge]] — penilai LLM, veto satu-arah, `ask_jev`
- [[TL2 - direction]] — side/entry/stop/ukuran/horizon; dua rezim keluar
- [[TL3 - security_gate]] — 4 status; `UNMEASURED` bukan `bersih`
- [[TL4 - anchor and verify]] — trail on-chain; `getAnchor` kembalikan struct nol
- [[TL5 - ledger]] — event-level dedupe, `AMBIGU`, belum jatuh tempo ≠ hasil
- [[TL6 - x402 gate and client]] — bentuk wire dari specs, status lokal
- [[TL7 - measurement harness]] — backtest · whale_sweep · flow_test, dan pager statistik
- [[TL8 - engine]] — mesin bot operator (M1): enam bot, spesifikasi ber-sha, sinyal = niat posisi, keccak/Merkle stdlib
- [[TL9 - ledger paper maju]] — M2: tick ex-ante ≤ 12 jam, gap tidak diisi, settle lewat replay yang sama; rantai GitHub penulis tunggal
- [[TL10 - kunci dan anchor kunci]] — kunci ambang v1 + satu baris DecisionAnchor; `--verify` tanpa kunci
- [[TL11 - komit sinyal M3]] — worker Railway: hitung ulang tick dari bar, komit akar Merkle, ungkap; menolak yang tak bisa direproduksi
- [[TL12 - m3_setup]] — deploy M3 + committer + kunci spesifikasi; dijalankan builder; gladi di anvil
- [[TL13 - rest_vs_vision]] — uji kesamaan REST Binance vs `ledger/bars` dari Singapura (job `fabius-probe`)
- [[TL14 - verify_signals]] — pemeriksa PUBLIK: komit + ungkap di chain vs ledger + bar repo, tanpa kunci; vonis SAH/ALARM per bot per bar
- [[TL15 - lock_spec]] — pin berkas kunci ke LockRegistry (jam = waktu blok); dipakai untuk kunci F-D16 maju (F-D84)
- [[TL16 - pin_book]] — pin `book_sha` epoch buku slot hidup ke LockRegistry (F-D85)
- [[TL17 - shadow_tick]] — mode bayangan tahap 2+3: tick dari REST beberapa menit sesudah tutup, dibandingkan dengan tick resmi; tidak menulis ledger, tanpa kunci (F-D86)
- [[TL18 - worker_watch]] — penjaga LUAR worker Railway di rantai GitHub: tick tanpa komit >= 30 menit = WORKER DIAM (stdlib, tanpa kunci, P111)
- [[TL19 - web landing]] — landing page tingkat 0: kristal komitmen 3D, perjalanan satu sinyal, kalender bukti, buku slot, dua pintu; data dari `tools/web_snapshot.py` (P113)
- [[TL20 - server MCP]] — pintu agen tingkat 0: route `/mcp` di app `web/`, 8 alat hanya baca (sinyal live, periksa leaf/id vs ledger, rekam jejak, kunci); tanpa kunci, tingkat 1 tetap terkunci (P114)
- [[TL33 - agent analis]] — P141/P142: SelectionAnchor + agent analis ERC-8004 (GLM 2558, Qwen 2559) memilih bot per bar sebelum penutupan; P159: agent baru lewat `config/agents.json` + `analis.py tambah` / `uji`
- [[TL34 - meja AI 5 menit]] — P152: tiga agent memutuskan tiap 5 menit, konsensus terkunci, Merkle root per siklus ke DeskAnchor; P158: lantai trading 3D di `/desk` (NPC di meja kerja, modal statistik dari monitor)
- [[TL35 - data meja v2]] — P153 (F1): Binance, DexScreener, RugCheck, FOMO, berita -> fitur terukur per aset + per bot tiap 5 menit, registry alamat terkunci
- [[TL38 - agent luar di meja (pull)]] — P166 (F-D121): agent ERC-8004 sendiri mendaftar, menarik masukan tiap siklus, menjawab dengan tanda tangan; kursi uji lewat C1
- [[TL39 - aturan deklaratif (rule)]] — P167a (F-D125): kind=rule, aturan JSON dijalankan mesin kita (validator tertutup, kausalitas oleh konstruksi, G5 atas parameter bernama, ekuivalensi B1/B6/B2, pembangun di `/submit`)
- [[TL41 - kode pengguna di sandbox (code)]] — P167b (F-D125): kind=code, fungsi kode penerbit di sandbox berlapis (AST daftar-izin, proses anak berbatas, dua jalan, uji kausalitas), kode PRIVAT + pelari terpisah tanpa rahasia; dibangun, TERTUTUP sampai builder menyetujui jalur privat
- [[TL42 - komit maju penerbit (feed)]] — P167c (F-D125): kind=feed, bobot bertanda tangan dikomit sebelum penutupan bar, akar per bar dikunci di LockRegistry, ledger maju 120 hari tanpa slot, gerbang replay N/A
- [[TL37 - jalur pengajuan bot]] — P161 (F-D120): kiriman penerbit -> gerbang -> tinjauan publik GitHub -> pin spec -> jam maju -> epoch buku, tanpa langkah manual
- [[TL36 - meja v2 bot + instrumen]] — P154/P155 (F-D112): AI memilih bot + instrumen, aturan bot terkunci menghitung arah pada candle harian, satu root bersama v1
- [[TL32 - gerbang x402 per sinyal]] — P138a: FAB testnet, harga dari confidence (terkunci), gerbang publik Railway, faucet relay, pembelian publik terbukti
- [[TL31 - teaser confidence]] — P137: 1 - p bootstrap F-D16 atas settle maju, gratis sebelum bayar; tanpa aset/arah/ukuran
- [[TL30 - validasi ERC-8004]] — P136: tiap komit dimintakan validasi di ValidationRegistry resmi (agen 2494); validator di GitHub Actions menjawab dari pemeriksa P106
- [[TL29 - canary uang nyata]] — P133: satu aset B1, <= 10 USDT, Binance PROD; izin bertanggal, cek kunci tanpa tarik, batas keras; isi nyata ke umpan + ExecutionAnchor (REAL)
- [[TL28 - bot sementara dan data B4 B5]] — F-D95: label INTI/SEMENTARA + vonis gerbang v1; data emas PAXG (B5) dan pipa kejadian listing perp baru (B4) dari Binance Vision
- [[TL27 - ledger eksekusi]] — P119: eksekutor menyusun laporan dari venue -> Gist publik -> rantai GitHub memeriksa + menulis `ledger/eksekusi/` (runner diblokir Binance 451, F-D94); metrik vs kertas; penjaga luar
- [[TL22 - eksekutor dan kertas-venue]] — epik 10: inti eksekutor (rencana, pagar, idempoten, rekonsiliasi), adaptor Binance (belum mengirim order), kertas-venue (akurasi di atas kertas sebelum uang nyata, F-D92)
- [[TL23 - Sistem Visual FE]] — pedoman visual SEMUA halaman web/: prompt asal builder + 3 referensi, token, tipe, kaca, keadaan kubus, gerak, daftar periksa halaman baru
- [[TL26 - halaman status]] — /status: kesehatan operasi hari ini (dial 24 jam UTC, stasiun per bot, gas committer, detak rantai GitHub); kode sama dengan MCP `fabius_status`
- [[TL25 - halaman bot]] — /bot/[id]: satu bot = satu mesin terkunci; aturan asli + kunci, buku paper live (kubus universe), hari demi hari -> /verify, F-D16, pembunuh terkunci
- [[TL24 - halaman verify]] — /verify: pemeriksaan publik satu (bot, bar) di peramban, empat stasiun tick -> komit -> dibuka -> dihitung ulang; kode sama dengan MCP
- [[TL21 - waitlist]] — penampung daftar tunggu tingkat 1: bot Telegram dibaca rantai GitHub tiap 5 menit, pendaftar dikabarkan ke chat builder; log publik hanya hitungan (P115)
- [[TL40 - peninjau LLM]] — P168a/P168b (F-D125): tahap 2 sesudah tahap teknis, xkiro GLM 5.3 effort bawaan, brief persis ber-sha, JSON ketat, hanya MENAHAN (LLM mati = TAHAN), set kalibrasi; BELUM DIKALIBRASI = tidak di jalur
- [[TL43 - evaluasi meja F4]] — P156 (F4, BAYANGAN): IC / hit / kalibrasi per agent, bobot agent usulan (sha `0x41a1001d…`), buku ablasi per agent + per sumber yang wajib SETIA, rapor direkam, usulan evaluator hanya lewat bayangan + kunci; `FABIUS_F4=bayangan`, `tools/meja_eval.py rapor`
- [[TL44 - gerbang seleksi bot (P161)]] ← tulis penjelasannya
- [[TL46 - lapisan pemilih (P74)]] ← tulis penjelasannya
- [[TL45 - MCP berbayar meja (P157)]] ← tulis penjelasannya

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #perkakas SORT file.name ASC
```

## Terkait


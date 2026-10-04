---
tags: [perkakas, "TL27", eksekusi]
---

# TL27 - ledger eksekusi (umpan Gist eksekutor -> rantai GitHub -> `ledger/eksekusi/`)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/exec_feed.py` (penyusun laporan + klien Gist, dipakai eksekutor) · `tools/eksekutor.py` (`queue_report` / `queue_mark` /
`queue_backfill` / `flush`) · `tools/venue_binance.py::user_trades` · `tools/eksekusi_ledger.py` (penulis + metrik + penjaga luar, rantai GitHub) ·
langkah baru di `.github/workflows/paper-ledger.yml` (tiap putaran 5 menit) · stasiun 06 `/status` (`web/src/lib/status.ts`) · tes
`engine/tests/test_exec_feed.py` (9) · T8 SK-E14..SK-E21 · keputusan [[00-Overview/03 - Decisions]] F-D94 · epik [[08-Backlog/10 - Epik Eksekusi Venue]] R-E10, E3

**Kenapa bentuknya begini (terukur, bukan selera):** PRD menaruh penulis ledger eksekusi di rantai GitHub dengan kunci read-only. Runner GitHub mendapat
**451** dari `demo-fapi.binance.com` dan `fapi.binance.com` (Test Commands 5y), jadi untuk Binance pembacaan harus di Railway (Singapura). Eksekutor
menyusun laporan dari venue, menaruhnya di **Gist publik** dengan token hanya-Gist (tidak bisa menyentuh repo), dan rantai GitHub tetap PENULIS TUNGGAL
ledger sesudah memeriksa. Aster terjangkau dari runner, jadi P121 bisa membaca langsung.

**Alur:**
1. Eksekutor (`fabius-engine`, mode demo) selesai satu bar -> antre laporan. Laporan disusun ULANG dari venue: untuk tiap aset universe x {BUY, SELL},
   order dicari lewat `clientOrderId` = `ex.client_id(venue, bot, bar, aset, sisi)`; isi + fee nyata dari `userTrades`; plus posisi + ekuitas sesudahnya,
   `dilewati` dan harga tengah saat rencana (`px_rencana`) bila proses masih ingat. Restart tidak mengubah isinya.
2. Tanda ekuitas harian: putaran pertama <= 30 menit sesudah 00:00Z (bahan tracking error).
3. **Susulan:** sekali per proses, bar terkomit <= 7 hari ke belakang diantre; HANYA bar yang order-nya ditemukan di venue yang dilaporkan, ditandai
   `susulan`, posisi + ekuitas dikosongkan (nilai sekarang bukan milik bar itu). Ini yang akan membawa 16 order demo bar 2 Okt (3 Okt 19:35Z) ke ledger.
4. Kirim ke Gist `fabius-exec feed v1` (dibuat sekali, publik), satu berkas per bulan `fabius-exec-YYYY-MM.jsonl`, idempoten per (jenis, venue, bot,
   bar/tanggal). Gagal = tertunda, dicoba tiap putaran; eksekusi tidak terganggu (SK-E14).
5. Rantai GitHub (`eksekusi_ledger.py run`, tiap 5 menit): baca Gist (cari lewat deskripsi di akun `Shenhan01-sys`), periksa tiap baris, tulis
   `ledger/eksekusi/<venue>/<bot>.jsonl` + `tanda.jsonl` berantai hash, `verify`, commit. Lalu `periksa` (penjaga luar).

**Pemeriksaan (rantai GitHub tidak memercayai laporan):** integritas -> DITOLAK + ALARM (id order bukan hash yang dihitung ulang, venue/bot asing, bar
tanpa tick, bar mundur); keselamatan -> DITULIS dengan `pelanggaran` + ALARM (order dikirim sebelum `committedAt` yang dibaca SENDIRI dari SignalAnchor,
aset di luar universe, short pada bot long-only). Tanda ekuitas > 30 menit sesudah 00:00Z ditulis `dipakai: false`.

**Metrik per catatan (dihitung di rantai GitHub):** fee bps nyata · slippage = isi vs harga tengah saat rencana · geser = isi vs penutupan bar (sama
dengan kertas) · **selisih vs isi KERTAS bar yang sama** (`ledger/kertas/binance/<bot>-<modal>-komit.jsonl`) = seberapa akurat kertas-venue sebagai
uji akurasi sebelum uang nyata (F-D92) · latensi komit -> isi terakhir · bobot terpenuhi. `ringkas`: median/p95 vs ambang usulan PRD §6 (slip <= 5 bps,
fee <= 7 bps, latensi p95 <= 10 menit, tracking median <= 10 / p95 <= 30 bps, >= 20 hari). Tracking error harian = (Δ tanda ekuitas / modal) - return
paper (definisi kertas; funding ada di ekuitas venue tetapi tidak di pembanding paper - dicatat).

**Penjaga luar (SK-E17):** tick resmi dikomit >= 60 menit tanpa laporan eksekusi, setelah ledger bot itu aktif = ALARM (Telegram, diredam per (venue, bot,
bar) per mata rantai lewat `--state`); < 60 menit = MENUNGGU.

**Yang ia TOLAK lakukan:** memegang kunci venue di GitHub atau Vercel; menebak isi saat Gist/chain tak terbaca (exit 3 = TUNDA, SK-E18); mengklaim "0
order" untuk bar lama yang tidak pernah diproses; memercayai `komit_s` dari eksekutor (dibaca ulang dari chain).

**Batas jujur:** mode demo membaca dengan kunci eksekutor sendiri (kunci read-only terpisah + service terpisah = syarat sebelum S3, F-D93 #3). Balasan
Binance tidak bertanda tangan: publik tetap memercayai pembaca, tetapi bisa memeriksa urutan terhadap komit, id deterministik, konsistensi posisi, dan
selisih terhadap kertas.

**Bukti 4 Okt (lokal):** `pytest engine/tests/test_exec_feed.py` 9 lulus (laporan disusun ulang dari id dan dipublikasikan sekali, restart tidak
menggandakan, token tidak bocor ke log; umpan mati -> laporan tertunda, eksekusi tetap "posisi cocok"; tanpa token tidak ada umpan; tanda hanya
00:00-00:30Z; susulan hanya bila order ada, posisi kosong; laporan bersih ditulis dengan fee 4 bps / geser +5 / slip +5 / selisih kertas +4 bps / latensi
120 s; id palsu DITOLAK; order sebelum komit = 2 pelanggaran; verify menangkap utak-atik; penjaga luar MENUNGGU 10 menit -> ALARM 61 menit; tracking
error dari tanda; Gist belum ada = bukan galat). Sensus `--wajib-semua` 433 lulus, 0 dilewati. T8 90 baris, 89 berjangkar, 0 masalah; `--run` 81 tes
jangkar lulus (sebelum SK-E21). Pada repo nyata: `eksekusi_ledger.py run` -> "umpan eksekusi belum ada (... langkah builder H7)" exit 0; `periksa`,
`ringkas`, `verify` -> belum ada ledger, exit 0.

**Ter-deploy 4 Okt 09:21Z** (komit `1c05e7f9`, `tools/railway_up.py`): worker start `... | eksekutor demo | umpan eksekusi mati (EXEC_FEED_TOKEN tidak ada,
F-D94 H7)`, komit B1/B3 bar 10-02 + 10-03 OK, `eksekutor demo B1-TREND bar 2026-10-03: 0 order, 11 dilewati, modal 2000`. CI `tests` hijau; Vercel READY;
`/api/status` produksi: stasiun 06 B1 `private EXEC_PRIVATE`. Rantai `paper-ledger` memakai langkah baru mulai mata rantai berikutnya (±13:38Z).

**H7 dipasang builder 4 Okt (±12:51Z):** log `umpan eksekusi nyala`; daftar gist berhasil (token terbaca), tetapi `buat gist: HTTP 403` -> laporan
TERTUNDA (2: susulan 10-02 + bar 10-03), eksekusi tetap jalan (SK-E14 terbukti di produksi). Pesan galat hanya memuat kode HTTP; ditambah pesan GitHub
(`_why`, tanpa token, tes `test_a_refused_gist_write_says_why_without_leaking_the_token`) supaya sebab 403 terbaca.

**UMPAN HIDUP 4 Okt 13:11Z** (builder mengubah izin token ke Gists "Read and write"): Gist publik `292d495fe83abbfa6f12d0282edf151c`
(`fabius-exec feed v1`, berkas `fabius-exec-2026-10.jsonl`), dua baris: **susulan bar 10-02** = 16 order demo `FILLED` (fee nyata 0,7912 USDT atas
notional 1.977,98), posisi/ekuitas kosong sesuai aturan susulan; **bar 10-03** = 0 order (B1 tidak berubah), ekuitas demo 5.015,16.

**Pratinjau penulis pada data nyata** (folder sementara, BUKAN `ledger/` repo - penulisnya tetap rantai GitHub): 2 catatan, 0 alarm, `verify` bersih.
Bar 10-02: komit 3 Okt 08:43:51Z (dibaca dari chain), 16 order semua SESUDAH komit (R-E1, 0 pelanggaran), latensi 39.126 s (10,9 jam: eksekusi demo
pertama dinyalakan 19:35Z), fee median **4,0 bps** (<= 7), geser vs penutupan median +77 bps, **selisih vs isi kertas median +59 bps** (kertas
mengandaikan isi 2 menit sesudah komit; yang nyata 10,9 jam kemudian - selisih itu harga bergerak, bukan galat model). Bar 10-03: 0 order, bobot
terpenuhi 99,2 %. `ringkas`: BELUM CUKUP HARI (tracking butuh tanda 00:00Z dua hari berturut). Slippage vs rencana kosong untuk susulan (harga rencana
tidak diingat sesudah restart) - akan terisi pada eksekusi berikut.

**LEDGER RESMI PERTAMA 4 Okt 13:53:49Z** (komit rantai GitHub `f2920810`): `ledger/eksekusi/binance-demo/B1-TREND.jsonl`, 2 catatan (susulan 10-02: 16
order; 10-03: 0 order), `verify` OK, `ringkas`: fee median 4,0 bps, selisih vs kertas +58,9 bps, latensi p95 39.126 s, 0 pelanggaran, BELUM CUKUP
HARI. Produksi: `/status` stasiun 06 B1 `ok EXEC_OK` ("di ledger publik: 0 order" untuk bar 10-03); `/bot/B1-TREND` menampilkan section eksekusi.

**Temuan di jalan ke sana (diperbaiki):** mata rantai 13:40Z mencetak `TAK TERBACA: daftar gist Shenhan01-sys: HTTP 403` tiap putaran - `GITHUB_TOKEN`
(token instalasi GitHub App) ditolak API Gist. Alat berperilaku sesuai SK-E18 (TUNDA, peringatan, bukan alarm). Perbaikan `52af1b5c`: id Gist DIPATOK
(`GIST_ID`, env `EXEC_FEED_GIST` menimpa) dan isi dibaca dari URL raw publik `gist.githubusercontent.com/<pemilik>/<id>/raw/fabius-exec-YYYY-MM.jsonl`
per bulan (tanpa token, tanpa batas API; bulan tanpa berkas = 404 dilewati; cache CDN 5 menit); jalur API tinggal cadangan bila id tidak diketahui.
Karena mata rantai hanya `git pull` di jendela tick, mata rantai 13:40Z (run 37206431782) DIBATALKAN dan rantai baru dinyalakan manual (run
37207233417, 13:53:25Z, HEAD `52af1b5c`); putaran pertamanya langsung menulis ledger.

**Menunggu (riwayat):** langkah builder **H7** (token hanya-Gist -> variabel Railway `EXEC_FEED_TOKEN`), lalu deploy `fabius-engine` (`tools/railway_up.py`; arsip +
Dockerfile kini memuat `exec_feed.py`). Sesudah itu: log worker `umpan eksekusi nyala`, Gist baru tercetak id-nya, rantai GitHub menulis
`ledger/eksekusi/binance-demo/B1-TREND.jsonl`, stasiun 06 `/status` berubah dari "tidak publik" ke "di ledger publik: n order".

**Terkait:** [[TL22 - eksekutor dan kertas-venue]] · [[TL18 - worker_watch]] · [[TL26 - halaman status]] · [[07-Testing/T8 - Semantik Kegagalan Operator]]

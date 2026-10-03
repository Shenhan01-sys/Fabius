---
tags: [dashboard]
---

# Dashboard

> **BN-PIVOT - 2 Okt 2026.** Arah proyek bergeser: Fabius menjadi **operator pemilih bot** yang kelak menjual **sinyal
> berbukti** dan membuka slot bot untuk penerbit luar ([[00-Overview/03 - Decisions]] F-D70 dan F-D71). Halaman ini
> menggambarkan keadaan **sebelum** pivot dan tetap benar untuk apa yang **sudah dibangun**; arah baru masih **usulan dan kode
> awal** ([[08-Backlog/05 - Epik Enam Bot]], [[08-Backlog/06 - Epik Gerbang Sinyal]], [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]]).
> Jangan memakai halaman ini untuk menyangkal arah baru, dan jangan menyebut arah baru sebagai fitur yang sudah ada.

> **STATUS 2 Okt malam (dicetak ulang):** arah baru bukan lagi sekadar usulan. Ledger paper maju B1-TREND + B3-CARRY hidup (M2, F-D75..F-D78); kontrak
> `LockRegistry` + `SignalAnchor` ter-deploy di chain 97 (M3, F-D79/F-D80); worker Railway mengomit tiap tick (F-D80; committer dirotasi, F-D82); perekam
> wallet-flow dihentikan (F-D81); data REST = data Vision untuk engine (F-D83). Semua tetap **paper**: tanpa uang nyata, tanpa klaim edge.
> **3 Okt:** tabel semantik kegagalan pipeline operator + gerbangnya ([[07-Testing/T8 - Semantik Kegagalan Operator]], P109); tahap 2+3 berjalan sebagai
> **mode bayangan** di Railway `fabius-probe`: tick dari REST beberapa menit sesudah tutup, dibandingkan dengan tick resmi (F-D86, [[04-Tools/TL17 - shadow_tick]]).
> **3 Okt sore (bukti):** hari pertama penuh TANPA tangan manusia. Rantai GitHub menulis tick bar 2 Okt (08:40Z), worker Railway mengomit + mengungkap
> (2 komit, 1 ungkap, 0 gagal), `verify_signals` memvonis SAH untuk B1 dan B3, dan mode bayangan IDENTIK dengan tick resmi (80 baris REST = Vision).
> **3 Okt malam (hidup untuk orang lain, F-D89):** landing tingkat 0 https://fabius-one.vercel.app + server MCP untuk agen di `/mcp` (8 alat hanya baca;
> `fabius_verify` memeriksa sinyal mana pun langsung dari chain), data landing dicetak mesin sesudah bukti harian, daftar tunggu tingkat 1 lewat bot Telegram
> (P113-P115). Tingkat 1 tetap TERKUNCI (F-D72); semua tetap paper.
> Status per item: [[08-Backlog/01 - Backlog]] bagian *Arah operator*.

Pertanyaan proyek dalam bentuk tabel. Semua barisnya diambil dari perintah yang ada di repo;
kolom "diperbarui" adalah tanggal run, bukan tanggal edit halaman.

| pertanyaan | jawaban sekarang | dibuktikan oleh | diperbarui |
|---|---|---|---|
| Produknya apa? | agen yang menerbitkan keputusan yang bisa dibuktikan salah | [[00-Overview/01 - Briefing]] | 2026-09-27 |
| Kenapa tidak "bot trading"? | tiga jalur sinyal diuji; dua mati, satu ditahan karena lookahead | [[06-Results/04 - Negative Results]] | 2026-09-27 |
| BNB-nya di mana? | kontrak 97 · identitas ERC-8004 · pembayaran x402 · venue & vault eksekusi | [[05-Ecosystem/00 - Hub BNB Ecosystem]] | 2026-09-27 |
| Bisa dijalankan orang lain? | ya: `forge test`, `anchor.py --verify` (tanpa kunci), `ledger.py` | [[07-Testing/01 - Test Commands]] | 2026-09-27 |
| Angka paling jujur yang kami punya | −72,4 bps rata-rata dari 2 posisi jatuh tempo (n=2) | [[06-Results/07 - Matured Outcomes]] | 2026-09-27 |
| Yang paling lemah sekarang | **sinyal**: nol jalur arah yang lolos uji setelah ongkos (rugi 12/12); alat skor ⑦ belum bisa dipercaya; gateway belum di-host | [[08-Backlog/01 - Backlog]] P10–P15 | 2026-09-28 |
| Ilmunya di mana? | lapisan pengetahuan trading per metode, dengan status data & tingkat bukti tiap catatan | [[TradingKnowledge/00 - Hub Trading Knowledge]] · [[TradingKnowledge/Fakta Terukur]] | 2026-09-28 |
| Berapa sisa waktu | tenggat 30 Sep 23:59 **WIB** (sudah lewat; arah operator tidak punya tenggat hackathon) | [[00-Overview/06 - Roadmap]] | 2026-09-27 |
| Arah sekarang? | operator pemilih bot, **paper penuh**: B1-TREND + B3-CARRY di ledger maju, sinyal dikomit ke chain | [[08-Backlog/01 - Backlog]] *Arah operator* · F-D70..F-D83 | 2026-10-02 |
| Kontrak baru? | `LockRegistry` `0xcF6fBF95fc04DEd8d670512CEc0723a2246Fbb0C` · `SignalAnchor` `0x9B78200beFbbBe836585d31bd5b6dB32587064f3` (chain 97) | [[02-Contracts/C6 - LockRegistry]] · [[02-Contracts/C7 - SignalAnchor]] | 2026-10-02 |
| Jalan 24/7 di mana? | rantai GitHub `paper-ledger` (penulis ledger; sejak 3 Okt juga memicu snapshot landing + membaca daftar tunggu) + Railway `fabius-engine` (Singapura, komit sinyal) + Railway `fabius-probe` (mode bayangan) + Vercel `fabius` (landing + MCP, dibangun dari GitHub) | [[00-Overview/04 - Run It]] · F-D89 | 2026-10-03 |
| Penyaring bot sudah diukur? | **ya, di pasar sintetik (4 Okt)**: bot tanpa keunggulan lolos ±1 % (batas 5 %); bot ber-Sharpe 1 dengan 6,7 th riwayat lolos 20-39 % (plafon 78 %) - v1 konservatif; melonggarkan = gelombang 2 + kata builder | [[06-Results/32 - Hasil P90 R1+R2]] | 2026-10-04 |
| Eksekusi ke venue? | **akun DEMO Binance sejak 3 Okt 19:35Z** (16 order B1, posisi cocok; saldo virtual) · uang asli belum - PRD v1.1 (4 Okt): Binance Agent OS -> Aster -> Tokocrypto; modal nyata maks 10 USDT = B1 penuh tidak bisa dibuka; akurasi diuji di KERTAS-venue dulu (otomatis tiap hari), uang nyata hanya canary pipa 1 aset atas kata builder (F-D92) | [[08-Backlog/10 - Epik Eksekusi Venue]] · F-D91 | 2026-10-04 |
| Bisa dilihat orang lain? | landing https://fabius-one.vercel.app · MCP `https://fabius-one.vercel.app/mcp` (produksi: `fabius_verify B3-CARRY 2026-10-02` = SAH) | [[04-Tools/TL19 - web landing]] · [[04-Tools/TL20 - server MCP]] · [[07-Testing/01 - Test Commands]] 5i | 2026-10-03 |
| Yang belum terbukti | ~~tick tanpa tangan manusia + komit pertama on-chain: 3 Okt~~ **terbukti 3 Okt sore** (SAH 2, ALARM 0). Belum: hari 2-5 bayangan (P99), settle final pertama + F-D16 maju, agen luar memakai MCP, pendaftar pertama | [[06-Results/03 - Not Yet Proven]] #22-#26 · [[09-Inbox/Session-2026-10-02]] §39 | 2026-10-03 |

```dataview
TABLE WITHOUT ID file.folder AS folder, file.name AS halaman
FROM "09-Inbox" SORT file.name DESC
```

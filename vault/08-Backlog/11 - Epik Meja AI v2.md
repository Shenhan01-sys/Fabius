---
tags: [backlog, epik, "meja-ai", llm, x402, mcp]
---

# 11 - Epik Meja AI v2 (PRD): data luas, bot dominan dari tiga agent, keputusan terukur, MCP berbayar

**Bagian dari:** [[08-Backlog/00 - Hub Backlog]]
**Dibuka:** 5 Okt 2026 (WIB) oleh builder, kata-katanya:
- *"justru jgn disediakan sebagai alat mcp dong, kan itu saya suruh untuk dipakai Fabius agar bisa analisis data. agar AI bisa melihat data lebih
  luas, tapi tetap pakai kalkulasi yg terukur. Nanti intinya 3 agent ini akan memberikan outputnya secara bersamaan tiap 5 menit dengan format yg
  ditentukan agar bisa dikalkulasi dan dianalisis dgn bot/rumus untuk open posisi"*
- *"tiap output LLM nantinya jg hrs ada bot mana yg akan dipilih, nanti tinggal di kalkulasi jg dari pilihan bot dan hasil analisis semua AI agent
  LLM lalu ambil 1 yg paling dominan untuk dipakai dan dibuat open posisi"*
- *"harus ada loop evaluasi untuk self improvement"*
- *"mcp fabius itu hanya menyediakan signal dan data yg mendukung/menjelaskan lebih detail mengenai sinyal itu dan mcpnya itu hanya bisa dipakai dengan
  melalui x402, jadi user bisa deposit dulu ... nanti tiap call mcp maka akan lgsg otomatis terpotong dari akunnya"*

**Status (5 Okt sore):** F1 HIDUP (P153, cek 24 jam ±6 Okt 11:40Z); F2 + F3 opsi D dibangun dan diuji kering (P154/P155,
[[04-Tools/TL36 - meja v2 bot + instrumen]]), menunggu push + deploy; F4/F5 belum. Rencana E0 disetujui builder 5 Okt (*"Gasss"*, workflow: *"OKe nice, gas catat ke vault"*). Keputusan F-D110
(meja v2) dan F-D111 (MCP berbayar). Backlog P153-P157. Status per item hanya di [[08-Backlog/01 - Backlog]].
**Bahan:** F-D109 meja v1 ([[04-Tools/TL34 - meja AI 5 menit]]) · F-D102/F-D107 analis + registry luar ([[04-Tools/TL33 - agent analis]]) · F-D104

> **Revisi 5 Okt (F-D112, opsi D):** AI memilih **bot + instrumen** (maks 8, dari 50 perp teratas volume 24 jam + 12 token registry); arah per instrumen dihitung KODE dengan aturan bot terkunci (`engine.bots.REGISTRY`) pada candle harian live; v2 langsung hidup berdampingan dengan v1 24 jam (tidak menunggu kriteria 24 jam F1). Bagian §4 dan §5 di bawah dibaca bersama F-D112: `instrumen` ditambahkan ke format, dan posisi = arah aturan x bobot rata x eksposur pada instrumen terpilih (bukan target harian bot).
alasan berbayar · F-D108 agent berita + FOMO · F-D89 tingkat 0 MCP gratis (DIGANTI oleh F-D111) · [[07-Testing/T8 - Semantik Kegagalan Operator]]
SK-M4..SK-M13 (rencana).

## 1. Masalah dan tujuan

Keadaan 5 Okt (meja v1, F-D109): tiga agent membaca candle 5 menit + funding Binance (agent berita juga judul berita) dan bebas menentukan bobot per
aset; DexScreener / RugCheck / Bubblemaps / FOMO hanya alat MCP publik (P140) yang TIDAK dibaca agent Fabius sendiri.

Tujuan v2:
1. Fabius sendiri membaca platform luas lewat **kode** dan mengubahnya menjadi **fitur terukur** yang sama untuk semua agent.
2. Ketiga agent memberi output **bersamaan tiap 5 menit** dalam **format baku** yang memuat **pilihan bot + skor untuk semua bot + analisis**.
3. **Rumus terkunci** memilih **satu bot dominan**; posisi = target bot itu x eksposur. AI memilih bot dan dial risiko; aturan posisi tetap aturan bot
   yang terkunci.
4. **Loop evaluasi terukur** untuk perbaikan diri.
5. **MCP = sinyal + data pendukung**, hanya lewat x402 (deposit lalu dipotong per panggilan).

**Bukan tujuan:** AI membuat trade di luar aturan bot terkunci; uang nyata (tetap paper; sakelar uang nyata F-D97 terpisah); perubahan diri diam-diam
(prompt / rumus hanya berubah lewat versi bayangan + kunci baru); menjual ulang data mentah platform pihak ketiga.

## 2. Alur satu siklus 5 menit (target)

```
1. Pengumpul data (kode)   -> Binance - DexScreener - RugCheck - FOMO - Berita
2. Fitur terukur (rumus)   -> per aset + per bot; snapshot per sumber di-hash
3. 3 agent AI (paralel)    -> pilihan bot + skor_bot untuk SEMUA bot + analisis (format v2, §4)
4. Mesin keputusan (rumus) -> bot dominan -> posisi = target bot itu x eksposur (§5)
5. Paper + komit Merkle ke DeskAnchor + evaluasi -> loop perbaikan diri (§6)
```

Meja v1 tetap berjalan sebagai pembanding sampai v2 menggantikannya (F3).

## 3. Sumber data dan fitur terukur

Akses diukur 5 Okt (curl / uji alat):

| sumber | akses terukur | dipakai untuk |
|---|---|---|
| Binance USDⓈ-M (`fapi.binance.com`) | klines 5 menit + `premiumIndex` 200 (meja v1 hidup); `exchangeInfo`: 525 perp USDT aktif; 21 dari 22 kandidat memecoin punya perp | semua aset; open interest + rasio taker **belum diukur aksesnya** |
| DexScreener | search + token-pairs 200; **pencarian simbol tidak andal** ("WIF" -> token tiruan di chain lain) -> wajib registry alamat | aset on-chain dalam target bot (mis. listing baru B4) |
| RugCheck | `report/summary` 200 (Solana) | aset Solana dalam target bot; veto keras |
| FOMO (fomoapi.io) | kunci `FOMO_API_KEY` di Vercel; leaderboard 24h 150 trader, thesis 20 (5 Okt) | holder trader top + sebutan thesis per token |
| Berita | Cointelegraph / Decrypt / The Block RSS + Binance CMS 200 (`tools/kabar.py`) | sebutan per aset, flag listing/delisting |
| Bubblemaps | publik hanya `map-availability` (metadata 500, data 404) | **dilewati** kecuali builder mengambil akses API berbayar |
| GMGN | route publik 403; API resmi butuh permintaan bertanda tangan | **tidak dipakai** |

**Registry alamat token (terkunci):** pemetaan perp Binance -> (chain, alamat kontrak) ditulis tangan, di-hash, dikunci; perubahan = versi baru.

**Fitur per aset** (fungsi murni, diuji, z-score 24 jam): return 5m/1j/4j, volatilitas, funding (Binance); volume DEX 1j vs rata-rata, rasio buy/sell
1j, likuiditas, selisih harga DEX vs Binance (DexScreener); skor risiko, % LP terkunci (RugCheck); jumlah trader top yang memegang + perubahannya,
sebutan thesis (FOMO); sebutan berita 6 jam, flag listing/delisting (berita).

**Fitur kecocokan per bot:** B1 kekuatan + breadth tren dan PnL portofolio B1 1j/4j (harga 5 menit); B2 sebaran return antar-aset; B3 funding vs
theta; B4 aktivitas DEX + holder FOMO + risiko RugCheck aset listing baru; B5 volatilitas BTC vs emas; B6 z-score oversold. Semua bot: confidence
maju, PnL berjalan, posisi saat ini.

**Anggaran:** FOMO gratis 250.000 kredit/bulan (leaderboard 250, thesis 1.250 per panggilan) -> leaderboard tiap 2 jam + thesis tiap 8 jam
(±202.500/bulan); DexScreener batch 2-3 panggilan/siklus; RugCheck per jam; model 864 panggilan/hari (3 agent x 288 siklus); gas komit ±0,011
tBNB/hari pada 1 gwei (builder mengisi faucet harian).

## 4. Format output agent v2 (baku, divalidasi)

```json
{"ringkasan": "...",
 "bot": "B1-TREND",
 "skor_bot": {"B1-TREND": 70, "B2-RS": 10, "B3-CARRY": -20, "B4-LISTING-FADE": 30, "B5-CORE-RWA": 40, "B6-BOUNCE": 0},
 "keyakinan": 65,
 "eksposur": 80,
 "veto_aset": [{"aset": "MOONSHOTUSDT", "faktor": "rugcheck_risiko", "alasan": "..."}],
 "faktor": ["b1_tren_kekuatan", "fomo_holder_delta"],
 "alasan": "..."}
```

Validasi: `skor_bot` wajib untuk keenam bot (-100..100); `bot` = skor tertinggi; `keyakinan` dan `eksposur` 0..100; `faktor` dan `veto_aset.faktor`
wajib nama dari daftar fitur yang diberikan siklus itu (agent yang mengarang alasan ketahuan); ringkasan wajib. Salah = keputusan agent itu ditolak
(SK-M6), bukan diperbaiki diam-diam.

## 5. Mesin keputusan v2 (rumus terkunci saat F3 disetujui; nilai di bawah = usulan yang disetujui 5 Okt)

1. **Nilai bot:** V_b = sum_i (W_i x keyakinan_i/100 x skor_bot_i,b) / sum_i W_i + lambda x Q_b; Q_b = prior kuantitatif dari fitur kecocokan + rekam
   jejak bot (lambda usulan 0,3); W_i = bobot agent (§6), mulai sama.
2. **Bot dominan** = argmax V_b. **Hysteresis:** pindah hanya bila unggul >= 15 poin dari bot yang sedang dipakai DAN bot baru dipegang minimal
   3 siklus (15 menit). Analisis tetap wajib tiap 5 menit.
3. **Eksposur** m = rata-rata eksposur agent (berbobot W) / 100, dikali gerbang risiko.
4. **Posisi** = target bot dominan (tick terakhir) x m, dikurangi aset ber-veto. Veto berlaku bila >= 2 agent atau veto keras data (RugCheck
   "danger", likuiditas di bawah batas).
5. **Risiko:** maks 25 % per aset, gross 1x, stop berbasis ATR (nilai dikunci di F3), batas rugi harian -3 % (meja datar sampai 00:00 UTC),
   perubahan < 2 % ekuitas tidak ditransaksikan; fee 0,05 % per sisi.

Konsekuensi yang dicatat jujur: bot harian mengubah target sekali sehari, jadi posisi meja v2 berubah saat **bot dominan berganti** atau **eksposur
berubah**, bukan tiap siklus.

## 6. Loop evaluasi dan perbaikan diri

- **Nilai per siklus:** `skor_bot` tiap agent dibandingkan dengan return portofolio tiap bot 5 menit dan 1 jam sesudahnya: IC (korelasi peringkat),
  hit rate pilihan utama, kalibrasi keyakinan.
- **Bobot agent otomatis (rumus terkunci):** diperbarui per jam dari IC 24 jam, dibatasi 0,5-2, sesudah pemanasan 288 siklus.
- **Rapor ke prompt:** tiap agent menerima kinerjanya sendiri (IC, hit rate, kesalahan terbesar); efeknya diukur sebelum/sesudah.
- **Ablasi:** buku bayangan "tanpa agent X" dan "tanpa sumber Y" mengukur kontribusi nyata tiap agent dan tiap sumber data.
- **Usulan evaluator:** agent evaluator harian menulis usulan perubahan fitur / prompt; berlaku hanya lewat versi bayangan (>= 288 siklus) dengan
  kriteria lulus yang ditulis lebih dulu, lalu dikunci hash + kata builder. Tidak ada perubahan diri diam-diam (SK-M13).

## 7. MCP = sinyal + data pendukung, berbayar lewat x402 (F-D111)

- **Deposit:** user mendepositkan **FAB** ke gerbang lewat x402 (tanpa gas; FAB uji dari faucet yang sudah ada) -> saldo per dompet.
- **Kunci API:** dompet menandatangani pesan -> kunci API terikat dompet.
- **Potong otomatis:** tiap panggilan alat MCP memotong saldo sesuai daftar harga; saldo kurang = ditolak + petunjuk deposit (SK-M11).
- **Alat berbayar:** `fabius_signal` 0,01 FAB (bot dominan, posisi, eksposur), `fabius_signal_explain` 0,02 FAB (output 3 agent, fitur, kontribusi),
  `fabius_data` 0,005 FAB (snapshot data pendukung); paket sinyal per bot x402 yang sudah ada tetap.
- **Gratis hanya penemuan:** `fabius_pricing` (harga + cara deposit) dan `fabius_account` (saldo).
- **Dicabut dari MCP:** alat data publik `fabius_dexscreener`, `fabius_rugcheck`, `fabius_bubblemaps`, `fabius_fomo` (P140) -> pengumpul internal
  Fabius; alat tingkat 0 gratis (F-D89) dipindah ke berbayar. Halaman web `/verify` tetap gratis.

## 8. Metrik dan kriteria lulus (usulan; dikunci saat tonggaknya disetujui)

| tonggak | keluar bila (terukur) |
|---|---|
| F1 | cakupan fitur >= 95 % siklus dalam 24 jam; kuota tiap sumber tidak terlampaui; 0 siklus terlambat karena pengumpul |
| F2 | >= 95 % output sah dalam 100 siklus; 100 % `faktor` dari daftar |
| F3 | bayangan >= 288 siklus berdampingan dengan v1; 0 pelanggaran batas risiko; laporan v1 vs v2 (PnL setelah fee, jumlah pindah bot) |
| F4 | metrik per agent + per sumber tercetak 3 hari berturut; bobot agent berubah sesuai rumus (tes); buku ablasi hidup |
| F5 | deposit -> saldo -> potong per panggilan teruji ujung-ke-ujung di testnet; alat data publik tercabut; `/desk` v2 menampilkan kontribusi |

## 9. Tonggak

| tonggak | isi | backlog |
|---|---|---|
| **E0** rencana | PRD ini + F-D110/F-D111 + baris T8 rencana SK-M4..SK-M13 | (halaman ini) |
| **F1** data | pengumpul di gerbang (cache + anggaran), registry alamat terkunci, fitur per aset + per bot + tes, panel kesehatan data | P153 |
| **F2** format v2 | prompt dengan tabel fitur, validasi `skor_bot` / `bot` / `faktor` / `eksposur` | P154 |
| **F3** mesin v2 | bot dominan, hysteresis, eksposur, veto, risiko; bayangan di samping v1 lalu menggantikan | P155 |
| **F4** evaluasi | rapor agent, bobot dinamis, buku ablasi, usulan evaluator | P156 |
| **F5** MCP berbayar + tampilan | deposit, saldo, kunci API, potong per panggilan; `/desk` v2 (matriks agent x bot, "kenapa bot ini"); halaman akun | P157 |

## 10. Alur kerja pengembangan (berlaku untuk setiap tonggak; sumber: [[08-Backlog/10 - Epik Eksekusi Venue]] §8 + [[Conventions]])

1. **Tulis dulu:** kriteria keluar + baris T8 rencana + status backlog 🟡.
2. **Kode + tes:** fungsi murni, jaringan dipalsukan; seluruh tes Python + forge + T8 lulus.
3. **Uji kering** dengan data dan model asli, tanpa komit dan tanpa efek -> bukti di [[07-Testing/01 - Test Commands]].
4. **Bayangan di produksi** (F3/F4) berdampingan dengan v1 >= 288 siklus -> hasil terukur.
5. **Kata builder** -> aktif / menggantikan. Transaksi, deploy kontrak, dan uang hanya atas kata builder.
6. **Vault seirama sebelum tonggak berikutnya:** backlog, catatan TL/C, Decisions bila ada keputusan, Inbox, Test Commands, Run It / Quick-Reference,
   hub -> gerbang (`sync_vault`, `check_links`, `hub_shape`, `check_failure_semantics`, `check_tool_citations`) -> commit tanpa atribusi AI ->
   kabari builder -> `prepush_check` -> push.

Aturan dasar ([[Conventions]]): setiap angka punya perintah yang mencetaknya dan dicetak ulang pada hari dikutip; tidak ada klaim melebihi yang diukur;
rumus dikunci sebelum data (versi baru = kunci baru); koreksi tetap terlihat ([[00-Overview/05 - Corrections]]).

## 11. Langkah builder (tidak bisa dikerjakan asisten)

- Mengisi faucet tBNB harian ke dompet gerbang `0x10c41a996Bab4042867c2dD388937A1e2743f1b1` (gas komit meja).
- Kata peralihan v1 -> v2 sesudah bayangan F3.
- Opsional: FOMO Starter ($49,99/bulan) bila ingin refresh per jam; akses API Bubblemaps bila ingin dipakai.
- Menguji deposit + MCP berbayar sebagai pengguna (F5).

## 12. Risiko dan pertanyaan terbuka

- Skor AI berhorison 5 menit mungkin tidak informatif - **diukur** (IC), bukan diasumsikan.
- Data DEX (pasangan on-chain) tidak sama dengan harga perp Binance; selisihnya fitur, bukan pengganti harga.
- Memecoin / listing baru sangat volatil; veto keras + batas 25 % per aset + batas harian adalah pagar, bukan jaminan.
- Model `:free` xkiro bisa kena batas; biaya kredit qwencloud untuk DeepSeek + Qwen.
- MCP berbayar menghapus pintu tingkat 0 gratis untuk agen (juri tetap bisa memeriksa lewat web `/verify`).
- Akses open interest + rasio taker Binance belum diukur dari Railway.

**Terkait:** [[00-Overview/03 - Decisions]] F-D110 / F-D111 · [[08-Backlog/01 - Backlog]] P153-P157 · [[04-Tools/TL34 - meja AI 5 menit]] ·
[[04-Tools/TL20 - server MCP]] · [[08-Backlog/06 - Epik Gerbang Sinyal]] · [[07-Testing/T8 - Semantik Kegagalan Operator]]

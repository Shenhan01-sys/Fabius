---
tags: [kompetitor, "KP3"]
---

# KP3 - AgentEco

**Bagian dari:** [[12-Competitors/00 - Hub Kompetitor]] · baseline: [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]]
**Sumber:** *(workspace)* `../Competitors/03-AgentEco/` — `page/page.txt` (`proj_5634cfa8383e15805c`), `deck/deck.txt` (PDF 12 slide), `video/transcript.txt` + `video/analysis.md` (`youtu.be/arWL6aU59ic`, 11:11), `github/README.md`, `github/commits.tsv` (78 commit, 26 Sep – 7 Okt); npm registry `@agenteco/sdk` (versi terbaru 0.1.2, 4 versi; **142 unduhan** 26 Sep–25 Okt via `api.npmjs.org/downloads/point/last-month/@agenteco/sdk`, 26 Okt); cek hidup 26 Okt: `agenteco-bnb.vercel.app` 200.

**Ringkas:** AgentEco adalah "economic layer for AI agents": marketplace + escrow on-chain di mana agen menemukan, menawar, menyewa, memverifikasi, dan membayar agen lain. Uang dikunci di `AgentEco.sol` sebelum kerja dimulai, teks penting (tugas, hasil, alasan sengketa, putusan) di-commit sebagai hash, sengketa diputus AI arbiter + dewan multisig dengan refund otomatis saat timeout, dan reputasi melekat ke alamat penjual. Ia bertabrakan dengan Fabius di **ketiga track** dan merupakan pesaing terdekat di dimensi "ekonomi antar-agen yang terbuka untuk pihak ketiga" — dimensi yang juga diklaim Fabius lewat `/submit-agent`, MCP, dan x402.

**Poin kunci:**
- Track: AI Agents + Consumer Apps + Finance & Commerce. Solo (Sanny Dermawan / Saypot San). Push terakhir 7 Okt (bekerja sampai deadline).
- Kontrak v3 terverifikasi BscScan + `ArbiterCouncil` multisig (1 suara memutus sengketa, 2 dari 3 untuk ubah fee/anggota/peran) + MockUSDT; 97 test Foundry termasuk fuzz, invariant, reentrancy.
- **Model bisnis ditegakkan kontrak:** fee 2,5 % dari payout penjual, dikunci per escrow, cap 10 %, diubah hanya oleh 2 suara dewan. Contoh nyata escrow #2003 (0,08 mUSDT → penjual 0,078, treasury 0,002).
- **SDK di npm** (`hire()` satu panggilan: cari → tawar → escrow → tunggu → verifikasi → bayar/sengketa), REST API, contoh buyer Python tanpa SDK. 142 unduhan dalam sebulan (tidak bisa dibedakan dari unduhan builder sendiri).
- AI di 5 peran (negosiasi, eksekusi, verifikasi, pembelaan penjual, arbitrase) dengan guardrail deterministik dan fallback Groq → Gemini → rule-based.
- Penilaian (pendapat): AgentEco **unggul** di bukti "agen benar-benar bertransaksi" dan model bisnis yang hidup di kontrak; Fabius **unggul** di standar ekosistem (ERC-8004, x402, MCP), bukti urutan waktu, dan presentasi; eksekusi teknis kira-kira setara.

**Detail:**

## 1. Profil AgentEco

| Aspek | AgentEco |
|---|---|
| Problem | Agen jago kerja tapi hanya untuk pemiliknya; agen yang bisa jual jasa sedikit dan tersebar. Inti: tidak ada kepercayaan antar agen asing — siapa bayar dulu, apakah hasil sesuai, siapa memutus sengketa, reputasi bisa dipalsukan, builder harus menyerahkan kunci. |
| Solution | Escrow dulu → hasil dicek (hash + JSON Schema + rubrik) → sengketa adil (AI arbiter merekomendasikan, dewan memutus, timeout = refund) → reputasi portabel per alamat (rating antar-agen satu pemilik dikecualikan) → terbuka untuk agen mana pun (bawa kunci, AI, harga sendiri). |
| Bukti di deck | escrow #2003 selesai dalam 54 d dengan fee; #2007 penjual & pembeli self-hosted dengan model Groq sendiri, rating 95; #2009 sengketa diputus dewan on-chain, refund penuh; #2004 pembeli Python tanpa SDK. |
| Batas yang diakui | kontrak belum diaudit, testnet; dewan kecil (roadmap: juri ber-stake); agen ter-host memegang kunci (roadmap: session key/smart account). |
| Stack | Solidity 0.8.34 + Foundry + OZ ReentrancyGuard; Node/Express 5 + Prisma 7 + Postgres (Supabase), API/host/keeper di Railway; Next.js 16 + wagmi + viem; SDK TypeScript. |
| Presentasi | Video 11 menit voice-over Bahasa Indonesia di atas rekaman layar; tempo lambat, tanpa hook visual di awal; deck 12 slide Inggris yang rapi. |

## 2. Head-to-head per kriteria juri (penilaian, tanpa bobot)

| Kriteria | Fabius | AgentEco | Siapa unggul & kenapa |
|---|---|---|---|
| Inovasi & orisinalitas | Bukti urutan sinyal, pra-registrasi strategi, desk multi-agen dengan formula terkunci, gerbang publik untuk bot luar | Marketplace + escrow + sengketa AI/dewan + negosiasi privat antar agen | **Setara, arah berbeda.** Escrow + marketplace agen adalah pola yang makin umum (tren "agent economy"); kombinasi sengketa AI → dewan → timeout refund rapi tapi tidak radikal. Fabius lebih jarang (bukti waktu), tapi lebih sempit kegunaannya. |
| Eksekusi teknis | 5 kontrak, 117 forge + 743 Python, rantai otomatis; x402 + MCP + ERC-8004 nyata; per 26 Okt alarm | 3 kontrak (v1→v3), 97 Foundry, keeper bot, SDK npm, deal end-to-end on-chain dengan token bergerak | **Setara.** Fabius lebih banyak lapisan dan memakai standar resmi BNB; AgentEco lebih sedikit lapisan tapi semuanya terlihat bekerja di video (dari create agent sampai refund sengketa). Keandalan hari ini menguntungkan AgentEco. |
| Dampak & kelayakan bisnis | 60/40 belum deploy, FAB tanpa nilai, tidak ada pembeli luar | Fee 2,5 % sudah hidup di kontrak, contoh nyata di treasury; pasar agent-to-agent | **AgentEco unggul.** Pendapatannya sudah mengalir (meski mUSDT) melalui jalur yang sama yang akan dipakai di mainnet; 60/40 Fabius masih "written and tested, not deployed". |
| UX | Banyak konsep; Privy login mudah; MCP untuk agen | Wizard create agent demo, marketplace berkartu (rating, harga, % sukses), order page yang meng-hash ulang teks di browser | **AgentEco sedikit unggul** untuk pengguna yang ingin mencoba: "buat agen → lihat ia bernegosiasi" adalah aha-moment yang jelas. Fabius unggul untuk agen (MCP) dan pengguna Telegram. |
| Presentasi & demo | Video 127 d terpoles, naratif kuat | Video 11 menit lambat tapi menunjukkan semua alur hidup, deck rapi | **Fabius unggul di presentasi; AgentEco unggul di kelengkapan demo.** Juri dengan waktu terbatas lebih mungkin menonton 2 menit Fabius sampai habis daripada 11 menit AgentEco. |

## 3. SWOT Fabius terhadap AgentEco

**Strengths (Fabius vs AgentEco)**
- **Memakai rel standar ekosistem BNB, bukan rel buatan sendiri.** Identitas agen Fabius di ERC-8004 Identity Registry resmi (tokenId 2494; analis 2558–2573) dan pembayaran lewat proxy x402 kanonis + Permit2. AgentEco memakai reputasi dan pembayaran di kontraknya sendiri. Untuk juri BNB Chain, "terintegrasi dengan standar" adalah argumen inovasi + teknis sekaligus.
- **MCP sebagai pintu agen.** Agen dengan MCP client bisa memakai Fabius tanpa SDK khusus; AgentEco butuh SDK npm/REST mereka.
- **Bukti waktu yang tidak dimiliki AgentEco.** AgentEco membuktikan *teks tidak berubah* sesudah commit; Fabius membuktikan *keputusan dibuat sebelum hasil* dan strategi dikunci sebelum bar. Itu lapisan yang lebih ketat untuk produk yang nilainya bergantung pada timing (sinyal).
- **Penolakan sebagai output.** Gerbang G1–G11 menolak 4/6 bot rumah sendiri, dan angkanya dipublikasikan. AgentEco tidak punya mekanisme penyaringan kualitas penjual sebelum listing (hanya laporan + delist).
- **Presentasi lebih padat** (127 d vs 11 menit).

**Weaknesses (Fabius vs AgentEco)**
- **Tidak ada transaksi antar agen yang hidup.** AgentEco memperlihatkan dua agen self-hosted bernegosiasi, escrow terdanai, hasil diterima, rating 95 — semua on-chain. Fabius punya agen luar uji (2573) milik builder dan x402 hanya dibeli builder; tidak ada adegan "agen A membayar Fabius untuk sinyal" yang direkam.
- **Model pendapatan belum di kontrak.** Fee AgentEco dipungut kontrak hari ini; `RevenueSplitter` Fabius belum di-deploy (LB2). Di kriteria kelayakan bisnis ini perbedaan antara "rencana" dan "berjalan".
- **Tidak ada SDK yang bisa di-`npm i`.** Developer bisa memulai AgentEco dalam satu baris; Fabius meminta submit lewat form `/submit` atau memakai MCP — lebih berat untuk developer yang ingin mencoba di hackathon.
- **Sengketa dan pemulihan.** AgentEco mendemokan sengketa dari awal sampai refund. Fabius tidak punya alur "pembeli tidak puas" untuk sinyal x402 (pembelian final).
- **Keandalan hari ini** *(cek hidup 26 Okt)*: AgentEco hidup; Fabius alarm + gate 500.

**Opportunities (karena AgentEco ada)**
- **Posisi "AgentEco untuk kerja umum, Fabius untuk sinyal yang bisa diaudit".** Escrow AgentEco memverifikasi hasil *sesudah* kerja; sinyal trading tidak bisa diverifikasi sesudah kerja tanpa bukti waktu. Kalimat ini membuat juri melihat Fabius sebagai spesialisasi yang perlu, bukan marketplace kedua.
- **Rekam satu transaksi agent-to-agent nyata sebelum Demo Day:** agen 2573 (atau klien MCP sederhana) membeli satu sinyal lewat x402, tx di BscScan. Ini menutup jarak terbesar terhadap AgentEco dengan biaya kecil, karena infrastrukturnya sudah ada.
- **Paket klien minimal.** Contoh klien MCP/x402 10 baris (Python atau TS) di README menyamai "`npm i` dan jalan" AgentEco.
- **Ambil pola biaya transparan.** AgentEco menampilkan fee dan bagian penjual sebelum tanda tangan; `/buy` Fabius bisa menampilkan harga 0,01 FAB + siapa menanggung gas + hak pembeli secara eksplisit.

**Threats (dari AgentEco)**
- **Bertemu di ketiga track dan Grand Prize.** AgentEco adalah satu-satunya kompetitor yang tumpang tindih penuh dengan Fabius *dan* menjual narasi "ekonomi agen terbuka". Juri bisa menilai keduanya sebagai kategori yang sama dan memilih yang buktinya lebih "transaksional".
- **Bukti adopsi npm** (142 unduhan) bisa dibaca juri sebagai traksi, meski tidak terbukti bukan dari builder. Fabius tidak punya metrik adopsi apa pun yang boleh dikutip.
- **Bahasa Indonesia di video AgentEco** dekat dengan audiens lokal panitia; Fabius full English. Untuk juri lokal ini bisa jadi nilai plus kecil bagi AgentEco.

## 4. Pertanyaan juri yang kemungkinan muncul
- "Apa bedanya dengan AgentEco / marketplace agen lain?" → bukti urutan + pra-registrasi + gerbang; marketplace lain memverifikasi hasil kerja, Fabius memverifikasi kapan keputusan dibuat — satu-satunya bukti yang berarti untuk sinyal.
- "Ada agen luar yang sudah membayar?" → jawaban jujur: belum (claims cheat sheet melarang "used by other agents"); tunjukkan jalurnya hidup dengan tx uji.

## 5. Langkah konkret sebelum Demo Day 31 Okt (pelajaran dari AgentEco)
1. Rekam satu pembelian sinyal oleh agen (bukan manusia) lewat x402/MCP, dengan tx BscScan.
2. Tambahkan contoh klien minimal di README dan halaman `/mcp`.
3. Di pitch, sebut eksplisit perbedaan "verifikasi hasil kerja" (AgentEco) vs "verifikasi waktu keputusan" (Fabius).

## 6. Batas analisis ini
- 97 test Foundry dan deal on-chain AgentEco dari deck/halaman mereka; tx #2003/#2007/#2009 tidak diperiksa langsung di BscScan.
- Angka unduhan npm tidak membedakan unduhan builder, CI, atau mirror.

**Terkait:** [[12-Competitors/KP2 - Perago]] · [[12-Competitors/KP4 - BagiPanen]] · [[05-Ecosystem/02 - x402 Payment]]

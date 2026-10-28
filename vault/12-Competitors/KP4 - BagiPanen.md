---
tags: [kompetitor, "KP4"]
---

# KP4 - BagiPanen

**Bagian dari:** [[12-Competitors/00 - Hub Kompetitor]] · baseline: [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]]
**Sumber:** *(workspace)* `../Competitors/04-BagiPanen/` — `page/page.txt` (`proj_553d22d0e66a264629`), `deck/deck.txt` (Canva 7 slide, ditranskripsi dari browser), `video/transcript.txt` + `video/analysis.md` (`youtu.be/wyMdC4O7ygk`, 2:59), `github/README.md`, `github/commits.tsv` (118 commit, 1–20 Okt); cek hidup 26 Okt: `bagipanen.vercel.app` 200, `gh run list -R MrPrinceAli/bagipanen` → workflow "Agen AI verifikator" sukses 2026-10-26 10:32Z.

**Ringkas:** BagiPanen adalah pembiayaan musim tanam untuk petani kecil Indonesia sebagai pengganti "ijon": investor mendanai satu musim dengan stablecoin, dana dikunci di escrow per musim, dan cair tiga tahap hanya jika **dua kunci** — agen AI ber-ERC-8004 (Gemini Vision + EXIF + cuaca Open-Meteo + sidik foto) dan koperasi — sama-sama menyetujui foto lahan. Setelah panen kontrak membagi hasil 55/40/5 dan menulis rapor petani on-chain. Ia bertabrakan dengan Fabius di **ketiga track** dan, dari delapan kompetitor, adalah yang **paling kuat di kriteria dampak dan presentasi**: problem lokal yang menyentuh, agen AI yang dibatasi manusia, ERC-8004 dipakai sampai ke reputation registry, dan masih dirawat sesudah deadline.

**Poin kunci:**
- Track: AI Agents + Consumer Apps + Finance & Commerce. Tim 2 orang (SandiJawa: MrPrinceAli, doaibu888). Repo dibuat 1 Okt (di dalam jendela perpanjangan), commit manusia terakhir 18 Okt, agen berjalan otomatis sampai 26 Okt.
- 5 kontrak terverifikasi (`CampaignFactory`, `HarvestCampaign`, `ReservePool`, `ReputationBook`, dsb.), **90 test Foundry dengan 100 % line/branch/function coverage** (klaim slide akhir video).
- **ERC-8004 dipakai dua sisi:** agen #2544 di IdentityRegistry resmi, `CampaignFactory` hanya menerima verdict dari pemilik NFT agen itu, dan koperasi menilai tiap verdict di ReputationRegistry resmi.
- Arsitektur tanpa server dan tanpa database: kontrak memegang uang dan state, IPFS memegang foto/verdict, agen AI satu-satunya proses off-chain (GitHub Actions ±5 menit, log publik).
- Hasil satu musim testnet: modal 1.000, panen 1.650 → investor 1.260 (return 26 %), petani +357,5, cadangan 32,5. Jalur juri tanpa wallet (`/coba`, `/masuk`).
- Penilaian (pendapat): BagiPanen **unggul** di dampak, UX untuk juri, presentasi, dan pemakaian ERC-8004; Fabius **unggul** di kedalaman primitif bukti (urutan waktu, pra-registrasi, gerbang statistik) dan platform terbuka; eksekusi teknis kira-kira setara, keandalan hari ini menguntungkan BagiPanen.

**Detail:**

## 1. Profil BagiPanen

| Aspek | BagiPanen |
|---|---|
| Problem | Petani kecil tak punya riwayat kredit (tak tercatat di SLIK OJK) → modal musim dari tengkulak via ijon (panen dijual murah sebelum tumbuh), risiko di petani, untung di tengkulak. Investor ritel tak bisa melihat apakah uang sampai ke lahan. |
| Solution | Escrow per musim (`CampaignFactory` → `HarvestCampaign`), token porsi non-transferable 1:1, tranche 40/35/25 % dengan dua kunci (AI `recordVerdict` + koperasi `verifierDecision`), waterfall 55/40/5 hard-coded, `ReservePool` untuk gagal panen, `ReputationBook` = rapor petani. |
| Agen AI | Baca konteks kontrak → unduh foto IPFS, SHA-256 → tolak foto daur ulang → EXIF GPS ≤ 2 km & ≤ 7 hari → cuaca 14 hari → Gemini Vision JSON terstruktur → setuju hanya jika confidence ≥ 0,70 dan semua cek lolos → verdict ke IPFS → `recordVerdict(ok, reasonCID)`. Alasan ditampilkan dalam Bahasa Indonesia. Retry + fallback model, idempoten. |
| Momen demo | Foto stok lahan mekanis (kemungkinan Midwest AS) ditolak 40 % yakin, koperasi juga menolak, uang tidak bergerak. |
| Roadmap | Pilot dengan koperasi mitra; social login + gas sponsorship; on-ramp Rupiah; fee kecil dari laba panen; nanti IoT/drone/satelit, asuransi parametrik, pasar sekunder token porsi, mitra crowdfunding berizin OJK. |
| Presentasi | Video 2:59 Inggris, slide editorial hijau-emas + rekaman app, subtitle; deck Canva 7 slide (problem, solusi vs ijon, 5 langkah + hasil 26 %, verifier AI, roadmap, penutup). UI app berbahasa Indonesia dengan alasan eksplisit. |

## 2. Head-to-head per kriteria juri (penilaian, tanpa bobot)

| Kriteria | Fabius | BagiPanen | Siapa unggul & kenapa |
|---|---|---|---|
| Inovasi & orisinalitas | Bukti urutan sinyal + pra-registrasi + desk multi-agen + gerbang publik | Dua kunci AI + koperasi untuk RWA pertanian, ERC-8004 identity + reputation sebagai pagar pemberi verdict | **Setara.** Pembiayaan pertanian on-chain sudah ada (crowdfarming), tapi "AI verifier ber-ERC-8004 yang dinilai koperasi di reputation registry" adalah pemakaian standar baru yang tepat sasaran. Fabius lebih orisinal secara primitif, BagiPanen lebih orisinal secara penerapan. |
| Eksekusi teknis | 5 kontrak, 117 forge + 743 Python, rantai otomatis; per 26 Okt alarm + gate 500 | 5 kontrak, 90 test 100 % coverage, agen berjalan di Actions dengan log publik, tanpa server/DB, sukses hari ini | **Setara secara isi, BagiPanen unggul secara keandalan hari ini.** Arsitektur BagiPanen lebih sederhana (lebih sedikit yang bisa rusak), dan yang ada bekerja saat dicek. |
| Dampak & kelayakan bisnis | Untuk trader/pembeli sinyal; tidak ada edge, belum ada pengguna | Untuk petani kecil + investor ritel Indonesia; return 26 % di satu siklus contoh; jalur ke mitra OJK | **BagiPanen unggul jelas.** Dampak sosialnya konkret, lokal, dan sesuai misi panitia ("every Indonesian builder… genuinely runs onchain"). |
| UX | Banyak konsep; Privy + Telegram | Mode juri tanpa wallet, satu klik per peran (petani, investor, koperasi, admin), alasan penolakan dalam bahasa petani | **BagiPanen unggul.** Dirancang untuk juri dan pengguna awam sekaligus. |
| Presentasi & demo | Video 127 d terpoles, hook sejarah, tanpa transaksi di layar | Video 3 menit terpoles, jalur gagal + jalur sukses, angka hasil panen, alasan AI yang bisa dibaca | **BagiPanen unggul tipis.** Kualitas produksi setara, tapi BagiPanen memperlihatkan produk yang bekerja dan momen "AI menolak foto palsu" yang mudah diingat. |

## 3. SWOT Fabius terhadap BagiPanen

**Strengths (Fabius vs BagiPanen)**
- **Bukti yang tidak bisa dipalsukan oleh operator.** Verdict BagiPanen bisa dibuat kapan saja oleh pemilik agen #2544 (tidak ada batas waktu terhadap foto/harga); Fabius menegakkan bahwa keputusan dibuat sebelum hasil ada (`TooLate`, `LockedAfterBar`). Kalau juri bertanya "bagaimana kalian tahu AI tidak diatur belakangan?", Fabius punya jawaban kontrak.
- **Penyaringan statistik terhadap diri sendiri.** Fabius menolak 4/6 bot rumah dengan gerbang G1–G11 dan mengukur false-positive ±1 %. BagiPanen memvalidasi foto, bukan kualitas keputusan agennya secara statistik (akurasi hanya dari rating koperasi).
- **Platform, bukan aplikasi tunggal.** Pihak ketiga bisa membawa bot/agen ke Fabius; BagiPanen satu alur vertikal.
- **Rel pembayaran agen.** x402 + MCP memungkinkan agen lain membeli keluaran Fabius; BagiPanen tidak menjual keluaran agennya ke agen lain.

**Weaknesses (Fabius vs BagiPanen)**
- **Tidak ada manusia di cerita.** BagiPanen punya petani di Gunungkidul dan Sidrap, koperasi, investor ritel. Fabius punya "bot" dan "pembeli sinyal" tanpa wajah. Untuk kriteria dampak, ini selisih terbesar.
- **Tidak ada sudut Indonesia.** BagiPanen menyebut SLIK OJK, ijon, tengkulak, Bahasa Indonesia di UI. Fabius tidak menyentuh konteks lokal sama sekali di submission-nya, padahal panitia menyebut "every Indonesian builder" dan Finance & Commerce dideskripsikan "for Indonesia".
- **ERC-8004 dipakai lebih dangkal.** Fabius terdaftar di IdentityRegistry, tapi validator-nya milik sendiri dan reputasi tidak diisi pihak ketiga; BagiPanen menjadikan identitas agen sebagai syarat kontrak dan reputasinya diisi koperasi. Di depan juri BNB, pemakaian BagiPanen lebih "benar".
- **Keandalan dan perawatan.** BagiPanen masih memperbaiki RPC dan snapshot log pada 18 Okt dan agennya sukses hari ini. Fabius tidak punya commit manusia sejak 7 Okt dan rantainya berhenti 13 Okt *(cek hidup 26 Okt)* — sinyal yang berlawanan menjelang Demo Day.
- **Jalur juri tanpa wallet lebih jelas di BagiPanen** (`/coba` tur terpandu). Fabius butuh Privy login dan pemahaman konsep untuk merasakan nilainya.

**Opportunities (karena BagiPanen ada)**
- **Tiru jalur juri.** Satu halaman "tour" Fabius: pilih satu bot → lihat spec terkunci (tx) → lihat commit bar kemarin (tx) → klik verify → lihat hasil. Tiga klik tanpa login.
- **Tunjukkan reputasi diisi pihak lain.** Kalau satu agen analis menerima umpan balik di ReputationRegistry dari pihak non-builder (atau validator independen), kelemahan ERC-8004 di atas berkurang.
- **Tambah satu kalimat konteks Indonesia yang jujur:** penipuan "grup sinyal" Telegram dan screenshot profit adalah masalah nyata di komunitas trader kripto Indonesia — tanpa mengklaim data yang tidak dimiliki (Not Yet Proven #10: nol sumber primer regulasi), cukup sebagai motivasi.
- **Pinjam struktur "momen gagal yang mudah diingat".** BagiPanen: AI menolak foto stok. Fabius: kontrak menolak commit yang terlambat, atau gerbang menolak bot sendiri yang sebelumnya terlihat profitable (B2-RS Sharpe 1,29 dikoreksi ke 0,85 — angka yang ada di Corrections).

**Threats (dari BagiPanen)**
- **Kandidat kuat Grand Prize dan AI Agents.** BagiPanen memenuhi semua kriteria dengan sedikit celah: dampak lokal, agen AI dengan guardrail manusia, standar BNB terbaru, demo tanpa wallet, produksi rapi. Ia menetapkan standar yang sulit dikejar oleh proyek infrastruktur abstrak.
- **Narasi "AI proposes, human/contract decides" sudah dipakai dengan contoh yang lebih kongkret.** Kalau Fabius memakai slogan "The AI picks the rulebook; code computes the position", juri yang baru melihat BagiPanen akan membandingkan dan merasakan Fabius lebih abstrak.
- **Kemungkinan finalis.** Pola commit pasca-deadline (perbaikan RPC log, snapshot) konsisten dengan tim yang bersiap untuk Demo Day; status finalis tidak dipublikasikan, jadi ini dugaan.

## 4. Pertanyaan juri yang kemungkinan muncul
- "Siapa pengguna nyata Fabius di Indonesia?" → jawaban jujur hari ini: belum ada; target adalah pembeli sinyal dan pembuat bot, problem-nya penipuan track record. Jangan mengarang angka.
- "Kenapa memakai ERC-8004 kalau validator-nya kalian sendiri?" → akui (claims cheat sheet melarang "trustless validation"), tunjukkan rencana validator independen.

## 5. Langkah konkret sebelum Demo Day 31 Okt (pelajaran dari BagiPanen)
1. Pulihkan rantai dan buat agen/worker terlihat hidup hari itu (BagiPanen sukses hari ini; Fabius harus juga).
2. Buat tur juri tanpa login tiga klik.
3. Siapkan satu "momen gagal yang mudah diingat" berbasis kontrak atau gerbang.
4. Satu slide konteks Indonesia yang tidak melebihi bukti.

## 6. Batas analisis ini
- 90 test dan 100 % coverage dari slide akhir video BagiPanen; tidak dijalankan ulang.
- Hasil musim 1.000 → 1.650 adalah data testnet mereka (siklus contoh), bukan hasil petani nyata.
- Status finalis tidak dipublikasikan; "kemungkinan finalis" adalah dugaan dari pola commit.

**Terkait:** [[12-Competitors/KP3 - AgentEco]] · [[12-Competitors/KP5 - SAMA]] · [[05-Ecosystem/01 - ERC-8004 Identity]]

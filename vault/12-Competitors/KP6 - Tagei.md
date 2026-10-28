---
tags: [kompetitor, "KP6"]
---

# KP6 - Tagei

**Bagian dari:** [[12-Competitors/00 - Hub Kompetitor]] · baseline: [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]]
**Sumber:** *(workspace)* `../Competitors/06-Tagei/` — `page/page.txt` (`proj_16da68317c5fd40d36`), `deck/deck.txt` (Canva 8 slide, ditranskripsi dari browser), `video/transcript.txt` (lirik lagu) + `video/analysis.md` (`youtu.be/92enL8Kd4uA`, 2:27), `github/README.md`, `github/commits.tsv` (85 commit, 27 Sep – 5 Okt); cek hidup 26 Okt: `bnb-play.vercel.app` (app yang ditautkan) **HTTP 402 `DEPLOYMENT_DISABLED`**, `tagei.vercel.app` (situs pemasaran) 200.

**Ringkas:** Tagei adalah game trading 30 detik: pilih LONG/SHORT, tahan tombol, roket mengikuti harga nyata (BNB/BTC/ETH/SOL/DOGE) sampai target, stop, cash out, atau waktu habis, lalu ronde diselesaikan on-chain dari checkpoint oracle Supra DORA-2 yang direkam tiap detik — dengan receipt. Ada co-pilot AI "PIX" yang menjelaskan tapi dilarang memprediksi. Tagei **tidak** ikut AI Agents; ia bertemu Fabius di Consumer Apps, Finance & Commerce, dan Grand Prize. Menariknya, di balik kemasan game, **inti teknis Tagei sangat mirip Fabius**: kebenaran direkam sebelum hasil ("Settlement never uses what you see on screen — only what is recorded on-chain"), evaluator yang sama di TypeScript dan Solidity diuji dengan golden vectors, dan AI yang dibatasi agar tidak memprediksi.

**Poin kunci:**
- Track: Consumer Apps + Finance & Commerce. Tim "kingbob", praktis satu kontributor (84 dari 85 commit oleh Candra0x6). Push terakhir 5 Okt.
- Kontrak (testnet 97): `BnbPlayArena`, `CheckpointOracle`, `StatelessSupraVerifier`, TestUSD + Faucet; Solidity 0.8.30 + Foundry, **100+ test** (unit, fuzz, invariant, differential) + review keamanan internal (deck slide 6).
- Fairness: harga masuk dikunci 3 detik sesudah commit; harga Supra diverifikasi on-chain dan ditulis ke log checkpoint append-only tiap detik; oracle diam 60 detik → ronde batal dan stake kembali.
- UX yang sangat dipikirkan: 700 ms hold dengan haptic, slide-off > 24 px membatalkan, target ≥ 44 px, mode kidal, guest wallet gasless via relayer, XP tidak naik dengan besar taruhan.
- **App yang ditautkan mati (402) per 26 Okt**; video adalah music video tanpa demo nyata.
- Penilaian (pendapat): Tagei **unggul** di UX dan branding; Fabius **unggul** di demo yang bisa diverifikasi hari ini (meski alarm), relevansi AI, dan kedalaman bukti; eksekusi teknis inti setara, keandalan publik keduanya bermasalah.

**Detail:**

## 1. Profil Tagei

| Aspek | Tagei |
|---|---|
| Problem | Trade pertama adalah tembok: dompet, gas, order type, candlestick, leverage; HP satu tangan memperburuk; app "fun" berbasis harga sulit dipercaya (angka acak tak terverifikasi) dan mendorong mengejar kerugian. |
| Solution | Market Track (garis + roket), satu gestur, guest gasless, receipt per ronde dari checkpoint oracle on-chain, PIX menjelaskan tanpa memprediksi, progres berbasis XP bukan stake. |
| Arsitektur | Client (React 19, Vite, Canvas 2D, signer EIP-712 guest) → Server Hono di Railway (price hub Supra, relayer bayar gas, recorder 1 checkpoint/detik, leaderboard) → Chain (`BnbPlayArena`, `CheckpointOracle`, `StatelessSupraVerifier`, TestUSD). Eksternal: Supra DORA-2, Claude Haiku 4.5 untuk PIX, Postgres, Vercel + Railway. |
| Roadmap | tier HYPER/WARP setelah ekonomi lane tervalidasi, multisig + timelock untuk peran admin, jalur oracle kedua, lebih banyak market. |
| Presentasi | Music video 2:27 kinetic typography (lirik, bukan penjelasan), deck 8 slide teknis dan jelas. |

## 2. Head-to-head per kriteria juri (penilaian, tanpa bobot)

| Kriteria | Fabius | Tagei | Siapa unggul & kenapa |
|---|---|---|---|
| Inovasi & orisinalitas | Bukti urutan sinyal + pra-registrasi + desk multi-agen | Trading sebagai game satu gestur dengan settlement dari checkpoint oracle | **Setara.** Prediksi harga jangka pendek sebagai game sudah banyak (pola "up/down"); keunikan Tagei ada di settlement yang diverifikasi dan desain anti-kecanduan. Fabius lebih orisinal di primitif, Tagei di pengalaman. |
| Eksekusi teknis | 5 kontrak, 117 forge + 743 Python, cross-language vectors (`gen_signal_vectors.py`), rantai otomatis | 4+ kontrak, 100+ test termasuk differential TS↔Solidity, recorder oracle per detik, relayer | **Setara secara rekayasa.** Keduanya memakai pola yang sama (evaluator dua bahasa + golden vectors). Keduanya juga punya masalah keandalan publik hari ini: Tagei app 402, Fabius alarm + gate 500. Fabius sedikit unggul karena halaman verifikasinya masih bisa dibuka. |
| Dampak & kelayakan bisnis | Pembeli sinyal & pembuat bot; belum ada pengguna | Pemula kripto; tidak ada model bisnis tertulis; produk mendekati permainan harga dengan taruhan | **Setara rendah.** Tagei punya pasar besar tapi risiko regulasi (judi/derivatif) tinggi dan tidak dibahas; Fabius punya model tertulis tapi tanpa edge. |
| UX | Banyak konsep | Salah satu UX paling dipikirkan dari sembilan proyek (haptic, aksesibilitas, guest gasless) | **Tagei unggul jelas** — di atas kertas. Juri tidak bisa mencobanya hari ini karena app mati. |
| Presentasi & demo | Video 127 d menjelaskan mekanisme; deck jujur | Music video tanpa penjelasan dan tanpa demo; deck jelas | **Fabius unggul.** Video Tagei kuat sebagai branding tapi tidak menjawab "apa yang dibangun"; juri harus ke deck. |

## 3. SWOT Fabius terhadap Tagei

**Strengths (Fabius vs Tagei)**
- **Penjelasan mekanisme sampai ke juri.** Video Fabius menjelaskan lock → commit → reveal → desk; video Tagei hanya lirik. Untuk kriteria presentasi + demo, Fabius lebih baik walau v1.
- **Ada di AI Agents dengan AI yang substantif.** PIX adalah penjelas yang dibatasi; analis Fabius ber-ERC-8004 dan keputusan mereka di-anchor. Tagei tidak bersaing di track AI sama sekali.
- **Tidak menyentuh taruhan.** Fabius sengaja paper, tanpa stake pengguna, dan menolak skema yield/early-bird (F-D17/F-D18). Tagei adalah permainan berbasis stake dengan tier leverage (CRUISE 1,5x; HYPER/WARP direncanakan) — juri yang sensitif regulasi Indonesia bisa melihat risiko perjudian.
- **Kode dan bukti terbuka lebih luas.** Fabius memublikasikan hasil negatif dan koreksinya; Tagei tidak membahas risiko pengguna kalah.

**Weaknesses (Fabius vs Tagei)**
- **UX dan aksesibilitas.** Tagei mendokumentasikan detail gestur, target sentuh, mode kidal, reduced motion. Fabius tidak punya satu pun pertimbangan aksesibilitas yang terdokumentasi di submission.
- **Branding dan daya ingat.** Maskot, warna, roket, slogan "Pick a side. Hold. Ride." — Tagei langsung dipahami dalam 3 detik. Fabius butuh paragraf untuk menjelaskan kenapa urutan penting.
- **Guest gasless sejak detik pertama.** Tagei: tanpa wallet, tanpa install, relayer bayar gas. Fabius: gasless untuk pembeli x402, tapi masuk tetap lewat Privy login.

**Opportunities (karena Tagei ada)**
- **Bukti bahwa "kebenaran direkam sebelum hasil" diterima juga di sisi konsumen.** Tagei memakai prinsip yang sama untuk game; Fabius bisa mengutip prinsip itu sebagai pola umum yang sedang muncul, dan memposisikan diri sebagai versinya untuk sinyal/agen.
- **App Tagei mati.** Di Consumer dan Finance, satu kompetitor dengan UX kuat tidak bisa didemokan hari ini — selama Fabius memulihkan rantainya sebelum 31 Okt, Fabius punya sesuatu yang bisa diklik dan Tagei tidak.
- **Ambil pola "XP tidak naik dengan stake" sebagai bahasa etika.** Fabius sudah punya prinsip sejenis (tanpa fee atas profit, tanpa early-bird); menyebutnya eksplisit di pitch memperkuat kesan bertanggung jawab di depan juri yang membandingkan dengan game trading.

**Threats (dari Tagei)**
- **Di Consumer Apps, juri yang membaca deck Tagei akan menilai UX-nya sangat tinggi.** Kalau Tagei memulihkan deployment sebelum Demo Day, ia menjadi pesaing kuat di track itu.
- **Kemiripan teknis bisa mengaburkan pembeda Fabius.** "Settlement only uses what's recorded on-chain" dan "signals sealed before the outcome" terdengar seperti klaim yang sama bagi juri non-teknis.

## 4. Pertanyaan juri yang kemungkinan muncul
- "Apa bedanya merekam sinyal sebelum hasil dengan merekam harga oracle sebelum settlement?" → Tagei membuktikan *harga* yang dipakai jujur; Fabius membuktikan *keputusan* pihak yang memberi sinyal tidak ditulis belakangan dan strateginya tidak diubah. Pihak yang diperiksa berbeda.

## 5. Langkah konkret sebelum Demo Day 31 Okt (pelajaran dari Tagei)
1. Pastikan setiap tautan di halaman submission Fabius hidup (pelajaran langsung dari 402 Tagei): landing, `/verify`, `/status`, gate x402, MCP.
2. Satu slogan tiga kata untuk Fabius yang bisa dipahami tanpa penjelasan (kandidat dari deck sendiri: "Sealed before outcome").
3. Sebut prinsip etis (tanpa taruhan pengguna, tanpa fee atas profit) dalam satu baris.

## 6. Batas analisis ini
- 100+ test Tagei dari deck; tidak dijalankan ulang.
- Status 402 dicek 21 dan 26 Okt; apakah Tagei memulihkannya sebelum 31 Okt tidak diketahui.

**Terkait:** [[12-Competitors/KP5 - SAMA]] · [[12-Competitors/KP7 - Kawal]] · [[01-Agent/A4 - Trust Gating and Real-Money Rules]]

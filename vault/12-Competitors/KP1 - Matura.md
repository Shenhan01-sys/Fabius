---
tags: [kompetitor, "KP1"]
---

# KP1 - Matura

**Bagian dari:** [[12-Competitors/00 - Hub Kompetitor]] · baseline: [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]]
**Sumber:** *(workspace)* `../Competitors/01-Matura/` — `page/page.txt` (halaman submission `proj_e7b7a5ec0b55d9a559`), `deck/deck.txt` (PDF 18 slide), `video/transcript.txt` + `video/analysis.md` (`youtu.be/19qaaHxEmRc`, 4:09), `github/README.md`, `github/commits.tsv`, `github/src/docs/test-report.md`; cek hidup 26 Okt (`curl -sL -w '%{http_code}' https://app.usematura.xyz` → 200 `/vaults`).

**Ringkas:** Matura adalah protokol "best-execution liquidity" untuk pendapatan yang sudah diterima tapi belum cair (gaji, payout freelance, marketplace). Issuer meng-attest klaim, pengguna minta *jumlah* (bukan fasilitas), router integer deterministik memilih kombinasi vault termurah, kontrak `MaturaRouter.executeRoute` memvalidasi ulang setiap leg sebelum dana bergerak, dan settlement diperiksa konservasinya. Ia **tidak** ikut track AI Agents dan tidak memakai AI sama sekali, jadi ia hanya bertabrakan dengan Fabius di Consumer Apps, Finance & Commerce, dan Grand Prize. Dari delapan kompetitor yang dipetakan, Matura adalah yang **paling rapi secara rekayasa** dan paling dekat dengan Fabius secara filosofi ("checkable, not asserted"), sehingga ia pembanding paling keras untuk kriteria eksekusi teknis.

**Poin kunci:**
- Track: Consumer Apps + Finance & Commerce. Solo builder (Arjuna Marcelino). BSC testnet 97. Submit 28 Sep, edit terakhir 7 Okt.
- 6 kontrak inti, tanpa proxy, diklaim terverifikasi di BscScan; Solidity 0.8.28 + OZ 5.6.1; 2 vault bersaing (Stable, Flex).
- Uji (laporan repo sendiri, `docs/test-report.md`): 169 test kontrak (unit + integrasi + fuzz + gas), 298 unit test monorepo, e2e 6 + 14; gerbang CI ABI-freshness, manifest-freshness, demo-fixture-freshness. 333 commit dalam ±12 hari (24 Sep – 6 Okt).
- Bukti siklus penuh di halaman: 3 tx yang bisa diklik (`ClaimRegistered`, `RouteExecuted`, `ClaimSettled`).
- App hidup 26 Okt; video 4:09 animasi produk + rekaman app asli; deck 18 slide dengan slide "What's not trustless".
- Penilaian keseluruhan (pendapat): di irisan track, Matura **unggul** di eksekusi teknis hari ini, kelayakan bisnis, dan UX; Fabius **unggul** di relevansi AI dan kebaruan primitif kepercayaan; presentasi kira-kira **setara** dengan gaya berbeda.

**Detail:**

## 1. Profil Matura (yang dilihat juri)

| Aspek | Matura | Catatan |
|---|---|---|
| Problem | Uang yang sudah "earned" belum "usable"; produk EWA/factoring: siloed, single-provider pricing, all-or-nothing | "market-structure problem, not a credit problem" |
| Solution | Aggregate (klaim ter-attest issuer) → best-execution routing (bigint optimizer, byte-identical untuk input + blok sama) → verifiable settlement (EIP-712, `executeRoute` re-check, konservasi) | Mirror off-chain `_validateLegs` = Solidity → "no quote-vs-execution gap" |
| Bisnis | take-rate pada spread pembiayaan; 3 sisi (pengguna, issuer, vault); GTM 3 fase (testnet → issuer nyata → vault pihak ketiga) | ada narasi "wedge, not a feature" |
| Batas yang diakui | issuer trust, testnet-only (MockUSDT), belum diaudit | slide 16 deck |
| Stack | Hardhat 3, NestJS + Prisma/Postgres, indexer reorg-safe, Next.js 15 + wagmi + SIWE, Fumadocs, pnpm/Turborepo | non-custodial: API hanya menyiapkan calldata tak-bertanda-tangan |
| AI | tidak ada | tidak masuk track AI Agents |
| Hidup 26 Okt | app 200, docs 200 | — |

Video (lihat `video/analysis.md`): persona Rizki menerima 20.000 USDT 13 hari lagi, minta 5.000 saja, Stable Vault 1,11 % menang, biaya 56,12 USDT, settlement mengembalikan 14.943,88. Angka konkret, satu alur, rekaman app nyata berlabel "BNB Testnet · illustrative data".

## 2. Head-to-head per kriteria juri (penilaian, tanpa bobot)

| Kriteria | Fabius | Matura | Siapa unggul & kenapa |
|---|---|---|---|
| Inovasi & orisinalitas | Commit-sebelum-hasil untuk sinyal trading + pra-registrasi strategi on-chain + desk AI yang dibatasi formula | Best-execution router untuk receivable, slice parsial lintas vault, determinisme byte-identical | **Fabius sedikit unggul.** EWA/factoring on-chain sudah ada di pasar (konsepnya dikenal); "urutan sebagai bukti" untuk agen AI lebih jarang. Tapi Matura menyajikan kebaruannya lebih tajam ("you request an amount, not a facility"). |
| Eksekusi teknis | 5 kontrak, 117 forge + 743 Python lulus (7 Okt), rantai otomatis GitHub + Railway, MCP, x402 | 6 kontrak terverifikasi, 169 + 298 + 20 test, gerbang freshness di CI, indexer reorg-safe, 3 tx siklus penuh diklik dari halaman | **Matura unggul hari ini.** Cakupan Fabius lebih luas, tapi per 26 Okt `/status` Fabius `alarm` dan gate x402 HTTP 500, sementara app Matura hidup. Juri yang mengklik akan melihat satu sistem yang bekerja dan satu yang menyala merah. |
| Dampak & kelayakan bisnis | Jual sinyal per panggilan (FAB tanpa nilai), 60/40 untuk publisher (belum deploy), 0/6 bot lulus forward, tidak ada pembeli luar | Take-rate spread, pasar gig/freelance yang nyata, rencana issuer partner | **Matura unggul.** Fabius secara jujur berkata produknya belum punya sesuatu yang layak dibeli (tidak ada edge); Matura punya nilai ekonomi yang jelas meski masih sintetis. |
| UX | Banyak halaman (`/verify`, `/status`, `/desk`, `/buy`, `/submit`…), Privy login, Telegram Mini App; konsep berat (G1–G11, lock, F-D16) | Wizard 5 langkah, kartu "Before you sign" (diterima, biaya, retained, vault terpilih), non-custodial | **Matura unggul** untuk track Consumer: satu tugas, satu alur. Fabius unggul di jangkauan kanal (web + Telegram + MCP), tapi jangkauan bukan kemudahan. |
| Presentasi & demo | Video v1 127 d, hook sejarah kuat, motion graphics, tapi tidak ada layar transaksi nyata; deck 12 slide jujur | Video 4:09 persona + angka konkret + rekaman app; deck 18 slide + slide batas kepercayaan | **Setara, beda gaya.** Fabius lebih mudah diingat (Fabius vs Hannibal), Matura lebih mudah dipahami (Rizki butuh 5.000). Matura menang di "demo", Fabius menang di "pitch". |

## 3. SWOT Fabius terhadap Matura

**Strengths (Fabius vs Matura)**
- **Primitif kepercayaan yang lebih kuat terhadap pihak yang diperiksa.** Matura tetap bergantung pada issuer yang di-allowlist (slide 16 mereka sendiri: "Issuer trust"). Fabius tidak meminta siapa pun dipercaya untuk *kapan* keputusan dibuat: `TooLate` dan `LockedAfterBar` ditegakkan kontrak, verifikasi tanpa kunci.
- **Ada di track AI Agents**, track terbesar (141 proyek), yang tidak diikuti Matura. Fabius punya dua kesempatan podium (AI Agents + Grand Prize) di mana Matura tidak hadir di salah satunya.
- **Platform terbuka.** Bot dan agen luar bisa masuk lewat gerbang yang sama (`/submit`, `/submit-agent`, MCP). Matura membuka sisi likuiditas hanya di fase 3 GTM.
- **Kejujuran yang lebih dalam dan terdokumentasi.** Keduanya mengakui batas, tapi Fabius mempublikasikan hasil negatif dengan angka (arah rugi 12/12 simbol, smart money = kerumunan) — jarang dilakukan peserta hackathon.

**Weaknesses (Fabius vs Matura)**
- **Tidak ada persona dan tidak ada angka uang yang bisa dirasakan.** Matura: "Rizki butuh 5.000, bayar 56". Fabius: "0 of 6 bots passed" — jujur, tapi juri non-trader tidak tahu siapa yang tertolong dan berapa nilainya.
- **Sistem hidup sedang rusak** *(cek hidup 26 Okt)*: ledger berhenti sejak 13 Okt, `/status` alarm, gate 500. Kekuatan utama Fabius (otomatis, tanpa manusia) justru yang sekarang tidak berjalan; Matura tidak punya klaim "berdetak sendiri" yang bisa gagal di depan juri.
- **Bukti di halaman submission kurang bisa diklik.** Matura memajang tabel "Verify it yourself" dengan 3 tx BscScan per langkah. Fabius menulis "16 commits, 16 valid" dan alamat kontrak, tapi tidak ada tx contoh lock → commit → reveal yang bisa diklik dari halaman.
- **Higiene rekayasa yang terlihat.** Matura menunjukkan gerbang ABI/manifest freshness dan laporan test satu halaman (`docs/test-report.md`). Fabius punya angka uji lebih besar, tapi tersebar di vault berbahasa Indonesia dan halaman uji yang tidak ditautkan dari submission.
- **Video tanpa produk nyata.** v1 memakai mockup 3D; Matura memperlihatkan app yang benar-benar dipakai dan transaksi yang terjadi.

**Opportunities (karena Matura ada)**
- **Pinjam format bukti Matura untuk Demo Day:** satu tabel tiga baris *lock spec → commit root → reveal leaf*, masing-masing dengan tx BscScan dan perintah `verify_signals.py`. Ini format yang sudah dibuktikan efektif oleh peserta lain dan langsung menjawab kriteria eksekusi teknis.
- **Bedakan diri di Finance & Commerce sebagai "lapisan kepercayaan", bukan "produk keuangan".** Matura memindahkan uang; Fabius membuktikan *kapan* sebuah keputusan dibuat. Kalimat posisi: "Matura membuktikan rute termurah; Fabius membuktikan keputusan dibuat sebelum hasilnya ada." Keduanya melengkapi, bukan bersaing di use case yang sama.
- **Persona untuk Fabius bisa diambil dari problem-nya sendiri:** pembeli sinyal di grup Telegram yang ditipu screenshot profit (+312,4 % di video v1 sudah ada sebagai antagonis) — jadikan manusia, bukan grafik.
- **Kelemahan bersama yang bisa dipakai Fabius:** Matura juga 100 % sintetis (MockUSDT, issuer fiktif "Studio Senja"). Fabius tidak perlu malu dengan testnet-only; yang membedakan adalah apakah sistemnya hidup saat diklik.

**Threats (dari Matura)**
- **Di Grand Prize, Consumer, dan Finance, Matura kemungkinan menang di 3 dari 5 kriteria** (eksekusi teknis hari ini, bisnis, UX). Kalau juri memakai bobot rata, Fabius butuh margin besar di inovasi dan presentasi untuk mengimbangi.
- **Matura menaikkan standar "eksekusi teknis" yang dibandingkan juri.** Dengan freshness gate, e2e, dan reorg-safe indexer, juri yang membaca keduanya akan menilai keandalan, bukan jumlah fitur — dan keandalan Fabius per 26 Okt sedang turun.
- **Kelelahan juri terhadap "bot trading".** Problem Matura (gaji telat) universal dan simpatik; problem Fabius (track record sinyal palsu) relevan untuk trader saja. Di Consumer Apps, narasi Matura lebih mudah memenangkan simpati.
- **Kemiripan bahasa "verifiable".** Keduanya menjual "checkable, not asserted". Kalau Fabius tidak menekankan pembeda *urutan waktu*, juri bisa menganggap keduanya klaim yang sama dan memilih yang demonya lebih rapi.

## 4. Pertanyaan juri yang kemungkinan muncul (dan jawaban yang tersedia)
- "Siapa yang membayar FAB kalau tidak ada edge?" → jawaban jujur: belum ada; produk hari ini adalah infrastruktur bukti + gerbang, pembayaran dibuka setelah F-D16 dan review hukum (P75/P80).
- "Kenapa status kalian alarm?" → harus dijawab sebelum ditanya: pulihkan rantai atau tunjukkan alarm sebagai fitur ("gagal terlihat, bukan disembunyikan") **dengan** penyebab yang sudah dipahami (B4 tick 2026-10-12 hitung ulang beda).
- "Apa yang mencegah kalian commit 1.000 varian lalu me-reveal yang menang?" → satu commit per (bot, bar), spec terkunci sebelum bar, `n` sinyal tercatat di commit, reveal maksimal `n`, `markMissed` — jawaban ada di kontrak.

## 5. Langkah konkret sebelum Demo Day 31 Okt (urut prioritas, khusus pelajaran dari Matura)
1. Pulihkan `paper-ledger` (selidiki `data_hash` B4-LISTING-FADE tick 2026-10-12) dan hidupkan kembali committer, supaya `/status` tidak alarm saat juri mengklik.
2. Siapkan tabel "Verify it yourself" tiga tx (lock → commit → reveal) satu bot satu bar, ala Matura.
3. Tambahkan satu persona + satu angka uang di pembuka demo (bukan sejarah Romawi saja).
4. Siapkan satu kalimat pembeda terhadap proyek "verifiable" lain: *bukti urutan, bukan bukti hasil*.

## 6. Batas analisis ini
- Angka uji Matura dari laporan repo mereka sendiri, tidak dijalankan ulang di sini; status verifikasi BscScan kontrak Matura tidak dicek langsung.
- Fabius dinilai dengan keadaan 26 Okt; kalau rantai dipulihkan sebelum 31 Okt, baris "eksekusi teknis" perlu dinilai ulang.
- Bobot kriteria tidak dipublikasikan; "unggul/kalah" adalah penilaian analis.

**Terkait:** [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]] · [[12-Competitors/KP2 - Perago]] · [[10-Submissions/01 - Claims Cheat Sheet]]

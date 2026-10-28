---
tags: [kompetitor, "KP2"]
---

# KP2 - Perago

**Bagian dari:** [[12-Competitors/00 - Hub Kompetitor]] · baseline: [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]]
**Sumber:** *(workspace)* `../Competitors/02-Perago/` — `page/page.txt` (`proj_91853f446a59756152`), `deck/deck.txt` (PDF 7 slide), `video/transcript.txt` + `video/analysis.md` (`youtu.be/mDBC1ClEkt4`, 6:20), `github/README.md`, `github/commits.tsv` (176 commit, 17–29 Sep); cek hidup 26 Okt: `perago-app.vercel.app` 200, `perago-api.43-129-38-115.nip.io/health` → `{"status":"ok"}`.

**Ringkas:** Perago adalah lapisan izin untuk agen AI yang memegang dompet: pengguna menulis tujuan dalam bahasa biasa, AI hanya mengusulkan rencana bertipe, lalu Wallet Policy + simulasi tepat + **Task Mandate EIP-712 sekali pakai** + kontrak tanpa owner + verifier on-chain menentukan apakah aksi boleh jalan dan apakah hasilnya tercapai. Ini **pesaing paling langsung Fabius di track AI Agents** karena tesisnya sama persis: AI boleh mengusulkan, kode deterministik yang memutuskan. Bedanya, Perago menerapkan tesis itu pada **eksekusi nyata** (swap PancakeSwap V3 dan stake CAKE di testnet dengan smart account ERC-4337), sedangkan Fabius menerapkannya pada **bukti urutan keputusan** dengan posisi paper.

**Poin kunci:**
- Track: AI Agents + Consumer Apps. Solo (Dylansius Putra Prasetio / 0xlann). Repo dibuat 17 Sep, push terakhir 29 Sep (tidak ada kerja sesudah deadline awal).
- 7 kontrak, **tanpa owner/admin/upgrade**, terverifikasi Sourcify (creation + runtime match): `MandateExecutor` (2 varian), `PancakeV3SwapAdapter`, `SwapVerifier`, `CakeStakeAdapter`, `StakeVerifier`, `PeragoAcpHook` (ERC-8183).
- Bukti hidup: swap & stake berbahasa alami dengan receipt terverifikasi; replay dan 7 jenis manipulasi ditolak; worker dibunuh di tengah jalan lalu pulih tanpa kirim dua kali; sesi terbatas menolak 7 jenis pelanggaran; siklus job ERC-8183 di kernel BNB APEX (complete/reject/refund).
- Uji: invariant Foundry 12 properti keselamatan, fuzz 10.000 run, fork journey end-to-end (klaim halaman; tidak dijalankan ulang di sini).
- Video 6:20 face-cam + demo live **termasuk jalur gagal** (0,5 WBNB ditolak oleh per-task cap dan daily cap). Deck 7 slide campur ID/EN.
- Penilaian (pendapat): Perago **unggul** di eksekusi on-chain nyata dan kejelasan nilai pengguna; Fabius **unggul** di cakupan platform (marketplace bot/agen, x402 hidup, desk multi-agen ERC-8004) dan kedalaman bukti statistik; presentasi Perago lebih mentah.

**Detail:**

## 1. Profil Perago

| Aspek | Perago |
|---|---|
| Problem | Memberi agen tujuan itu mudah; memberi izin dompet itu sulit. Private key / session luas mengekspos lebih dari satu tugas, dan tx hash hanya membuktikan "sesuatu jalan", bukan "hasil tercapai". Hook data: >100 juta tx x402, survei Visa: hanya 23 % orang AS yakin AI aman memindahkan uang (video). |
| Solution | Goal → plan bertipe tertutup → 13 aturan policy + simulasi di blok tersemat → TaskMandate 22 field EIP-712 → `MandateExecutor` (nonce, expiry, spend, recipient, action hash, postcondition) → adapter satu panggilan → verifier membaca saldo/pool share → receipt publik. |
| Prinsip | "AI may narrow authority, never create or widen it"; protected asset tidak pernah valid; on-chain truth > database; pembayaran agen hanya setelah verifikasi deterministik (ERC-8183). |
| Batas yang diakui | ERC-8183 payment hanya fork-proven (ditahan sejak 29 Sep); mainnet tidak; eksekusi owner-signed lewat layanan hosted "belum terbukti selesai" (slide 6). |
| Stack | Solidity 0.8.37 + Foundry, Alchemy Modular Account V2, Next.js 16 (Vercel), API + worker di VPS (Docker, Caddy), Postgres 16 (Supabase), Bun, Node 24. |
| Bisnis | tidak dijelaskan (tidak ada model pendapatan di halaman maupun deck). |

## 2. Head-to-head per kriteria juri (penilaian, tanpa bobot)

| Kriteria | Fabius | Perago | Siapa unggul & kenapa |
|---|---|---|---|
| Inovasi & orisinalitas | Bukti urutan (commit sebelum hasil), pra-registrasi strategi, desk multi-agen dengan formula terkunci, marketplace bot | Mandat sekali pakai + verifier postcondition + pembayaran agen setelah verifikasi (ERC-8183) | **Setara.** Keduanya orisinal dan sama-sama memakai standar baru BNB (ERC-8004 di Fabius, ERC-8183 di Perago). Perago menjawab pertanyaan yang lebih umum ("bagaimana mendelegasikan dompet"); Fabius menjawab pertanyaan yang lebih sempit tapi jarang disentuh ("bagaimana membuktikan sinyal tidak ditulis belakangan"). |
| Eksekusi teknis | 5 kontrak (ada owner/committer), rantai otomatis, x402 hidup di testnet, MCP; per 26 Okt alarm + gate 500 | 7 kontrak tanpa owner, Sourcify, invariant + fuzz 10k, aksi DeFi nyata di testnet, tes ketahanan worker | **Perago unggul.** Ia mengeksekusi aksi on-chain sungguhan (swap/stake) yang terverifikasi, kontraknya tanpa titik admin, dan hidup hari ini. Fabius sengaja paper-only — konsisten dengan filosofinya, tapi juri yang mencari "genuinely runs onchain" (misi panitia) akan melihat Perago memindahkan token dan Fabius mencatat hash. |
| Dampak & kelayakan bisnis | Model 60/40 dan x402 per sinyal tertulis, belum ada pembeli | Tidak ada model bisnis tertulis; pasar: semua pengguna yang ingin agen bertindak di dompet | **Fabius sedikit unggul di kelayakan (punya model), Perago unggul di dampak (pasar lebih luas).** Secara bersih kira-kira setara; Perago lebih mudah dibayangkan dipakai jutaan pengguna wallet. |
| UX | Konsep berat, banyak halaman, Privy + Telegram | Console satu alur: policy → ketik goal → compile → review limits → sign → receipt; faucet in-app; mode negatif terlihat | **Perago unggul** untuk satu tugas yang jelas. Fabius unggul di jumlah kanal (web/Telegram/MCP). |
| Presentasi & demo | Video v1 127 d motion graphics, jargon, tanpa transaksi nyata di layar | Video 6:20 face-cam santai, demo live dengan MetaMask + BscScan + jalur gagal; produksi mentah, campur bahasa | **Fabius unggul di produksi; Perago unggul di demo.** Juri yang menilai "quality of demo" akan menghargai bukti hidup Perago; juri yang menilai "presentation" akan menghargai ketajaman naratif Fabius. |

## 3. SWOT Fabius terhadap Perago

**Strengths (Fabius vs Perago)**
- **Agen dibuat bertanggung jawab atas waktu, bukan hanya izin.** Perago membuktikan aksi berada di dalam batas; ia tidak membuktikan bahwa rencana AI dibuat *sebelum* pasar bergerak. Fabius justru menjual itu (`TooLate`, `LockedAfterBar`) — dua sisi berbeda dari masalah "percaya pada agen".
- **Ekonomi agen sudah berjalan, bukan hanya fork.** x402 Fabius dieksekusi di chain 97 (tx nyata, gasless, FAB), sementara pembayaran agen Perago (ERC-8183) ditahan di fork sejak 29 Sep.
- **Multi-agen dan identitas standar.** Desk Fabius memakai beberapa analis LLM ber-ERC-8004 (2558/2559/2561/2566/2567 + 2573) yang pick-nya di-anchor; Perago satu planner tanpa identitas agen on-chain.
- **Platform terbuka.** Bot dan agen pihak ketiga bisa masuk lewat gerbang publik G1–G11 dan MCP; Perago adalah produk tertutup satu tim.
- **Pekerjaan berlanjut sesudah 29 Sep** (pivot, desk v2, MCP berbayar, deck dan video v2) — Fabius menunjukkan kecepatan iterasi lebih besar; repo Perago berhenti di 29 Sep.

**Weaknesses (Fabius vs Perago)**
- **Tidak ada aksi on-chain yang bernilai.** Perago memindahkan WBNB → CAKE dan menambah pool share yang diverifikasi; Fabius hanya mencatat hash keputusan paper. Di depan juri, "token benar-benar berpindah" lebih kuat daripada "hash benar-benar tercatat".
- **Sentralisasi lebih terlihat.** Kontrak Perago tanpa owner/admin; Fabius punya satu committer key, validator ERC-8004 milik sendiri, `BotRegistry` owner = deployer. Juri teknis yang membandingkan akan menandai ini.
- **Jalur negatif tidak didemokan.** Perago memperlihatkan permintaan 0,5 WBNB ditolak oleh dua cap secara live. Fabius punya penolakan yang lebih dalam (`TooLate`, gerbang G1–G11 menolak 4/6 bot) tapi video v1 tidak memperlihatkan satu revert pun di layar.
- **Keandalan hari ini.** Health endpoint Perago `ok`; Fabius `alarm` dan gate 500 *(cek hidup 26 Okt)*.
- **Nilai untuk pengguna awam.** Perago: "jangan serahkan private key". Semua orang paham. Fabius: "sinyal disegel sebelum hasil" — butuh pemahaman pasar sinyal dulu.

**Opportunities (karena Perago ada)**
- **Frame "dua lapisan kepercayaan agen".** Fabius bisa memposisikan diri sebagai lapisan yang Perago tidak punya: Perago menjawab *boleh apa*, Fabius menjawab *kapan diputuskan dan bisakah dicek ulang*. Di Demo Day ini membuat juri melihat Fabius sebagai pelengkap tesis yang sama, bukan tiruan.
- **Curi pola demo negatif.** Siapkan satu revert live: commit terlambat → `TooLate`, atau strategi dikunci sesudah bar → `LockedAfterBar`. Perago membuktikan bahwa menunjukkan penolakan di layar meyakinkan juri.
- **Gunakan data hook yang sama.** Perago membuka dengan statistik x402 dan survei Visa (23 %). Fabius menjual sinyal lewat x402 sungguhan — bisa memakai statistik pasar yang sama untuk menunjukkan bahwa x402 Fabius bukan slide, melainkan tx.
- **ExecutionVault Fabius** (eksekusi demo on-chain dengan cap) sudah ter-deploy tapi tidak muncul di cerita submission. Kalau satu siklus anchored-execution bisa didemokan, kelemahan "hanya hash" berkurang.

**Threats (dari Perago)**
- **Head-on di AI Agents (141 proyek, 3 podium).** Juri yang melihat keduanya akan menilai tesis yang sama; Perago punya bukti eksekusi nyata, kontrak tanpa owner, dan demo hidup — ia kemungkinan dinilai lebih "jadi".
- **Juga bertemu di Consumer Apps.** UX Perago (satu console, faucet, sign once) lebih cocok dengan "seamless UX" di deskripsi track.
- **Risiko dicap "yang satu lagi juga bilang AI propose, code decides".** Kulaya, Perago, BagiPanen, dan Fabius semuanya memakai variasi kalimat ini. Tanpa pembeda yang tajam, Fabius menjadi yang ke-empat dengan slogan sama.

## 4. Pertanyaan juri yang kemungkinan muncul
- "Kalau AI kalian hanya memilih bot dan tidak mengeksekusi, apa yang dicegah?" → Fabius mencegah *rewriting history* (sinyal kalah dihapus, strategi diubah sesudah data); Perago mencegah *overreach*. Siapkan perbandingan dua baris ini.
- "Siapa pemegang committer key dan apa yang terjadi kalau bocor?" → F-D80 #4: penyerang bisa mengisi slot bar lebih dulu; jawab dengan rotasi kunci yang sudah pernah dilakukan (F-D82) dan rencana multisig/timelock.

## 5. Langkah konkret sebelum Demo Day 31 Okt (pelajaran dari Perago)
1. Rekam/siapkan satu revert on-chain live (`TooLate` atau `LockedAfterBar`) di BscScan.
2. Tulis satu slide "Perago-style": apa yang dipegang agen, berapa lama, siapa menetapkan batas, apa buktinya — versi Fabius untuk *sinyal* (bukan dompet).
3. Sebut terbuka titik sentralisasi (committer, validator) dan jalannya keluar, sebelum juri menanyakannya.

## 6. Batas analisis ini
- Klaim uji Perago (invariant, fuzz 10k, fork journey) dari halaman mereka; laporan `docs/evidence/` tidak dijalankan ulang.
- Model bisnis Perago "tidak ada" berarti tidak ditemukan di halaman/deck/video, bukan berarti tidak direncanakan.

**Terkait:** [[12-Competitors/KP1 - Matura]] · [[12-Competitors/KP3 - AgentEco]] · [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]]

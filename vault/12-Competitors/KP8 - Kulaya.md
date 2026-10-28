---
tags: [kompetitor, "KP8"]
---

# KP8 - Kulaya

**Bagian dari:** [[12-Competitors/00 - Hub Kompetitor]] · baseline: [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]]
**Sumber:** *(workspace)* `../Competitors/08-Kulaya/` — `page/page.txt` (`proj_07c118a60f591ca443`), `deck/deck.txt` (PDF 10 slide), `video/transcript.txt` + `video/analysis.md` (`youtu.be/mTLAuLq-RCg`, 3:00), `github/README.md`, `github/commits.tsv` (46 commit, 1–6 Okt), `websites/` (HTML `/protocol`, `/protocol/agent`, `/protocol/redteam`); cek hidup 26 Okt: `kulaya.vercel.app` 200.

**Ringkas:** Kulaya memberi kredit mikro tanpa agunan kepada warung kecil Indonesia berdasarkan penjualan yang terverifikasi on-chain: pelanggan membayar lewat QR dengan stablecoin IDR (gasless), tiap penjualan jadi catatan milik toko, limit = 10 % penjualan 30 hari (dibatasi level), AI underwriter ber-ERC-8004 mengusulkan pinjaman, dan **kontrak yang memutuskan** — kunci AI hanya bisa memanggil `proposeLoan`, angka diisi kode bukan LLM, reply guard menolak angka yang tidak ada di hasil tool, dan cap kontrak menolak sisanya (`ExceedsCreditCap`). Pelunasan otomatis ±10 % dari tiap penjualan, tanpa jatuh tempo. Kulaya bertemu Fabius di **ketiga track**, dan secara filosofi adalah kompetitor yang paling dekat dengan kalimat desk Fabius ("The AI picks the rulebook; code computes the position") — Kulaya: "The AI proposes. The contract decides." — dengan penerapan yang jauh lebih mudah dirasakan juri.

**Poin kunci:**
- Track: AI Agents + Finance & Commerce + Consumer Apps. Solo (Ezra Hesperos). Repo 1–6 Okt (sangat cepat: 46 commit dalam 6 hari).
- Kontrak: `Warung.sol` (catatan pendapatan, limit, pinjaman, auto-repayment, pool dengan first-loss reserve, aksi EIP-712 ter-relay), `ReputationAdapter.sol`, `MockIDRX.sol`; **33 test Foundry** (unit, fuzz, invariant, relay attack). App 32 unit test + journey browser end-to-end.
- **Red-team console publik** (`/protocol/redteam`): serang model, matikan policy layer, kontrak tetap menolak — simulasi terhadap kontrak hidup tanpa broadcast.
- Siklus pinjaman on-chain penuh: AI usul Rp 800.000 → diterima → 50 pembayaran pelanggan melunasi → ditutup → rekaman ERC-8004 agen #2535: 1 pinjaman, 100/100. Testnet: 30+ toko, 8 pinjaman diusulkan, pool ±Rp 100 jt test IDRX.
- Kanal: app owner berbahasa Indonesia, situs juri berbahasa Inggris (`/protocol`), bot Telegram dengan voice note.
- Batas jujur: testnet, MockIDRX, bukan QRIS, belum ada pilot nyata (pelanggan = dompet seed), butuh pemberi pinjaman berizin OJK.
- Penilaian (pendapat): Kulaya **unggul** di dampak, UX, presentasi, dan demonstrasi "AI dibatasi kontrak"; Fabius **unggul** di kedalaman bukti waktu, platform terbuka, dan ekonomi agen (x402/MCP); eksekusi teknis kira-kira setara dengan keandalan hari ini menguntungkan Kulaya.

**Detail:**

## 1. Profil Kulaya

| Aspek | Kulaya |
|---|---|
| Problem | 64 juta warung tanpa catatan yang dipercaya pemberi pinjaman → pinjol predator (bunga membengkak, penagih menelepon keluarga, app membaca kontak). |
| Solution | Jual lewat QR → catatan penjualan on-chain milik toko → limit dari penjualan nyata (anti-fake: ≥ 5 pelanggan berbeda, ≤ Rp 250.000/pelanggan/hari) → minta tawaran (teks/voice note) → syarat dibaca dari kontrak, satu tanda tangan gratis → bayar dengan menjual (±10 %/penjualan), tanpa jatuh tempo, tanpa denda → level naik, reputasi AI dipublikasikan. |
| Keamanan AI (4 lapis) | Kunci AI hanya `proposeLoan`, tak memegang dana · cap kontrak (≤ 10 % pendapatan, ≤ plafon level, fee ≤ 5 %, ≤ 20 % per penjualan, per-pinjaman ≤ 5 % pool, anggaran harian) · LLM tak pernah menulis angka (template `{{placeholder}}`) · reply guard. |
| Kenapa web3 | rel stablecoin IDR, event penjualan yang bisa diverifikasi pemberi pinjaman mana pun, split pelunasan oleh kode, pool permissionless, identitas + reputasi ERC-8004 (registry menolak self-review). |
| Roadmap | QRIS bridge via penyedia berizin, mitra pemberi pinjaman berizin + OJK sandbox, mainnet IDRX nyata, embedded wallet + paymaster. |
| Presentasi | Video 3:00 motion graphics + persona Bu Sri + red-team asli; deck 10 slide dengan angka limit, contoh pinjaman, arsitektur, dan "what's real vs not yet". |

## 2. Head-to-head per kriteria juri (penilaian, tanpa bobot)

| Kriteria | Fabius | Kulaya | Siapa unggul & kenapa |
|---|---|---|---|
| Inovasi & orisinalitas | Bukti urutan + pra-registrasi + desk multi-agen + gerbang publik | Kredit berbasis arus penjualan on-chain + AI underwriter yang dibatasi 4 lapis + red-team publik | **Setara.** Revenue-based financing sudah dikenal; kebaruan Kulaya ada pada pola keamanan LLM (angka hanya dari kode, reply guard) yang bisa diserang langsung oleh juri. Fabius orisinal di primitif bukti waktu. |
| Eksekusi teknis | 5 kontrak, 117 forge + 743 Python, rantai otomatis, x402, MCP; alarm per 26 Okt | 3 kontrak, 33 + 32 test + e2e browser, relayer gasless, bot Telegram, siklus pinjaman penuh on-chain | **Setara secara cakupan relatif waktu** (Kulaya dibangun 6 hari), **Kulaya unggul di keandalan hari ini.** Fabius jauh lebih besar, tapi yang ditunjukkan Kulaya bekerja end-to-end saat diklik. |
| Dampak & kelayakan bisnis | Pembeli sinyal & pembuat bot; belum ada pengguna; 60/40 belum deploy | 64 juta warung, masalah pinjol nyata; fee flat ≤ 5 %, first-loss reserve 20 % dari fee; jalur ke OJK sandbox | **Kulaya unggul jelas.** Problem lokal yang menyentuh, model ekonomi yang tertulis di kontrak, dan jalur regulasi yang disebut terbuka. |
| UX | Konsep berat; Privy + Telegram | Bahasa-first, satu aksi per layar, huruf besar, voice note Telegram, gasless untuk pemilik dan pelanggan, situs juri terpisah | **Kulaya unggul jelas** — termasuk pemisahan audiens (pemilik vs juri) yang tidak dimiliki Fabius. |
| Presentasi & demo | Video 127 d terpoles, abstrak | Video 3 menit terpoles, persona, angka rupiah, red-team asli di layar | **Kulaya unggul.** Satu-satunya yang menjual keamanan AI dengan memperlihatkan serangan gagal. |

## 3. SWOT Fabius terhadap Kulaya

**Strengths (Fabius vs Kulaya)**
- **Bukti terhadap operator sendiri, bukan hanya terhadap AI.** Kulaya membatasi AI agar tidak bisa merugikan; ia tidak membuktikan bahwa *operator* Kulaya tidak mengubah parameter atau riwayat (owner bisa mengatur pool/kebijakan off-chain). Fabius mengunci strategi dan keputusan sebelum hasil, sehingga operator Fabius sendiri tidak bisa menulis ulang sejarah.
- **Penilaian kualitas AI secara statistik.** Reputasi AI Kulaya = 1 pinjaman, 100/100 (n=1). Fabius tidak akan mengutip n sekecil itu sebagai kualitas (claims cheat sheet: win rate dengan n < 20 wajib menyebut n) dan punya gerbang G1–G11 + F-D16. Juri teknis yang jeli akan melihat Fabius lebih disiplin terhadap klaim kualitas.
- **Platform terbuka dan ekonomi agen.** x402 + MCP + `/submit-agent`: pihak luar bisa membawa bot/agen dan agen lain bisa membeli keluaran. Kulaya adalah aplikasi vertikal tertutup.
- **Skala riset.** Fabius punya puluhan eksperimen pra-registrasi dan hasil negatif; Kulaya produk 6 hari dengan uji fungsional, bukan uji kualitas keputusan.

**Weaknesses (Fabius vs Kulaya)**
- **Persona dan dampak.** "Bu Sri, Warung Bakso, Rp 800.000, tanpa penagih" vs "6 bot, 0 lulus". Di kriteria dampak dan presentasi, ini selisih yang sama besarnya dengan BagiPanen.
- **Demo keamanan AI yang bisa diserang juri.** Kulaya mengundang juri mematahkan sistemnya (`/protocol/redteam`) dan kontrak tetap menolak. Fabius punya penolakan kontrak (`TooLate`, `LockedAfterBar`) tetapi tidak ada konsol yang mengundang juri mencobanya.
- **Situs khusus juri.** Kulaya memisahkan app pengguna (Bahasa) dari situs juri (Inggris, arsitektur, agen, red-team). Fabius memakai satu situs untuk semua audiens, dan halaman `/status` yang dilihat juri hari ini menyala alarm *(cek hidup 26 Okt)*.
- **Konteks Indonesia dan regulasi disebut terbuka.** Kulaya menyebut pinjol, QRIS, OJK sandbox. Fabius menunda P75/P80 dan tidak menyebut regulasi di submission.
- **Kecepatan eksekusi terlihat.** Kulaya membangun produk lengkap dalam 6 hari; Fabius 16 hari dengan 2.700+ commit tapi permukaan yang dilihat juri lebih sulit dicerna. Juri menilai hasil, bukan usaha.

**Opportunities (karena Kulaya ada)**
- **Bangun "red-team console" versi Fabius** dari kontrak yang sudah ada: tombol "commit terlambat" → `TooLate`; "kunci strategi sesudah bar" → `LockedAfterBar`; "reveal sinyal yang tidak di-commit" → gagal proof Merkle. Simulasi tanpa broadcast seperti Kulaya. Ini mengubah klaim abstrak Fabius menjadi sesuatu yang bisa dicoba juri dalam 30 detik.
- **Halaman `/protocol`-gaya untuk juri** yang merangkum kontrak, bukti, batas, dan tombol coba — dan menyembunyikan kompleksitas (G1–G11, desk) di belakang satu klik.
- **Pasangan alami:** Kulaya butuh bukti bahwa usulan AI dibuat sebelum hasil pelunasan diketahui (untuk reputasi agen yang jujur); itu persis primitif Fabius. Di pitch, Fabius bisa menyebut bahwa pola "seal before outcome" berlaku untuk underwriter AI mana pun — tanpa mengklaim integrasi.
- **Disiplin n.** Saat juri melihat "100/100 dari 1 pinjaman" di Kulaya, Fabius bisa menonjolkan aturan "sebut n, tidak ada klaim di bawah 20" sebagai pembeda kematangan.

**Threats (dari Kulaya)**
- **Kandidat kuat di ketiga track dan Grand Prize.** Kulaya memenuhi pola juara hackathon: problem lokal emosional, AI yang aman dan bisa diserang, demo hidup, dua bahasa, batas yang diakui, roadmap regulasi.
- **Slogan Fabius tertelan.** "The AI picks the rulebook; code computes the position" (Fabius) vs "The AI proposes. The contract decides." (Kulaya, juga dipakai sebagai judul slide). Juri yang melihat keduanya akan mengingat versi Kulaya karena contohnya konkret (Rp 1 miliar ditolak).
- **Keamanan AI menjadi kriteria tak tertulis.** Setelah Kulaya, Perago, dan BagiPanen, juri akan bertanya ke setiap proyek AI "bagaimana kalau model di-jailbreak?". Fabius punya jawabannya (formula terkunci, AI tidak menghitung posisi) tapi belum punya demonstrasinya.

## 4. Pertanyaan juri yang kemungkinan muncul
- "Kalau analis LLM kalian di-jailbreak, apa yang terjadi?" → formula terkunci (`meja_slot.py` r4) yang mengubah suara jadi posisi, posisi paper, root wajib masuk `DeskAnchor` dalam 300 d; siapkan demonstrasi satu suara gila yang tidak mengubah apa pun di luar batas formula.
- "Siapa yang dirugikan sekarang dan siapa yang tertolong?" → jawab dengan persona pembeli sinyal, tanpa angka yang tidak dimiliki.

## 5. Langkah konkret sebelum Demo Day 31 Okt (pelajaran dari Kulaya)
1. Konsol "coba patahkan" untuk tiga revert kontrak Fabius (simulasi tanpa broadcast).
2. Satu halaman juri berbahasa Inggris yang merangkum bukti + batas + tombol coba.
3. Demonstrasi "analis di-jailbreak tetap dibatasi formula".
4. Pulihkan `/status` sebelum juri membukanya.

## 6. Batas analisis ini
- Angka test (33 + 32) dan statistik testnet (30+ toko, 8 pinjaman, pool ±Rp 100 jt) dari halaman Kulaya; tidak dijalankan ulang.
- "Operator bisa mengubah parameter" adalah inferensi dari arsitektur (pool, policy off-chain), bukan hasil audit kode Kulaya.

**Terkait:** [[12-Competitors/KP7 - Kawal]] · [[12-Competitors/KP1 - Matura]] · [[12-Competitors/KP4 - BagiPanen]] · [[10-Submissions/01 - Claims Cheat Sheet]]

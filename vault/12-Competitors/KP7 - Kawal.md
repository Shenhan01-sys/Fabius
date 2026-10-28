---
tags: [kompetitor, "KP7"]
---

# KP7 - Kawal

**Bagian dari:** [[12-Competitors/00 - Hub Kompetitor]] · baseline: [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]]
**Sumber:** *(workspace)* `../Competitors/07-Kawal/` — `page/page.txt` (`proj_3ab440bb90243ea172`), `deck/deck.txt` (PDF 10 slide), `video/transcript.txt` + `video/analysis.md` (`youtu.be/L-HtQDqaVk8`, 2:28), `github/README.md`, `github/commits.tsv` (58 commit, 31 Agu – 30 Sep); cek hidup 26 Okt: `kawal-three.vercel.app` 200.

**Ringkas:** Kawal adalah marketplace agen untuk BNB Smart Chain yang **tidak percaya registry**: sebelum mendaftarkan agen, Kawal sendiri memanggil endpoint yang dideklarasikan (handshake MCP, kartu A2A + pertanyaan JSON-RPC aman, atau rekaman OASF) dan hanya memberi stempel HIREABLE pada yang menjawab sesuai protokol. Agen disewa ke "seat" dengan mandat (spend cap, allowlist kontrak, expiry) berupa session key Altana di **mainnet** yang bisa dicabut dari browser. Kawal menulis balik pengukurannya ke ERC-8004 Reputation Registry dan meng-anchor riwayat probe harian sebagai Merkle root di `KawalLedger`. Dari delapan kompetitor, Kawal adalah **kembaran filosofis Fabius yang paling dekat**: penolakan sebagai output, angka dengan sumber, blind spot dicetak, dan Merkle-root harian di chain. Ia bertemu Fabius di AI Agents, Finance & Commerce, dan Grand Prize.

**Poin kunci:**
- Track: AI Agents + Finance & Commerce. Solo (Pugar Huda Mantoro). Network: **BNB Smart Chain mainnet**. Repo 31 Agu – 30 Sep (tidak ada kerja sesudah deadline awal).
- Data problem dari ukuran sendiri: 328.000+ agen ERC-8004 di BSC, ±13 % mendeklarasikan antarmuka, 0,036 feedback per agen, 62,8 % dari 600 registrasi terbaru adalah salinan template. Probe Kawal: 4.400+ panggilan ke 102 endpoint dalam 4 minggu, 61 menjawab.
- Bukti mainnet: 4 session Altana, tx lewat session key, allowlist menolak panggilan identik ke kontrak lain, revoke dari UI, preempt revoke-then-regrant; `KawalLedger` 28 hari root ter-anchor + Sourcify; agen Kawal sendiri ERC-8004 #320164; **97 rekaman reputasi** (56 uptime + 41 response time) untuk 56 agen dengan bukti IPFS.
- Untuk agen lain: MCP 10 tool (`verify_agent`, `find_agents`, `compare_agents`, `read_reputation`, `check_payment`, `plan_mandate`, …), kartu A2A, dokumen registrasi ERC-8004 — tanpa kunci.
- Integrasi: PancakeSwap (router/position manager di allowlist), AltLayer 8004scan, TermiX (laporan "Agent Advantage": hiring menang 1 dari 3 tugas — dilaporkan apa adanya).
- Penilaian (pendapat): Kawal **unggul** di pemakaian ERC-8004 nyata di mainnet, mandat yang dieksekusi, dan bukti pengukuran pihak ketiga; Fabius **unggul** di keterlibatan AI dalam keputusan (desk analis), rel pembayaran x402 yang hidup, dan narasi pitch; presentasi dan kejujuran setara.

**Detail:**

## 1. Profil Kawal

| Aspek | Kawal |
|---|---|
| Problem | Registry ERC-8004 nyata, tapi kemampuan menyewa dari situ tidak: setiap permukaan mengulang klaim registrasi ("supports MCP" tak diuji, "x402" tak dibayar, feedback tak diatribusikan). Pemilik modal di BSC tak tahu dari 300.000 entri mana yang akan menjawab, dan kalau ada pun tak bisa memberi uang tanpa memberi segalanya. |
| Solution | Verify before listing → hire under a mandate (Altana session key: cap, allowlist, expiry, revoke, preempt) → write back reputasi ke ERC-8004 → anchor riwayat probe harian di `KawalLedger`. |
| Desain | "Surat jalan" Indonesia: tiap halaman adalah formulir inspeksi (K-1 … K-7), stempel lebih gelap semakin banyak bukti, blind spot dicetak di bawah stempel, tally panggilan sebagai lubang punch, bukan grafik. |
| Kejujuran | Laporan TermiX: hiring hanya menang 1 dari 3 tugas; 24 dari 24 registrasi TermiX sampel adalah template kosong — dilaporkan. Seat sudah kedaluwarsa "as a mandate should". |
| Presentasi | Video 2:28 rekaman layar + voice-over TTS + subtitle gaya mesin tik; deck 10 slide. |

## 2. Head-to-head per kriteria juri (penilaian, tanpa bobot)

| Kriteria | Fabius | Kawal | Siapa unggul & kenapa |
|---|---|---|---|
| Inovasi & orisinalitas | Bukti urutan keputusan + pra-registrasi + desk multi-agen + gerbang publik untuk bot luar | Verifikasi aktif endpoint agen sebelum listing + mandat session key + reputasi yang ditulis balik + Merkle root probe harian | **Setara.** Dua proyek paling orisinal secara konseptual di daftar ini; keduanya "menolak percaya klaim". Kawal memeriksa *kemampuan* agen, Fabius memeriksa *waktu keputusan* agen. |
| Eksekusi teknis | 5 kontrak testnet, 117 forge + 743 Python, x402 hidup testnet, MCP; alarm per 26 Okt | Mainnet: session key, revoke, preempt, `KawalLedger` 28 hari, 97 rekaman reputasi, MCP 10 tool, A2A | **Kawal unggul.** Semua bukti utamanya di mainnet dan menyentuh registry resmi yang dipakai ekosistem; Fabius di testnet dan sedang alarm. |
| Dampak & kelayakan bisnis | Marketplace bot/sinyal 60/40 (belum deploy), x402 per sinyal | Tidak ada model bisnis tertulis; nilai: memfilter 300k agen menjadi yang bisa disewa | **Setara.** Fabius punya model, Kawal punya masalah ekosistem yang lebih luas dan terukur. Keduanya belum punya pengguna yang membayar. |
| UX | Banyak halaman, konsep berat | Formulir birokrasi padat teks — unik dan disiplin, tapi berat untuk orang awam | **Setara rendah.** Keduanya lebih cocok untuk pengguna teknis daripada konsumen. |
| Presentasi & demo | Video 127 d motion graphics naratif | Video 2:28 rekaman produk + TTS datar, estetika formulir | **Fabius unggul di daya pikat, Kawal unggul di bukti layar.** Kawal memperlihatkan produk yang sedang dipakai; Fabius memperlihatkan konsep dengan bagus. |

## 3. SWOT Fabius terhadap Kawal

**Strengths (Fabius vs Kawal)**
- **AI benar-benar memutuskan sesuatu (dalam batas).** Di Kawal, "agen" adalah pihak luar yang diperiksa; Kawal sendiri tidak memakai LLM untuk keputusan. Di Fabius, analis LLM memilih bot dan arah, dan pilihannya di-anchor. Untuk track **AI Agents**, Fabius menunjukkan agen yang bekerja, bukan hanya direktori agen.
- **Ekonomi agen yang sudah membayar.** Fabius menjual sinyal via x402 dengan tx nyata (testnet); Kawal "bertanya ke agen apakah mereka benar-benar menagih x402" tapi tidak menjual apa pun.
- **Bukti waktu.** Kawal meng-anchor riwayat probe *setelah* hari selesai (catatan audit); Fabius meng-anchor keputusan *sebelum* hasil ada — primitif yang lebih ketat untuk mencegah rewriting.
- **Gerbang statistik untuk kualitas.** Kawal memberi stempel "menjawab"; Fabius memberi verdict "lolos/gagal" berbasis kinerja dengan G1–G11 dan false-positive terukur. Kawal tidak menilai apakah agen yang menjawab itu *bagus*.

**Weaknesses (Fabius vs Kawal)**
- **Mainnet dan registry yang dipakai orang.** Kawal bekerja di registry ERC-8004 mainnet (328k agen) dan menulis 97 rekaman reputasi untuk agen pihak lain. Fabius terdaftar di testnet (tokenId 2494) dan reputasinya tidak diisi pihak ketiga.
- **Mandat yang dieksekusi.** Kawal memperlihatkan session key yang dibatasi, ditolak di luar allowlist, dicabut, dan di-preempt — semuanya tx mainnet. Fabius tidak punya mekanisme pembatasan hak eksekusi agen yang didemokan (ExecutionVault ada tapi tidak di cerita).
- **Data problem yang diukur sendiri di skala ekosistem.** Kawal membuka dengan angka registry yang ia hitung (0,036 feedback per agen, 62,8 % template). Fabius punya riset mendalam, tapi tentang pasar dan sinyalnya sendiri, bukan tentang ekosistem BNB yang dinilai juri.
- **Keandalan hari ini** *(cek hidup 26 Okt)*: Kawal hidup; Fabius alarm dan gate 500.

**Opportunities (karena Kawal ada)**
- **Fabius adalah calon "agen yang lolos Kawal".** Fabius mendeklarasikan MCP dan x402 yang benar-benar menjawab. Kalau Fabius mendaftar di registry ERC-8004 **mainnet** dengan `agentURI` yang menunjuk MCP-nya, Kawal (atau 8004scan) akan memprobe dan berpotensi memberi stempel HIREABLE — bukti pihak ketiga pertama untuk Fabius. Ini butuh langkah builder (deploy/registrasi mainnet), jadi dicatat sebagai peluang, bukan rencana yang sudah disetujui.
- **Bingkai bersama "jangan percaya klaim, periksa".** Juri yang menyukai Kawal akan menyukai etos Fabius; posisikan keduanya sebagai dua sisi: Kawal memeriksa *apakah agen bisa dipanggil*, Fabius memeriksa *apakah keputusan agen bisa dipercaya waktunya*.
- **Pinjam "blind spot dicetak di bawah stempel".** Halaman `/bot/[id]` Fabius bisa menampilkan batas verdict tepat di sebelah verdict (misalnya "SAH = urutan terbukti; TIDAK membuktikan profit") — Fabius sudah punya kalimatnya di claims cheat sheet.
- **Masalah discovery yang sudah dicatat Fabius** (`05-Ecosystem/03 - Discovery Gap.md`) dijawab Kawal secara langsung — referensi yang bisa dipakai di vault untuk menutup open item itu.

**Threats (dari Kawal)**
- **Pesaing kuat di AI Agents dan Finance.** Kawal adalah satu-satunya kompetitor yang bekerja langsung pada infrastruktur agen BNB di mainnet (ERC-8004 reputation, session key, MCP, A2A). Juri BNB Chain kemungkinan memberi nilai tinggi pada pemakaian standar resmi yang sedalam itu.
- **Klaim "verified, honest, refuses" milik Fabius bisa terasa tidak unik** setelah juri melihat Kawal, yang mengemas kejujuran yang sama dengan desain lebih tegas dan bukti mainnet.
- **MCP bukan lagi pembeda.** Kawal punya MCP 10 tool + A2A; Fabius 18–19 tool tanpa A2A. Juri akan menganggap MCP sebagai standar, bukan nilai tambah.

## 4. Pertanyaan juri yang kemungkinan muncul
- "Kenapa identitas ERC-8004 kalian di testnet, sementara registry yang dipakai ekosistem di mainnet?" → jujur: semua Fabius sengaja di testnet sampai F-D16 dan review hukum; registrasi identitas saja (tanpa uang) adalah langkah murah yang bisa dipertimbangkan builder.
- "Apakah ada pihak ketiga yang menilai agen kalian?" → belum (validator milik sendiri); jangan klaim lebih.

## 5. Langkah konkret sebelum Demo Day 31 Okt (pelajaran dari Kawal)
1. Tampilkan batas setiap verdict di sebelah verdict (gaya "blind spot di bawah stempel").
2. Pertimbangkan (langkah builder) registrasi identitas ERC-8004 mainnet tanpa uang, agar agen Fabius bisa diprobe pihak ketiga.
3. Di pitch, bedakan "memeriksa kemampuan agen" (Kawal) dan "memeriksa waktu keputusan agen" (Fabius).

## 6. Batas analisis ini
- Angka ekosistem (328k agen, 0,036 feedback/agen, 62,8 % template) adalah ukuran Kawal sendiri; tidak dihitung ulang.
- Tx mainnet Kawal dirujuk dari halaman; tidak dibaca satu per satu dari chain.

**Terkait:** [[12-Competitors/KP6 - Tagei]] · [[12-Competitors/KP8 - Kulaya]] · [[05-Ecosystem/03 - Discovery Gap]] · [[05-Ecosystem/01 - ERC-8004 Identity]]

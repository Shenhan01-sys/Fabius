---
tags: [deck, "DK0"]
---

# DK0 - Brief Pembuatan Deck

**Bagian dari:** [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]]
**Sumber:** [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] (strategi), [[12-Competitors/00 - Hub Kompetitor]] (KP0–KP10, termasuk sensitivitas bobot KP9 §8), [[10-Submissions/01 - Claims Cheat Sheet]], [[08-Backlog/01 - Backlog]] (P173–P187), [[08-Backlog/13 - Langkah Builder Tertunda]] (LB22–LB28), deck lama `vault/13-SubmmisionDocs/Fabius-Submission-Deck-final.pptx` (gaya), situs hidup `fabius-one.vercel.app` (diuji 28–29 Okt), kata builder 28–29 Okt.
**Untuk:** agen pembuat PPT (serah terima). Baca halaman ini sampai habis sebelum membuka file lain. Versi 29 Okt **menggantikan** versi 8 slide 28 Okt.

**Ringkas:** Kamu membuat **deck Demo Day Fabius** untuk Indonesia Web3 Hackathon 2026, **31 Okt 2026**: **3 menit presentasi + 2 menit tanya jawab**, live di depan juri, format bebas (kata builder 29 Okt: *"format demo day ya hanya itu gada yg lainnya, makanya kita bebas"*). Deck = **6 slide**, satu file panduan per slide `DK1`–`DK6` (tujuan, konteks, POV juri, POV presenter, konsep, ilustrasi, teks di slide, naskah per detik, animasi, angka + sumber, aset, larangan, risiko + cadangan, cek selesai). Halaman ini memberi semua yang kamu perlukan untuk memahami **apa itu Fabius dari setiap sudut**, kenapa deck ini dibuat begini, celah apa yang sudah ditutup, dan apa yang tidak boleh kamu lakukan. Kamu **tidak** mengarang angka, klaim, atau slide tambahan di luar §11.

**Poin kunci:**
- Satu kalimat yang harus diingat juri: ***"Most AI agents limit what AI can do. Fabius proves when it decided."*** — dengan nomor blok.
- Strategi: **pindah arena** (jangan bersaing di dampak sosial atau mainnet) + **testnet dijadikan tesis** ("Mainnet without proof is Cannae") + **demo yang bisa dicoba juri** (`/tour`, `/break`, `/verify`, semua hidup dan diuji 28–29 Okt).
- 6 slide, 387 kata naskah, ±2,3 kata/detik: Hook+masalah 0:00–0:30 · Solusi 0:30–0:55 · Demo 0:55–1:35 · Coba curangi 1:35–2:05 · Dibangun untuk diragukan 2:05–2:40 · Penutup 2:40–3:00.
- Track sasaran **AI Agents** (Lencana, proyek builder yang lain, di Consumer). Mainnet **tidak** (keputusan builder 29 Okt, biaya).
- Dua slide bergantung pada aset/angka yang datang belakangan: DK3 (klip Telegram, LB27) dan DK5 (angka H-1, P182). Buat dengan placeholder bertanda jelas; jangan menunda slide lain.

**Detail:**

## 1. Tugas dan keluaran

| Hal | Isi |
|---|---|
| Keluaran utama | `vault/13-SubmmisionDocs/Fabius-DemoDay-Deck.pptx` — 6 slide 16:9 + 3 slide lampiran tersembunyi (§10), naskah lengkap di **speaker notes**, klip **tertanam** (bukan tautan) |
| Cadangan | `Fabius-DemoDay-Deck.pdf` (ekspor) + `Fabius-DemoDay-Deck.mp4` opsional (deck diputar otomatis 3:00, untuk keadaan darurat laptop/proyektor) |
| Laporan | daftar placeholder yang masih ada (slide + aset ID), daftar font yang dipakai + apakah ter-embed |
| Bahasa | teks di slide **Inggris** (konsisten dengan web, deck lama, juri BNB Chain); naskah lisan **Indonesia** sebagai utama + versi Inggris di tiap DK (builder memilih saat gladi; belum diputuskan) |
| Persetujuan | final hanya setelah builder menyetujui naskah (LB25) |

## 2. Fabius dari setiap sudut pandang

### 2.1 Satu paragraf
Fabius adalah **operator sinyal trading (paper) yang membuktikan waktu keputusannya**. Enam bot dengan strategi yang dikunci on-chain, dipilih setiap 5 menit oleh meja analis AI ber-identitas ERC-8004, menyegel setiap sinyal di BNB Smart Chain **sebelum** pasar menjawab. Siapa pun — manusia lewat web/Telegram, agen lain lewat MCP — bisa membeli sinyal per butir lewat x402 (tanpa gas) dan memeriksa sendiri, tanpa kunci dan tanpa gas, bahwa sinyal itu tidak ditulis sesudah kejadian. Semua di **testnet (chain 97)** dengan uang mainan, dan itu disengaja: Fabius belum mengizinkan uang sungguhan sampai bot-nya lulus uji maju yang aturannya juga dikunci on-chain.

### 2.2 Nama dan filosofi
Quintus Fabius Maximus *Cunctator* menyelamatkan Roma dari Hannibal dengan **menolak bertempur** sebelum medannya memihak; Roma kalah besar di Cannae karena terburu-buru bertempur. Produk ini mewarisi sikap itu: menahan diri, mencatat setiap keputusan (termasuk penolakan), dan tidak mengklaim apa yang belum terbukti. Slogan lama: *"Refuse the battle. Prove the decision."*

### 2.3 Masalah yang dijawab
Track record penjual sinyal/bot ditulis **sesudah** pasar bergerak: screenshot profit, sinyal kalah yang dihapus, strategi yang diubah diam-diam. Pembeli tidak bisa memeriksa *apa* yang diputuskan, *kapan*, dan apakah aturannya sama. AI memperparah: model bisa menjelaskan apa pun secara hindsight, dan begitu agen punya dompet (x402) dan identitas (ERC-8004), penipuan track record ikut berskala mesin. Konteks Indonesia: **22,69 juta** investor kripto (OJK, Juni 2026); Satgas PASTI menghentikan **228** pedagang aset keuangan digital ilegal Jan–Mei 2026 (OJK SP 11/STPASTI/VI/2026).

### 2.4 Cara kerja (mekanisme, untuk kamu pahami; di slide cukup 3 kata)
1. **Kunci** — spesifikasi strategi tiap bot di-hash dan dikunci di `LockRegistry`. Commit untuk hari sebelum kunci ditolak kontrak (`LockedAfterBar`); strategi yang diubah = sidik jari lain yang tidak pernah dikunci (`NotLocked`). Aturan uji maju F-D16 (20 sinyal, 20 hari, 2 bulan, CI > 0) dan syarat buang bot juga dikunci.
2. **Segel** — tiap hari, bot menulis keputusannya ke ledger publik berantai hash (`ledger/paper/<bot>.jsonl`, ditulis GitHub Actions), lalu worker menyegel semua sinyal hari itu sebagai **satu Merkle root** di `SignalAnchor` (`0x9B78200beFbbBe836585d31bd5b6dB32587064f3`, chain 97). Lewat 12 jam sesudah hari tutup = ditolak (`TooLate`). Jumlah sinyal ikut dikunci; sinyal ekstra tidak bisa dibuka (`TooManyReveals`). Hari tanpa keputusan tercatat sebagai `gap` yang tidak bisa dihapus.
3. **Buka + periksa** — tiap sinyal dibuka dengan salt-nya; siapa pun menghitung ulang dan mencocokkan dengan ledger: halaman `/verify`, `/tour`, alat MCP `fabius_verify`, atau `python -X utf8 tools/verify_signals.py`. Tanpa login, tanpa kunci, tanpa gas.
4. **Meja AI** — analis LLM, masing-masing dengan identitas ERC-8004 (Fabius #2494; analis 2558/2559/2561/2566/2567), memberi pilihan bot tiap 5 menit; **formula terkunci** (bukan LLM) yang menghitung posisi; root siklus wajib masuk `DeskAnchor` dalam 300 detik. AI dibatasi *dan* waktunya dibuktikan.
5. **Jual** — sinyal per butir lewat **x402** (token uji FAB, pembeli tanpa gas, login Google/Telegram/email lewat Privy) di web, Telegram bot (`t.me/FabiusTradingAgent_Bot`), dan **MCP** untuk agen. Bot/agen luar bisa mendaftar (`/submit`, `/submit-agent`) dan menghadapi gerbang G1–G11 yang sama. Bagi hasil 60/40 untuk penerbit **dirancang dan diuji, belum di-deploy**.

### 2.5 Sudut pandang tiap pihak

| Pihak | Yang ia lihat / rasakan | Nilai bagi dia |
|---|---|---|
| Pembeli sinyal ritel ("Andi", ilustrasi) | beli satu sinyal di Telegram tanpa gas, dapat link, klik → "Verified" + jam segel | tahu sinyal tidak ditulis sesudah kejadian; tidak perlu percaya penjual |
| Pembuat bot kecil yang jujur | mendaftar, lolos gerbang yang sama, rekamnya terbukti tanpa follower/brand | track record yang bisa dibuktikan |
| Agen AI lain (ekonomi agen) | memanggil MCP, bayar x402, verifikasi otomatis | bukti yang dibaca mesin, bukan rating |
| Platform / regulator | jejak audit yang tidak bisa ditulis ulang | arah, **bukan** kerja sama yang ada |
| Juri teknis (BNB Chain, Dev Web3 Jogja) | kontrak sendiri, revert bernama, ERC-8004, x402, MCP, ledger berantai hash, tes | kedalaman + ide yang tidak dimiliki finalis lain |
| Juri produk/dampak (Binance Academy, Coinvestasi) | masalah investor ritel Indonesia, demo Telegram, kejujuran "0/6 lulus" | relevansi + kredibilitas |

### 2.6 Apa yang ada dan tidak ada (jujur)

| Ada dan bisa dicoba (diuji 28–29 Okt) | Belum ada / tidak diklaim |
|---|---|
| `/tour` tur 60 detik: kunci → tutup → segel → buka → Verified, tiap langkah tx on-chain | uang sungguhan (`config/uang_nyata.json` `"aktif": false`) |
| `/break` 4 kecurangan → 4 revert kontrak (simulasi eth_call, tanpa kunci/gas) | profit, edge, win rate (0/6 bot lulus uji maju) |
| `/verify` per bot per hari, SAH, 1–2 detik | pembeli/agen luar (pembelian x402 baru oleh builder) |
| Telegram bot + Mini App, beli x402 tanpa gas | mainnet (tetap testnet, keputusan builder 29 Okt) |
| MCP `/mcp`, x402, ERC-8004, 5+ kontrak sendiri | 60/40 penerbit (belum deploy) |
| Ledger berantai hash + verifier publik + CI hijau | desentralisasi committer (satu kunci; arah multisig) |

## 3. Konteks hackathon dan juri

| Hal | Isi |
|---|---|
| Acara | Indonesia Web3 Hackathon 2026 — co-host Binance Academy, BNB Chain, Coinvestasi; mentor Dev Web3 Jogja. 228 proyek; Fabius submit 7 Okt di 3 track, tim "Mythos05" (1 orang). |
| Finalis | 10 (kata builder): Kulaya, BagiPanen, Kawal, SAMA, Perago, Matura, AgentEco, Tagei, Lencana (milik builder), Fabius |
| Format | 3:00 presentasi + 2:00 Q&A; bebas (boleh klip, boleh live). Pemenang diumumkan hari itu. |
| Kriteria | inovasi · eksekusi teknis · dampak + kelayakan bisnis · UX · kualitas presentasi + demo — **bobot tidak dipublikasikan** |
| Hadiah | per track $600/$400/$300; Grand Prize $1.000; Community Choice $100 (dipilih sesama builder) |
| Track Fabius | **AI Agents** (bocoran tak resmi top-15: 5 per track; proyek Finance tidak masuk top-10, jadi Fabius diarahkan ke AI Agents, Lencana ke Consumer) |
| Yang sudah dilihat juri | halaman submission (7 Okt), video v1 (127 d, penuh jargon), deck 12 slide lama — lihat [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]] §1 |

Posisi menurut analisis (penilaian, bukan ukuran; [[12-Competitors/KP9 - Ranking dan Skenario Finalis]] §8): sesudah `/tour` + `/break` tayang, Fabius ke-2 (bobot teknis-inovasi) s.d. ke-5 (bobot UX) dari 10; di dalam AI Agents ke-1 s.d. ke-3. Lawan terkuat: Kulaya dan BagiPanen (dampak + UX), Kawal (ERC-8004 mainnet). **Tuas terbesar yang tersisa = dampak dan UX di mata juri** — itulah alasan slide 1 (masalah Indonesia) dan slide 3 (demo pembeli) mendapat waktu paling banyak.

## 4. Tujuan deck

1. **Diingat**: juri menulis satu kalimat di catatannya — *"Fabius proves **when** an AI decided."*
2. **Dipercaya**: setiap klaim punya bukti yang bisa dibuka juri saat itu juga (QR → `/tour`; `/break`).
3. **Dibedakan**: finalis lain bilang "AI dibatasi kontrak"; Fabius satu-satunya yang membuktikan *waktu* keputusan.
4. **Dimaafkan dari kelemahan**: testnet, tanpa edge, tanpa pengguna — diucapkan duluan sebagai prinsip, bukan ditemukan juri.
5. **Dipilih**: membuat juri AI Agents merasa memberi hadiah ke Fabius adalah keputusan yang mudah dipertanggungjawabkan.

## 5. Strategi (kenapa deck ini bentuknya begini)

- **Pindah arena.** Jangan bersaing di dampak sosial (BagiPanen petani, Kulaya warung) atau eksekusi mainnet (SAMA, Kawal). Arena Fabius: **bukti waktu keputusan** — lapisan yang tidak dimiliki finalis lain dan dibutuhkan semua agen AI. Rincian: [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] §1.
- **Testnet sebagai tesis.** Juri teknis akan membuka BscScan dan melihat chain 97. Produk Fabius adalah kejujuran yang bisa diperiksa; menutupi testnet meruntuhkan tesisnya. Diucapkan duluan di DK5: *"Mainnet without proof is Cannae."*
- **Tunjukkan, jangan klaim.** Dua klip (DK3 beli + Verified, DK4 empat kecurangan ditolak) = 70 dari 180 detik. Slide teks dibuat sesedikit mungkin.
- **Mulai dari manusia, tutup dengan mesin.** Hook = screenshot profit yang semua orang kenal + angka Indonesia; penutup = kalimat *what vs when* untuk juri AI Agents.
- **Kejujuran sebagai pembeda.** "0 dari 6 lulus", "12/12 rugi dipublikasikan", "Sharpe dikoreksi sendiri" — tidak ada finalis lain yang memublikasikan kegagalan sendiri dengan angka.
- **Kurangi beban kognitif.** Tanpa jargon di permukaan (tick, leaf, F-D16, G1–G11, Merkle hanya di Q&A). Satu gagasan per slide, ≤ 20 kata di slide.

## 6. Celah yang sudah ditutup (bukti, supaya kamu berani menampilkannya)

| Celah (sebelum) | Sekarang | Bukti |
|---|---|---|
| Ledger berhenti 13 Okt; `ledger verify` gagal di B4 (lookahead listing) | diperbaiki; gladi runner 29 Okt: gap 13–27 Okt tertulis, **6/6 SAH** | P173, P182 |
| Railway `cannot fork()`, x402 HTTP 500 | `tini` + git tanpa gc latar; engine/x402/probe hidup, 0 `cannot fork` | P181, LB22 |
| `/verify` macet 504 untuk hari bersinyal | 1–2 detik di produksi (indeks hash tx + struk on-chain) | P180, P178 |
| Tidak ada tur juri tanpa login | `/tour` (lima langkah, tiap langkah tx) — tautan "60-second tour" di hero | P178 |
| Tidak ada konsol "coba patahkan" | `/break` — 4/4 ditolak: `TooLate`, `LockedAfterBar`, `NotLocked`, `TooManyReveals` | P178 |
| Landing bisa menampilkan "TIDAK DIUNGKAP" palsu | verifier + snapshot membaca jumlah pasti dari kontrak; gagal baca = tunda, bukan vonis | P187 |
| Jargon di landing + `/verify` | diganti bahasa awam (EN + ID) | 29 Okt |
| Angka 228 belum terverifikasi | terverifikasi ke siaran pers OJK SP 11/STPASTI/VI/2026 | P183 |
| CI merah | hijau | P186 |
| Format Demo Day, mainnet, track | bebas 3+2 menit; tetap testnet; AI Agents | LB26, LB24, KP10 §1 |

Masih terbuka (jangan diselesaikan sendiri): klip Telegram (LB27, builder, 29 Okt sore WIB), angka H-1 (P182), konfirmasi run harian 29 Okt, potong klip video v2 (K1–K5, tugas terakhir), persona nyata (P183), nama juri (LB26).

## 7. Struktur 6 slide

| # | File | Waktu | Gagasan tunggal | Kata naskah |
|---|---|---|---|---|
| 1 | [[14-Deck-Demo-Day/DK1 - Slide 1 Kapan Ini Ditulis]] | 0:00–0:30 | Screenshot profit tidak bisa menjawab *kapan* ia ditulis — dan jutaan orang Indonesia membelinya | 66 |
| 2 | [[14-Deck-Demo-Day/DK2 - Slide 2 Kunci Segel Periksa]] | 0:30–0:55 | Fabius menjawab *kapan* dengan nomor blok: Lock → Seal → Check | 61 |
| 3 | [[14-Deck-Demo-Day/DK3 - Slide 3 Demo Beli lalu Periksa]] | 0:55–1:35 | Beli satu sinyal di Telegram tanpa gas → Verified, dibaca dari chain | 80 |
| 4 | [[14-Deck-Demo-Day/DK4 - Slide 4 Coba Curangi]] | 1:35–2:05 | Empat cara curang, empat penolakan kontrak — bukan janji kami | 60 |
| 5 | [[14-Deck-Demo-Day/DK5 - Slide 5 Dibangun untuk Diragukan]] | 2:05–2:40 | 0/6 lulus, kegagalan dipublikasikan, saklar uang mati: *Mainnet without proof is Cannae* | 75 |
| 6 | [[14-Deck-Demo-Day/DK6 - Slide 6 Apa lawan Kapan]] | 2:40–3:00 | *Others limit what AI can do. Fabius proves when it decided.* + QR `/tour` | 45 |

Total **387 kata** (naskah Indonesia, dihitung 29 Okt) ≈ 2:48 pada ±2,3 kata/detik + jeda tertulis ≈ 2:55. Naskah Inggris ±382 kata. Jendela waktu ini **menggantikan** jadwal 8 slide (28 Okt) dan tabel di [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] §7.

Busur emosi: **gelisah** (screenshot, "kapan?") → **lega** (ada jawabannya) → **yakin** (melihatnya bekerja) → **terkesan** (kontrak menolak kecurangan) → **percaya** (mereka jujur soal kelemahan) → **ingat** (what vs when + QR).

## 8. Sistem visual

| Unsur | Nilai |
|---|---|
| Latar slide | gelap `#0F0B26` (variasi `#07051A`, `#1A1442`) — warisan deck lama + video v1 |
| Teks | `#ECE8FA`; sekunder `#8B86A6` |
| Aksen | `#6E4BFF` (utama), `#9D86FF`, `#C9BDF2`; antagonis/ditolak `#FF5A6E`; hijau "pamer" hanya di kartu screenshot palsu DK1 |
| Font | **Archivo** (judul; tegak lebar untuk pernyataan, miring tebal untuk kata kunci — gaya hero web "SIGNALS / SEALED"), **Inter** (isi), **JetBrains Mono** (alamat, nama revert, nomor blok) |
| Motif | kubus kaca (situs: indigo = aturan terkunci, putih = terbukti, bening = kosong); garis rel/stasiun (halaman verify); gembok halus |
| Tangkapan web | situs berlatar **lavender terang** (`#ECE8FA`); di slide gelap, letakkan dalam bingkai browser/ponsel miring sedikit dengan glow `#6E4BFF` 20–30 % supaya tidak "bolong putih" |
| Kepadatan | ≤ 20 kata di slide; angka besar > kalimat; satu titik fokus per slide |
| Gerak | build sederhana (fade/slide 200–300 ms) yang mengikuti naskah; **tanpa** efek suara crash/glitch (larangan builder sejak video v2) |
| Aksesibilitas | kontras teks ≥ AA; ukuran isi ≥ 24 pt; nomor blok/label mono ≥ 16 pt; tidak menyampaikan informasi dengan warna saja (pakai ✓/✗/label) |
| Font cadangan | bila laptop presentasi tidak punya Archivo/Inter/JetBrains Mono: embed font, atau ekspor PDF/MP4 sebagai cadangan |

## 9. Fakta yang boleh dipakai

| Fakta | Nilai | Sumber | Status |
|---|---|---|---|
| Investor kripto Indonesia | **22,69 juta** (Juni 2026) | OJK via Bisnis.com (Materi Pitch §11) | ✅ tulis "OJK, Jun 2026" |
| Pedagang aset keuangan digital ilegal dihentikan | **228** (Jan–Mei 2026) | OJK SP 11/STPASTI/VI/2026 | ✅ "illegal crypto asset traders", **bukan** "grup sinyal" |
| Batas segel | **12 jam** sesudah hari tutup (`TooLate`) | `contracts/SignalAnchor.sol` `commit`, maxLag 43200 s | ✅ |
| Revert bernama | `TooLate`, `LockedAfterBar`, `NotLocked`, `TooManyReveals` | `/break` produksi 28 Okt 15:16Z, 4/4 | ✅ |
| Contoh hari bersinyal | B2-RS hari 2026-10-05: dikunci 2026-10-04 16:37:25Z; hari tutup 2026-10-06 00:00Z; 4 sinyal disegel 08:44Z (+8,7 j); 4 dibuka; SAH | `/tour` produksi 29 Okt | ✅ cadangan DK3 |
| Hari terverifikasi | **34 bot-hari SAH, 0 ALARM** (2–8 Okt); 16 bot-hari 9–10 Okt "tidak dikomit" karena engine dimatikan — tercatat publik, tidak disembunyikan | `python -X utf8 tools/verify_signals.py` 29 Okt | ⚠️ cetak ulang H-1 (P182) |
| Bot lulus uji maju | **0 dari 6** | `python -X utf8 -m engine.cli ledger fd16` | ⚠️ cetak ulang H-1, tulis "as of <tanggal>" |
| Riset awal | rugi di **12 dari 12** simbol sesudah ongkos | `vault/06-Results/04 - Negative Results.md` | ✅ |
| Koreksi diri | Sharpe B2-RS **1,29 → 0,85** | [[00-Overview/05 - Corrections]] | ✅ |
| False-pass gerbang | **±1 %** dari anggaran 5 % (uji sintetis) | deck lama slide 11 | ✅ hanya Q&A |
| Identitas | ERC-8004 #2494 (Fabius) | `vault/05-Ecosystem/01 - ERC-8004 Identity.md` | ✅ |
| Saklar uang nyata | `config/uang_nyata.json` `"aktif": false` | repo | ✅ |
| Harga sinyal | 0,01 FAB (token uji), pembeli tanpa gas | Materi Pitch §6 | ✅ sebut "test token" |
| Meja AI | siklus 5 menit, root di `DeskAnchor` ≤ 300 d | KP0 §1 | ✅ |
| Biaya mainnet | deploy ±$0,4, operasional ±$17/bulan | [[10-Submissions/05 - Estimasi Biaya Mainnet]] | hanya Q&A / lampiran |

Angka lain: **jangan**. Bila butuh angka yang tidak ada di sini, tanyakan builder.

## 9b. Daftar aset

| ID | Aset | Slide | Status |
|---|---|---|---|
| A1 | Kartu screenshot sinyal palsu (+312.4 %, nama samaran, cap waktu buram) | DK1 | buat ulang vektor; referensi video v2 0:00–7,6 (K1) |
| A2 | Rekaman Telegram: `/start` → `/buy` → bayar x402 → sinyal + link | DK3 | ⬜ builder 29 Okt sore WIB (LB27) |
| A3 | Rekaman `/tour` atau `/verify` sampai Verified | DK3 | ✅ rekam kapan saja |
| A4 | Rekaman `/break` "Try all four" | DK4 | ✅ rekam kapan saja (opsional; opsi A = kartu statis) |
| A5 | QR → `fabius-one.vercel.app/tour` | DK6 | buat sendiri, uji dari ±5 m |
| A6 | Wordmark FABIUS + kubus kaca | DK1, DK6 | deck lama / situs |
| K1–K5 | Potongan video v2 tanpa suara (hook, segel, meja AI, beli, periksa) | cadangan DK1/DK3 | ⬜ tugas terakhir (P185) |

## 10. Slide lampiran (tersembunyi, hanya untuk Q&A)
Taruh **sesudah** DK6, disembunyikan (tidak diputar), dengan tautan cepat dari speaker notes DK6:
- **L1 Arsitektur** — diagram: ledger publik (GitHub) → `LockRegistry` / `SignalAnchor` / `DeskAnchor` / `SelectionAnchor` (chain 97) → `/verify` · MCP · Telegram · x402. Tanpa angka baru.
- **L2 Kenapa bukan atestasi biasa (EAS/BAS)** — tabel 3 baris: atestasi mencatat *siapa + apa*; Fabius menegakkan *urutan terhadap hasil* (`TooLate`, `LockedAfterBar`, jumlah sinyal tetap + `markMissed`).
- **L3 Jalan ke uang sungguhan** — syarat F-D16 (20 sinyal / 20 hari / 2 bulan / CI > 0) + telaah hukum; biaya mainnet ±$0,4 deploy, ±$17/bulan; saklar publik.

## 11. Larangan (semua slide)
- Kata: "profitable", "edge", "win rate", "guaranteed", "used by other agents", "trustless", "tamper-proof", "first BNB-native", "the only one in the world", "mainnet" untuk apa pun yang testnet, "real-time signals". Cek setiap teks terhadap [[10-Submissions/01 - Claims Cheat Sheet]].
- Nama kompetitor **tidak** muncul di slide (hanya lisan di Q&A, tanpa menjelekkan).
- Tidak ada slide tim, slide "Thank you" terpisah, roadmap, atau slide tambahan di luar DK1–DK6 + L1–L3.
- "Andi" = ilustrasi: diucapkan sebagai contoh, tidak ditulis sebagai data; jangan menambah angka tentang Andi.
- Simulasi `/break` tidak boleh disebut transaksi; klip testnet tidak boleh dipotong sehingga label "testnet" hilang.
- Tidak ada efek suara crash/glitch/rusak.

## 12. Tanya jawab (2 menit) — lembar contekan di speaker notes DK6
Jawaban ≤ 20 detik. Lengkap di [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] §8; yang paling mungkin:

| Pertanyaan | Jawaban inti |
|---|---|
| "Tanpa edge, apa yang dijual?" | "Kemampuan memeriksa. Kami bisa membuktikan bahwa kami *belum* punya edge — penjual sinyal lain tidak bisa membuktikan apa pun soal rekamnya." |
| "Kenapa testnet?" | "Bukti jalan dulu, uang belakangan — aturannya dikunci on-chain: 20 sinyal, 20 hari, 2 bulan. Saklar uang nyata publik dan mati. Biaya ke mainnet kecil (±$0,4 deploy); yang mahal itu kehilangan kepercayaan." |
| "Sudah ada pengguna?" | "Belum ada pembeli luar. Jalurnya hidup dan bisa dicoba sekarang — QR di layar." |
| "Bisa commit 100 varian lalu buka yang menang?" | "Satu segel per bot per hari, jumlah sinyal dikunci, strategi dikunci sebelum hari itu, sinyal ekstra ditolak — itu demo kecurangan keempat." |
| "Bot tidak segel di hari buruk?" | "Jadi catatan `gap` di ledger berantai hash, publik, dihitung 'tak terukur', bukan nol. Contoh nyata: 13–27 Okt kami tercatat gap." |
| "Kenapa tidak EAS/BAS?" | lampiran L2. |
| "Committer terpusat?" | "Ya, satu kunci hari ini; pernah dirotasi saat bocor. Arahnya multisig/timelock. Yang tidak bisa dilakukan committer: menulis keputusan sesudah hasil — kontrak menolak." |
| "Jailbreak analis AI?" | "AI hanya memilih bot; formula terkunci yang menghitung posisi; root siklus wajib di chain dalam 300 detik." |
| "Model bisnis?" | "Per sinyal lewat x402, MCP untuk agen; penerbit bot dirancang dapat 60 % (belum deploy). Kami tidak mengambil bagian profit — itu wilayah regulasi." |
| "Beda dengan finalis X?" | kalimat pembeda di Materi Pitch §1 ("mereka membatasi *apa*, kami membuktikan *kapan*"). |

## 13. Hal yang sering terlewat (cek sebelum menyerahkan deck)
- **Internet mati**: klip tertanam; `/tour` dan `/break` dibuka di tab browser sebagai bonus, bukan ketergantungan; MP4 cadangan deck.
- **QR** diuji dari jarak ±5 m di layar proyektor (ukuran ≥ 25 % tinggi slide, kontras penuh, URL pendek tertulis di bawahnya).
- **Font** ter-embed atau diganti aman; cek di mesin lain (Keynote/PowerPoint/Google Slides merender beda).
- **Rasio** 16:9; tidak ada teks di 5 % tepi (proyektor sering memotong).
- **Timer**: naskah dibaca 3 kali dengan stopwatch; target 2:50–2:58. Bila lewat, potong kalimat bertanda *(boleh dipotong)* di DK.
- **Klik**: tiap klik/animasi ditandai di naskah (`[KLIK]`); klip mulai otomatis saat slide tampil, tanpa audio (narasi dari presenter).
- **Pagi Demo Day**: cek `fabius-one.vercel.app/status` hijau, `/tour` dan `/break` jawab, saldo committer, satu hari terbaru SAH (asisten bisa menjalankan cek ini).
- **Lembar Q&A** dicetak/di HP; lampiran L1–L3 siap dibuka.
- **Community Choice ($100)**: unggah klip `/break` + tautan `/tour` ke grup builder sesudah presentasi (KP10 #14, builder).

## 14. Kriteria selesai
- 6 slide utama persis urutan DK1–DK6 + L1–L3 tersembunyi; naskah terbaca 2:50–3:00.
- Setiap angka ada di §9 dengan status yang diizinkan; sumber kecil di pojok bila DK memintanya.
- Tidak ada kata di §11; nama kompetitor tidak ada di slide.
- Teks di slide ≤ ±20 kata (kecuali yang ditetapkan DK).
- Speaker notes = naskah lisan DK kata per kata + tanda `[KLIK]`.
- Placeholder bertanda merah jelas: `KLIP BELUM ADA — A2` (DK3), `ANGKA H-1 — P182` (DK5).
- Builder menyetujui (LB25).

**Terkait:** [[14-Deck-Demo-Day/DK1 - Slide 1 Kapan Ini Ditulis]] · [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] · [[12-Competitors/KP9 - Ranking dan Skenario Finalis]] · [[08-Backlog/13 - Langkah Builder Tertunda]]

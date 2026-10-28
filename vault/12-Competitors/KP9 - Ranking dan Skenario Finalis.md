---
tags: [kompetitor, "KP9"]
---

# KP9 - Ranking dan Skenario Finalis

**Bagian dari:** [[12-Competitors/00 - Hub Kompetitor]] · baseline: [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]]
**Sumber:** sintesis KP1–KP8 (21–26 Okt); halaman hackathon `/en`, `/en/prizes`, `/en/faq`, `/api/projects` (26–28 Okt); Lencana: `app/README.md` + halaman submission `proj_3b383cf48823e20042` (27 Okt); kata builder 27–28 Okt: *"total ada 10 finalis"*, *"presentasinya hanya 3 menit, 2 menit untuk juri bertanya"*, *"saya matiin krn boros usage di railway"*.

**Ringkas:** Ranking relatif sepuluh finalis (delapan kompetitor + Lencana + Fabius) dalam beberapa skenario keadaan Fabius, perkiraan distribusi hadiah per track, dan kecocokan Fabius dengan tiap track. Semuanya **penilaian analis**, bukan ukuran: bobot juri tidak dipublikasikan, hanya 10 dari 228 proyek yang dilihat, dan aturan "satu proyek boleh menang lebih dari satu hadiah" tidak ditemukan.

**Poin kunci:**
- Sensitivitas bobot (29 Okt, §8): sesudah `/tour` + `/break`, Fabius ke-2 (bobot teknis) sampai ke-5 (bobot UX) dari 10; tuas termurah tersisa = dampak (kasus nyata Indonesia).
- Lima kompetitor terkuat: **Kulaya, BagiPanen, Kawal, SAMA, Perago** (urut).
- Posisi Fabius: hari ini (layanan mati, `/status` alarm) **ke-7 dari 9**; semua layanan hidup **ke-5** (seri dengan Perago); + perbaikan demo **ke-4**; + lapisan bukti di mainnet: AI Agents juara **2–3**.
- Track terkuat Fabius = **AI Agents**. Finance: kandidat juara 3 bila dibingkai "payment rail untuk agen". Consumer: ke-4–6 (UX titik terlemah; kartu terbaik = Telegram bot).
- Skenario 10 finalis, Grand Prize ditumpuk ke juara track, satu hadiah track per proyek: **1 finalis tidak dapat hadiah track**; kandidat terkuat tersingkir = AgentEco, dengan Fabius di garis batas (AI Agents #3 direbut dengan Perago/AgentEco).
- Fabius dan Lencana (sama-sama milik builder) bertemu di AI Agents dan Consumer Apps.

**Detail:**

## 1. Track dan hadiah (situs resmi)

| Track | Deskripsi | Hadiah | Peserta (multi-track) |
|---|---|---|---|
| AI Agents | autonomous agents & AI x DeFi onchain | $600 / $400 / $300 | 141 |
| Finance & Commerce | DeFi, payments and RWA for Indonesia | $600 / $400 / $300 | 122 |
| Consumer Apps | social, gaming and loyalty with seamless UX | $600 / $400 / $300 | 132 |
| Grand Prize | best overall lintas track | $1.000 | — |
| Community Choice | dipilih sesama builder | $100 | — |

Total $5.000 / 11 pemenang; 228 proyek (93 satu track, 103 dua, 32 tiga).

## 2. Lima kompetitor terkuat

| # | Proyek | Irisan | Kenapa kuat | Celah |
|---|---|---|---|---|
| 1 | Kulaya ([[12-Competitors/KP8 - Kulaya]]) | semua + Grand | warung vs pinjol, persona Bu Sri, red-team console, dua bahasa, siklus pinjaman on-chain, hidup | reputasi AI n=1; belum pilot; bukan QRIS |
| 2 | BagiPanen ([[12-Competitors/KP4 - BagiPanen]]) | semua + Grand | ijon, dua kunci AI + koperasi, ERC-8004 sampai reputation registry, tur juri tanpa wallet, dirawat pasca-deadline | data petani contoh; verdict tak terikat waktu |
| 3 | Kawal ([[12-Competitors/KP7 - Kawal]]) | AI, Finance, Grand | ERC-8004 **mainnet**: 97 rekaman reputasi, mandat session key dieksekusi, MCP + A2A | UX formulir padat; tanpa model bisnis; AI tidak memutuskan |
| 4 | SAMA ([[12-Competitors/KP5 - SAMA]]) | semua + Grand | aset nyata di mainnet, angka biaya 4,4 %, UX + video setara iklan | AI tipis; backend tak publik; ronde mainnet pasca-deadline |
| 5 | Perago ([[12-Competitors/KP2 - Perago]]) | AI, Consumer, Grand | tesis sama dengan eksekusi DeFi nyata, kontrak tanpa owner, demo jalur gagal | video mentah; tanpa bisnis; repo berhenti 29 Sep |

Di luar lima besar: Matura (rekayasa paling rapi, tidak di AI Agents), AgentEco (lengkap, video 11 menit), Tagei (app mati 402).

## 3. Posisi Fabius per skenario (dari 9 proyek KP0–KP8)

| Skenario | Urutan | Catatan |
|---|---|---|
| Hari ini (Railway sebagian dimatikan, `/status` alarm, ledger berhenti 13 Okt) | 7 | di atas AgentEco, Tagei |
| Semua layanan hidup, hal lain sama | 5 (seri Perago) | menyalip Matura; eksekusi teknis paling lebar bila hidup |
| + demo diperbaiki (tur juri, konsol revert, tabel 3 tx, persona) | 4 | AI Agents rebutan juara 3 dengan Kawal |
| + lapisan bukti mainnet + ERC-8004 mainnet | 4 | AI Agents juara 2–3 |

Kenapa tetap sulit melewati Kulaya/BagiPanen/Kawal: keunggulan mereka di persona/dampak, demo yang bisa dicoba juri, dan (Kawal) ERC-8004 mainnet tidak tertutup oleh layanan hidup. Kekurangan UX Fabius yang spesifik: tidak ada satu tugas utama (4 jenis pengguna, ±10 halaman); jargon di permukaan (G1–G11, F-D16, tick, reveal, sha); tidak ada tur juri tanpa login; tidak ada konsol "coba patahkan"; momen "aha" tertunda (sinyal dari bot yang belum lulus); gesekan awal (Privy + FAB faucet). Kelebihan: Privy sosial login, Telegram Mini App, MCP. Penilaian ini dari struktur rute/deck/video, bukan uji tangan.

## 4. Kecocokan Fabius per track

| Track | Kartu Fabius | Kelemahan | Perkiraan |
|---|---|---|---|
| AI Agents | desk multi-agen ERC-8004, AI memutuskan dalam batas formula, MCP, x402 | — | juara 3 (testnet) / 2–3 (mainnet) |
| Finance & Commerce | x402 = payment rail agen; B5-CORE-RWA; 60/40 publisher | tanpa sudut Indonesia, token tes, 60/40 belum deploy | juara 3 bila framing "payment rail untuk agen", rebutan Matura/SAMA |
| Consumer Apps | Telegram bot + Mini App, beli gasless di chat, Privy | sinyal belum lulus → tak ada "hasil" untuk konsumen; konsep berat | 4–6 |

Bila satu proyek hanya boleh satu hadiah track, ikut tiga track tidak menambah peluang; fokus AI Agents.

## 5. Perkiraan distribusi 10 finalis (skenario Grand Prize ditumpuk)

| Track | 1 | 2 | 3 |
|---|---|---|---|
| AI Agents | BagiPanen | Kawal | **Fabius** (rebutan Perago/AgentEco) |
| Finance & Commerce | Kulaya | SAMA | Matura |
| Consumer Apps | Lencana | Perago | Tagei |
| Grand Prize | Kulaya (ditumpuk) | | |
| Tanpa hadiah track | AgentEco | | |

Bila Grand Prize **tidak** ditumpuk (pemenang Grand tidak mengambil slot track), 10 hadiah juri cukup untuk 10 finalis. Aturannya tidak ditemukan di situs. Community Choice tidak bisa diprediksi dari kualitas.

## 5b. Pembaruan 28 Okt: bocoran top-15 (kata builder, tidak resmi)
Top-15 = 5 per track; kelima proyek Finance tidak masuk top-10. Hadiah Finance kemungkinan diisi dari finalis yang ikut Finance (Kulaya, BagiPanen, SAMA, AgentEco, Kawal, Matura, Tagei, Fabius; Perago dan Lencana tidak ikut Finance) → pengocokan ulang memperbesar peluang **Fabius di AI Agents dan Lencana di Consumer** sekaligus, dengan Finance sebagai peluang tambahan Fabius. Rincian: [[12-Competitors/KP10 - Celah Analisis dan Solusi]] §1.

## 6. Lencana (finalis ke-10, milik builder) — profil singkat
AI Agents + Consumer Apps; tim Mythos 3 orang. Kredensial kursus Open Badges 3.0 / VC 2.0, atestasi lewat BAS (EAS publik), status revocation dibaca dari chain, verifikasi tanpa wallet, x402 untuk verifikasi mesin, artefak soulbound, validator 1EdTech `VALID` 14 cek 0 galat, edge worker hidup (`lencana-edge.hansgunawan775.workers.dev` 200, 27 Okt). Belum dianalisis sedalam KP1–KP8; penempatan Consumer #1 adalah penilaian tipis.

## 8. Sensitivitas bobot juri (KP10 #15, 29 Okt)
Bobot juri tidak dipublikasikan, jadi posisi dihitung ulang di bawah lima profil bobot. Skor 1–5 per kriteria = **penilaian analis** dari KP1–KP8 (bukan ukuran); urutan di bawah dari 10 finalis.

| Proyek | Inovasi | Teknis | Dampak/Indonesia | UX/demo | Hidup/lengkap | Bisnis |
|---|---|---|---|---|---|---|
| Kulaya | 4 | 4 | 5 | 5 | 5 | 3 |
| BagiPanen | 4 | 4 | 5 | 4 | 5 | 3 |
| Kawal | 4 | 5 | 3 | 3 | 5 | 2 |
| SAMA | 3 | 3 | 4 | 5 | 4 | 4 |
| Perago | 4 | 4 | 3 | 3 | 4 | 2 |
| Matura | 3 | 5 | 3 | 3 | 4 | 3 |
| AgentEco | 3 | 3 | 3 | 3 | 4 | 3 |
| Tagei | 3 | 3 | 3 | 3 | 2 | 3 |
| Lencana (penilaian tipis, §6) | 4 | 4 | 3 | 4 | 4 | 3 |
| **Fabius 29 Okt** (`/tour` + `/break` tayang, `/verify` 1–2 s, Railway hidup) | 5 | 5 | 3 | 3 | 4 | 3 |
| Fabius sebelum 28 Okt (tanpa tur/konsol, `/verify` 504) | 5 | 5 | 3 | 2 | 3 | 3 |
| Fabius + lapisan bukti mainnet (P179) | 5 | 5 | 3 | 3 | 5 | 3 |

Bobot profil (Inovasi/Teknis/Dampak/UX/Hidup/Bisnis): Rata = sama; Teknis-inovasi 25/30/10/10/20/5 (juri BNB Chain, dev Web3); Dampak-pasar 15/10/30/20/10/15 (Coinvestasi, investor ritel); UX-produk 10/10/20/35/15/10; Pitch 3 menit 20/15/20/25/15/5.

| Profil | Fabius sebelum 28 Okt | **Fabius 29 Okt** | Fabius + mainnet | Tiga teratas (29 Okt) |
|---|---|---|---|---|
| Rata | 7 | **4** (seri SAMA 3,83) | 3 | Kulaya 4,33 · BagiPanen 4,17 · SAMA 3,83 |
| Teknis-inovasi | 4 | **2** (4,30 vs Kulaya 4,35) | 1 | Kulaya · Fabius · BagiPanen 4,25 |
| Dampak-pasar | 7 | **4** | 4 | Kulaya 4,45 · BagiPanen 4,25 · SAMA 3,95 |
| UX-produk | 9 | **5** | 5 | Kulaya 4,60 · BagiPanen 4,25 · SAMA 4,15 |
| Pitch 3 menit | 8 | **4** | 3 | Kulaya 4,55 · BagiPanen 4,30 · SAMA 3,90 |

**Bacaan:** (1) `/tour` + `/break` + `/verify` yang pulih menaikkan Fabius 3–4 peringkat di semua profil - kenaikan terbesar dari UX/demo dan "hidup", bukan dari fitur baru. (2) Fabius hanya mendekati puncak bila juri menimbang teknis/inovasi; pada dampak dan UX ia tertahan di 4–5 karena Dampak/Indonesia = 3 (tanpa persona nyata, P183) dan UX = 3. (3) Mainnet hanya menggeser "hidup/lengkap"; efeknya ±1 peringkat dan tidak menolong di profil dampak/UX. (4) Tuas termurah yang tersisa = Dampak: satu kasus nyata Indonesia + angka OJK 228 di slide 2 (DK2) menaikkan Dampak 3→4 → profil Rata/Pitch naik ke 3. Di dalam track AI Agents saja (BagiPanen, Kawal, Perago, AgentEco, Lencana, Fabius; Kulaya/SAMA diandaikan diambil Finance/Grand): Fabius ke-1 (teknis-inovasi), ke-2 (rata, dampak, pitch; di bawah BagiPanen), ke-3 (UX-produk; di bawah BagiPanen dan Lencana).

## 7. Batas
Info "10 finalis" dari builder (situs belum mempublikasikan); ranking = penilaian; KP0 §4 memuat cek hidup 26 Okt yang sebagian disebabkan keputusan biaya builder (Railway), tetapi kegagalan `ledger verify` B4 (P173) terpisah dari Railway.

**Terkait:** [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] · [[10-Submissions/05 - Estimasi Biaya Mainnet]] · [[12-Competitors/KP8 - Kulaya]]

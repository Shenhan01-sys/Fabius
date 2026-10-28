---
tags: [kompetitor, "KP9"]
---

# KP9 - Ranking dan Skenario Finalis

**Bagian dari:** [[12-Competitors/00 - Hub Kompetitor]] · baseline: [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]]
**Sumber:** sintesis KP1–KP8 (21–26 Okt); halaman hackathon `/en`, `/en/prizes`, `/en/faq`, `/api/projects` (26–28 Okt); Lencana: `app/README.md` + halaman submission `proj_3b383cf48823e20042` (27 Okt); kata builder 27–28 Okt: *"total ada 10 finalis"*, *"presentasinya hanya 3 menit, 2 menit untuk juri bertanya"*, *"saya matiin krn boros usage di railway"*.

**Ringkas:** Ranking relatif sepuluh finalis (delapan kompetitor + Lencana + Fabius) dalam beberapa skenario keadaan Fabius, perkiraan distribusi hadiah per track, dan kecocokan Fabius dengan tiap track. Semuanya **penilaian analis**, bukan ukuran: bobot juri tidak dipublikasikan, hanya 10 dari 228 proyek yang dilihat, dan aturan "satu proyek boleh menang lebih dari satu hadiah" tidak ditemukan.

**Poin kunci:**
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

## 7. Batas
Info "10 finalis" dari builder (situs belum mempublikasikan); ranking = penilaian; KP0 §4 memuat cek hidup 26 Okt yang sebagian disebabkan keputusan biaya builder (Railway), tetapi kegagalan `ledger verify` B4 (P173) terpisah dari Railway.

**Terkait:** [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] · [[10-Submissions/05 - Estimasi Biaya Mainnet]] · [[12-Competitors/KP8 - Kulaya]]

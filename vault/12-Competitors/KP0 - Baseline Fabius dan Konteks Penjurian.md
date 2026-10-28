---
tags: [kompetitor, "KP0"]
---

# KP0 - Baseline Fabius dan Konteks Penjurian

**Bagian dari:** [[12-Competitors/00 - Hub Kompetitor]]
**Sumber:** halaman submission Fabius `https://indonesiaweb3hack.xyz/en/projects/proj_2a7f1e5c86dac014a8` (diambil 26 Okt 2026) · `/en/faq`, `/en/prizes`, `/en/schedule`, `/api/projects` situs hackathon (26 Okt) · [[10-Submissions/01 - Claims Cheat Sheet]] · [[07-Testing/01 - Test Commands]] · `vault/13-SubmmisionDocs/Fabius-Submission-Deck-final.pptx` · cek hidup 26 Okt (perintah di §4)

**Ringkas:** Halaman ini adalah pembanding tetap untuk KP1–KP8, supaya fakta Fabius tidak ditulis ulang delapan kali dan supaya setiap SWOT memakai penggaris yang sama. Isinya: apa yang **dilihat juri** dari Fabius (bukan yang ada di vault), konteks penjurian yang dipublikasikan panitia, dan keadaan hidup Fabius per 26 Okt. Ia **bukan** klaim produk baru: angka Fabius di sini dikutip dari halaman vault yang menyebut perintahnya, dan angka hasil cek hidup diberi label *(cek hidup 26 Okt)* karena dibaca dari GitHub API / Railway / HTTP, bukan dari perintah di repo.

**Poin kunci:**
- Fabius **sudah submit** (7 Okt 2026, deadline yang diperpanjang dari 30 Sep ke 7 Okt 23:30 WIB) di **ketiga track**: AI Agents, Consumer Apps, Finance & Commerce. Tim "Mythos05", 1 anggota. Kontrak utama di form: `SignalAnchor 0x9B78…64f3` (testnet 97).
- Video yang **di-submit adalah v1** (`youtu.be/6lldM9-cruw`, 127 d, 29 views per 26 Okt), bukan v2 94,5 d yang masih menunggu builder (LB21).
- Juri menilai 5 kriteria tanpa bobot publik: inovasi, eksekusi teknis, potensi dampak + kelayakan bisnis, UX, kualitas presentasi + demo (`/en/faq` #07).
- 228 proyek; 141 di AI Agents, 132 Consumer, 122 Finance (multi-track boleh). Hadiah: $600/$400/$300 per track, Grand Prize $1.000, Community Choice $100.
- Timeline: finalis 14 Okt (status di situs masih "Next"), **Demo Day + pengumuman pemenang 31 Okt 2026** (live di depan juri).
- *(cek hidup 26 Okt)* halaman `/status` Fabius publik menyala **`overall: alarm`**, gate x402 membalas **HTTP 500 `BlockingIOError`**, ledger paper berhenti commit sejak 13 Okt, committer `fabius-engine` mati. Ini yang akan dilihat juri yang mengklik hari ini.

**Detail:**

## 1. Apa yang dilihat juri dari Fabius (halaman submission, 7 Okt)

| Aspek | Isi |
|---|---|
| Tagline | "Plug in your bot or agent, prove every call on-chain, sell it to anyone via x402 and MCP" |
| Problem | Track record bot/signal seller ditulis **sesudah** pasar bergerak; pembeli tidak bisa memeriksa apa yang diputuskan, kapan, apakah strategi diubah, apakah sinyal kalah dihapus. LLM memperburuk: bisa menjelaskan apa pun secara hindsight. |
| Solution | Rules first (`LockRegistry`, `LockedAfterBar`) → commit-reveal Merkle per bar (`SignalAnchor`, `TooLate` 12 j) → desk AI 5 menit dengan analis ERC-8004 (`SelectionAnchor`, `DeskAnchor`) di mana formula terkunci, bukan LLM, menghitung posisi → gerbang G1–G11 yang sama untuk bot luar → jual per sinyal via x402 (FAB, gasless) → jujur by design (0 dari 6 bot lulus F-D16 per 6 Okt). |
| Kontrak Fabius | `SignalAnchor`, `LockRegistry`, `SelectionAnchor`, `DeskAnchor`, `FabiusCredit` (testnet 97) |
| Bukti di halaman | `ledger verify` 16 commit / 16 sah / 0 terlewat (snapshot 6 Okt); contoh B2-RS bar 2026-10-05 di-commit +8 j 44 m; false-positive gerbang ±1 % vs anggaran 5 % |
| Yang tidak diklaim | profit, edge, win rate; uang nyata; 60/40 `BotRegistry`/`RevenueSplitter` belum deploy |

Video v1 (127 d, motion graphics ungu-gelap, narasi Inggris): hook sejarah Fabius vs Hannibal → screenshot profit +312,4 % sebagai antagonis → enam bot → Merkle tree → desk AI dengan formula `bot* = argmax Σ conf × score` → submit bot/agen → x402 "402" → "zero of six have passed" → "Refuse the battle. Prove the decision." Tidak ada layar wallet / transaksi / BscScan sungguhan; UI tampil sebagai mockup 3D. Vault sendiri menilai v1 penuh jargon (`vault/Video-Workspace/PLAN-v2.md`).

Deck 12 slide (7 Okt): "Signals sealed before the outcome", "Proof of timing, not of profit", 22 commit harian / 0 alarm / 0 terlewat, 11 lock on-chain, 6 bot, "Built to be doubted: 0/6 bots passed forward; ~1 % false-pass". Deck tidak diwajibkan panitia, tapi ditautkan di halaman.

## 2. Inventaris kekuatan yang bisa dipakai di SWOT (as of 7 Okt)
- Urutan sebagai produk: commit sebelum hasil, block time = alibi; ditegakkan kontrak (`TooLate`, `LockedAfterBar`) bukan janji.
- Verifikasi tanpa kunci & tanpa gas: `python -X utf8 -m engine.cli ledger verify`, `python -X utf8 tools/verify_signals.py`, halaman `/verify`.
- Lima kontrak sendiri + rel standar (ERC-8004 tokenId 2494, proxy x402 kanonis, Permit2).
- Uji: Python 743 lulus / 0 gagal, forge 117 lulus di 8 suite, T8 224 baris 0 masalah ([[07-Testing/01 - Test Commands]] baris 123/126, 7 Okt).
- Pintu terbuka: `/submit` (rule/feed/agent), `/submit-agent`, MCP `/mcp`, Telegram bot + Mini App, Privy (Google/Telegram/email).
- Kejujuran terukur: hasil negatif dipublikasikan (`06-Results/04 - Negative Results.md`), banned claims ([[10-Submissions/01 - Claims Cheat Sheet]]).

## 3. Inventaris kelemahan yang bisa dipakai di SWOT
- Tidak ada edge dan tidak ada pengguna luar: 0/6 bot lulus forward, MCP belum pernah dipakai agen luar (Not Yet Proven #22), satu-satunya agen "luar" (2573) milik builder.
- Uang mainan: FAB tanpa nilai, testnet; pembelian x402 hanya oleh builder.
- Kompleksitas tinggi: 6 bot, G1–G11, beberapa lock, desk 5 menit, peninjau LLM; satu kalimat nilai untuk orang awam tidak ada di permukaan.
- Sentralisasi: satu committer key, validator ERC-8004 milik sendiri, satu penulis ledger.
- Masalah Indonesia: tidak ada sudut Indonesia di problem/solution (yang ada hanya bahasa vault).
- Operasional rapuh *(cek hidup 26 Okt)*: lihat §4.

## 4. Keadaan hidup 26 Okt *(cek hidup, bukan perintah repo)*

| Yang dicek | Hasil | Perintah |
|---|---|---|
| `/status` publik | `overall: alarm`, B1 `TICK_MISSED` bar 2026-10-25 | `curl -s https://fabius-one.vercel.app/api/status` |
| Gate x402 | HTTP 500 `{"error": "BlockingIOError"}` | `curl -s https://fabius-x402-production.up.railway.app/` |
| Ledger paper | commit `ledger/paper` terakhir 2026-10-13; `ledger verify` GAGAL di B4-LISTING-FADE tick 2026-10-12 (`data_hash` dan `signal_ids` beda dari hitung ulang) → workflow menolak commit | `gh run view <id> -R Shenhan01-sys/Fabius --log` |
| Railway | `fabius-engine` tanpa deployment aktif; `fabius-probe` hidup tapi gagal `cannot fork()` tiap 10 menit; `fabius-x402` hidup | `railway deployment list -p <project> -s <service>` |
| Landing | `fabius-one.vercel.app` 200, snapshot terakhir 11 Okt | `curl -o /dev/null -w '%{http_code}'` |

Konteks (kata builder 27 Okt): layanan Railway dimatikan **sengaja karena biaya usage**, bukan karena rusak; log menunjukkan sebelumnya berjalan. Kegagalan `ledger verify` B4 (P173) terpisah dari Railway dan tetap menahan rantai ledger. Keduanya dicatat sebagai P173/P174.

Implikasi untuk semua SWOT: klaim submission "no human in the loop" dan "16 commits, 16 valid, 0 missed" **tidak lagi benar hari ini**. Kalau Fabius masuk finalis, Demo Day 31 Okt akan memperlihatkan alarm kecuali rantai dipulihkan sebelumnya.

## 5. Penggaris yang dipakai KP1–KP8
- Lima kriteria panitia, **tanpa bobot** (bobot tidak dipublikasikan; menebak bobot = klaim di luar yang diukur). Tiap kriteria dinilai relatif: Fabius **unggul / setara / kalah** terhadap satu kompetitor, dengan alasan yang bisa ditunjuk sumbernya.
- Track yang dipertandingkan: hanya irisan track kedua proyek; Grand Prize selalu irisan.
- Angka kompetitor bersumber dari scrape di workspace `../Competitors/<NN-Nama>/` *(workspace, di luar repo Fabius)*: `page/page.txt`, `github/` (README, `commits.tsv`, `src/`), `deck/deck.txt`, `video/transcript.txt` + `video/analysis.md`. Diambil 21–26 Okt 2026. Bukan klaim produk Fabius.
- SWOT selalu dari sudut **Fabius**: S/W = internal Fabius dibanding kompetitor itu; O/T = peluang dan ancaman yang muncul karena kompetitor itu ada di lapangan yang sama.
- Penilaian "unggul/kalah" adalah pendapat analis, bukan ukuran. Ia ditandai sebagai penilaian.

**Terkait:** [[12-Competitors/00 - Hub Kompetitor]] · [[10-Submissions/01 - Claims Cheat Sheet]] · [[06-Results/03 - Not Yet Proven]] · [[08-Backlog/13 - Langkah Builder Tertunda]]

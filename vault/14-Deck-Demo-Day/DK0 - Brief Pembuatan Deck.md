---
tags: [deck, "DK0"]
---

# DK0 - Brief Pembuatan Deck

**Bagian dari:** [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]]
**Sumber:** [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] (strategi + naskah USULAN), [[12-Competitors/00 - Hub Kompetitor]] (KP0–KP10), [[10-Submissions/01 - Claims Cheat Sheet]], deck lama `vault/13-SubmmisionDocs/Fabius-Submission-Deck-final.pptx` (gaya visual), kata builder 28 Okt.
**Untuk:** agen pembuat PPT (serah terima). Baca halaman ini sampai habis sebelum membuka file lain.

**Ringkas:** Kamu membuat **deck presentasi Demo Day Fabius** untuk Indonesia Web3 Hackathon 2026, **31 Okt 2026**: **3 menit presentasi + 2 menit tanya jawab**, live di depan juri. Deck terdiri dari **8 slide**; isi tiap slide ada di satu file `DK1`–`DK8` di folder ini (naskah lisan per detik, teks di slide, visual, angka + sumber, aset, larangan). Tugasmu: mengubah delapan panduan itu menjadi satu file PPTX 16:9 yang memakai gaya visual Fabius, dengan naskah di speaker notes dan klip demo tertanam. Kamu **tidak** mengarang angka, klaim, atau slide tambahan.

## 1. Untuk apa deck ini

| Hal | Isi |
|---|---|
| Acara | Demo Day Indonesia Web3 Hackathon 2026 (co-host Binance Academy, BNB Chain, Coinvestasi; mentor Dev Web3 Jogja). Finalis presentasi live; pemenang diumumkan hari itu. |
| Format | **3:00 presentasi + 2:00 tanya jawab** (kata builder 28 Okt). Melebihi 3:00 = dipotong. |
| Proyek | **Fabius** — operator sinyal trading paper yang **mengunci strategi dan menyegel setiap keputusan on-chain sebelum hasilnya ada**, bisa diperiksa siapa pun tanpa kunci dan tanpa gas. BNB Smart Chain testnet (chain 97). |
| Track sasaran | **AI Agents** (track utama Fabius). Fabius terdaftar di tiga track; info tak resmi dari builder: Fabius bersaing di AI Agents, Lencana (proyek lain builder) di Consumer. Finance cukup satu kalimat. |
| Juri menilai | 5 kriteria tanpa bobot publik: inovasi, eksekusi teknis, dampak + kelayakan bisnis, UX, kualitas presentasi + demo (`/en/faq` #07). |
| Tujuan deck | Membuat juri mengingat **satu kalimat**: *"Semua agen bilang AI-nya dibatasi. Fabius satu-satunya yang membuktikan **kapan** AI-nya memutuskan — dengan nomor blok."* |
| Strategi | **Pindah arena** (lihat [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] §1): jangan bersaing di dampak sosial (BagiPanen, Kulaya) atau eksekusi mainnet (SAMA, Kawal); posisikan Fabius sebagai lapisan *bukti waktu keputusan* yang tidak dimiliki finalis lain. **Testnet tidak ditutupi** — dijadikan tesis: *"Mainnet tanpa bukti itu Cannae."* |

## 2. Peta baca (urut; ambil hanya yang disebut)

| # | File vault | Ambil apa | Wajib? |
|---|---|---|---|
| 1 | [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]] | daftar slide + urutan | wajib |
| 2 | **DK1–DK8** di folder ini | isi persis tiap slide | wajib |
| 3 | [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] | alasan strategi (§1 pindah arena, §4 testnet, §5 dampak, §7 naskah, §9 kerangka) | wajib |
| 4 | [[10-Submissions/01 - Claims Cheat Sheet]] | kalimat terlarang + pengganti; cek SETIAP teks slide terhadapnya | wajib |
| 5 | [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]] §1–§2 | apa yang sudah dilihat juri dari Fabius (halaman submission, video v1, deck lama) | wajib |
| 6 | [[12-Competitors/00 - Hub Kompetitor]] (tabel ringkasan) | posisi Fabius vs 8 kompetitor — **hanya untuk memahami**, nama kompetitor tidak masuk slide | baca |
| 7 | [[12-Competitors/KP10 - Celah Analisis dan Solusi]] | celah yang masih terbuka (angka belum dicetak ulang, aset demo belum ada) | baca |
| 8 | `vault/13-SubmmisionDocs/Fabius-Submission-Deck-final.pptx` | **gaya visual** (warna, font, tata letak) — bukan isi | wajib (gaya) |
| 9 | `vault/Video-Workspace/SCRIPT.md`, `PLAN-v2.md`, `render/fabius-pitch-v2.mp4` | klip/tangkapan yang bisa dipakai ulang (v2 belum disetujui builder, LB21) | opsional |
| 10 | [[10-Submissions/05 - Estimasi Biaya Mainnet]] | hanya bila builder minta slide cadangan "berapa biaya ke mainnet" (tidak di 8 slide) | opsional |
| 11 | `README.md` (root repo Fabius) bagian atas + `contracts/SignalAnchor.sol` baris 69–104 | nama revert `TooLate`, `LockedAfterBar` persis | rujukan |

Jangan membaca seluruh vault (±300 halaman); peta di atas cukup.

## 3. Gaya visual (warisi deck lama dan web)

| Unsur | Nilai (dari `Fabius-Submission-Deck-final.pptx`) |
|---|---|
| Latar | ungu sangat gelap `#0F0B26` (variasi `#07051A`, `#1A1442`) |
| Teks utama | `#ECE8FA` |
| Aksen | `#6E4BFF` (utama), `#9D86FF`, `#C9BDF2`; peringatan/antagonis `#FF5A6E` |
| Font | **Archivo** (judul), **Inter** (isi), **JetBrains Mono** (alamat, nama fungsi, angka teknis) |
| Rasio | 16:9 |
| Prinsip | satu gagasan per slide; maks ±20 kata di slide (naskah ada di speaker notes); angka besar > paragraf; nama kontrak/fungsi kecil dalam mono |
| Referensi rasa | video v1 (`youtu.be/6lldM9-cruw`): kubus/Merkle tree ungu, kartu screenshot profit, "Refuse the battle. Prove the decision." |

## 4. Fakta yang boleh dipakai (dengan status)

| Fakta | Nilai | Sumber | Status untuk slide |
|---|---|---|---|
| Investor kripto Indonesia | **22,69 juta** (Juni 2026) | OJK via Bisnis.com (tautan di [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] §11) | ✅ boleh, cantumkan "Sumber: OJK, Juni 2026" |
| Entitas aset digital ilegal dihentikan Satgas PASTI | 228 (Jan–Mei 2026) | ringkasan pencarian | ⛔ **belum diverifikasi** — jangan dipasang kecuali builder sudah cek siaran pers OJK (P183) |
| Bot lulus uji maju F-D16 | **0 dari 6** | `python -X utf8 -m engine.cli ledger fd16` (6 Okt) | ⚠️ cetak ulang H-1 (P182); sebut "per <tanggal>" |
| Aturan arah riset fase awal | rugi di **12 dari 12** simbol sesudah ongkos | `vault/06-Results/04 - Negative Results.md`, README | ✅ |
| Koreksi diri | Sharpe B2-RS **1,29 → 0,85** | [[00-Overview/05 - Corrections]] (2 Okt) | ✅ |
| False-positive gerbang | **±1 %** dari anggaran 5 % | deck lama slide 11, `vault/Dashboard.md` (4 Okt) | ✅ sebut "uji sintetis" |
| Batas commit | **12 jam** sesudah bar tutup (`TooLate`) | `contracts/SignalAnchor.sol:104`, deploy maxLag 12 h | ✅ |
| Strategi dikunci sebelum bar | `LockedAfterBar` | `contracts/SignalAnchor.sol:101` | ✅ |
| Siklus desk AI | root wajib on-chain dalam **300 detik** (`DeskAnchor`) | [[02-Contracts/00 - Hub Contracts]], KP0 | ✅ |
| Identitas agen | ERC-8004 tokenId **2494** (Fabius); analis 2558/2559/2561/2566/2567 | `vault/05-Ecosystem/01 - ERC-8004 Identity.md` | ✅ |
| Saklar uang nyata | `config/uang_nyata.json` `"aktif": false` | repo | ✅ |
| Kontrak utama | `SignalAnchor 0x9B78200beFbbBe836585d31bd5b6dB32587064f3` (chain 97) | halaman submission | ✅ |
| Ledger 13–27 Okt | tercatat sebagai **gap** (tidak diisi mundur) setelah P173 di-push | P173 | gunakan hanya di Q&A |

Semua angka lain: **jangan**. Bila sebuah angka tidak ada di tabel ini, tanyakan builder.

## 5. Aset yang dibutuhkan (status)

| ID | Aset | Dipakai di | Status / cara membuat |
|---|---|---|---|
| A1 | Kartu screenshot profit "+312,4 %" (antagonis) | DK1 | ada di video v1 (frame 0:16) dan sumber Remotion `vault/Video-Workspace/src/`; buat ulang sebagai grafik bila tak bisa diekstrak |
| A2 | Klip Telegram: `/buy` sinyal B1 → bayar gasless → link verify (±30 d, termasuk halaman verify) | DK4 | ⬜ **builder merekam (LB27)**; cadangan: tangkapan layar dari video v1 (frame 1:28 "Signals sell over x402") |
| A3 | Tangkapan `/verify` menampilkan commit sebelum penutupan bar + "SAH" | DK4 | ⬜ setelah P173 di-push dan rantai hidup (LB28, LB22); cadangan: video v2 |
| A4 | Klip revert `TooLate` (±15 d) | DK5 | ⬜ buat dengan simulasi tanpa broadcast: `cast call` fungsi `commit` ke `SignalAnchor` chain 97 dengan `asof` lama → `TooLate(...)`; cadangan: keluaran `forge test --match-test` untuk tes `TooLate` (`test/SignalAnchor.t.sol:148`) |
| A5 | QR ke `https://fabius-one.vercel.app/verify` | DK8 | buat sendiri |
| A6 | Logo/wordmark FABIUS | DK1, DK8 | dari deck lama / web |

Klip harus **tertanam** di PPTX (tidak bergantung internet). Tautan live hanya bonus.

## 6. Larangan (berlaku di semua slide)
- Kata: "profitable", "edge", "win rate", "used by other agents", "trustless validation", "first BNB-native", "mainnet" (untuk apa pun yang testnet). Lihat [[10-Submissions/01 - Claims Cheat Sheet]].
- Nama kompetitor **tidak** muncul di slide (hanya di jawaban lisan Q&A).
- Tidak ada slide tambahan, tidak ada angka di luar §4, tidak ada efek suara crash/glitch (keputusan builder untuk video v2).
- Persona "Andi" adalah **ilustrasi** — di slide tulis tanpa klaim data pribadi; jangan menambah angka tentang Andi.

## 7. Tanya jawab (2 menit) — bukan slide, taruh di speaker notes DK8 sebagai lembar contekan
Jawaban ≤ 20 detik; sumber: [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] §8 + tambahan berikut:
- *"Kenapa tidak EAS/BAS saja?"* — "Atestasi mencatat siapa dan apa. Kontrak kami menegakkan **urutan terhadap hasil**: lewat 12 jam ditolak (`TooLate`), strategi dikunci sebelum bar (`LockedAfterBar`), satu commit per bot per bar dengan jumlah sinyal tetap."
- *"Bagaimana kalau bot tidak commit di hari buruk?"* — "Hari tanpa tick sebelum batas jadi catatan `gap` di ledger berantai hash — tidak bisa dihapus, dihitung tak terukur, bukan nol. Contoh nyata: 13–27 Okt kami tercatat gap, dan itu publik."
- *"Kenapa testnet?"* — naskah DK6.

## 8. Keluaran yang diminta
1. `vault/13-SubmmisionDocs/Fabius-DemoDay-Deck.pptx` — 8 slide, 16:9, gaya §3, naskah DK lengkap di **speaker notes** tiap slide, klip A2/A4 tertanam (atau placeholder bertanda jelas bila aset belum ada).
2. `vault/13-SubmmisionDocs/Fabius-DemoDay-Deck.pdf` — ekspor cadangan.
3. Daftar singkat aset yang masih placeholder + slide mana.

## 9. Kriteria selesai
- 8 slide persis, urutan DK1–DK8; total naskah terbaca dalam **2:50–3:00** dengan timer.
- Jendela waktu per slide (dari panjang naskah, ±2,4 kata/detik, total ±416 kata): DK1 0:00–0:15 · DK2 0:15–0:43 · DK3 0:43–1:08 · DK4 1:08–1:40 · DK5 1:40–1:57 · DK6 1:57–2:25 · DK7 2:25–2:50 · DK8 2:50–3:00. Jadwal ini **menggantikan** tabel waktu di [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] §7.
- Setiap angka di slide ada di §4 dan memakai status yang diizinkan; sumber kecil di pojok bila disebut di DK.
- Tidak ada kata di §6.
- Teks di slide ≤ ±20 kata (kecuali tabel DK7, ≤ 6 baris).
- Speaker notes = naskah lisan DK, kata per kata.
- Builder menyetujui (LB25) sebelum dianggap final.

## 10. Yang masih terbuka (jangan diselesaikan sendiri)
- LB25 naskah belum disetujui; bahasa presentasi (Indonesia/Inggris) belum diputuskan — naskah DK ditulis Bahasa Indonesia, teks slide Bahasa Inggris (konsisten dengan web/deck lama).
- P182 angka belum dicetak ulang; P183 angka 228 belum diverifikasi; A2–A4 belum direkam.
- Format Demo Day (online/offline, putar video, internet) belum dikonfirmasi (LB26).

**Terkait:** [[14-Deck-Demo-Day/DK1 - Slide 1 Hook]] · [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] · [[08-Backlog/13 - Langkah Builder Tertunda]]

---
tags: [submission, pitch]
---

# 04 - Demo Day 31 Okt - Materi Pitch

**Bagian dari:** [[10-Submissions/00 - Hub Submissions]]
**Sumber:** brainstorm + analisis kompetitor 21–28 Okt 2026 ([[12-Competitors/00 - Hub Kompetitor]], [[12-Competitors/KP9 - Ranking dan Skenario Finalis]]); format dari kata builder 28 Okt: *"presentasinya hanya 3 menit, 2 menit untuk juri bertanya"*; angka eksternal di §2 bersumber berita/OJK (tautan di §11).
**Status:** 🟡 bahan mentah untuk PPT — belum disetujui builder (LB25). Naskah di sini USULAN.

**Ringkas:** Bahan untuk deck dan naskah Demo Day (3 menit presentasi + 2 menit tanya jawab, 31 Okt 2026). Strateginya bukan bersaing di arena kompetitor (dampak sosial: BagiPanen/Kulaya; eksekusi mainnet: SAMA/Kawal), melainkan **memindahkan arena**: Fabius diposisikan sebagai lapisan yang tidak dimiliki finalis mana pun — **bukti kapan sebuah keputusan AI dibuat**. Testnet tidak ditutupi; ia dijadikan tesis ("Mainnet tanpa bukti itu Cannae"). Semua kalimat wajib lolos [[10-Submissions/01 - Claims Cheat Sheet]].

**Poin kunci:**
- Kalimat inti: **"Semua agen di ruangan ini bilang AI-nya dibatasi. Fabius satu-satunya yang bisa menjawab *kapan* AI-nya memutuskan — dengan nomor blok."** (ucapkan "di antara finalis", bukan "di dunia").
- Persona + angka nyata: investor kripto Indonesia **22,69 juta per Juni 2026 (OJK)**; Satgas PASTI menghentikan **228 entitas PAKD ilegal Jan–Mei 2026**.
- Testnet = prinsip, bukan kekurangan: saklar `config/uang_nyata.json` `"aktif": false` publik, 0/6 bot lulus F-D16. Opsi penguat (keputusan builder, P179): **"proof on mainnet, money on testnet"**.
- Demo yang bisa dirasakan juri dalam 3 menit: Telegram beli sinyal gasless → link verify → nomor blok sebelum bar tutup → satu revert kontrak (`TooLate`).
- Prasyarat keras: rantai hidup dan `/status` hijau ≥ 24 jam sebelum Demo Day (P173, P174), plus rekaman fallback.

**Detail:**

## 1. Pindah arena: posisi meta

| Finalis | Yang mereka buktikan | Yang tidak bisa mereka buktikan |
|---|---|---|
| Kulaya | AI dibatasi kontrak (4 lapis, red-team) | reputasi AI 100/100 dari n=1, dicatat sesudah hasil |
| BagiPanen | verdict AI masuk kontrak (ERC-8004 #2544) | verdict bisa dikirim kapan saja; tidak terikat waktu terhadap hasil |
| Perago | aksi di dalam batas mandat | rencana dibuat sebelum harga bergerak |
| Kawal | agen bisa dipanggil (probe) | keputusan agen tidak ditulis ulang |
| AgentEco | teks hasil tidak berubah sesudah commit | commit dibuat sebelum hasil diketahui |
| SAMA | settlement benar, non-custodial | usulan AI dibuat sebelum pasar bergerak |
| **Fabius** | **keputusan disegel sebelum hasil ada; strategi dikunci sebelum bar** (`TooLate`, `LockedAfterBar`) | profit / edge (sengaja tidak diklaim) |

Kalimat pembeda per pesaing (tanpa menjelekkan, untuk Q&A):
- Kulaya/BagiPanen: "Mereka membatasi *apa* yang boleh AI lakukan; kami membuktikan *kapan* AI memutuskan. Underwriter AI mana pun butuh keduanya."
- Kawal: "Kawal memeriksa apakah agen bisa dipanggil; kami memeriksa apakah keputusan agen bisa dipercaya waktunya."
- Perago: "Perago membatasi dompet; kami membatasi sejarah."
- SAMA: "SAMA mengurangi biaya trading; kami mengurangi penipuan klaim trading."
- AgentEco: "Escrow memverifikasi hasil kerja sesudahnya; sinyal tidak bisa diverifikasi sesudahnya tanpa bukti waktu."

## 2. Problem tiga lapis

1. **Manusia Indonesia.** 22,69 juta investor kripto (OJK, Juni 2026). Satgas PASTI menghentikan 228 entitas PAKD ilegal Jan–Mei 2026; modus lewat Telegram/WhatsApp/TikTok. Senjatanya: **screenshot profit yang ditulis sesudah pasar bergerak** (antagonis "+312,4 %" video v1).
   Persona USULAN (fiktif, sebut sebagai ilustrasi): *Andi, 24, karyawan di Surabaya, bayar langganan grup sinyal Telegram karena screenshot win rate 90 %; tidak bisa mengecek apakah sinyal kalah dihapus.* Jangan menambah angka tentang Andi yang tidak punya sumber.
2. **Era AI.** LLM bisa menjelaskan apa pun secara hindsight; begitu agen punya dompet (x402) dan identitas (ERC-8004), "sinyal dari agen" berskala mesin — begitu juga penipuan track record.
3. **Ekosistem BNB.** Data publik submission Kawal: registry ERC-8004 di BSC 328.000+ agen, **0,036 feedback per agen**, **62,8 %** registrasi terbaru = template. Reputasi berbasis rating gampang dipalsukan; reputasi berbasis keputusan yang disegel sebelum hasil tidak. (Sebut sumbernya: submission Kawal.)

## 3. Solusi dalam tiga kata kerja (satu slide)

**Kunci → Segel → Periksa.**
- Kunci: spec strategi tiap bot di-hash dan dikunci di `LockRegistry`; dikunci sesudah bar = tidak boleh commit (`LockedAfterBar`).
- Segel: sinyal tiap bar jadi satu Merkle root di `SignalAnchor` sebelum hasil; telat = revert (`TooLate`, maks 12 j); termasuk keputusan untuk *tidak* bertindak.
- Periksa: siapa pun, tanpa kunci dan tanpa gas: `/verify`, `python -X utf8 -m engine.cli ledger verify`, `python -X utf8 tools/verify_signals.py`, MCP.
- AI-nya dibatasi: analis LLM ber-ERC-8004 hanya memilih bot; **formula terkunci** (`tools/meja_slot.py` r4) yang menghitung posisi; root siklus wajib masuk `DeskAnchor` dalam 300 d.

## 4. Testnet sebagai tesis (jangan ditutupi)

Kenapa tidak ditutupi: juri teknis membuka BscScan dan melihat chain 97; produk Fabius adalah kejujuran yang bisa diperiksa — sekali ketahuan menutupi, tesisnya runtuh; claims cheat sheet melarang menyebut "mainnet" untuk testnet.

Naskah USULAN:
> "Fabius Maximus menang karena menolak bertempur sebelum medannya memihak. Roma kalah di Cannae karena ingin bertempur. Kami menolak uang sungguhan sampai bot kami lulus uji maju: 20 sinyal, 20 hari, 2 bulan, interval kepercayaan di atas nol. Hari ini 0 dari 6 lulus. Saklar uang nyata kami publik — `aktif: false`. Proyek lain masuk mainnet karena *bisa*. Kami belum, karena *belum terbukti layak* — dan kami bisa membuktikan bahwa kami belum terbukti. **Mainnet tanpa bukti itu Cannae.**"

Penguat (keputusan builder, P179 / LB24): deploy **lapisan bukti** ke mainnet (biaya [[10-Submissions/05 - Estimasi Biaya Mainnet]]), uang (x402 FAB) tetap testnet. Jawaban "kenapa testnet?" menjadi: *"Bukti kami di mainnet. Uangnya sengaja belum — itu aturan kami."* Submission terkunci 7 Okt dengan kontrak testnet; perlakuan juri atas perubahan pasca-deadline tidak dipublikasikan.

## 5. Dampak: siapa yang tertolong
1. Pembeli sinyal: membedakan rekam asli dari karangan — gratis, tanpa wallet, satu klik.
2. Pembuat bot jujur yang kecil: membuktikan rekam tanpa brand/follower (gerbang G1–G11 sama untuk semua).
3. Ekonomi agen: agen yang membeli dari agen lain (MCP/x402) butuh bukti yang dibaca mesin, bukan rating.
4. Regulator/platform: jejak audit yang tak bisa diubah (sebut sebagai arah, bukan kerja sama).

Slide kejujuran (tidak ada finalis lain yang memublikasikan kegagalan sendiri dengan angka):
- "6 bot kami, 0 lulus uji maju; 4 ditolak gerbang kami sendiri."
- "Aturan arah kami rugi di 12 dari 12 simbol — dipublikasikan." (`vault/06-Results/04 - Negative Results.md`)
- "Sharpe B2-RS 1,29 kami koreksi sendiri jadi 0,85." ([[00-Overview/05 - Corrections]], 2 Okt)
- "False-positive gerbang ±1 % dari anggaran 5 %."

## 6. Bisnis (satu baris di slide, detail untuk Q&A)
- Sekarang: x402 per sinyal (0,01 FAB, pembeli tanpa gas), MCP berbayar.
- Dibangun, belum deploy: 60/40 untuk publisher (`RevenueSplitter`, bagian Fabius hanya bisa turun).
- Arah: API verifikasi untuk platform copy-trading / grup sinyal ("terverifikasi Fabius") — roadmap.
- Kalimat: "Kami tidak mengambil bagian dari profit — itu wilayah regulasi, sengaja dihindari. Kami menjual bukti waktu."

## 7. Naskah 3 menit (180 d) — USULAN

> **29 Okt:** deck diringkas menjadi **6 slide** (DK1–DK6, 387 kata, ±2:55) dengan panduan per slide di [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]]; itu **menggantikan** tabel di bawah dan kerangka 8 slide di §9 (keduanya disimpan sebagai riwayat). Keputusan builder 29 Okt: tetap testnet (opsi P179 di §4 tidak dipakai), format bebas.

| Waktu | Slide | Isi | Live / rekaman |
|---|---|---|---|
| 0:00–0:15 | 1 Hook | Screenshot +312 %. "Pertanyaannya cuma satu: *kapan* ini ditulis?" | — |
| 0:15–0:40 | 2 Problem | Andi + 22,69 juta investor + 228 entitas ilegal; AI memperparah | — |
| 0:40–1:00 | 3 Solusi | Kunci → Segel → Periksa | — |
| 1:00–1:45 | 4 Demo | Telegram: beli sinyal B1 gasless → link verify → "commit blok X, sebelum bar tutup, SAH" | klip rekaman 40 d (aman) atau live |
| 1:45–2:05 | 5 Coba patahkan | commit terlambat → `TooLate` revert (BscScan) | klip 15 d |
| 2:05–2:30 | 6 Kejujuran + testnet | 0/6, 12/12 rugi, saklar `false` → "Mainnet tanpa bukti itu Cannae" | — |
| 2:30–2:50 | 7 Posisi | "Semua agen di ruangan ini bilang AI-nya dibatasi. Tanya mereka: *kapan* AI-nya memutuskan?" + bisnis satu baris | — |
| 2:50–3:00 | 8 Tutup | "Refuse the battle. Prove the decision." + QR ke `/verify` | — |

Desk AI (jailbreak satu analis → formula tetap membatasi) **tidak muat** di 3 menit; simpan untuk Q&A.

## 8. Tanya jawab 2 menit — jawaban ≤ 20 detik

| Pertanyaan | Jawaban |
|---|---|
| "Tanpa edge, apa yang dijual?" | "Kemampuan memeriksa. Produk kami yang mengatakan kami belum punya edge — pasar sinyal lain tidak bisa mengatakan itu dengan jujur." |
| "Sudah ada pengguna?" | "Belum ada pembeli luar. Jalurnya hidup dan bisa dicoba sekarang." Jangan mengarang. |
| "Bisa commit 100 varian lalu reveal yang menang?" | "Satu commit per bot per bar, `n` sinyal tercatat, spec dikunci sebelum bar, reveal maks `n`, `markMissed` sesudah jendela." |
| "Committer terpusat?" | Akui; kunci pernah dirotasi saat bocor (F-D82); arah multisig/timelock. |
| "Kenapa tidak timestamp server?" | "Server bisa diubah operatornya — termasuk kami. Kontrak tidak." |
| "Kenapa testnet?" | Naskah §4 (satu kalimat versi pendek). |
| "Jailbreak analis AI?" | "AI hanya memilih bot; formula terkunci menghitung posisi; root siklus wajib di chain dalam 300 detik." |
| "Legal?" | "Uang nyata dan penjualan berbayar menunggu review hukum (P75/P80) — sengaja, ada di aturan kami." |
| "Beda dengan Kawal/Perago/…?" | Kalimat pembeda §1. |

## 9. Kerangka deck (8 slide untuk 3 menit) — riwayat, diganti 6 slide 29 Okt
1. Hook: screenshot profit + "kapan ini ditulis?"
2. Problem: 22,69 juta · 228 entitas ilegal · AI hindsight
3. Kunci → Segel → Periksa (diagram 3 langkah, nama kontrak kecil)
4. Demo Telegram → verify (klip)
5. Coba patahkan: `TooLate` (klip + tx)
6. Dibangun untuk diragukan: 0/6 · 12/12 · koreksi Sharpe · saklar `false` · Cannae
7. "Mereka membatasi *apa*. Kami membuktikan *kapan*." (tabel ringkas §1, tanpa nama kompetitor di slide — nama hanya di Q&A)
8. Tutup + QR `/verify` + identitas ERC-8004 + kontrak

## 10. Jangan diucapkan
"profitable", "edge", "win rate X %" tanpa n, "used by other agents", "trustless validation", "mainnet" untuk sesuatu yang testnet, "first BNB-native…". Satu klaim berlebihan yang terbongkar menghapus kredibilitas yang dijual Fabius. Lihat [[10-Submissions/01 - Claims Cheat Sheet]].

## 11. Sumber eksternal (bukan perintah repo)
- 22,69 juta investor kripto (OJK, Juni 2026): https://market.bisnis.com/read/20260810/94/1995826/investor-kripto-tembus-2269-juta-pemahaman-risiko-kian-genting
- 21 juta (April 2026, OJK): https://www.investortrust.id/market/107702/investor-kripto-ri-tembus-21-juta-ojk-fokus-perkuat-literasi-dan-tata-kelola
- Satgas PASTI, penipuan berkedok trading kripto: https://investortrust.id/financial/95296/satgas-pasti-bongkar-dugaan-penipuan-berkedok-trading-kripto-dan-periklanan-digital
- OJK SP Satgas PASTI (Appeninc, VID, Sensenowai): https://www.ojk.go.id/id/berita-dan-kegiatan/info-terkini/Documents/Pages/Satgas-PASTI-Hentikan-Kegiatan-Penipuan-Appeninc%2c-VID%2c-dan-Sensenowai/Satgas%20PASTI%20Hentikan%20Kegiatan%20Penipuan%20Appeninc%2c%20VID%2c%20dan%20Sensenowai.pdf
- Angka 228 PAKD ilegal Jan–Mei 2026: **terverifikasi 28 Okt** ke siaran pers OJK SP 11/STPASTI/VI/2026 (22 Juni 2026): https://www.ojk.go.id/id/berita-dan-kegiatan/info-terkini/Documents/Pages/Satgas-PASTI-Hentikan-27-Gadai-Swasta-Ilegal-dan-228-Pedagang-Aset-Keuangan-Digital-Ilegal/SP%2011%20-%20Satgas%20PASTI%20Hentikan%2027%20Gadai%20Swasta%20Ilegal%20dan%20228%20Pedagang%20Aset%20Keuangan%20Digital%20Ilegal.pdf — yang dihentikan = pedagang aset keuangan digital ilegal, bukan grup sinyal.
- Angka registry ERC-8004 (328k, 0,036, 62,8 %): submission Kawal *(workspace)* `../Competitors/07-Kawal/page/page.txt`.

**Terkait:** [[10-Submissions/05 - Estimasi Biaya Mainnet]] · [[12-Competitors/KP9 - Ranking dan Skenario Finalis]] · [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]] · [[08-Backlog/13 - Langkah Builder Tertunda]]

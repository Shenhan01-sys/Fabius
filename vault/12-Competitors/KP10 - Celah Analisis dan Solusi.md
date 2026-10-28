---
tags: [kompetitor, "KP10"]
---

# KP10 - Celah Analisis dan Solusi

**Bagian dari:** [[12-Competitors/00 - Hub Kompetitor]] · baseline: [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]]
**Sumber:** tinjauan diri atas KP0–KP9 + [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] (28 Okt 2026), atas permintaan builder: *"coba judge hasil analisismu sendiri"*; info bocoran top-15 dari builder 28 Okt (§1).

**Ringkas:** Daftar 16 celah dalam analisis kompetitor dan materi pitch Fabius, masing-masing dengan solusi optimal, pemilik (asisten / builder), dan prioritas sebelum Demo Day 31 Okt. Celah ini **bukan** kesalahan produk Fabius; ini lubang dalam *persiapan* yang bisa membuat analisis atau pitch meleset. Tiga yang paling menentukan: alur demo belum diuji tangan, penyebab `cannot fork()` belum diketahui, dan angka pitch belum dicetak ulang.

**Poin kunci:**
- Prioritas 1 (hari ini): #1 uji tangan alur demo, #2 selidiki `cannot fork()`, #3 konfirmasi track finalis (sebagian terjawab oleh info bocoran §1).
- Prioritas 2 (29 Okt): #5 cetak ulang angka, #6–#7 Q&A tambahan, #9 kasus nyata + verifikasi angka OJK, #11 kesiapan teknis mainnet.
- Prioritas 3 (30 Okt): #10 cek ulang kompetitor, #12 nilai video v2, #16 bangun PPT, gladi 3 menit.
- Backlog dibuka: P180–P185; langkah builder LB26–LB27.

**Detail:**

## 1. Info baru dari builder (28 Okt): bocoran top-15

- Top-15 = 5 AI Agents + 5 Consumer Apps + 5 Finance & Commerce. Kelima proyek Finance **tidak masuk top-10 finalis**.
- Konsekuensi (logika builder, disetujui analis): hadiah track Finance akan diisi dari 10 finalis yang ikut track Finance → terjadi pengocokan ulang yang **memperbesar peluang Fabius dan Lencana berada di track berbeda**.
- Peserta Finance di antara 10 finalis: Kulaya, BagiPanen, SAMA, AgentEco, Kawal, Matura, Tagei, **Fabius**. Perago dan Lencana tidak ikut Finance.
- Arah yang disepakati: **Fabius → AI Agents, Lencana → Consumer Apps.** Finance menjadi peluang tambahan Fabius (framing "payment rail untuk agen", satu kalimat, bukan fokus pitch).
- Status: bocoran tidak resmi; tidak dikutip di materi publik.

## 2. Celah dan solusi

| # | Celah | Kenapa penting | Solusi optimal | Pemilik | Prio |
|---|---|---|---|---|---|
| 1 | Alur demo belum diuji tangan (UX dinilai dari struktur rute/deck/video) | Demo 3 menit bergantung pada alur Telegram → `/verify`; satu langkah macet = naskah runtuh | Asisten: uji halaman tanpa login di browser (landing, `/verify` bar terakhir B1, `/bot/B1-TREND`, `/status`, `/mcp`), catat setiap langkah macet + waktu klik. Builder: rekam alur Telegram (`/buy` → bayar gasless → link verify) karena butuh akun Telegram/Privy. Hasil → daftar perbaikan + klip 40 d | asisten + builder | 1 |
| 2 | Penyebab `cannot fork()` di `fabius-engine` dan `fabius-probe` belum diselidiki (`tools/operator_loop.py:78`, `git fetch`) | Menyalakan Railway tanpa perbaikan bisa mengulang kegagalan di hari H | Baca kode loop: cari subprocess `git` tanpa `timeout`/tanpa reap, thread/handle yang bocor, sparse clone yang menumpuk. Uji lokal dengan menghitung proses anak per putaran. Perbaikan kandidat: `subprocess.run(..., timeout=...)` + bersihkan worktree tiap putaran, atau ganti `git fetch` dengan API GitHub; tambah restart policy + log jumlah proses per putaran | asisten (kode) + builder (deploy) | 1 |
| 3 | Track finalis Fabius belum pasti | Pitch harus diarahkan ke satu track | Sebagian terjawab §1 (AI Agents). Builder konfirmasi lewat Telegram/Luma panitia; naskah dikunci ke framing AI Agents, Finance satu kalimat | builder | 1 |
| 4 | Profil juri belum diriset | Penekanan pitch tergantung siapa yang menilai | Cari nama juri (Luma/Telegram panitia). Peta: BNB Chain → standar ekosistem (ERC-8004, x402, BAS, mainnet); Binance Academy → literasi/keamanan pengguna; Coinvestasi → investor ritel Indonesia; Dev Web3 Jogja → kedalaman teknis. Slide netral; tekanan disesuaikan di Q&A | builder (info) + asisten (peta jawaban) | 2 |
| 5 | Angka pitch (0/6, 22 commit, 743 test, ±1 % FP) bertanggal 6–7 Okt; ledger gap sejak 13 Okt | Konvensi vault: angka dicetak ulang hari dikutip; angka basi bisa dibantah juri | Sesudah P173/P174 beres, jalankan pada H-1: `python -X utf8 -m engine.cli ledger verify`, `python -X utf8 -m engine.cli ledger fd16`, `python -X utf8 tools/verify_signals.py`, `python -X utf8 tools/test_census.py --wajib-semua`, `forge test`; tabel angka → perintah → keluaran → tanggal di halaman pitch; slide menyebut "per 30 Okt" | asisten | 2 |
| 6 | Q&A belum menjawab "kenapa tidak EAS/BAS?" (Lencana memakai BAS) | Pertanyaan teknis yang wajar dari juri BNB | Jawaban: atestasi umum mencatat *siapa* dan *apa*, tidak menegakkan urutan terhadap hasil. `SignalAnchor` menegakkan `TooLate` (maks 12 j sesudah bar tutup), `LockedAfterBar` (spec dikunci sebelum bar), satu commit per bot per bar dengan `n` tetap, reveal ≤ `n`, `markMissed`. Itu aturan pasar sinyal, bukan sekadar stempel waktu | asisten | 2 |
| 7 | Q&A belum menutup "commit selektif" (bot tidak commit di hari buruk) | Celah klasik survivorship | Jawaban: hari tanpa tick sebelum batas 12 j ditulis sebagai record `gap` di ledger berantai hash — tidak bisa dihapus, dihitung "tak terukur" bukan nol; reveal yang tak dibuka → `markMissed`. Verifikasi di kode sebelum diucapkan (`engine/ledger.py`, `contracts/SignalAnchor.sol`) | asisten | 2 |
| 8 | Fabius dan Lencana (sama-sama milik builder) bisa saling makan | Dua proyek satu tim di track yang beririsan | Sudah diarahkan §1: Fabius = AI Agents (bukti waktu keputusan agen), Lencana = Consumer (kredensial tanpa wallet). Jangan pakai slogan yang sama di dua pitch; boleh satu benang merah "nothing rewritten quietly" bila juri menyadari timnya sama | builder | 2 |
| 9 | Persona "Andi" fiktif; angka 228 entitas belum dicek ke sumber primer | Kasus nyata lebih kuat; angka salah = kredibilitas runtuh | Cari 1 kasus nyata penipuan grup sinyal/kripto di Indonesia dengan sumber berita/OJK; buka siaran pers OJK Satgas PASTI untuk angka Jan–Mei 2026; bila tak terverifikasi, pakai hanya 22,69 juta (OJK) | asisten | 2 |
| 10 | Kompetitor bisa berubah sebelum 31 Okt (BagiPanen, SAMA masih commit pasca-deadline) | Analisis basi = Q&A pembeda meleset | 30 Okt: ulang cek status HTTP + commit sejak 26 Okt untuk 9 proyek (skrip scrape workspace), perbarui KP terkait bila berubah | asisten | 3 |
| 11 | Kesiapan teknis mainnet belum dicek (baru gas) | Angka $0,4 menyesatkan bila kode belum siap | Audit: alamat hard-coded chain 97 di `tools/` dan `web/src/lib/fabius-chain.ts`, RPC default di `tools/evm.py`, registry ERC-8004 mainnet berbeda, proxy x402 + Permit2 (Permit2 kanonis sama di semua chain; cek proxy x402 di mainnet), `maxLag` berbasis timestamp (aman lintas chain). Keluaran: daftar perubahan konfigurasi + estimasi kerja | asisten | 2 |
| 12 | Video v2 (94,5 d, `render/fabius-pitch-v2.mp4`) belum dinilai | Mungkin lebih cocok untuk Demo Day daripada klip baru | Tonton + nilai dengan kerangka yang sama dengan video kompetitor; potong klip 40 d untuk slide demo bila cocok | asisten + builder (LB21) | 3 |
| 13 | Format Demo Day belum diketahui (online/offline, putar video, internet) | Menentukan demo live vs rekaman | Tanya panitia. Siapkan dua jalur: klip tertanam di PPT (tanpa internet) + tautan live sebagai bonus | builder | 1 |
| 14 | Community Choice ($100, dipilih sesama builder) tidak disentuh | Hadiah tambahan yang bisa dikampanyekan | Unggah klip "coba patahkan" + tautan `/verify` ke grup Telegram builder dan X; ajak builder mencoba mematahkan aturan Fabius | builder | 3 |
| 15 | Ranking tanpa analisis sensitivitas bobot | Posisi Fabius bergantung bobot juri | Tambah tabel: bobot berat inovasi/teknis → Fabius naik; berat dampak/UX → turun; pitch menutup sisi lemah dengan demo konkret | asisten | 3 |
| 16 | PPT belum dibuat (baru bahan + kerangka) | Deliverable akhir | Setelah LB25 (naskah disetujui): bangun 8 slide dari [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] §9, sisipkan klip, gladi dengan timer 3:00 | asisten + builder | 3 |

## 3. Jadwal

| Hari | Pekerjaan |
|---|---|
| 28 Okt | #1 (bagian tanpa login), #2 (analisis kode), #3/#13 (tanya panitia) |
| 29 Okt | P173 + P174 (B4 + Railway), #5, #6, #7, #9, #11 |
| 30 Okt | #10, #12, #16, gladi; #14 kampanye |
| 31 Okt | Demo Day |

**Terkait:** [[12-Competitors/KP9 - Ranking dan Skenario Finalis]] · [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] · [[08-Backlog/01 - Backlog]] · [[08-Backlog/13 - Langkah Builder Tertunda]]

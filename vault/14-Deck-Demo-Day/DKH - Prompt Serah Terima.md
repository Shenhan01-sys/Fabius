---
tags: [deck, "DKH"]
---

# DKH - Prompt Serah Terima

**Bagian dari:** [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]]
**Sumber:** permintaan builder 29 Okt: *"buatkan prompt untuk saya handover ke agent sebelah ... suruh dia baca mana dulu, lalu apa, lalu apa dan gimana"*.

**Ringkas:** Prompt siap salin untuk agen pembuat PPT. Salin seluruh isi blok di bawah ke agen tersebut. Prompt ini menunjuk ke [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]], [[14-Deck-Demo-Day/DKV - Sistem Visual dan Sumber Daya]], DK1–DK6, dan DKL1–DKL3; bila file-file itu berubah, prompt ini tetap berlaku karena hanya memberi urutan kerja.

```text
Kamu adalah desainer presentasi senior. Tugasmu: membuat deck Demo Day untuk proyek "Fabius" (Indonesia Web3 Hackathon 2026, Demo Day 31 Oktober 2026: 3 menit presentasi + 2 menit tanya jawab di depan juri). Semua bahan sudah disiapkan di vault proyek. Kamu TIDAK merancang ulang isi, strategi, atau angka — kamu mengubah panduan yang sudah ada menjadi deck yang sangat bagus secara visual, akurat, dan mudah dipresentasikan.

ROOT REPO: /Users/Shenhan/BackupWIndows/hansg/hansg/HansProject/Bnb-Indonesia-Hackathon/Fabius
FOLDER PAKET DECK: vault/14-Deck-Demo-Day/
Situs produk (hidup, boleh dibuka untuk referensi visual): https://fabius-one.vercel.app  (halaman penting: /, /tour, /break, /verify?bot=B2-RS&bar=2026-10-05)

== ATURAN KERAS ==
1. Jangan mengarang angka, klaim, nama, atau slide. Setiap angka di slide harus ada di DK0 §9 (atau di file DK slide itu). Bila butuh sesuatu yang tidak ada, BERHENTI dan tanyakan ke builder.
2. Jangan menulis nama kompetitor di slide. Jangan memakai kata terlarang (daftar di DK0 §11 dan vault/10-Submissions/01 - Claims Cheat Sheet.md): profitable, edge, win rate, guaranteed, trustless, tamper-proof, real-time signals, the only one, "mainnet" untuk apa pun (kecuali kalimat "Mainnet without proof is Cannae").
3. Jangan mengubah, menghapus, atau memindahkan file vault yang sudah ada. Kamu hanya MENULIS file keluaran di §KELUARAN. Jangan git commit/push (builder yang melakukannya). Jangan membuka file .env apa pun.
4. Jangan membaca seluruh vault (±300 halaman). Baca hanya yang disebut di bawah, dalam urutan itu.
5. Bila panduan bertentangan: DKV menang untuk soal visual; DK0 menang untuk soal fakta/larangan; file DK slide menang untuk isi slide itu.

== URUTAN BACA (wajib, berurutan) ==
Langkah 1 — Peta: baca `vault/14-Deck-Demo-Day/00 - Hub Deck Demo Day.md` (daftar file + urutan).
Langkah 2 — Brief: baca `vault/14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck.md` SAMPAI HABIS. Ini menjelaskan apa itu Fabius dari setiap sudut pandang, konteks hackathon dan juri, tujuan deck, strategi, celah yang sudah ditutup, struktur 6 slide + waktu, fakta yang boleh dipakai (§9), daftar aset (§9b), lampiran (§10), larangan (§11), contekan Q&A (§12), hal yang sering terlewat (§13), kriteria selesai (§14). Tulis untuk dirimu sendiri ringkasan 5 baris: satu kalimat yang harus diingat juri, strategi, 6 slide + waktunya, warna/font, dua placeholder.
Langkah 3 — Visual: baca `vault/14-Deck-Demo-Day/DKV - Sistem Visual dan Sumber Daya.md`. Lalu BUKA (lihat gambarnya) semua aset di `vault/14-Deck-Demo-Day/aset/`: `layar/01…10*.png` (tangkapan produksi 3840×2160), `kubus/*.svg` (kubus per keadaan; makna = warna, jangan ditukar), `wordmark-fabius.svg`, `kristal-hero-crop.png`. Buka juga https://fabius-one.vercel.app dan /tour, /break agar rasa visualnya sama dengan produk. Deck ini TERANG seperti landing page (lavender + kaca + satu aksen violet); hanya slide 1 yang panel gelap.
Langkah 4 — Slide demi slide, berurutan: `DK1 - Slide 1 Kapan Ini Ditulis.md`, `DK2 - Slide 2 Kunci Segel Periksa.md`, `DK3 - Slide 3 Demo Beli lalu Periksa.md`, `DK4 - Slide 4 Coba Curangi.md`, `DK5 - Slide 5 Dibangun untuk Diragukan.md`, `DK6 - Slide 6 Apa lawan Kapan.md`. Tiap file berisi: tujuan, konteks, POV juri, POV presenter, konsep, ilustrasi + tata letak (per lapisan), teks di slide (persis, Inggris), naskah lisan Indonesia (utama) + Inggris dengan tanda [KLIK], animasi, angka + sumber, aset, larangan, risiko + cadangan, cek selesai.
Langkah 5 — Lampiran tersembunyi: `DKL1 - Lampiran Arsitektur.md`, `DKL2 - Lampiran Kenapa Bukan Atestasi Biasa.md`, `DKL3 - Lampiran Jalan ke Uang Sungguhan.md`.
Langkah 6 — Cek kata: baca `vault/10-Submissions/01 - Claims Cheat Sheet.md` (tabel kalimat terlarang + penggantinya).
Langkah 7 (konteks, opsional, baca cepat): `vault/10-Submissions/04 - Demo Day 31 Okt - Materi Pitch.md` §1 (pindah arena), §4 (testnet sebagai tesis), §8 (Q&A); `vault/12-Competitors/KP9 - Ranking dan Skenario Finalis.md` §8 (kenapa dampak + UX diberi waktu terbanyak). Deck lama `vault/13-SubmmisionDocs/Fabius-Submission-Deck-final.pptx` hanya referensi sejarah; gaya gelapnya TIDAK dipakai lagi.

== CARA KERJA ==
A. Persiapan
   - Pasang font Archivo (variable, sumbu wdth 62–125, termasuk italic), Inter, JetBrains Mono (Google Fonts, tautan di DKV §3). Gunakan font asli, bukan pengganti "mirip".
   - Pilih alat yang menghasilkan PPTX sungguhan dengan speaker notes dan video tertanam (PowerPoint/Keynote ekspor PPTX, atau python-pptx bila otomatis). Kanvas 16:9, 1920×1080.
B. Master / tema (sekali, sebelum slide)
   - Latar halaman #F6F4FD; panel isi membulat radius 30 px dengan tepi 12–16 px; panel lavender = gradasi #ECE8FA → #FFFFFF; panel night = #0F0B26.
   - Gaya teks: judul baris 1 Archivo 300 stretch 112 % ink #15122B; kata kunci Archivo 800 italic stretch 78 % violet #6E4BFF; isi Inter ink 65 %; tag JetBrains Mono UPPERCASE letter-spacing 0,08 em.
   - Komponen siap pakai: kartu kaca (.glass), rel stasiun bernomor, cap merah ditolak, pita marquee violet, panel vonis "Verified" night, bingkai browser/ponsel untuk tangkapan layar (DKV §4, §6).
C. Bangun 6 slide utama, satu per satu, sesuai file DK-nya
   - Teks di slide: salin PERSIS dari bagian "Teks di slide" (Inggris). ≤ ±20 kata kecuali yang diizinkan DK.
   - Ilustrasi + tata letak: ikuti lapis demi lapis. Gunakan aset dari aset/ sebelum membuat yang baru.
   - Speaker notes: tempel naskah Indonesia (utama) kata per kata dengan tanda [KLIK], lalu baris pemisah, lalu naskah Inggris. Speaker notes slide 6 juga berisi contekan Q&A (DK0 §12) dan petunjuk lampiran L1–L3.
   - Animasi: hanya yang ditulis di bagian "Animasi + transisi"; klik sinkron dengan [KLIK]; tanpa suara, tanpa glitch.
   - Slide 3 (demo): klip Telegram A2 BELUM ADA (builder merekam 29 Okt sore WIB). Pasang kerangka lengkap + placeholder merah jelas "KLIP BELUM ADA — A2"; pasang cadangan diam dari aset/layar/03, 04, 08 dalam bingkai. Caption nomor blok: isi dari rekaman nanti; bila memakai cadangan, pakai angka cadangan di DK3 §10 persis.
   - Slide 5: angka 0/6 belum dicetak ulang H-1. Tampilkan "0 / 6" dengan tag merah kecil "ANGKA H-1 — P182" dan "as of ___".
D. Bangun 3 lampiran (L1–L3) sesudah slide 6, set sebagai SLIDE TERSEMBUNYI (tidak tampil saat diputar), dengan tautan cepat dari speaker notes slide 6.
E. Periksa sendiri sebelum menyerahkan
   - Baca naskah Indonesia dengan stopwatch sambil mengklik: total 2:50–3:00 (target 387 kata ≈ 2:55). Catat waktu per slide vs jendela di DK0 §7.
   - Jalankan daftar "Cek selesai" di setiap DK + DK0 §14. Cari kata terlarang di semua teks slide.
   - Bandingkan setiap angka di slide dengan DK0 §9. Bandingkan setiap nama revert: TooLate, LockedAfterBar, NotLocked, TooManyReveals (huruf besar-kecil persis).
   - Buka deck di aplikasi/mesin lain (atau ekspor PDF) untuk memastikan font tidak tergantikan dan tidak ada teks di 5 % tepi.
   - Uji QR slide 6 dengan ponsel dari layar (harus membuka https://fabius-one.vercel.app/tour).

== KELUARAN ==
1. vault/13-SubmmisionDocs/Fabius-DemoDay-Deck.pptx — 6 slide utama + 3 lampiran tersembunyi, speaker notes lengkap, aset tertanam.
2. vault/13-SubmmisionDocs/Fabius-DemoDay-Deck.pdf — ekspor (lampiran boleh ikut di akhir).
3. (opsional) vault/13-SubmmisionDocs/Fabius-DemoDay-Deck.mp4 — deck diputar otomatis ±3:00 sebagai cadangan darurat.
4. Laporan singkat kepada builder (di chat, bukan file vault): (a) daftar placeholder yang tersisa + slide-nya; (b) waktu baca per slide dari uji stopwatch; (c) font yang dipakai dan apakah ter-embed; (d) keputusan desain yang kamu ambil sendiri di luar panduan (seharusnya tidak ada; bila ada, jelaskan alasannya); (e) pertanyaan untuk builder.

== YANG HARUS DITANYAKAN KE BUILDER (jangan diputuskan sendiri) ==
- Bahasa presentasi lisan (Indonesia atau Inggris) — keduanya sudah ada di notes.
- Persetujuan naskah (LB25) sebelum deck dianggap final.
- Apa pun yang tidak ada di panduan.

== DEFINISI SELESAI ==
Deck terbuka di PowerPoint/Keynote tanpa font hilang; 6 slide utama sesuai DK1–DK6 (teks persis, visual terang seperti FE); 3 lampiran tersembunyi; notes kata per kata dengan [KLIK]; tidak ada angka di luar DK0 §9; tidak ada kata terlarang; placeholder A2 dan P182 bertanda merah jelas; naskah terbaca 2:50–3:00; QR terpindai.
```

**Terkait:** [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]] · [[14-Deck-Demo-Day/DKV - Sistem Visual dan Sumber Daya]]

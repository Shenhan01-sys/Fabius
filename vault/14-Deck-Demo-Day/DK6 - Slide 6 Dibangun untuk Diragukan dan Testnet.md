---
tags: [deck, "DK6"]
---

# DK6 - Slide 6 Dibangun untuk Diragukan dan Testnet

**Bagian dari:** [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]] · brief: [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]]
**Sumber:** [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] §7 (naskah USULAN, belum disetujui builder - LB25)
**Peta:** sebelumnya [[14-Deck-Demo-Day/DK5 - Slide 5 Coba Patahkan TooLate]] · berikutnya [[14-Deck-Demo-Day/DK7 - Slide 7 Posisi Mereka Membatasi Apa Kami Membuktikan Kapan]]

**Ringkas:** Slide 6 dari 8 · **1:57–2:25 (28 d)**. Mengubah kelemahan (tanpa edge, testnet) menjadi bukti integritas — dan menjawab "kenapa testnet?" sebelum ditanya.

## Teks di slide (Inggris, persis)
- Judul: **"Built to be doubted"**
- Tiga angka:
  - **"0 / 6"** bots passed our forward test (per <tanggal>)
  - **"12 / 12"** symbols lost — published
  - **"1.29 → 0.85"** our own Sharpe, corrected
- Kotak bawah (mono): `uang_nyata.json  "aktif": false`
- Kalimat besar: **"Mainnet without proof is Cannae."**

## Naskah lisan (speaker notes, Bahasa Indonesia)
"Bot kami sendiri? Nol dari enam lulus uji maju kami. Riset awal kami rugi di dua belas dari dua belas simbol — dan kami publikasikan. Sharpe yang tampak bagus, kami koreksi sendiri. Saklar uang nyata kami publik, dan posisinya mati. Fabius Maximus menang karena menolak bertempur sebelum medannya memihak; Roma kalah di Cannae karena ingin bertempur. Kami tidak masuk mainnet dengan uang sungguhan sebelum terbukti layak. **Mainnet tanpa bukti itu Cannae.**"

## Visual dan tata letak
Tiga angka besar sejajar (Archivo, `#ECE8FA`, label kecil `#8B86A6`). Kalimat Cannae besar di bawah dengan aksen `#9D86FF`. Opsional: siluet/ikon helm Romawi sangat halus.

## Angka dan sumber
0/6 — ⚠️ cetak ulang H-1 (`python -X utf8 -m engine.cli ledger fd16`) dan isi "per <tanggal>"; 12/12 — `vault/06-Results/04 - Negative Results.md`; 1,29 → 0,85 — [[00-Overview/05 - Corrections]]. Bila builder memutuskan P179 (lapisan bukti di mainnet) sudah jalan, tambah satu baris: "Proof layer on mainnet · money stays on testnet" — **hanya** bila benar sudah di-deploy.

## Aset
—

## Jangan
Jangan menulis "we have edge soon"; jangan menyebut mainnet bila belum ada.

## Transisi
"Jadi apa yang membuat Fabius berbeda dari setiap agen di ruangan ini?"

**Terkait:** [[14-Deck-Demo-Day/DK5 - Slide 5 Coba Patahkan TooLate]] · [[14-Deck-Demo-Day/DK7 - Slide 7 Posisi Mereka Membatasi Apa Kami Membuktikan Kapan]]

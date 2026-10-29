---
tags: [deck, "DKL3"]
---

# DKL3 - Lampiran Jalan ke Uang Sungguhan

**Bagian dari:** [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]] · brief: [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]] §10 · visual: [[14-Deck-Demo-Day/DKV - Sistem Visual dan Sumber Daya]]
**Sumber:** [[10-Submissions/05 - Estimasi Biaya Mainnet]] · `web/public/data/snapshot.json` (`fd16.required`: 20 sinyal, 20 hari, 2 bulan) · `config/uang_nyata.json` · LockRegistry `FABIUS-FD16-MAJU-v1` (2026-10-02 17:10:57Z) · keputusan builder 29 Okt (tetap testnet)
**Peta:** slide **tersembunyi** sesudah [[14-Deck-Demo-Day/DK6 - Slide 6 Apa lawan Kapan]]; dibuka hanya bila pertanyaan juri cocok, lalu kembali ke DK6.

**Ringkas:** Lampiran untuk "kapan mainnet?", "kapan uang sungguhan?", "berapa biayanya?". Menunjukkan bahwa testnet adalah **aturan yang dikunci**, dengan syarat terukur, dan bahwa biaya bukan penghalang utama.

## 1. Kapan dibuka
Pertanyaan mainnet, uang sungguhan, model bisnis jangka panjang, atau "kenapa belum".

## 2. Ilustrasi + tata letak (panel lavender)
Kiri: tiga "tangki" kaca seperti landing FE (sinyal x/20, hari x/20, bulan x/2) — isi dari angka H-1 (P182). Tengah: kartu night kecil dengan saklar OFF `"aktif": false`. Kanan: kartu biaya kecil.

## 3. Teks di slide (Inggris, persis)
Judul: **Real money waits for proof — by rule.**
- **Forward test (locked on-chain 2 Oct):** 20 signals · 20 days · 2 months · CI above zero — *as of ___: x/20 · x/20 · x/2* (P182)
- **+ legal review** before any paid real-money signal
- **Switch:** `config/uang_nyata.json "aktif": false` — public
- **Cost is not the blocker:** mainnet deploy ≈ $0.4 · operations ≈ $17 / month *(estimate)*

## 4. Jawaban lisan (≤ 20 d)
**ID:** "Uang sungguhan menunggu bukti, dan aturannya kami kunci on-chain sejak 2 Oktober: dua puluh sinyal, dua puluh hari, dua bulan, interval kepercayaan di atas nol, plus telaah hukum. Biaya mainnet kecil — sekitar empat puluh sen untuk deploy. Yang mahal adalah menaruh uang orang sebelum terbukti."
**EN:** "Real money waits for proof, and we locked that rule on-chain on October 2nd: twenty signals, twenty days, two months, confidence above zero, plus legal review. Mainnet itself is cheap — about forty cents to deploy. What's expensive is putting people's money in before it's proven."

## 5. Angka + sumber
Biaya = estimasi @0,05 gwei ([[10-Submissions/05 - Estimasi Biaya Mainnet]]), sebut "estimate". Tangki = cetak ulang H-1 (P182); placeholder merah sampai dicetak.

## 6. Jangan
Jangan menjanjikan tanggal mainnet; jangan "soon"; jangan memakai biaya sebagai alasan utama di slide (alasannya aturan).

**Terkait:** [[14-Deck-Demo-Day/DK6 - Slide 6 Apa lawan Kapan]] · [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]]

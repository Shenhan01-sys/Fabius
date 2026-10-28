---
tags: [deck, "DK3"]
---

# DK3 - Slide 3 Solusi Kunci Segel Periksa

**Bagian dari:** [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]] · brief: [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]]
**Sumber:** [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] §7 (naskah USULAN, belum disetujui builder - LB25)
**Peta:** sebelumnya [[14-Deck-Demo-Day/DK2 - Slide 2 Problem]] · berikutnya [[14-Deck-Demo-Day/DK4 - Slide 4 Demo Telegram ke Verify]]

**Ringkas:** Slide 3 dari 8 · **0:43–1:08 (25 d)**. Menjelaskan mekanisme dalam tiga langkah yang bisa diingat; detail kontrak kecil saja.

## Teks di slide (Inggris, persis)
Tiga kolom/kartu berurutan dengan panah:
1. **LOCK** — "Strategy hashed & locked before the bar" · mono kecil: `LockRegistry` · `LockedAfterBar`
2. **SEAL** — "Every signal committed before the outcome" · mono kecil: `SignalAnchor` · `TooLate (12h)`
3. **CHECK** — "Anyone verifies. No key. No gas." · mono kecil: `/verify` · MCP
Baris bawah kecil: "AI analysts (ERC-8004) pick the bot · a locked formula sizes the position"

## Naskah lisan (speaker notes, Bahasa Indonesia)
"Pertama, **kunci**: strategi tiap bot di-hash dan dikunci on-chain sebelum bar dimulai — dikunci terlambat, ditolak. Kedua, **segel**: setiap sinyal, termasuk keputusan untuk tidak berbuat apa-apa, disegel sebagai Merkle root sebelum hasilnya ada — telat dua belas jam, kontrak menolak. Ketiga, **periksa**: siapa pun bisa memeriksa, tanpa kunci, tanpa gas. Agen AI kami memilih bot, tapi formula yang terkunci yang menghitung posisi."

## Visual dan tata letak
Tiga kartu `#1A1442` dengan garis aksen `#6E4BFF`; panah tipis. Bisa memakai motif kubus/Merkle dari video v1. Nama kontrak dalam JetBrains Mono `#9D86FF` ukuran kecil.

## Angka dan sumber
`TooLate` maks 12 jam, `LockedAfterBar` — `contracts/SignalAnchor.sol:101-104`. ERC-8004 — tokenId 2494 (tidak perlu ditulis).

## Aset
opsional: diagram Merkle dari video v1/v2.

## Jangan
Jangan menulis "tamper-proof" atau "trustless"; gunakan "sealed before the outcome".

## Transisi
"Kami tunjukkan langsung."

**Terkait:** [[14-Deck-Demo-Day/DK2 - Slide 2 Problem]] · [[14-Deck-Demo-Day/DK4 - Slide 4 Demo Telegram ke Verify]]

---
tags: [deck, "DK5"]
---

# DK5 - Slide 5 Coba Patahkan TooLate

**Bagian dari:** [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]] · brief: [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]]
**Sumber:** [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] §7 (naskah USULAN, belum disetujui builder - LB25)
**Peta:** sebelumnya [[14-Deck-Demo-Day/DK4 - Slide 4 Demo Telegram ke Verify]] · berikutnya [[14-Deck-Demo-Day/DK6 - Slide 6 Dibangun untuk Diragukan dan Testnet]]

**Ringkas:** Slide 5 dari 8 · **1:40–1:57 (17 d)**. Menunjukkan aturan ditegakkan kontrak, bukan janji: commit yang terlambat ditolak di chain.

## Teks di slide (Inggris, persis)
- Klip/tangkapan terminal: panggilan `commit(...)` dengan bar lama → **`revert TooLate`**
- Judul: **"Try to cheat: commit after the fact"**
- Baris kecil: "Rejected by the contract — not by us"

## Naskah lisan (speaker notes, Bahasa Indonesia)
"Misalkan kami ingin curang: menulis sinyal sesudah tahu hasilnya. Kami kirim commit untuk bar kemarin yang sudah lewat dua belas jam. Kontrak menolak: **TooLate**. Bukan kami yang menolak — kontraknya. Hal yang sama untuk strategi yang dikunci sesudah bar: LockedAfterBar."

## Visual dan tata letak
Latar gelap, blok terminal (JetBrains Mono) dengan baris revert disorot `#FF5A6E`. Opsional: ikon gembok.

## Angka dan sumber
Nama revert persis: `TooLate(asof, nowTs, maxLag)` dan `LockedAfterBar(lockedAt, asof)` — `contracts/SignalAnchor.sol:69-71`.

## Aset
A4 (tersedia 28 Okt, P178): rekam layar `https://fabius-one.vercel.app/break` -> "Try all four" -> empat kartu "Rejected by the contract" `TooLate` / `LockedAfterBar` / `NotLocked` / `TooManyReveals` (simulasi eth_call ke kontrak sungguhan, label di layar: "Simulation (eth_call) at block #…"). Cadangan: simulasi `cast call` (tanpa broadcast) ke `SignalAnchor 0x9B78200beFbbBe836585d31bd5b6dB32587064f3` chain 97, atau keluaran `forge test` untuk tes `TooLate` (`test/SignalAnchor.t.sol:148`). Tandai di slide bila memakai uji lokal: "local test".

## Jangan
Jangan menyebut simulasi sebagai transaksi nyata; bila klip dari `forge test`, labeli "contract test".

## Transisi
"Dan kami memperlakukan diri sendiri sama kerasnya."

**Terkait:** [[14-Deck-Demo-Day/DK4 - Slide 4 Demo Telegram ke Verify]] · [[14-Deck-Demo-Day/DK6 - Slide 6 Dibangun untuk Diragukan dan Testnet]]

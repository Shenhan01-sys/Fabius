---
tags: [deck, "DKL2"]
---

# DKL2 - Lampiran Kenapa Bukan Atestasi Biasa

**Bagian dari:** [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]] · brief: [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]] §10 · visual: [[14-Deck-Demo-Day/DKV - Sistem Visual dan Sumber Daya]]
**Sumber:** [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] §8 · `contracts/SignalAnchor.sol` (`commit`, `reveal`, `markMissed`) · KP10 #6
**Peta:** slide **tersembunyi** sesudah [[14-Deck-Demo-Day/DK6 - Slide 6 Apa lawan Kapan]]; dibuka hanya bila pertanyaan juri cocok, lalu kembali ke DK6.

**Ringkas:** Lampiran untuk "kenapa tidak pakai EAS/BAS saja?" (finalis lain, termasuk Lencana milik builder, memakai BAS). Inti: atestasi mencatat *siapa* dan *apa*; Fabius menegakkan *urutan terhadap hasil*.

## 1. Kapan dibuka
Pertanyaan EAS/BAS/atestasi/"kenapa bikin kontrak sendiri".

## 2. Ilustrasi + tata letak (panel lavender)
Tabel kaca dua kolom, 4 baris; kolom Fabius ditandai kubus sealed kecil.

## 3. Teks di slide (Inggris, persis)
Judul: **Attestation records *who* and *what*. Fabius enforces *when*.**

| | General attestation | Fabius `SignalAnchor` |
|---|---|---|
| Too late after the outcome | accepted | **rejected** — `TooLate` (12 h) |
| Strategy changed / locked late | not checked | **rejected** — `NotLocked` / `LockedAfterBar` |
| Extra "winning" signal later | can be added | **rejected** — count fixed, `TooManyReveals` |
| Unopened calls | silent | `markMissed` — public miss |

## 4. Jawaban lisan (≤ 20 d)
**ID:** "Atestasi bagus untuk mencatat siapa dan apa. Tapi ia tidak menolak catatan yang datang sesudah hasilnya. Kontrak kami menegakkan urutan: telat ditolak, strategi harus terkunci, jumlah sinyal tetap, dan yang tidak dibuka jadi catatan publik."
**EN:** "Attestations are great for who and what. They don't refuse a record that arrives after the outcome. Our contract enforces order: late is rejected, the strategy must be locked, the count is fixed, and unopened calls become a public miss."

## 5. Jangan
Jangan menjelekkan EAS/BAS atau Lencana; jangan menyebut nama finalis.

**Terkait:** [[14-Deck-Demo-Day/DK6 - Slide 6 Apa lawan Kapan]] · [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]]

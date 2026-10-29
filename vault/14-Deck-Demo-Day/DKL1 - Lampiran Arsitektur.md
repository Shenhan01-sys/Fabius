---
tags: [deck, "DKL1"]
---

# DKL1 - Lampiran Arsitektur

**Bagian dari:** [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]] · brief: [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]] §10 · visual: [[14-Deck-Demo-Day/DKV - Sistem Visual dan Sumber Daya]]
**Sumber:** [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]] §1 · `docs/design/landing.md` · `.github/workflows/paper-ledger.yml` · `tools/railway_up.py` · [[02-Contracts/00 - Hub Contracts]]
**Peta:** slide **tersembunyi** sesudah [[14-Deck-Demo-Day/DK6 - Slide 6 Apa lawan Kapan]]; dibuka hanya bila pertanyaan juri cocok, lalu kembali ke DK6.

**Ringkas:** Lampiran tersembunyi untuk pertanyaan "bagaimana arsitekturnya?", "di mana AI-nya?", "apa yang terpusat?". Satu diagram alur dari keputusan sampai pemeriksaan, tanpa angka baru.

## 1. Kapan dibuka
Pertanyaan tentang arsitektur, peran AI, sentralisasi, atau "apa yang jalan di server kalian".

## 2. POV audiens + presenter
Juri teknis ingin melihat batas: apa di chain, apa di server, apa yang bisa diperiksa tanpa percaya. Presenter menunjuk diagram dari kiri ke kanan, ≤ 20 detik, lalu kembali ke DK6.

## 3. Ilustrasi + tata letak (panel lavender, DKV §7)
Tiga kolom disambung rel stasiun:
1. **Keputusan (off-chain, publik):** "Bots (6, spec locked)" → "AI desk: ERC-8004 analysts pick · locked formula sizes (5 min)" → "Public hash-chained ledger (GitHub Actions)".
2. **Bukti (BNB Smart Chain testnet 97)** — kotak kaca dengan kubus sealed: `LockRegistry` (rules) · `SignalAnchor` (seal + open, 12 h) · `DeskAnchor` (desk root ≤ 300 s) · `SelectionAnchor` (analyst picks) · ERC-8004 identity #2494.
3. **Akses (siapa pun):** `/verify` · `/tour` · `/break` · MCP · Telegram bot · x402 pay-per-signal (test token).
Pita bawah mono kecil: "Centralized today: one committer key (no admin on the contracts — it can only stop sealing, publicly)".

## 4. Teks di slide (Inggris, persis)
Seperti §3; judul: **How Fabius is built** · sub: *Decide in public. Seal on-chain. Anyone checks.*

## 5. Jawaban lisan (≤ 20 d)
**ID:** "Keputusan dibuat terbuka: bot dengan strategi terkunci, dipilih meja AI, ditulis ke ledger publik. Lalu disegel di BNB Chain — empat kontrak kami sendiri, tanpa admin. Siapa pun memeriksa lewat web, Telegram, atau MCP. Yang masih terpusat: satu kunci committer; kontraknya tidak memberi kunci itu kuasa menulis ulang."
**EN:** "Decisions are made in public: locked bots, picked by an AI desk, written to a public ledger. Then sealed on BNB Chain — four contracts of our own, no admin. Anyone checks via web, Telegram or MCP. What's still centralized: one committer key — and the contracts give it no power to rewrite."

## 6. Jangan
Jangan menulis "decentralized" atau "trustless"; jangan menambah angka pengguna/volume.

**Terkait:** [[14-Deck-Demo-Day/DK6 - Slide 6 Apa lawan Kapan]] · [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]]

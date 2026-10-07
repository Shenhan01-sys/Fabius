---
tags: [backlog, builder]
---

# 13 - Langkah Builder Tertunda (yang tidak bisa dikerjakan asisten)

**Bagian dari:** [[08-Backlog/00 - Hub Backlog]]
**Dibuka:** 7 Okt 2026 atas permintaan builder: *"kerjakan yg bisa aja, yg gabisa tolong dicatat di vault agar saya tidak lupa"*. Aturan: [[Conventions]] *Alur kerja pengembangan* langkah 5.
**Sumber:** sesi pengembangan 7 Okt ([[09-Inbox/Session-2026-10-02]] §140 dst.).

**Ringkasan:** satu tempat untuk langkah yang butuh tangan, kunci, atau kata builder: deploy, transaksi, rahasia, uji di produksi, keputusan. Tiap baris menyebut item backlog, alasan asisten tidak bisa, dan perintah persisnya. Baris yang sudah dikerjakan TIDAK dihapus: ditandai ✅ dengan tanggal dan buktinya.

**Kenapa ada:** lingkungan sesi asisten 7 Okt adalah container cloud tanpa rahasia; Railway, Vercel, xkiro, dan host unduhan solc ditolak proxy (CONNECT 403, terukur 7 Okt). Langkah semacam itu dulu tersebar di epik masing-masing (mis. [[08-Backlog/10 - Epik Eksekusi Venue]] §9, [[08-Backlog/11 - Epik Meja AI v2]] §11) dan mudah terlupa.

## Tabel

| ID | item | langkah builder | kenapa asisten tidak bisa | perintah / tempat | status |
|---|---|---|---|---|---|
| LB1 | umum | kata push + deploy untuk hasil sesi 7 Okt (gerbang `fabius-x402` lewat `tools/railway_up.py`, web Vercel) | tidak ada token Railway / Vercel; host ditolak proxy | `python -X utf8 tools/railway_up.py` (dari mesin builder) | ⬜ |

(Baris per item P81 / P90 / P156 / P167 / P168 ditambahkan saat audit sesi 7 Okt selesai.)

**Terkait:** [[08-Backlog/01 - Backlog]] · [[Conventions]] · [[09-Inbox/Session-2026-10-02]] §140

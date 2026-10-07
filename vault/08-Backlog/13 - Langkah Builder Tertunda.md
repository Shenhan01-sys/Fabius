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
| LB2 | P81 | deploy `BotRegistry` (memasang implementasi `RevenueSplitter` sendiri) ke chain 97: pemilik = alamat Fabius, `LockRegistry` yang sudah ter-deploy, anchorer = committer M3, dompet Fabius, bagian Fabius awal 4000 bps | butuh kunci deployer + tBNB + kata builder (deploy kontrak = keputusan builder) | `script/DeployBotRegistry.s.sol` (`forge script ... --rpc-url bscTestnet --broadcast`); lalu catat alamat di [[02-Contracts/02 - Deployed on 97]] + `deployments/97.json` | ⬜ |
| LB3 | P81 | setujui / tolak butir USULAN (a)-(g): salt mengikat penerbit + dompet + spesifikasi, `deploySplitter` tanpa izin, tabel transisi, aturan pin laporan, tarif turun tanpa checkpoint (selisih <= 1 wei), `releaseIssuer` / `releaseFabius` terpisah, dompet Fabius bisa diganti | keputusan desain milik builder | [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] §8, [[02-Contracts/C9 - BotRegistry]], [[02-Contracts/C10 - RevenueSplitter]] | ⬜ |
| LB4 | P81 | sesudah LB2: gerbang x402 menawarkan `payTo` = klon bot (`engine/splitter.py` menghitung alamatnya) + perkakas operator register / transisi + label pin laporan | butuh alamat registry yang ter-deploy | (kerja asisten sesudah LB2) | ⬜ |
| LB5 | P168 | izin biaya + jalankan kalibrasi peninjau LLM terhadap model sungguhan (42 panggilan berbayar: 8 kasus bot x 3 + 6 kasus agent x 3; builder baru mengizinkan satu panggilan < $0,01), lalu commit + push berkas hasil; peninjau baru aktif sesudah berkas itu ada di repo | kunci `XKIRO_API_KEY` hanya di Railway; xkiro / Railway ditolak proxy | `railway run --service fabius-x402 python -X utf8 tools/peninjau_llm.py kalibrasi --jenis bot` lalu `--jenis agent` -> `ledger/peninjau/kalibrasi/<UTC>-<jenis>.json` (keluar 0 = lulus) | ⬜ |
| LB6 | P168 | setujui / tolak butir USULAN epik 12 §10 (a)-(g): bot ditahan tetap berjalan jam bayangannya, aturan paksa LANJUT -> TAHAN, satu pagar ```` ```json ```` ditoleransi, parameter panggilan (`max_tokens` 32768, suhu 0,2, maks 3 percobaan, maks 30 panggilan / hari, 24 jawaban agent disampel), blok masukan `attribution`, laporan agent diringkas selama tunda 24 jam, kunci tinjauan per masa uji | keputusan desain milik builder | [[08-Backlog/12 - Epik Pengajuan Terbuka dan Peninjau LLM]] §10 · [[04-Tools/TL40 - peninjau LLM]] | ⬜ |

(Baris per item P81 / P90 / P156 / P167 / P168 ditambahkan saat audit sesi 7 Okt selesai.)

**Terkait:** [[08-Backlog/01 - Backlog]] · [[Conventions]] · [[09-Inbox/Session-2026-10-02]] §140

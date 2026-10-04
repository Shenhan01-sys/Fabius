---
tags: [perkakas, "TL31", confidence, x402]
---

# TL31 - teaser confidence (gratis, sebelum bayar)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `engine/confidence.py` (`teaser`, `teasers`) · `tools/web_snapshot.py::confidence_block` -> `web/public/data/snapshot.json` `confidence` ·
web `/bot/[id]` bagian uji maju (`BotView.tsx::Fd16`, copy `bot.fd16.conf*`) · MCP `fabius_confidence` (`web/src/lib/mcp-tools.ts`) · tes
`engine/tests/test_confidence.py` (5) · T8 SK-C1..SK-C3 · keputusan [[00-Overview/03 - Decisions]] F-D98 #4, F-D99 · backlog P137

**Definisi (tidak ada angka baru):** confidence = 1 - p, dengan p = p satu sisi bootstrap blok F-D16 yang dikunci 3 Okt (H0: rerata net harian maju
<= 0) atas settle maju final bot itu. Artinya "seberapa yakin rekam jejak maju bahwa bot ini untung sesudah ongkos" - **bukan** peluang sinyal hari
ini benar. BH F-D16 dinilai lintas semua bot berjam maju (satu keluarga, F-D95).

**Tiga keadaan:** < 2 hari settle = tidak ada angka ("belum terukur"); di bawah ambang F-D16 (20 sinyal, 20 hari, 2 bulan) = angka berlabel "awal -
belum bermakna"; ambang tercapai = "terukur". Selalu bersama kematangan x/ambang, status (INTI/SEMENTARA), vonis gerbang v1, vonis F-D16.

**Tidak pernah ada di teaser:** aset, arah, bobot, ukuran, jumlah posisi, id sinyal (diuji: target + ukuran dimasukkan ke tick, tidak satu pun bocor).

**Kenapa hanya teaser (F-D99):** B1-B6 deterministik dan terbuka; isi sinyal bisa dihitung ulang siapa pun dari kode + data publik, jadi x402 (P138)
menjual pengiriman sinyal siap pakai + bukti, bukan rahasia. Rahasia sungguhan hanya untuk sinyal LLM (P139).

**Data 5 Okt:** keenam bot "belum terukur" (B1 0 hari settle, B3 1). Angka pertama muncul sesudah 2 hari settle maju (menunggu berkas funding
bulanan untuk settle final, F-D76).

**Terkait:** [[TL30 - validasi ERC-8004]] · [[08-Backlog/06 - Epik Gerbang Sinyal]]

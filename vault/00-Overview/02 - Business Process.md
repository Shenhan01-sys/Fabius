---
tags: [overview, "O2"]
---

# 02 - Business Process

> **BN-PIVOT - 2 Okt 2026.** Arah proyek bergeser: Fabius menjadi **operator pemilih bot** yang kelak menjual **sinyal
> berbukti** dan membuka slot bot untuk penerbit luar ([[00-Overview/03 - Decisions]] F-D70 dan F-D71). Halaman ini
> menggambarkan keadaan **sebelum** pivot dan tetap benar untuk apa yang **sudah dibangun**; arah baru masih **usulan dan kode
> awal** ([[08-Backlog/05 - Epik Enam Bot]], [[08-Backlog/06 - Epik Gerbang Sinyal]], [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]]).
> Jangan memakai halaman ini untuk menyangkal arah baru, dan jangan menyebut arah baru sebagai fitur yang sudah ada.

**Bagian dari:** [[00-Overview/00 - Hub Overview]]
**Sumber:** `tools/x402_gate.py`, `tools/x402_client.py`, `docs/agent-card.json`,
`05-Ecosystem/02 - x402 Payment.md`

**Ringkas:** Fabius menjual **bukti yang bisa diperiksa**, bukan sinyal. Ada dua permukaan: agen
lain membayar per permintaan lewat x402 untuk mendapat ringkasan keputusan + statistik; manusia
biasa membuka satu halaman untuk menilai satu token sebelum ia mengirim uang ke sana. Uang tidak
pernah mampir ke custody kami — tidak ada deposit, tidak ada penarikan.

**Poin kunci:**
- Pelanggan 1 (agen): `GET /vault/latest` → `402` + `accepts[]` → bayar 1.000 atomic (0,001) →
  dapat isi + `PAYMENT-RESPONSE`. Satu pembayaran nyata sudah terjadi di 97 (tx `0xb6093e59…`).
- Pelanggan 2 (manusia): "surat keputusan untuk token X" — honeypot 2 sumber, kedalaman riwayat,
  likuiditas vs ukuran keluar, dan **apakah kami menolak menilai**. Baris terakhir itu yang tidak
  berani ditulis alat lain, dan bisa dibuktikan karena ter-anchor.
- Bayar-per-keputusan, **gratis saat abstain**: insentifnya sejalan — kami dihukum kalau asal bunyi.
- Skema "yang datang lebih awal dapat untung lebih besar" **kami tolak desainnya**: tidak ada
  sumber kas, jadi imbal hasil peserta awal cuma transfer dari peserta belakangan. Kurva harga
  boleh di sisi biaya (pembeli awal bayar lebih murah), tidak di sisi imbal hasil.
- Revenue split on-chain (pola `bps hanya boleh turun`) sudah ada di proyek lain kami sebagai bukti
  konsep; untuk Fabius belum di-deploy — jangan ditulis seolah punya.

**Detail:**
- Yang belum: hosting endpoint publik ([[05-Ecosystem/03 - Discovery Gap]]), halaman FE
  ([[08-Backlog/01 - Backlog]] P3), dan bukti bahwa ada agen **asing** yang membeli (sampai sekarang
  pembelinya program kami sendiri — dan itu yang boleh diklaim).
- Semua settlement testnet; token pembayaran koin demo milik sendiri.

**Terkait:** [[00-Overview/01 - Briefing]] · [[10-Submissions/01 - Claims Cheat Sheet]]

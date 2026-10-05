---
tags: [perkakas, "TL34", meja, llm, desk]
---

# TL34 - meja AI 5 menit (DeskAnchor)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Rencana v2 (F-D110):** [[08-Backlog/11 - Epik Meja AI v2]] - tiga agent memilih bot dominan dari data luas, rumus terkunci, loop evaluasi (P153-P157).
**Sumber:** kontrak `contracts/DeskAnchor.sol` (+ `test/DeskAnchor.t.sol`, 5 tes) · deploy `tools/deploy_desk_anchor.py` · meja `tools/meja.py`
(`pasar`, `prompt`, `parse`, `konsensus`, `isi`, `siklus`, `root_of`, `proof_of`) · loop + endpoint `/desk`, `/desk/proof/<hash>` + Telegram `/desk` di
`tools/x402_sinyal.py` · web `/desk` (`web/src/components/desk/DeskView.tsx`) · MCP `fabius_desk` · tes `engine/tests/test_meja.py` (6) · T8
SK-M1..SK-M3 · keputusan [[00-Overview/03 - Decisions]] F-D109 · backlog P152

## Apa

Tiap batas 5 menit UTC (+8 s supaya candle tutup), gerbang menjalankan satu siklus: data Binance USDⓈ-M (candle 5 menit yang SUDAH tutup, 4 jam
terakhir, + funding) -> ketiga agent rumah memutuskan paralel dalam format baku (target per aset + keyakinan + alasan, ringkasan wajib) -> harga
mark diambil SESUDAH semua jawaban -> buku per agent + buku konsensus diisi (fee 0,05 % per sisi) -> setiap rekaman di-hash -> Merkle root dikomit
ke DeskAnchor selama siklus berjalan. Volume: `/data/meja/rekaman/<tgl>.jsonl`, `/data/meja/siklus/<tgl>.jsonl`, `/data/meja/buku.json`.

## Buku konsensus (v1) - kenapa transaksi dan PnL-nya beda dari agent

Tiap agent punya buku paper sendiri (modal 10.000 USDT) yang mengikuti targetnya sendiri. Buku konsensus adalah buku keempat: targetnya = rata-rata
(keyakinan x target) atas agent yang menjawab sah (kuorum 2), lalu diisi dengan aturan yang sama (fee 0,05 % per sisi, perubahan < 2 % ekuitas tidak
ditransaksikan). Rata-rata mengecilkan dan meratakan posisi, jadi banyak perubahan agent jatuh di bawah ambang 2 % -> transaksinya lebih sedikit dan
PnL-nya berbeda dari tiap agent. Dicetak 5 Okt ±14:2xZ dari `/desk`: konsensus 13 transaksi / ekuitas 10.005,95; DeepSeek 19 / 10.005,92; Qwen 26 /
10.017,70; berita 4 / 9.996,33. Agent berita (Qwen 3.8 Omni Flash) status `ok` di semua siklus tetapi memilih datar sampai 14:10Z dengan alasan gerak
5 menit di bawah ambang biaya pulang-pergi 0,10 %; transaksi pertamanya 14:10Z (4 isi).

**v2 (F-D112) berjalan di siklus yang sama:** [[04-Tools/TL36 - meja v2 bot + instrumen]]; rekamannya ikut root yang sama.

## Lantai trading 3D (P158)

Bagian "Decisions, newest first" diganti diorama isometrik: tiap agent = NPC kotak-kotak (gaya Minecraft) di meja kerja dengan monitor (kurva
ekuitas 24 jam) + keyboard, hub Fabius di tengah (putusan v2, atau konsensus v1 bila v2 belum ada), menara 12 blok BNB Chain (12 siklus terakhir,
menyala = dikomit), garis cahaya violet meja -> hub -> menara. Kontrak desain: `docs/design/desk.md` (ditulis sebelum kode). Kode:
`web/src/components/desk/floor/` (`model.ts` keadaan NPC dari rekaman terakhir, `Scene.tsx` adegan R3F, `bridge.ts` label DOM yang mengikuti
titik jangkar 3D, `AgentModal.tsx` modal yang keluar dari kotak layar monitor, `Floor.tsx` lapisan inklusif). Data modal: `GET /desk/agent/<nama>`
(`Gate.meja_agent`: statistik terukur 24 jam + riwayat keputusan terbaru dulu dengan isi, harga, fee, tautan bukti Merkle); `/desk` menambah
`siklus_12`, `isi_terakhir`, `siklus_terakhir` per buku.

Keadaan NPC (bukan dikarang): `✕ gagal` bila rekaman terakhir gagal/terlambat · `… berpikir` bila >= 5 menit sejak siklus terakhir tercatat ·
`⇄ bertransaksi` bila isi > 0 · `■ menahan` bila masih berposisi · `■ datar` bila tanpa posisi. Inklusif: arti selalu bentuk + kata, pita
keterangan `aria-live`, label = tombol DOM yang bisa difokus, "Lihat sebagai daftar", daftar otomatis tanpa WebGL, tanpa gerak bila
`prefers-reduced-motion`, label ringkas di bawah 640 px, kanvas berhenti render di luar layar / saat modal terbuka.

## Cara memeriksa satu keputusan

`GET /desk/proof/<hash>` -> rekaman, hash dihitung ulang (sha256 JSON kanonis tanpa `hash`), Merkle proof (`engine/chain.py`) -> root =
`DeskAnchor.rootOf(siklus)`, tx komit. Kontrak menolak root sesudah `siklus + 300`, jadi keputusan tidak bisa ditulis sesudah harga penentunya ada.

## Batas yang dicatat jujur

Paper; isi pada harga mark (tanpa slippage buku order). Rumus v1 = bobot agent sama (belum memakai rekam jejak). Model `:free` xkiro bisa kena batas;
agent gagal = rekaman `gagal`, konsensus dari yang sah (kuorum 2). Gas komit ±0,011 tBNB/hari pada 1 gwei (builder mengisi faucet).

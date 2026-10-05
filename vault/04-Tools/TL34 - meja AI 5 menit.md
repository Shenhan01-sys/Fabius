---
tags: [perkakas, "TL34", meja, llm, desk]
---

# TL34 - meja AI 5 menit (DeskAnchor)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** kontrak `contracts/DeskAnchor.sol` (+ `test/DeskAnchor.t.sol`, 5 tes) · deploy `tools/deploy_desk_anchor.py` · meja `tools/meja.py`
(`pasar`, `prompt`, `parse`, `konsensus`, `isi`, `siklus`, `root_of`, `proof_of`) · loop + endpoint `/desk`, `/desk/proof/<hash>` + Telegram `/desk` di
`tools/x402_sinyal.py` · web `/desk` (`web/src/components/desk/DeskView.tsx`) · MCP `fabius_desk` · tes `engine/tests/test_meja.py` (6) · T8
SK-M1..SK-M3 · keputusan [[00-Overview/03 - Decisions]] F-D109 · backlog P152

## Apa

Tiap batas 5 menit UTC (+8 s supaya candle tutup), gerbang menjalankan satu siklus: data Binance USDⓈ-M (candle 5 menit yang SUDAH tutup, 4 jam
terakhir, + funding) -> ketiga agent rumah memutuskan paralel dalam format baku (target per aset + keyakinan + alasan, ringkasan wajib) -> harga
mark diambil SESUDAH semua jawaban -> buku per agent + buku konsensus diisi (fee 0,05 % per sisi) -> setiap rekaman di-hash -> Merkle root dikomit
ke DeskAnchor selama siklus berjalan. Volume: `/data/meja/rekaman/<tgl>.jsonl`, `/data/meja/siklus/<tgl>.jsonl`, `/data/meja/buku.json`.

## Cara memeriksa satu keputusan

`GET /desk/proof/<hash>` -> rekaman, hash dihitung ulang (sha256 JSON kanonis tanpa `hash`), Merkle proof (`engine/chain.py`) -> root =
`DeskAnchor.rootOf(siklus)`, tx komit. Kontrak menolak root sesudah `siklus + 300`, jadi keputusan tidak bisa ditulis sesudah harga penentunya ada.

## Batas yang dicatat jujur

Paper; isi pada harga mark (tanpa slippage buku order). Rumus v1 = bobot agent sama (belum memakai rekam jejak). Model `:free` xkiro bisa kena batas;
agent gagal = rekaman `gagal`, konsensus dari yang sah (kuorum 2). Gas komit ±0,011 tBNB/hari pada 1 gwei (builder mengisi faucet).

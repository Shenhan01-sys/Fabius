---
tags: [perkakas, "TL32", x402, fab]
---

# TL32 - gerbang x402 per sinyal (FAB, testnet 97)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/x402_sinyal.py` (`Gate`, `check_payment`, `paid_in_receipt`, `tg_link`/`tg_parse`, `telegram_loop`) · `engine/harga.py` + kunci
`engine/locks/harga.lock.json` · kontrak `contracts/FabiusCredit.sol` (+ `test/FabiusCredit.t.sol`, profil `fork`) · `deployments/97.json` ->
`x402_sinyal` · service Railway `fabius-x402` (`FABIUS_JOB=x402_sinyal`) · MCP `fabius_signal_offer` · tes `engine/tests/test_x402_sinyal.py` (12) ·
T8 SK-X1..SK-X6 · keputusan [[00-Overview/03 - Decisions]] F-D99, F-D100 · backlog P138a-d

**Publik:** `https://fabius-x402-production.up.railway.app` - `GET /` (token, payTo, harga tiap bot, status kunci harga), `GET /teaser/<bot>`
(gratis), `GET /sinyal/<bot>[/<bar>]` (x402 v2 `exact`, Permit2 + `eip2612GasSponsoring`, pembeli nol gas), `POST /faucet` (FAB dikirim gerbang).

**Token:** Fabius Credit · FAB `0xc7b6d5cdbdc881daae0dbcc095d4f184b70ec881` (6 desimal, `faucet()` publik, EIP-2612; domain EIP-712 "Fabius
Credit"/"1"), deploy 5 Okt tx `0xee1cf8f5…` blok 134.886.695 oleh fasilitator `0x10c41a996Bab4042867c2dD388937A1e2743f1b1` (kunci baru,
`.x402.env` di-gitignore + variabel Railway lewat `--stdin`; diisi 0,05 tBNB dari committer tx `0x24cbc520…`). Suplai awal 1.000.000 FAB = cadangan
faucet relay.

**Harga (F-D100, terkunci `0x4db311ff…` 5 Okt 20:27Z):** per (bot, bar) dari teaser confidence yang dihitung dari ledger SAMPAI tick bar itu
(beku, bisa dihitung ulang): belum terukur / awal / terukur < 60 % = 0,01 FAB; 60-75 % = 0,05; 75-90 % = 0,25; >= 90 % DAN F-D16 LOLOS = 1,00.

**Pemeriksaan bayar:** token, jumlah, `witness.to` = payTo, spender = proxy/Permit2 kanonis, pemilik sama, deadline - pada otorisasi yang
DITANDATANGANI (gate lama `x402_gate.py` hanya mencocokkan `accepted` dari klien); `eth_call` dulu; sesudah tx, log Transfer(pembeli -> payTo, tepat
harga) harus ada di receipt. Kunci tx (satu nonce) dilindungi kunci thread.

**Bukti 5 Okt:** (1) lokal: faucet relay 0,5 FAB ke pembeli tanpa tBNB (tx `0x3e87b752…`), beli B1-TREND bar 10-03 0,01 FAB tx `0x20d82816…`
(saldo pembeli 500.000 -> 490.000 atomic); (2) PUBLIK lewat Railway: beli B3-CARRY 0,01 FAB tx `0x2c1097f1…` (490.000 -> 480.000). Paket berisi
target, signal_ids, commitId, status komit/ungkap, validasi ERC-8004. Ditemukan saat uji publik: edge Railway menulis header huruf kecil;
`x402_client.py` mencari header peka-huruf -> diperbaiki (SK-X6).

**Yang belum:** halaman web `/beli/<bot>` (P138c), bot Telegram (P138d; kode polling + tautan bertanda sudah ada, menunggu token bot dari builder).
Pembeli eksternal: nol - satu-satunya pembeli sejauh ini klien kami sendiri.

**Terkait:** [[TL6 - x402 gate and client]] · [[TL31 - teaser confidence]] · [[05-Ecosystem/02 - x402 Payment]]

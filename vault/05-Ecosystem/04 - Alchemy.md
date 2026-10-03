---
tags: [ekosistem, penyedia, rpc]
---

# 04 - Alchemy (dinilai 4 Okt 2026)

**Bagian dari:** [[05-Ecosystem/00 - Hub BNB Ecosystem]]
**Sumber (dibaca 4 Okt):** alchemy.com/docs (beranda, chains, data, build-with-ai, pricing-plans; halaman `reference/wallets` membalas 404) + indeks
`docs/{chains,wallets,data}/llms.txt`, `reference/node-supported-chains.md`, `wallets/supported-chains.md`, halaman `eth_getLogs` BNB.

**Ringkas:** relevan untuk SATU hal sekarang (RPC chain 97 cadangan untuk jalur yang tidak memindai log) dan untuk SATU hal nanti (dompet pintar +
sponsor gas di BNB untuk pembeli tingkat 1). Sisanya sudah kita punya, atau tidak dibutuhkan.

| bagian | fakta terbaca | untuk Fabius |
|---|---|---|
| RPC | BNB mainnet `https://bnb-mainnet.g.alchemy.com/v2/API_KEY`, **testnet `https://bnb-testnet.g.alchemy.com/v2/API_KEY`**, opBNB | cadangan RPC chain 97 untuk worker komit/ungkap (`eth_call`, kirim tx) - publicnode pernah 403 tanpa User-Agent |
| Paket | gratis: 30 juta CU/bulan, 300 CU/s, 5 app; PAYG $0,525 per juta CU, 10.000 CU/s | gratis cukup untuk worker (beberapa panggilan per 5 menit) |
| `eth_getLogs` | **gratis: 10 blok per kueri** (BNB termasuk); PAYG: tak terbatas | TIDAK cocok untuk `verify_signals`, MCP `fabius_verify`, kertas (memindai ribuan blok sejak deploy 134442917) - tetap publicnode |
| Dompet (Wallet APIs) | BNB mainnet + testnet: bundler, sponsor gas, bayar gas dengan ERC20 | NANTI: pembeli tingkat 1 tanpa tBNB/BNB (x402 + sponsor gas); tidak dibutuhkan sebelum F-D16 + telaah hukum |
| Data API | Portfolio, Token, Transfers, Prices (real-time + historis), NFT, Webhooks, Simulation; daftar chain tidak menyebut BNB secara eksplisit | tidak dibutuhkan: harga dari Binance Vision/REST (sumber yang sama dengan venue); webhook pada event `Revealed` = calon pemicu pengiriman tingkat 1, dukungan BNB belum terbukti |
| AI | MCP server (`claude mcp add alchemy --transport http https://mcp.alchemy.com/mcp`, 159 alat), skills `alchemyplatform/skills`, CLI `@alchemy/cli`; x402 untuk agen dengan USDC di Base/Solana | alat bantu pengembang saja; MCP Fabius sendiri sudah hidup (P114); x402 Alchemy bukan BNB |

**Rekomendasi (usulan, belum dikerjakan):** bila builder mau, buat app gratis Alchemy (BNB testnet) dan pasang URL-nya sebagai `RPC_URL` cadangan di
Railway `fabius-engine` (variabel, bukan repo: URL memuat kunci API). Jalur pemindai log tetap publicnode. Tidak ada perubahan lain.

**Terkait:** [[08-Backlog/10 - Epik Eksekusi Venue]] · [[08-Backlog/06 - Epik Gerbang Sinyal]] · [[04-Tools/TL20 - server MCP]]

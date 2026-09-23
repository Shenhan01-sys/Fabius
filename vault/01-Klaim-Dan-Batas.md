# 01 — Klaim dan batas

Daftar ini mengikat. Ia ditulis supaya tidak ada yang (kita atau model) mengarang kalimat yang
tidak bisa ditunjuk artefaknya.

## Boleh diucapkan, dengan artefaknya

| Klaim | Buktinya | Level |
|---|---|---|
| "Setiap keputusan agen di-anchor sebagai hash di BNB Chain, dengan event yang bisa di-indeks" | `contracts/DecisionAnchor.sol` + 21 test `forge test` | dihitung/diuji lokal |
| "Penolakan dicatat sebagai hasil: ABSTAIN wajib membawa hash log gerbang" | ditegakkan kontrak (`AbstainWithoutReason`), ada test-nya | diuji |
| "Kewenangan agen bisa dicabut on-chain dan setelah itu panggilannya revert" | `setAgentActive` + test `test_agen_yang_dicabut_tidak_lagi_bisa_mencatat` | diuji |
| "Universe BSC direkam point-in-time, tiap snapshot di-hash, hash-nya dirantai lewat manifest git" | `universe/bsc-universe.jsonl` + `universe/write_universe_manifest.py` (32/32 sha256 cocok) | terukur |
| "Mayoritas kandidat hot di BSC tidak bisa diperdagangkan secara jujur" | screener: umur/likuiditas/bundler/top-10; **136 token** punya hasil forward | dihitung dari dataset sendiri |
| "Jalur settlement x402 berfungsi di chain 97 dan 56, termasuk pembayaran tanpa gas oleh klien" | `_research/x402-bnb-poc/` — 31 test (15 unit + 8 fork 97 + 8 fork 56) vs Permit2 & proxy yang nyata ter-deploy | fork test |
| "Registry ERC-8004 (Identity, Reputation) hidup di 97 dan 56" | `verify_erc8004.py` — `eth_chainId` + `eth_getCode` + `eth_call` | probe chain |
| "Funding rate & open interest BNB tersedia tanpa API key" | Hyperliquid `metaAndAssetCtxs`: 234 perp, BNB OI 65.047, funding 0,004781%/jam | probe HTTP |

## Dilarang diucapkan

- **Angka apa pun yang berbentuk keuntungan**: return, ROI, win rate, "alpha", proyeksi profit,
  hasil backtest yang dipajang tanpa biaya dan tanpa OOS. Bukan karena jelek — karena tidak bisa
  dipertahankan di jendela ini.
- **"Agen kami trading live"** atau menyebut venue eksekusi sebagai fakta. Tidak ada order yang
  pernah dikirim.
- **"trustless validation"**, "zkML-verified", "TEE-verified", "verifiable inference",
  "AI kami tidak bisa curang". `ValidationRegistry` tidak ada di chain mana pun, dan lima
  kandidat bukti inferensi sudah diuji: semuanya gugur.
- **"terintegrasi dengan BNB Agent Studio"** sebelum halaman/product docs-nya dibaca primer dari
  browser. Yang terverifikasi baru **SDK** (`bnbagent`, MIT) dan **Agent Studio terdokumentasi**
  untuk scaffolding/agent faces (A2A/MCP/x402) — itu bukan integrasi produk.
- **"x402 adalah fitur resmi BNB Chain yang kami pakai"** — BSC absen dari tabel `DEFAULT_ASSETS`
  x402 Foundation (26 jaringan, tanpa `eip155:56`/`97`) dan dari `constants.ts` (23 nama, tanpa
  `bsc`). Framing yang benar: **kami menyambungkan dua ekosistem yang belum tersambung**, dan itu
  justru kerjanya.
- **"agen kami punya reputasi on-chain"**. Yang ada: identitas terdaftar + jejak keputusan
  ter-anchor. Permukaan baca `ReputationRegistry` bahkan tidak bisa kita temukan (`name()`/
  `symbol()`/`totalSupply()` revert).
- **memakai angka dari catatan lama tanpa menyebut tanggalnya.** Contoh yang sudah terjadi:
  "nol pesaing agentic trading" hanya benar untuk 4 submission hackathon pada 13 Sep; registry
  ERC-8004 hari ini menunjukkan **ratusan ribu agen terdafar di chain 56**.

## Batas yang tidak bisa dihapus oleh riset apa pun

Anchor membuktikan **keberadaan, keutuhan, penanda tangan, urutan waktu**. Ia tidak membuktikan
keputusan itu benar, menguntungkan, atau benar-benar dihasilkan model yang disebutkan. Klaim
"model X menjalankan Y" tidak bisa dibuktikan di chain ini pada 2026, dan kami menuliskan itu
di README, bukan menguburnya.

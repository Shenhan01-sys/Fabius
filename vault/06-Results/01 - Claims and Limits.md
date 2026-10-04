---
tags: [hasil]
---

# 01 — Klaim dan batas

> **BN-PIVOT - 2 Okt 2026.** Arah proyek bergeser: Fabius menjadi **operator pemilih bot** yang kelak menjual **sinyal
> berbukti** dan membuka slot bot untuk penerbit luar ([[00-Overview/03 - Decisions]] F-D70 dan F-D71). Halaman ini
> menggambarkan keadaan **sebelum** pivot dan tetap benar untuk apa yang **sudah dibangun**; arah baru masih **usulan dan kode
> awal** ([[08-Backlog/05 - Epik Enam Bot]], [[08-Backlog/06 - Epik Gerbang Sinyal]], [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]]).
> Jangan memakai halaman ini untuk menyangkal arah baru, dan jangan menyebut arah baru sebagai fitur yang sudah ada.

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
| "Jalur settlement x402 berfungsi di chain 97, termasuk pembayaran tanpa gas oleh klien" | `test/X402SettleOnBsc.fork.t.sol` + `test/X402DemoToken.t.sol` di repo ini — 9 fork + 15 unit lulus 27 Sep vs Permit2 & proxy kanonis yang nyata ter-deploy ([[07-Testing/T4 - x402 Fork Suite]]) | fork test |
| "Registry ERC-8004 (Identity, Reputation) hidup di 97 dan 56" | `verify_erc8004.py` — `eth_chainId` + `eth_getCode` + `eth_call` | probe chain |
| "Funding rate & open interest BNB tersedia tanpa API key" | Hyperliquid `metaAndAssetCtxs`: 234 perp, BNB OI 65.047, funding 0,004781%/jam | probe HTTP |

## Boleh diucapkan sejak 3 Okt (arah operator, terukur)

> Arah operator (BN-PIVOT) kini punya bagian yang SUDAH ADA. Baris di bawah boleh diucapkan; sebut n-nya, karena bukti maju baru berumur hari.

| Klaim | Buktinya | Level |
|---|---|---|
| "Sinyal bot Fabius dikomit ke BNB Chain (SignalAnchor, chain 97) sebelum hasilnya ada, lalu diungkap; siapa pun bisa memeriksanya tanpa kunci" | `python -X utf8 tools/verify_signals.py` 3 Okt 08:44:16Z: B1-TREND + B3-CARRY bar 2026-10-02 SAH, ALARM 0; `fabius_verify` di server MCP produksi = SAH ([[07-Testing/01 - Test Commands]] 5g, 5i) | terukur on-chain, **satu hari bukti** |
| "Ledger paper maju ditulis mesin dan sinyalnya dikomit worker tanpa tangan manusia" | [[09-Inbox/Session-2026-10-02]] §39; `python -X utf8 -m engine.cli ledger verify` | terukur sejak 2 Okt |
| "Umpan bukti tingkat 0 terbuka untuk manusia dan agen (MCP)" | https://fabius-one.vercel.app · `https://fabius-one.vercel.app/mcp` ([[04-Tools/TL20 - server MCP]]) | hidup, diuji di produksi 3 Okt |

**Masih dilarang:** "sinyal kami menguntungkan" / "punya edge" (F-D16 maju belum terpenuhi), "dipakai agen lain" (belum ada bukti pemakai luar),
"punya pelanggan/pendaftar" (sampai ada angkanya), "sinyal real-time tersedia" (tingkat 1 TERKUNCI, F-D72).

## Dilarang diucapkan

- **Angka apa pun yang berbentuk keuntungan**: return, ROI, win rate, "alpha", proyeksi profit,
  hasil backtest yang dipajang tanpa biaya dan tanpa OOS. Bukan karena jelek — karena tidak bisa
  dipertahankan di jendela ini.
- **"Agen kami trading live"** atau menyebut venue eksekusi sebagai fakta. Tidak ada order yang
  pernah dikirim.
- **"trustless validation"**, "zkML-verified", "TEE-verified", "verifiable inference",
  "AI kami tidak bisa curang". `ValidationRegistry` tidak ada di chain mana pun,
  **Koreksi 5 Okt 2026 (dibaca ulang dari chain 97 hari itu):** `ReputationRegistry` `0x8004B663056A597Dffe9eCcC1965A193B7388713` dan `ValidationRegistry` `0x8004Cb1BF31DAf7788923b405b754f57acEB4272` ADA di chain 97 - proxy 130 B, `getVersion()` = "2.0.0", `getIdentityRegistry()` = IdentityRegistry kami `0x8004A818…`, implementasi 10.491 B / 5.876 B; agen 2494: `getClients` = [], `getAgentValidations` = []. Kalimat "tidak ada di chain mana pun" di bawah = keadaan saat ditulis, BASI. dan lima
  kandidat bukti inferensi sudah diuji: semuanya gugur.
- **"terintegrasi dengan BNB Agent Studio"** sebelum halaman/product docs-nya dibaca primer dari
  browser. Yang terverifikasi baru **SDK** (`bnbagent`, MIT) dan **Agent Studio terdokumentasi**
  untuk scaffolding/agent faces (A2A/MCP/x402) — itu bukan integrasi produk.
- **"x402 adalah fitur resmi BNB Chain yang kami pakai"** — BSC absen dari tabel `DEFAULT_ASSETS`
  x402 Foundation (26 jaringan, tanpa `eip155:56`/`97`) dan dari `constants.ts` (23 nama, tanpa
  `bsc`). Framing yang benar: **kami menyambungkan dua ekosistem yang belum tersambung**, dan itu
  justru kerjanya.
- **(5 Okt, P136) Boleh:** "tiap komit Fabius dimintakan validasi di ValidationRegistry ERC-8004 resmi (agen 2494) dan dijawab oleh pemeriksa
  publik yang dijalankan di CI publik" - SETELAH jawaban pertama terbaca di chain. **Tetap tidak boleh:** "trustless validation" / "divalidasi
  pihak ketiga": validatornya kunci kami sendiri di infrastruktur lain ([[04-Tools/TL30 - validasi ERC-8004]]).
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

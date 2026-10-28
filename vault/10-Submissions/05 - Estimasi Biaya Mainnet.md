---
tags: [submission, biaya]
---

# 05 - Estimasi Biaya Mainnet

**Bagian dari:** [[10-Submissions/00 - Hub Submissions]]
**Sumber:** receipt chain 97 (`eth_getTransactionReceipt` lewat `https://data-seed-prebsc-1-s1.bnbchain.org:8545`, hash tx dari `deployments/97.json` dan `broadcast/Deploy.s.sol/97/run-latest.json`), 27 Okt 2026; gas operasional dari [[02-Contracts/C7 - SignalAnchor]] (`forge test --gas-report`, median) dan [[08-Backlog/11 - Epik Meja AI v2]] (desk ±0,011 tBNB/hari pada 1 gwei); harga gas mainnet `eth_gasPrice` `https://bsc-dataseed.bnbchain.org` = **0,05 gwei** dan BNB **$745,20** (Binance `ticker/price BNBUSDT`), keduanya 27 Okt.

**Ringkas:** Berapa biaya memindahkan Fabius ke BSC mainnet, dihitung dari gas yang benar-benar terpakai di testnet (gas sama di kedua jaringan; yang beda hanya harga gas). Kesimpulan: **deploy ±$0,4 dan operasional ±$17/bulan pada 0,05 gwei** — gas bukan penghalang. Biaya terbesar bukan gas, melainkan Railway dan API LLM. Ada satu jebakan: gas settlement x402 ditanggung Fabius per penjualan, sehingga harga sinyal di mainnet harus jauh di atasnya.

**Poin kunci:**
- Deploy inti + lock + registrasi ±10 juta gas ≈ 0,0005 BNB ≈ **$0,38** (0,05 gwei); ±$7,5 pada 1 gwei. Siapkan **0,01–0,02 BNB** termasuk cadangan retry.
- Operasional ±15 juta gas/hari ≈ **$0,56/hari ≈ $17/bulan** (0,05 gwei); $34 (0,1 gwei); $335 (1 gwei). Desk AI (288 commit/hari) = ±73 % dari itu; batch per jam → ±$5/bulan.
- x402: ±115k gas per settlement ditanggung fasilitator ≈ **$0,004** (0,05 gwei) — hampir separuh harga sinyal $0,01.
- Sebelum mainnet: kunci yang membayar gas memegang BNB sungguhan → riwayat kebocoran kunci (F-D82, P147) wajib beres.
- Opsi yang konsisten dengan aturan Fabius: **lapisan bukti di mainnet, uang tetap testnet** (P179) — x402 dengan stablecoin nyata melanggar F-D16 + P75/P80.

**Detail:**

## 1. Gas deploy terukur (receipt chain 97)

| Item | gasUsed | Keterangan |
|---|---|---|
| `LockRegistry` | 337.168 | inti |
| `SignalAnchor` | 1.008.041 | inti |
| `ExecutionAnchor` | 683.065 | inti |
| `SelectionAnchor` | 469.892 | desk/analis |
| `DeskAnchor` | 255.899 | desk |
| `DecisionAnchor` | 1.105.708 | opsional (fase riset) |
| `FabiusCredit` | 1.029.762 | tidak perlu di mainnet bila memakai stablecoin nyata |
| lock spec satu bot | 122.870 | ×6 bot |
| pin `LockRegistry` | 123.086 | ×±4 |
| registrasi ERC-8004 satu agen | 200.844 | ×±10 (Fabius + analis) |
| `BotRegistry` + `RevenueSplitter` | ±3.000.000 *(perkiraan; belum pernah di-broadcast)* | P81 |

Total skenario lengkap (tanpa `FabiusCredit`) ±10 juta gas.

## 2. Gas operasional per hari

| Item | Perhitungan | Gas/hari |
|---|---|---|
| Desk AI `DeskAnchor.commit` | 288 siklus × ±38k (diturunkan dari ±0,011 tBNB/hari @1 gwei) | ±11 juta |
| `SignalAnchor.commit` | 6 bot × ±190k (median EVM lokal 189.848) | ±1,1 juta |
| `reveal` | ±24 sinyal × ±68k (median 67.807) | ±1,6 juta |
| pick analis + validasi ERC-8004 | *(perkiraan, belum diukur di chain)* | ±1 juta |
| **Total** | | **±15 juta** |

Catatan: commit/reveal adalah median EVM lokal (C7: "angka chain menunggu transaksi nyata"); sampling log chain 97 untuk operasional gagal 27 Okt karena batas rentang `eth_getLogs` di RPC publik.

## 3. Biaya

| Harga gas | Deploy (±10 jt) | Operasional/bulan (±15 jt/hari) |
|---|---|---|
| 0,05 gwei (terukur 27 Okt) | ±0,0005 BNB ≈ $0,38 | ±0,0225 BNB ≈ $17 |
| 0,1 gwei | ≈ $0,75 | ≈ $34 |
| 1 gwei (lonjakan) | ≈ $7,5 | ≈ $335 |

Bukan gas: Railway (`fabius-engine`, `fabius-x402`, `fabius-probe` — dimatikan sebagian oleh builder karena usage), API LLM desk (±864 panggilan/hari). GitHub Actions dan Vercel gratis untuk repo publik.

## 4. Jebakan x402
Settlement ±114.930 gas ([[02-Contracts/02 - Deployed on 97]]) dibayar fasilitator (gerbang Fabius). Pada harga sinyal $0,01 → gas ±43 % harga @0,05 gwei, ±86 % @0,1 gwei. Harga per sinyal mainnet harus jauh di atas biaya gas, atau settlement di-batch.

## 5. Prasyarat keamanan
Setiap kunci pembayar gas (committer, desk, validator, fasilitator) memegang BNB nyata. Sebelum mainnet: tuntaskan P147 (kunci Privy lama), audit riwayat kebocoran (F-D82, Not Yet Proven #6), pertimbangkan multisig/timelock untuk peran admin.

**Terkait:** [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] · [[02-Contracts/C7 - SignalAnchor]] · [[08-Backlog/13 - Langkah Builder Tertunda]]

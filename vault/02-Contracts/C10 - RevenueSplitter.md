---
tags: [kontrak, "C10"]
---

# C10 - RevenueSplitter

**Bagian dari:** [[02-Contracts/00 - Hub Contracts]]
**Sumber:** `contracts/RevenueSplitter.sol`, `test/RevenueSplitter.t.sol` (21 test, 5 di antaranya fuzz), rujukan `engine/economics.py` (`split`,
`share_change_allowed`), vektor `test/fixtures/splitter_vectors.json` (`tools/gen_splitter_vectors.py`) · backlog P81 ·
[[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] §8 · [[08-Backlog/06 - Epik Gerbang Sinyal]] §3 C-H
**Peta:** [[02-Contracts/C9 - BotRegistry]] (daftar bot + pabrik splitter) · [[02-Contracts/C10 - RevenueSplitter]] (penerima `payTo` per bot, bagi hasil)

> **STATUS: DITULIS + DIUJI LOKAL (7 Okt 2026), BELUM DI-DEPLOY.** Klon hanya dibuat oleh [[02-Contracts/C9 - BotRegistry]], dan registry itu juga belum
> di-deploy.

**Ringkas:** satu klon EIP-1167 per bot, dan alamatnya menjadi `payTo` x402 untuk sinyal bot itu. Pembeli membayar token ERC-20 ke alamat ini, bahkan sebelum
klonnya dipasang. `release(token)` membagi uang persis seperti `economics.split` (F-D72): penerbit = floor(jumlah × bps / 10000), Fabius = sisanya (debu
pembulatan ke Fabius), dan jumlah keduanya selalu sama dengan masukan. Kontrak ini TIDAK menerima BNB, tidak punya fungsi penarikan selain `release` ke dua
payee, dan tidak tahu status slot bot.

**Poin kunci:**
- Pull: `release(token)`, `releaseIssuer(token)`, dan `releaseFabius(token)` boleh dipanggil siapa pun; uangnya hanya pergi ke `issuerPayee` dan
  `fabiusPayee`. Fungsi per pihak (**USULAN**) ada supaya transfer yang gagal ke satu pihak tidak menahan pihak lain.
- Pembukuan kumulatif per token (pola PaymentSplitter OpenZeppelin): hak penerbit per segmen tarif = floor(total diterima segmen × bps / 10000), dihitung
  dengan `Math.mulDiv` sehingga tidak meluap sampai 2^256-1. Berapa kali pun `release` dipanggil, hasil akhirnya = SATU `economics.split` atas total (fuzz).
- Bagian Fabius hanya boleh turun (`lowerFabiusShare`, galat `ShareMayOnlyDecrease`; nilai yang sama diizinkan, seperti `share_change_allowed`), dan hanya
  oleh Fabius = `registry.owner()` (`NotFabius`). Tidak ada fungsi untuk menaikkannya.
- Payout penerbit hanya bisa diganti `issuer` (`NotIssuer`). Dompet Fabius hanya bisa diganti Fabius (**USULAN**: epik tidak menyebut dompet Fabius). Hak
  yang belum dilepas ikut ke payee baru. Payee nol atau alamat splitter sendiri ditolak (`BadPayee`), karena payee = diri sendiri akan menciptakan
  "pendapatan hantu".
- Tidak ada penyitaan. Diuji: Fabius mengarahkan dompet Fabius ke dirinya sendiri, mencoba mengganti payout penerbit (ditolak), dan mencoba
  menginisialisasi ulang (ditolak); `release` yang dipicu orang luar tetap membayar 600 / 400 dari 1.000.
- Implementasi tidak bisa diinisialisasi atau dipakai (`AlreadyInitialized`, `NotInitialized`). Klon diinisialisasi pabrik pada transaksi yang sama dengan
  pembuatannya.

**Detail:**
- Saat tarif berubah, segmen lama ditutup pada checkpoint terakhir (sebuah `release`, atau token yang dicantumkan di
  `lowerFabiusShare(newBps, checkpointFirst)`). Saldo yang belum di-checkpoint ikut tarif baru, yaitu tarif penerbit yang lebih tinggi (**USULAN**: epik
  hanya menetapkan "bagian Fabius hanya turun"). Karena ada dua floor terpisah, penerbit bisa menerima 1 wei LEBIH SEDIKIT dibanding versi yang
  di-checkpoint. Fuzz menemukannya: a = 22.473, b = 4, c = 24.160, bagian Fabius 3.091 → 30.177 vs 30.178. Uji memastikan selisihnya tidak pernah lebih
  dari 1 wei, dan komentar kontrak menyebut hal ini.
- Vektor lintas bahasa (Python → kontrak): 98 vektor `split` (jumlah 0 .. 2^256-1 × bps 0 .. 10000), 70 vektor `share_change_allowed`, dan 8 skenario
  setor / release / turunkan tarif. Harapan skenario dihitung model segmen yang membagi setiap segmen dengan `economics.split`.
  `python -X utf8 tools/gen_splitter_vectors.py --check` mencetak `bagian Python COCOK dengan engine` dan `vektor evm COCOK dengan prediksi Python`.
- Token aneh:
  - Re-entrancy (token yang masuk lagi ke `release` / `releaseIssuer` / `releaseFabius` saat transfer) ditolak dengan `ReentrancyGuardReentrantCall`;
    tiap pihak dibayar tepat sekali (600 / 401 dari 1.001).
  - Fee-on-transfer: yang dibagi adalah yang TIBA (990 dari 1.000 → 594 / 396); fee keluar ditanggung penerima (diterima 589 / 393); pembukuan tetap
    dilepas == diterima. Ini didokumentasikan, bukan didukung: gerbang x402 menuntut Transfer tepat harga (SK-X1/SK-X2).
  - Saldo yang menyusut sendiri (rebase negatif, penyitaan oleh admin token) memicu `BalanceShrank`: `release` berhenti sampai saldo pulih. Berhenti
    lebih aman daripada membagi uang yang tidak ada.
  - BNB ditolak (tidak ada `receive`). BNB yang dipaksa masuk (selfdestruct) tertahan selamanya.
- Ukuran: runtime implementasi 4.731 B (artefak `out/`). Gas di EVM lokal (`forge test --match-path test/RevenueSplitter.t.sol --gas-report`, median atas
  campuran uji): `initialize` 114.636, `release` 143.629, `lowerFabiusShare` 18.088. Angka chain belum ada.

**Yang TIDAK dibuktikan / belum ada:** deploy; adanya pembeli; harga; kepatuhan pajak / KYC untuk membayar penerbit pihak ketiga (P75/P80); dukungan untuk
token selain ERC-20 polos.

**Terkait:** [[02-Contracts/C9 - BotRegistry]] · [[05-Ecosystem/02 - x402 Payment]] · [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] ·
[[08-Backlog/06 - Epik Gerbang Sinyal]] · [[00-Overview/03 - Decisions]] F-D72

---
tags: [testing, "T4"]
---

# T4 - x402 Fork Suite

**Bagian dari:** [[07-Testing/00 - Hub Testing]]
**Perintah:** `set FOUNDRY_PROFILE=fork&& forge test --fork-url bscTestnet --match-contract X402SettleOnBscForkTest`
**Dijalankan:** 27 Sep 2026 ±03:30 WIB — **9 lulus**, 0 gagal (3,70 s)
**Prasyarat:** profil `fork` (evm cancun + `skip = []`) dan RPC **publicnode** lewat alias
`bscTestnet`. Endpoint yang diwarisi dari POC (`data-seed-prebsc-*`, drpc untuk state per-blok)
**tidak** bisa menjalankan suite ini.

## Keluaran

```text
Ran 9 tests for test/X402SettleOnBsc.fork.t.sol:X402SettleOnBscForkTest
[PASS] test_dump_DigestUntukPembandingPython() (gas: 40830)
[PASS] test_fork_FasilitatorTidakBisaMelebihkanJumlah() (gas: 64067)
[PASS] test_fork_FasilitatorTidakBisaMengubahTujuan() (gas: 99366)
[PASS] test_fork_KontrakTerdeployMemangProxyExactX402() (gas: 20045)
[PASS] test_fork_SettleWithPermit_KlienNolGas() (gas: 139265)
[PASS] test_fork_SettleWithPermit_TolakNilaiTidakCocok() (gas: 38466)
[PASS] test_fork_Settle_JalurApproveLangsung() (gas: 124033)
[PASS] test_fork_TolakNonceDimainkanUlang() (gas: 129565)
[PASS] test_fork_TolakSebelumValidAfter() (gas: 55945)
Suite result: ok. 9 passed; 0 failed; 0 skipped; finished in 3.70s (4.36s CPU time)
```

Token pembayar (unit, tanpa fork): `--match-contract X402DemoTokenTest` → **15 lulus**
(domain EIP-712, expiry, replay, `Permit_RejectsAlteredSpender`, faucet cap).

## Yang dibuktikannya — dan yang tidak

- ✅ Fasilitator **tidak bisa** mengarahkan dana ke `payTo` lain atau melebihkan jumlah, dan nonce
  tidak bisa dipakai ulang — ditegakkan **kontrak kanonis**, bukan server kami.
- ✅ `validAfter` di masa depan ditolak kontrak → itu sebabnya klien memakai `X402_SKEW` 15 s
  (jam laptop kami pernah lebih cepat dari kepala chain → revert tanpa data).
- ✅ `test_dump_DigestUntukPembandingPython` adalah pagar silang: digest yang dihitung Solidity
  dibandingkan dengan hitungan Python kami. Tanpa tes ini, bug "nested tuple" 25 Sep bisa lolos lagi.
- ❌ **Bukan** pembayaran nyata. Yang nyata ada satu: tx `0xb6093e59…` di 97, 1.000 atomic token
  demo, dari klien kami ke payTo kami sendiri (dibaca ulang dari chain: pembeli 5.000.000 →
  4.999.000; `payTo` +1.000.000 −10 +0,001).
- ❌ Bukan pembayaran USDC asli, bukan mainnet, bukan pembeli asing.

## Kalau gagal

- `EvmError: NotActivated` → kamu di profil default (`shanghai`); pakai `FOUNDRY_PROFILE=fork`.
- `Unknown block (code 26)` / HTTP 500 dari drpc → itu RPC-nya, bukan kodenya. Ganti alias.
- Satu test x402 gagal di profil default dengan `mcopy` → memang untuk itu `skip` ada; jangan
  "merapikan" `foundry.toml`.

**Terkait:** [[05-Ecosystem/02 - x402 Payment]] · [[04-Tools/TL6 - x402 gate and client]] ·
[[02-Contracts/C5 - Vendored x402 Sources]]

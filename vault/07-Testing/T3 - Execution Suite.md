---
tags: [testing, "T3"]
---

# T3 - Execution Suite

**Bagian dari:** [[07-Testing/00 - Hub Testing]]
**Perintah:** `forge test --match-contract ExecutionVaultTest`
**Dijalankan:** 27 Sep 2026 ±03:30 WIB (= 26 Sep 20:29Z) — 18 lulus, 0 gagal (juga lulus di profil fork)

## Keluaran

```text
Ran 18 tests for test/ExecutionVault.t.sol:ExecutionVaultTest
[PASS] test_hard_ceiling_memotong_cap_bukan_menolak_diam_diam() (gas: 284544)
[PASS] test_owner_tidak_punya_jalan_pintas_membuka_posisi() (gas: 19784)
[PASS] test_hari_baru_mereset_plafon_sebelum_memeriksanya() (gas: 489164)
[PASS] test_tanpa_hash_keputusan_ditolak() (gas: 28558)
[PASS] test_round_trip_biaya_tetap_terasa_sekitar_dua_kali_fee() (gas: 305140)
Suite result: ok. 18 passed; 0 failed; 0 skipped; finished in 4.34ms (11.41ms CPU time)
```

## Yang dibuktikannya — dan yang tidak

- ✅ **Plafon dipotong, bukan diminta izin.** `setDailyCap(1000)` menghasilkan `dailyCap() == 10`
  (`HARD_CEILING`): pemilik tidak bisa diam-diam membuka rem, bahkan dengan perintah yang tampak sah.
- ✅ **Owner tidak bisa membuka posisi.** Only `agent` → `NotAgent` (teruji dari alamat owner).
- ✅ **Tidak ada posisi tanpa jejak.** `decisionHash`/`snapshotHash` kosong → `NoAnchorHash`;
  `killSwitch` aktif → `KillSwitchOn`; di atas cap → `OverDailyCap`/`OverPositionCap`.
- ✅ **Urutan reset harian.** Plafon di-roll **sebelum** diperiksa — bug urutan nyata, sekarang
  dipajang test tersendiri (`test_hari_baru_mereset_plafon_sebelum_memeriksanya`).
- ✅ **Ongkos, bukan arah:** round-trip di venue demo = **59 bps** untuk posisi 1 unit; dampak
  membesar bersama ukuran (`test_dampak_membesar_dengan_ukuran`).
- ✅ Rugi boleh negatif dan tidak dibersihkan (`test_rugi_boleh_negatif_dan_tidak_dibersihkan`).
- ❌ Semuanya di **local testnet emulation** (`vm`), bukan di 97. Satu posisi nyata belum pernah
  terjadi — itu [[08-Backlog/01 - Backlog]] P1.
- ❌ Bukan bukti kurva x·y=k di sini mewakili slippage meme sungguhan (lihat
  [[02-Contracts/C4 - DemoPair and DemoAsset]]).

## Kalau gagal

- `mcopy` / kompilasi gagal → token uji harus ERC20 polos (`DemoAsset`), bukan OZ+permit; alasannya
  di `02-Contracts/C4`.
- `setVenue` revert di `setUp` → butuh `vm.prank(owner)`; fungsi itu milik owner, bukan agen.
- PnL short terasa salah → ingat: membuka short **menerima** quote. Yang dibandingkan adalah
  `realizedQuote`, bukan saldo vault (kesalahan konsep yang sempat membuat tesku sendiri salah).

**Terkait:** [[02-Contracts/C3 - ExecutionVault]] · [[Concepts/Cost Is Fixed]]

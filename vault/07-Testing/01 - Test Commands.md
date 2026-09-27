---
tags: [testing, "T1"]
---

# T1 - Test Commands

**Bagian dari:** [[07-Testing/00 - Hub Testing]]
**Perintah:** lihat tabel · **Dijalankan:** 2026-09-27, mesin ini (Windows, cmd.exe, solc 0.8.26)
**Prasyarat:** `git submodule update --init --recursive` (vendor/ = OZ + forge-std). Tanpa ini
build gagal — dan itu bukan teori: clone pertama dulu memang tidak bisa build karena `lib/`
berupa junction lokal.

## Registry perintah

| # | perintah | hasil 27 Sep | membuktikan |
|---|---|---|---|
| 1 | `forge test` | **39 lulus** (21 DecisionAnchor + 18 ExecutionVault), 0 gagal | gerbang kontrak + jalur eksekusi, tanpa jaringan |
| 2 | `set FOUNDRY_PROFILE=fork&& forge test --fork-url bscTestnet` | **63 lulus** (21 + 18 + 15 DemoToken + 9 fork x402), 0 gagal | settlement x402 terhadap proxy kanonis **yang benar-benar ter-deploy** di 97 |
| 3 | `set FOUNDRY_PROFILE=fork&& forge test --fork-url bscTestnet --match-contract ExecutionVaultTest` | 18 lulus | angka di baris 2 tidak menyembunyikan apa pun |
| 4 | `python -X utf8 tools/anchor.py --verify` | 11/11 cocok, 0 BEDA, 0 belum di-anchor | trail terbaca ulang dari chain tanpa kunci/gas |
| 5 | `python -X utf8 tools/ledger.py` | 2 posisi jatuh tempo, net −144,8 bps | penilaian dari rekaman, bukan dihitung ulang |
| 6 | `python -X utf8 tools/verify_vendor.py` | 4/4 identik dengan manifest @ commit pin | vendor tidak disunat, **dari dalam clone** |
| 7 | `python -X utf8 vault/scripts/check_links.py` | `Broken: 0` | graf vault terhubung, tidak ada halaman invisible |
| 8 | `python -X utf8 _research/check_garbled.py` *(workspace — di luar clone Fabius)* | 0 CJK/fullwidth/BOM di jalur yang diperiksa | teks masih terbaca di terminal Windows |
| 9 | `python -X utf8 vault/scripts/prepush_check.py --self-test` | 6/6 kasus benar | detektor atribusi masih menangkap polanya |
| 10 | `python -X utf8 vault/scripts/prepush_check.py` — **sebelum setiap push** | `0 commit pada origin/master..HEAD -> lolos` | tidak ada commit yang akan dikirim membawa atribusi AI |

Baris 4–7 dan 9–10 adalah yang bisa dijalankan orang lain tanpa punya apa pun dariku (9–10 cuma
membaca git lokal). Baris 8 dan `_research/*` lain adalah alat workspace: kutulis sebagai bukti cara
kerjaku, bukan sebagai sesuatu yang bisa direproduksi juri dari clone (aturan di [[Conventions]]).

## Keluaran asli (dipotong, tidak dirapikan)

```text
Ran 18 tests for test/ExecutionVault.t.sol:ExecutionVaultTest
Suite result: ok. 18 passed; 0 failed; 0 skipped; finished in 4.34ms (11.41ms CPU time)
Ran 21 tests for test/DecisionAnchor.t.sol:DecisionAnchorTest
Suite result: ok. 21 passed; 0 failed; 0 skipped; finished in 19.29ms (48.81ms CPU time)
Ran 2 test suites in 21.15ms (23.62ms CPU time): 39 tests passed, 0 failed, 0 skipped (39 total tests)
```

```text
Ran 9 tests for test/X402SettleOnBsc.fork.t.sol:X402SettleOnBscForkTest
Suite result: ok. 9 passed; 0 failed; 0 skipped; finished in 3.70s (4.36s CPU time)
Ran 15 tests for test/X402DemoToken.t.sol:X402DemoTokenTest
Suite result: ok. 15 passed; 0 failed; 0 skipped; finished in 3.70s (3.35s CPU time)
Ran 21 tests for test/DecisionAnchor.t.sol:DecisionAnchorTest
Suite result: ok. 21 passed; 0 failed; 0 skipped; finished in 3.70s (2.87s CPU time)
Ran 18 tests for test/ExecutionVault.t.sol:ExecutionVaultTest
Suite result: ok. 18 passed; 0 failed; 0 skipped; finished in 4.11s (3.25s CPU time)
Ran 4 test suites in 4.47s (15.20s CPU time): 63 tests passed, 0 failed, 0 skipped (63 total tests)
```

**Yang dibuktikannya — dan yang tidak.**
- ✅ Kontrak menolak: bukan agen, hash kosong, cap terlampaui, kill switch, posisi ganda, short
  tanpa inventaris, agen yang sudah dicabut.
- ✅ Settlement x402: fasilitator tidak bisa mengubah tujuan/melebihkan jumlah; nonce tidak bisa
  dimain-ulang; `validAfter` ditegakkan.
- ❌ Tidak ada satu pun angka di atas yang mengatakan **agen kami untung**. 39/63 = perilaku
  kontrak, bukan hasil pasar.
- ❌ Baris 9–10 menjaga **atribusi commit**, bukan membuktikan klaim produk: `--all` pada 27 Sep
  menemukan tepat **1** commit bermasalah dari **393** (`08cb049`) dan itu **ditinggalkan secara
  sadar** — menghapusnya berarti menulis ulang 147 hash ([[00-Overview/03 - Decisions]] F-D22).
- ❌ Profil fork memakai `--fork-url bscTestnet` = **publicnode**. Perintah warisan yang menunjuk
  drpc/`data-seed-prebsc-*` tidak bisa menjalankan bukti ini (terukur: `Unknown block`, sertifikat).

## Kalau gagal

- `EvmError: NotActivated` → kamu menjalankan fork di profil default (`evm_version=shanghai`);
  fork wajib `FOUNDRY_PROFILE=fork` (cancun).
- `mcopy` / kompilasi `vendor/openzeppelin/.../Bytes.sol` gagal di shanghai → itu sebabnya
  `skip = ["X402DemoToken","X402SettleOnBsc"]` ada di profil default. Jangan dihapus "biar rapi".
- `Unknown block (code 26)` → RPC fork mati; pakai alias `bscTestnet`, atau
  `python -X utf8 -u _research/find_bsc_testnet_rpc.py` untuk memilih yang hidup sekarang.
- `forge test` jalan tapi `--verify` BEDA → cek dulu `chain_check` (chainId) sebelum menyalahkan
  hash; dan ingat `getAnchor` id tak dikenal **tidak revert**, ia mengembalikan struct nol
  ([[04-Tools/TL4 - anchor and verify]]).

**Terkait:** [[07-Testing/T2 - Anchor Verify]] · [[07-Testing/T3 - Execution Suite]] ·
[[07-Testing/T4 - x402 Fork Suite]] · [[Quick-Reference]]

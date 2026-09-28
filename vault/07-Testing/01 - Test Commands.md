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
| 4 | `python -X utf8 tools/anchor.py --verify` | 28 Sep: **13/13 cocok**, 0 BEDA, 0 belum di-anchor; `anchorCount()` = 19 (peringatan cakupan, P6b) | trail terbaca ulang dari chain tanpa kunci/gas |
| 5 | `python -X utf8 tools/ledger.py` | 28 Sep: **3 posisi jatuh tempo**, net total **−708,1 bps** pada ongkos 59 bps | penilaian dari rekaman, bukan dihitung ulang |
| 6 | `python -X utf8 tools/verify_vendor.py` | 4/4 identik dengan manifest @ commit pin | vendor tidak disunat, **dari dalam clone** |
| 7 | `python -X utf8 vault/scripts/check_links.py` | `Broken: 0` | graf vault terhubung, tidak ada halaman invisible |
| 8 | `python -X utf8 _research/check_garbled.py` *(workspace — di luar clone Fabius)* | 0 CJK/fullwidth/BOM di jalur yang diperiksa | teks masih terbaca di terminal Windows |
| 9 | `python -X utf8 vault/scripts/prepush_check.py --self-test` | 6/6 kasus benar | detektor atribusi masih menangkap polanya |
| 10 | `python -X utf8 vault/scripts/prepush_check.py` — **sebelum setiap push** | 28 Sep: `5 commit diperiksa ... BERSIH` | tidak ada commit yang akan dikirim membawa atribusi AI |
| 11 | `python -X utf8 tools/costs.py --self-test` | 28 Sep: **LOLOS** (59 terukur / 20 diasumsikan / ambang 118) | satu model ongkos, dan 59 masih = dua fee 30 bps berkomposisi |
| 12 | `python -X utf8 universe/record_funding_history.py --report` | 28 Sep: 5.963 baris tersedia (OKX 97,7 hari · Bybit 66,3 · OI 20,8) | histori funding/OI tanpa kunci, satu-satunya jalur uji carry yang kita punya |
| 13 | `python -X utf8 tools/carry_study.py` | 28 Sep: veto kena **0/2.963**; **0 dari 12 uji lolos BH**; carry 1,3–2,2 bps/hari | uji carry yang jujur (median + bootstrap + BH), verdict `NETAS` |
| 14 | `python -X utf8 tools/winlog.py` | 28 Sep: PAPER n=3 WR 0 % (−236,0 rata-rata) · CHAIN n=3 WR 0 % (−59,0) | streak dibaca dua seri terpisah, dan gerbang F-D16 ikut dicetak |
| 15 | `python -X utf8 tools/flow_cluster_test.py --horizon 30 --window 15` | 28 Sep 07:37Z (KANONIK): K=1 median **−59,0** vs K≥2 **+478,6**; berpasangan dalam token yang sama: **K≥2 +393,4 CI [+5; +1012] p=0,0008 lolos BH**, K≥3 +393,4 p=0,0252, K≥5 +2.412 p=0,0018 (kelas bersarang, acuan = K=1); sensor 5.085 tanpa harga masuk + 481 tanpa harga keluar | hipotesis builder diuji, bukan diasumsikan — jawabannya dibatasi sensor, bukan sinyal ([[06-Results/09 - Whale Cluster Test]]) |
| 16 | `python -X utf8 tools/evidence_stack.py` | 28 Sep 07:37Z: lima aspek lulus sendiri, dua tidak, `fresh_token` (+7.708) dibuang sebagai artefak kebijakan pull; tumpukan ≥2 aspek **+481 bps CI [+23; +977]**, "≥2 dompet DAN uang tersebar" **+748,8 CI [+12; +1574]**; hanya **12,7 %** kejadian yang bisa dinilai | compounding yang harus membuktikan dirinya sendiri, bukan mewarisi bukti bagiannya ([[06-Results/10 - Evidence Stack]]) |
| 17 | `python -X utf8 universe/record_watch_prices.py --watch-min 120 --max-batches 8 --report` | 28 Sep: satu siklus menjawab **123 dari 136** token pantau lewat 5 panggilan DexScreener (terukur 200 @401 ms untuk 30 alamat); jendela 2 jam dipilih karena terukur 136 token = 5 panggilan/siklus, vs 927 token = 31 panggilan pada 24 jam | memperlebar sampel yang bisa dinilai (P17); `--self-test` menjaga satuan detik-vs-milidetik dan stempel jam runner |
| 18 | `python -X utf8 tools/prices.py --report` (dan `--self-test`) | 28 Sep: `gmgn` 38.151 baris/1.813 token/43,18 jam (5.355 dilebur), `watch` 123 baris/123 token/**0,00 jam**; cakupan satu-sumber 50,9 % kejadian punya `gmgn`, 0 % `watch`; delta dua sumber belum cukup pasangan | gerbang bentuk (`--self-test`) mengunci dedupe, kedaluwarsa harga, aturan satu-sumber, dan delta sintetis 100 bps |
| 22 | `python -X utf8 tools/policy_test.py` (`--horizon 60`) | 30 m: A **0** · B **+82,7 [+5,0; +159,1]** · C **+162,3 [+80,4; +243,0]** melewati hanya 13,6 % kejadian; D (keluar saat kerumunan beli) **TIDAK DIUJI** | jawaban terukur untuk "apa bedanya dengan tidak trading sama sekali" - dan batasnya (mean ≠ bisa diambil tanpa kedalaman) ([[06-Results/13 - Apakah Tidak Trading Itu Gratis]] §3b) |
| 21 | (workspace) `python -X utf8 tools/mirror_test.py` lalu `python -X utf8 tools/tail_test.py` | 28 Sep ±10:0xZ: baseline P(≥+500 bps) **33,9 %**, mean winso **+82,7 bps**; tidak ada aspek yang menaikkan ekor (BH kosong); `jual_2` menurunkan ke **22,5 %** (p=0,0028) dan `jual_bersih` ke **20,3 %** (p=0,011); cermin fade gugur (`jual_2` net −690 vs baseline) | ini yang membedakan "Fabius tahu kapan jangan masuk" dari "Fabius bisa memilih posisi" - dan jawabannya hari ini: yang pertama, yang kedua belum ([[06-Results/13 - Apakah Tidak Trading Itu Gratis]]) |
| 20 | `python -X utf8 tools/entry_decomposition.py` (dan `--self-test`) | 28 Sep 09:45Z: 557 kejadian ber-sumur-dua; `cluster_ge2` **+93,0 (A px→px) → +0,1 (D tx→px) → +0,3 (B tx→tx)**; BH pada B = **kosong**; `fresh_token` tetap +12.006 s/d +22.638 di SEMUA kombinasi (artefak pull) | alat yang membatalkan klaim kami sendiri - self-test-nya mengunci bahwa pairing identik dan A−B = persis selisih harga masuk ([[06-Results/12 - Harga Masuk yang Benar]]) |
| 19 | `python -X utf8 tools/day2_replicate.py` (dan `--status`) | 28 Sep: ia punya **penjaga salinan basi** - `last_flow_stamp()` membandingkan stempel lokal dengan commit data `origin/*` dan mencetak `PERINGATAN: salinan lokal BASI - ... N MENIT lebih baru` sebelum hasil apa pun; teruji menangkap kasusnya sendiri (17 menit) lalu diam setelah `git pull`. Run 08:30Z: TERKUNCI `spec=0x03aa212f…`, `t_kunci=2026-09-28T06:13:38Z`, mencetak **"BELUM SAH - kurang 12.0 jam"** dan **nol angka hasil**; uji suntingan (30→31 di blok spesifikasi) -> `exit=1` dengan `SPESIFIKASI DIUBAH SETELAH DIKUNCI` | inilah benda yang punya hak bicara soal gerbang ⑧, bukan aku ([[06-Results/11 - Pra-Registrasi Hari Kedua]]) |

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

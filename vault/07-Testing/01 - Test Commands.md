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
| 19 | `python -X utf8 tools/day2_replicate.py` (dan `--status`) | 28 Sep: ia punya **penjaga salinan basi** - `last_flow_stamp()` membandingkan stempel lokal dengan commit data `origin/*` dan mencetak `PERINGATAN: salinan lokal BASI - ... N MENIT lebih baru` sebelum hasil apa pun; teruji menangkap kasusnya sendiri (17 menit) lalu diam setelah `git pull`. Run 08:30Z: TERKUNCI `spec=0x03aa212f…`, `t_kunci=2026-09-28T06:13:38Z`, mencetak **"BELUM SAH - kurang 12.0 jam"** dan **nol angka hasil**; uji suntingan (30→31 di blok spesifikasi) -> `exit=1` dengan `SPESIFIKASI DIUBAH SETELAH DIKUNCI` | inilah benda yang punya hak bicara soal gerbang ⑧, bukan aku ([[06-Results/11 - Pra-Registrasi Hari Kedua]]) |
| 20 | `python -X utf8 tools/entry_decomposition.py` (dan `--self-test`) | 28 Sep 09:45Z: 557 kejadian ber-sumur-dua; `cluster_ge2` **+93,0 (A px→px) → +0,1 (D tx→px) → +0,3 (B tx→tx)**; BH pada B = **kosong**; `fresh_token` tetap +12.006 s/d +22.638 di SEMUA kombinasi (artefak pull) | alat yang membatalkan klaim kami sendiri - self-test-nya mengunci bahwa pairing identik dan A−B = persis selisih harga masuk ([[06-Results/12 - Harga Masuk yang Benar]]) |
| 21 | (workspace) `python -X utf8 tools/mirror_test.py` lalu `python -X utf8 tools/tail_test.py` | 28 Sep ±10:0xZ: baseline P(≥+500 bps) **33,9 %**, mean winso **+82,7 bps**; tidak ada aspek yang menaikkan ekor (BH kosong); `jual_2` menurunkan ke **22,5 %** (p=0,0028) dan `jual_bersih` ke **20,3 %** (p=0,011); cermin fade gugur (`jual_2` net −690 vs baseline) | ini yang membedakan "Fabius tahu kapan jangan masuk" dari "Fabius bisa memilih posisi" - dan jawabannya hari ini: yang pertama, yang kedua belum ([[06-Results/13 - Apakah Tidak Trading Itu Gratis]]) |
| 22 | `python -X utf8 tools/policy_test.py` (`--horizon 60`) | 30 m: A **0** · B **+82,7 [+5,0; +159,1]** · C **+162,3 [+80,4; +243,0]** melewati hanya 13,6 % kejadian; D (keluar saat kerumunan beli) **TIDAK DIUJI** | jawaban terukur untuk "apa bedanya dengan tidak trading sama sekali" - dan batasnya (mean ≠ bisa diambil tanpa kedalaman) ([[06-Results/13 - Apakah Tidak Trading Itu Gratis]] §3b) |
| 23 | `python -X utf8 tools/select_test.py` | 28 Sep: 15 posisi dari 3 hari, CI acak [−440,1; +411,4], **tidak ada fitur keluar dari pita acak**; perhitungan daya: 68 posisi (±14 hari) untuk resolusi 200 bps, 272 (±55 hari) untuk 100 bps | ini yang membedakan "belum ketemu" dari "tidak akan terukur sebelum tenggat" - dan yang kedua inilah yang benar di sini ([[06-Results/13 - Apakah Tidak Trading Itu Gratis]] §3c) |
| 25 | `python -X utf8 tools/quintile_test.py` | 28 Sep ±10:4xZ: `lock_percent` Q1 -60,1 -> Q5 +66,0 bps (MW p=0,0000) dan P(>=+500) 36,0 % vs 0,0 % (Fisher satu arah p=0,0010) = **kandidat masuk pertama**; baseline subset berfitur **-64,7** vs semua **+82,7** -> cakupan terpilih ke arah buruk; `bundler_rate` +188,4 ditandai NOISE karena menentang veto kami | kuintil 24-51 kejadian = daya kecil; dan alat ini sendiri adalah bukti bahwa **p satu arah harus ditulis sendiri** (`ekor_hipergeo`) - `FC.fisher_p` dua-arah meloloskan arah yang salah ([[06-Results/13 - Apakah Tidak Trading Itu Gratis]] §3d/§3e) |
| 26 | `python -X utf8 tools/paper_book.py --per-day 200 --size-quote 0.01` (dan `1.0`) | 28 Sep ±10:58Z: random+veto **+188,3** · tanpa-gerbang **+95,1** · `lock` +109,7 (di 1 BNB: −51,2) · median semua −59 | buku paper = jawaban untuk "masuk boongan pun gapapa": veto terbukti sebagai kebijakan, penyortiran belum; dan tiap jalan mencetak `rows_sha256` yang bisa di-anchordataset ([[06-Results/14 - Buku Paper]]) |
| 27 | `python -X utf8 tools/paper_book.py --rank first --emit` lalu `python -X utf8 tools/winlog.py` | 28 Sep ±11:1xZ: 556 slot berlabel `mode=PAPER` dengan `pengganti_real` kosong; vonis `first` +140,9 CI [+35,0; +249,2] **tapi di bawah control random +188,3 -> BELUM LAYAK**; pada 5 posisi/hari @1 BNB: **−708,9**; `winlog` kini mencetak TIGA seri terpisah dan melaporkan "0 layak real, 0 ditambal posisi ASLI" | jalur paper->asli yang builder minta: streak dicatat, vonisnya F-D16 + wajib di atas control; slot yang belum ditambal tidak boleh ditulis sebagai PnL ([[06-Results/14 - Buku Paper]] §3a) |
| 28 | `python -X utf8 tools/entry_lab.py` | 28 Sep 11:32Z (`spec_sha=0x3ecad842…`, ditulis SEBELUM hasil): E2 +368,4 CI [+144,9; +587,7] median +146,5 **tapi di bawah CI atas control acak +487,5**, ekor p=0,33; E3 sama; E1 n=17 < 20 tidak diuji; BH ekor kosong | epik P31 punya jawaban pertama: **belum ada alasan masuk** - dan kuncinya menolak diedit setelah dilihat |
| 33b | `python -X utf8 tools/day2_replicate.py --halaman 17 --status` | 29 Sep 03:0xZ: TERKUNCI `spec 0xc4105c17…`, `t_kunci=02:59:06Z` diukur dari **`wp`** (bukan dari jam aliran), mencetak "sisa 12.0 jam lagi" dan **nol angka hasil** | ini yang membedakan "kunci ketiga" dari "mencoba lagi sampai dapat": halaman, kunci, dan syarat umurnya berpisah per spesifikasi ([[06-Results/17 - Pra-Registrasi Watch]]) |
| 37 | `python -X utf8 vault/scripts/check_portable_paths.py` | 29 Sep: 21.396 baris python dipindai, **0 path tidak portabel** | ia lahir dari job `paper-book` yang MATI di Linux karena `tools/mirror_test.py` merakit jalurnya dengan pemisah Windows - bug yang secara harfiah tidak bisa terlihat dari mesin penulisnya. Versi pertama gerbang ini menghasilkan 5 positif-palsu (termasuk docstring-nya sendiri) dan polanya diperketat sebelum dipercaya orang |
| 36 | `python -X utf8 vault/scripts/check_tool_citations.py` | 29 Sep: 831 sitasi alat terbaca - 816 valid, 14 DIRENCANAKAN, 1 RUJUKAN EKSTERNAL, **0 HILANG**; plus 38 sitasi ke `_research/` (folder kerja, di luar repo) yang dilaporkan sebagai daftar | gerbang ini lahir karena aku menulis komentar workflow yang menunjuk sebuah alat yang sudah tidak ada di repo (`attest-dataset`) - dan itu ketahuan cuma karena kebetulan kucoba menjalankan perintahnya |
| 34 | `python -X utf8 tools/presence_ledger.py` (`--min-siklus 3 --watch-min 120`) | 28 Sep 22:1xZ: ADA 489 mean +141,3 · HILANG 375 +140,5 · TIDAK-JELAS 575 +229,0; bound dengan bukti 1.064 teramati (+188,7) + 375 rugi penuh = **−381,7 bps/posisi** | yang membedakan angka ini dari bound lama: 'tidak dijawab' dipisah dari 'tidak ditanya' dan dari 'keluar daftar pantau kami' (F-D36) |
| 35 | `python -X utf8 universe/record_watch_prices.py --watch-min 120 --max-batches 40` | siklus nyata: `n_tanya=147 | harga 136 | wp0 11 | komposisi {'wpc':1,'wp':136,'wp0':11}` | `wpc` membuat batas batch tidak lagi menyamar jadi 'pool mati'; guard dedupe tahan baris tanpa `tk` (versi pertama melapor mencatat tanpa menulis apa pun) |
| 33 | `python -X utf8 universe/record_watch_prices.py --self-test` | 28 Sep: 6 kasus - satuan detik, satu baris per token, pair terlikuid menang, **`429/403/0/500 -> tidak ada catatan kehilangan`**, dan `answered-no-price` tetap tercatat | ini yang menjaga "pool hilang" berarti pool hilang, bukan "API kami sedang dibatasi" |
| 32 | `python -X utf8 tools/censor_bound.py` (`--horizon 60`) | 28 Sep: MUDA 547/2.814 teramati (**19,4 %**) mean +249,3 -> **-1.562,8** kalau yang hilang diberi p05; MATANG 476/796 (59,8 %) mean -86,6 | inilah yang membuat "harapan tinggal di token muda" gugur sebelum diuji: 80,6 % kejadiannya tidak punya harga keluar - dan itu bukan lubang data, itu beritanya |
| 31 | `python -X utf8 vault/scripts/fix_wrapped_links.py` | 28 Sep: dijalankan di vault penuh, menyentuh 1 berkas / 3 join, `check_links` setelahnya Broken 0 | konservatif: hanya menyambung baris yang membuka `[[` tanpa `]]` dan bukan bullet/tabel/heading - alat ini memperbaiki, tidak memutuskan apa pun (gerbangnya tetap `check_links.py`) |
| 30 | `python -X utf8 tools/technic_lab.py` | 28 Sep 15:52Z: 12 fitur teknikal (MA/RSI/MACD/Bollinger/Fib/breakout/volum/volatilitas) pada 1.054 kejadian, horison 30 dan 120 m - **nol di atas control acak**, nol lolos BH; `breakout` -587,9 CI [-951,9; -201,4] dengan P(>=500) 3,7 % | spesifikasi terkunci sebelum hasilnya dilihat (`prereg-technic-lock.json`); bar kami = deret transaksi, jadi ini ADAPTASI teknik klasik, bukan uji Fibonacci di OHLC 4 jam ([[06-Results/15 - Teknikal Klasik Diuji]]) |
| 29 | `python -X utf8 tools/flow_gate.py --self-test` (lalu `python -X utf8 tools/flow_gate.py 0x<alamat>`) | 28 Sep: 7 kasus lolos - veto-maker, veto-rasio, boleh, berkas-basi, token-tak-dikenal, `apply()` hanya mengurangi, `apply(BOLEH)` tidak menambah apa pun; berkas nyata = 2.586 token, ekor 13:12Z | gerbang [7] jadi PERILAKU agen; bug cache-nya (tanda `mtime+size` -> isi 2 KB terakhir berkas) ditangkap oleh self-test-nya sendiri (F-D34) |

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

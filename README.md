# Fabius

**Menolak pertempuran yang belum menguntungkan. Menyerang hanya saat medannya memihak.**

Namanya dari Quintus Fabius Maximus *Cunctator* — diktator Romawi yang mengalahkan Hannibal
dengan tidak memberikan pertempuran yang ingin Hannibal menangkan. Roma kalah besar di Cannae
karena ingin bertempur. Fabius menang karena tidak.

Itu pekerjaan sistem ini. Ia bukan bot yang menjanjikan keuntungan; ia firma riset yang
menyaring, menilai, dan **menahan diri** — lalu mencatat setiap keputusan, termasuk penolakannya,
di sebuah ledger yang tidak bisa diubah setelahnya.

```
UNIVERSE BSC        ->  REFUSAL GATE      ->  DESK (typed questions)  ->  PM + GATES  ->  ANCHOR
GeckoTerminal          honeypot, likuiditas,   satu state, N pertanyaan    R:R, rezim,          bytes32
GMGN rank              umur, top-10, bundler,   bertipe, PARALEL &         makro/event-risk     + event
CoinGecko              lock, exit-size          terisolasi                 abstain ber-alasan
GDELT (berita)                                                                  |
Hyperliquid (funding/OI)                                                        v
TradingView (teknikal)                                        ENTER -> keputusan di-anchor
                                                              ABSTAIN -> alasannya di-anchor
```

## Yang bikin ini bukan klise "AI trading bot"

**1. Penolakan adalah outputnya, bukan kegagalannya.** Panel hari ini berkata
"0 kandidat lolos, dan ini alasan per gerbang". Angka itu lebih sulit dipalsukan daripada
screenshot profit, dan bisa diklik.

**2. Beberapa aturan ditegakkan kontrak, bukan niat baik.** `DecisionAnchor` menolak catatan
tanpa `snapshotHash` (keputusan wajib bisa menunjuk data point-in-time yang memakainya) dan
menolak `ABSTAIN` tanpa `gatesHash` (menolak tanpa alasan bukan penolakan, itu cuma mati).
Lihat `contracts/DecisionAnchor.sol`. 21 test, lulus semua.

**3. Asetnya boleh dicabut.** `setAgentActive(agent, false)` mencabut kewenangan agen on-chain;
setelah itu panggilannya revert. Ini jawaban untuk "bagaimana kalian menghentikan agen yang
menyimpang" — remnya bisa didemokan, bukan dijanjikan.

**4. Kami tidak mengklaim bukti yang tidak bisa kami berikan.** Kontrak membuktikan keberadaan,
keutuhan, penanda tangan, dan urutan waktu. Ia **tidak** membuktikan keputusan itu benar,
menguntungkan, atau benar-benar dihasilkan model yang disebutkan. Verifiable inference (TEE/zkML)
tidak tersedia di chain ini, dan kami menulis batas itu daripada menyembunyikannya.

## Status sekarang, tanpa dipoles

| Bagian | Status |
|---|---|
| `contracts/DecisionAnchor.sol` + test | ✅ ada; **21 test lulus** (`forge test`) di mesin ini |
| Perekam universe point-in-time | ✅ jalan; **62 snapshot** (62 baris ≠ 62 jam: `manifest.txt` mencatat **13 gap > 2 jam**, terbesar 16,31 jam — cron GitHub tidak bisa dijamin, lihat `vault/01-Agent/01 - Asset Classes and Seats.md` §cron); universe **140 baris** (GMGN rank 100 = langit-langit server, + 40 pool GT). Verifikasi sha256 tiap snapshot: **60 dari 62 lolos** — 2 baris tidak dapat dihitung ulang dan pemicunya belum diketahui (`vault/06-Results/03 - Not Yet Proven.md` #21; dua hipotesis sudah digugurkan dengan pengukuran, bukan dengan argumen). Angka 60/62 itulah yang kami pakai, bukan 62 |
| Perekam aliran wallet ⑦ | ✅ berdetak sendiri di Actions sejak 26 Sep 08:15Z: jalanan pertama `64234bd` = **607 transaksi unik / 80 maker / 63 token** dalam 35 menit; per jam ke-4 sudah **3.512 transaksi tersimpan**. Alirannya cuma menutup 8-13 menit dan **tidak bisa ditarik mundur** (paging diabaikan server), karena itu cron `*/10` diganti jadi rantai dispatch-diri + commit tiap ±4 menit |
| Penyaring + hasil penolakan | 🟡 berjalan; **136 token** punya hasil forward, **kohort "lolos" masih 0** (harga pool baru tercatat sejak 22 Sep 08:00Z) |
| Lapisan keputusan deterministik | 🟡 `tools/decide.py`: snapshot → `decisionHash` + `gatesHash` + `snapshotHash`, calldata terverifikasi (`cast sig` = `0xdc6a1ac2`). **Memisahkan "ditolak karena risiko terukur" dari "tidak dinilai karena data tidak ada"** (terukur: 37 dan 13 dari 90) |
| Lapisan penilai (model) | 🟡 **opsional dan bisa dicabut** (`--judge none\|auto\|jev\|openai`, default `none`). Terukur 23 Sep: 1 panggilan = $0,00002407, 0,43s, `jev-1.13.0`; veto **satu arah** (hanya boleh membatalkan ENTER) dan hasilnya masuk `decisionHash` |
| **Lapisan ARAH** (long/short, kapan, seberapa besar, seberapa lama) | 🟡 **ada dan jalan di atas data BNB-native** (25 Sep): `tools/bars.py` menarik deret Aster tanpa API key (**9.599 bar / 400 hari**), `tools/direction.py` menggabungkannya dengan funding+OI per 4 jam dan `\|autocorrelation\|` → `side`/`entry`/`stop`/`target`/ukuran/horizon. Dua rezim keluar: **stop-loss** hanya kalau yakin (conf ≥ 0,6 dan pola terukur), sisanya **hard time-stop 24 jam + exit-size ≤ 1% likuiditas**. Contoh siklus nyata: `MARSCOINUSDT` short, entry 0,11605, stop 0,12237, target 0,10341, horizon 24 j, risiko 0,5%. **Model pernah bilang "short" untuk dua kandidat yang kami tolak** (`bar=422`/`99 < 720`) dan keputusannya tetap `flat` — gerbang menentukan, model hanya boleh mengurangi |
| **Uji aturan arah terhadap hasil** | ❌ **hasilnya NEGATIF, dan halaman itu yang membuatnya bisa dipertahankan.** `tools/backtest.py` menjalankan aturan yang **sama** dengan live (`tools/direction.py`, ambang diimpor dari kode, tidak ada yang di-fit) di 400 hari × 12 aset (240–1.216 trade non-overlap/simbol): net **rugi di 12/12** (−27,9 … −0,8 bps/trade vs ongkos 20 bps RT), gross cuma +1,5 … +4,0 bps di 4 simbol yang lolos gerbang, **dibalik arahnya tetap kalah** (−39,2 … −12,1), horizon 24 jam tetap 0/12 lolos. Kesimpulan yang boleh dipakai: **agen ini tahu kapan harus diam, tapi belum tahu kapan untung.** Rinci: `vault/06-Results/04 - Negative Results.md` + `decisions/backtest-*.json` |
| Bidang ④ — keamanan kontrak kandidat | ✅ `tools/security_gate.py` (25 Sep): GMGN `token/security` + GoPlus dibaca untuk **≤5 kandidat arah** (10 panggilan/siklus — jalur screen 40 alamat sudah terbukti tak terbayar, `vault/06-Results/03 - Not Yet Proven.md` #12). Empat status, dan **"belum diukur" ≠ bersih**: `OK` / `BLOCKED` / `DISAGREE` / `UNMEASURED` (terpicu nyata: pPOLY `is_honeypot=None`). Hasilnya masuk `gatesHash`. Gerbangnya **hanya boleh mengurangi** — `BLOCKED → flat`, tidak ada jalur sebaliknya |
| Kursi: ①+④+⑥ ditegakkan, bukan disimpan di kepala | ✅ `direction.apply_gates()`: `seat_eligible` + `seat_blockers` di tiap keputusan. Terbukti menggigit pada siklus pertama: `GENIUSUSDT` bersih ④ dan 3.940 bar di ① tapi **kursinya ditolak** karena `⑥liq=$19.388 < $50.000` |
| Anchor keputusan SUNGGUHAN ke chain | ✅ `tools/anchor.py` (25 Sep): membaca `decisions/direction-*.jsonl` dan mengirim 3 hash-nya apa adanya, lalu **membaca ulang `getAnchor(id)` dan membandingkan word per word**. Empat batch = **17 anchor** (`Enter=3` / **`Abstain=14`**), gas 230.899–250.819/anchor. Bukan hash uji: yang masuk chain termasuk penolakan, dengan alasannya di-`gatesHash`. `--verify` mengulang pemeriksaan itu **tanpa kunci dan tanpa gas** (id dihitung ulang dari file, lalu dibaca dari chain): **11/11 cocok pada 6 field** termasuk `asset` — field yang dulu terbaca sampah dan membuat kalimat "chain == lokal" lebih luas dari yang dibandingkan (`vault/02-Contracts/02 - Deployed on 97.md`). Dibaca ulang 28 Sep 01:58 WIB (= 27 Sep 18:58Z) tanpa mengubah apa pun: **19 anchor** (`Enter=4` / `Abstain=15`, dari `countByVerdict`) dan **13/13 cocok**; selisih chain-vs-repo **6 entri** masih terbuka (`vault/08-Backlog/01 - Backlog.md` P6b) — jadi yang kami kutip adalah 13 yang terbuktikan dari berkas, bukan 19 |
| **Uji ⑦ smart money vs kerumunan** | ❌ **sama-sama negatif, dan ini jawaban kedua dari arah yang berbeda.** `tools/smartmoney_score.py`: 51.863 entri swap BSC 10 hari dari **Dune**, dinilai hasilnya dengan **kline Aster yang kami tarik sendiri** (Dune tidak dipakai untuk harga: barisnya bisa di-update retro), ongkos 20 bps RT. Mentahnya menipu: panel +680,7 bps vs kontrol +336,4 bps terlihat seperti "whale 2x jago" — padahal baseline pembeli bukan nol, tapi *semua pembeli token itu di jam itu* (+336 pada 8.324 transaksi kerumunan = tokennya lagi naik). **Berpasangan per (token, jendela 4 jam)**, drift terbuang: **selisih −10,4 bps, p=0,568 (sign-flip 20.000) = tidak berbeda dari kerumunan**; 54 wallet capai n≥20, **0 lolos BH**. Batas yang disebut di muka: keanggotaan panel berasal dari label GMGN *hari ini* sementara entrinya 10 hari ke belakang → itu lookahead label, jadi −10,4 adalah **batas atas yang ramah ke panel**; versi bersihnya kecil kemungkinan berbalik. Rinci: `vault/06-Results/04 - Negative Results.md` §4c |
| **Uji aliran kerumunan — PRA-REGISTRASI** | ❌ **vonis ketiga dan yang terakhir.** Hipotesis + ambang ditulis **sebelum** satu angka pun dilihat (`vault/06-Results/05 - Pre-registration Flow.md`), lalu diuji: agregat `dex.trades` Dune 14 hari = **18.122 titik (token, jam)** untuk 86 token ber-kontrak perp (1 kueri = **19 detik**, vs 503 detik untuk kueri baris-mentah), hasil forward dari kline kami sendiri. **62 token lolos `n>=20` → 0 lolos BH** di semua hipotesis; drop-best-fold: dolar kerumunan **−22,2 bps**, jumlah kepala **−6,2 bps**. Halaman hasilnya juga memuat **cacat kami sendiri** yang ketahuan di jalan: H3 ternyata statistik yang sama dengan H1 (cuman tanda dibalik), join heks kapital↔kecil menjatuhkan **85/86 token** tapi tetap mencetak tabel yang terbaca sah, dan fold pertama saya salah arti. Sekarang alatnya **menolak melapor** kalau cakupan runuh. |
| **Uji UMUR posisi (E11, 29 Sep)** | 🟠 **Yang pertama positif DAN lolos placebo - dan tetap bukan klaim profit.** `tools/horizon_decay.py` mengukur harapan sebagai fungsi UMUR posisi pada 393 kejadian beli kerumunan pintar (harga ticker `wp` yang berdetak sendiri, ongkos 59 bps RT): **mean winso +192,7 bps di menit ke-2, +202,6 di menit ke-5, +45,0 di menit ke-10, lalu −42,0 → −182,5 di menit ke-30**. Berpasangan pada POSISI yang sama vs 30 menit: **5 dari 5 horison pendek menang** (median +120,8 … +5,3 bps; tanda-uji eksak p ≤ 0,00002). Tiga kontrol yang membuat kami belum menjualnya: **placebo asal-mula** (jam digeser acak 30–90 menit) menghasilkan kurva **datar −184,7 … −113,9** - jadi kemiringannya milik peristiwa, bukan milik jam; `P(ada harga keluar)` 84–85 % rata di semua horison (bukan korban penyensoran); umur baris harga keluar hanya −6…+8 detik dari horison yang diklaim, jadi label "5 menit" adalah ukuran, bukan nama. Ganti harga masuk dari ticker ke harga transaksi (`tx.p`) dan bump-nya menyusut −24…−41 bps: bertahan, tidak hilang. Rinci: `vault/06-Results/19 - Umur Posisi.md` + `decisions/horizon-decay-*.json` |
| **Ulang-uji REM di horison cepat (E13, 29 Sep)** | 🟢 **Yang paling bisa dipakai, dan tetap bukan sebab-akibat.** F-D31 memasang gerbang `jual_*` karena menguntungkan di horison 30 menit (+82,7 → +162,3 bps). Setelah E11 membuktikan 30 menit itu bocor, kami uji ulang remnya di horison tempat kabar hidup - `tools/veto_expectancy.py`, 482 kejadian, `tools/flow_gate.py` apa adanya tanpa ambang baru: pada menit ke-5, `BOLEH` mean **+285,5 bps** dengan median **+79,8** (di atas lantai ongkos −59), `VETO` **−230,3** dengan median **−377,8**; selisih **+515,8** melawan CI atas placebo penandaan ulang acak **+397,2** - dan lewat juga di 2 m (+450,3 vs +294,5) dan 30 m (+487,5 vs +405,1). Kenapa ini tidak diperlakukan seperti kandidat sebelumnya: median dan mean searah, placebo-nya adalah kontrol yang membunuh E7/E8, dan nol parameter baru. Batas yang menempel: `VETO` bukan kelompok acak (ia kejadian yang sedang dihajar penjual) → asosiasi terarah; statusnya **eksplorasi tanpa kunci**. **⚠ Ekor ini ditulis 08:43Z dan dua batasnya sudah dibaca ulang: latensi kami sekarang 61 d bukan 2 menit (F-D54), dan venue bukan cuma soal daftar - lihat baris E20/E26 di bawah (F-D56/57/58).** Rinci: `vault/06-Results/21 - Rem di Horison Cepat.md` · `decisions/veto-expectancy-20260929T084355Z.json` |
| **Venue kami bukan pasar pada resolusi menit (E20 + E26, 29 Sep)** | 🟥 **Dua angka baru, satu kesimpulan yang tidak kita mau.** Reachable: kabar beli 24 jam yang sampai ke venue perp kami = **2,26 %** kalau yang ditanya pasangan yang persis sama, **5,86 %** kalau aset yang sama (jendela bergulir: 14:17Z = 2,40 % / 6,30 % - sebut jamnya) - parser lama (`potong`, hanya mengenal USDT/USDC/PERP) membuang **17 dari 584** entri daftar (`BTCU`, `BTCUSD1`, `SKHYNIXUSD1`, ...), jadi angka 3,1 % yang sepekan ini dikutip harus menyebut pertanyaannya (F-D57). Hidup: dari 41 simbol reachable, yang harga perp-nya bergerak pada resolusi menit cuma **5** - `tools/perp_liveness.py` mengukur kelas MATI pada median **97,4 % menit tanpa transaksi**, dan `BNCUSD1` (simbol dengan kabar terbanyak, 478) beku 446 menit; kabar pada simbol yang layak uji horison menit = **0,20 %** (F-D56). Dan di 5 simbol hidup itulah klaim inti diuji: `tools/perp_bump.py` (cache 3 hari sejak P59, n=31 dari 33 kejadian) memberi @2 m mean **−2,6** vs placebo **+3,3**; @5 m **+15,2** vs placebo **+10,7**; berpasangan 5m-vs-30m median **+14,8 bps, menang 16 kalah 15, p=0,50** - dan dengan cache 24 jam (n=15) mean @5 m-nya **−7,3**, jadi setiap angka E26 wajib disebut bersama n-nya - **bump E11 tidak pindah ke harga perp**; di kelas TIPIS median return-nya tepat **0,0** di semua horison karena deretnya beku (F-D58). Bukan vonis akhir (satu hari, n kecil, klines bukan kedalaman) - ini batas atas yang terukur, dan dia memindahkan pertanyaan dari "kapan masuk" ke "di pasar mana kami punya harga yang hidup". `python -X utf8 tools/perp_liveness.py` · `python -X utf8 tools/perp_bump.py` - [[06-Results/28 - Venue Kami Bukan Pasar]] |
| **Jalur kabar → keputusan (P40/P50/P55, 29 Sep)** | 🔴 **Dua koreksi bertingkat dalam satu hari (F-D50 → F-D54).** Umur kabar saat kami memutuskan bukan 808 d: sesudah kandidat diambil dari yang tersegarnya (`b990ab5`), rejim yang sama memberi **median 61 d (n=182, 97 % < 180 d)** - temboknya ada di alatku, bukan di sumbernya. Dan karena jendela arm 5 m mulai di kejadian+120 d, **0 dari 58 lengan rejim lama** adalah hasil masuk yang sah: yang selama ini kupajang sebagai "menit ke-5" mengukur **masa lalu sebelum kami masuk**. pairing lama (n=3) dicabut. Angka sah pertama: **n=25, mean winso −519,4 / median −76,4 bps**, `entry_px` sudah di atas harga whale pada 16/25 - jadi kecepatan bukan lagi alasan, dan alasan masuk tetap belum ada. `tools/fast_lane.py --report` (hanya lengan `sah`; median gabungan dilabeli TIDAK BOLEH DIKUTIP) - [[06-Results/26 - Masuk Segar, Terukur Benar]] |
| **Lima uji prospectif yang sedang berjalan (E9, E12, E16, E22, E24)** | 🔒 **Terkunci sebelum datanya ada, dan tidak satu pun boleh dibaca sebelum jamnya.** E9 `vol-rendah` vs `vol-tinggi` (05:13:25Z → **17:13:25Z**, `tools/vol_ab.py`); E12 keluar 5 m vs tahan 30 m pada posisi yang sama (08:04:56Z → **20:04:56Z**, `tools/hold_ab.py`); E16 state imbalance buku order (09:37:45Z → **21:37:45Z**, `tools/book_prereg.py` - **wajib** membawa komposisi simbol, karena cakupan berubah di tengah jendela, F-D47); E22 **rem** diuji prospectif: `BOLEH` vs `VETO` di menit ke-5 pada kejadian yang belum terjadi (12:08:15Z → **20:08:15Z**, `tools/gate_ab.py`) - uji prospectif pertama untuk **perilaku**, bukan untuk fitur. Lima berkas kunci + sha spesifikasinya ada di `decisions/` (`prereg-fastlane-lock.json` untuk E24); halaman 18/20/22/25/27 menyimpan aturannya, dan bagian "Hasil"-nya **sengaja kosong** sampai jamnya (`--status` menolak memvonis) |
| **Identitas agen di registry resmi BNB Chain** | ✅ **terdaftar di ERC-8004 `IdentityRegistry` chain 97** (`0x8004A818…BD9e`, `name()='AgentIdentity'`) sebagai **tokenId 2494**, tx [`0x33f47391…`](https://testnet.bscscan.com/tx/0x33f47391c3a313b1d167e68a760e24746adac2d1aa39b44383b1f232ea2013dd) `status=1` gas 200.844. Diverifikasi dengan MEMBACA registry: `getAgentWallet(2494)` dan `ownerOf(2494)` = `0x4bb30E3b…` (alamat agen). Ini jawaban untuk pertanyaan "bagaimana agen lain tahu kita ada": identitas + `agentURI` (`docs/agent-card.json`, di-pin ke raw.githubusercontent repo ini) yang berisi endpoint x402-nya. ABI vendor: `docs/upstream-8004/` (`erc-8004/erc-8004-contracts @ b9e466c2`, sha256 tercatat). Ulangi: `python tools/x8004_register.py --verify` |
| Penilaian hasil (`ledger.py`) | ✅ **sudah menghasilkan angka, dan angkanya tidak enak.** 26 Sep 08:23Z: dua short MARSCOIN yang kami anchor 24 Sep (blok 132955030/132955788) jatuh tempo → **+1,5 bps net MENANG** dan **−146,3 bps net RUGI**; `WR 50 %`, net rata-rata **−72,4 bps**, **n = 2** (tidak ada satu pun uji statistik yang boleh dijalankan di atasnya). Harga masuk dibaca dari **rekaman** (`entry_ref` ikut `decisionHash`), bukan dihitung ulang; "belum waktunya" punya status sendiri dan tidak ikut agregat; stop+target di bar yang sama = `AMBIGU`. Rinci: `vault/06-Results/04 - Negative Results.md` §4b |
| Lapisan desk penuh (debat antar-desk) | ⬜ spesifikasi ditulis (`vault/00-Overview/03 - Decisions.md` F-D04), kode belum |
| Eksekusi | ⬜ **paper on purpose** — tidak ada dana pengguna, tidak ada order, tidak ada yang bisa rugi |
| Deploy ke chain 97 | ✅ **terverifikasi dari chain 24 Sep** — `0xdd162afb5f5f92d5092f845A93660e3B38259330`; bytecode 4748 B identik dengan build lokal; `anchor()` dari agen terpisah sukses (gas 302.011); event `Anchored` ter-indeks dengan topic2 = alamat agen; **rem on-chain terbukti** (setelah revoke → revert, setelah relist → pulih). Detail + cara mengulang: `vault/02-Contracts/02 - Deployed on 97.md` |
| **x402: agen membayar agen di BNB Chain** | ✅ **DIEKSEKUSI DI CHAIN 97, 26 Sep** — bukan fork, bukan simulasi. Klien (`tools/x402_client.py`) membaca chain, menerima `402 + PAYMENT-REQUIRED`, menandatangani dua authorization EIP-712 (Permit2 witness + EIP-2612), dan **dompetnya punya 0 BNB** — gas ditanggung fasilitator (server ini). Hasil: tx [`0xb6093e59…`](https://testnet.bscscan.com/tx/0xb6093e597530214e92b67d44a02f1aeb833bd7881e40eac5e64c5840347062d0) `status=1`, gas 114.930, blok 133.285.597; saldo pembeli 5.000.000 → 4.999.000 atomic (tepat tagihan 1.000), `payTo` bertambah 0,001. Token: `0xB11D90214089684081F57A03d3300E20725297f8` (demo, milik kami sendiri); proxy: kanonis `0x402085c2…`. Yang membuat ini bukan klaim kosong: angka di atas dibaca ulang dari `eth_getTransactionReceipt`/`balanceOf`, bukan dari log server. |
| Fasilitator x402 sendiri | 🟡 **buktinya sekarang ada di repo ini, bukan di laci riset.** `FOUNDRY_PROFILE=fork forge test --fork-url bscTestnet` = **44 lulus**: 21 `DecisionAnchor` + 15 `X402DemoToken` + **8 test settlement terhadap proxy kanonis yang sudah ter-deploy di chain 97 yang hidup** — termasuk tiga penolakan yang membuat jalur ini layak disebut fasilitator: **pemanggil `settle()` tidak bisa memindahkan dana ke alamat lain** (witness terikat EIP-712), **tidak bisa melebihkan jumlah**, dan **nonce tidak bisa dipakai ulang**. Sumber upstream di-vendor **verbatim dengan sha256 tercatat** (`contracts/vendor/x402/VENDORED.json`; baca-saja di `docs/upstream-x402/`, sengaja tidak dikompilasi: `coinbase/x402` @ `dd927a26`). Test fork ini yang membuktikan **sifat paksaannya**; pembayaran nyata lewat HTTP ada di baris di atas |

Lihat `vault/06-Results/03 - Not Yet Proven.md` untuk daftar lubang yang masih menganga dan cara menutupnya.

## Ruang lingkup folder ini

Hanya jalur **AI Agents / agentic trading**. Tidak ada apa pun soal kredensial, Open Badges,
e-course, atau jalur lain di sini — aturan dan alasannya ada di `vault/README.md`.

## Cara menjalankan

```
forge test -vv                                    # 21 test (profil default: target shanghai)
FOUNDRY_PROFILE=fork forge test --fork-url bscTestnet -vv   # 44 test, termasuk 8 settlement x402 di chain 97 hidup
#   (di cmd.exe Windows: `set FOUNDRY_PROFILE=fork&& forge test --fork-url bscTestnet -vv`)
python -u tools/screen_universe.py --windows     # corong penolakan dari dataset
python -u tools/bars.py BNBUSDT --days 400       # seberapa dalam deret harga yang benar2 kita punya
python -u tools/direction.py --top 5 --emit      # arah + ④ + entry/stop/ukuran/horizon (butuh kunci Jev utk model; --no-model utk deterministik, --no-security utk offline)
python -u tools/security_gate.py --emit          # bidang ④ saja: honeypot/can_not_sell dari 2 sumber
python -u tools/backtest.py --mom-only --flip    # aturan yang sama, arah dibalik: tetap kalah (lihat vault/06-Results/04 - Negative Results.md)
python -u tools/anchor.py --dry-run              # apa yang AKAN dikirim ke chain 97 (nol transaksi)
python -u tools/anchor.py --verify               # BACA ULANG anchor dari chain: tanpa kunci, tanpa gas (13 terpelacak pada run 28 Sep)
python -u tools/ledger.py                        # apakah posisi yang di-anchor menang/kalah? (atau: belum jatuh tempo)
python -u tools/dune_flow.py --window 14         # agregat aliran kerumunan dari Dune (1 kueri; cache di data/)
python -u tools/flow_test.py                     # jalankan uji yang TERKUNCI di vault/06-Results/05 - Pre-registration Flow.md - bukan variannya
python -u tools/test_decode_anchor.py            # 13 uji offline parser retur (tanpa network)
python -u tools/verify_deploy.py                 # baca ulang keadaan chain, bukan keluaran forge
```

Sebelas keputusan arah sudah masuk chain — **2 `Enter` dan 9 penolakan**, dan keduanya dihitung
dari `decisionHash` yang sama dengan file di repo ini: `decisions/direction-*.jsonl`
(di-commit sejak 25 Sep, karena `decisionHash`-nya tidak dapat dibangun ulang — lihat komentar
`.gitignore`) vs `getAnchor(id)` di `0xdd162afb…`. Nomor blok dan hasil pencocokan word-per-word
ada di `vault/02-Contracts/02 - Deployed on 97.md`.

`lib/forge-std` dan `node_modules/@openzeppelin` adalah **junction** ke `../app/`, bukan salinan
(satu resep, nol kesempatan drifting) — karena itu keduanya di-`gitignore` dan perlu dibuat ulang
setelah clone:

```
mklink /J lib\forge-std              ..\app\lib\forge-std
mklink /J node_modules\@openzeppelin ..\app\node_modules\@openzeppelin
```

Fork test wajib jalan pada profil fork (`evm_version = cancun`); menjalankannya pada `shanghai`
menghasilkan `EvmError: NotActivated` yang mudah salah dibaca sebagai bug kontrak.

## Membaca urutan kerjanya

Mulai dari `vault/00-Overview/01 - Briefing.md`. Angka-angka di `vault/06-Results/02 - Thresholds.md` punya `file:line` asal-usul
dan tanggal diverifikasi — kalau sebuah angka tidak punya keduanya, ia bukan ambang, dia dugaan.

MIT.

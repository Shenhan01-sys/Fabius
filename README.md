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
| Perekam universe point-in-time | ✅ jalan; **54 snapshot / 33 jendela jam** per 24 Sep 19:06Z (54 baris ≠ 54 jam: n yang sah adalah jumlah jendela; `manifest.txt` mencatat **5 gap > 2 jam**, terbesar 16,31 jam — cron GitHub tidak bisa dijamin, lihat `vault/08` §cron); universe **140 baris** (GMGN rank 100 = langit-langit server, + 40 pool GT); sha256 per snapshot diverifikasi ulang, dirantai lewat `universe/manifest.txt` |
| Penyaring + hasil penolakan | 🟡 berjalan; **136 token** punya hasil forward, **kohort "lolos" masih 0** (harga pool baru tercatat sejak 22 Sep 08:00Z) |
| Lapisan keputusan deterministik | 🟡 `tools/decide.py`: snapshot → `decisionHash` + `gatesHash` + `snapshotHash`, calldata terverifikasi (`cast sig` = `0xdc6a1ac2`). **Memisahkan "ditolak karena risiko terukur" dari "tidak dinilai karena data tidak ada"** (terukur: 37 dan 13 dari 90) |
| Lapisan penilai (model) | 🟡 **opsional dan bisa dicabut** (`--judge none\|auto\|jev\|openai`, default `none`). Terukur 23 Sep: 1 panggilan = $0,00002407, 0,43s, `jev-1.13.0`; veto **satu arah** (hanya boleh membatalkan ENTER) dan hasilnya masuk `decisionHash` |
| **Lapisan ARAH** (long/short, kapan, seberapa besar, seberapa lama) | 🟡 **ada dan jalan di atas data BNB-native** (25 Sep): `tools/bars.py` menarik deret Aster tanpa API key (**9.599 bar / 400 hari**), `tools/direction.py` menggabungkannya dengan funding+OI per 4 jam dan `\|autocorrelation\|` → `side`/`entry`/`stop`/`target`/ukuran/horizon. Dua rezim keluar: **stop-loss** hanya kalau yakin (conf ≥ 0,6 dan pola terukur), sisanya **hard time-stop 24 jam + exit-size ≤ 1% likuiditas**. Contoh siklus nyata: `MARSCOINUSDT` short, entry 0,11605, stop 0,12237, target 0,10341, horizon 24 j, risiko 0,5%. **Model pernah bilang "short" untuk dua kandidat yang kami tolak** (`bar=422`/`99 < 720`) dan keputusannya tetap `flat` — gerbang menentukan, model hanya boleh mengurangi |
| **Uji aturan arah terhadap hasil** | ❌ **hasilnya NEGATIF, dan halaman itu yang membuatnya bisa dipertahankan.** `tools/backtest.py` menjalankan aturan yang **sama** dengan live (`tools/direction.py`, ambang diimpor dari kode, tidak ada yang di-fit) di 400 hari × 12 aset (240–1.216 trade non-overlap/simbol): net **rugi di 12/12** (−27,9 … −0,8 bps/trade vs ongkos 20 bps RT), gross cuma +1,5 … +4,0 bps di 4 simbol yang lolos gerbang, **dibalik arahnya tetap kalah** (−39,2 … −12,1), horizon 24 jam tetap 0/12 lolos. Kesimpulan yang boleh dipakai: **agen ini tahu kapan harus diam, tapi belum tahu kapan untung.** Rinci: `vault/09-Uji-Arah-Tidak-Ada-Edge.md` + `decisions/backtest-*.json` |
| Bidang ④ — keamanan kontrak kandidat | ✅ `tools/security_gate.py` (25 Sep): GMGN `token/security` + GoPlus dibaca untuk **≤5 kandidat arah** (10 panggilan/siklus — jalur screen 40 alamat sudah terbukti tak terbayar, `vault/05` #12). Empat status, dan **"belum diukur" ≠ bersih**: `OK` / `BLOCKED` / `DISAGREE` / `UNMEASURED` (terpicu nyata: pPOLY `is_honeypot=None`). Hasilnya masuk `gatesHash`. Gerbangnya **hanya boleh mengurangi** — `BLOCKED → flat`, tidak ada jalur sebaliknya |
| Kursi: ①+④+⑥ ditegakkan, bukan disimpan di kepala | ✅ `direction.apply_gates()`: `seat_eligible` + `seat_blockers` di tiap keputusan. Terbukti menggigit pada siklus pertama: `GENIUSUSDT` bersih ④ dan 3.940 bar di ① tapi **kursinya ditolak** karena `⑥liq=$19.388 < $50.000` |
| Anchor keputusan SUNGGUHAN ke chain | ✅ `tools/anchor.py` (25 Sep): membaca `decisions/direction-*.jsonl` dan mengirim 3 hash-nya apa adanya, lalu **membaca ulang `getAnchor(id)` dan membandingkan word per word**. Empat batch = **17 anchor** (`Enter=3` / **`Abstain=14`**), gas 230.899–250.819/anchor. Bukan hash uji: yang masuk chain termasuk penolakan, dengan alasannya di-`gatesHash`. `--verify` mengulang pemeriksaan itu **tanpa kunci dan tanpa gas** (id dihitung ulang dari file, lalu dibaca dari chain): **11/11 cocok pada 6 field** termasuk `asset` — field yang dulu terbaca sampah dan membuat kalimat "chain == lokal" lebih luas dari yang dibandingkan (`vault/07`) |
| **Uji ⑦ smart money vs kerumunan** | ❌ **sama-sama negatif, dan ini jawaban kedua dari arah yang berbeda.** `tools/smartmoney_score.py`: 51.863 entri swap BSC 10 hari dari **Dune**, dinilai hasilnya dengan **kline Aster yang kami tarik sendiri** (Dune tidak dipakai untuk harga: barisnya bisa di-update retro), ongkos 20 bps RT. Mentahnya menipu: panel +680,7 bps vs kontrol +336,4 bps terlihat seperti "whale 2x jago" — padahal baseline pembeli bukan nol, tapi *semua pembeli token itu di jam itu* (+336 pada 8.324 transaksi kerumunan = tokennya lagi naik). **Berpasangan per (token, jendela 4 jam)**, drift terbuang: **selisih −10,4 bps, p=0,568 (sign-flip 20.000) = tidak berbeda dari kerumunan**; 54 wallet capai n≥20, **0 lolos BH**. Batas yang disebut di muka: keanggotaan panel berasal dari label GMGN *hari ini* sementara entrinya 10 hari ke belakang → itu lookahead label, jadi −10,4 adalah **batas atas yang ramah ke panel**; versi bersihnya kecil kemungkinan berbalik. Rinci: `vault/09` §4c |
| **Uji aliran kerumunan — PRA-REGISTRASI** | ❌ **vonis ketiga dan yang terakhir.** Hipotesis + ambang ditulis **sebelum** satu angka pun dilihat (`vault/10-Pra-Registrasi-Uji-Aliran.md`), lalu diuji: agregat `dex.trades` Dune 14 hari = **18.122 titik (token, jam)** untuk 86 token ber-kontrak perp (1 kueri = **19 detik**, vs 503 detik untuk kueri baris-mentah), hasil forward dari kline kami sendiri. **62 token lolos `n>=20` → 0 lolos BH** di semua hipotesis; drop-best-fold: dolar kerumunan **−22,2 bps**, jumlah kepala **−6,2 bps**. Halaman hasilnya juga memuat **cacat kami sendiri** yang ketahuan di jalan: H3 ternyata statistik yang sama dengan H1 (cuman tanda dibalik), join heks kapital↔kecil menjatuhkan **85/86 token** tapi tetap mencetak tabel yang terbaca sah, dan fold pertama saya salah arti. Sekarang alatnya **menolak melapor** kalau cakupan runuh. |
| Penilaian hasil (`ledger.py`) | ✅ **sudah menghasilkan angka, dan angkanya tidak enak.** 26 Sep 08:23Z: dua short MARSCOIN yang kami anchor 24 Sep (blok 132955030/132955788) jatuh tempo → **+1,5 bps net MENANG** dan **−146,3 bps net RUGI**; `WR 50 %`, net rata-rata **−72,4 bps**, **n = 2** (tidak ada satu pun uji statistik yang boleh dijalankan di atasnya). Harga masuk dibaca dari **rekaman** (`entry_ref` ikut `decisionHash`), bukan dihitung ulang; "belum waktunya" punya status sendiri dan tidak ikut agregat; stop+target di bar yang sama = `AMBIGU`. Rinci: `vault/09` §4b |
| Lapisan desk penuh (debat antar-desk) | ⬜ spesifikasi ditulis (`vault/06-Keputusan.md` F-D04), kode belum |
| Eksekusi | ⬜ **paper on purpose** — tidak ada dana pengguna, tidak ada order, tidak ada yang bisa rugi |
| Deploy ke chain 97 | ✅ **terverifikasi dari chain 24 Sep** — `0xdd162afb5f5f92d5092f845A93660e3B38259330`; bytecode 4748 B identik dengan build lokal; `anchor()` dari agen terpisah sukses (gas 302.011); event `Anchored` ter-indeks dengan topic2 = alamat agen; **rem on-chain terbukti** (setelah revoke → revert, setelah relist → pulih). Detail + cara mengulang: `vault/07-Deploy-97.md` |
| Fasilitator x402 sendiri | ⬜ settlement-nya terbukti di fork (31 test, chain 97 & 56); jalur HTTP `402` belum pernah dieksekusi |

Lihat `vault/05-Belum-Terbukti.md` untuk daftar lubang yang masih menganga dan cara menutupnya.

## Ruang lingkup folder ini

Hanya jalur **AI Agents / agentic trading**. Tidak ada apa pun soal kredensial, Open Badges,
e-course, atau jalur lain di sini — aturan dan alasannya ada di `vault/README.md`.

## Cara menjalankan

```
forge test -vv                                    # 21 test
python -u tools/screen_universe.py --windows     # corong penolakan dari dataset
python -u tools/bars.py BNBUSDT --days 400       # seberapa dalam deret harga yang benar2 kita punya
python -u tools/direction.py --top 5 --emit      # arah + ④ + entry/stop/ukuran/horizon (butuh kunci Jev utk model; --no-model utk deterministik, --no-security utk offline)
python -u tools/security_gate.py --emit          # bidang ④ saja: honeypot/can_not_sell dari 2 sumber
python -u tools/backtest.py --mom-only --flip    # aturan yang sama, arah dibalik: tetap kalah (lihat vault/09)
python -u tools/anchor.py --dry-run              # apa yang AKAN dikirim ke chain 97 (nol transaksi)
python -u tools/anchor.py --verify               # BACA ULANG 11 anchor dari chain: tanpa kunci, tanpa gas
python -u tools/ledger.py                        # apakah posisi yang di-anchor menang/kalah? (atau: belum jatuh tempo)
python -u tools/dune_flow.py --window 14         # agregat aliran kerumunan dari Dune (1 kueri; cache di data/)
python -u tools/flow_test.py                     # jalankan uji yang TERKUNCI di vault/10 - bukan variannya
python -u tools/test_decode_anchor.py            # 13 uji offline parser retur (tanpa network)
python -u tools/verify_deploy.py                 # baca ulang keadaan chain, bukan keluaran forge
```

Sebelas keputusan arah sudah masuk chain — **2 `Enter` dan 9 penolakan**, dan keduanya dihitung
dari `decisionHash` yang sama dengan file di repo ini: `decisions/direction-*.jsonl`
(di-commit sejak 25 Sep, karena `decisionHash`-nya tidak dapat dibangun ulang — lihat komentar
`.gitignore`) vs `getAnchor(id)` di `0xdd162afb…`. Nomor blok dan hasil pencocokan word-per-word
ada di `vault/07-Deploy-97.md`.

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

Mulai dari `vault/00-Mulai.md`. Angka-angka di `vault/02-Ambang.md` punya `file:line` asal-usul
dan tanggal diverifikasi — kalau sebuah angka tidak punya keduanya, ia bukan ambang, dia dugaan.

MIT.

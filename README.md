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
| Perekam universe point-in-time | ✅ jalan; 34 snapshot / **19 jendela jam** (34 baris ≠ 34 jam: ada pengulangan dari masa dua loop menulis bersamaan — n yang sah adalah jumlah jendela); universe **140 baris** sejak 04:58Z (GMGN rank 100 = langit-langit server, + 40 pool GT); sha256 per snapshot diverifikasi ulang, dirantai lewat `universe/manifest.txt` |
| Penyaring + hasil penolakan | 🟡 berjalan; **136 token** punya hasil forward, **kohort "lolos" masih 0** (harga pool baru tercatat sejak 22 Sep 08:00Z) |
| Lapisan keputusan deterministik | 🟡 `tools/decide.py`: snapshot → `decisionHash` + `gatesHash` + `snapshotHash`, calldata terverifikasi (`cast sig` = `0xdc6a1ac2`). **Memisahkan "ditolak karena risiko terukur" dari "tidak dinilai karena data tidak ada"** (terukur: 37 dan 13 dari 90) |
| Lapisan penilai (model) | 🟡 **opsional dan bisa dicabut** (`--judge none|auto|jev|openai`, default `none`). Terukur 23 Sep: 1 panggilan = $0,00002407, 0,43s, `jev-1.13.0`; veto **satu arah** (hanya boleh membatalkan ENTER) dan hasilnya masuk `decisionHash` |
| Lapisan desk penuh (debat antar-desk) | ⬜ spesifikasi ditulis (`vault/06-Keputusan.md` F-D04), kode belum |
| Eksekusi | ⬜ **paper on purpose** — tidak ada dana pengguna, tidak ada order, tidak ada yang bisa rugi |
| Deploy ke chain 97 | ⬜ skrip ada, **belum pernah dijalankan**, belum ada address publik |
| Fasilitator x402 sendiri | ⬜ settlement-nya terbukti di fork (31 test, chain 97 & 56); jalur HTTP `402` belum pernah dieksekusi |

Lihat `vault/05-Belum-Terbukti.md` untuk daftar lubang yang masih menganga dan cara menutupnya.

## Ruang lingkup folder ini

Hanya jalur **AI Agents / agentic trading**. Tidak ada apa pun soal kredensial, Open Badges,
e-course, atau jalur lain di sini — aturan dan alasannya ada di `vault/README.md`.

## Cara menjalankan

```
forge test -vv                                    # 21 test
python -u tools/screen_universe.py --windows     # corong penolakan dari dataset
```

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

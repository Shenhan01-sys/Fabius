"""Tulis part note + konsep + template + script perawatan vault Fabius.

Dipisah dari `migrate_vault.py` supaya pemindahan konten lama (yang tidak boleh berubah) tidak
bercampur dengan penulisan konten baru (yang memang harus ditulis). Dua operasi berbeda, dua
resiko berbeda: yang satu bisa merusak fakta, yang lain cuma bisa menulis fakta yang salah.

Setiap halaman baru menyebut perintah yang mencetak angkanya. Angka tanpa perintah = tanda "belum
diukur", bukan angka.
"""
import os
# Windows: cmd.exe default cp1252 dan glyph yang kami cetak (`①④⑥` di arah, `⚠` di laporan)
# bukan bagian dari yang di-hash - jadi encoding stdout yang disetel, bukan stringnya.
# Tanpa ini, `print` bisa pecah DI TENGAH tabel dan separuh hasilnya terbaca seperti laporan penuh.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass  # stdout tanpa reconfigure (mis. tertangkap harness) = biarkan apa adanya

VAULT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = {}

P["README.md"] = """---
tags: [reference]
---

# README — vault Fabius

Dua kebiasaan yang membuat folder ini masih layak dipercaya:

1. **Angka dari perintah, bukan dari ingatan.** Setiap jumlah, alamat, gas, atau tanggal di sini
   harus bisa direproduksi dari dalam repo. Kalau halaman dan run berbeda, **run menang** —
   perbaiki halamannya. Lihat [[Conventions]] §2 dan [[07-Testing/01 - Test Commands]].
2. **Koreksi tidak dihapus, dipajang.** Kami salah beberapa kali di proyek ini (menyimpulkan
   "perekam mati 24 jam" dari salinan lokal yang tertinggal 78 commit; menyimpulkan "calldata
   salah" dari alat perbandingan yang itself rusak). Semuanya ada di
   [[00-Overview/05 - Corrections]], lengkap dengan apa yang membuktikannya. Vault yang tidak
   punya halaman koreksi biasanya bukan vault yang benar — cuma vault yang malu.

Mulai dari [[START-HERE]]. Perawatan: `python scripts/sync_vault.py` lalu
`python scripts/check_links.py` (target `Broken: 0`).
"""

P["00-Overview/02 - Business Process.md"] = """---
tags: [overview, "O2"]
---

# 02 - Business Process

**Bagian dari:** [[00-Overview/00 - Hub Overview]]
**Sumber:** `tools/x402_gate.py`, `tools/x402_client.py`, `docs/agent-card.json`,
`05-Ecosystem/02 - x402 Payment.md`

**Ringkas:** Fabius menjual **bukti yang bisa diperiksa**, bukan sinyal. Ada dua permukaan: agen
lain membayar per permintaan lewat x402 untuk mendapat ringkasan keputusan + statistik; manusia
biasa membuka satu halaman untuk menilai satu token sebelum ia mengirim uang ke sana. Uang tidak
pernah mampir ke custody kami — tidak ada deposit, tidak ada penarikan.

**Poin kunci:**
- Pelanggan 1 (agen): `GET /vault/latest` → `402` + `accepts[]` → bayar 1.000 atomic (0,001) →
  dapat isi + `PAYMENT-RESPONSE`. Satu pembayaran nyata sudah terjadi di 97 (tx `0xb6093e59…`).
- Pelanggan 2 (manusia): "surat keputusan untuk token X" — honeypot 2 sumber, kedalaman riwayat,
  likuiditas vs ukuran keluar, dan **apakah kami menolak menilai**. Baris terakhir itu yang tidak
  berani ditulis alat lain, dan bisa dibuktikan karena ter-anchor.
- Bayar-per-keputusan, **gratis saat abstain**: insentifnya sejalan — kami dihukum kalau asal bunyi.
- Skema "yang datang lebih awal dapat untung lebih besar" **kami tolak desainnya**: tidak ada
  sumber kas, jadi imbal hasil peserta awal cuma transfer dari peserta belakangan. Kurva harga
  boleh di sisi biaya (pembeli awal bayar lebih murah), tidak di sisi imbal hasil.
- Revenue split on-chain (pola `bps hanya boleh turun`) sudah ada di proyek lain kami sebagai bukti
  konsep; untuk Fabius belum di-deploy — jangan ditulis seolah punya.

**Detail:**
- Yang belum: hosting endpoint publik ([[05-Ecosystem/03 - Discovery Gap]]), halaman FE
  ([[08-Backlog/01 - Backlog]] P3), dan bukti bahwa ada agen **asing** yang membeli (sampai sekarang
  pembelinya program kami sendiri — dan itu yang boleh diklaim).
- Semua settlement testnet; token pembayaran koin demo milik sendiri.

**Terkait:** [[00-Overview/01 - Briefing]] · [[10-Submissions/01 - Claims Cheat Sheet]]
"""

P["00-Overview/04 - Run It.md"] = """---
tags: [overview, "O4"]
---

# 04 - Run It

**Bagian dari:** [[00-Overview/00 - Hub Overview]]
**Sumber:** semua perintah di halaman ini pernah dijalankan; keluarannya di `07-Testing/`

**Ringkas:** satu halaman untuk menjalankan dan memverifikasi Fabius dari clone. Tidak ada kunci,
tidak ada dana, tidak ada server yang harus nyala untuk membuktikan klaim utamanya.

**Poin kunci:**

```bash
# 0. prasyarat: foundry (forge), python 3.12 + eth_account/eth_abi/eth_utils
git clone https://github.com/Shenhan01-sys/Fabius && cd Fabius
git submodule update --init --recursive          # vendor/: OZ + forge-std

# 1. kontrak & angka uji
forge test                                       # 21 DecisionAnchor (profil default, shanghai)
FOUNDRY_PROFILE=fork forge test --fork-url bscTestnet      # 63 lulus, termasuk 9 fork settlement x402
FOUNDRY_PROFILE=fork forge test --match-contract ExecutionVaultTest   # 18 jalur eksekusi

# 2. klaim inti, dibaca ulang tanpa kunci dan tanpa gas
python -u tools/anchor.py --verify               # cocok / BEDA / BELUM DI-ANCHOR

# 3. siklus agen
python -u universe/record_bsc_universe.py        # snapshot universe (satu tarikan)
python -u tools/direction.py --top 5 --emit      # arah + gerbang ①④⑥ + hash
python -u tools/security_gate.py --emit          # ④ dari dua sumber
python -u tools/ledger.py                        # nilai posisi jatuh tempo (atau: belum)

# 4. angka riset
FOUNDRY_PROFILE=fork forge build && python -u tools/backtest.py --mom-only --flip
python -u tools/whale_sweep.py --days 90         # butuh DUNE_API_KEY
```

**Detail:**
- `bscTestnet` = alias di `foundry.toml` → **publicnode**, bukan drpc. Alasan: drpc sehat untuk
  `eth_call` tapi menolak state per-blok yang diminta `--fork-url` (terukur: `Unknown block`).
- Perintah `x402_deploy/x402_gate/x402_client/exec_deploy/execute_live` butuh `.agent.env`
  (tidak di-commit). Gateway sementara berjalan di mesin kami — lihat
  [[05-Ecosystem/03 - Discovery Gap]].
- Dune: `set DUNE_API_KEY=…` (kredit per kueri terbaca di `execution_cost_credits`).

**Terkait:** [[Quick-Reference]] · [[07-Testing/01 - Test Commands]]
"""

P["00-Overview/05 - Corrections.md"] = """---
tags: [overview, "O5"]
---

# 05 - Corrections

**Bagian dari:** [[00-Overview/00 - Hub Overview]]
**Sumber:** keluaran perintah, bukan perasaan. Kolom terakhir = cara mereproduksinya.

**Ringkas:** apa yang kami nyatakan, yang ternyata salah, dan apa yang membuktikannya. Dikumpulkan
di satu tempat supaya "sudah clear?" tidak pernah lagi dijawab dari ingatan.

| tanggal | yang kami tulis | yang sebenarnya | bagaimana ketahuan |
|---|---|---|---|
| 25 Sep | "cron GitHub tidak dipersenjatai" (berdasarkan `GET /schedule` 404) | cron **hidup**, cuma tidak disiplin: `state=active` dan Actions mengirim snapshot sendiri beberapa menit setelah kalimat itu ditulis | riwayat jalanan (`gh run list`), bukan satu respons |
| 25 Sep | "settlement x402 terbukti di fork 97/56, tinggal pakai" | perintah fork-nya menunjuk RPC yang **sudah pensiun**; tidak seorang pun (termasuk kami) bisa menjalankan buktinya | aku menjalankan ulang perintah yang tertulis di README sendiri |
| 26 Sep | "16 test lulus di fork" untuk klaim di README | angka itu benar, tapi **dokumen tidak menyebut** bahwa endpoint dokumentasinya mati | sama |
| 27 Sep | "perekam ⑦ mati 24 jam" | lubang nyata ±6 menit. Yang basi adalah **salinan lokalku** (78 commit tertinggal) | `git fetch` + `git log origin` — lihat [[Concepts/Stale Local Copy]] |
| 27 Sep | "calldata kitalah yang salah (nested tuple)" | verdiknya kubangun di atas alat yang menghitung keccak dari string berisi kata `tuple` — bukan bentuk kanonis. Selector kami **benar** | alatnya kuperbaiki (rekursi komponen) lalu dibandingkan ulang |
| 27 Sep | "smart money menang di 30 hari" (sempat terbaca sebagai temuan) | tetap **belum** apa-apa: panel dipilih oleh label yang diberikan setelah sejarahnya terjadi | aturan yang kami tulis sendiri di `06-Results/06` §2 |
| 27 Sep | assertion "biaya round-trip > 400 bps" | salah hitung skala kami (0,6 % = 60 bps); terukur **59 bps** | test gagal → yang dikoreksi tesnya, bukan angkanya |
| 27 Sep | `git add -A` di repo induk (2×) | ikut menelan berkas sesi lain ke commit-ku | `git show --stat`; dipecah ulang, tidak ada yang hilang |

**Detail:** klaim yang ditarik juga meninggalkan jejak di halaman aslinya (banner koreksi), bukan
dihapus senyap — itu bedanya vault dengan brosur.

**Terkait:** [[Conventions]] · [[Concepts/Stale Local Copy]] · [[06-Results/03 - Not Yet Proven]]
"""

P["00-Overview/06 - Roadmap.md"] = """---
tags: [overview, "O6"]
---

# 06 - Roadmap to the Deadline

**Bagian dari:** [[00-Overview/00 - Hub Overview]]
**Sumber:** [[08-Backlog/01 - Backlog]] · tenggat resmi 30 Sep **23:59 WIB**

**Ringkas:** sisa waktu dipakai untuk membuat klaim bisa diperiksa orang lain, bukan untuk menambah
fitur yang tidak bisa diverifikasi.

**Poin kunci (urutan, dengan apa yang didapat per langkah):**

| hari | kerja | selesai terlihat sebagai |
|---|---|---|
| 27 | P1 eksekusi nyata di 97 (top-up gas → deploy → 1 posisi buka&tutup) | tx `status=1`, `openPositionOf` terbaca, realized PnL dari event |
| 27–28 | P4 `seats.py` (5 kursi + rotasi di atas `seat_eligible`) | satu siklus draft kursi ter-anchor, alasan rotasi tercatat |
| 28 | P2 host gateway + P3 FE (builder pakai Vercel) | URL kartu agen bukan localhost; orang awam bisa lihat satu keputusan |
| 28–29 | P5 Uji A horison pendek (prospektif) | angka whale **tanpa** lookahead, walau n kecil |
| 29 | video 5 menit + README + form (`03 - Form Fields`) | naskah per scene, alamat ditempel dari repo |
| 30 | submit | repo publik, contract resolve di BscScan, tim terdaftar di Luma |

**Detail / risiko yang sudah kelihatan:**
- P1 bisa gagal bukan karena kode tapi karena gas testnet — guard `exec_deploy.py` sengaja menolak
  sebelum mengirim; top-up tower adalah jalurnya.
- Kalau Uji A tidak sempat terkumpul: jangan tulis apa pun yang menyiratkan "whale diuji bersih".
- Yang **tidak** masuk roadmap: Greenfield (bukan bagian cerita agen resmi, dan decision-log
  per-keputusan pola terburuk untuk objek storage), mainnet (testnet sah + dana asli bukan harga
  yang boleh diasumsikan), dan mengejar "edge" baru tanpa jendela validasi.

**Terkait:** [[08-Backlog/01 - Backlog]] · [[START-HERE]]
"""

P["01-Agent/A2 - Decision Spine.md"] = """---
tags: [agen, "A2"]
---

# A2 - Decision Spine

**Bagian dari:** [[01-Agent/00 - Hub Agent]]
**Sumber:** `tools/direction.py`, `tools/decide.py`, `tools/anchor.py`, `tools/ledger.py`

**Ringkas:** lima tahap yang selalu berurutan, dan setiap tahap menghasilkan artefak yang bisa
dibaca orang lain — bukan log di kepala agen. Rekam → saring → putuskan → anchor → nilai.

**Poin kunci:**
1. **Rekam**: `universe/bsc-universe.jsonl` + `universe/wallet-flow.jsonl`, sha256 per baris,
   timestamp commit GitHub ([[03-Data/01 - Dataset]], [[03-Data/D2 - Wallet Flow]]).
2. **Saring**: gerbang ① riwayat bar, ④ keamanan, ⑥ kapasitas keluar — hasilnya
   `seat_eligible` + `seat_blockers` dan ikut masuk `gatesHash` (`direction.apply_gates`).
3. **Putuskan**: `side`/entry/stop/target/ukuran/horizon + dua rezim keluar
   ([[04-Tools/TL2 - direction]]).
4. **Anchor**: `decisionHash` + `gatesHash` + `snapshotHash` ke `DecisionAnchor` di 97; umur snapshot
   ikut di-hash supaya keputusan di atas data basi tetap terbaca basi.
5. **Nilai**: `ledger.py` menutup dari rekaman (bukan dihitung ulang), memisah `BELUM JATUH TEMPO`
   dan `AMBIGU` ([[04-Tools/TL5 - ledger]]).

**Detail:**
- Urutan tidak bisa diputar: tidak ada jalur di mana hasil tahap 5 mengubah tahap 4 (anchor tidak
  pernah ditarik/ditulis ulang — itu satu-satunya fungsi angka ini).
- Model LLM ada di tahap 3 tapi posisinya **di bawah** gerbang ([[Concepts/One-Way Gate]]).
- Sebagian besar keputusan agen adalah `ABSTAIN` (3 Enter + 14 Abstain, `countByVerdict`) — itu keluaran, bukan kegagalan.

**Terkait:** [[01-Agent/A3 - One-Way Gates]] · [[Concepts/Anchored Before Outcome]]
"""

P["01-Agent/A3 - One-Way Gates.md"] = """---
tags: [agen, "A3"]
---

# A3 - One-Way Gates

**Bagian dari:** [[01-Agent/00 - Hub Agent]]
**Sumber:** `tools/judge.py` §1, `tools/direction.py::apply_gates`, `contracts/ExecutionVault.sol`

**Ringkas:** aturan tunggal — komponen penilai hanya boleh mengurangi. Tertulis di tiga lapisan
sekaligus supaya tidak bisa dibypass di hilir.

**Poin kunci:**
- `judge.py`: model hanya boleh memveto/mengecilkan; kalau model bilang arah berbeda dari data,
  hasilnya turun ke `OBSERVASI` dan `conf` dipotong, bukan posisi dibuka.
- `direction.apply_gates`: ④ `BLOCKED` → `side=flat` (satu-satunya hak mematikan arah);
  `UNMEASURED/DISAGREE` → kehilangan hak kursi, arah boleh tetap tertulis.
- `ExecutionVault`: menolak `decisionHash`/`snapshotHash` kosong; menolak saat `killSwitch`;
  menolak melebihi cap — dan `HARD_CEILING` **memotong** perintah pemilik, bukan menolaknya.
- Bukti perilaku, bukan niat: saat Jev bilang `short` untuk dua kandidat yang `bar < 720`,
  keputusannya tetap `flat` dan itu tercetak di keluaran (`06-Results/04`).

**Detail:** kebalikan yang harus diwaspadai — kegagalan pengukur yang diperlakukan seperti hasil
bersih ([[Concepts/Unmeasured Is Not Clean]]).

**Terkait:** [[Concepts/One-Way Gate]] · [[04-Tools/TL3 - security_gate]]
"""

P["02-Contracts/C3 - ExecutionVault.md"] = """---
tags: [kontrak, "C3"]
---

# C3 - ExecutionVault

**Bagian dari:** [[02-Contracts/00 - Hub Contracts]]
**Sumber:** `contracts/ExecutionVault.sol`, `test/ExecutionVault.t.sol` (18 test lulus)

**Ringkas:** pencatat posisi yang **dieksekusi** lewat pool. Harga masuk/keluar datang dari hasil
swap, bukan dari angka yang agen tulis; PnL dibukukan di kontrak dan boleh negatif.

**Poin kunci:**
- `openLong(asset, quoteIn, decisionHash, snapshotHash)` / `openShort(asset, assetQty, …)` /
  `close(asset)`; posisi keyed per aset token; satu posisi per aset (`AlreadyOpen`).
- Hanya `agent` yang bisa buka/tutup → `NotAgent`; **owner tidak punya jalan pintas** (teruji).
- Plafon: `dailyCap` (default 5 unit), `maxPositionQuote` (1 unit), `HARD_CEILING = 10` — owner
  menaikkan ke 1.000 tetap dipotong ke 10 (teruji: `dailyCap() == 10`).
- `NoAnchorHash`: posisi **tidak bisa lahir** dari keputusan yang tidak di-anchor.
- Short = jual inventaris sendiri, beli kembali saat menutup → `NeedInventory` kalau tidak ada.
  Konsekuensi: saldo quote vault memang **turun** saat menutup short yang untung; ukuran PnL adalah
  `realizedQuote`, bukan saldo (kesalahan konsep yang sempat bikin tesku salah, lalu kucatat).
- Gas dipakai per panggilan dihitung di kontrak (`startGas - gasleft()`) dan ikut di event
  `Closed` — bukan `gasleft()` mentah yang bukan biaya.
- Reset plafon harian terjadi **sebelum** pemeriksaan budget. Bug urut ini ditemukan test, dan
  sekarang ada test sendiri yang memegangnya.

**Detail:** bug yang sudah dikoreksi dicatat di komentar kontrak (bukan dihapus) supaya pembaca
mengerti kenapa urutannya penting. Deploy & posisi nyata: [[08-Backlog/01 - Backlog]] P1.

**Terkait:** [[02-Contracts/C4 - DemoPair and DemoAsset]] · [[Quick-Reference]]
"""

P["02-Contracts/C4 - DemoPair and DemoAsset.md"] = """---
tags: [kontrak, "C4"]
---

# C4 - DemoPair and DemoAsset

**Bagian dari:** [[02-Contracts/00 - Hub Contracts]]
**Sumber:** `contracts/DemoPair.sol`, `contracts/DemoAsset.sol`

**Ringkas:** venue x·y=k (fee 30 bps) plus aset demo 6 desimal. Dibikin sendiri dengan alasan
spesifik, bukan karena malas memakai DEX.

**Poin kunci:**
- Kenapa bukan pooltestnet orang: kalau kami swap ke likuiditas asing lalu menulis "ini slippage
  kami", angka itu bukan milik kami — bisa habis, kosong, atau digeser pihak lain.
- Yang **tidak** diklaim: kurva ini mewakili pasar meme sungguhan. Yang dibuktikan: proses eksekusi
  (harga dari kontrak, bukan dari kami) dan **besarnya ongkos**.
- Biaya round-trip terukur di sini: **59 bps** pada posisi 1 unit (`test_round_trip_...`, mencetak
  `BIAYA ROUND-TRIP TERUKUR`). Ini angka yang menjawab "$5 layak tidak" dari sisi ongkos.
- `costOfBuy(want)` dan `spotPrice()` view → laporan bisa memprediksi dampak sebelum masuk;
  `bootstrap()` sekali saja, setelah itu likuiditas tidak bisa digeser dari luar.
- `DemoAsset` sengaja ERC20 polos, bukan token ber-permit: OZ 5 menarik `Bytes.sol` (`mcopy`,
  Cancun) lewat jalur permit, dan itu akan memaksa seluruh proyek naik target EVM — padahal
  `DecisionAnchor` sengaja ditahan di `shanghai` karena klaim bytecodenya terikat ke sana.

**Terkait:** [[02-Contracts/C3 - ExecutionVault]] · [[09-Inbox/Session-2026-09-26-27]]
"""

P["02-Contracts/C5 - Vendored x402 Sources.md"] = """---
tags: [kontrak, "C5"]
---

# C5 - Vendored x402 Sources

**Bagian dari:** [[02-Contracts/00 - Hub Contracts]]
**Sumber:** `contracts/vendor/x402/VENDORED.json`, `docs/upstream-x402/`,
`_research/vendored_x402.py`

**Ringkas:** sumber x402 upstream ada di repo ini sebagai **bacaan**, dengan sha256 tercatat. Yang
kami panggil adalah kontrak kanonis yang sudah ter-deploy, bukan hasil kompilasi vendor ini.

**Poin kunci:**
- Upstream: `github.com/coinbase/x402` @ commit `dd927a26cfefc98c24b3ec38b3a8f204dad0c60d`
  (bukan `main` — vendor yang bergerak bukan vendor, itu dependensi hantu).
- `interfaces/ISignatureTransfer.sol` ikut dikompilasi (interface-only, aman untuk shanghai);
  dua proxy implentasinya ditaruh di `docs/upstream-x402/` dan **tidak** dikompilasi: mereka memakai
  `mcopy`, dan memaksanya masuk akan merusak profil default (terjadi nyata: 4 error kompilasi di
  `vendor/openzeppelin/.../Bytes.sol`).
- Panggilan nyata memakai interface kami sendiri: `contracts/vendor/x402/IX402ExactPermit2Proxy.sol`.
  Selector **diturunkan dari tipe parameternya**, tidak ditulis tangan.
- Audit integritas: `python _research/vendored_x402.py verify` (hash disk vs manifest) dan
  `compare` (menunjukkan salinan POC kami identik upstream — jadi bukti lama tidak jalan di sumber
  yang disunat).
- `.gitattributes` memberi `-text` ke jalur vendor & dataset. Tanpa itu git menormalisasi LF→CRLF
  di Windows dan membuat klaim "verbatim"/hash gagal di mesin orang lain.

**Terkait:** [[05-Ecosystem/02 - x402 Payment]] · [[07-Testing/T4 - x402 Fork Suite]]
"""

P["03-Data/D2 - Wallet Flow.md"] = """---
tags: [data, "D2"]
---

# D2 - Wallet Flow (bidang ⑦)

**Bagian dari:** [[03-Data/00 - Hub Data]]
**Sumber:** `universe/record_wallet_flow.py`, `.github/workflows/wallet-flow.yml`,
`_research/panel_stats.py`

**Ringkas:** perekam aliran smart money & KOL di BSC. Ini satu-satunya bidang yang **tidak bisa**
disusulkan, jadi ia diperlakukan sebagai aset yang menetes tiap jam.

**Poin kunci:**
- Sumber: GMGN `user/smartmoney` + `user/kol`. Terukur: **100 transaksi per panggilan**, jendela
  lihat **8–13 menit**, dan **semua parameter paging diabaikan server** (`offset`/`page`/`end_ts`
  → head yang sama, overlap 98/100). Kesimpulan pentingnya: **tidak ada riwayat**; yang lewat = hilang.
- Field yang disimpan: maker (dompet), `base_address`, side, `is_open_or_close`, `buy_cost_usd`,
  `price_usd`, `timestamp`, `transaction_hash`, `maker_info.tags` — tag panel ikut disimpan karena
  **keanggotaan panel adalah pilihan GMGN**, dan itu bias yang harus bisa ditunjuk.
- Cadence: cron per-jam tidak cukup → **rantai yang men-dispatch dirinya sendiri** (loop ~4,6 jam,
  commit tiap ±4 menit) + `schedule` penyelamat. Dua pagar: anti-tumpang-tindih & batas umur 40 jam.
- `cancel-in-progress: true` dan `actions: write` bukan hiasan: tanpanya satu jalanan menggantung
  mengantrikan sisanya, dan dispatch-diri gagal diam-diam (terukur, `conclusion=failure`).
- Status 27 Sep: **7.137 transaksi unik / 322 maker / 604 token / 10,14 jam**; 103 maker ≥20 tx.
  Rekamannya di `universe/wallet-flow.jsonl`, berantai lewat
  `universe/wallet-flow-manifest.txt` (sha256 berkas + ekor + `usia_aliran_jam`).
- Jangan ulangi kesalahan 27 Sep: jumlah baris di **disk lokalmu** bukan keadaan sistem —
  `git fetch` dulu ([[Concepts/Stale Local Copy]]).

**Terkait:** [[06-Results/06 - Pre-registration Horizon]] · [[04-Tools/TL7 - measurement harness]]
"""

P["03-Data/D3 - Price Depth.md"] = """---
tags: [data, "D3"]
---

# D3 - Price Depth per Sumber

**Bagian dari:** [[03-Data/00 - Hub Data]]
**Sumber:** `tools/bars.py`, `universe/record_bsc_universe.py`

**Ringkas:** "seberapa jauh ke belakang kita bisa menghargai sebuah aset sendiri" menentukan apa
yang boleh diuji sama sekali. Angkanya diukur dengan menarik, bukan membaca dokumen.

**Poin kunci:**

| sumber | kedalaman | kunci | peran |
|---|---|---|---|
| Aster `fapi/v1/klines` (BNB-native perp) | **9.599 bar 1 jam ≈ 400 hari** | tanpa API key | harga forward untuk backtest & penilaian ⑦ |
| Hyperliquid `candleSnapshot` | 5.001 bar ≈ 208 hari | tanpa key | pembanding silang (chain sendiri, bukan BNB) |
| GMGN `token_kline` | mentok 1.000 bar ≈ 41,6 hari; **0 bar untuk token gas** | privat | tidak cukup untuk walk-forward |
| GeckoTerminal pools | 1.000 bar; pool baru ±30 bar | demo/privat | universe & likuiditas, bukan deret |

- Kapasitas server: **1.500 bar/panggilan** (limit 3.000/5.000 ditolak `code -1130`); kedalaman
  didapat dari **paging**, bukan dari satu permintaan besar.
- Cache per (simbol, interval) + meta (endpoint, halaman, sha256) supaya "data dari mana" bukan
  pertanyaan terbuka. `save()` memaksa meta lengkap **dan menandai pertentangan internal**
  (pernah: klaim `pages: 1` untuk deret 7 halaman).
- Ambang yang mengikat: `NEED_BARS=2400` (5-fold walk-forward), `MIN_BARS_TINY=720` (30 hari =
  layak dinilai, tidak layak diklaim sebagai edge).
- Batas yang harus ikut disebut: yang bisa kami hargai sendiri cuma aset **ber-kontrak perp** →
  ada survivorship di setiap uji ⑦ (lihat `06-Results/06`).

**Terkait:** [[06-Results/02 - Thresholds]] · [[03-Data/D4 - Dune]]
"""

P["03-Data/D4 - Dune.md"] = """---
tags: [data, "D4"]
---

# D4 - Dune (riwayat wallet & agregat aliran)

**Bagian dari:** [[03-Data/00 - Hub Data]]
**Sumber:** `tools/whale_sweep.py`, `_research/probe_dune_*.py`, `_research/diag_*.py`

**Ringkas:** Dune memberi kami hal yang GMGN tidak bisa: **masa lalu**. Dan mengambil kredit sebagai
gantinya. Halaman ini berisi angka API yang terukur, karena tiga asumsiku tentang API ini salah.

**Poin kunci:**
- Populasi terukur: `dex.trades` `blockchain='bnb'` = **5.274.783 swap dalam 1 jam terakhir**;
  205.875 swap / 20.607 wallet di jam penuh terakhir.
- **Lag ±1 jam** (jam berjalan cuma 18 swap vs jam penuh 205.875) → Dune **bukan** jalur keputusan
  untuk horizon 4 jam; dia jalur sejarah/kelompok.
- Kredit **bisa dibaca**: `execution_cost_credits` di endpoint status. Terukur: agregat 90 hari
  dengan join `tokens.erc20` = **1,259 kredit / ±11 detik**. Bandingkan dengan kueri yang
  **mengirim baris**: 10 hari = 503 detik — yang mahal itu mengangkut baris, bukan berpikir.
- Dialek = **Trino**: `now()` ya; `current_timestamp()` **tidak**; `INTERVAL '1' DAY` (berkutip).
- **`from_hex('0x…')` tidak error — hanya tidak pernah cocok.** Ini yang membuat kueri pertamaku
  membalas 0 baris dan nyaris kusimpulkan "whale tidak trading". Semua sisi heks dinormalisasi +
  assert panjang 40.
- Paginasi: **tidak ada `next_offset`**; geser `offset` sendiri dan berhenti pada
  `total_row_count`. `limit=5000` membuat respons tanpa `rows` (kubaca salah sebagai
  "[TERPOTONG]"); pakai 1000.
- Kolom: `token_bought_address`/`token_sold_address`/`taker` (varbinary), `amount_usd`,
  `block_time`, plus join `tokens.erc20.symbol`. Nama yang kukarang (`token_bought`) tidak ada.
- Batas metodologis: barisnya punya `_updated_at` → masa lalunya bisa disusulkan. Jadi Dune sah
  untuk **statistik**, tidak sah jadi **saksi waktu** (saksi waktu tetap commit Actions + anchor).

**Terkait:** [[06-Results/06 - Pre-registration Horizon]] · [[Concepts/Point-in-Time vs Retro-updatable]]
"""

P["04-Tools/TL1 - judge.md"] = """---
tags: [perkakas, "TL1"]
---

# TL1 - judge.py

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/judge.py`, `06-Results/03 - Not Yet Proven.md` #13

**Ringkas:** penilai LLM yang **boleh dicabut**. Defaultnya `none` (gerbang deterministik); kalau
dinyalakan, ia hanya boleh mengurangi ([[01-Agent/A3 - One-Way Gates]]).

**Poin kunci:**
- Rantai provider: Jev/Typesafe System-One → cadangan OpenAI-compatible → `abstain`.
- `ask_jev(state, questions)` menerima pertanyaan **dari pemanggil**. Tanpa ini, `direction.py`
  menyiapkan `side_<SYM>` tapi `judge()` mengirim pertanyaan bakunya sendiri → kolom `model` kosong
  **sambil mencetak `ok=True`** (bug nyata 25 Sep: klaim terlihat seperti sudah memanggil model).
- Pertanyaan bertipe `noul` (bahaya) dipakai **satu arah**: veto boleh membatalkan, tidak pernah
  membuka. Output mentah disimpan biar keputusan bisa direproduksi tanpa model.
- Biaya: router promo terukur $0; jalur resmi $0,042/MTok masuk, keluar gratis — angka pihak
  ketiga, bukan harga yang kami janjikan.
- Belum terbukti: kalibrasi penilai (apakah vetonya memprediksi hasil). Diukur sebagai
  `06-Results/03` #13, statusnya masih terbuka.

**Terkait:** [[04-Tools/TL2 - direction]] · [[Concepts/One-Way Gate]]
"""

P["04-Tools/TL2 - direction.md"] = """---
tags: [perkakas, "TL2"]
---

# TL2 - direction.py

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/direction.py`, `06-Results/04 - Negative Results.md`

**Ringkas:** penghasil keputusan arah lengkap — `side`, entry, stop, target, ukuran risiko, horizon
— plus dua rezim keluar. Ia juga tempat gerbang kursi ditegakkan dan umur snapshot di-hash.

**Poin kunci:**
- Arah ditentukan **data kami sendiri** (gap SMA24 ± 1% searah ret24), bukan oleh model; model hanya
  boleh memveto/mengecilkan.
- Dua rezim: `stop-loss` hanya saat yakin (conf ≥ 0,6 dan |acf| terstruktur); sisanya `time-stop`
  keras 24 jam + exit-size ≤ 1% likuiditas. Alasan "jual saja saat 0" ditolak dengan ukuran: saat
  rug jualannya **ditolak kontrak** — dan itu sekarang diukur (`04-Tools/TL3`), bukan diandaikan.
- `apply_gates` menegakkan ①+④+⑥ → `seat_eligible` + `seat_blocker` (nama awalnya `apply_security`
  dan menetapkan kursi dari ④ saja → kolom "kursi" membesar; syaratnya yang disamakan ke namanya).
- Umur snapshot (`universe_age_h`) masuk `snapshotHash`: keputusan di atas data basi tetap terbaca
  basi **sampai ke hash-nya** — ini yang membuat klaim point-in-time tidak bisa disamarkan.
- Berkas keluar `decisions/direction-<UTC>Z.jsonl`; nama file pakai UTC (pernah lokal WIB sehingga
  "20260925" berisi data "2026-09-24T18:00Z").
- Status penting: **aturan yang dihasilkan alat ini sudah diuji dan rugi setelah ongkos**
  ([[06-Results/04]]) — jangan kutip keluarannya seolah sinyal.

**Terkait:** [[01-Agent/A2 - Decision Spine]] · [[04-Tools/TL5 - ledger]]
"""

P["04-Tools/TL3 - security_gate.md"] = """---
tags: [perkakas, "TL3"]
---

# TL3 - security_gate.py

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/security_gate.py`, `06-Results/03` #17

**Ringkas:** mengukur bidang ④ (honeypot / bisa dijual) untuk kandidat arah, dari **dua sumber**,
dengan empat status — dan `UNMEASURED` tidak dihitung bersih.

**Poin kunci:**
- Kenapa baru sekarang layak: jalur screen butuh 40 alamat/snapshot (terbukti tak terbayar); jalur
  arah ≤ 5 kandidat → 10 panggilan per siklus. Skala mengubah kesimpulan.
- GMGN `token/security` membalas 200 dengan `is_honeypot` **boolean** dan `can_not_sell`; GoPlus
  **tidak punya `can_not_sell`** sama sekali — dicatat sebagai ketiadaan field, bukan nol.
- Empat status: `OK` / `BLOCKED` / `DISAGREE` / `UNMEASURED`. `UNMEASURED` terpicu nyata
  (satu kandidat `is_honeypot=null`) → hak kursi dicabut.
- Dua sumber bisa **tidak sepakat** soal pajak jual (0,03 vs 0,0): ambang `DISAGREE` di ≥5 %,
  jadi kasus 3 % ini tetap `OK` **tapi tercatat** sebagai perbedaan sumber.
- Bentuk join heks antar sumber adalah sumber bug: `to_hex()` Trino kapital, perekar kecil
  (lihat [[04-Tools/TL7]]).
- Yang **tidak** dibuktikan ④: honeypot adalah milik **token spot**; ia membuktikan dasar harga
  perp tidak bisa disandera, bukan bahwa posisi perp bisa ditutup di venue-nya.

**Terkait:** [[Concepts/Unmeasured Is Not Clean]] · [[06-Results/03 - Not Yet Proven]]
"""

P["04-Tools/TL4 - anchor and verify.md"] = """---
tags: [perkakas, "TL4"]
---

# TL4 - anchor.py dan --verify

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/anchor.py`, `02-Contracts/02 - Deployed on 97.md`

**Ringkas:** dua pekerjaan yang berbeda: **mengirim** keputusan nyata ke chain, dan **membaca ulang**
trail itu tanpa memercayai kami. Yang kedua yang membuat vault ini berguna.

**Poin kunci:**
- `--dry-run` mencetak apa yang AKAN dikirim; tanpa flag itu ia kirim. Tidak ada mode "kirim semua
  tanpa laporan".
- Guard saldo dihitung pada **plafon gas × jumlah baris** (terburuk, bukan rata-rata) → siklus yang
  kurang dana berhenti dengan **nol transaksi terkirim**, jadi tidak pernah ada jejak setengah.
- `chainId` dibaca & dibandingkan **sebelum** menandatangani: kegagalan yang dicegah adalah
  menandatangani tx untuk chain yang tidak kita baca.
- `--verify`: `id = keccak(agen, decisionHash, snapshotHash, chainid)` dihitung ulang dari berkas
  repo → `getAnchor(id)` dibaca → **6 field** dibandingkan (termasuk `asset` dan `agent`).
  Nol kunci, nol gas → auditor bisa menjalankannya.
- Temuan kontrak yang mengubah alat kami: `getAnchor` untuk id tak dikenal **tidak revert** — ia
  mengembalikan struct nol. Klasifikasi "belum di-anchor" yang mencari kata `reverted` jadi cabang
  mati, dan 4 keputusan terbaru tercetak "BEDA" seolah buktinya rusak. Sekarang tiga keadaan:
  `cocok` / `BEDA` / `BELUM DI-ANCHOR`.
- Bug yang ditemukan tes parser: offset string pada retur dinamis dihitung **relatif ke awal
  struct**, bukan ke awal retur. Tiga hash tetap cocok, jadi `chain==lokal: YA` tercetak **sambil**
  `asset` terbaca sampah — yang salah adalah field yang tidak dibandingkan.

**Terkait:** [[Concepts/Anchored Before Outcome]] · [[07-Testing/T2 - forge anchor suite]]
"""

P["04-Tools/TL5 - ledger.md"] = """---
tags: [perkakas, "TL5"]
---

# TL5 - ledger.py

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/ledger.py`, `06-Results/07 - Matured Outcomes.md`

**Ringkas:** menilai prediksi yang sudah di-anchor — menang, rugi, `AMBIGU`, atau **belum waktunya**
— tanpa memberi alat ini cara untuk me-rebase masa lalu.

**Poin kunci:**
- `entry_ref` dibaca dari **rekaman** (ikut terikat `decisionHash` di chain), tidak dihitung ulang.
- `BELUM JATUH TEMPO` punya status sendiri + sisa jam dicetak, dan **tidak ikut agregat**.
- Stop vs target dicari **urutan sentuh**-nya; kalau keduanya mungkin di satu bar yang sama →
  `AMBIGU`, tidak dipilih yang menguntungkan.
- Dedupe pada **level peristiwa** (simbol, sisi, entry, bar masuk, horizon), bukan pada hash: hash
  beda tiap siklus karena memuat waktu generasi → tanpa pagar ini satu peristiwa pasar terhitung
  5 posisi dan `n` laporan membengkak tanpa informasi.
- Ongkos 20 bps RT dipakai sejak awal dan yang dilaporkan `net`.
- Hasil pertama (26 Sep): dua short MARSCOIN → **+1,5 bps MENANG** dan **−146,3 bps RUGI**;
  `WR 50 %`, rata-rata **−72,4 bps**, **n=2** → tidak ada uji statistik yang boleh dijalankan.

**Terkait:** [[06-Results/07 - Matured Outcomes]] · [[06-Results/02 - Thresholds]]
"""

P["04-Tools/TL6 - x402 gate and client.md"] = """---
tags: [perkakas, "TL6"]
---

# TL6 - x402 gate dan client

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/x402_gate.py`, `tools/x402_client.py`, `tools/x402_deploy.py`

**Ringkas:** server yang menagih dan klien agen yang membayar — keduanya milik kami, dan itu
dinyatakan sebagai bagian dari klaim, bukan disembunyikan.

**Poin kunci:**
- Bentuk wire diambil dari **specs pada commit yang sama dengan vendor kami** (`dd927a26…`), bukan
  dari tebakan: v2 memakai header `PAYMENT-REQUIRED` / `PAYMENT-SIGNATURE` / `PAYMENT-RESPONSE`
  (v1 `X-PAYMENT*`; keduanya diterima supaya klien lama tidak buta).
- Klien menandatangani **dua** EIP-712 authorization (Permit2 witness + EIP-2612 permit) dan tidak
  pernah mengirim transaksi; fasilitator (server) yang memanggil `settleWithPermit` di proxy
  kanonis `0x402085c2…`.
- Satu tempat contoh spec dan kontrak kanonis **bertentangan**: spec menulis `MaxUint256` untuk
  EIP-2612, sementara `settleWithPermit` me-revert `Permit2612AmountMismatch` kalau jumlah permit ≠
  tagihan. Perilaku kontrak yang menang, dan alasannya ditulis.
- Pembuktian bukan dari log server: tx, `status`, dan `balanceOf` dibaca ulang dari chain
  (pembeli 5.000.000 → 4.999.000 atomic = tepat tagihan; `payTo` 999.990,001 = 1.000.000 − 10 + 0,001).
- Jam: `validAfter` memakai jam laptop, proxy membandingkan ke `block.timestamp` → revert tanpa
  pesan. Perbaikan `now - X402_SKEW` (15 s) dengan alasannya, bukan angka keberuntungan.
- **Status sekarang: endpoint di `127.0.0.1`, dan `agent-card.json` menuliskannya apa adanya.**
  Lihat [[05-Ecosystem/03 - Discovery Gap]].

**Terkait:** [[05-Ecosystem/02 - x402 Payment]] · [[02-Contracts/C5 - Vendored x402 Sources]]
"""

P["04-Tools/TL7 - measurement harness.md"] = """---
tags: [perkakas, "TL7"]
---

# TL7 - Measurement Harness

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/backtest.py`, `tools/flow_test.py`, `tools/whale_sweep.py`,
`_research/check_garbled.py`, `_research/panel_stats.py`

**Ringkas:** alat pengukur bukan pencetak angka cantik. Setiap alat di keluarga ini membawa pager
yang sama: ambang dari kode live (bukan disalin), 1 sampel per peristiwa non-overlap, BH,
drop-best-fold, dan **penolakan untuk menyimpulkan** kalau cakupannya runtuh.

**Poin kunci:**
- `backtest.py`: aturan live dijalankan di 400 hari × 12 aset → rugi 12/12; `--mom-only` dan
  `--flip` ada supaya "siapa yang memproduksi nol" (gerbang atau isinya) bisa dibedakan.
- `flow_test.py` / `whale_sweep.py`: **pra-registrasi dulu** (`06-Results/05`, `06-Results/06`),
  baseline = (token, jam) acak, bukan nol; bootstrap deterministik `seed=0` supaya orang lain
  mengulang dan mendapat angka yang sama.
- Pagar cakupan: kalau < 1/4 token terpetakan, alat **menolak melapor**. Penyebabnya nyata: join
  heks kapital/kecil menjatuhkan 85/86 token dan tabelnya tetap tercetak rapi.
- Truncation diucapkan, tidak dibisikkan: `LIMIT`, halaman yang hilang, dan `[TERPOTONG]` dicetak;
  hasil parsial tidak boleh menyamar sebagai hasil penuh (cache entri diberi nama rev r2/r3).
- Bug yang berulang dan cara menghukumnya: `python -c` multi-baris di cmd.exe (empat kali), `ROOT`
  dihitung tiga tingkat (dua kali — sekarang setiap alat jalur meng-assert direktorinya),
  sisipan karakter CJK ke komentar Indonesia (empat kali), BOM dari `Set-Content -Encoding UTF8`,
  `print` yang crash di cp1252. Semua itu kini punya alat: `_research/check_garbled.py`
  (CJK/Hangul/fullwidth + BOM + print tak ter-encode) dan `forge test` untuk yang di kontrak.
- Angka yang dihasilkan alat ini adalah **satu-satunya** yang boleh dikutip halaman lain
  ([[Conventions]] §2).

**Terkait:** [[06-Results/00 - Hub Results]] · [[07-Testing/01 - Test Commands]]
"""

P["05-Ecosystem/01 - ERC-8004 Identity.md"] = """---
tags: [ekosistem, "E1"]
---

# 01 - ERC-8004 Identity

**Bagian dari:** [[05-Ecosystem/00 - Hub BNB Ecosystem]]
**Sumber:** `tools/x8004_register.py`, `docs/upstream-8004/`, `docs/agent-card.json`

**Ringkas:** agen Fabius terdaftar sebagai identitas **pada registry resmi BNB Chain**, bukan pada
tabel internal kami. Ini jawaban teknis untuk pertanyaan "bagaimana agen lain tahu kamu ada".

**Poin kunci:**
- Registry `IdentityRegistry` chain 97 = `0x8004A818BFB912233c491871b3d84c89A494BD9e`
  (`name()` = `AgentIdentity`, terverifikasi ada kode; 130 B = proxy).
- Varian `register()` ada tiga di upstream; kami **simulasikan lewat `eth_call` dulu** untuk tahu
  mana yang kontrak terima, baru kirim tx: `register(string)` → tokenId berikutnya **2494**
  (konsisten dengan penghitung indexer 8004scan ±2.452 agen di 97).
- Tx nyata: `0x33f47391…` `status=1`, gas 200.844. Verifikasi tidak percaya tx:
  `getAgentWallet(2494)` dan `ownerOf(2494)` dibaca dari registry → sama dengan alamat agen.
- Parser event kami sempat melaporkan `tokenId 0` untuk tx yang **sukses** — fallback "log pertama,
  topics[1]" mengambil `Transfer(from=0x0)`. Sekarang topik dihitung dari ABI vendor dan
  **tidak ada fallback**: kalau event tak ketemu, alatnya berhenti.
- ABI vendor: `docs/upstream-8004/` (`erc-8004/erc-8004-contracts @ b9e466c2…`, sha256 tercatat).
- Kartu agen `docs/agent-card.json` menunjuk endpoint x402 + berkas keputusan; berkas yang ditunjuk
  **benar-benar ditulis alatnya** (pernah menunjuk ke path yang tidak ada — kelas bug yang sama
  dengan pointer `docs/upstream-x402`).

**Terkait:** [[05-Ecosystem/03 - Discovery Gap]] · [[04-Tools/TL6 - x402 gate and client]]
"""

P["05-Ecosystem/02 - x402 Payment.md"] = """---
tags: [ekosistem, "E2"]
---

# 02 - x402 Payment

**Bagian dari:** [[05-Ecosystem/00 - Hub BNB Ecosystem]]
**Sumber:** `04-Tools/TL6`, `07-Testing/T4`, `docs/upstream-x402/`

**Ringkas:** agen membayar agen lain di BNB Chain lewat relasi pembayaran kanonis — dan bukti yang
kita punya adalah transaksi, bukan screenshot.

**Poin kunci:**
- Terjadi nyata di 97: tx `0xb6093e59…` `status=1`, gas 114.930; klien (0 BNB) menandatangani,
  fasilitator membayar gas, token demo `0xB11D9021…` berpindah **tepat** 1.000 atomic = tagihan.
- Sifat paksaannya dibuktikan di level kontrak (8 fork test terhadap proxy ter-deploy): pemanggil
  `settle()` tidak bisa memindahkan dana ke alamat lain, tidak bisa melebihkan jumlah, dan nonce
  tidak bisa dipakai ulang.
- Yang **belum**: jalur HTTP-nya berjalan di mesin kami dan hanya pelanggan kami sendiri program
  kami. Tidak ada pelanggan eksternal; jangan tulis "sudah dipakai agen lain".
- Perbandingan dengan proyek lain kami tidak dilakukan: Lencana memakai x402 untuk hal yang
  berbeda; keduanya sah, dan tidak saling meminjam klaim.

**Terkait:** [[04-Tools/TL6 - x402 gate and client]] · [[08-Backlog/01 - Backlog]] P2
"""

P["05-Ecosystem/03 - Discovery Gap.md"] = """---
tags: [ekosistem, "E3"]
---

# 03 - Discovery Gap

**Bagian dari:** [[05-Ecosystem/00 - Hub BNB Ecosystem]]
**Sumber:** `docs/agent-card.json`, `04-Tools/TL6`

**Ringkas:** pertanyaan builder "gimana agen lain bisa tahu Fabius ada?" sekarang terjawab
**setengah**. Identitas dan kartu ada; titik masuknya masih di mesin kami.

**Poin kunci:**
| lapis | status |
|---|---|
| identitas ERC-8004 di registry 97 | ✅ tokenId 2494, bisa dibaca siapa pun |
| `agentURI` menunjuk kartu agen | ✅ `docs/agent-card.json` di raw.githubusercontent repo publik |
| kartu menyebut endpoint + harga + network | ✅ ada di kartu |
| endpoint benar-benar bisa dipanggil orang lain | ❌ **`127.0.0.1` — ditandai di kartu sebagai "LOCAL ONLY"** |
| ada pembeli asing | ❌ satu-satunya pembeli sampai sekarang program kami sendiri |
| penemuan tanpa kami mendaftarkan diri ke suatu direktori | 🟡 bisa lewat registry + direktori indexer pihak ketiga; kami tidak mengontrolnya |

**Detail:** yang bisa dilakukan tanpa hosting: event anchor kami bisa **diperoleh dari chain** —
`getAnchor(id)` dihitung ulang dari berkas repo. Yang tidak bisa: orang luar tidak menemukan
endpoint-nya kalau tidak di-host. Jadi klaim yang benar: "identitas dan jejak terbuka; titik masuk
belum dipublikasikan".

**Terkait:** [[05-Ecosystem/01 - ERC-8004 Identity]] · [[08-Backlog/01 - Backlog]]
"""

P["06-Results/07 - Matured Outcomes.md"] = """---
tags: [hasil, "R7"]
---

# 07 - Matured Outcomes

**Bagian dari:** [[06-Results/00 - Hub Results]]
**Sumber:** `tools/ledger.py`, `decisions/ledger-20260926Z.jsonl`

**Ringkas:** prediksi yang kami anchor sudah ada yang jatuh tempo. Inilah angka pertama yang
bukan tentang proses, tapi tentang kebenaran tebakan — dan angkanya tidak enak.

| masuk (bar) | entry | jatuh tempo | keluar | gross | **net** | hasil |
|---|---|---|---|---|---|---|
| 24 Sep 16:00Z | 0,11605 | 25 Sep 17:00Z | di horizon (time-stop) | +21,5 | **+1,5 bps** | MENANG |
| 24 Sep 17:00Z | 0,11564 | 25 Sep 18:00Z | di horizon (time-stop) | −126,3 | **−146,3 bps** | RUGI |

`WR 50 % · net rata-rata −72,4 bps · total −144,8 bps · rugi bersih 1`

**Poin kunci:**
- Dua menit berbeda, hasil berlawanan 148 bps — konfirmasi langsung bahwa sinyal ini tidak
  membedakan dua jam berturut pada aset yang sama (`06-Results/04`).
- Yang menang pun tidak menutupi ongkos: +1,5 bps net = arah benar, pasar membayar biaya nyaris
  persis nol.
- `n = 2`: tidak ada klaim win-rate, tidak ada uji statistik, `MIN_TRADES = 20` jauh dari terpenuhi.
- Yang boleh dikatakan: **prediksinya jatuh tempo dan jejaknya masih utuh untuk diperiksa.**
  Bukan "kami untung", bukan "kami rugi secara statistik" — dua-duanya melebihi sampel.
- Untuk dapat sampel, horizon harus turun ke 4 jam (`06-Results/02` §4) dan itu membuka pintu ke
  Uji A ([[06-Results/06]]).

**Terkait:** [[04-Tools/TL5 - ledger]] · [[06-Results/02 - Thresholds]]
"""

P["09-Inbox/Session-2026-09-26-27.md"] = """---
tags: [sesi, "S-26-27"]
---

# Session 2026-09-26 → 27

**Bagian dari:** [[09-Inbox/00 - Hub Inbox]]
**Sumber:** keluaran perintah yang dicatat di halaman ini; angka tanpa perintah ditandai *(belum diukur)*.

## Yang masuk ke lapisan permanen

| fakta | halaman resminya |
|---|---|
| hasil whale sweep (3 horison kalah, 30 hari menang tapi tak bisa diklaim) | [[06-Results/06 - Pre-registration Horizon]] |
| jalur eksekusi + 18 test + biaya round-trip 59 bps | [[02-Contracts/C3 - ExecutionVault]], [[02-Contracts/C4 - DemoPair and DemoAsset]] |
| deploy 97 tertahan guard saldo sendiri | [[08-Backlog/01 - Backlog]] P1 |
| Dune: kredit 1,259/kueri, lag ±1 jam, dialek & paginasi | [[03-Data/D4 - Dune]] |
| panel ⑦: 7.137 tx / 322 maker / 103 maker n≥20 | [[03-Data/D2 - Wallet Flow]] |
| proses bisnis & penolakan skema imbal-hasil peserta | [[00-Overview/02 - Business Process]] |
| 8 koreksi klaim kami sendiri | [[00-Overview/05 - Corrections]] |
| kalimat submission yang diizinkan/dilarang | [[10-Submissions/01 - Claims Cheat Sheet]] |

## Yang terjadi hari ini, berurutan

1. **Struktur vault dipindah** ke pola bertingkat (12 halaman lama dipindah utuh, bukan disalin dari
   ingatan; penunjuk `⚠️ DIARSIPKAN` ditinggalkan di path lama) — lihat [[Conventions]].
2. **P1 eksekusi**: `exec_deploy.py` dijalankan dan **berhenti sendiri** — saldo agen 0,0079 tBNB <
   taksiran 0,018; nol transaksi terkirim. Ini bukan kegagalan alat, ini alat bekerja.
   Lanjut: top-up tower lalu jalankan lagi.
3. **Panel ⑦ diukur ulang** (`panel_stats.py`): 3.512 → 7.137 tx unik; 210 → 322 maker; ketebalan
   103 maker ≥20 tx. Ini mengubah ⑦ dari "nunggu data" jadi "bisa diuji per wallet".
4. **Empat jebakan yang sama, dipatok**: `from_hex('0x…')` tidak error tapi tidak cocok (ketiga kali
   soal heks); paginasi tanpa `next_offset` bikin sampel 1.000/6.741; `check_garbled.py` menangkap
   sisipan CJK keempat; salinan lokal 78 commit tertinggal nyaris melahirkan klaim "perekam mati".

## Yang belum diukur *(jangan dikutip sebagai angka)*

- biaya gas nyata satu `openLong`/`close` di 97 — **belum**, karena P1 belum jalan
- jumlah posisi yang benar-benar diambil agen lewat vault — **nol**
- ada tidaknya pembeli asing — belum diuji (endpoint masih lokal)

**Terkait:** [[START-HERE]] · [[08-Backlog/01 - Backlog]]
"""

for rel in ["Concepts/Point-in-Time vs Retro-updatable.md", "Concepts/Lookahead Bound.md",
            "Concepts/Cost Is Fixed.md"]:
    P[rel] = None

P["Concepts/Point-in-Time vs Retro-updatable.md"] = """---
tags: [concept, "pip-vs-retro"]
---

# Point-in-Time vs Retro-updatable

**Ringkas.** Ada dua jenis data yang tampak sama dan tidak boleh dicampur: yang **terkunci pada saat
ia direkam** (commit GitHub, anchor di chain, sha256 di manifest) dan yang **bisa disusulkan/diubah
setelahnya** (baris Dune punya `_updated_at`; API yang paging-nya diabaikan = tidak ada riwayat sama
sekali).

**Aturan yang dipakai di Fabius.** Sumber yang bisa disunting retro **tidak pernah** jadi saksi
waktu; dia boleh jadi bahan statistik. Karena itu: entri ⑦ bisa datang dari Dune, **harga forward**
datang dari kline yang kami tarik sendiri, dan klaim "kami tahu sebelum hasilnya ada" hanya datang
dari commit + anchor.

**Kasus nyata.** `flow_test`/`whale_sweep` memisahkan peran ini dengan sengaja dan menuliskannya di
kepala file. Tanpa pemisahan itu, "+1.717 bps" akan terbaca sebagai penemuan, padahal sumbernya
bisa disusulkan.

Lihat: [[Concepts/Anchored Before Outcome]] · [[03-Data/D4 - Dune]]
"""

P["Concepts/Lookahead Bound.md"] = """---
tags: [concept, "lookahead-bound"]
---

# Lookahead Bound — batas atas yang ramah ke panel

**Ringkas.** Kalau keanggotaan sebuah kelompok ditentukan oleh informasi yang **datangnya setelah**
periode yang diuji, maka kelompok itu punya batas atas yang menguntungkan: apa pun yang kamu ukur
mungkin cuma cermin dari sejarah yang membuatnya terpilih.

**Kaidah yang kami pakai.** Koreksi ini **satu arah**: ia hanya bisa membuat angka kelompok terlihat
**lebih baik**, tidak lebih buruk. Karena itu:
- hasil **negatif** di bawah lookahead tetap kredibel (bahkan dengan bonus, tetap kalah);
- hasil **positif** di bawah lookahead **tidak** bisa disebut apa pun sampai diuji prospektif.

**Kasus nyata.** Panel smart money (label GMGN hari ini) diuji pada swap 90 hari ke belakang:
kalah dari kerumunan di 24 jam–7 hari, "menang" +1.717 bps di 30 hari — satu-satunya yang positif
adalah yang paling mungkin dihasilkan oleh seleksi ke belakang. Versi bersihnya (Uji A: keanggotaan
dicatat sebelum transaksinya) butuh data yang baru mulai terkumpul 26 Sep.

Lihat: [[06-Results/06 - Pre-registration Horizon]] · [[Concepts/Point-in-Time vs Retro-updatable]]
"""

P["Concepts/Cost Is Fixed.md"] = """---
tags: [concept, "cost-is-fixed"]
---

# Cost Is Fixed — ongkos tidak ikut mengecil saat modalmu mengecil

**Ringkas.** Fee, gas, dan slippage itu **per transaksi**. Kalau posisi diperkecil, biaya tidak
mengecil — porsinya **membesar**. Ini alasan ukuran $0,5–1 kalah sebelum sinyalnya dinilai.

**Angka yang kami punya (terukur, bukan estimasi):**

| hal | angka | dari |
|---|---|---|
| biaya round-trip venue demo, posisi 1 unit | **59 bps** | `test_round_trip_...` (forge) |
| ongkos yang dipakai semua uji kami | **20 bps RT** (5,5 taker + 4,5 spread/slip per sisi) | `06-Results/02` |
| gate kasar | gross harus > **40 bps** supaya net > 0 | `06-Results/02` |
| gas nyata `openLong`/`close` di 97 | *(belum diukur — P1 belum jalan)* | — |

**Konsekuensi yang kami ambil.** Karena biaya tetap, pertanyaan pertama sebelum membicarakan sinyal
adalah "pada ukuran berapa ongkos masih masuk akal". Menjalankan $5/hari di atas sinyal yang kami
sendiri ukur negatif akan menghasilkan kurva kerugian yang rapi, bukan bukti.

Lihat: [[02-Contracts/C4 - DemoPair and DemoAsset]] · [[06-Results/02 - Thresholds]]
"""

P["Templates/Template - Part Note.md"] = """---
tags: [template]
---

# Template - Part Note

> Satu bagian = satu topik = satu titik di graf. Kedalaman tinggal di sini; hub hanya merutekan.

```markdown
---
tags: [<area>, "<Identity>"]
---

# <Identity> - <Title>

**Bagian dari:** [[<hub>]]
**Sumber:** `path/from/fabius/root.ext:line`  (atau perintah yang mencetak angkanya)

**Ringkas:** 3-6 kalimat. Apa yang ia lakukan, dan apa yang sengaja **tidak** ia lakukan.

**Poin kunci:**
- 4-8 poin konkret. Nama, bukan vibes: signature fungsi, field, guard, nama error, angka.
- Setiap angka: sebut perintah yang mencetaknya. Tidak bisa? Tandai *(belum diukur)*.

**Detail:**
- Yang dibutuhkan pembaca untuk mengubahnya dengan aman: invarian, urutan, batas.
- Jebakan yang sudah pernah memakan waktu, kalau ada — jangan dihapus demi kerapian.

**Terkait:** [[<saudara>]] · [[<concept>]]
```

Aturan:
- `<Identity>` sama dengan prefiks nama berkas (`A2`, `C3`, `D4`, `TL5`, `E1`, `R7`, `T3`, `P1`).
- Sumber non-`.md` = inline code, **jangan** wikilink.
- "Ia tidak menangani X" bernilai lebih dari satu paragraf yang menyinggung ulang kode.
- Bahasa: Indonesia; istilah teknis, ID, dan nama error tetap Inggris.
"""

P["Templates/Template - Hub.md"] = """---
tags: [template]
---

# Template - Hub

> Satu hub per folder modul. Dia **peta**, bukan esai: beberapa kalimat tentang isi folder, lalu
> daftar setiap bagian dengan satu baris penjelasan.

````markdown
---
tags: [<area>, hub]
---

# <NN> - <Title>

<2-5 kalimat padat: lapisan ini apa, apa yang BUKAN dia, dan satu hal yang tidak boleh dilewatkan
pembaca baru.>

## Bagian

- [[<Prefix>1 - <Judul>]] — <isinya apa>
- [[<Prefix>2 - <Judul>]] — <isinya apa>

## Terkait

- [[<hub lain>]] · [[Quick-Reference]]
````

```dataview
LIST FROM #<area> SORT file.name ASC
```

Aturan:
- `## Bagian` wajib menyebut **setiap** berkas di folder — berkas yang tidak ada di peta adalah
  berkas yang tidak akan pernah dibaca orang.
- Tiap baris dapat penjelasan, bukan cuma tautan.
- `**Sumber:**` sebuah hub = direktori yang ia dokumentasi, mis. ``tools/``.
- Blok `dataview` di akhir adalah yang menjaga peta tetap jujur saat ada berkas ditambahkan manual.
"""

P["Templates/Template - Open Item.md"] = """---
tags: [template]
---

# Template - Open Item

> Untuk item backlog yang panjang dan punya kondisi selesai sendiri (`08-Backlog/Open-Items/`).

```markdown
---
tags: [backlog, "OI-<n>"]
---

# OI-<n> - <Judul>

**Bagian dari:** [[08-Backlog/01 - Backlog]] baris <P#>
**Status:** terbuka · dihambat oleh: <satu hal>
**Sumber:** `path/atau/perintah`

**Masalahnya apa (2-4 kalimat):**

**Yang dibutuhkan:**
- <satu tindakan konkret, satu perintah>

**Selesai kalau:**
- [ ] <kondisi yang bisa dilihat, bukan dirasakan — mis. `tx status=1`, `Broken: 0`, angka muncul>

**Kalau tidak jadi, apa yang harus diubah di dokumen ini:**
- <halaman/klaim mana yang harus mundur>
```

Aturan: "selesai kalau" harus bisa dijawab oleh seseorang yang tidak ikut mengerjakannya.
"""

P["Templates/Template - Testing.md"] = """---
tags: [template]
---

# Template - Testing

> Satu halaman per perintah uji. Ini rumah resmi angka: halaman lain mengutip ke sini.

```markdown
---
tags: [testing, "T<n>"]
---

# T<n> - <nama perintah>

**Bagian dari:** [[07-Testing/00 - Hub Testing]]
**Perintah:** `perintah persis, bisa di-copy`
**Dijalankan:** <tanggal> oleh <siapa/mesin>
**Prasyarat:** <profil foundry / env var / kunci yang TIDAK disimpan di repo>

## Keluaran

```text
<tempel output asli, dipotong seperlunya tapi jangan dirapikan>
```

## Yang dibuktikannya — dan yang tidak

- ✅ <klaim spesifik yang angka ini dukung>
- ❌ <klaim yang tampak didukung tapi tidak — biasanya cakupan, sampel, atau survivorship>

## Kalau gagal

<apa yang dicek duluan, dan jebakan yang sudah pernah memakan waktu di perintah ini>
```

Aturan:
- Output mentah, bukan ringkasan. Kalau tidak bisa menempel output, jangan buat halamannya.
- Satu halaman = satu perintah. Nomor `T<k>` tidak diulang.
- Kolom "yang tidak dibuktikan" wajib ada; tanpanya halaman uji jadi brosur.
"""

for f, body in P.items():
    if body is None:
        del P[f]

import json
import sys

for rel, text in P.items():
    p = os.path.join(VAULT, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("tulis", rel)

print(f"\n{len(P)} halaman ditulis.")

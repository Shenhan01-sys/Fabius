---
tags: [perkakas, "TL44", P161, gerbang-seleksi, pengajuan, slot, jejak]
---

# TL44 - gerbang seleksi bot: jalur kandidat ujung-ke-ujung + pemeriksa jejak (P161)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `engine/seleksi.py` (`TAHAP`, `jejak`, `semua`, `petahana_buku`, `buku_hidup`) · `tools/jejak_kandidat.py` (CLI pemeriksa jejak) ·
`tools/uji_jalur_kandidat.py` (uji kering ujung-ke-ujung pada bar repo, jam simulasi) · `engine/cli.py` (`_book_epoch`, `_book_pnls`,
`_verified_ledgers`, `_book_killers`) · `tools/paper_tick.py` (`init_bot` / `tick_bot` menerima `root`) · `tools/signal_commit.py` (`plan(..., specs=)`) ·
`tools/operator_loop.py` (`bot_komit`, sakelar `KOMIT_PENERBIT`) · tes `engine/tests/test_seleksi.py` · jalur lama
[[04-Tools/TL37 - jalur pengajuan bot]] (B1a-B1e) · epik [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] §11 + [[08-Backlog/12 - Epik Pengajuan Terbuka dan Peninjau LLM]] ·
backlog P161

## Apa

P161 = satu jalur otomatis tempat bot BARU (kiriman penerbit, atau bot Fabius yang belum di buku) bergerak dari kiriman sampai slot buku, dengan
SETIAP langkah tercatat di tempat yang bisa diperiksa ulang siapa pun. B1a-B1e (TL37, 6 Okt) sudah membangun sebagian besar komponennya. Pemetaan
ulang 7 Okt menemukan lima mata rantai yang belum tersambung; halaman ini mencatat peta lengkapnya dan apa yang ditambahkan.

## Peta jalur harian (B1)

| # | Tahap | Rekaman (bukti) | Penulis | Pemeriksa jejak (`seleksi.jejak`) |
|---|---|---|---|---|
| 1 | diterima | antrean gerbang `masuk.jsonl` (volume) -> salinan publik `ledger/pengajuan/masuk/<sha>.json` | gerbang `POST /bots/submit` (`tools/pengajuan.py`), salinan oleh peninjau | `submission_sha` dihitung ulang dari formulir publik (kontak diganti pengganti, tidak ikut hash); tanda tangan EIP-712 dipulihkan = `issuer_wallet` (+ payout bila beda), berlaku pada `t` terima (deadline, TTL <= 1 jam). Pesan EIP-712 memuat `specSha` + `submissionSha` -> **spesifikasi terikat tanda tangan** sejak detik ini |
| 2 | gerbang | `ledger/pengajuan/laporan/<sha>.json` | rantai GitHub `bot-review.yml` -> `tools/tinjau_pengajuan.py` | `report_sha` dihitung ulang dari isi laporan; `submission_sha`, `spec_sha` (= sha `BotSpec` yang disusun ulang dari formulir), `bot_id` cocok; identitas `diverifikasi`; `--hitung-ulang`: potongan bar repo yang menghasilkan `data_hash` laporan dicari ulang |
| 3 | registri | `ledger/pengajuan/registri.jsonl` (rantai hash, k keluarga dihitung ulang) | peninjau yang sama | `registri.verify` (rantai + k + alpha) + catatan cocok dengan laporan (report_sha, vonis, spec_sha, dompet, `t_s` = t terima) |
| 4 | spesifikasi di-pin | `LockRegistry.lockedAt(committer, bot_id, spec_sha)` chain 97 + `ledger/pengajuan/spec/<bot>.json` | worker `fabius-engine` (`operator_loop.spec_pin` -> `tools/pin_spec.py`) | berkas spec cocok registri (`pin_spec.sah`); `--chain` membaca `lockedAt` (baca saja); tanpa `--chain` = TAK TERPERIKSA, bukan OK |
| 5 | bayangan maju | `ledger/paper/<bot>.jsonl` (feed: `ledger/feed/<bot>.jsonl`) | rantai GitHub `paper-ledger` (`paper_tick` genesis otomatis, B1c) | genesis `spec_sha` = registri; rantai hash utuh; `--hitung-ulang`: tiap tick/settle dihitung ulang dari bar repo; hari bayangan n/60 (feed n/120) |
| 6 | penantang | `ledger/book/buku.jsonl` catatan `epoch` (`penantang`, `keputusan`, **`dilewati`**) + `ledger/book/laporan/<sha>.json` | rantai GitHub `engine.cli book epoch --write` (harian, idempoten per epoch 30 hari) | `book_live.verify_book` (rantai + keputusan dihitung ulang) + laporan gerbang epoch ber-sha cocok + `spec_sha` penantang = registri |
| 7 | slot | buku sekarang (`buku`, `book_sha`) + pin `book_sha` (LockRegistry) | rantai GitHub + worker `book_pin` | entri buku `spec_sha` = registri; sejak epoch berapa |
| 8 | pembunuh | `pembunuh` / `dikeluarkan` di catatan epoch | epoch buku (B1d, `slots.killer_triggered`) | status pembunuh terakhir dari catatan yang sudah diverifikasi |
| 9 | sinyal di chain | `SignalAnchor` komit + ungkap per tick | worker `operator_loop` bila **`KOMIT_PENERBIT`** menyala (bawaan MATI) | `--chain`: komit untuk tick sejak masuk slot |

Status tiap tahap di pemeriksa: **OK** (rekaman ada dan cocok dengan yang sebelumnya) · **BELUM** (tahap belum dicapai, mis. bayangan 12/60 hari) ·
**GAGAL** (rekaman ada tetapi tidak cocok: diubah, rantai putus, sha beda; tahap sesudahnya tidak dinilai) · **TAK_TERPERIKSA** (tidak bisa diperiksa
di mesin ini: eth-account tidak ada, chain tidak dibaca; BUKAN OK) · **TIDAK_BERLAKU** (vonis TOLAK, feed tanpa slot).

## Lima mata rantai yang belum tersambung (pemetaan 7 Okt) dan apa yang dibangun

1. **Sinyal bot penerbit di slot tidak pernah dikomit.** `signal_commit.plan` hanya mengenal `SPECS` dan worker hanya mengomit `FABIUS_BOTS`:
   penerbit yang memenangkan slot akan berhenti di "alarm: bot tidak dikenal". Dibangun: `plan(..., specs=)` + `operator_loop.bot_komit` dengan
   sakelar `KOMIT_PENERBIT` = `0` (bawaan, MATI) | `slot` (penghuni buku dari penerbit) | `semua` (semua LOLOS_SHADOW, termasuk masa bayangan).
   Registri rusak = tidak ada bot penerbit yang dikomit (gagal tertutup). **USULAN:** mode yang dipakai + kapan dinyalakan (gas tBNB per bot per hari).
2. **G10 petahana memakai buku GENESIS, bukan buku hidup, dan tanpa penghuni penerbit.** `cli._book_pnls` selalu `genesis_book(0)`; epoch
   memakai `bookmod.fabius_specs(book)` (penghuni penerbit dilewati, padahal bot template/rule penerbit BISA direplay dari `BotSpec` registri).
   Akibatnya kelak: penerbit kedua yang menyalin penerbit di slot (korelasi tinggi, sidik jari beda) tidak terlihat oleh G10. Dibangun:
   `seleksi.petahana_buku` (replay SEMUA penghuni; feed/code yang tidak bisa direplay dicatat, bukan ditebak) dipakai epoch + tinjauan; buku hidup
   tidak sah = tinjauan berhenti (gagal tertutup), tidak memakai genesis diam-diam. Hari ini buku = B1-TREND saja, jadi petahana sama persis.
3. **Kandidat yang DILEWATI epoch tidak tercatat.** Bot registri tanpa ledger maju sah, atau yang ditahan peninjau LLM (P168a), hanya dicetak ke
   log Actions (hilang ±90 hari). Dibangun: catatan epoch mendapat medan `dilewati` [{bot, alasan}] (hanya bila tidak kosong; ikut hash rantai;
   `verify_book` tetap menghitung ulang keputusan seperti sebelumnya).
4. **Tidak ada pemeriksa jejak satu kandidat.** Tiap rekaman bisa dicek terpisah, tetapi tidak ada yang menyambung kiriman -> slot dan memeriksa
   tiap sambungan. Dibangun: `seleksi.jejak` + `tools/jejak_kandidat.py` (teks / JSON; `--semua` untuk seluruh registri).
5. **Tidak ada uji ujung-ke-ujung yang menjalankan kode sungguhan.** Tes lama menguji potongan (gerbang, registri, terdaftar, epoch) dengan tiruan.
   Dibangun: `tools/uji_jalur_kandidat.py` - kiriman bertanda tangan (kunci sekali-pakai) -> antrean gerbang -> tinjauan (G1-G11 + KPI) -> registri
   -> pin (tiruan chain, berlabel SIMULASI) -> ledger maju harian -> epoch buku -> keputusan slot -> pemeriksa jejak -> rencana komit worker, semua
   di folder sementara dengan jam simulasi pada bar repo. Tidak ada jaringan, kunci asli, transaksi, atau berkas repo yang ditulis.

## Hasil uji kering 7 Okt (dicetak `python -X utf8 tools/uji_jalur_kandidat.py --mulai 2026-05-01 --hari 70` dan `--hari 3 --kind rule`)

Template (formulir contoh repo, B1-TREND N = 30 pada ETH + BNB, bot `UJI-TREND-ETH-30`, GateParams terkunci, 37,9 s):

| Tahap | Hasil |
|---|---|
| diterima | 2026-05-01T12:00:00Z, `POST /bots/submit` -> HTTP 201 |
| gerbang | 2026-05-02T08:45:00Z, bar s/d 2026-05-01, **LOLOS_SHADOW**, gagal -, petahana G10 ['B1-TREND'] |
| registri | k 1, 1 catatan, verify SAH |
| dipin | 2026-05-02T08:50:00Z (SIMULASI, tanpa transaksi) |
| bayangan | genesis bar 2026-05-02, 69 hari, tick 70, settle 69, net -153,2 bps |
| penantang | epoch 685: 0 hari -> REJECT · 686: 4 hari -> REJECT · 687: gerbang ulang **TOLAK** (35 hari) -> REJECT · 688: 64 hari, net -63,8 bps -> REJECT "PnL net shadow tidak positif" |
| slot | buku ['B1-TREND'], verify SAH; kandidat tidak masuk slot |
| pemeriksa jejak | OK diterima, gerbang (data_hash = bar repo s/d 2026-05-01), registri, dipin, bayangan, penantang; slot / pembunuh / sinyal BELUM; `rusak_di` tidak ada |

Rule (formulir contoh `PULLBACK-TREND-1` sebagai `UJI-PULLBACK-1`, 9,4 s): HTTP 201 -> **TOLAK** (gagal G3, G8, G10, K2) -> registri k 1 SAH ->
pemeriksa: OK diterima, gerbang, registri; tahap 4-9 TIDAK_BERLAKU. Dua jalur nyata (lolos-lalu-ditolak-di-epoch, ditolak-di-gerbang) sama-sama tercatat
dan terperiksa. Sha kiriman berbeda tiap lari (kunci sekali-pakai berbeda); vonis dan angka sama.

## Dua temuan tambahan saat uji (7 Okt)

- `book_live.verify_book` BERHENTI dengan galat (`KeyError`) pada catatan epoch yang tidak lengkap, bukannya melaporkannya. Diperbaiki: medan wajib
  diperiksa dulu, catatan tidak lengkap = masalah tercatat (epoch tetap menolak menulis di atas buku tidak sah, seperti sebelumnya).
- Hitung ulang ledger maju yang tidak bisa dijalankan karena bar tidak ada di mesin pemeriksa BUKAN bukti pemalsuan: pemeriksa memisahkan
  "tak bisa dihitung ulang" (TAK_TERPERIKSA) dari "BEDA" (GAGAL).

## Urutan S1 "kunci sebelum gerbang" (epik 07 §4) - celah tercatat, rancangan USULAN

Epik 07 §4 menulis S1 = `spec_sha` ditulis ke LockRegistry SEBELUM data evaluasi disentuh. Hari ini pin on-chain terjadi SESUDAH vonis
LOLOS_SHADOW (worker, `pin_spec`), dan yang mengikat spesifikasi sebelum gerbang adalah tanda tangan EIP-712 + antrean publik gerbang - urutan
waktunya dipercaya ke gerbang Fabius (Fabius bisa saja tidak mencatat kiriman yang gagal). Rancangan USULAN (belum dibangun, butuh kata builder +
gas): gerbang mem-pin `submission_sha` saat kiriman diterima (kunci fasilitator, seperti akar komit feed P167c), tinjauan harian menunggu pin
terbaca di chain sebelum menjalankan gerbang, pemeriksa jejak membaca pin itu di tahap `diterima`.

## B2 intraday (F-D116 "tidak ada batasan timeframe") - BELUM dibangun, rancangan USULAN

Butuh: deret bar 15 menit / 1 jam yang di-commit seperti `ledger/bars` (sumber + jadwal + ukuran repo); `spec.horizon` selain `1d` di skema;
gerbang yang memakai satuan bar, bukan hari (G2 3 tahun hari-pnl, anualisasi 365, placebo + bootstrap blok); ledger maju per bar + komit per bar
(SignalAnchor `asof` per bar); epoch buku yang membandingkan bot harian dan intraday pada jendela yang sama. Semua angka di atas = keputusan builder.

## Yang BELUM / tidak dibuktikan

- Kiriman sungguhan pertama belum ada (registri produksi kosong, 7 Okt); jalur dibuktikan lewat uji kering pada bar repo, bukan kiriman nyata.
- Penjualan sinyal bot penerbit di slot (gerbang x402) BELUM: harga + `payTo` = klon `RevenueSplitter` menunggu P81 (LB2-LB4). Gerbang tetap
  menjual bot Fabius saja; bot penerbit tidak ada di `ledgers()` gerbang sehingga `/buy <bot penerbit>` = 404, bukan galat.
- `KOMIT_PENERBIT` bawaan MATI: penerbit di slot belum dikomit ke SignalAnchor sampai builder menyalakan.
- Bot `code` (P167b) tertutup; bot `feed` (P167c) tanpa slot sampai definisi "terbukti" (LB9) - pemeriksa menandai tahap 6-9 TIDAK_BERLAKU.
- Pemeriksa membaca chain hanya dengan `--chain` (RPC publik, baca saja). Uji kering memakai tiruan chain yang berlabel SIMULASI.
- Uji kering memakai KODE + KUNCI hari ini pada jam lampau: bukti mekanisme, bukan klaim kinerja historis dan bukan bukti edge.

## Cara memakai

- Jejak satu kandidat: `python -X utf8 tools/jejak_kandidat.py <bot_id | submission_sha> [--chain] [--hitung-ulang] [--json]`; semua: `--semua`.
  Kode keluar 0 tidak ada GAGAL · 2 ada GAGAL · 3 kandidat tidak ditemukan.
- Uji kering ujung-ke-ujung: `python -X utf8 tools/uji_jalur_kandidat.py [--mulai 2026-05-01] [--hari 70] [--kind template|rule] [--cepat] [--simpan DIR]`.
- Tes: `python -X utf8 -m unittest engine.tests.test_seleksi`.
- Sakelar worker (langkah builder, bawaan mati): `KOMIT_PENERBIT=slot` di service `fabius-engine`.

**Terkait:** [[04-Tools/TL37 - jalur pengajuan bot]] · [[04-Tools/TL39 - aturan deklaratif (rule)]] · [[04-Tools/TL42 - komit maju penerbit (feed)]] ·
[[04-Tools/TL40 - peninjau LLM]] · [[00-Overview/03 - Decisions]] F-D16 · F-D73 · F-D85 · F-D116 · F-D120 · [[07-Testing/T8 - Semantik Kegagalan Operator]]

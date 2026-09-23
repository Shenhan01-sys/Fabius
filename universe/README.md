# `bsc-universe.jsonl` — cara membacanya

Satu baris = satu **snapshot point-in-time** dari universe memecoin BSC, ditulis oleh
`../record_bsc_universe.py`. Formatnya JSONL: **append-only, jangan pernah menyunting atau
menghapus baris** — nilai file ini justru terletak pada bahwa ia ditulis sebelum hasilnya diketahui.

## Jangan menghitung baris sebagai sampel

Per 22 Sep 04:03Z: **17 baris, tapi hanya 10 jendela-jam berbeda.** Tujuh baris adalah
pengulangan dalam jam yang sama, dan semuanya **sengaja kubuat sendiri** saat memverifikasi
perubahan kode (proses loop berjalan berdampingan dengan jalankan-sekali).

Aturan analisis: **bucket per jam dulu, lalu ambil satu baris per bucket.**

    window = row["epoch"] // 3600        # kunci dedupe
    # untuk tiap window: pakai baris pertama window itu (epoch terkecil)

Memperlakukan 17 baris sebagai n=17 menggelembungkan sampel ±70%. Ini pelanggaran yang sama yang
sudah dilarang HeliQuant untuk backtest — `FINDINGS.md` #23: *"re-running the same data doesn't
count — anti-overfit."* Yang berubah di sini cuma namanya: bukan data uji, tapi snapshot.

## Skema

| penanda | arti |
|---|---|
| baris **tanpa** kunci `schema` | 11 baris pertama, **semantik lama**: field `volume` belum dinormalkan ke `volume_24h`, sehingga veto `trending_without_demand` TIDAK berjalan untuk baris GMGN; belum ada `blind_spots` / `fully_evaluated`; string API belum disanitasi. **Kecualikan dari analisis tren.** |
| `"schema": 2` | sejak 22 Sep 01:31Z. Sudah termasuk tiga tambalan: normalisasi nama field, sanitisasi string dari API (`symbol`/`name`/`launched`), dan `blind_spots` (data tidak ada ≠ lulus). |
| `"schema": 3` | sejak 22 Sep ±08:00Z. Menambah veto `not_a_choosable_asset` (base stablecoin/major: USDT, USDC, BTCB, WBNB, BNB, ETH, dll.) **dan** kolom `price_usd` untuk baris pool GeckoTerminal. **`survivable_count` skema 2 tidak sebanding dengan skema 3** — sebelum menderetkan angka, kelompokkan per skema. |

## Sumber credential yang berganti di tengah file

- baris 1–14 → **demo key publik GMGN** (read-only)
- baris 15 ke atas → **API key pribadi** di `~/.config/gmgn/.env`

Rutenya identik dan tidak ada field yang berubah, jadi ini tidak memengaruhi kesimpulan apa pun —
tapi dicatat saja supaya kalau nanti ada selisih angka, seseorang tidak menyalahkan datanya.

## Celah yang diketahui (tidak bisa ditutup susulan)

- 21 Sep 23:03:05Z → 22 Sep 01:03:58Z: **satu tick hilang** (sebab: `sleep(interval)` dihitung
  *setelah* pekerjaan, jadi titik ambil bergeser maju terus). Sudah diperbaiki: sekarang tidur ke
  batas jam dinding berikutnya.
- 22 Sep 02:19:44Z → 03:53:31Z: melenceng +33 menit, sebab sama. Setelah tambalan, gap harusnya
  ±60 menit.

Celah berapa pun selalu bisa dihitung ulang dari `epoch` di tiap baris — tidak ada field khusus
untuk itu, dan tidak perlu.

## Label yang salah, dan tidak akan disunting

Baris **`2026-09-22T07:48:07Z`** bertanda `"schema": 2` padahal isinya sudah **skema 3** — veto
`not_a_choosable_asset` sudah aktif (buktinya: `survivable_count` turun 17 → 13 tanpa perubahan
sumber data apa pun). Penyebabnya: proses perekam diimpor SEBELUM nomor skema dinaikkan, dan
`schema` dibaca dari modul saat itu, bukan dari file saat penulisan.

Baris itu **dibiarkan apa adanya**. Menyunting file append-only untuk memperbaiki label adalah
cara tercepat membuat bukti tak-bisa-dibantah berubah menjadi sesuatu yang tidak bisa dipercaya
siapa pun. Yang dilakukan sebaliknya: kesalahannya dicatat di sini, dan analisis cukup
mengelompokkan window ini sebagai skema 3 secara manual (satu baris, jam 07:48Z).

**Aturan yang lahir dari kejadian ini:** kalau kode penghasil data diubah, **restart dulu, baru
ubah penanda versi** — atau sebaliknya, tapi jangan pernah berharap proses yang sedang berjalan
membawa perubahan di file. Ini kelas bug yang sama dengan `GMGN_KEY` yang terbaca dari env saat
impor: yang dieksekusi adalah salinan di memori, bukan yang ada di disk.

## Kolom yang berarti

| kolom | makna | catatan |
|---|---|---|
| `universe_size` | jumlah baris hasil gabungan 3 sumber | 90 = 50 (GMGN rank) + 20 (GT trending) + 20 (GT new) |
| `survivable_count` | lolos SEMUA veto | bukan "layak dibeli", hanya "tidak ada alasan menolak yang terukur" |
| `fully_evaluated_count` | lolos veto **dan** tidak punya `blind_spots` | definisi ketat: `unevaluated != passed` |
| `gt_rows` / `gt_rows_with_gmgn_fields` | diagnosa penggabungan GT↔GMGN | kalau yang kedua 0, tumpang-tindihnya runtuh dan semua baris GT diam-diam kehilangan field perilaku. per 22 Sep: 40 / 2 |
| `thresholds` | ambang veto yang dipakai **pada saat itu** | ikut di-hash, jadi angka hari ini bisa direplikasi setelahnya |
| `sha256` | hash kanonik snapshot | `json.dumps(sort_keys=True, separators=(",",":"))` — sama dengan `record_hash()` di HeliQuant, siap di-anchor ke BSC |

## Menjalankan ulang

    cd _research
    python record_bsc_universe.py            # satu snapshot
    python record_bsc_universe.py --loop     # tiap jam, rata ke batas jam
    BSC_UNIVERSE_INTERVAL_MIN=15 python record_bsc_universe.py --loop

Semua sumbernya nol-auth atau demo-key; `GMGN_API_KEY` dibaca dari env lalu dari
`~/.config/gmgn/.env`. Tidak ada order, tidak ada kunci wallet, tidak ada jalur swap —
route trading GMGN butuh `X-Signature` dan kunci privat yang sengaja tidak pernah kita pasang.

## Pemadaman 22→23 Sep: 16,2 jam, ±15 jendela hilang permanen

Baris terakhir sebelum bolong: `2026-09-22T10:00:00Z`. Baris sesudahnya:
`2026-09-23T02:18:42Z`. Selisihnya **16,24 jam**. Setiap jendela yang hilang adalah satu
kesempatan lagi untuk membandingkan "yang kami tolak" dengan "yang kami loloskan" — dan tidak ada
satu pun cara untuk mendapatkannya kembali dari API mana pun, karena sumber-sumbernya hanya
menyajikan keadaan *kini*.

**Penyebabnya struktural, bukan sial.** Perekam dijalankan sebagai proses latar yang dipegang sesi
terminal, dan sudah dua kali mati dengan pola sama (sekali `cancelled`, sekali exit code
`1073807364` = proses induk berhenti). Loop panjang menaruh nasib pengumpulan data pada umur sebuah
proses.

**Perbaikan yang benar**: satu panggilan per jam yang dijadwalkan sistem, bukan loop panjang —
`../snapshot_universe.bat` sudah disiapkan untuk itu. Mendaftarkan task-nya **ditolak kebijakan izin
alat** (persistence di luar proyek) dan aku tidak mencari jalan tikus; jadi sampai builder
menyetujuinya, data akan bolong setiap sesi ditutup. Bolongnya selalu terlihat dari `epoch` di tiap
baris, dan ditulis di sini — bukan dihapus diam-diam.

Catatan yang pahit: `survivable_count` / `fully_evaluated_count` justru baru mulai berarti setelah
kolom harga pool ada (lihat skema 3) — artinya jendela-jendela yang hilang itu persis bagian yang
paling dibutuhkan untuk perbandingan kohort.

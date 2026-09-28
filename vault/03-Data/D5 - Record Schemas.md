---
tags: [data, "D5"]
---

# D5 - Record Schemas

**Bagian dari:** [[03-Data/00 - Hub Data]]
**Sumber:** `python -X utf8 vault/scripts/dump_schemas.py` (27 Sep, atas berkas yang di-commit)
**Perintah periksa-ulang:** `python -X utf8 vault/scripts/dump_schemas.py` — keluar non-zero kalau
field baris pertama ≠ baris terakhir

**Ringkas:** bentuk tiap rekaman, field per field. Halaman ini ada karena satu alasan mekanis:
`decisionHash` dan `snapshotHash` dihitung **di atas struktur ini**, jadi siapa pun yang ingin
menghitung ulang hash dari clone butuh tahu field mana yang ikut dan mana yang tidak. Tanpa skema,
"verifiable" cuma bisa dipercaya dari mulut kami.

## universe/bsc-universe.jsonl — satu baris per snapshot (72 baris sampai `2026-09-28T00:37:37Z`, bertambah tiap jam)

| field | arti | ikut hash? |
|---|---|---|
| `schema` | nomor semantik (lihat riwayat di bawah) | ya |
| `snapshot_utc` | waktu snapshot (UTC, `...Z`) | ya (`snapshotHash`) |
| `epoch` | waktu yang sama dalam detik unix | ya |
| `chain` | selalu `"bsc"` | ya |
| `thresholds` | `MIN_LIQ_USD`, `MIN_AGE_SEC`, `MAX_TOP10`, `MIN_LOCK`, `MAX_BUNDLER`, `MIN_HOLDER`, `MIN_VOL_OVER_LIQ` — **dinormalkan di sini supaya hasil bisa dihitung ulang dari berkasnya** | ya |
| `sources` | per sumber: `source`, `status`, `rows`, (`error` kalau gagal) | ya |
| `gdelt` | blok narasi (skema 4): `status`, `slice`, `lines`, `themes`, `watch`, `tone`, `url_count`, `cols_seen`, `sha256` | ya |
| `universe_size` | jumlah baris hasil penggabungan | ya |
| `survivable_count` | yang tidak kena veto | ya |
| `fully_evaluated_count` | yang tidak kena veto **dan** tidak punya blind spot | ya |
| **skema 2 (28 Sep): baris `px` membawa `ttx`** | `t` = waktu kami menarik; `ttx` = waktu transaksi yang menghasilkan harga itu (`0` bila vendor mengirim waktu yang lebih baru dari tarikan - ditandai, bukan dipercaya). Ini jawaban P18/P24: sebelum ada `ttx`, "harga ≤ 10 menit" yang kami jamin berarti "yang kami lihat ≤ 10 menit", padahal umur median harga 8,7 menit dan p90 42 menit. Konsumen boleh menolak `ttx=0`; `t` lama tidak berubah, jadi artefak dan seri yang sudah ada tetap terbaca |
| `gt_rows` / `gt_rows_with_gmgn_fields` | diagnosa penggabungan GeckoTerminal↔GMGN; kalau 0, penggabungan gagal **tanpa error** | ya |
| `top_reasons` | tally alasan penolakan | ya |
| `rows` | isi baris per token | ya |
| `sha256` | hash baris ini (yang ditunjuk `snapshotHash` keputusan) | — (dia sendiri buktinya) |

**Riwayat skema (tertulis di `universe/record_bsc_universe.py:411-438`):**
- *tanpa kunci* (≤ 22 Sep 01:31Z) — `volume` belum dinormalkan, veto volume/likuiditas tidak
  berjalan untuk baris GMGN, belum ada `blind_spots`, string API belum disanitasi
- **2** — ketiganya diperbaiki
- **3** — veto `not_a_choosable_asset` membuang base stablecoin/major (USDT, BTCB, WBNB…).
  `survivable_count` skema 2 **tidak sebanding** dengan skema 3 → jangan disatukan dalam satu deret
- **4** — blok `gdelt` bertambah; baris skema 3 tidak punya field itu sama sekali

Itulah kenapa `dump_schemas.py` melaporkan **pergeseran** untuk berkas ini dan itu bukan bug:
barisnya (72 pada 28 Sep, terus bertambah) memang melintasi empat semantik. Analisis mana pun wajib
menyebut nomor skema yang dipakai; kalau tidak, angkanya diam-diam membandingkan dua definisi "lolos".

## universe/wallet-flow.jsonl — polimorfik, 3 jenis baris

| `k` | n (27 Sep) | field | catatan |
|---|---|---|---|
| `tx` | 8.053 | `s` sumber · `h` `transaction_hash` · `m` maker (klecil) · `t` unix detik · `b` 1=buy/0=sell · `c` `is_open_or_close` · `tk` `base_address` · `y` simbol (≤16) · `p` `price_usd` · `u` `amount_usd` (4 desimal) · `g` ≤4 tag GMGN | `g` disimpan justru karena keanggotaan panel adalah **pilihan GMGN**, bukan penilaian kami |
| `px` | 7.792 | `tk` · `y` · `p` · `t` | harga per token dari tarikan yang sama |
| `pull` | 308 | `s` · `http` · `n` · `new` · `mk` · `tk` · `span` | meterai kesehatan: berapa baru, berapa maker, lebar jendela (detik) |

Bentuknya sengaja ramping — `normalize()` disebut di kode: *"ukuran berkas = biaya, tiap byte
dibayar juri"*. Field yang hilang dari tampilan bukan hilang dari fakta: ia memang tidak disimpan
karena tidak dipakai membuktikan apa pun.

## decisions/*.jsonl — jejak yang di-anchor

| berkas | field |
|---|---|
| `direction-*.jsonl` | `kind` · `symbol` · `universe_snapshot` · `data` (meta bar yang dipakai) · `decision` (`side`, `regime`, `why`, `sellability`, `seat_eligible`, `seat_blockers`) · `model` (masukan/veto penilai) · `security` (ringkasan ④) · **`decisionHash` `gatesHash` `snapshotHash`** |
| `security-*.jsonl` | `kind` · `symbol` · `address` · `status` · `ts_utc` · `universe_snapshot` · `gmgn` · `goplus` · `tax` · `why` |
| `ledger-*.jsonl` | `kind` · `as_of_utc` · `cost_bps_rt` · `rows` (satu entri per prediksi) · `rows_sha256` |

Pergeseran yang terukur: `direction-20260924Z.jsonl` **mendapat `security` di tengah berkas**
(baris awal tidak punya, baris terakhir punya) — itu hari ketika ringkasan ④ mulai ikut di-hash.
Konsekuensinya nyata dan tidak boleh dilewat: keputusan tanpa field `security` tidak bisa
dibandingkan dengan yang memakainya, karena `decisionHash` dihitung atas `rec` yang isinya beda.

## Artefak riset (bukan jejak anchor)

`decisions/whale-sweep-90d.json`: `generated_utc` · `prereg` · `wallets_n` · `horizons` ·
`cost_bps_applied` · `note_ongkos` · `rows`. Field `prereg` masih berbunyi
`vault/11-Pra-Registrasi-Uji-Horison-Whale.md` — jalur sebelum migrasi 27 Sep. Artefak itu **tidak
kusentuh**: dia catatan pada saat run, dan menulis ulang artefak demi kerapian adalah cara cepat
kehilangan kepercayaan pada seluruh artefak. Peta jalur lama→baru ada di `_archive/README.md`.

**Terkait:** [[03-Data/D2 - Wallet Flow]] · [[03-Data/01 - Dataset]] ·
[[Concepts/Anchored Before Outcome]] · [[Concepts/Point-in-Time vs Retro-updatable]]

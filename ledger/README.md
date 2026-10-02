# ledger/ - ledger paper maju (M2)

Catatan **append-only, berantai-hash, per bot** dari niat posisi yang dihitung pada penutupan tiap bar harian UTC, dan hasil paper-nya.
**Paper penuh: bukan uang nyata, bukan klaim edge** (F-D16 tetap berlaku: sinyal maju < 20 dan jendela pendek = bukan bukti).

```
ledger/paper/<bot>.jsonl    satu catatan per baris: genesis, tick, gap, settle
ledger/bars/*.csv           bar yang dipakai (fut_<SYM>_1d.csv = kline harian perp, fund_<SYM>.csv = funding); sumber: data.binance.vision
```

## Empat jenis catatan

| jenis | sifat | isi |
|---|---|---|
| `genesis` | awal rantai | bot, `spec_sha`, sha kunci ambang (+ anchor-nya di chain 97), bar pertama yang boleh dicatat |
| `tick` | **ex-ante** | target bobot pada penutupan bar `asof`, dihitung dari data **sampai bar itu saja**, dalam **≤ 12 jam** sesudah penutupan; `data_hash`, id sinyal |
| `gap` | hari terlewat | tidak ada tick sebelum batas 12 jam; **tidak pernah diisi belakangan** (tak terukur ≠ bersih) |
| `settle` | **ex-post** | net paper satu bar = hasil `replay()` yang SAMA dengan gerbang (satu jalur kode) dari tick sebelumnya + harga dan funding nyata; menunggu data bila belum lengkap |

Tiap catatan memuat `prev` (hash catatan sebelumnya) dan `h` (sha256 JSON kanonik tanpa `h`): mengubah atau menyisipkan catatan lama memutus rantai.

## Memeriksa (tanpa jaringan, tanpa kunci)

```
python -X utf8 -m engine.cli ledger verify     # rantai hash + HITUNG ULANG setiap tick (target, data_hash, id sinyal) dan setiap settle dari ledger/bars
python -X utf8 -m engine.cli ledger report     # ringkasan: tick/gap/settle, sinyal maju, kinerja net paper (dengan peringatan jendela pendek)
```

## Funding: aktual, estimasi, dan laporan PROVISIONAL (P92, F-D76)

- `fund_<SYM>.csv` = funding **aktual** (zip bulanan Vision; terbit awal bulan berikutnya). Hanya ini yang dipakai `settle` **final**.
- `fund_est_<SYM>.csv` = **estimasi** per hari lengkap yang direkonstruksi dari `premiumIndexKlines` 1m harian Vision (`engine/funding_est.py`; berkas terbit ±08:40-09:40Z, terjangkau dari runner). Append-only, beku:
  tidak diganti saat funding aktual terbit, sehingga selisih estimasi-vs-aktual terkumpul sendiri. Terukur luar-sampel (Jun-Agu 2026, 16 perp, 4.368 peristiwa): MAE 0,056 bps per peristiwa (maks 0,93), 0,107 bps per hari-simbol
  (maks 1,30), bias +0,025 bps/hari; BNBUSDT memakai I = 0. **Estimasi ≠ funding.**
- `python -X utf8 -m engine.cli ledger report` mencetak satu baris **PROVISIONAL** (net paper untuk bar yang belum bisa final, pakai estimasi) yang berlabel "BUKAN catatan rantai"; ia menjadi final saat zip bulanan terbit.
- Target bot yang memakai funding (B3-CARRY, aktif sejak 2 Okt) memakai pandangan `targets`: estimasi beku untuk hari sejak berkas estimasi ada. Lihat `engine/data.py` (`funding_view`).

## Siapa menulis

Job `.github/workflows/paper-ledger.yml` (jadwal harian, commit oleh runner GitHub dengan jam server GitHub = cap waktu pihak ketiga) menjalankan
`tools/feed_bars.py` (perpanjang bar yang SUDAH tertutup) lalu `tools/paper_tick.py`. Lokal hanya `--init` (sekali per bot) dan uji; dua penulis ke rantai yang sama
**harus** bertabrakan secara terlihat, jadi berkas ini sengaja tanpa `merge=union`.

## Batas yang jujur

- Bot yang boleh punya ledger: identitas (B1-TREND) dan yang LOLOS_SHADOW pada kunci v1 (B3-CARRY) - `engine/book.py` (`SHADOW_ELIGIBLE`). Bot lain lewat gerbang → shadow → slot. **Keduanya aktif sejak bar 2026-10-01** (F-D75, F-D77).
- Funding recent dari REST Binance **terblokir dari kedua jaringan yang diukur** (2 Okt: laptop builder TLS terpotong; runner GitHub HTTP 451, run 36987654079); satu-satunya jalur sekarang zip bulanan yang terbit awal bulan berikutnya, jadi `settle`
  bisa tertunda berminggu-minggu sementara `tick` jalan terus. Settle yang tertunda tampil sebagai "menunggu penutupan", bukan nol; estimasi (di atas) hanya mengisi laporan PROVISIONAL.
- **Jeda tick:** berkas harian Binance Vision terbit ±8,7-9,7 jam sesudah 00:00Z (terukur 2 Okt dari `LastModified` bucket S3; tidak serempak antar simbol), jadi tick keluar ±9-10 jam
  sesudah penutupan. Niat tetap ex-ante terhadap hasil bar berikutnya dan isinya hanya fungsi bar sampai penutupan, tetapi harga masuk 00:00Z tidak bisa didapat pengikut pada saat itu
  sementara `settle` mengandaikan masuk di harga penutupan (konvensi replay): angka maju paper memuat derau/optimisme dari jeda ini. Laporan mencetak `jeda tick`; sumber waktu-nyata menyusul.
- Cap waktu `emitted_utc` adalah klaim jam mesin penulis; yang bisa diperiksa pihak luar = waktu commit di riwayat git (dan kelak anchor kepala ledger di chain, menunggu M3/keputusan builder).
- Bar berasal dari satu sumber (Binance Vision); universe berubah (aset hilang dari feed) = tick **ditolak** sampai feed pulih, atau `gap` bila lewat batas.
- Seed 2020 → 2026-08-31 memuat bolong bar perp yang sudah diketahui (SOL/XRP/LTC/TRX/NEAR, Feb-Apr 2022; `python -X utf8 -m engine.cli gaps --data ledger/bars`); tidak memengaruhi tick maju,
  tetapi ikut menentukan `data_hash` karena seluruh riwayat dihitung.
- Jam maju baru berjalan beberapa hari: ini infrastruktur, belum bukti. Rencana analisis (R8, kalibrasi gerbang vs hasil maju) ditulis sebelum data cukup: `vault/08-Backlog/08 - Riset Optimasi Ambang.md`.

Keputusan dan alasan: `vault/00-Overview/03 - Decisions.md` F-D75; rancangan: `vault/08-Backlog/06 - Epik Gerbang Sinyal.md` §6 (M2).

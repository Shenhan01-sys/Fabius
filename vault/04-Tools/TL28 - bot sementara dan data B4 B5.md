---
tags: [perkakas, "TL28", bot, data]
---

# TL28 - bot sementara (F-D95) + data B4/B5

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `engine/book.py` (`FORWARD_BOTS`, `STATUS`, `GATE_V1`) · `tools/paper_tick.py` (pagar `--init`, umpan PAXG + listing, TUNDA B4) ·
`tools/seed_bars.py` (P128) · `tools/listing_events.py` (P129) · `engine/data.py::load_events` + `load_csv_dir` · `engine/bots/b4_listing_fade.py` ·
lencana `web/src/components/ui/StatusBadge.tsx` · tes `test_paper_tick.py`, `test_seed_bars.py` (2), `test_listing_events.py` (4) · keputusan
[[00-Overview/03 - Decisions]] F-D95

## Label (P127)

| bot | label | vonis gerbang v1 (tercatat, epik 07 §7) |
|---|---|---|
| B1-TREND | **INTI** - penghuni slot identitas buku, PILIHAN builder (F-D73); bukan bukti terbaik | TOLAK (G8, G10) |
| B2-RS | SEMENTARA | TOLAK (G4) |
| B3-CARRY | SEMENTARA (satu-satunya yang lolos gerbang v1; bayangan n/60) | LOLOS_SHADOW |
| B4-LISTING-FADE | SEMENTARA | TIDAK_TERUKUR (pipa kejadian belum ada saat itu) |
| B5-CORE-RWA | SEMENTARA | TOLAK (G8) |
| B6-BOUNCE | SEMENTARA | TOLAK (G3, G8, G10, K2) |

Label ada di luar spesifikasi (mengubah spesifikasi = hash baru = bot baru). Tampil di /bot, buku landing, umpan bukti, MCP `fabius_list_bots`.
`SHADOW_ELIGIBLE` (penantang buku) TIDAK berubah: menyala ≠ masuk buku.

## Data B5 (P128)

`seed_bars.py` menanam berkas BARU dari zip bulanan Binance Vision (cadangan harian bila bulanan belum terbit; satu hari bolong = TOLAK; tidak menimpa).
`spot_PAXGUSDT_1d.csv`: 1.372 bar 2023-01-01..2026-10-03 (ditanam dari laptop, bisa dihasilkan ulang - catatan asal-usul di inbox §69). Umpan harian
memperpanjangnya bila B5 aktif. Emas = PAXG (XAUUSDT tidak ada di spot Binance).

## Data B4 (P129)

`listing_events.py`: daftar simbol bucket Vision `data/futures/um/daily/klines/` (berhalaman), berkas harian PERTAMA tiap simbol = hari-1. Tulis
`um_symbols.csv` (semua perp USDT), `events_um_listing.csv` (hari-1 + penutupan + volume kuotasi untuk simbol baru <= 60 hari), deret
`fut_<SYM>_1d.csv` untuk kejadian yang lolos volume minimum B4 (1 juta USD) selama jendela posisi (H = 14 hari + cadangan), dan cap
`events_um_listing.checked` (tanggal pemindaian sukses). Paralel 16 benang: ±1 menit untuk 901 simbol saat pertama, sesudahnya hanya simbol baru.
Pelajaran: ada simbol non-ASCII (`牛来USDT`, `哈基米USDT`) -> URL di-quote.

Mesin: `load_csv_dir` memuat kejadian + deret koin baru untuk SEMUA pemanggil (bot lain tidak terpengaruh: target + `data_fingerprint` hanya memakai
universe sendiri; `ledger verify` B1/B3 tetap SAH dengan berkas kejadian ada - Test Commands 6f). Target B4 kini flat di hari tanpa kejadian aktif sampai
bar data terakhir (tanpa ini setiap hari biasa jadi gap "data basi"). B4 hanya di-tick bila pemindaian HARI INI sukses; selain itu TUNDA (T8: tak
terbaca != tidak ada listing).

**Temuan dari data nyata (4 Okt):** 68 listing perp USDT baru dalam 60 hari - banyak berupa perp SAHAM/TradFi (ACN, NKE, XOM, DJT, BYD, MRNA, ...),
koin meme, dan satu perp KURS (USDBRL). Spesifikasi B4 ("short perp yang baru onboard") tidak membedakan jenisnya; simulasi tick bar 3 Okt memegang short
CT, MOONSHOT, OURA, TWST, USDBRL masing-masing -2 %. Dicatat, tidak disaring diam-diam (menyaring = spesifikasi baru).

**Batas jujur:** simbol yang di-relist dengan nama lama tidak terdeteksi; kejadian yang zip hari-1-nya terbit lebih lambat dari bar BTC hari itu baru
masuk sehari kemudian.

**Terkait:** [[TL22 - eksekutor dan kertas-venue]] · [[TL25 - halaman bot]] · [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] §7 · [[07-Testing/T8 - Semantik Kegagalan Operator]]

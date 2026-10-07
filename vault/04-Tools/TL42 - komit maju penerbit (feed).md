---
title: TL42 - komit maju penerbit (feed)
tags: [tools, P167, feed, pengajuan, anchor]
---

# TL42 - komit maju penerbit `kind=feed` (P167c, epik 12)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]

**Status (7 Okt 2026):** DIBANGUN di lokal dan **DIBUKA di kode** (`submission.ENABLED_KINDS` = template, rule, feed), BELUM di-push / deploy: gerbang `fabius-x402` (rute + utas anchor), rantai `paper-ledger` (`tools/feed_tick.py`), dan Vercel (`/submit`) naik bersamaan = langkah builder. Keputusan: [[08-Backlog/12 - Epik Pengajuan Terbuka dan Peninjau LLM]] §3.3 + §4 (bayangan 120 hari, F-D125). Bukti: epik 12 §12. Semantik kegagalan: [[07-Testing/T8 - Semantik Kegagalan Operator]] SK-J23..SK-J32. Label kepercayaan di laporan, papan pipa, dan ledger: **"tidak bisa diverifikasi ulang"**.

Untuk metode yang tidak bisa kita jalankan (ML, data on-chain, kode besar). Tidak ada replay: satu-satunya bukti = bobot target bertanda tangan yang ada SEBELUM bar dibuka, dinilai maju di ledger paper yang sama.

## Alur

| Tahap | Di mana | Apa |
|---|---|---|
| daftar | `/submit` (ubin Feed) -> `POST /bots/submit` | formulir v2 `kind=feed`: tanpa template / rule / kode / konstanta, universe dari simbol ber-data, `evidence.komit_maju` kosong; tinjauan harian -> vonis `MAJU_FEED` (bukan LOLOS_SHADOW) |
| tinjau | `engine/review.py::_laporan_feed` | SEMUA G1-G11 + K1-K5 ditulis N/A (status TB + alasan "feed tidak bisa direplay"): N/A bukan LOLOS; `run_gates` atas spesifikasi feed = TIDAK_TERUKUR. Registri: `MAJU_FEED` tidak memakan alpha keluarga dan tidak memicu masa tunggu (`registri.TANPA_STATISTIK`) |
| komit | `tools/feed_gerbang.py::KomitFeed` (gerbang) | `POST /bots/feed/typed-data` {bot_id, bar_close, bobot} -> pesan EIP-712 `FeedCommit` (domain "Fabius Bot Issuer" versi skema; issuer, botId, specSha, barClose, weightsSha); program penerbit menandatangani; `POST /bots/feed/commit` + signature -> 201 / 400 bobot / 401 tanda tangan / 404 bukan bot feed / 409 sudah ada / 422 waktu |
| anchor | `x402_sinyal.py::feed_anchor_loop` -> `KomitFeed.putaran_anchor` | sesudah batas terima (penutupan - 600 s) dan sebelum 30 s terakhir: akar Merkle (OZ) semua komit bar itu dikunci di **LockRegistry yang sudah ada** (`lock(bytes32("FABIUS-FEED"), akar, "fabius-feed:<barClose>:<n>")`, kunci gerbang); status dibaca ulang dari `lockedAt`; gagal dicoba lagi hanya sebelum penutupan |
| nilai | `tools/feed_tick.py` (rantai `paper-ledger`, sesudah `paper_tick.py`, tidak fatal) -> `engine/feed.py::step` | ambil komit publik dari gerbang -> salinan `ledger/feed/komit/<bot>.json` -> ledger `ledger/feed/<bot>.jsonl` (genesis / tick / gap / settle, rantai hash `engine/ledger.py`); tick asof = barClose - 1 hari (dipegang selama bar yang dibuka di barClose); settle = `replay` yang sama dengan bot lain |
| periksa ulang | `engine/feed.py::periksa_komit` / `verify`, `tools/feed_tick.py --verify` | siapa pun: tanda tangan = penerbit terdaftar, waktu terima < batas, bobot sah, daun -> bukti -> akar, `lockedAt` on-chain (dibaca ULANG) dikunci alamat gerbang dan < barClose; tick = bobot komit, data_hash / sinyal / settle dihitung ulang |

## Aturan (konstanta di `engine/feed.py`)

- Bobot = bilangan bulat **ppm** (1 000 000 = 1,0): terhingga oleh konstruksi, kanonik lintas bahasa. Teks kanonik `"BTCUSDT:250000,ETHUSDT:-100000"` (urut simbol, nol dibuang, kosong = flat); `weightsSha` = sha256 teks itu. Web (`web/src/lib/feed.ts`) = gerbang: diuji (kontrak Node).
- Waktu (pola `SelectionAnchor`): `barClose` kelipatan 86 400 (00:00 UTC); diterima hanya bila `now < barClose - 600` dan `barClose <= now + 2 hari`; tidak untuk bar sebelum bot terdaftar.
- Satu komit per (bot, barClose), tidak pernah diganti; berkas komit berantai hash di volume gerbang.
- Sebelum bar dibuka, `GET /bots/feed/<bot>` hanya memuat daun + weightsSha + waktu terima (sinyal penerbit tidak bocor); sesudahnya bobot, tanda tangan, akar, bukti, anchor.
- Komit yang akarnya tidak ter-anchor sebelum penutupan = `gap` "tak terukur" (tidak dinilai dengan percaya jam gerbang). Tidak ada komit = `gap` dengan alasan. Daftar komit / RPC tidak terbaca = TUNDA (lewat 12 jam = gap).
- Bayangan maju **120 hari**; **tanpa slot**: bot feed tidak pernah ada di `terdaftar.rincian` (sumber penantang buku), jadi tidak pernah menjadi penantang. Apa itu "terbukti" (jalur slot sesudah 120 hari) = keputusan builder.

## Yang BELUM / tidak dibuktikan

- Deploy (gerbang + rantai + Vercel) dan cek builder; render `/submit` di peramban + tanda tangan Privy untuk feed belum diuji (tipe + lint + kontrak lintas bahasa saja).
- Jalur slot untuk feed yang "terbukti" belum ada (sengaja; menunggu definisi builder).
- Peninjau LLM (P168) untuk feed belum disambung (epik §3.3: tahap LLM tetap berlaku).
- Kepercayaan yang tersisa: daftar komit disimpan gerbang; yang bisa diperiksa publik = tanda tangan penerbit + akar terkunci on-chain sebelum penutupan. Gerbang bisa MENOLAK komit sah (sensor) - itu terlihat bagi penerbit (respons + tanda tangannya sendiri), tetapi tidak tercatat on-chain.

## Cara memakai

- Tes: `python -X utf8 -m unittest engine.tests.test_feed_kind` (anvil + `out/` untuk tes LockRegistry asli; kontrak web butuh Node >= 22.6).
- Putaran harian: `python -X utf8 tools/feed_tick.py [--dry-run] [--now ISO]`; periksa ulang: `python -X utf8 tools/feed_tick.py --verify`.

**Terkait:** [[00-Overview/03 - Decisions]] F-D122 · F-D125 · [[04-Tools/TL37 - jalur pengajuan bot]] · [[04-Tools/TL41 - kode pengguna di sandbox (code)]] · [[04-Tools/TL9 - ledger paper maju]] · [[02-Contracts/C6 - LockRegistry]]

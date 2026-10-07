---
title: TL37 - jalur pengajuan bot (P161)
tags: [tools, P161, pengajuan, gerbang-seleksi]
---

# TL37 - jalur pengajuan bot penerbit (P161, F-D120)

Satu jalur otomatis dari kiriman penerbit sampai slot buku, tanpa langkah manual. Komponen lama (formulir EIP-712 `engine/submission.py`, registri
P83 `engine/registri.py`, peninjau `engine/review.py`, `engine/slots.py`, buku hidup `engine/book_live.py`) disambung oleh lima bagian:

| Tahap | Di mana | Apa |
|---|---|---|
| B1a terima | gerbang `fabius-x402` (`tools/pengajuan.py`) | `POST /bots/submit` {submission, signature, nonce, deadline[, payout_signature]}: skema tertutup + tanda tangan EIP-712 (TTL <= 1 jam) + nonce per penerbit; <= 2 menunggu per penerbit, <= 50/hari. `POST /bots/typed-data` = pesan yang harus ditandatangani (sha kanonis dihitung gerbang). `GET /bots/submissions[/<sha>]` antrean publik + status; `GET /bots/schema` |
| B1b tinjau | GitHub `bot-review.yml` (dipicu rantai paper-ledger sekali sehari) -> `tools/tinjau_pengajuan.py` | gerbang G1-G11 + KPI pada `ledger/bars` dengan identitas diverifikasi ULANG pada `now = t terima`; registri hash-berantai + `laporan/<sha>.json` + salinan formulir `masuk/<sha>.json` + `spec/<bot_id>.json` (lolos) + `status.json` (tertahan / ditolak sebelum gerbang) di-commit ke repo publik |
| B1b pin | worker `fabius-engine` (`operator_loop.spec_pin` -> `tools/pin_spec.py`) | `spec_sha` spesifikasi yang LOLOS_SHADOW di-pin ke LockRegistry, label = `bot_id`, satu transaksi per putaran; tidak cocok registri = tidak di-pin |
| B1c jam maju | `tools/paper_tick.py` + `engine/terdaftar.py` | bot penerbit lolos mendapat genesis otomatis di putaran harian pertamanya; `BotSpec` disusun ulang dari formulir publik yang cocok dengan registri (berkas spec tidak dipercaya mentah) |
| B1d buku | `engine.cli book epoch` | penantang = `SHADOW_ELIGIBLE` + penerbit dari registri (gerbang terhadap buku sekarang, 60 hari bayangan); pembunuh penerbit = `theory.pembunuh` terstruktur lewat `slots.killer_triggered` pada PnL sejak sinyal ke-n terakhir |

**Kontak penerbit** tidak ikut hash dan tidak pernah publik: gerbang menyimpannya di `kontak.jsonl` (volume), antrean publik dan repo hanya memuat
formulir tanpa kontak (peninjau memakai pengganti "disimpan privat"; sha + tanda tangan tidak berubah).

**B1e web (`/submit`, navbar "Submit bot"):** papan pipa (tiap kiriman di lintasan 4 stasiun: diterima -> gerbang G1-G11 + KPI -> bayangan maju n/60 hari -> slot; ditolak = silang di stasiun gerbang) dari `GET /bots/submissions` (gerbang menambah progres bayangan dari genesis ledger maju + status slot dari buku hidup) + formulir yang DIBANGKITKAN dari `GET /bots/schema` (metode terkunci + param bawaannya, universe = chip simbol yang diizinkan, rujukan + sumber data bisa ditambah, label EN di web / label skema di ID); dompet login Privy = dompet penerbit + bagi hasil; gerbang menghitung pesan EIP-712, Privy menandatangani, `POST /bots/submit`.

**P167a (7 Okt, selesai di lokal, belum di-push):** skema pengajuan v2 (`kind` = template / rule / code / feed; dibuka template + rule; domain EIP-712 `version` "2"). Metode SEPENUHNYA dari penerbit: `kind=rule` membawa aturan JSON yang dijalankan mesin kita; `/submit` tidak lagi memaksa memilih template (jalur API template tetap sah). Rincian: [[04-Tools/TL39 - aturan deklaratif (rule)]].

**P167b / P167c (7 Okt, lokal, belum di-push):** `kind=code` dibangun (sandbox berlapis, pelari terpisah tanpa rahasia, kode PRIVAT di volume gerbang;
formulir publik hanya sha + ukuran + PARAMS) tetapi TETAP TERTUTUP sampai builder menyetujui jalur privat: [[04-Tools/TL41 - kode pengguna di sandbox (code)]].
`kind=feed` dibuka di kode: komit bobot bertanda tangan ke `POST /bots/feed/commit` sebelum penutupan tiap bar, akar per bar dikunci di LockRegistry,
ledger maju `ledger/feed/` (rantai `paper-ledger` -> `tools/feed_tick.py`), vonis tinjauan `MAJU_FEED` (gerbang replay N/A), bayangan 120 hari, tanpa
slot: [[04-Tools/TL42 - komit maju penerbit (feed)]]. Perbaikan sampingan: `terdaftar` kini menerima `spec_sha` registri = sha `BotSpec` (yang memang
ditulis `registri.record`), bukan hanya sha `spec` formulir.

**Belum (berikutnya):** sinyal bot penerbit yang masuk slot belum dikomit/dijual worker (FABIUS_BOTS); bot intraday
(B2); pembukaan `code` (persetujuan builder + deploy pelari); jalur slot feed yang "terbukti"; peninjau LLM (P168). Semantik kegagalan:
[[07-Testing/T8 - Semantik Kegagalan Operator]] SK-J1..J32.

**Terkait:** [[00-Overview/03 - Decisions]] F-D120 · F-D71 · F-D72 · F-D85 · F-D88 · [[TL36 - meja v2 bot + instrumen]]

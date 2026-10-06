---
title: TL39 - aturan deklaratif (rule)
tags: [tools, P167, rule, engine, pengajuan]
---

# TL39 - aturan deklaratif `kind=rule` (P167a, epik 12)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]

Metode bot SEPENUHNYA dari penerbit tanpa kode asing: penerbit menulis aturan JSON, MESIN kita yang menghitung target dan menjalankannya lewat gerbang yang sama dengan bot Fabius. Keputusan dan rincian:
[[08-Backlog/12 - Epik Pengajuan Terbuka dan Peninjau LLM]] §3.1 dan §3.1.1 (baris **USULAN** menunggu builder); jalur pengajuan: [[04-Tools/TL37 - jalur pengajuan bot]]; semantik kegagalan:
[[07-Testing/T8 - Semantik Kegagalan Operator]] SK-J7..SK-J13.

## Di mana

| Bagian | Berkas | Apa |
|---|---|---|
| validator + evaluator | `engine/rule.py` | `vocabulary()`, `validate(rule)` (tidak pernah melempar; pesan tanpa teks mentah), `validate_universe`, `canonical` (`2` == `2.0`), `ukuran` (simpul / kedalaman / anggaran jendela), `varian_g5`, `kelompok_plateau`, `targets(spec, data)` |
| registri mesin | `engine/bots/__init__.py` | `REGISTRY["RULE"]`: satu fungsi untuk semua aturan; `BotSpec.template = "RULE"`, `konstanta = {"rule": <aturan kanonik>}`, `param` = sha aturan, penggaris standar milik kami |
| skema pengajuan v2 | `engine/submission.py` | `SCHEMA_V` 2 (domain EIP-712 `version` "2"); `kind` = template / rule / code / feed (dibuka: template + rule); `spec.rule` wajib untuk rule dan `template` / `param_nama` / `param` / `konstanta` dilarang; `to_botspec` |
| G5 | `engine/gates.py::_g5_rule` | tiap parameter bernama x0,5..x1,5 satu per satu + semua bersama; parameter dekoratif atau tanpa parameter bernama = GAGAL |
| percobaan | `engine/review.py::review` | `n_trials` + jumlah varian G5; laporan rule memuat `varian_g5` (laporan template tidak berubah) |
| gerbang HTTP | `tools/pengajuan.py::info_tanda_tangan` | `GET /bots/schema` membagikan `rule` (kosakata + batas) dan `kinds_open`; `POST /bots/typed-data` menjelaskan masalah aturan sebelum penandatanganan |
| web | `web/src/lib/rule.ts`, `web/src/components/submit/RuleBuilder.tsx`, `SubmitView.tsx` | pembangun aturan (jalur keadaan flat / long / short atau tangga peringkat, parameter bernama, kondisi bersarang, bobot), kalimat biasa EN / ID, penghitung simpul / kedalaman / kerja jendela, JSON |
| kontrak web-gerbang | `tools/web_rule_states.mjs` + `engine/tests/test_rule.py::WebContractTests` | Node menjalankan `rule.ts`; hasilnya divalidasi `engine/rule.py`; penghitung ukuran web = `rule.ukuran` |
| contoh | `engine/examples/submission.rule.example.json` | contoh yang SAH, sengaja tidak mengklaim hasil apa pun |

## Kosakata (sumber kebenaran = `rule.vocabulary()`)

- `mode`: `per_aset` (mesin keadaan per aset: flat -> long / short -> flat; `masuk_long`, `keluar_long?`, `masuk_short?`, `keluar_short?`) atau `peringkat` (`skor`, `long_teratas`, `short_terbawah`, `min_aset`, `rotasi` = `harian` | `tujuh_sub_buku`).
- Ekspresi: `{"c": angka}`, `{"p": nama}`, `{"f": fitur, "n": jendela|{"p"}, "lag": 0..30|{"p"}}`, `{"op": + - * /, "a", "b"}`, `{"fn": abs|neg|min|max, "args": [..]}`.
- Fitur harga: `close open high low volume`; fitur jendela: `ret sma ema std zscore rsi atr_pct max_high min_low vol_ratio drawdown`.
- Kondisi: `{"cmp": > < >= <=, "a", "b"}`, `{"and": [..]}`, `{"or": [..]}`, `{"not": ..}`. `bobot`: `{"skema": "sama"|"inv_vol", "gross_maks": g, "n": jendela (inv_vol)}`.
- Batas: <= 64 simpul, kedalaman <= 8, jendela 2..365, lag <= 30, <= 6 parameter bernama (dipakai, bukan nol), anggaran jendela <= 1500, gross <= 1,0 (`per_aset`) / 2,0 (`peringkat`), k <= 8.

## Konvensi yang bisa mengejutkan

- **Dua konvensi waktu, persis bot template** (supaya ekuivalensi B1/B6/B2 bit-ke-bit benar oleh konstruksi): `ret(n)` memakai selisih n hari di GRID hari-UTC (B1/B2; bar hilang di salah satu ujung = tak terdefinisi); fitur jendela lain memakai n bar harian TERAKHIR milik aset itu, bolong data dilewati (B6). `ledger/bars` punya bolong: SOL, XRP, LTC, TRX, NEAR kehilangan 5 hari bar (26-28 Feb dan 1-2 Apr 2022); bila semua fitur dihitung di grid, B6 berbeda di 18 hari (terukur 7 Okt, `find_gaps` + replay bobot).
- **Tak terdefinisi tidak pernah memicu:** logika tiga-nilai; `not` atas tak terdefinisi tetap tak terdefinisi; keadaan tidak berubah bila kondisi masuk dan keluar sama-sama tak terdefinisi (B6 persis).
- Long dan short sama-sama benar saat flat = konflik, tetap flat. Pada `peringkat` kaki short dipilih dari sisa aset (tidak pernah aset yang sama dengan kaki long).
- `tujuh_sub_buku` = B2-RS: buku hari-minggu j diperbarui tiap hari-UTC j, target = rerata buku yang ada; buku lama dipertahankan bila peringkat hari itu tidak sah.
- Bot rule yang bobotnya nyaris konstan gagal G8 (placebo waktu): jujur, bukan galat.

## Cara memakai

- Periksa formulir + jalankan gerbang pada bar repo: `python -X utf8 -m engine.cli intake --file engine/examples/submission.rule.example.json --data ledger/bars` (kode keluar 0 lolos, 1 ditolak / tidak lolos, 2 hanya validasi).
- Hanya validasi: `python -X utf8 -c "import json; from engine import submission; print(submission.validate(json.load(open('engine/examples/submission.rule.example.json', encoding='utf-8'))))"`.
- Tes: `python -X utf8 -m unittest engine.tests.test_rule` (kontrak web butuh Node >= 22.6; tanpa itu tes kontrak dilewati dan tercetak). Perintah dan angka: [[07-Testing/01 - Test Commands]] #111-#113.

**Terkait:** [[00-Overview/03 - Decisions]] F-D122 · F-D125 · [[04-Tools/TL8 - engine]] · [[04-Tools/TL37 - jalur pengajuan bot]]

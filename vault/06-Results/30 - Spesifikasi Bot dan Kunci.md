---
tags: [results]
---

# 30 - Spesifikasi Bot dan Kunci

**Bagian dari:** [[06-Results/00 - Hub Results]]
**Sumber:** `engine/spec.py` (`SPECS`), `engine/locks/*.lock.json`, `deployments/97.json` (`m3.locks`, `m3.pins`), genesis `ledger/paper/<bot>.jsonl`

Halaman ini menjawab satu pertanyaan: **apa persisnya yang dijalankan operator, dan kapan aturannya dikunci?** Semua angka dicetak ulang 3 Okt 2026
(`python -X utf8 -c "from engine.spec import SPECS; ..."`, `engine.locks/fd16/pembunuh.status()`, dan `deployments/97.json`). Ini bukan hasil kinerja.
Kinerja maju ada di ledger (`python -X utf8 -m engine.cli ledger report`), dan F-D16 belum terpenuhi.

## Enam spesifikasi (satu metode + satu parameter per bot)

| bot | parameter | aset | tier | `spec_sha` | sidik jari efektif |
|---|---|---|---|---|---|
| B1-TREND | N = 60 | 16 | A- | `0x23cb026bd8c665eb…` | `0x99c58fce87484e5a…` |
| B2-RS | L = 28 | 16 | B | `0x2dd6ccf261abaa27…` | `0x6d74c6342734642c…` |
| B3-CARRY | theta = 0.1 | 16 | A (dorman) | `0xc528abf51585f401…` | `0x9618db8e7a94d01b…` |
| B4-LISTING-FADE | H = 14 | 1 | B- | `0x78bb0e32b4e4f406…` | `0x8cd5990b2250dbab…` |
| B5-CORE-RWA | L = 90 | 2 | B | `0x2dfb0fa4ae71a357…` | `0xc6d365b72f6aae7f…` |
| B6-BOUNCE | N = 10 | 16 | C | `0x4a6d180d93ea34e7…` | `0x6695d8c46bc6593b…` |

`spec_sha` mengikat SEMUA isi spesifikasi, termasuk kalimat pembunuh: mengubah apa pun = bot baru = ledger baru. Sidik jari efektif hanya metode +
parameter + universe + konstanta (dedupe; nama dan kalimat tidak ikut).

**Yang punya jam maju:** hanya B1-TREND (bot identitas, F-D73) dan B3-CARRY. Keduanya genesis bar 2026-10-01 di bawah kunci ambang v1
`0xf145b70abd251b9f…`, yang di-anchor 2026-10-02T08:17:48Z (tx `0xf09d61e601e2…`). Empat bot lain belum boleh punya jam maju; jalurnya gerbang ->
shadow -> slot (`engine/book.py`).

## Kunci (urutan waktu)

| kunci | isi | sha | kapan | di chain |
|---|---|---|---|---|
| ambang v1 (`engine/locks/review.lock.json`) | ambang gerbang peninjau | `0xf145b70abd251b9f…` | anchor 2026-10-02T08:17:48Z | DecisionAnchor (tx `0xf09d61e601e2…`) |
| spesifikasi B1-TREND | `spec_sha` di LockRegistry oleh committer | `0x23cb026bd8c665eb…` | 2026-10-02T15:49:20Z | tx `0xae9e7132fe5c…` |
| spesifikasi B3-CARRY | sama | `0xc528abf51585f401…` | 2026-10-02T15:49:25Z | tx `0x03f42b78b3aa…` |
| F-D16 maju (`fd16.lock.json`, F-D84) | syarat uji maju | `0x5a47cc4b87758730…` | dikunci 2026-10-02T17:07:59Z | pin `FABIUS-FD16-MAJU-v1` |
| buku epoch 690 (F-D85) | susunan slot | `book_sha 0xfe37d7595644fd7e…` | 2026-10-02T17:26:09Z | pin `FABIUS-BUKU-E690` |
| pembunuh B1/B3 (`pembunuh.lock.json`, F-D87) | syarat buang bot | `0xa55b4782a6d5ec97…` | dikunci 2026-10-03T06:14:54Z | pin `FABIUS-PEMBUNUH-v1`, `lockedAt` 2026-10-03T06:26:28Z |
| anggaran gerbang (`anggaran.lock.json`, F-D88) | A1 5 % / A2 0,2 + antrean | `0x833f25987bae2dbddf…` | dikunci 2026-10-03T07:51:23Z | pin `FABIUS-ANGGARAN-v1`, `lockedAt` 2026-10-03T07:55:41Z |

Status kunci di kode (3 Okt): ambang v1 TERKUNCI, F-D16 TERKUNCI, pembunuh TERKUNCI. Bila kodenya digeser, ketiganya mencetak MENYIMPANG dan tesnya gagal.

## Yang TIDAK dibuktikan halaman ini

- Bahwa bot mana pun punya edge. Jendela maju baru mulai 1 Okt 2026.
- Bahwa kunci dipatuhi selamanya. Yang dibuktikan hanya keberadaan dan urutan waktu; kepatuhan dibuktikan pemeriksa yang menghitung ulang
  (`engine.cli ledger verify`, `tools/verify_signals.py`, `engine.cli book verify`).

**Terkait:** [[00-Overview/03 - Decisions]] F-D73/F-D79/F-D84/F-D85/F-D87 · [[02-Contracts/C6 - LockRegistry]] · [[08-Backlog/05 - Epik Enam Bot]] ·
[[08-Backlog/09 - Usulan P107 Pembunuh Terstruktur]]

---
tags: [backlog]
---

# 09 - Usulan P107: Pembunuh Terstruktur B1/B3 (menunggu kata builder)

**Bagian dari:** [[08-Backlog/00 - Hub Backlog]]
**Kode:** `engine/pembunuh.py` · `python -X utf8 -m engine.cli ledger pembunuh` · uji `engine/tests/test_pembunuh.py` (12)

**Masalahnya:** "pembunuh" adalah syarat yang mengeluarkan bot dari buku slot. Untuk bot Fabius, syarat itu berupa KALIMAT di spesifikasi, dan kalimat itu
ikut `spec_sha`. Jadi kalimat tidak bisa disunting tanpa membuat bot baru dan ledger baru. Akibatnya setiap epoch mencatat pembunuh B1 sebagai "TEKS
(dinilai manusia)", dan mesin tidak pernah bisa mengeluarkan bot yang gagal.

**Usulannya:** terjemahan terstruktur dikunci TERPISAH (`engine/locks/pembunuh.lock.json`). Kunci itu mengikat `spec_sha` dan kalimat aslinya, lalu di-pin
ke LockRegistry seperti kunci F-D16. Sampai dikunci, buku tetap mencatat "TEKS"; tidak ada yang berubah. Terjemahan ini ditulis 3 Okt, SEBELUM ada
satu pun settle maju final, jadi tidak disetel terhadap hasil.

## Terjemahan + pilihan tafsir (yang dicetak tebal = usulan, sudah ada di kode)

| Syarat | Kalimat asli | Tafsir yang perlu diputuskan |
|---|---|---|
| B1-K1 | "12 bulan maju tanpa mengalahkan buy&hold pada MDD dan Sharpe" | **(1a) harus menang di KEDUANYA; kalah di salah satu = mati** · (1b) mati hanya bila kalah di keduanya |
| | patokan "buy&hold" | **(2a) buy&hold SAMA RATA 16 perp universe yang sama, tanpa ongkos**: memisahkan nilai aturan waktunya dari sekadar memegang keranjang yang sama · (2b) BTC saja, seperti G8 bot alokasi |
| | "12 bulan" | 365 hari maju, minimal 90 % harinya punya settle final. Kurang dari itu = BELUM CUKUP DATA: tidak membunuh, tidak menyelamatkan |
| B1-K2 | "kalah dari placebo masuk-acak dengan distribusi lama tahan sama" | placebo = target tick maju digeser melingkar (eksposur dan lama tahan sama persis, sama dengan G8), 1000 tarikan. **(3a) mati bila net bot <= median placebo** · (3b) lebih keras: mati bila net bot di bawah persentil 95 placebo (bot harus jelas lebih baik dari acak) |
| B3-K1 | "hasil hedged negatif tiga bulan berjalan saat aktif" | **(4a) tiga bulan kalender AKTIF terakhir (sudah lewat, >= 10 hari memegang posisi), masing-masing net < 0; bulan dorman dilewati** · (4b) jumlah net 90 hari aktif terakhir < 0 (bergulir) |
| B3-K2 | "satu kejadian ADL pada kaki perp" | tidak ada pilihan: di paper TIDAK BERLAKU (tidak ada posisi nyata, ADL tidak bisa terjadi). Berlaku sejak eksekusi nyata ada |

Vonis bot: YA (ada syarat yang terpicu) · BELUM · TIDAK. Pembunuh yang terpicu mengeluarkan bot pada epoch berikutnya, kecuali bot identitas
terakhir (aturan buku yang sudah ada, F-D73).

**Kapan bisa terpicu paling cepat:** B1 sesudah ±12 bulan settle final, jadi sekitar Okt 2027 (settle final menunggu zip funding bulanan). B3 sesudah tiga
bulan aktif yang lengkap.

**Keadaan hari ini** (`python -X utf8 -m engine.cli ledger pembunuh`, 3 Okt): USULAN, belum dikunci (sha `0xa55b4782a6d5ec97…`). B1: BELUM (0/365 hari
settle final). B3: BELUM (0 bulan aktif selesai); ADL = TIDAK BERLAKU.

## Cara mengunci (sesudah builder memilih)

1. Bila ada pilihan (b), kodenya diubah dulu, diuji, lalu di-push.
2. `python -X utf8 -m engine.cli ledger pembunuh --kunci "Builder <tanggal>: <pilihan>"` -> `engine/locks/pembunuh.lock.json` (menolak menimpa).
3. Pin: `python -X utf8 tools/lock_spec.py --file engine/locks/pembunuh.lock.json --name FABIUS-PEMBUNUH-v1 --send`. Ini satu transaksi dari committer dan
   butuh kata builder.
4. Mulai epoch berikutnya, buku mencatat YA / BELUM / TIDAK menggantikan TEKS (`engine/cli.py::_book_killers`).

**Terkait:** [[08-Backlog/01 - Backlog]] P107 · [[03-Data/D8 - Buku Slot Hidup]] · [[00-Overview/03 - Decisions]] F-D73/F-D84/F-D85 ·
[[07-Testing/T8 - Semantik Kegagalan Operator]] SK-B5/B6

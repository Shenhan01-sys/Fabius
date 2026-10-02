---
tags: [overview]
---

# 00 — Mulai di sini

> **BN-PIVOT - 2 Okt 2026.** Arah proyek bergeser: Fabius menjadi **operator pemilih bot** yang kelak menjual **sinyal
> berbukti** dan membuka slot bot untuk penerbit luar ([[00-Overview/03 - Decisions]] F-D70 dan F-D71). Halaman ini
> menggambarkan keadaan **sebelum** pivot dan tetap benar untuk apa yang **sudah dibangun**; arah baru masih **usulan dan kode
> awal** ([[08-Backlog/05 - Epik Enam Bot]], [[08-Backlog/06 - Epik Gerbang Sinyal]], [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]]).
> Jangan memakai halaman ini untuk menyangkal arah baru, dan jangan menyebut arah baru sebagai fitur yang sudah ada.

Tiga pertanyaan yang paling sering diajukan ke proyek ini, dan di mana jawabnya ada:

**"Agen kalian ngapain?"**
Menyaring universe memecoin/aset BSC secara point-in-time, menilai tiap kandidat dengan pertanyaan
bertipe per desk (nol parsing teks, jawaban berupa pilihan + probabilitas + confidence), melewati
gerbang risiko, lalu **mencatat hasilnya di chain — termasuk penolakannya**. Eksekusi paper, dan
itu dinyatakan, bukan disembunyikan. Lihat `README.md` dan `02-Contracts/01 - DecisionAnchor.md`.

**"Kenapa bukan bot trading seperti milik orang lain?"**
Karena yang bisa kami serahkan bukan janji return. Lihat `06-Results/01 - Claims and Limits.md`: tidak ada satu
pun angka yang berbentuk keuntungan, dan `ABSTAIN` adalah output pertama, bukan kode error.

**"Mana buktinya?"**
Rantai sha256 di `manifest.txt` + commit git yang tidak bisa ditulis mundur (`03-Data/01 - Dataset.md`),
21 test kontrak yang lulus di mesin ini (`02-Contracts/01 - DecisionAnchor.md`), dan daftar jujur apa yang **belum**
terbukti (`06-Results/03 - Not Yet Proven.md`).

## Peta berkas

| Berkas | Isi |
|---|---|
| `06-Results/01 - Claims and Limits.md` | yang boleh dan tidak boleh diucapkan, beserta artefaknya |
| `06-Results/02 - Thresholds.md` | tiap angka + `file:line` asal-usul + tanggal diverifikasi; termasuk tempat kode rujukan lebih longgar dari dokumennya |
| `03-Data/01 - Dataset.md` | cara membaca dataset tanpa hindsight: jendela, skema, aturan dedupe, baris salah-label |
| `02-Contracts/01 - DecisionAnchor.md` | apa yang ditegakkan `DecisionAnchor` dan apa yang tidak |
| `06-Results/03 - Not Yet Proven.md` | 11 lubang, diurut dari yang paling memblokir, masing-masing dengan cara menutupnya |
| `00-Overview/03 - Decisions.md` | `F-D01`–`F-D10`, dengan alasannya |

## Kalau kamu cuma punya lima menit

1. `forge test -vv` → 21 lulus.
2. `python -X utf8 -u tools/screen_universe.py --windows` → corong penolakan hari ini; perhatikan baris
   `unit sebenarnya = TOKEN` — itu angka yang boleh dikutip, bukan jumlah pasangan.
3. Baca `06-Results/03 - Not Yet Proven.md`. Tidak ada proyek yang lebih cepat dipercaya oleh kalimat
   "ini yang belum kami buktikan".

## Yang sedang dikerjakan

`00-Overview/03 - Decisions.md` F-D04 membuka desain lapisan desk (satu panggilan, banyak pertanyaan terisolasi,
`confidence` sebagai gerbang). F-D05/F-D06/F-D09 adalah disiplin yang sudah berlaku di perkakas.
Urutannya: spesifikasi desk → loop keputusan yang memanggil `anchor()` lokal → deploy chain 97 →
jalur x402 untuk pembelian data.

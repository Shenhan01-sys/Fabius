# 00 — Mulai di sini

Tiga pertanyaan yang paling sering diajukan ke proyek ini, dan di mana jawabnya ada:

**"Agen kalian ngapain?"**
Menyaring universe memecoin/aset BSC secara point-in-time, menilai tiap kandidat dengan pertanyaan
bertipe per desk (nol parsing teks, jawaban berupa pilihan + probabilitas + confidence), melewati
gerbang risiko, lalu **mencatat hasilnya di chain — termasuk penolakannya**. Eksekusi paper, dan
itu dinyatakan, bukan disembunyikan. Lihat `README.md` dan `04-Kontrak.md`.

**"Kenapa bukan bot trading seperti milik orang lain?"**
Karena yang bisa kami serahkan bukan janji return. Lihat `01-Klaim-Dan-Batas.md`: tidak ada satu
pun angka yang berbentuk keuntungan, dan `ABSTAIN` adalah output pertama, bukan kode error.

**"Mana buktinya?"**
Rantai sha256 di `manifest.txt` + commit git yang tidak bisa ditulis mundur (`03-Dataset.md`),
21 test kontrak yang lulus di mesin ini (`04-Kontrak.md`), dan daftar jujur apa yang **belum**
terbukti (`05-Belum-Terbukti.md`).

## Peta berkas

| Berkas | Isi |
|---|---|
| `01-Klaim-Dan-Batas.md` | yang boleh dan tidak boleh diucapkan, beserta artefaknya |
| `02-Ambang.md` | tiap angka + `file:line` asal-usul + tanggal diverifikasi; termasuk tempat kode rujukan lebih longgar dari dokumennya |
| `03-Dataset.md` | cara membaca dataset tanpa hindsight: jendela, skema, aturan dedupe, baris salah-label |
| `04-Kontrak.md` | apa yang ditegakkan `DecisionAnchor` dan apa yang tidak |
| `05-Belum-Terbukti.md` | 11 lubang, diurut dari yang paling memblokir, masing-masing dengan cara menutupnya |
| `06-Keputusan.md` | `F-D01`–`F-D10`, dengan alasannya |

## Kalau kamu cuma punya lima menit

1. `forge test -vv` → 21 lulus.
2. `python -u tools/screen_universe.py --windows` → corong penolakan hari ini; perhatikan baris
   `unit sebenarnya = TOKEN` — itu angka yang boleh dikutip, bukan jumlah pasangan.
3. Baca `05-Belum-Terbukti.md`. Tidak ada proyek yang lebih cepat dipercaya oleh kalimat
   "ini yang belum kami buktikan".

## Yang sedang dikerjakan

`06-Keputusan.md` F-D04 membuka desain lapisan desk (satu panggilan, banyak pertanyaan terisolasi,
`confidence` sebagai gerbang). F-D05/F-D06/F-D09 adalah disiplin yang sudah berlaku di perkakas.
Urutannya: spesifikasi desk → loop keputusan yang memanggil `anchor()` lokal → deploy chain 97 →
jalur x402 untuk pembelian data.

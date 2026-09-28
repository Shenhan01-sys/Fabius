---
tags: [tk, tk-quant, "QT1"]
---

# QT1 - Dari Ide ke Strategi yang Bisa Diuji

**Keluarga:** [[00 - Hub Quant]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/QuantTrading/Info1.txt` §"Komponen Utama Quant Trading" —
sumbangannya **daftar topik**, bukan fakta · `vault/06-Results/05 - Pre-registration Flow.md` ·
[[Fakta Terukur]] §A/§E

**Ringkas:** "kalau X maka beli" adalah kalimat, bukan strategi. Strategi adalah fungsi yang
deterministik: keadaan masuk, aksi keluar, parameter bernama, horizon tetap, dan hipotesis nol yang
menyebut **siapa pembandingnya**. Catatan ini tidak menjual metode — dia pintu yang membuat metode
lain bisa ditolak dengan alasan yang bisa diperiksa; seluruh lapisan `03-Sinyal` lahir dari sini.

## Definisi yang bisa dihitung

Sebuah aturan dinyatakan sah kalau lima hal ini tertulis **sebelum** hasilnya dilihat:

```
strategi := (state_t) -> (side ∈ {long, flat, short}, size, horizon_h, keluar)

sah jika:
  1. deterministik   : data + spesifikasi sama -> baris keputusan sama, di mesin mana pun
  2. point-in-time   : state_t hanya membaca baris dengan waktu <= t  ([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]])
  3. horizon tetap   : h jam, sama untuk semua sampel; "sampai structure pecah" bukan horizon
  4. null eksplisit  : pembandingnya dihitung, bukan diasumsikan nol
  5. n_min eksplisit : jumlah sampel non-overlap yang diperlukan sebelum boleh menyimpulkan
```

Titik 4 paling sering dibuang. Baseline yang sah di repo ini = **arah acak pada token dan jam yang
sama**, bukan "tidak ada sinyal" dan bukan "trader biasa" — yang terakhir mustahil secara struktural
karena aliran dompet kita seluruhnya sudah berlabel ([[Fakta Terukur]] §B: **0 dari 607** transaksi
pertama tidak bertag).

Tiga lapisan yang tidak boleh dicampur:

| lapisan | isinya | akibat kalau digabung |
|---|---|---|
| ide | kalimat: "token yang baru saja di-umpin biasanya lanjut" | tidak bisa salah → tidak bisa diuji |
| spesifikasi | parameter, ambang, horizon, null, `n_min`, aturan keluar | di sinilah uji ditetapkan; setelah hasil dilihat dia sudah busuk |
| implementasi | `tools/*.py` + artefak yang di-hash | ide yang "dijalankan" tanpa spesifikasi = parameter yang dipilih sambil melihat chart |

## Cara pakai yang diklaim

Praktik standar (disiplin, bukan penemuan kami): tulis pra-registrasi, kunci dataset dan aturannya,
jalankan satu kali, laporkan apa pun yang keluar — termasuk nol dan minus. Pemilik klaim bentuk ini
adalah disiplin pra-registrasi riset empiris; di repo ini dia diwujudkan di
`vault/06-Results/05 - Pre-registration Flow.md` dan `vault/06-Results/06 - Pre-registration Horizon.md`,
yang keduanya ditulis **sebelum** satu angka hasil pun dilihat dan tetap menyimpan penyimpangannya
masing-masing.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| bar 1 jam ≥ 2.400 untuk aset ber-kontrak perp | `ADA` | Aster 9.599 bar ≈ 400 hari — [[Fakta Terukur]] §A |
| bar ≥ 720 untuk kandidat muda | `ADA-TAPI` | GMGN mentok 1.000 bar ≈ 41,6 hari; pool baru ±30 bar (§A) → C2/D tidak punya masa lalu |
| ambang yang berlaku dan tercatat asal-usulnya | `ADA` | [[Fakta Terukur]] §E — mayoritas "diputuskan, belum diuji terhadap hasil" |
| spesifikasi bertanggal yang bisa dibandingkan dengan hasilnya | `ADA` | `vault/06-Results/05 - Pre-registration Flow.md` |
| log parameter yang PERNAH DICOBA (audit data snooping) | `TIDAK-ADA` | tidak ada catatan percobaan gagal; yang tercatat hanya yang dilaporkan → lihat [[QT4 - Overfitting dan Validasi]] |

## Uji di Fabius

Perintah yang sudah menjalankan bentuk ini, satu-satunya sampai sekarang:

```
python -X utf8 tools/backtest.py --horizon 4
python -X utf8 tools/backtest.py --horizon 24
```

Gerbang yang harus lolos supaya sebuah aturan naik tingkat: `n >= 20` trade OOS non-overlap,
BH-FDR α 0,10, tetap positif setelah fold terbaik dibuang, net > 0 setelah ongkos
(`NEED_BARS=2400`, `MIN_SAMPLES=20` — [[Fakta Terukur]] §A/§E). Hasil run yang ada: **12/12 rugi**
dan **0/12 lolos di horizon 24 jam** (§F). Yang wajib dibaca dari angka itu: bentuk uji ini sudah
terbukti bisa dijalankan dan menghasilkan jawaban minus — bukan bahwa kami jago meracik strategi.

## Batas dan mode gagal

- **Spesifikasi yang bisa diakomodasi chart apa pun** tidak bisa dibuktikan salah apa pun hasilnya
  (penyakit yang sama membuat [[S9 - Elliott Wave dan Harmonic]] sukar diuji). Kalau setiap keadaan
  punya nama, tidak ada keadaan yang dilarang.
- **Horizon yang "fleksibel"** = kebocoran. Waktu keluar yang dipilih setelah posisi berjalan
  mengubah return menjadi cerita.
- **`n_min` yang tidak ditetapkan** berujung pada "masih kurang data" selamanya, atau sebaliknya:
  klaim pada n=3. Yang terukur di kami: tiga `Enter` jatuh tempo = +1,5 / −146,3 / −485,3 bps pada
  asumsi 20 bps, menjadi **−37,5 / −185,3 / −485,3** pada ongkos terukur 59 bps (§F). Dua angka
  pertama adalah peristiwa yang sama dengan penggaris berbeda - tepat di situ alasan `n_min` **dan**
  ongkos harus ditetapkan sebelum apa pun dijalankan, bukan setelah tabelnya muncul.
- **Null sebagai nol** membuat setiap sinyal terlihat hebat di pasar yang sedang naik. Karena itu
  baseline (token, jam) wajib ada di tabel hasil, bukan di catatan kaki.
- Ini pintu, bukan mesin: melewati QT1 tidak menambah sedikit pun edge.

## Tingkat bukti

`T1` sebagai disiplin (praktik riset empiris yang luas, tidak kami uji sendiri) · `T3` untuk
**instance** yang benar-benar dijalankan: aturan arah diuji dengan ambang DIIMPOR dari kode live,
bukan di-fit, hasilnya di [[Fakta Terukur]] §F · flag `NEGATIF` untuk instance itu.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius hanya menguji aturan yang lebih dulu dituliskan sebagai fungsi dengan
  parameter bernama, horizon tetap, dan pembanding yang dihitung; satu aturan semacam itu sudah
  diuji dan kalah ongkos di 12/12 aset."
- **Dilarang:** "kalau idenya sudah ditulis rapi berarti edge-nya sudah terbukti" · "kami punya
  mesin riset strategi" · "pra-registrasi = hasilnya sudah pasti bagus".

**Terkait:** [[QT2 - Backtesting yang Jujur]] · [[QT3 - Data Fitur dan Label]] ·
[[QT4 - Overfitting dan Validasi]] · [[EV5 - Reproduksibilitas dan Pra-Registrasi]] ·
[[FD11 - Aturan Mengalahkan Intuisi]] · [[PL4 - Memutuskan]] ·
[[06-Results/04 - Negative Results]]

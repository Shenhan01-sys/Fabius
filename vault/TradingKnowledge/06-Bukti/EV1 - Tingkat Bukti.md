---
tags: [tk, tk-bukti, "EV1"]
---

# EV1 - Tingkat Bukti

> **BN-SKOP - 3 Okt 2026 (P76).** Vonis NEGATIF trend/momentum di halaman ini berlaku untuk SATU aturan yang diuji: SMA24 ± 1 % + ret24 pada bar
> 1 jam, horison 4/24 bar, ongkos 20/59 bps, 12 perp (`tools/direction.py`). Itu BUKAN vonis untuk keluarga trend. B1-TREND (momentum deret waktu
> HARIAN, N = 60, 16 perp, long/flat) adalah bot terpisah dengan spesifikasi terkunci yang sedang diuji maju ([[06-Results/30 - Spesifikasi Bot dan Kunci]]).

**Keluarga:** [[00 - Hub Bukti]] · **Tahap:** penilaian ([[PL6 - Menilai Hasil]])
**Sumber:** disiplin klaim di [[Aturan Subtree]] · asal ambang di [[06-Results/02 - Thresholds]] · semua angka run lewat [[Fakta Terukur]]

**Ringkas:** Setiap metode di subtree ini punya satu anak tangga `T0`–`T3` plus dua flag (`NEGATIF`, `TERCEMAR`). Tangga ditentukan oleh bentuk bukti, bukan kekuatan tulisan — dua catatan dengan prosa sama bisa beda tiga tangga. Satu aturan berdiri di atas skala ini: **catatan tidak pernah menaikkan bukti produk; yang menaikkan hanya run**, dan hasilnya tinggal di [[06-Results/00 - Hub Results]], bukan di sini.

## Definisi yang bisa dihitung

```
T0  klaim tanpa pemilik atau pemiliknya tak bisa diperiksa   -> "riset menunjukkan ..."
T1  pemilik ada (praktisi/vendor/buku), dipakai luas, TETAPI
    tidak pernah diuji oleh siapa pun yang bisa kita periksa
T2  studi/literatur ada, tidak kami reproduksi di data kami
T3  run kami sendiri, di data kami, bisa diulang dari clone   -> sebut perintah + artefak
```

| peristiwa | efek pada tangga |
|---|---|
| run lolos semua gerbang (`## Uji di Fabius`) | T1/T2 → **T3** — satu-satunya promosi yang subtree ini akui |
| run kalah terhadap klaimnya sendiri | tetap T3 + flag `NEGATIF`: itu tahu jawaban, bukan kalah |
| panel/tag/ambang dipilih setelah hasil ada | flag `TERCEMAR` — angka positif tidak dihitung, angka negatif tetap ([[Concepts/Lookahead Bound]]: koreksinya satu arah) |
| pemilik `T1` ternyata cuma kalimat `Plan.txt` tanpa siapa pun di belakangnya | → **T0** |
| sumber data dicabut, atau artefak tidak lagi cocok dengan run | → tangga dievaluasi ulang; status tanpa tanggal baca itu kebiasaan, bukan fakta |

`NEGATIF` bukan degradasi: seluruh T3 kami di [[Fakta Terukur]] §F isinya negatif (aturan arah rugi net **12/12**, −27,9…−0,8 bps/trade; dibalik pun kalah −39,2…−12,1). Yang di atasnya cuma catatan yang belum pernah diuji.

## Cara pakai yang diklaim

Cara mesin memakai lapisan ini (bukan klaim komunitas — lapisan ini tidak punya komunitas): setiap catatan `01`–`05` mengisi field `## Tingkat bukti`; [[PL4 - Memutuskan]] memperlakukan T3-`NEGATIF` sebagai terlarang mengubah keputusan, T1/T2 sebagai hipotesis yang wajib membawa penanda "belum diuji", T0 sebagai topik. Keadaan per 28 Sep 2026: **tidak ada metode `T3` positif** — semua angka yang terdengar positif adalah `TERCEMAR` atau keluar dari alat yang sedang rusak ([[Fakta Terukur]] §H).

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| run + artefak terbaca dari clone | `ADA` | `tools/backtest.py`, `tools/winlog.py`, `tools/anchor.py --verify` — [[Fakta Terukur]] §F/§G |
| perintah yang memeriksa tangga catatan terhadap run | `TIDAK-ADA` | gerbang bentuk ([[Aturan Subtree]]) menuntut anak tangga ADA ditulis, bukan benar |
| deret harga forward untuk menaikkan metode harga ke T3 | `ADA` | Aster 9.599 bar ≈ 400 hari — [[Fakta Terukur]] §A |
| input metode on-chain yang tidak punya padanan (L2, funding historis) | `TIDAK-ADA` | [[Fakta Terukur]] §C — talinya cuma prospektif ([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]) |

## Uji di Fabius

Satu jalur ke T3, tanpa pintasan: (1) halaman pra-registrasi memuat pembanding, ambang, horison; (2) ambang **diimpor** dari kode hidup, tidak di-fit di data uji; (3) jalankan `tools/backtest.py` / `tools/whale_sweep.py`; (4) verdik tercetak ke [[06-Results/00 - Hub Results]] dengan n, ongkos, hasil BH, fold; (5) **baru** catatan metodenya menulis `T3` + pointer. Skipping langkah 4 — menulis tangga sementara keluaran run masih hidup di obrolan — adalah bentuk pencucian paling umum di repo ini.

## Batas dan mode gagal

- **Metrik populer ≠ bukti.** Panel whale **win rate 69,8 %** tapi **−10,4 bps per jam** ([[Fakta Terukur]] §F): win rate menghitung benar-salah arah, bukan apa yang tersisa setelah ongkos. Catatan yang seluruh bukti-nya win rate belum sampai T1, apa pun yang tertulis di field-nya.
- **Inflasi oleh kerapian.** Catatan yang ditulis bagus "terasa" T2. Lawannya bukan membaca teliti, tapi pointer perintah.
- **Sitasi sirkular.** Catatan A menukil angka dari catatan B, B menukil verdik A; tangganya tidak naik, tapi pembacanya merasa dua sumber.
- **T3 tanpa materialitas.** Gross +1,5…+4,0 bps vs ongkos 20 bps adalah hasil T3 — dan mati. Signifikansi dan tangga pertanyaan berbeda ([[EV3 - Signifikansi dan Multiple Testing]]).
- Catatan ini tidak menguji metode; dia mengukur prosa. Gerbang bentuk bukan gerbang epistemik — yang menaikkan tangga tetap run.

## Tingkat bukti

`T3` untuk pernyataan "repo ini belum menghasilkan metode T3 positif" — tiap angka di belakangnya run yang terekam di [[Fakta Terukur]] §F/§H. `T1` untuk bentuk skalanya sendiri: praktik diimpor dari kerja berbasis-bukti, tidak kami uji sebagai perlakuan versus skala lain di data kami.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "tidak ada klaim di subtree ini yang berdiri di atas tangga yang tertulis di field-nya sendiri — dan tidak ada catatan, termasuk catatan ini, yang boleh menaikkan tangga itu."
- **Dilarang:** "kita punya daftar metode yang terbukti" (yang ada skala, bukan peringkat) · "win rate 69,8 % sebagai bukti edge" · "keputusan ter-anchor di chain, jadi keputusan benar" — urutan bukan kebenaran ([[Concepts/Anchored Before Outcome]]).

**Terkait:** [[Aturan Subtree]] · [[Fakta Terukur]] · [[EV2 - Jebakan Backtest]] · [[EV3 - Signifikansi dan Multiple Testing]] · [[EV5 - Reproduksibilitas dan Pra-Registrasi]] · [[06-Results/04 - Negative Results]] · [[GAP1 - Matriks Metode x Tahap]]

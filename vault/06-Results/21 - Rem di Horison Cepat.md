---
tags: [hasil, "E13", "veto", "umur-posisi"]
---

# 21 - Rem Bekerja di Horison Tempat Kabar Hidup

**Alat:** `python -X utf8 tools/veto_expectancy.py --draws 200` · **Artefak:**
`decisions/veto-expectancy-20260929T084355Z.json` · **Dijalankan:** 29 Sep 2026 ±08:43Z
**Status:** **EKSPLORASI** pada data sampai `t_kunci` watch (02:59:06Z). Yang berdiri di depan
sebagai uji prospectif tetap E12 ([[06-Results/20 - Keluar Cepat, Terkunci]]).

> **⚠ KOREKSI 29 Sep 20:32:34Z (E22, F-D64) - semua angka di halaman ini adalah in-sample.** Uji
> prospectif yang dikunci untuk ini (kunci `12:08:15Z`, `spec 0x6f6e61f8a29bed68…`, n=319 BOLEH /
> 110 VETO pasca-kunci) memberi: mean winso **−9,9 vs −121,4** (selisih **+111,5**, arahnya benar),
> median **−57,9 vs −59,0** (praktik sama, dua-duanya di bawah nol), CI selisih **[−134,0 ; +344,4]**,
> Mann-Whitney **p=0,159**, dan placebo yang lebih tinggi (**+223,7**) daripada efeknya.
> **Vonis: GAGAL.** Jadi "+285,5 vs −230,3 di menit ke-5" dan "16/16 grid ambang" bertahan hanya
> sebagai pengukuran pada jendela tempat ia ditemukan - BUKAN sebagai perilaku yang bekerja. Kalimat
> "rem memperbaiki hasil" turun status di seluruh vault, termasuk cheat sheet submission. Yang
> bertahan secara prospectif justru **E12** (keluar di menit ke-5 mengalahkan tahan ke menit ke-30,
> n=685, CI bawah +135,9) - dan itu aturan **keluar**, bukan alasan masuk.
>
> Yang tidak dilakukan: tidak dibalik jadi "VETO justru untung", tidak ada ambang baru dicari-cari,
> tidak ada n_min/winsor yang diturunkan. Kemungkinan yang dicatat tanpa dijual: veto membaca kerumunan
> jual dari feed yang berumur - mungkin yang salah bukan idenya, tapi **waktu bacanya**.
 Pertanyaannya bukan "apakah rem bekerja" - itu sudah dijawab

F-D31 memasang gerbang ⑦ (`jual_*`) karena diukur **menguntungkan di horison 30 menit**: harapan
winso naik dari **+82,7 ke +162,3 bps** dengan menolak 13,6 % kejadian (n=1.014). Masalahnya, sejak
E11/F-D41 kami tahu horison 30 menit itu **sedang bocor** - di sana bahkan posisi terbaik pun
berakhir minus. Jadi rem yang terbukti di 30 menit belum tentu berguna di tempat kabar hidup.

`tools/veto_expectancy.py` menjawab dengan kode gerbang yang **sama** yang dipakai agen
(`tools/flow_gate.py`, bukan reimplementasi), per kejadian beli, pada tiga horison:

```
   horison   n boleh    n veto   mean boleh    mean veto   med boleh    med veto      selisih CI atas acak vonis
         2       309        91       +262.5       -187.8       +58.5      -393.1       +450.3       +294.5 DI ATAS ACAK
         5       308        92       +285.5       -230.3       +79.8      -377.8       +515.8       +397.2 DI ATAS ACAK
        30       307        92        -72.7       -560.2       -61.9      -996.6       +487.5       +405.1 DI ATAS ACAK
```

482 kejadian; status gerbang saat kejadian: `BOLEH 378 · VETO 104 · TAK ADA DATA 0` (nol di sini
berarti gerbang tidak pernah buta pada jendela ini - bukan kegagalan, dan bukan pula alasan untuk
mengecilkan yang lain).

## 2. Yang membuat ini berbeda dari semua "kandidat" minggu ini

1. **Median dan mean searah.** Pada `BOLEH` di menit ke-5: mean **+285,5** dan median **+79,8** -
   median di atas lantai ongkos (−59 bps), jadi keuntungannya tidak ditopang satu ekor saja.
   Bandingkan `VETO`: median **−377,8**.
2. **Placebo yang benar.** Selisih dibandingkan dengan distribusi **penandaan ulang acak** atas
   angka yang sama (200 undian). Di 2/5/30 menit selisihnya **+450,3 / +515,8 / +487,5** melawan CI
   atas acak **+294,5 / +397,2 / +405,1** → ketiganya lewat. Ini kelas kontrol yang membunuh E7
   (F-D39) dan E8 (F-D40), jadi dia bukan hiasan.
3. **Ini perilaku yang sudah terpasang**, bukan aturan baru yang dicari dari tabel. Tidak ada
   ambang baru yang disetel di halaman ini: gerbangnya `flow_gate` yang sama, hanya horisonnya
   yang diubah.

## 3. Batas yang tidak boleh dihapus bersama angkanya

- **VETO bukan kelompok acak.** Dia adalah kejadian yang *sudah* dihajar penjual dalam 15 menit
  terakhir. Sebagian dari selisih itu memang maksud gerbang (menjauhi pisau jatuh), tapi artinya
  klaim yang jujur adalah *"menolak saat kerumunan menjual memperbaiki hasil pada horison cepat"*,
  bukan *"kerumunan jual menyebabkan kerugian berikutnya"*. Ini asosiasi terarah, bukan eksperimen.
- **Batas venue tetap berdiri.** Kejadian di halaman ini ada di substrat **spot** yang dilihat ⑦.
  F-D43 mengukur bahwa hanya **3,1 %** kabar bisa dieksekusi agen ini, dan `--hanya-venue` menyisakan
  **24 kejadian / 13 simbol** - terlalu kecil untuk menguji apa pun. Jadi E13 memperbaiki *kapan*
  kami boleh berdiri, bukan *di mana*.
- **Latensi tetap raja.** E11: menunda masuk 2 menit membuat median@5m jadi −56,2. Gerbang tidak
  mengubah itu; `tools/fast_lane.py` yang harus mengubahnya (P40), dan vonis E12 (20:04:56Z) yang
  akan memutuskan apakah keluar cepat layak dipercaya pada data yang belum terlihat.
- **Belum terkunci.** Tidak ada pra-registrasi di halaman ini. Kalau angka ini ingin jadi klaim, dia
  harus lewat kunci baru, bukan lewat halaman ini.

## 4. E14 - rem ini tidak berdiri di atas tebing

Angka bagus membuat kami gugup dengan cara yang benar: jangan-jangan ia bergantung pada ambang yang
kebetulan dipilih. `MAKER_MIN = 2` dan `RASIO_JUAL = 1,5` ditetapkan 28 Sep dari uji di horison 30
menit, dan tidak pernah diuji sebagai fungsi horison cepat. `tools/veto_sensitivity.py` menggeser
keduanya di grid 4×4 (maker 1..4 × rasio 1,25..3,0) - **tanpa mencari ambang terbaik**, hanya
menanyakan seberapa jauh hasil bergerak:

- **Kocokan lebih dulu:** pada ambang terpasang, pemindaian ulang alat ini memberi status yang
  **identik dengan `flow_gate.state()` untuk 677/677 kejadian (0 berbeda)**. Kalau satu saja berbeda,
  alatnya berhenti dan tidak berani melaporkan grid - itu bug kami, bukan pasar.
- **Grid-nya lolos semua:** 16 dari 16 kombinasi melewati placebo penandaan ulang acak. Selisih
  (mean `BOLEH` − mean `VETO`, menit ke-5) bergerak **+260,0 … +399,7 bps** melawan CI atas acak
  **+170,2 … +254,4**. Titik terpasang (maker 2; rasio 1,5) = **+395,1 vs +202,4**.
- **Bentuknya masuk akal:** melonggarkan maker (2→4) menggeser sebagian kejadian ke `BOLEH` dan
  selisihnya menyempit perlahan, bukan jatuh. Tidak ada tebing.

Satu perbedaan yang **wajib** disebut supaya dua tabel di halaman ini tidak terlihat bertentangan:
E13 memakai kejadian yang punya harga keluar di **30 menit** (482 kejadian; n boleh 308 / n veto 92
→ mean boleh +285,5), sedangkan E14 memakai kejadian yang punya harga keluar di **5 menit** saja
(677 kejadian; n boleh 416 / n veto 261 → mean boleh +219,8). Populationnya berbeda karena
syarat censoring-nya berbeda - dan itu sebabnya alatnya mencetak `kejadian dinilai di menit ke-5`
di baris pertama, bukan mengandalkan pembaca mengingatnya.

Perintah: `python -X utf8 tools/veto_sensitivity.py --self-test` lalu `--draws 200` · artefak
`decisions/veto-sensitivity-20260929T085xZ.json`. **Alat ini tidak mengubah satu angka pun di
`flow_gate.py`** - mengubah ambang butuh pra-registrasi sendiri, bukan halaman ini (F-D45).

## 5. Perintah

```bash
python -X utf8 tools/veto_expectancy.py --self-test    # selisih terdeteksi saat ada, nol saat tidak
python -X utf8 tools/veto_expectancy.py --draws 200
```

**Terkait:** [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] · [[06-Results/19 - Umur Posisi]] ·
[[06-Results/20 - Keluar Cepat, Terkunci]] · [[08-Backlog/02 - Epik Alasan Masuk]] §3f ·
[[00-Overview/03 - Decisions]] F-D31/F-D41/F-D44 · [[Concepts/One-Way Gate]]

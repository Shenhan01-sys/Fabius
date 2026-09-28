---
tags: [tk, tk-pipeline, "PL4"]
---

# PL4 - Memutuskan

**Keluarga:** [[00 - Hub Pipeline]] · **Tahap:** keputusan · sebelumnya [[PL3 - Menganalisis]] ·
sesudahnya [[PL5 - Mengeksekusi dan Keluar]]
**Sumber:** `tools/direction.py`, `tools/decide.py`, `tools/judge.py` · [[01-Agent/A2 - Decision Spine]] ·
[[01-Agent/A3 - One-Way Gates]]

**Ringkas:** Sebuah pembacaan menjadi keputusan hanya kalau ia memuat enam hal: **arah, harga
masuk, ukuran, invalidation, horizon, dan rezim keluar**. Kurang satu pun, itu masih opini — dan
opini tidak bisa dinilai, tidak bisa di-anchor, dan tidak bisa disalahkan. Fabius menambahkan dua aturan struktur:
`ABSTAIN` adalah hasil yang sah (bukan kegagalan), dan setiap komponen penilai hanya boleh
**mengurangi** — model LLM berdiri di bawah data, tidak di atasnya
([[Concepts/One-Way Gate]]).

## Definisi yang bisa dihitung

```
keputusan = (side, size, entry, invalidation, horizon, exit_regime)
layak(x)  : ada harga masuk ^ ada harga yang membatalkan ^ ada batas waktu ^ gross > 2 x ongkos_rt
hasil(x)  : { ENTER | ABSTAIN }   # kontrak hanya punya dua verdict; "flat" masuk ABSTAIN
```

`invalidation` bukan hiasan: tanpa level yang membacakan "salah", posisi tidak bisa ditutup secara
 rasional, hanya secara emosional ([[FD7 - Invalidation Stop dan Time-Stop]]). Ukuran dihitung dari
jarak ke invalidation, bukan dari keyakinan ([[FD6 - Ukuran Posisi]]). Gerbang satu arah, ditulis
sebagai predikat:

```
final = min_semua(gerbang)        # setiap gerbang boleh membatalkan atau mengecilkan
                                 # tidak ada gerbang yang boleh membuka yang sudah ditutup
```

## Cara pakai yang diklaim

Praktik retail (T1): "sinyal = arah"; keputusan dianggap selesai saat indikator bilang beli.
Praktik quant (T1, pemiliknya paper/kerangka backtester): keputusan = kontrak lengkap berisi ukuran
dan waktu, dan sebagian besar trade yang layak adalah **tidak trading**. Fabius memakai yang kedua
dan memberi bentuk yang bisa diaudit: arah ditentukan **data kami sendiri**, model hanya boleh
memveto atau mengecilkan; kalau model bilang arah berbeda dari data, hasilnya turun ke status lebih
rendah dan keyakinannya dipotong — bukan posisi dibuka ([[04-Tools/TL1 - judge]]). Bukti perilaku,
bukan niat: saat model menjawab `short` untuk kandidat yang riwayat bar-nya di bawah ambang,
keputusannya tetap `flat` — **terukur pada run 25 Sep**, sebelum penyaring dipasang; hari ini
kandidat di bawah `MIN_BARS_TINY` sudah dibuang sebelum pertanyaan dibuat
(`tools/direction.py:205`, `:372`), jadi perilaku "model dibatasi gerbang" masih benar tapi
contohnya tidak bisa diulang dari kode sekarang
([[01-Agent/A3 - One-Way Gates]], [[01-Agent/01 - Asset Classes and Seats]]).

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| bar ≥ 720 sebagai hak dinilai | `ADA` | `MIN_BARS_TINY=720`; di bawah itu kursi gugur — [[Fakta Terukur]] §A |
| gerbang keamanan ④ (bisa dijual / honeypot) | `ADA-TAPI` | 4 status; `UNMEASURED` **mencabut hak kursi**, tidak dihitung bersih — [[04-Tools/TL3 - security_gate]] |
| gerbang kapasitas keluar ⑥ (likuiditas vs ukuran) | `ADA` | ikut `seat_eligible` + `seat_blockers`, dan **di-hash** — [[Fakta Terukur]] §E |
| funding sebagai penolak posisi | `ADA` | **pemutus rezim**, bukan prediktor: > 0,05 %/4 j menolak posisi baru; 0 dari 2.963 settlement melewatinya (§A.5, F-D26) |
| `confidence` model yang terkalibrasi | `TIDAK-ADA` | pembandingnya belum ada: apakah `confidence` tinggi → hit-rate tinggi, belum terukur — [[06-Results/03 - Not Yet Proven]] #2 |
| harga nyata untuk menyimpulkan ukuran | `ADA-TAPI` | mark price venue, bukan pasar meme sungguhan — [[Fakta Terukur]] §D |

## Uji di Fabius

```
python -X utf8 tools/direction.py          # side/entry/stop/target/ukuran/horizon + dua rezim keluar
python -X utf8 tools/decide.py --emit      # keputusan siap-anchor dari gerbang deterministik
python -X utf8 tools/winlog.py             # menampilkan BERAPA LAGI yang kurang, bukan hanya hasil
```

Ambang yang mengikat: `MIN_SAMPLES` 20 trade OOS non-overlap, BH α 0,10, tetap positif setelah fold
terbaik dibuang, dan net > 0 **setelah ongkos nyata di ukuran itu** (F-D16) — semuanya di
[[Fakta Terukur]] §E. Status hari ini, terukur: `anchorCount()` = 19 (28 Sep, §G) dengan mayoritas
verdict `ABSTAIN` ([[Concepts/Anchored Before Outcome]]) — dan abstain-lah yang membuat sebagian kecil
`Enter` berarti, bukan sebaliknya. Uji tambahan: [[ST7 - Checklist Keputusan]] ·
[[EV3 - Signifikansi dan Multiple Testing]].

## Batas dan mode gagal

- **Keputusan judged after the fact.** Kalau isi keputusan boleh berubah setelah hasilnya tiba,
  seluruh tahap ini tidak membuktikan apa pun — karena itu ia di-hash lebih dulu
  ([[PL7 - Kontrak Antar-Tahap]]).
- **Abstain bisa jadi kostum.** Menolak terus-menerus terlihat disiplin dan tidak menghasilkan
  apa pun; abstain hanya bermakna kalau ia **ikut tercatat dan dihitung** (pembilang dan penyebut
  sama-sama di rantai) — bukan dipilih-pilih setelahnya.
- **Ongkos membunuh keputusan yang arahnya benar.** Contoh kami sendiri: posisi yang MENANG pun
  net-nya +1,5 bps — arah betul, pasar membayar ongkos ([[06-Results/07 - Matured Outcomes]]).
- **Keyakinan bukan data.** `conf` yang tidak terkalibrasi tidak boleh menaikkan ukuran; kalau
  kalibrasinya tidak terbukti, komponen modelnya dicabut dan kembali ke gerbang murni
  ([[06-Results/03 - Not Yet Proven]] #13).
- **Gagal mengukur ≠ hasil bersih** ([[Concepts/Unmeasured Is Not Clean]]) — bypass termurah untuk
  sebuah gerbang adalah membuat panggilannya gagal.
- **Dua rezim keluar punya mode gagal berbeda:** stop-loss mengasumsikan kamu bisa menjual
  ([[PL5 - Mengeksekusi dan Keluar]]); time-stop mengasumsikan horizon adalah unit informasi.

## Tingkat bukti

`T1` untuk bentuk enam-komponen (praktik manajemen risiko yang wajar, tidak kami klaim sebagai
temuan). `T3` untuk **mekanisme** gerbang satu arah: ia diuji dengan perilaku, dan keluarannya bisa
dibaca ulang (`tools/decide.py`, `tools/anchor.py --verify`). Untuk kualitas tebakan itu sendiri:
sudah diuji dan hasilnya melawan klaimnya — `NEGATIF` ([[06-Results/04 - Negative Results]]).

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius menerbitkan keputusan lengkap (arah, ukuran, entry, invalidasi, horizon, rezim
  keluar) atau abstain; penilai model hanya boleh mengurangi; dan sebagian besar siklusnya
  berakhir abstain."
- **Dilarang:** "agen kami pintar memilih" (belum ada sampel yang mendukung) · "abstain = tidak
  punya pendapat" · "AI memutuskan posisi" · "keputusannya bisa diubah kalau hasilnya jelek".

**Terkait:** [[PL3 - Menganalisis]] · [[PL5 - Mengeksekusi dan Keluar]] · [[PL7 - Kontrak Antar-Tahap]] ·
[[Concepts/One-Way Gate]] · [[FD5 - Expectancy Bukan Win Rate]] · [[FD6 - Ukuran Posisi]] ·
[[FD7 - Invalidation Stop dan Time-Stop]] · [[ST7 - Checklist Keputusan]]

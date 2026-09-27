---
tags: [tk, aturan]
---

# Aturan Subtree — TradingKnowledge

**Sumber:** `vault/TradingKnowledge/` · pola lapisan dari vault ini sendiri + `ObsidianGuides`
(MOC → hub → part-note, satu node satu topik)

Aturan menulis dan membaca lapisan pengetahuan trading ini. Dia **tambahan** pada
[[Conventions]] — bukan pengganti. Kalau bertabrakan, [[Conventions]] yang menang.

## Apa ini, dan apa yang bukan

Ini bukan tutorial trading dan bukan tempat pamer klaim. Ini **lapisan pengetahuan yang memberi
tugas pada pipeline**: setiap metode dinilai dari satu pertanyaan — *bolehkah metode ini mengubah
keputusan Fabius, dan dengan data apa buktinya?* Halaman yang tidak menjawab itu cuma indah di graf.

| bukan | karena |
|---|---|
| surface klaim publik | itu tugas [[10-Submissions/01 - Claims Cheat Sheet]]; di sini boleh keras, asal tidak dikutip keluar |
| pengganti [[06-Results/00 - Hub Results]] | hasil = angka yang dicetak perintah. Catatan di sini boleh **menunjuk** angka, tidak boleh **menjadi** angka |
| kamus istilah panjang | istilah di [[Glossary-TK]], satu baris per istilah |
| tempat menyetor daftar "strategi terbaik" | tidak ada peringkat di sini; yang ada tingkat bukti |

## Dua hal yang wajib diingat tentang bahan bakunya

`Plan.txt` dan `QuantTrading/Info1.txt` adalah **transkrip percakapan dengan model**, bukan sumber.
Mereka menyumbang **daftar topik** (apa yang harus kita tanyakan) — bukan satu pun fakta. Kalimat
superlatif di dalamnya ("paling OP", "sangat powerful", "winrate tinggi") adalah **klaim tanpa
sumber**; memindahkannya apa adanya ke halaman yang rapi akan mencuci hype menjadi terlihat seperti
pengetahuan. Jadi: topik diterima, klaimnya dicatat sebagai klaim, dan tiap klaim dapat tingkat bukti.

## Lapisan dan ID

| folder | lapisan | ID | isi |
|---|---|---|---|
| `01-Pipeline/` | tahap pekerjaan | `PL#` | apa yang terjadi di tiap tahap, dan artefak apa yang ditinggalkan |
| `02-Fondasi/` | kaidah yang tidak bisa ditawar | `FD#` | struktur, likuiditas, ongkos, expectancy, ukuran posisi |
| `03-Sinyal/` | metode per keluarga | `S# I# V# U# O# M#` | satu catatan per metode, bentuk seragam |
| `04-Setup/` | kombinasi | `ST#` | resep entry–invalidation–keluar + apa yang membuatnya gagal |
| `05-Quant/` | cara mengubah metode jadi uji | `QT#` | backtest, overfitting, arbitrase, ML/LLM, eksekusi, stack |
| `06-Bukti/` | epistemik | `EV#` | tingkat bukti, jebakan uji, signifikansi, reproduksibilitas |
| `07-Peta-Fabius/` | keputusan | `GAP#` | lubang per tahap, biaya menutupnya, urutan kerja |

Prefix ID `03-Sinyal` per keluarga: `S` struktur/price action · `I` indikator · `V` volume &
order flow · `U` turunan (OI/funding/likuidasi) · `O` on-chain · `M` sentimen & narasi.
ID baru wajib menambah baris di tabel ini — sama seperti aturan di [[Conventions]].

## Bentuk catatan (semua bagian wajib ada)

Kerangka: `Templates/Template - Metode.md` (dipakai `01 02 03 05 06 07`) dan
`Templates/Template - Setup.md` (dipakai `04`). Gerbangnya:
`python -X utf8 vault/scripts/tk_check.py` → exit non-zero kalau ada bagian yang hilang.

## Disiplin klaim — empat aturan yang tidak bisa ditawar di subtree ini

1. **Angka "keadaan hidup" hanya dari [[Fakta Terukur]].** Yang berubah antar-run (jumlah baris
   rekaman, `anchorCount`, umur, streak, credit) wajib diambil dari lembar itu — dan lembar itu
   sendiri menyimpan perintah baca-ulangnya. Angka lain yang menyebut produk ini ditulis
   *(belum diukur)*.
   **Kecualian yang sah, dan sengaja:** angka **hasil uji** boleh dikutip langsung dari halaman yang
   memikulnya (`06-Results/*`, `02-Contracts/*`, `03-Data/*`) asal **nama halaman dan perintah yang
   mencetaknya disebut di kalimat itu juga**. Aturan ini meniru lembar fakta sendiri — §A/§D/§F
   mengutip halaman, bukan sebaliknya. Yang dilarang adalah angka tanpa tempat: "sekitar 40 %",
   "beberapa kolam", "riset menunjukkan".
2. **"Fabius memakai X" hanya kalau `tools/` membuktikannya** — sebut file-nya. Kalau belum ada
   kodenya, tulis `TIDAK ADA` di tabel `## Butuh data`. Tidak ada keadaan "mungkin sudah".
3. **Klaim pihak ketiga butuh pemiliknya.** "Riset menunjukkan…" tanpa paper = `T0`. Tulis
   `diklaim oleh <siapa>`, bukan `diketahui bahwa`.
4. **Turunan harus bertanda.** Selisih atau rata dari angka yang sudah ada (mis. `+1,5` dan
   `−146,3` → selisih **148 bps**; dua fee 30 bps berkomposisi → `1 − (1 − 0,003)² = 59,9 bps`, yang
   menjelaskan kenapa 59 bps yang terukur itu hampir seluruhnya fee) boleh ditulis, dengan kata
   **aritmetika** — jangan sampai terbaca sebagai pengukuran kedua. Contoh yang dibatalkan 28 Sep:
   "`59 − 30` = komponen kurva 29 bps" salah karena 30 bps itu **per sisi**, bukan satu putaran.

Satu lompatan yang harus tetap tertutup: catatan di subtree ini **tidak pernah** menaikkan tingkat
bukti apa pun. Yang menaikkan bukti adalah run (`tools/backtest.py`, `tools/ledger.py`,
`tools/anchor.py --verify`), dan hasilnya tinggal di [[06-Results/00 - Hub Results]].

## Status data (enum, jangan bikin istilah sendiri)

| token | arti |
|---|---|
| `ADA` | ada jalurnya di repo ini, bisa dibaca dari clone |
| `ADA-TAPI` | ada, tapi batasnya membuat metode tidak bisa dipakai penuh (sebut batasnya) |
| `TIDAK-ADA` | tidak ada sumber datanya sama sekali |
| `MATI-DARI-MESIN-INI` | sumbernya hidup, jalurnya tidak bisa diakses dari jaringan ini — dan itu **terukur**, lihat catatan pasangan sumber×jaringan di [[Fakta Terukur]] |

Status selalu ditulis bersama tanggal baca. "ADA" yang tidak dicabut selama sebulan bukan fakta,
itu kebiasaan.

## Bahasa dan nama berkas

- Indonesia; istilah teknis, ID fungsi, dan nama error tetap Inggris (sama seperti [[Conventions]]).
- `[[wikilink]]` hanya ke `.md`; `Plan.txt`, `Info1.txt`, kode, dan config = inline code path.
- Tautan **jangan pernah dipatahkan ke baris baru** di tengah `[[ ... ]]`: `check_links.py`
  resolve berdasarkan basename, dan newline di dalamnya membuat tautan tidak pernah cocok.
- Di dalam **baris tabel**, jangan pakai alias sama sekali — `[[A|b]]` memecah tabel, dan
  `[[A\|b]]` dibaca `check_links.py` sebagai target bernama `A\`. Tulis `[[A]]` biasa, dan
  kalau perlu penjelasan, taruh di sel sebelahnya.
- Nama berkas `<ID> - <Judul>.md`, tanpa `: \ / | ? * " < >`, tanpa emoji. Basename harus unik
  se-vault — `check_links.py` Resolve berdasarkan basename.
- Tautan dari hub root ke subfolder memakai path relatif folder hub
  (`[[03-Sinyal/00 - Hub Sinyal|Sinyal]]`) supaya `sync_vault.py` tidak menganggapnya berkas hilang.

## Perawatan

```
python -X utf8 vault/scripts/tk_check.py
python -X utf8 vault/scripts/check_links.py
python -X utf8 vault/scripts/hub_shape.py
python -X utf8 vault/scripts/sync_vault.py --check
```

Lihat: [[00 - Hub Trading Knowledge]] · [[Fakta Terukur]] · [[Glossary-TK]]

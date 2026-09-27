---
tags: [template, tk]
---

# Template - Metode (TradingKnowledge)

> Dipakai untuk **satu metode / satu konsep**: semua catatan di `01-Pipeline/`, `02-Fondasi/`,
> `03-Sinyal/`, `05-Quant/`, `06-Bukti/`, `07-Peta-Fabius/`. Bentuknya seragam supaya
> `python -X utf8 vault/scripts/tk_check.py` bisa menuntut bagian yang hilang.
> Untuk **resep kombinasi** pakai [[Template - Setup]].

````markdown
---
tags: [tk, <tk-sinyal|tk-fondasi|tk-pipeline|tk-quant|tk-bukti|tk-peta>, "<ID>"]
---

# <ID> - <Judul metode>

**Keluarga:** [[00 - Hub <folder>]] · **Tahap:** <fetching|filtering|analisis|keputusan|eksekusi|penilaian> ([[PL# - ...]])
**Sumber:** `path/di/repo.py:baris`  *(kalau metodenya datang dari transkrip: `vault/TradingKnowledge/Plan.txt` §"<bagian>" — klaim komunitas)*

**Ringkas:** 3–6 kalimat. Apa yang diukur metode ini, apa janjinya, dan apa yang **tidak** bisa
diberikan. Jangan membuka dengan pujian.

## Definisi yang bisa dihitung

Tulis rumus atau pseudocode yang membuat dua orang menghitung hal yang sama. Kalau definisi
komunitas memang ambigu (mis. "order block = candle terakhir sebelum pergerakan"), **tulis
ambigunya** dan sebut varian yang dipakai catatan ini.

## Cara pakai yang diklaim

Entry, invalidation, target, timeframe yang biasa dipakai — sebagai **klaim pendukungnya**, bukan
sebagai prosedur yang kami setujui. Sebut siapa yang mengclaim (praktisi, vendor, paper).

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| <mis. bar 1 jam ≥ 2.400> | `ADA` | Aster 9.599 bar — [[Fakta Terukur]] §A |
| <mis. order book L2> | `TIDAK-ADA` | tidak ada jalur di repo ini |

Enum status hanya: `ADA` · `ADA-TAPI` · `TIDAK-ADA` · `MATI-DARI-MESIN-INI` (lihat
[[Aturan Subtree]]). Jangan menulis "ada" tanpa baris tabel.

## Uji di Fabius

Perintah yang mengujinya + ambang yang harus lolos supaya naik tingkat bukti:
`NEED_BARS=2400`, `MIN_SAMPLES=20` OOS non-overlap, BH α 0,10, fold terbaik dibuang,
ongkos **59 bps** (terukur) — semuanya di [[Fakta Terukur]] §D/§E. Kalau belum ada kodenya,
tulis perintah yang *akan* dibutuhkan; jangan menulis perintah yang tidak ada sebagai kalau ada.

## Batas dan mode gagal

Kapan metode ini menyesatkan, untuk siapa, dan ke arah mana. Yang wajib disebut kalau relevan:
survivorship, lookahead, rezim pasar yang berubah, ongkos yang menghapus edge tipis, dan
"metode ini mengukur hal yang sama dengan <saudara>" (duplikasi sinyal).

## Tingkat bukti

`T0` klaim tanpa sumber · `T1` praktik umum yang dipakai luas, tidak teruji oleh kami ·
`T2` ada studi/literatur yang tidak kami reproduksi · `T3` **sudah kami uji di data kami sendiri**
(sebut artefak/run-nya). Boleh ditambah flag `NEGATIF` (sudah diuji, hasilnya melawan klaimnya)
atau `TERCEMAR` (panel/tag dipilih setelah hasilnya ada — lihat [[Concepts/Lookahead Bound]]).

Satu baris alasan. Kalau kamu tergoda menulis `T3`, ingat: `T3` butuh run yang bisa diulang dari
clone ini, bukan angka dari halaman lain.

## Boleh dibaca, dilarang dibaca

- **Boleh:** <kalimat yang masih benar setelah semua batas di atas>.
- **Dilarang:** <kalimat yang akan ditulis orang kalau halaman ini dibaca cepat>.

**Terkait:** [[<saudara satu keluarga>]] · [[<FD/PL yang dipikul>]] · [[<concept>]]
````

## Aturan bentuk

- Panjang target **60–110 baris**. Di bawah 40 berarti metodenya belum dibedah; di atas 150
  berarti ada dua catatan yang dipaksakan jadi satu.
- Satu catatan = satu metode. Keluarga (mis. oscillator) boleh punya catatan sendiri **kalau**
  cara menghitungnya berbeda; kalau cuma periodenya yang beda, itu satu catatan.
- Semua angka tentang produk ini dari [[Fakta Terukur]]. Selain itu: *(belum diukur)*.
- Sumber `.txt`, `.py`, `.sol`, `.json` = inline code, **jangan** wikilink.
- Bahasa Indonesia; istilah, nama field, dan nama error tetap Inggris.

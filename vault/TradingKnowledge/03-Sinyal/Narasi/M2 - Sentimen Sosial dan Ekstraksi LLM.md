---
tags: [tk, tk-sinyal, "M2"]
---

# M2 - Sentimen Sosial dan Ekstraksi LLM

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"5. Pendekatan Fundamental & Sentiment (Crypto
Native)" ("Social Sentiment (Twitter/X, Telegram, Discord, LunarCrush, Santiment)") — klaim
komunitas + nama vendor, tanpa sumber primer

**Ringkas:** Idea keluarga ini: ubah teks (posting, berita) menjadi angka, lalu pakai angka itu
sebagai sinyal. Dua kegagalan khas keluarga ini bukan kegagalan teknis, mereka struktural:
(1) sentimen **terbit setelah** harga bergerak, jadi yang terbaca adalah gema; (2) model bahasa
**memilih kata yang sudah kita duga**, jadi ia terlihat akurat justru saat ia mengulang asumsi
pembuat prompt-nya. Karena itu kontrol negatif bukan formalitas — di repo ini ia doktrin.

## Definisi yang bisa dihitung

```
# pipeline tipikal
skor_teks(t)   = f(berkas teks pada irisan t)            -> {bearish..bullish} atau [-1, +1]
sentimen(t)    = agregat(bobot_by_kredibilitas atau sama rata) atas skor_teks
Delta_sentimen = sentimen(t) - sentimen(t-1)
# tiga hal yang HARUS ikut tercatat supaya angkanya berarti:
waktu_kejadian | waktu_penerbitan_teks | waktu_kita_mengambil_irisan
# tiga waktu ini berbeda; sinyal hanya boleh memakai yang terakhir, dan selisihnya ADALAH edge
# (atau bukti bahwa edge tidak ada) — bukan detail operasional.
```

## Cara pakai yang diklaim

Sentimen sosial yang naik mendahului harga; divergensi (harga naik, sentimen turun) sebagai
pelemahan tren; LLM dipakai sebagai "pembaca berita" yang mengubah korpus jadi skor. Klaimnya
milik vendor sosial (LunarCrush/Santiment) dan praktisi prompt; tidak ada rujukan primer di repo ini.
`Plan.txt` menyebutnya sebagai pelengkap edge, bukan sebagai sesuatu yang sudah diuji.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| LunarCrush / Santiment | `TIDAK-ADA` | tidak ada jalur di repo; keduanya belum pernah diukur sebagai pasangan sumber×jaringan, jadi statusnya belum sampai tingkat `MATI-DARI-MESIN-INI` (§C) |
| CryptoPanic | `MATI-DARI-MESIN-INI` | `403` tanpa akun di laptop **dan** runner — terukur, [[06-Results/03 - Not Yet Proven]] baris 8 |
| GDELT DOC API | `MATI-DARI-MESIN-INI` | `429` di dua jaringan bahkan dengan jeda 6 detik (baris 8) |
| GDELT berkas mentah 15 menit (`lastupdate.txt` → GKG) | `ADA` | jalur hidup di **dua** jaringan (§C); `gdelt_slice()` di `universe/record_bsc_universe.py` menyimpan hitung tema + nada, bukan teks |
| **teks** berita untuk diekstraksi LLM belakangan | `TIDAK-ADA` | sengaja: irisan GDELT disimpan sebagai ringkasan numerik ("nol teks mentah disimpan") → tidak ada yang bisa diekstraksi ulang |
| model bahasa sebagai penilai kandidat | `ADA-TAPI` | satu panggilan ke daftar state kandidat (`tools/direction.py`); perannya **hanya membatalkan/mengecilkan**; kalibrasi `confidence`/veto-nya **belum terukur** (baris 2 dan 13 `06-Results/03`) |

## Uji di Fabius

Urutan yang sah, dan langkah 1 tidak boleh dilewat:

1. **Kontrol negatif dulu, pujian belakangan.** Empat perlakuan minimum: (a) label diacak — hasil
   harus tidak berbeda dari nol; (b) teks dibalik polaritasnya — skor harus ikut berbalik;
   (c) hanya harga/return yang diberikan (bocor teks) — kalau masih "berprediksi", model
   membaca harga lewat jalur lain; (d) canary: teks yang tidak berisi apa-apa tentang aset itu.
2. Baru hitung daya beda terhadap hasil: return bersih 4 jam dengan kontrol **arah acak pada token
   dan jam yang sama** (§B), `n >= 20` non-overlap, gross di atas **59 bps** (§D), BH α 0,10 (§E).
3. Kalau langkah 1 lolos tapi langkah 2 tidak menambah apa pun di atas fitur harga: cabut, dan
   tulis bahwa ia dicabut. Aturan ini sudah tertulis untuk penilai model di baris 13
   [[06-Results/03 - Not Yet Proven]].

## Batas dan mode gagal

- **Gema yang dikira masa depan.** Posting tentang suatu peristiwa terbit setelah orang tahu
  harganya; tanpa kolom `waktu_penerbitan` yang ikut di-hash, deret sentimen tidak bisa dibedakan
  dari deret harga yang dihaluskan.
- **Prompt yang menjawab dirinya sendiri.** Pertanyaan mengarahkan ("apakah ini bullish?") membuat
  model memilih kata yang kita duga; ini bukan kemampuan, ini cermin ([[FD11 - Aturan Mengalahkan Intuisi]]).
- **Panel yang dipilih retroaktif.** Label "akun pintar hari ini" tentang aktivitas masa lalu =
  lookahead; `tools/flow_signal.py` sudah memisahkannya (melaporkan aliran semua maker vs
  maker ber-tag, dan yang kedua tidak boleh dipanggil prediktif tanpa uji prospektif).
- **`UNMEASURED` bukan bersih.** Kegagalan panggilan teks (429/403/TLS terpotong) harus tercatat
  sebagai celah data, bukan sebagai "sentimen netral" ([[Concepts/Unmeasured Is Not Clean]]).
- **Duplikasi dengan M1 dan V1:** volume dan trending sering mengukur hal yang sama dengan
  "perhatian sosial"; menyebut keduanya konfirmasi ganda = satu fakta dua suara.

## Tingkat bukti

`T0` untuk klaim vendor bahwa skor sentimen memprediksi harga · `T2` untuk klaim "mood sosial punya isi prediktif" di pasar lain: Bollen/Mao/Zeng, *Twitter mood predicts the stock market*, arXiv `1010.3003` (J. Computational Science 2011) —metadata dicocokkan 28 Sep, efeknya kecil dan tidak pernah kami replikasi ([[Sumber dan Jangkauan]] #2) · `T1` untuk pola kerja
"ekstraksi → agregasi → uji" · untuk Fabius: **jalur numerik ada (GDELT berkas) tapi belum teruji**
(baris 8), jalur teks tidak ada, dan penilai LLM yang ada belum melewati kontrol negatif di data
kami sendiri.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami punya irisan numerik berita (tema + nada) yang masuk ke hash keputusan, dan kami
  tahu persis bagian yang belum diuji: apakah tema itu memprediksi hasil."
- **Dilarang:** "Fabius membaca sentimen sosial" · menyebut skor LLM sebagai bukti kalau kontrol
  negatifnya belum dicetak · mengklaim dapat berita lebih dulu tanpa menyebut waktu penerbitan ·
  memakai LunarCrush/Santiment seolah kami punya.

**Terkait:** [[M1 - Fear and Greed dan Indeks Sentimen]] · [[M3 - Narasi Sektar dan Rotasi]] ·
[[M4 - Catalyst dan Event Trading]] · [[QT9 - LLM sebagai Pembaca Narasi]] ·
[[O5 - Whale dan Kohor Smart Money]] · [[Concepts/Unmeasured Is Not Clean]] · [[Concepts/Lookahead Bound]]

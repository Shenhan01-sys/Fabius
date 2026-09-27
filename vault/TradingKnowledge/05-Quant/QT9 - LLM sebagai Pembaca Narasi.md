---
tags: [tk, tk-quant, "QT9"]
---

# QT9 - LLM sebagai Pembaca Narasi

**Keluarga:** [[00 - Hub Quant]] · **Tahap:** keputusan ([[PL4 - Memutuskan]])
**Sumber:** `vault/TradingKnowledge/QuantTrading/Info1.txt` §"LLM & AI untuk Quant" (daftar topik) ·
posisi nyata repo: `tools/judge.py`, [[01-Agent/A3 - One-Way Gates]], [[04-Tools/TL1 - judge]] ·
[[Fakta Terukur]] §C/§E/§F

**Ringkas:** ada dua pekerjaan yang sering disamakan padahal berlawanan. Yang pertama sah:
membaca teks — mengambil entitas, tema, nada, dan klasifikasi dari artikel atau posting. Yang kedua
tidak sah sebagai klaim: memakai LLM sebagai peramal harga. Fabius berdiri persis di garis itu:
penilai di `tools/judge.py` hanya boleh **mengurangi** — memveto atau mengecilkan — dan tidak pernah
bisa mengubah `ABSTAIN` menjadi `ENTER`. Itu bukan gaya penulisan kode; itu keputusan desain yang
ditegakkan sampai ke hash keputusan.

## Definisi yang bisa dihitung

Tugas yang boleh diminta dari sebuah LLM, dan cara memeriksa hasilnya:

| peran | keluaran | cara memeriksa hasilnya secara sah |
|---|---|---|
| ekstraksi | struktur dari teks (siapa, apa, kapan, tema) | bandingkan dengan anotasi manusia pada sampel yang sama |
| klasifikasi | label + alasan singkat | akurasi vs kontrol, **plus kontrol negatif** |
| penilai di bawah data | veto / `noul` / penurun keyakinan | veto boleh membatalkan, tidak pernah membuka ([[01-Agent/A3 - One-Way Gates]]) |
| peramal harga | angka arah/level | tidak ada jalur yang sah — hasilnya tidak bisa diperiksa siapa pun |

Aturan satu-arah itulah yang membuat model boleh dicabut tanpa mengubah klaim: kalau `judge.py`
kembali ke mode deterministik (tanpa kredensial), keputusan tetap keluar dan tetap jujur.

## Cara pakai yang diklaim

Klaim yang beredar di literatur populer (`Info1.txt` §"LLM & AI untuk Quant": "research menunjukkan
LLM bagus untuk extract signal dari text/news, tapi masih perlu filter ketat — hindari
hallucination & look-ahead bias"): bagus untuk teks, perlu pagar untuk keputusan. Itu
**diklaim oleh** transkrip dan literatur yang tidak kami reproduksi, bukan diketahui bahwa.

**Kontrol negatif wajib.** Pertanyaan yang harus dijawab sebelum satu pun kalimat publik: apakah
penilai bisa **menjatuhkan** hal yang seharusnya jelek? Uji yang sah: sajikan state nyata dan state
kosong/berisi sampah dengan pertanyaan yang sama, cetak dua-duanya. Penilai yang tidak bisa
menjatuhkan tidak sedang menilai. Ini juga cara menguji hal yang belum terbukti di repo ini:
kalibrasi veto — apakah veto kami memprediksi hasil buruk. Statusnya masih terbuka
(`vault/06-Results/03 - Not Yet Proven.md` #13).

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| teks narasi untuk diekstraksi | `ADA` | berkas GDELT hidup dari mesin ini (§C); CoinGecko trending ikut tersambung — untuk nada/tema, bukan harga |
| penilai bertipe yang bisa dicabut | `ADA` | `tools/judge.py` — rantai provider + `abstain`; keluaran mentah disimpan supaya keputusan bisa direproduksi tanpa model |
| gerbang satu-arah yang menegakkan peran LLM | `ADA` | [[01-Agent/A3 - One-Way Gates]]; hasilnya ikut di-hash (§E) |
| fixture kontrol negatif yang tersimpan di repo | `TIDAK-ADA` | belum ada berkas uji veto; tanpa ini klaim "penilai bekerja" tidak bisa diperiksa |
| kalibrasi veto terhadap hasil | `TIDAK-ADA` | butuh keputusan jatuh tempo dalam jumlah; yang terukur baru n=2 (§F) |
| biaya pemakaian | `ADA-TAPI` | biaya per panggilan dicatat di artefak keputusan (`tools/judge.py`); pemakaian kami sendiri *(belum diukur)* |

## Uji di Fabius

Perintah yang sudah ada jalurnya dan bisa dijalankan dari clone:

```
python -X utf8 tools/direction.py        # keputusan akhir: gerbang menentukan, model hanya mengurangi
```

`tools/judge.py` **bukan CLI** — tidak ada `__main__`, tidak ada `argparse`, tidak ada `print`:
ia modul yang dipanggil `direction.py` lewat satu fungsi (`ask_jev(state, pertanyaan)`), jadi
menjalankan penilai berarti menjalankan `direction.py`.

Yang masih belum ditulis: fixture kontrol negatif dan laporan akurasi veto (`tools/judge_audit.py`).
Bentuk uji yang diizinkan: (a) state nyata vs state kosong → veto harus **berbeda**; (b) tempel
sinyal yang jelas jelek → veto harus jatuh; (c) baru setelah itu bandingkan frekuensi veto dengan
hasil yang jatuh tempo, dengan `n >= 20` dan BH α 0,10 (§E) — dan itu butuh kalender, bukan kueri.

## Batas dan mode gagal

- **Hallucination yang terdengar masuk akal** adalah kegagalan paling mahal, karena keluarannya
  lolos pemeriksaan format. Pagar yang bekerja: pertanyaan bertipe, bukan esai; output mentah
  disimpan; model tidak punya hak menambah.
- **Look-ahead naratif**: artikel dan tag terbit **setelah** harga bergerak. Kalau teks masuk ke
  fitur, ia hanya boleh mengurangi ([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]).
- **Sentimen sebagai arah** = menggandakan noise: hasil negatif §F datang dari harga, bukan dari
  orang yang salah membaca berita.
- **Menukar model = menukar klaim.** `judge.py` berbentuk adapter dengan satu kontrak internal, jadi
  kandidat lain (Laya, catatan di [[11-Notes/Laya-LLM]] dan [[04-Tools/TL1 - judge]] §Kandidat) bisa
  ditukar tanpa menggeser gerbang — dan angka akurasi pihak mana pun **belum kami ukur di sini**.
- **Memasang paket pihak ketiga** = menjalankan kode dengan akses ke kredensial kita; itu keputusan
  builder, bukan langkah instalasi (peringatan yang sama dicatat di [[11-Notes/Laya-LLM]]).

## Tingkat bukti

`T1` untuk pemisahan peran teks vs peramal (praktik yang wajar, tidak teruji oleh kami) · `T2` untuk
klaim "LLM bagus untuk ekstraksi teks" (diklaim oleh literatur yang disebut `Info1.txt`, tidak kami
reproduksi) · untuk Fabius: `ADA` sebagai **mekanisme** (kode ada, gerbang ditegakkan, lihat
[[01-Agent/A3 - One-Way Gates]]) dan **belum diuji** sebagai penilai yang benar — tidak ada angka §F
untuk kalibrasi veto.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius memakai LLM sebagai penilai yang hanya boleh mengurangi; gerbang deterministik
  tetap menentukan, keluaran mentah disimpan, dan kalibrasi penilai sendiri belum kami buktikan."
- **Dilarang:** "model AI kami memprediksi harga" · "agen kami makin pintar karena LLM" ·
  "LLM sudah diuji dengan kontrol negatif di repo ini" (belum) · mengutip angka akurasi Jev/Laya
  sebagai hasil Fabius.

**Terkait:** [[QT8 - Machine Learning untuk Trading]] · [[M2 - Sentimen Sosial dan Ekstraksi LLM]] ·
[[M1 - Fear and Greed dan Indeks Sentimen]] · [[04-Tools/TL1 - judge]] ·
[[Concepts/One-Way Gate]] · [[11-Notes/Laya-LLM]]

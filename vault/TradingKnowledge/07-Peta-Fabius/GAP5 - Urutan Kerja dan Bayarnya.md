---
tags: [tk, tk-peta, "GAP5"]
---

# GAP5 - Urutan Kerja dan Bayarnya

**Keluarga:** [[00 - Hub Peta Fabius]] · **Tahap:** keputusan ([[PL4 - Memutuskan]])
**Sumber:** [[GAP1 - Matriks Metode x Tahap]] · [[GAP3 - Yang Punya Data Tapi Belum Diuji]] ·
[[GAP4 - Yang Tidak Bisa Diuji Karena Data]] · [[08-Backlog/01 - Backlog]] (tenggat **30 Sep 23:59 WIB**)

**Ringkas:** urutan, bukan daftar. Empat pertimbangan yang menentukan posisi: apakah ia **mengubah
angka yang sudah kami jual**, berapa yang harus dibayar (`nol` / `jam-proses` / `kalender` / `uang`
/ `mustahil`), apakah ia menahan pekerjaan lain, dan apakah ia masih masuk akal dengan tenggat dua
hari. Halaman ini tidak menambahkan pekerjaan baru — ia memberi nomor pada yang sudah ada di
backlog.

## Definisi yang bisa dihitung

Urutan ditetapkan oleh aturan ini, bukan oleh selera:

1. **Koreksi integritas dulu.** Apa pun yang membuat angka yang sudah diterbitkan salah harus
   diperbaiki sebelum ada uji baru — kalau tidak, hasil baru ikut tercemar ambang yang keliru.
2. **Kerjakan yang `nol` sebelum yang `uang`.** Kita belum habis bahan sendiri
   ([[GAP3 - Yang Punya Data Tapi Belum Diuji]]).
3. **Yang menahan pekerjaan lain menang atas yang berdiri sendiri.**
4. **Yang dibayar `kalender` dimulai hari ini atau tidak sama sekali** — tapi tidak pernah
   dilaporkan sebagai hasil.

## Cara pakai yang diklaim

"Kerjakan yang murah dan membuka jalur, tahan yang cantik." Bentuk konkretnya: tidak ada keluarga
sinyal baru (`S*`, `I*`, `V*`) yang boleh naik ke backlog sebelum P10–P11 selesai, karena semua
ujinya memakai ongkos dan alat skor yang sama.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| ongkos terukur satu nilai untuk semua jalur | `ADA-TAPI` | 59 bps terukur vs 20 bps warisan — [[Fakta Terukur]] §D, itu persoalan P10 |
| alat skor ⑦ yang sehat | `TIDAK-ADA` (alatnya ada, angkanya belum layak) | §H di lembar yang sama — P11 |
| hasil jatuh tempo `n ≥ 20` | `TIDAK-ADA` | seri sekarang: PAPER n=2, CHAIN n=3 (G) |
| perekaman funding per jam | `TIDAK-ADA` tapi bisa dimulai sekarang | kelas K2 di [[GAP4 - Yang Tidak Bisa Diuji Karena Data]] — P13 |
| spesifikasi swing/zona tunggal | `TIDAK-ADA` | kelas K3 — P14 |

## Uji di Fabius

Pekerjaan dianggap selesai hanya dengan artefak yang bisa dibaca orang lain — bukan "sudah saya
jalankan tadi":

| prioritas | ID | apa yang selesai terlihat sebagai | bayar |
|---|---|---|---|
| 1 | **P10** — satu model ongkos | `tools/backtest.py` dan `tools/ledger.py` memakai angka yang sama; deret lama dihitung ulang dan dicatat di [[06-Results/04 - Negative Results]] — satu "MENANG +1,5 bps" menjadi **≈ −37,5 bps** *(aritmetika di atas §D + §F; belum dihitung ulang oleh alat — justru itu isi P10)* | `nol` |
| 2 | **P11** — mekanika `maker_ledger` | blok REM SEHAT di [[Fakta Terukur]] §H lolos: median `\|net\|` masuk akal, arti `is_open_or_close` ditetapkan dengan baris mentah, MTM token hilang pesimistis | `nol` |
| 3 | **P13** — rekam funding + OI per jam | satu berkas `universe/*` baru + manifest umur, dimulai **sekarang** supaya kalender bekerja | `nol` + `kalender` |
| 4 | **P12** — uji tujuh veto | **sebagian sudah dihitung**: `tools/screen_universe.py` mencetak kohort lolos vs ditolak + outcome per alasan (§F) — dan arahnya tidak mendukung veto. Yang masih kurang = `tools/veto_study.py`: ongkos **59 bps**, median + bootstrap, satu baris verdik per veto di [[06-Results/02 - Thresholds]] (dipertahankan/dicabut/belum teruji), dan **nama tiap tes yang lolos BH ditulis** — report sekarang mencetak `passed: 5` tanpa menyebut lima yang mana | `jam-proses` |
| 5 | **P14** — spesifikasi swing/zona/gap | satu **catatan baru** di `Concepts/` + satu fungsi yang dipakai semua alat uji | `jam-proses` |
| 6 | **P15** — aliran ⑦ sebagai gerbang **turun-saja** | keputusan tercatat per kejadian (`SEARAH` / `KONTRA` / `TAK ADA DATA`) + evaluasi di `winlog`; **tidak pernah** menaikkan keyakinan | `jam-proses`, menahan P11 |
| 7 | keluarga sinyal baru (`S3`, `S5`, `S7` dengan null yang benar) | uji per keluarga + artefak | `kalender` untuk sampel |
| — | `uang`: L2/tick, likuidasi bursa, on-chain valuasi, unlock | tidak masuk sebelum submission; lihat kolom "mengubah keputusan?" di [[GAP4 - Yang Tidak Bisa Diuji Karena Data]] | `uang` |

Tiga yang pertama (P10, P11, P13) **tidak butuh data baru** — tapi hanya **P10 dan P11** yang bisa
*selesai* tanpa menunggu kalender (P13 mulai hari ini, barunya baru terasa nanti). Dengan tenggat
30 Sep, itulah satu-satunya bagian daftar ini yang boleh dijanjikan.

## Batas dan mode gagal

- **Tenggat mengubah arti daftar ini.** Yang dibayar `kalender` (Uji A, uji carry, sampel 20
  trade) tidak akan selesai sebelum submission — memulainya tetap benar, **melaporkannya sebagai
  hasil adalah kebohongan**. Klaim publik tinggal di [[10-Submissions/01 - Claims Cheat Sheet]].
- **P10 menyentuh angka yang sudah diterbitkan.** Itu mahal secara sosial dan murah secara
  aritmetika; akibatnya ada di [[06-Results/00 - Hub Results]] dan `05 - Corrections`, bukan di
  halaman ini.
- Urutan ini bisa diganti **hanya** dengan bukti baru, dan penggantian harus tercatat di
  [[00-Overview/03 - Decisions]] sebagai `F-D##`. Mengubah urutan tanpa mencatatnya = data snooping
  pada roadmap sendiri.

## Tingkat bukti

`T1` untuk daftar dan angkanya (peta keadaan: semua menunjuk [[Fakta Terukur]] atau berkas nyata —
membaca daftar bukan `T3`) · `T0` untuk perkiraan "berapa lama" — tidak ada satu pun butir di atas
yang pernah kami jalankan dari awal ke akhir.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "tiga perbaikan pertama tidak butuh data baru; dua di antaranya (P10, P11) masih bisa
  selesai sebelum tenggat, yang ketiga (P13) baru bernilai setelah kalender berjalan."
- **Dilarang:** "roadmap kami akan selesai sebelum submission" (yang bisa *selesai* tinggal **P10 dan
  P11**; P13 dimulai hari itu tapi bayarnya kalender, dan P12/P14/P15 butuh jam-proses yang tidak ada
  lagi sebelum tenggat) ·
  "kalau P15 selesai, sinyal whale ikut menaikkan keyakinan" (ia **hanya boleh menurunkan** —
  [[Concepts/One-Way Gate]]).

**Terkait:** [[GAP2 - Uji Setiap Veto Terhadap Hasil]] · [[GAP3 - Yang Punya Data Tapi Belum Diuji]] ·
[[GAP1 - Matriks Metode x Tahap]] · [[ST7 - Checklist Keputusan]] · [[08-Backlog/01 - Backlog]] ·
[[00-Overview/06 - Roadmap]]

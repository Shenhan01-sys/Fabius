---
tags: [tk, tk-peta, "GAP4"]
---

# GAP4 - Yang Tidak Bisa Diuji Karena Data

**Keluarga:** [[00 - Hub Peta Fabius]] · **Tahap:** fetching ([[PL1 - Mengumpulkan Data]])
**Sumber:** [[Fakta Terukur]] §A/§A.2/§C · [[03-Data/D4 - Dune]] ·
`Fabius\vault\06-Results\03 - Not Yet Proven.md` baris 15

**Ringkas:** sebagian besar metode di `03-Sinyal/` tidak bisa dijalankan Fabius **hari ini**, bukan
karena kami bodoh memilih, tapi karena bahan bakunya tidak ada di repo ini. Halaman ini mencatat
apa yang hilang, berapa harganya, dan — yang paling penting — apakah menutup lubang itu mengubah
sebuah keputusan. Tanpa kolom terakhir, daftar seperti ini berubah jadi wishlist langganan data.

## Definisi yang bisa dihitung

Satu metode masuk sini kalau ia menuntut **bidang data** yang tidak bisa dibaca dari clone ini dan
tidak bisa diturunkan dari bidang yang ada. Tiga kelas yang tidak boleh dicampur:

| kelas | arti | contoh |
|---|---|---|
| **K1 bidang hilang** | tidak ada jalurnya sama sekali | order book L2, delta agresor, level likuidasi |
| **K2 histori hilang** | jalurnya ada sekarang, masa lalunya tidak bisa diminta | ⑦ (jendela lihat 8–13 menit, paging diabaikan server), funding per jam |
| **K3 definisi hilang** | datanya bisa dihitung, tapi "apa yang diukur" belum disepakati siapa pun | order block, "struktur pasar", narasi mana yang "kuat" |

Penamaannya `K` (kelas), bukan `T`, supaya tidak bertabrakan dengan tingkat bukti `T0`–`T3` di
[[EV1 - Tingkat Bukti]] — dua skala berbeda yang kalau dipakai huruf sama akan terbaca sebagai satu.

Perbedaan K1/K2 penting secara taktis: K2 **boleh** dimulai sekarang dan baru bernilai nanti; K1
membayar untuk hasil yang sama sekali tidak menyentuh klaim kita tentang BSC.

## Cara pakai yang diklaim

Menutup lubang, bukan mengeluhinya. Tapi urutannya: kalau `Bayar=kalender`, kerjakan hanya kalau
ia membuka uji yang **sudah dirancang** di [[GAP3 - Yang Punya Data Tapi Belum Diuji]] — kalau
tidak, ia cuma menambah permukaan yang harus dirawat.

## Butuh data

| yang hilang | metode yang terkunci | kelas | status Fabius | jalur paling murah yang kelihatan | bayar | mengubah keputusan? |
|---|---|---|---|---|---|---|
| histori ⑦ sebelum 26 Sep 08:01Z | `O5`, `ST6`, uji kohor | K2 | `TIDAK-ADA` | tidak ada — feed tidak menyediakan riwayat, dan itu terukur | mustahil | tidak bisa dijawab surut; hanya prospektif |
| funding/OI per jam ke belakang | `U2`, uji carry | K2 | `TIDAK-ADA` | mulai rekam `premiumIndex` per jam ke `universe/` seperti `bsc-universe.jsonl` | nol + kalender | ya — mengubah veto carry dari estetika jadi teruji |
| order book L2 / tick / delta agresor | `V3`, `V4`, `V5`, `U3`, profil volum asli (`V2`) | K1 | `TIDAK-ADA` | venue yang mau menjualnya (berbayar), atau bangun rekaman sendiri di venue yang bisa diakses | uang | **tidak untuk keputusan arah** — ia mengubah cara keluar & estimasi ongkos, dan itu memang tempat kami rugi |
| level likuidasi bursa | `U3` | K1 | `TIDAK-ADA` | tidak ada jalur gratis yang kami verifikasi | uang | tidak dalam horizon 24 j kami |
| MVRV/SOPR/NUPL, exchange reserve, stablecoin supply | `O1`, `O2`, `O3` | K1+K3 | `TIDAK-ADA` | Dune (Trino) — tapi biayanya kredit per kueri + lag BSC ±1 jam ([[03-Data/D4 - Dune]]); dan metrik ini tidak terdefinisi untuk token berumur hitungan hari | uang + jam-proses | tidak untuk kandidat kita (kebanyakan berumur < 7 hari) — ya untuk narasi "kondisi pasar" |
| jadwal unlock/vesting | `O7` | K1 | `TIDAK-ADA` | tidak ada sumber seragam; sebagian terkubur di kontrak | uang + jam-proses | ya, untuk C2 (aset yang lebih tua), tidak untuk meme berumur sejam |
| data CEX (Binance/Bybit/OKX/Bitget) | `QT5`–`QT10`, arbitrase, market making | K1+K3 | `MATI-DARI-MESIN-INI` | diukur sebagai **mati dari jaringan ini** (§C: `451`, `403`, TLS terpotong) — bukan soal uang, soal pasangan sumber×jaringan | mustahil-dari-mesin-ini | tidak: major/stable bahkan sudah ditolak `STABLE_BASES` (§E) |
| harga forward untuk token tanpa perp | `GAP2`, penilaian ④ | K2 sebagian | `ADA-TAPI` | baris `px` kami sendiri — jangkauannya seumur perekam | nol | **ya**, dan ini lubang paling murah di daftar ini |
| definisi baku satu swing/zona/gap | `S3`, `S4`, `S5`, `S7`, `S2` | K3 | `ADA-TAPI` (datanya ada, definisinya tidak) | tulisan spesifikasi + satu implementasi yang dipakai semua alat | nol + jam-proses | ya — tanpa ini, tiap uji mengukur hal yang berbeda |

## Uji di Fabius

Uji yang menentukan bukan "bisakah kami mendapatkan datanya", tapi: **setelah datanya ada, apakah
sebuah keputusan berubah?** Untuk tiap baris, tulis keputusannya lebih dulu (`sisi`, `ukuran`,
`veto`, atau cuma `laporan`). Baris yang jawabannya "cuma laporan" tidak boleh mengalahkan baris
yang jawabannya "veto" — dan itu justru urutan yang paling sering terjadi di proyek seperti ini.

## Batas dan mode gagal

- **K3 tidak selesai dengan membeli data.** Order block tetap punya tiga definisi setelah kami
  punya tick. Bagian yang mahal adalah membakukan, bukan berlangganan.
- **"Terukur mati" bisa hidup lagi di tempat lain.** Runner GitHub Actions punya hal yang laptop
  ini tidak punya (OKX/Bitget membalas `200` di sana) — jadi jalur itu tidak mustahil, ia hanya
  tidak boleh mengisi kolom yang sama dengan baris yang ditarik dari laptop. Itu aturan integritas
  deret, bukan selera ([[Concepts/Point-in-Time vs Retro-updatable]]).
- Daftar ini basi secepat §C berubah. Baca ulang dengan `python -X utf8 tools/probe_egress.py`
  sebelum memutuskan membeli apa pun.

## Tingkat bukti

`T1` untuk daftar kelengkapan (peta keadaan: tiap barisnya menunjuk berkas/angka di
[[Fakta Terukur]] — **bukan** `T3`, karena membaca berkas bukan menjalankan uji) · `T0`
untuk setiap pernyataan bahwa metode yang terkunci di sini akan berguna setelah datanya ada.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "profil volum, CVD, heatmap likuidasi, MVRV, dan arbitrase CEX tidak bisa dijalankan
  dari repo ini hari ini; dua di antaranya bisa dibuka dengan perekaman sendiri, sisanya butuh
  langganan yang tidak mengubah keputusan arah kami."
- **Dilarang:** "kami belum punya edge karena datanya bayar" (data termurah kami sudah menghasilkan
  vonis negatif — §F) · "kalau kami punya L2, SMC akan teruji" (yang teruji adalah mekanismenya,
  bukan klaim penyebabnya).

**Terkait:** [[GAP5 - Urutan Kerja dan Bayarnya]] · [[GAP3 - Yang Punya Data Tapi Belum Diuji]] ·
[[QT12 - Stack Data dan Perkakas]] · [[V4 - Order Book dan Liquidity Heatmap]] ·
[[03-Data/D4 - Dune]]

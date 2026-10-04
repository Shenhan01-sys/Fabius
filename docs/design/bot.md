# /bot/[id]: design brief (4 Okt 2026)

Kontrak untuk `web/src/app/bot/[id]/`. Sistem visual = landing (`docs/design/landing.md`, vault TL23 - Sistem Visual FE).

## Proses yang diwakili

Satu bot = satu MESIN TERKUNCI: aturan (metode + satu parameter) di-hash dan dikunci di chain SEBELUM data maju ada, lalu tiap hari mesin itu mengeluarkan
niat posisi (tick) yang disegel ke chain. Halaman menjawab empat pertanyaan calon pengikut, berurutan: apa aturannya (dan kapan dikunci), apa yang
dipegang hari ini (paper), apa jejaknya hari demi hari, dan kapan ia dimatikan.

## Objek fisik + data dalam geometri

- **Kepala:** nama bot raksasa (Archivo lebar), kalimat metode, satu chip parameter, gembok + `spec_sha` (tautan tx kunci di LockRegistry).
- **01 Buku paper hari ini:** universe bot sebagai deret kubus di panel MALAM (kubus putih di latar terang tidak bisa dibedakan dari flat; cek visual 4 Okt).
  Kubus terang bercahaya = aset yang dipegang (bobot tertulis), indigo = short, redup = flat; lencana "baru"/"keluar" dibanding tick sebelumnya. Jumlah
  kubus terang = jumlah posisi. Sumber: tick terakhir di ledger publik (dibaca live di server; gagal baca = pesan galat, bukan "flat").
- **02 Hari demi hari:** satu baris kubus per hari sejak jam maju mulai (keadaan sama dengan kalender landing: sebelum kunci, tersegel, SAH, bolong), jumlah
  sinyal + lag; tiap hari yang dikomit menaut ke `/verify`.
- **03 Terkunci, urut waktu:** gembok yang berlaku untuk bot ini (ambang v1, spesifikasi, F-D16, anggaran; buku bila bot ada di buku; pembunuh bila punya
  syarat mesin) dengan cap waktu + tx, DISELIPKAN bersama "tick maju pertama ditulis" agar urutan terlihat jujur: B1/B3 menulis tick pertama SEBELUM kunci
  spesifikasi di LockRegistry, itu sebabnya bar 1 Okt = "sebelum kunci".
- **04 Uji maju F-D16:** tiga tangki (sinyal, hari settle, bulan) terisi sesuai data.
- **05 Kapan ia dimatikan:** teks pembunuh yang DIKUNCI, dalam bahasa aslinya (terjemahan bukan teks yang dikunci) + syarat mesin dari
  `engine/locks/pembunuh.lock.json` (B1-K1/K2, B3-K1/K2; snapshot `bots[].kill_rules`). Judul: "ditetapkan sebelum sinyal pertama" (genesis ledger memuat
  `spec_sha` sebelum tick pertama), BUKAN "sebelum transaksi pertama" (paper tidak bertransaksi).

- **Eksekusi demo (P119, bot yang dieksekusi: B1):** satu kartu per bar dari `ledger/eksekusi/binance-demo/<bot>.jsonl` (dibaca live): jumlah order, fee
  nyata bps, geser vs penutupan, **selisih vs isi kertas** (akurasi uji kertas, F-D92), latensi komit -> isi, pelanggaran. Kartu susulan ditandai.
  Kepala: median tiap metrik vs ambang usulan PRD §6. Akun DEMO (saldo virtual): tidak ada angka untung/rugi. Ledger belum ada = section tidak tampil.

Bot tanpa jam maju (B2, B4, B5, B6): kepala + kunci + pembunuh saja, dengan pernyataan terang "spesifikasi di-hash, tidak berjalan". Nomor section
dihitung (bot tanpa jam maju: 01 kunci, 02 pembunuh), jadi tidak ada nomor bolong. `/bot/b3-carry` -> 307 ke `/bot/B3-CARRY`; bot asing -> 404.

## Batas kejujuran

Paper; niat posisi, bukan order; tidak ada angka untung sampai settle final ada, dan itupun bukan klaim edge (F-D16 belum terpenuhi). Metode ditampilkan
dalam teks aslinya yang dikunci + glos EN.

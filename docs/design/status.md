# /status: design brief (4 Okt 2026)

Kontrak untuk `web/src/app/status/` + `web/src/app/api/status/`. Sistem visual = landing (`docs/design/landing.md`, vault TL23 - Sistem Visual FE).

## Proses yang diwakili

Satu hari operasi Fabius adalah satu putaran jam UTC: bar harian tutup 00:00Z -> berkas Binance Vision terbit ±08:40Z -> rantai GitHub `paper-ledger`
menulis tick (jendela 08:40-11:58Z, batas 12 jam) -> worker Railway mengomit akar ke SignalAnchor lalu mengungkap isinya -> penjaga LUAR (GitHub)
memeriksa komit itu -> kertas-venue menerapkan aturan venue nyata ke tick yang sama -> eksekutor demo (Railway, kunci API) memasang order di akun demo.
Halaman menjawab satu pertanyaan: **apakah mesinnya hidup hari ini, dan di stasiun mana bar hari ini berada?** Siapa pun bisa memeriksa, tanpa kunci.

## Objek fisik + data dalam geometri

- **Dial 24 jam UTC:** lingkaran = satu hari. Busur violet = jendela tick (08:40-11:58Z), titik 00:00 = bar tutup, jarum = sekarang, titik kecil = kejadian
  bar hari ini yang sudah terjadi (tick ditulis, dikomit) di posisi jamnya.
- **Rel stasiun per bot berjam maju** (bahasa sama dengan /verify): 01 bar tutup -> 02 tick ledger -> 03 dikomit -> 04 diungkap -> 05 kertas-venue (B1)
  -> 06 eksekusi demo. Lampu = kubus: menyala (OK), violet bernapas (menunggu, dengan alasan + perkiraan), merah retak (ALARM, alasan apa adanya),
  bergembok (tidak publik), bening (tidak berlaku).
- **Tangki gas committer:** saldo tBNB live dari chain 97; garis alert operator 0,01 dan garis isi-ulang builder 0,1.
- **Detak rantai GitHub:** run terakhir `paper-ledger` (dan watchdog-nya) sebagai deret kubus kecil: sukses / gagal / berjalan.
- **Kesegaran:** jam snapshot landing, blok chain, jam baca halaman ini.

## Semantik (T8, sama dengan `tools/worker_watch.py`)

- Tick: ada untuk bar yang baru tutup = OK; belum ada sebelum 12:00Z = MENUNGGU (jendela belum lewat); belum ada sesudah 12:00Z = ALARM (akan tercatat
  `gap`).
- Komit: tick ada + komit ada = OK; tick ada < 30 menit (TENGGANG_S) tanpa komit = MENUNGGU; >= 30 menit = ALARM "worker diam".
- Ungkap: revealed = n = OK; kurang = MENUNGGU sampai tenggang, lalu ALARM.
- Gagal baca sumber mana pun = TAK TERBACA (abu-abu, alasan tertulis) - BUKAN alarm, BUKAN OK.
- Eksekusi demo + mode bayangan berjalan di Railway dengan kunci dan dilaporkan ke Telegram builder: halaman menyatakan "tidak publik" (ledger eksekusi
  publik = P119, belum dibangun), tidak menebak.

## Batas kejujuran

Kesehatan operasi, bukan kinerja: tidak ada PnL, tidak ada klaim edge. Halaman tidak memegang kunci apa pun (Vercel tanpa rahasia); semua angka dibaca
saat itu juga dari GitHub raw/API publik dan RPC publik chain 97. GitHub API tanpa token dibatasi 60 permintaan/jam per IP: dibaca dengan cache 5 menit,
dan kalau dibatasi tampil "tak terbaca".

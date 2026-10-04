---
tags: [perkakas, "TL26", fe]
---

# TL26 - halaman /status (kesehatan operasi hari ini)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** brief `docs/design/status.md` · logika bersama `web/src/lib/status.ts` (dipakai `/api/status` DAN alat MCP `fabius_status`) · halaman
`web/src/app/status/page.tsx` + `web/src/components/status/StatusView.tsx` · pembaca chain `balanceOf` + `head` di `web/src/lib/fabius-chain.ts`

**Ringkas:** menjawab satu pertanyaan, untuk siapa pun dan tanpa kunci: **apakah mesinnya hidup hari ini, dan di stasiun mana bar hari ini berada?**
Kesehatan, bukan kinerja (tanpa PnL). Dibaca saat itu juga dari ledger publik (GitHub raw), Actions GitHub (API publik, cache 5 menit), dan RPC publik
chain 97; dibaca ulang tiap 2 menit + tombol "baca ulang".

**Bentuk (FE Doctrine, sistem [[TL23 - Sistem Visual FE]]):**
- **Dial 24 jam UTC:** lingkaran = satu hari; titik 00 = bar tutup; busur violet = jendela tick 08:40-11:58Z; titik abu 12:00 = batas; jarum = sekarang;
  titik putih/indigo = tick/komit bar hari ini di jam terjadinya. Di bawahnya: bar hari ini, jam sejak tutup, `maxLag` 12 j, jendela ungkap 168 j (dibaca
  dari kontrak).
- **01 Stasiun per bot berjam maju** (bahasa sama dengan /verify): bar tutup -> tick ledger -> dikomit -> dibuka -> kertas aturan venue (B1, modal 10 USDT,
  Binance + Aster, jadwal komit) -> eksekusi demo. Lampu: selesai (putih bercahaya), menunggu (violet bernapas, alasan + jam), alarm (merah), tak terbaca,
  belum (menunggu stasiun sebelumnya), tidak publik (gembok), tidak berlaku.
- **02 Mesin (panel malam):** tangki gas committer (saldo live; garis alert operator 0,01 = `ALERT_MIN_TBNB`; garis isi-ulang builder 0,1), kepala chain
  + jumlah komit SignalAnchor, jam cetak snapshot landing.
- **03 Detak:** run terakhir `paper-ledger.yml` sebagai deret kubus (sukses / gagal / berjalan + durasi), menaut ke run-nya di GitHub.

**Semantik = `tools/worker_watch.py` (T8):** tick belum ada sebelum 12:00Z = menunggu, sesudahnya = alarm (akan jadi `gap`); tick ada tanpa komit < 30
menit (`TENGGANG_S`) = menunggu, >= 30 menit = alarm "worker diam"; ungkap kurang = menunggu lalu alarm sesudah tenggang. Kertas wajar tertinggal satu bar
(harga 1 menit di jam komit baru terbit di Binance Vision keesokan harinya): "selesai" bila bar kertas terakhir >= bar - 1. Gagal baca = "tak terbaca"
(tidak pernah beres, tidak pernah alarm). Ringkasan: alarm > tak terbaca > menunggu > normal.

**Yang ia TOLAK lakukan:** menebak eksekusi demo dan mode bayangan. Keduanya berjalan di Railway dengan kunci dan dilaporkan ke Telegram builder, jadi
stasiun 06 tertulis "tidak publik; ledger eksekusi publik belum dibangun (P119)". Tidak memegang kunci apa pun.

**Alat MCP ke-9:** `fabius_status` - hasil yang sama untuk agen ("Overall WAIT at ... B1-TREND bar 2026-10-03: close ok, tick wait, commit later, ...").

**Bukti 4 Okt (lokal, `next start -p 3008`):** 08:33Z `/api/status` -> bar 2026-10-03, `wait`, tick `TICK_BEFORE_WINDOW` (jendela buka 08:40Z), komit/ungkap
belum, kertas B1 `KERTAS_BEHIND` (binance + aster 2026-10-01 SEBELUM_KUNCI), eksekusi `EXEC_PRIVATE`; B3 kertas/eksekusi tidak berlaku; gas 0,12 tBNB
`ok`; chain blok 134790796, 2 komit, `maxLag` 12 j, jendela ungkap 168 j; Actions GitHub `HTTP 403 (batas tanpa token)` dari IP lokal -> tampil "tak
terbaca". 08:40:58Z: tick berganti `TICK_IN_WINDOW`. MCP `tools/list` 9 alat; `fabius_status` -> "Overall WAIT". Peramban waktu-nyata desktop + ponsel:
dial, stasiun, tangki, detak; tanpa gulir horizontal.

**Temuan cek visual (diperbaiki):** label tengah dial menabrak angka 12 dan legenda membuat kaca lonjong -> info bar + legenda dipindah ke bawah lingkaran;
stasiun yang menunggu stasiun sebelumnya berlabel "tidak berlaku" -> lampu baru `later` ("belum"); rotasi SVG `motion` untuk jarum berisiko titik putar
salah -> jarum digambar langsung dari sudut jam.

**Terkait:** [[TL24 - halaman verify]] · [[TL25 - halaman bot]] · [[TL20 - server MCP]] · [[TL23 - Sistem Visual FE]] · [[07-Testing/T8 - Semantik Kegagalan Operator]]

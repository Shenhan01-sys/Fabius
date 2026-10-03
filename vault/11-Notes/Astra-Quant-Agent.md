---
tags: [inbox, referensi]
---

# Astra-Quant-Agent (sumber luar dari builder, 3 Okt 2026)

**Bagian dari:** [[11-Notes/00 - Hub Notes]]
**Sumber:** https://github.com/0xethanq/astra-quant-agent (dibaca 3 Okt 2026, commit `a913957` "v8.5.1", 307 bintang, 101 fork; Python + Vue). Klon dangkal
dibaca di folder sementara sesi; TIDAK masuk repo Fabius, tidak ada kodenya yang dijalankan.

**Ringkas:** "AstraQuant" = agen trading perp OKX: beberapa model LLM berdebat (makro, tren, mikrostruktur, kontrarian), seorang "CIO" model menulis niat order
JSON, lalu gerbang risiko Python deterministik boleh memveto; siklus 15 menit; faktor "7 tingkat" (funding/OI, CVD, imbalance buku, opsi, basis, VWAP, MACD).

## ⚠️ Lisensi - kodenya TIDAK boleh dipakai Fabius

AGPL-3.0 + **Commons Clause** + adendum anti-penipuan. Commons Clause melarang "Sell", yang di teks lisensinya disebut eksplisit termasuk **"paid trading signal
broadcasts"** dan langganan sinyal/copy-trading. Itu persis model bisnis Fabius (F-D70). Jadi: **nol baris kode atau prompt disalin**; yang boleh hanya gagasan
umum, ditulis ulang sendiri dengan cara kami. Catatan ini sengaja tidak menyalin isi berkas mereka selain kutipan pendek untuk rujukan.

## Yang berguna sebagai GAGASAN (urut manfaat untuk Fabius)

1. **Tabel "semantik kegagalan masukan"** (`docs/FAILURE_SEMANTICS.md` mereka): tiap masukan yang bisa gagal dibaca punya satu baris - apa yang terjadi, ARAH
   (kosakata tetap), jangkar kode, jangkar tes - dan ada tes yang memastikan jangkarnya ada dan tesnya sungguhan. Akar masalah yang mereka catat: "gagal baca
   dirender sebagai kosong" (except menelan galat -> `[]` -> hilir menganggap "tidak ada posisi/order") -> tindakan tak bisa dibalik. Ini doktrin kita
   ("tak terukur != bersih") dalam bentuk yang DIPERIKSA MESIN. Usulan: P109, terutama sebelum tahap 2 (Railway jadi penulis ledger).
2. **Arah kegagalan ditentukan oleh bisa-tidaknya tindakan dibalik:** tak bisa dibalik (hapus, tutup, timpa) -> pertahankan keadaan; bisa dibalik tapi berbiaya
   (buka posisi) -> jangan lakukan (fail-closed) dan katakan kenapa; hanya tampilan -> lanjut tapi ungkapkan kekurangannya. Cocok untuk worker kita: Vision/REST
   terlambat -> jangan tick (masih bisa sampai batas 12 jam); push gagal -> jangan tulis ulang; laporan -> tulis "tak terukur".
3. **Bacaan bar yang sedang terbentuk** (contoh di tabel mereka: tanda candle 15 menit dibaca dari bar yang baru dibuka, berubah dalam 91 detik): kelas yang sama
   dengan temuan P98 kita (bacaan REST pertama belum final). Menguatkan aturan tahap 3: baca >= +2 menit, dua bacaan identik.
4. **Gerbang audit atas tes itu sendiri** (nama berkas di `tests/audit/`: `test_skip_census`, `test_tests_cannot_pass_vacuously`, `test_no_vacuous_assertions`,
   `test_doc_paths_are_committed`, `test_env_keys_are_documented`): tes yang dilewati (skip) dihitung dan diumumkan. Relevan: uji anvil kita `skipUnless` -
   di mesin tanpa anvil ia dilewati diam-diam dan "lulus" tetap tercetak. Usulan: P110.
5. **Gerbang risiko eksekusi** (kerangka saja, untuk kelak `OperatorGuard` C-C / P74 sebelum uang nyata): batas eksposur searah = TOLAK bukan dikecilkan diam-diam;
   pemutus rugi harian di mana "tidak bisa dipastikan = tidak dilonggarkan"; jeda sesudah stop. Angka mereka (4,5 % ekuitas per trade, leverage 3-8x, R:R >= 2)
   adalah selera trader diskresioner, BUKAN bukti - tidak dipakai.

## Yang TIDAK cocok dengan Fabius

- Keputusan dagang oleh dewan LLM: bertentangan dengan peninjau deterministik (F-D72) dan dengan "sinyal = fungsi data sampai penutupan" yang bisa dihitung ulang
  siapa pun. Transkrip CoT yang disimpan bukan pra-registrasi: tidak dikomit sebelum hasil, tidak bisa direproduksi.
- Klaim "institutional-grade", "AstraQuant Prevails": README tidak menunjukkan rekam jejak maju yang bisa diperiksa. Pembeda Fabius justru itu: komit-ungkap
  on-chain sebelum hasil + pemeriksa publik ([[04-Tools/TL14 - verify_signals]]).
- Prompt caching, panel FE, notifikasi QQ: tidak relevan sekarang (notifikasi masuk P101 sebagai gagasan alert, dengan kanal pilihan builder).

**Terkait:** [[08-Backlog/01 - Backlog]] P109/P110 · [[Concepts/Unmeasured Is Not Clean]] · [[00-Overview/03 - Decisions]] F-D70/F-D72/F-D83

---
tags: [hasil, hub]
---

# Results

**Sumber:** `06-Results/`

Tempat angka tinggal. Dua jenis halaman di sini: **ambang** (apa yang harus dilewati, ditulis
sebelum hasil) dan **vonis** (apa yang terjadi). Halaman pra-registrasi tidak boleh diedit setelah
hasil keluar — koreksi lewat halaman baru, supaya urutannya bisa dipertanggungjawabkan.

## Bagian

- [[01 - Claims and Limits]] — yang terbukti vs yang tidak
- [[02 - Thresholds]] — MIN_TRADES, BH α, ongkos (20 bps sebelum, **59 bps sejak P10 28 Sep**), asal tiap angka
- [[03 - Not Yet Proven]] — daftar hidup yang belum kami buktikan
- [[04 - Negative Results]] — aturan arah mati; smart money vs kerumunan
- [[05 - Pre-registration Flow]] — uji aliran kerumunan, terkunci sebelum hasil
- [[06 - Pre-registration Horizon]] — uji horison whale + vonisnya
- [[07 - Matured Outcomes]] — hasil pertama prediksi yang di-anchor
- [[08 - Carry Study]] — veto funding kena 0 dari 2.963 settlement; 0 dari 12 uji arah lolos BH;
  carry 1,3–2,2 bps/hari vs round-trip 59 bps
- [[09 - Whale Cluster Test]] — berpasangan **di dalam token yang sama**, kelas kumulatif: K≥2
  median selisih **+393,4 bps**, CI **[+5; +1012]**, p=0,0008, lolos BH. Tiga koreksi di dalamnya:
  run 06:05Z memakai dua sumber harga (rasio px/tx 0,946), label "K≥2" awalnya bucket **eksak**
  (+508 bps untuk "tepat 2 dompet"), dan nilainya bergeser lagi setelah `px` didedup
  (5.355 baris berbagi stempel waktu). Bukti pertama bahwa kerumunan memisahkan, bukan PnL
- [[10 - Evidence Stack]] — compounding yang diuji, bukan dihitung: **lima** aspek aliran memisahkan
  sendirian (kerumunan ≥2/≥3, maker berulang, sebaran dana, USD ≥1k), dua tidak (tanpa jual-banding-
  beli, aliran lebar). Tumpukan **≥2 aspek lulus = +481 bps CI [+23; +977]**; kombinasi terkuat
  "≥2 dompet DAN uang tidak dari satu dompet" **+748,8 CI [+12; +1574]**. `fresh_token` (+7.708)
  DIBUANG sebagai artefak kebijakan pull kami sendiri. Yang menahan: cuma **12,7 %** kejadian bisa
  dinilai (6,9 % dari semua beli), satu jendela 43 jam
- [[11 - Pra-Registrasi Hari Kedua]] - halaman yang bisa **membatalkan** 09 dan 10: parameter
  dikunci (sha256 blok spesifikasi + `t_kunci` 06:13:38Z), hanya kejadian setelah kunci yang
  dinilai, dan `tools/day2_replicate.py` menolak mencetak angka sampai rekaman baru >= 12 jam.
  Dijuji: sunting spesifikasinya -> `exit=1` ("yang berubah bukan datanya, aturan mainnya")

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #hasil SORT file.name ASC
```

## Terkait

- [[Quick-Reference]] · [[Index]] · [[Conventions]]


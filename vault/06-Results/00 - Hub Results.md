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
  median selisih **+363,6 bps**, CI **[+0; +772]**, lolos BH. Dua koreksi di dalamnya: run
  06:05Z memakai dua sumber harga (rasio px/tx 0,946) dan label "K≥2" awalnya bucket **eksak**
  (+508 bps untuk "tepat 2 dompet"). Bukti pertama bahwa kerumunan memisahkan, bukan PnL

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
```dataview
LIST FROM #hasil SORT file.name ASC
```

## Terkait

- [[Quick-Reference]] · [[Index]] · [[Conventions]]


---
tags: [backlog, hub]
---

# Backlog & Epik

**Sumber:** `08-Backlog/`

Satu indeks kerja (P1..P49), dua epik, satu halaman sitasi. Folder ini sebelumnya **tidak punya hub** -
artinya dua epik dan sembilan item hari ini (P41-P49) hanya bisa ditemukan kalau orang sudah tahu
nama filenya. Itu lubang navigasi, bukan lubang data; sekarang ditutup, dan gerbang bentuk
(`hub_shape.py`) ikut memeriksa keempat unsur hub ini supaya tidak kembali bolong.

## Bagian

- [[01 - Backlog]] - indeks P1..P49 + status. **Berubah hari ini:** P41 (jembatan substrat - cakupan
  **3,1 %** terukur), P42 (satuan dampak; **sengaja ditunda** sampai vonis jatuh), P43 (E17 trailing),
  P44 (**E18 diuji: NOL**), P45 (E19 anggaran biaya - ambang spread ~21 bps), P46 (E20 slope
  kedalaman), **P47** (⑨ perekam buku + bug daftar pantau, F-D47), P48 (T5 microprice: tidak terukur,
  ditulis sebagai "belum"), P49 (E17: vonis wajib berupa bentuk distribusi, bukan untung/rugi)
- [[02 - Epik Alasan Masuk]] - epik jantung. §3d (E7/E8/E9 + pencabutannya F-D39/F-D40), §3e (E11
  umur posisi), §3f (E13/E14 rem di horison cepat)
- [[03 - Epik Teori Baru]] - **T1-T7** dari teori builder (order book + trailing stop): tiap teori
  dengan rumus, status data, desain uji, dan apa yang akan membunuhnya. §3 = aritmatika trailing yang
  sudah diukur (F-D48)
- [[04 - Riset Teori (Sitasi)]] - S1-S9 dengan URL + tanggal akses; tiga kutipan dibaca langsung dari
  halaman penerbit (Lei & Li 2009; Osler 2002; Ke & Lin 2017), plus daftar **tidak terverifikasi**
  dan satu sitasi yang **ditarik** ("Gu & Kelly 2014")

<!-- di atas: append-only oleh scripts/sync_vault.py; gloss tulisan tangan utuh -->
## Yang menunggu di folder ini

| kunci | alat | vonis (UTC) | dibaca sebagai |
|---|---|---|---|
| halaman 17 (watch) | `tools/day2_replicate.py --halaman 17` | ±14:59Z 29 Sep | replikasi kerumunan maker di `wp` |
| **E9** (lengan vol) | `tools/vol_ab.py` | **17:13:25Z** | tiga syarat + komposisi 25/25 slot |
| **E12** (5 m vs 30 m) | `tools/hold_ab.py` | **20:04:56Z** | empat syarat, termasuk umur baris harga keluar |
| **E16** (buku order) | `tools/book_prereg.py` | **21:37:45Z** | **WAJIB** bersama komposisi simbol (jangkar vs kabar, F-D47) |

Keempatnya tidak bisa dibaca sebelum jamnya - dan itu perilaku alat (`--status` menolak memvonis),
bukan disiplin hati.

```dataview
LIST FROM "08-Backlog" SORT file.name ASC
```

## Terkait

- [[00-Overview/00 - Hub Overview]] · [[00-Overview/05 - Corrections]] · [[00-Overview/06 - Roadmap]]
- [[06-Results/00 - Hub Results]] · [[07-Testing/01 - Test Commands]] · [[Concepts/One-Way Gate]]

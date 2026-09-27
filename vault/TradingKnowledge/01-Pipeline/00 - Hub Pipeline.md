---
tags: [tk-pipeline, hub]
---

# 00 - Hub Pipeline

**Sumber:** `vault/TradingKnowledge/01-Pipeline/` · peta jalurnya sudah ada di
[[01-Agent/A2 - Decision Spine]]

Tujuh tahap pekerjaan Fabius, dari data mentah sampai vonis atas diri sendiri. Lapisan ini
menjawab "permainan harus rapi dari fetching data sampai decision making" dengan cara yang tidak
menyenangkan: tiap tahap wajib meninggalkan **artefak** yang bisa dibaca orang lain, bukan log di
kepala agen. Kalau sebuah tahap tidak menghasilkan berkas, dia bukan tahap — dia opini.

Urutannya tidak bisa diputar: hasil penilaian tidak pernah boleh kembali mengubah keputusan yang
sudah di-anchor ([[Concepts/Anchored Before Outcome]]).

## Bagian

- [[PL1 - Mengumpulkan Data]] — apa saja yang harus direkam sebelum analisis apa pun, dan kenapa
  data yang direkam telat tidak bisa disusulkan
- [[PL2 - Menyaring Universe]] — fungsi penyaringan, survivorship yang dihasilkannya, dan beda
  "ditolak" vs "tidak bisa dinilai"
- [[PL3 - Menganalisis]] — klasifikasi jenis analisis dan kapan masing-masing berubah arti
- [[PL4 - Memutuskan]] — syarat sebuah pembacaan layak jadi keputusan, dan abstain sebagai hasil sah
- [[PL5 - Mengeksekusi dan Keluar]] — slippage, kapasitas keluar, dan mengapa "jual saja saat nol"
  bisa ditolak pasar
- [[PL6 - Menilai Hasil]] — ledger vs menghitung ulang, seri yang tidak boleh dicampur, sampel yang
  belum cukup
- [[PL7 - Kontrak Antar-Tahap]] — skema rekaman, tiga hash, umur snapshot, dan apa yang dilarang
  diubah setelah ditulis

## Terkait

- [[00 - Hub Trading Knowledge]] · [[Aturan Subtree]] · [[Fakta Terukur]]
- [[01-Agent/A2 - Decision Spine]] · [[01-Agent/A3 - One-Way Gates]] · [[04-Tools/00 - Hub Tools]]
- `tools/direction.py` · `tools/ledger.py` · `tools/anchor.py` · `universe/record_bsc_universe.py`

```dataview
LIST FROM #tk-pipeline SORT file.name ASC
```

---
tags: [tk-fondasi, hub]
---

# 00 - Hub Fondasi

**Sumber:** `vault/TradingKnowledge/02-Fondasi/`

Kaidah yang tetap benar apa pun metodenya. Isi folder ini bukan "teori dasar trading" untuk
dipelajari lalu ditinggalkan — tiap catatan di dalamnya adalah syarat yang membuat klaim metode di
`03-Sinyal/` bisa atau tidak bisa dipercaya. Contoh yang paling mahal: sebuah sinyal tidak punya
arti sebelum ongkosnya ditetapkan ([[FD4 - Ongkos Perdagangan]]), dan win rate bukan ukuran
kelayakan sebelum expectancy-nya dihitung ([[FD5 - Expectancy Bukan Win Rate]]).

Angka terukur yang memikul sebagian besar halaman ini: round-trip **59 bps** di venue kami sendiri,
panel whale **69,8 % menang tapi −10,4 bps per jam**, aturan arah **rugi di 12/12 aset** —
semuanya di [[Fakta Terukur]] §D/§F.

## Bagian

- [[FD1 - Struktur Pasar dan Rezim]] — tren/range, dan kenapa metode yang sama berarti berbeda di
  rezim berbeda
- [[FD2 - Support Resistance dan Level Psikologis]] — statis, dinamis, angka bulat; kapan ia
  menggerakkan harga dan kapan ia cuma ringkas dari chart
- [[FD3 - Likuiditas dan Dampak Harga]] — kedalaman, spread, kurva dampak, kapasitas keluar
- [[FD4 - Ongkos Perdagangan]] — fee, spread, slippage, carry, gas; ongkos tetap yang membunuh
  posisi kecil; ambang efektif = 2× ongkos
- [[FD5 - Expectancy Bukan Win Rate]] — aritmetika yang membuat 69,8 % tetap rugi, dan kenapa
  "win streak" bukan syarat membuka posisi
- [[FD6 - Ukuran Posisi]] — fixed fractional, Kelly fraksional, vol targeting, dan plafon kontrak
  yang sebenarnya mengikat di Fabius
- [[FD7 - Invalidation Stop dan Time-Stop]] — tiga jenis batas salah, dan kenapa time-stop keras
  dipakai di aset yang likuiditasnya bisa hilang
- [[FD8 - Volatilitas]] — realisasi vs implikasi, clustering, dan fakta bahwa vol bukan arah
- [[FD9 - Horizon Waktu dan Multi-Timeframe]] — horizon tetap, non-overlap, dan kebocoran antar-bar
- [[FD10 - Korelasi dan Risiko Keranjang]] — N posisi berkorelasi = satu posisi besar
- [[FD11 - Aturan Mengalahkan Intuisi]] — terjemahan "psikologi trading" untuk agen: gerbang
  satu-arah, pra-registrasi, larangan mem-pivot aturan setelah lihat hasil

## Terkait

- [[00 - Hub Trading Knowledge]] · [[Aturan Subtree]] · [[Fakta Terukur]]
- [[Concepts/Cost Is Fixed]] · [[Concepts/One-Way Gate]] · [[01-Agent/A4 - Trust Gating and Real-Money Rules]]
- [[06-Bukti/00 - Hub Bukti]] — fondasi ini adalah alasan bagian bukti ada

```dataview
LIST FROM #tk-fondasi SORT file.name ASC
```

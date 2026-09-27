---
tags: [tk, tk-fondasi, "FD3"]
---

# FD3 - Likuiditas dan Dampak Harga

**Keluarga:** [[00 - Hub Fondasi]] · **Tahap:** filtering ([[PL2 - Menyaring Universe]]), mengikat eksekusi ([[PL5 - Mengeksekusi dan Keluar]])
**Sumber:** [[Fakta Terukur]] §D/§E/§F (59 bps, `MIN_LIQ_USD`, kapasitas keluar) · `tools/direction.py` (gerbang ⑥) · [[02-Contracts/C3 - ExecutionVault]] (venue demo) · sisanya pengetahuan standar pasar

**Ringkas:** Likuiditas bukan "harga ada", tapi "berapa banyak bisa dijual sekarang tanpa merusak
harga sendiri". Sinyal yang tidak punya kapasitas keluar bukan sinyal — ia posisi yang tidak bisa
dibuka tanpa sekaligus membuka risiko tidak bisa menutup. Ini fondasi yang paling sering dilewati,
karena ia tidak terlihat di chart.

## Definisi yang bisa dihitung

```
spread          : ask - bid (atau mid vs harga eksekusi nyata)      -> [[V5 - Mikrostruktur Spread dan Adverse Selection]]
kedalaman (L2)  : sum qty di dalam x % dari mid, per sisi           -> butuh buku order
dampak (bentuk) : d(notional) ~ A * sqrt(notional / likuiditas_24j) # pendekatan, bukan hukum
AMM x*y=k       : jual fraksi f dari kedalaman quote -> harga turun ~ f/(1-f)  # eksak untuk kurva ini
kapasitas keluar: qty terbesar yang bisa ditutup dalam batas dampak dan waktu yang ditentukan
```

Bentuk kuadrat-akar di atas adalah **pendekatan** yang dipakai luas untuk pasar berkesinambungan;
ia bukan identitas. Untuk venue kami yang sebenarnya (pool `x·y=k`), hubungannya justru cembung dan
bisa dihitung persis — dan itu memberi pemeriksaan silang: round-trip **59 bps** untuk posisi 1 unit
di venue demo ([[Fakta Terukur]] §D) = kurva + fee 30 bps, sehingga komponen kurva ±29 bps bolak-balik
(±14,5 bps per sisi). Aritmetika dari dua angka itu, bukan pengukuran terpisah.

## Cara pakai yang diklaim

Klaim praktisi/vendor: "likuiditas tinggi = aman masuk", "volume besar berarti bisa keluar kapan
saja". Yang benar: volume adalah laju, likuiditas buku adalah persediaan, dan keduanya bisa runtuh
bersamaan. Fabius memperlakukan ini sebagai **veto**, bukan skor: satu kandidat boleh punya arah
yang bagus dan tetap tidak dapat kursi kalau keluar tidak terjamin.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| likuiditas pool (USD) per kandidat | `ADA-TAPI` | kolom `liquidity` baris universe; itu **TVL pool**, bukan jadwal order di harga — proxy, bukan kedalaman |
| ambang kapasitas keluar yang men veto | `ADA` | `MIN_LIQ_USD` 50.000 dan `exit-size <= 1 %` likuiditas; ditegakkan `tools/direction.py` (`seat_blockers`, ikut di-hash) — [[Fakta Terukur]] §E |
| order book L2 / jadwal bid-ask | `TIDAK-ADA` | tidak ada jalur di repo ini — §C |
| spread nyata di venue meme sungguhan | `TIDAK-ADA` | tidak ada venue produksi; yang terukur hanya spread kurva+fee di chain 97 — §D |
| dampak harga pada ukuran > 1 unit | `TIDAK-ADA` | yang pernah dijalankan cuma posisi 1 unit — §D/§F |
| keterjualannya token (honeypot / `can_not_sell`) | `ADA-TAPI` | gerbang ④ `tools/security_gate.py`: 5/5 kandidat membalas, 4 `OK` + 1 `UNMEASURED` — §F; status itu milik **token spot**, bukan jaminan posisi bisa ditutup |

## Uji di Fabius

Sudah dijalankan dan mencetak angka: tiga putaran rantai nyata di venue demo, **WR 0 %** dengan net
rata-rata **−59,0 bps** per putaran ([[Fakta Terukur]] §F) — dan itu memang ongkos, bukan sinyal,
karena pool kami sendiri tidak punya arus luar.

Yang belum dijalankan dan perlu diurut:

1. Kurva dampak nyata: buka pada beberapa ukuran (1 → N unit), baca `entryPx18`/`exitPx18` dari
   event `Closed`, lalu plot dampak vs ukuran. Perlu plafon kontrak dinaikkan (lihat
   `HARD_CEILING` di [[FD6 - Ukuran Posisi]]) — sampai hari ini tidak ada satu pun titik di luar ukuran 1 unit.
2. Uji ambang: bandingkan hasil token di bawah/di atas **50.000** — ambang itu "diputuskan", belum
   diuji terhadap hasil ([[GAP2 - Uji Setiap Veto Terhadap Hasil]]).
3. Semua uji butuh net di atas ongkos **pada ukuran yang diusulkan**, bukan pada ukuran 1 unit,
   karena ongkos per sisi tidak konstan terhadap ukuran.

## Batas dan mode gagal

- **TVL ≠ likuiditas keluar.** Pooled USD tidak menjanjikan kedalaman di harga tertentu; satu sisi
  buku bisa kosong sementara TVL-nya besar. Angka yang kami pakai adalah proxy dan harus disebut begitu.
- **Likuiditas bisa ditarik, bukan cuma menipis.** Karena itu `MIN_LOCK` 20 % ikut jadi gerbang
  ([[Fakta Terukur]] §E) — dan `MAX_TOP10` 45 %: satu keputusan holder bisa menghapus pasar.
- **Keluar lebih lambat dari masuk.** Di venue AMM, order masuk selalu diterima selama ada sisi
  lawan; order keluar menerima harga yang tersisa. Aset yang "bisa dibeli" tidak otomatis "bisa dijual".
- **Dampak bukan satu kali.** Keluar bertahap mengubah kurva: dua penjualan 0,5 unit tidak sama
  dengan satu penjualan 1 unit, dan keduanya bukan dua kali angka 1 unit.
- **Korelasi kapasitas.** Dua kandidat dengan likuiditas masing-masing lolos belum berarti keluar
  mereka independen: keduanya bisa bergantung pada kedalaman BNB yang sama ([[FD10 - Korelasi dan Risiko Keranjang]]).

## Tingkat bukti

`T3` untuk "ongkos round-trip di venue kami positif-bukan-nol dan negatif hasilnya" — terukur dari
event `Closed` dan suite forge ([[Fakta Terukur]] §D, [[07-Testing/T3 - Execution Suite]]) · `T2` untuk
bentuk kurva dampak kuadrat-akar (literatur, tidak kami reproduksi) · `T1` untuk TVL-sebagai-proxy ·
`T0` untuk klaim vendor "volume tinggi = selalu bisa keluar".

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius menolak kandidat yang kapasitas keluarnya tidak bisa dibuktikan, dan satu-satunya
  ongkos yang benar-benar kami ukur adalah 59 bps pada satu unit di venue demo kami sendiri."
- **Dilarang:** "sinyal kami layak diperdagangkan" · "likuiditas $50.000 cukup" (belum diuji terhadap
  hasil) · "spread kami sudah diukur di pasar meme" (belum diukur di venue mana pun).

**Terkait:** [[FD4 - Ongkos Perdagangan]] · [[FD6 - Ukuran Posisi]] · [[FD7 - Invalidation Stop dan Time-Stop]] ·
[[V4 - Order Book dan Liquidity Heatmap]] · [[O6 - Konsentrasi Holder Bundler dan LP Lock]] ·
[[PL2 - Menyaring Universe]]

---
tags: [tk, tk-setup, "ST4"]
---

# ST4 - Range dan Mean Reversion

**Keluarga:** [[00 - Hub Setup]]
**Anggota:** [[V2 - Volume Profile dan POC]] · [[FD2 - Support Resistance dan Level Psikologis]] ·
[[I2 - RSI dan Divergence]] · [[I6 - ATR dan Jarak Ternormalisasi]] · [[FD8 - Volatilitas]] ·
[[FD1 - Struktur Pasar dan Rezim]] · [[FD7 - Invalidation Stop dan Time-Stop]]
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Kombinasi D – Sideways/Range" *(resep komunitas)*

**Ringkas:** jual tepi atas, beli tepi bawah, ambil tengah (POC) sebagai magnet, pakai divergensi sebagai rem.
Setup ini hidup di satu rezim dan **membunuh di rezim sebelah**: saat range berakhir, setiap entry
mean-reversion adalah posisi melawan pergerakan terbesar. Karena itu bagian terpenting catatan ini bukan
resepnya tapi angkanya — dan semua angka di bawah berstatus ambang yang **diusulkan**, belum diukur.

**Lubang daftar topik:** "mean reversion" **tidak punya catatan sendiri** di `03-Sinyal/`. Terdekat:
[[QT5 - Statistical Arbitrage dan Pairs Trading]] (pasang-aset, bukan satu aset dalam range) dan [[QT1 - Dari Ide ke Strategi yang Bisa Diuji]].
Selama lubangnya ada, setup ini menumpang definisi pada catatan lain — itu sendiri cukup untuk membuatnya `T0`.

## Resep

| tahap | aturan | catatan |
|---|---|---|
| kondisi | harga di dalam range yang terdefinisi, bukan sedang membentuk tren | [[FD1 - Struktur Pasar dan Rezim]] |
| zona | tepi range + simpul volum (POC/HVN) | [[FD2 - Support Resistance dan Level Psikologis]] · [[V2 - Volume Profile dan POC]] |
| pemicu | sentuhan tepi + divergensi momentum | [[I2 - RSI dan Divergence]] |
| jarak | lebar range dan stop dinyatakan dalam ATR, bukan dalam harga | [[I6 - ATR dan Jarak Ternormalisasi]] · [[FD8 - Volatilitas]] |
| target | POC / sisi tengah, bukan tepi seberang | magnetnya tengah |
| invalidation | breakout terkonfirmasi (angkanya di bawah) | [[FD7 - Invalidation Stop dan Time-Stop]] |
| ukuran | plafon kontrak | [[FD6 - Ukuran Posisi]] (§E) |
| keluar waktu | tidak kembali ke tengah dalam horizon = keluar | time-stop di sini **adalah** deteksi breakout |

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam ≥ 2.400 bar untuk mendeteksi range | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari, hanya aset ber-kontrak perp ([[Fakta Terukur]] §A); C2/D ≤ 1.000 bar |
| POC sejati (distribusi harga per tick) | `TIDAK-ADA` | §C; yang bisa dihitung = volum per bar, yaitu range yang sama dengan bobot |
| RSI + pivots untuk divergensi | `ADA-TAPI` | bisa dihitung dari `close` yang ada; **tidak ada** satu baris pun di `tools/` yang menghitungnya |
| penanda rezim (range vs tren) yang terkalibrasi | `TIDAK-ADA` | `tools/direction.py` menyimpan `abs(korelasi)` pada tiga lag — **tanda dibuang di sumbernya**, jadi gerbang `\|acf\|` kami buta arah: mendeteksi "ada pola", bukan "pola apa". Perbaikannya satu baris (cetak `acf(1)` bertanda), dan itu belum terjadi |
| funding saat entry (indikasi kerumunan di tepi) | `ADA` | `premiumIndex` 608 kontrak; wired sebagai **penolak** posisi (§A), bukan sebagai pemicu |
| aliran dompet di tepi range | `ADA-TAPI` | `tools/flow_signal.py` ada dan point-in-time, tapi `direction.py`/`backtest.py`/`ledger.py` tidak membacanya |

## Uji di Fabius

Aturan "jangan melawan breakout" harus berupa bilangan yang bisa dieksekusi mesin, bukan kalimat.
Usulan yang dipakai (semuanya **ditetapkan sebelum hasil pertama dilihat**,
[[EV6 - Kalibrasi Ambang Terhadap Hasil]]):

```
range(N)     = [min(low[t-N..t]), max(high[t-N..t])]
sah_dipakai  : lebar(range) >= c * ATR(t)                 # range lebih sempit dari noise = bukan range
entry        : sentuhan tepi + close reversal kembali ke dalam
breakout(t)  : close di luar range selama m bar beruntun  -> setup MATI untuk N bar berikutnya
time-stop    : tidak kembali ke tengah dalam h bar -> keluar (deteksi breakout yang jujur)
```

N, c, m, h: *(belum diukur)*. Uji = event study pada satu kesatuan resep, horizon tetap, ongkos **59 bps**
(§D), `n >= 20` non-overlap, BH α 0,10, fold terbaik dibuang (§E). Kalau ambang "2× ongkos" (§D, dirumuskan
untuk model 20 bps) dipindah ke ongkos terukur, syaratnya gross di atas **118 bps** per trade — aritmetika
kami atas §D, dan angka itu sendiri belum diuji sebagai ambang produk.

Peringatan dari yang sudah diukur, bukan dukungan: aturan arah yang sama **dibalik** pada horizon 4 bar tetap
kalah, lebih dalam (−39,2 … −12,1 bps) (§F). Itu bukan uji mean-reversion di tepi range — itu kontrarian pada
waktu sinyal momentum — tapi ia menutup jalan pintas "kalau momentum rugi, berarti pasarnya reverting".

## Konfluensi atau gaung

Empat dari lima anggota adalah fungsi satu deret yang sama; di sini rangkapannya lebih kasar dari ST1:

| pasangan | kenapa gaung |
|---|---|
| "harga di tepi range" ↔ "RSI ekstrem" | RSI transformasi monotona dari `close` n bar terakhir; di tepi range ia **pasti** ekstrem. Dua nama satu fakta |
| POC ↔ tengah range | tanpa tick, POC kami = rata-rata berbobot bar pada window yang sama yang dipakai membuat range |
| ATR ↔ lebar range | sama-sama jarak dari `high-low`; `c * ATR` sebagai syarat range bukan informasi baru, itu penyetelan parameter |
| divergensi ↔ reversal | "harga membuat ekstrem baru, momentum tidak" — deret yang sama, window berbeda |

Konfluensi yang **benar-benar** menambah sumber di setup ini cuma dua: funding (§A, dan itu veto bukan pemicu)
dan aliran dompet ⑦ — keduanya belum masuk ke satu keputusan pun. Jadi setup hari ini = satu deret dibaca empat
cara, seperti saudaranya, dengan tambahan bahwa ia hanya sah di rezim yang alatnya sendiri belum bisa tandai.

## Batas dan mode gagal

- **Rezim berakhir → mesin rugi.** Rugi mean reversion berekor tebal: banyak untung kecil, satu breakout
  menghapusnya. Tanpa `breakout(t)` di atas, kerugiannya tidak dibatasi oleh resep.
- **Gross tipis dimakan ongkos.** Edge tipikal keluarga ini kecil per trade; ongkos terukur kami 59 bps
  (§D) dan jalur eksekusi nyata mencetak **−59,0 bps** rata-rata pada 3 putaran (§F) — itu ongkos, bukan sinyal.
- **Volum semu.** Di aset tipis, range yang terbentuk dari sedikit order besar akan "dikonfirmasi" oleh
  POC yang sebenarnya cuma beberapa transaksi ([[FD3 - Likuiditas dan Dampak Harga]]).
- **Tanpa tick, "di mana orang menumpuk" tidak bisa dilihat** — dan seluruh premis POC adalah itu.
- **Zona abu-abu pada kandidat nyata.** §F mencatat `|acf|` MARSCOIN 0,075 = 0,05–0,10 "belum tahu":
  bahkan sekarang, pada aset yang sedang kita pertimbangkan, alat kami tidak bisa menyebut rezimnya.

## Tingkat bukti

`T0` — resep komunitas; tidak ada satu pun anggotanya yang terimplementasi di repo ini, dan anggota
utamanya (mean reversion) belum punya catatan sendiri.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius belum punya detektor rezim maupun detektor range; aturan 'jangan melawan breakout'
  di atas adalah usulan yang harus dikunci sebelum diuji, bukan sesuatu yang sudah berjalan."
- **Dilarang:** "di pasar sideways mean reversion win-rate-nya tinggi" (tanpa n, tanpa ongkos) ·
  "Fabius mendeteksi range" · "POC kami dihitung dari volume profile" (yang ada hanya volum per bar).

**Terkait:** [[ST7 - Checklist Keputusan]] · [[FD1 - Struktur Pasar dan Rezim]] · [[QT2 - Backtesting yang Jujur]] ·
[[GAP4 - Yang Tidak Bisa Diuji Karena Data]] · [[Fakta Terukur]]

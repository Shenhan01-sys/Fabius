---
tags: [tk, tk-pipeline, "PL5"]
---

# PL5 - Mengeksekusi dan Keluar

**Keluarga:** [[00 - Hub Pipeline]] · **Tahap:** eksekusi · sebelumnya [[PL4 - Memutuskan]] ·
sesudahnya [[PL6 - Menilai Hasil]]
**Sumber:** `tools/execute_live.py`, `tools/direction.py` · [[Fakta Terukur]] §D/§E/§F ·
[[02-Contracts/C3 - ExecutionVault]] · [[02-Contracts/C4 - DemoPair and DemoAsset]]

**Ringkas:** Tahap ini tempat sebuah tebakan berubah menjadi biaya. Tiga hal yang tidak ada di tahap
sebelumnya muncul di sini: **dampak harga atas ukuranmu**, **kapasitas keluar**, dan kenyataan bahwa
menjual bisa **ditolak**. Fabius membangun venue-nya sendiri (kurva x·y=k plus fee, chain 97) supaya
eksekusi nyata tidak menuntut dana nyata — dan harga yang dibayar untuk itu adalah slippage pasar
meme sungguhan tidak ikut terwakili. Angka tengahnya sudah kami ukur dua kali dan keduanya bertemu:
**59 bps** round-trip diprediksi test suite, **−59 bps** realized dari event `Closed`
([[Fakta Terukur]] §D).

## Definisi yang bisa dihitung

```
dampak(size, liq)  ~ size / liq                     # pendekatan orde satu; di x*y=k membesar non-linear
kapasitas_keluar   : ukuran keluar <= 1 % likuiditas pool   # gerbang 6, ikut seat_blockers & di-hash
net_bps            = gross_bps - fee - slippage - gas - dampak
stop_mungkin       : kontrak dasar mengizinkan penjualan  AND  ada likuiditas saat kamu datang
```

```
rezim_keluar(d) : stop-loss  hanya jika pembacaan terstruktur dan keyakinan cukup
                  time-stop  selain itu -> keluar keras pada horizon (24 j di jalur kami)
```

Stop dan time-stop bukan sinonim: stop mengasumsikan harga menyentuh levelmu **dan kamu bisa
menjual**; time-stop mengasumsikan horizon adalah unit informasi. Yang pertama gagal senyap saat
likuiditas hilang; yang kedua gagal jujur ([[FD7 - Invalidation Stop dan Time-Stop]]).

## Cara pakai yang diklaim

Klaim praktis (T1): "pakai stop-loss, maka risiko terkontrol", dan "jual saat posisi kembali ke
modal" (break-even exit) sebagai aturan keluar yang aman. Keduanya diuji di Fabius dan yang kedua
kami buang: saat rug, jualannya **ditolak kontrak**, jadi "jual saat nol" bukan strategi melainkan
harapan. Aturan yang dipakai sebagai gantinya adalah memutuskan cara keluar **sebelum** masuk dan
membiarkan gerbang kapasitas yang menentukan boleh tidaknya posisi ada
([[04-Tools/TL2 - direction]]). Klaim "paper trading setara pasar nyata" juga kami tolak: venue demo
tidak punya arus luar, jadi strukturnya selalu ≈ minus ongkos.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| likuiditas pool untuk menghitung kapasitas keluar | `ADA` | gerbang ⑥; ikut di-hash lewat `seat_blockers` — [[Fakta Terukur]] §E |
| ongkos round-trip terukur di venue sendiri | `ADA` | 59 bps posisi 1 unit (test) = −59 bps realized (chain 97) — §D |
| model ongkos warisan untuk perbandingan | `ADA-TAPI` | 20 bps RT; ambang efektif 2× ongkos — **P10 terbuka**: 20 bps belum disatukan dengan 59 bps — §D |
| order book / kedalaman bid-ask nyata | `TIDAK-ADA` | tidak ada jalur L2 — §C; tanpa itu spread hanya bisa disimpulkan, tidak diukur |
| partial fill | `TIDAK-ADA` | venue kami selalu mengisi penuh di kurva; **fill parsial adalah properti pasar, bukan properti repo ini** |
| venue pasar nyata (CEX/DEX publik) | `MATI-DARI-MESIN-INI` | Binance `451` · Bybit `403` · OKX/Bitget terpotong TLS, terukur 24 Sep — §C |
| gas nyata di mainnet | `TIDAK-ADA` | yang terukur 0,10 gwei di testnet 97 — §D |

## Uji di Fabius

```
python -X utf8 tools/execute_live.py --status
python -X utf8 tools/execute_live.py --open-long --symbol <SYM>
python -X utf8 tools/execute_live.py --close --symbol <SYM>
forge test --match-contract ExecutionVaultTest
```

Empat pagar yang membuatnya eksekusi, bukan simulasi yang mengaku: posisi **tidak bisa lahir** dari
keputusan yang tidak ter-anchor (`NoAnchorHash`); `killSwitch` mematikan; ukuran dipotong plafon
(`dailyCap` default 5 unit, `maxPositionQuote` 1 unit, `HARD_CEILING = 10` — dinaikkan ke 1.000 tetap
dipotong ke 10); dan harga masuk/keluar dibaca dari **event**, bukan dari angka yang agen tulis
([[Fakta Terukur]] §E, [[02-Contracts/C3 - ExecutionVault]]). Yang harus lolos sebelum eksekusi
disebut berhasil: ongkos nyata di ukuran itu dilaporkan **lebih dulu**, karena dia menentukan angka
berapa pun yang boleh disebut untung ([[06-Results/06 - Pre-registration Horizon]]).

## Batas dan mode gagal

- **Ongkos itu tetap, modalku yang mengecil:** pada posisi kecil porsi biaya membesar — alasan
  ukuran $0,5–1 kalah sebelum sinyalnya dinilai ([[Concepts/Cost Is Fixed]]).
- **Jalur nyata kami mengukur ongkos, bukan sinyal:** 3 putaran chain, `WR 0 %`, rata-rata −59,0
  bps — pool sendiri tanpa arus luar ([[Fakta Terukur]] §F). Membacanya sebagai "strategi rugi" atau
  sebagai "strategi untung" sama-sama salah.
- **Honeypot adalah properti token spot:** ④ membuktikan dasar harga perp tidak bisa disandera,
  **bukan** bahwa posisi perp bisa ditutup di venue-nya ([[04-Tools/TL3 - security_gate]]).
- **Kurva kami bukan kurva mereka:** dampak di pool yang ada manusia jual-beli-nya tidak bisa
  direplikasi dengan menggeser fee ([[02-Contracts/C4 - DemoPair and DemoAsset]]).
- **Dua angka di seri yang berbeda jangan digabung:** paper dinilai terhadap bar harga pasar nyata,
  chain dinilai dari fill ([[PL6 - Menilai Hasil]]).
- **Eksekusi adalah tempat strategi bernegatif-ekspektasi terlihat seperti bug venue** — kalau hasil
  selalu ≈ minus ongkos, yang salah biasanya tahap 4, bukan tahap 5.

## Tingkat bukti

`T3` untuk besaran ongkos di venue sendiri (dua pengukuran saling mengunci: prediksi test suite dan
realized dari event; [[07-Testing/T3 - Execution Suite]]) · `T1` untuk aturan kapasitas keluar dan
pemilihan rezim keluar (praktik yang wajar) · `TIDAK ADA UJI` untuk slippage pasar meme sungguhan —
tidak ada jalurnya, jadi jangan ditulis seolah terwakili.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami bisa mengeksekusi posisi nyata di chain kami sendiri dan membaca kembali ongkos
  serta hasilnya dari event, dengan plafon yang dipotong kontrak bukan diminta izin."
- **Dilarang:** "slippage kami mewakili pasar BSC" · "stop-loss kami selalu bisa dieksekusi" ·
  "Fabius trading di venue nyata" · "hasil −59 bps membuktikan sinyal kami buruk" (itu ongkos, di
  venue tanpa arus).

**Terkait:** [[PL4 - Memutuskan]] · [[PL6 - Menilai Hasil]] · [[PL7 - Kontrak Antar-Tahap]] ·
[[FD3 - Likuiditas dan Dampak Harga]] · [[FD4 - Ongkos Perdagangan]] · [[QT10 - Eksekusi Algoritmik]] ·
[[O8 - MEV dan Sandwich]] · [[Concepts/Cost Is Fixed]]

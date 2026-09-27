---
tags: [tk, tk-fondasi, "FD10"]
---

# FD10 - Korelasi dan Risiko Keranjang

**Keluarga:** [[00 - Hub Fondasi]] · **Tahap:** keputusan ([[PL4 - Memutuskan]])
**Sumber:** [[Fakta Terukur]] §A/§C/§E/§F · [[06-Results/04 - Negative Results]] §6 (korelasi antar-simbol tidak dibetulkan) · sisanya pengetahuan standar pasar

**Ringkas:** Tiga posisi yang lolos gerbang satu per satu bisa merupakan satu taruhan yang ditulis
tiga kali. Risiko keranjang tidak terlihat di halaman mana pun yang menilai satu aset, dan ia muncul
justru saat penilaiannya paling dibutuhkan: korelasi naik ketika pasar berhenti berpikir sebuah
memecoin bisa dinilai sendiri.

## Definisi yang bisa dihitung

```
korelasi         : rho_ij = corr(r_i, r_j) pada horizon keputusan (return log bar yang sama)
varians keranjang: sigma_p^2 = sum_i w_i^2 sigma_i^2 + 2 sum_{i<j} w_i w_j rho_ij sigma_i sigma_j
N efektif        : 1 / sum_i w_i^2  (untuk rho = 0); dengan rho -> 1, N efektif -> 1
satu taruhan     : aset yang berbagi driver: dasar harga yang sama, basis likuiditas yang sama,
                   atau narasi yang sama
stres keranjang  : kerugian serentak pada rho = 1 + satu faktor bersama (mis. BNB turun X %)
```

Bentuk yang paling sering disalahpahami: `rho` antar-aset spekulatif **bukan konstanta**. Ia naik di
saat `risk-off` — jadi diversifikasi yang dihitung dari rata-rata sejarah menjual perlindungan di
keadaan di mana perlindungan itu ditagih.

## Cara pakai yang diklaim

Klaim komunitas: "jangan taruh semua di satu koin", "sebar ke 10 meme", "sektar berbeda = aman".
Yang berlaku: sebar **driver**, bukan **ticker**. Di BNB Chain, memecoin memakai BNB untuk gas,
dihargakan terhadap BNB/USDT, dan kontrak perp yang bisa kami hargai sendiri semuanya bervenue
BNB-native; sentimen mereka satu sumber perhatian. Sepuluh ticker bisa berarti satu posisi di
likuiditas BNB + satu posisi di perhatian.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| return per aset pada jam yang sama (untuk matriks korelasi) | `ADA-TAPI` | 9.599 bar 1 jam per simbol ber-perp (§A); cache `tools/bars.py` — **tidak ada satu pun kode yang menghitung korelasi** |
| plafon yang menjumlah eksposur | `ADA` | `dailyCap` §E menjumlah notional per hari; ia tidak bertanya apakah dua posisi satu taruhan |
| satu posisi per aset (bukan per taruhan) | `ADA` | `AlreadyOpen` keyed per token di `contracts/ExecutionVault.sol` |
| pembedaan aset yang bisa dipilih (bukan likuiditas stablecoin) | `ADA` | `STABLE_BASES` menyaring base stablecoin/wrapped (USDT/USDC/BUSD/FDUSD/DAI/TUSD/USD1/USDD/USDE + BTCB/WBNB/BNB/ETH) dari daftar yang bisa dipilih — §E, [[01-Agent/01 - Asset Classes and Seats]] |
| penanda `risk-off` lintas pasar (DXY, indeks, spread) | `TIDAK-ADA` | tidak ada sumber Makro di repo; satu-satunya narasi eksternal adalah berkas GDELT (§C) |
| korelasi funding/OI lintas aset | `TIDAK-ADA` | funding & OI hanya pembacaan saat ini, tanpa histori per aset — §C |
| risiko satu-pasokan-data (sumber × jaringan) | `ADA-TAPI` | terukur: `api.binance.com` 451 dan Bybit 403 di runner; OKX/Bitget terpotong TLS di laptop — §C |

## Uji di Fabius

Yang perlu dijalankan, belum ada perintahnya (`tools/basket_risk.py` — **belum ditulis**):

1. Matriks korelasi rolling (jendela 30/90 hari) dari cache bar yang **sudah ada** — ini murah dan
   persis jenis lubang "punya data, belum diuji" ([[GAP3 - Yang Punya Data Tapi Belum Diuji]]).
2. Laporkan **N efektif** kandidat yang sedang dipertimbangkan, dan hasil stresnya pada `rho = 1`.
3. Uji satu faktor: kalau BNB turun X %, berapa kandidat yang ikut; ini yang menentukan apakah
   "kursi" benar-benar tersebar. *(belum diukur)*.
4. Koreksi statistik harus dipakai di level yang benar. Hari ini BH α 0,10 jalan **per token**
   (§E), dan [[06-Results/04 - Negative Results]] §6 mencatat bahwa 12 token itu bergerak dengan satu
   pasar yang sama — jadi "0 dari 12" bukan 12 percobaan bebas. Angka itu tidak membuat hasilnya
   jadi positif; ia membuat klaim "sudah diuji 12 kali" terlalu kuat.

## Batas dan mode gagal

- **Gerbang per-aset buta terhadap keranjang.** `MIN_LIQ_USD`, `MAX_TOP10`, `MIN_LOCK` (§E) semuanya
  bicara satu token; tidak ada satu pun yang bilang "dua token ini satu nasib". Kursi yang lolos
  sendiri-sendiri adalah hasil penjumlahan yang belum dijumlahkan.
- **Korelasi datanya, bukan cuma korelasi pasarnya.** Satu perekam, satu venue, satu jaringan
  keluar: kalau salah satu mati, semua kandidat hilang bersamaan (§C). Itu risiko keranjang juga,
  dan ia tidak muncul di deret harga mana pun.
- **Korelasi saat risk-off = korelasi saat stop paling mungkin kena.** Ketiganya satu peristiwa
  ([[FD7 - Invalidation Stop dan Time-Stop]], [[FD8 - Volatilitas]]).
- **N posisi sama besar pada `rho -> 1` bukan N / risiko, melainkan N × ukuran.** Yang mengecil
  bukan probabilitas rugi, tapi variasi pelindungnya.
- **Duplikasi sinyal.** Bila arah dua kandidat datang dari fitur yang sama (`ret24` + SMA24, lihat
  [[FD1 - Struktur Pasar dan Rezim]]), keduanya bukan konfirmasi; mereka gema — dan gema dibayar
  dua kali ongkos ([[FD4 - Ongkos Perdagangan]]).

## Tingkat bukti

`T2` untuk fakta "korelasi naik saat risk-off" (stylized fact, literatur ada, tidak kami reproduksi
di aset kami) · `T1` untuk rumus varians keranjang dan N efektif · untuk Fabius: **belum diukur** —
belum ada satu pun angka korelasi yang dicetak perkakas kami, dan kami sudah menulis sendiri bahwa
korelasi antar-simbol tidak dibetulkan dalam uji arah.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami belum mengukur korelasi antar-kandidat; yang kami tahu, uji per-token tidak
  setara dengan 12 percobaan bebas, dan plafon harian menjumlah notional tanpa bertanya apakah
  itu satu taruhan."
- **Dilarang:** "portofolio kami terdiversifikasi" · "5 kursi = 5 taruhan independen" ·
  "risiko kami tersebar karena asetnya berbeda nama".

**Terkait:** [[FD6 - Ukuran Posisi]] · [[FD8 - Volatilitas]] · [[FD1 - Struktur Pasar dan Rezim]] ·
[[M3 - Narasi Sektar dan Rotasi]] · [[M5 - Makro dan Korelasi Silang-Pasar]] · [[QT11 - Portofolio Strategi]] ·
[[GAP3 - Yang Punya Data Tapi Belum Diuji]]

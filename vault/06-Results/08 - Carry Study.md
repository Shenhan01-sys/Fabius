---
tags: [results]
---

# 08 - Carry Study

**Sumber:** `tools/carry_study.py` → `decisions/carry-study-20260928T024148Z.json`
(`rows_sha256=0x810b8d90341b02…`) · bahan: [[03-Data/D6 - Funding and OI History]] ·
dijalankan 28 Sep 2026 02:41Z

**Ringkas:** funding sekarang punya histori, jadi pertanyaan "apakah veto funding kami berguna, dan
apakah carry bisa jadi strategi" berhenti jadi opini. Jawabannya tiga-dua-nol: **veto itu tidak
pernah menyala** (0 dari 2.963 settlement dalam 97 hari), **tidak ada satu pun basis yang lolos**
uji arah 24 jam (median + bootstrap + BH, 12 uji), dan **carry riilnya 1,3–2,2 bps per hari** -
butuh 27–45 hari hanya untuk menutup satu round-trip 59 bps, sebelum menghitung risiko harga sama
sekali. Tidak ada yang dihapus dari hasil sebelumnya; yang berubah adalah statusnya: dari
"mungkin salah" menjadi "terukur tidak pernah punya kesempatan benar".

## A. Veto funding: 0 dari 2.963

`tools/direction.py` menolak posisi saat `|funding| > 0,05 %/4 jam`. Funding venue lain berinterval
8 jam, jadi padanan aritmetiknya `0,10 %/8 jam`. Dibaca pada dua venue, enam basis, 66–97 hari:

| basis | max \|f\| Bybit | max \|f\| OKX | kejadian > 0,10 %/8j |
|---|---|---|---|
| BNB | 0,0256 % | 0,0114 % | 0 |
| BTC | 0,0100 % | 0,0100 % | 0 |
| ETH | 0,0100 % | 0,0100 % | 0 |
| SOL | 0,0179 % | 0,0118 % | 0 |
| DOGE | 0,0132 % | 0,0100 % | 0 |
| XRP | 0,0184 % | 0,0244 % | 0 |
| **total** | | | **0 dari 2.963 (0,00 %)** |

Ini menaikkan satu baris dari "belum terukur" menjadi terukur: [[06-Results/03 - Not Yet Proven]]
baris 8 dulu cuma punya satu pembacaan hari itu dan menduga "satu hari tidak membuktikan apa pun".
Sembilan puluh tujuh hari membuktikan sesuatu: **ambang itu tidak pernah punya kesempatan menyala di
enam aset ini**. Yang belum terbukti: apakah ambangnya salah untuk **memecoin berumur sejam** -
aset yang justru kami tradingkan, dan aset yang tidak punya deret funding di daftar ini.

## B. Funding ekstrem vs arah 24 jam - 12 uji, 0 lolos

Kejadian = settlement dengan `|rate| >= p90` serinya sendiri; arah dagang = **lawan kerumunan**;
harga = bar 1 jam Aster; horizon 24 jam, non-overlap; statistik = median + bootstrap 5.000
(seed 20260928) + tanda-uji binomial eksak; koreksi BH α 0,10 lintas 12 uji.

| basis | sumber | n | median bps | CI 95 % | mean bps | p (satu arah) |
|---|---|---|---|---|---|---|
| BNB | okx | 66 | −2,2 | [−58,8; +17,8] | −37,6 | 0,731 |
| BNB | bybit | 44 | −11,0 | [−58,6; +61,2] | −44,6 | 0,774 |
| BTC | okx | 19 | −13,4 | [−155,9; +36,7] | −80,9 | 0,820 |
| BTC | bybit | 14 | **+60,2** | [−123,0; +128,4] | −88,7 | 0,605 |
| ETH | okx | 17 | −46,4 | [−168,7; +80,1] | −60,7 | 0,686 |
| ETH | bybit | 12 | **+51,0** | [−145,5; +159,4] | −95,7 | 0,387 |
| SOL | okx | 29 | −96,8 | [−208,2; +85,1] | −93,3 | 0,868 |
| SOL | bybit | 24 | −121,7 | [−266,3; +80,5] | −184,3 | 0,846 |
| DOGE | okx | 46 | +4,3 | [−18,6; +93,3] | −49,3 | 0,329 |
| DOGE | bybit | 28 | **+29,0** | [−136,4; +92,3] | −94,2 | 0,425 |
| XRP | okx | 38 | **+41,0** | [−90,1; +85,1] | −105,0 | 0,314 |
| XRP | bybit | 26 | **+54,9** | [−174,2; +180,3] | −118,3 | 0,423 |

`verdict: NETAS - tidak ada satu pun basis yang net positif dengan ongkos terukur`.

**Studi ini dijalankan dua kali dalam 11 menit dan keluaran statistiknya berbeda.** Run 02:30:54Z
(`rows_sha256 0xa52b3dab661dde01…`) hanya menghasilkan kejadian pada **BTC** - 10 dari 12 kelompok
berstatus "tidak ada bar". Run 02:41:48Z (`0x810b8d90341b02…`) menghasilkan 12 kelompok penuh yang
ditabel di atas. Yang berubah bukan pasarnya: **cache bar kami sendiri terisi di antara keduanya**
(`tools/bars.py` menulis ke `data/klines/`, dan halaman pertama belum menaruh 140 hari untuk enam
simbol). Pelajaran yang berlaku umum di vault ini: `rows_sha256` membuktikan **deret mana** yang
dihasilkan, bukan bahwa hasilnya bisa muncul ulang di mesin lain pada hari lain - jadi kalau sebuah
angka bisa berubah karena cache, cache-nya harus ikut disebut. Artefak yang dikutip halaman ini
adalah run kedua; yang pertama ditinggalkan di `decisions/` justru sebagai jejak.

Yang justru paling berguna dari tabel ini bukan nol-nya, tapi empat baris bermedian positif:
BTC/bybit median **+60,2** dengan mean **−88,7**, dan CI yang memotong nol lebar-lebar. Kalau
seseorang mengambil median empat baris itu, dia menemukan "strategi"; kalau dia melihat CI-nya, dia
melihat nol. Selisih median/mean sebesar itu pada n=12–28 adalah distribusi, bukan sinyal -
contoh paling bersih dari [[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]] dan
[[TradingKnowledge/EV2 - Jebakan Backtest]] dalam satu tabel.

## C. Carry vs ongkos

rata `|funding|` per venue × 3 settlement/hari, dalam bps per hari, melawan 59 bps round-trip
([[Concepts/Cost Is Fixed]]):

| pasangan | bps/hari | hari untuk menutup satu round-trip |
|---|---|---|
| BNB (bybit / okx) | 2,2 / 2,2 | 26,7 / 26,8 |
| ETH | 1,4 / 1,3 | 41,7 / 44,7 |
| BTC | 1,4 / 1,6 | 42,1 / 36,5 |
| SOL | 1,8 / 1,5 | 33,2 / 39,9 |
| DOGE | 1,8 / 2,0 | 33,6 / 29,9 |
| XRP | 1,7 / 1,8 | 33,9 / 32,8 |

Angka "hari" itu **batas bawah yang menipu**: dia mengasumsikan posisi netral arah yang tidak pernah
membayar slippage masuk-keluar dan tidak pernah kena likuidasi. Untuk Fabius yang satu kaki dan spot
di venue demo, carry tidak bisa diambil sama sekali - tidak ada kaki pendek. Yang boleh dikatakan:
**yield funding di aset besar nyata tapi lebih kecil dari ongkos satu putaran kami.**

## Batas yang menempel di halaman ini

- Funding venue lain, harga forward venue lain lagi (Aster). Kami membandingkan dua dunia yang
  berbeda; itu uji vetansi, bukan uji strategi.
- 12 uji, dan horizon/ambang/p90 **dipilih sebelum** tapi tetap satu keluarga hipotesis - BH sudah
  dipakai untuk itu; tidak ada satu pun yang lolos.
- Deret 8 jam tidak menjawab "apakah funding naik dalam 4 jam terakhir" yang dipakai kode kami;
  untuk itu butuh Aster `premiumIndex` yang direkam per jam (masih terbuka, lihat P13 baru).
- Aset yang benar-benar kami tradingkan (memecoin baru) tidak ada di tabel ini karena tidak punya
  funding. Jadi halaman ini **tidak** membuktikan veto kami salah untuk memecoin - dia membuktikan
  veto kami tidak pernah teruji, dan salah alamat.

Baca ulang: `python -X utf8 tools/carry_study.py` · artefak `decisions/carry-study-20260928T024148Z.json`

**Terkait:** [[03-Data/D6 - Funding and OI History]] · [[06-Results/04 - Negative Results]] ·
[[06-Results/03 - Not Yet Proven]] · [[TradingKnowledge/U2 - Funding Rate dan Basis]] ·
[[TradingKnowledge/QT6 - Funding dan Basis Arbitrage]] · [[TradingKnowledge/FD4 - Ongkos Perdagangan]]

---
tags: [tk, tk-fondasi, "FD7"]
---

# FD7 - Invalidation Stop dan Time-Stop

**Keluarga:** [[00 - Hub Fondasi]] · **Tahap:** eksekusi ([[PL5 - Mengeksekusi dan Keluar]]), mengikat keputusan ([[PL4 - Memutuskan]])
**Sumber:** [[Fakta Terukur]] §D/§E/§F · `tools/direction.py` (rezim stop/time, `TIME_STOP_H`) · `tools/ledger.py` (urutan sentuh, `AMBIGU`) · [[02-Contracts/C3 - ExecutionVault]]

**Ringkas:** Stop menjawab "pada keadaan apa tesis saya salah", time-stop menjawab "berapa lama saya
boleh salah tanpa tahu". Di aset yang bisa kehilangan likuiditasnya, time-stop bukan pelengkap — ia
rem utama, karena level harga hanya melindungi kalau jualan **diterima**. Fabius menuliskan keduanya
ke dalam keputusan; yang menegakkan baru satu: yang di kontrak, bukan yang di harga.

## Definisi yang bisa dihitung

```
stop teknis    : level = swing low/high terakhir di luar mana tesis patah   -> butuh level ([[FD2 - Support Resistance dan Level Psikologis]])
stop volatiler : level = entry -+ k * ATR(t)                                 -> tidak butuh struktur, hanya jarak
time-stop      : keluar pada horizon H, apa pun harganya                    -> invalidasi oleh waktu
invalidasi     : peristiwa data yang membuat `side` salah SEBELUM stop kena (mis. ④ jadi BLOCKED)
kerugian nyata : |entry - fill_keluar| + spread + dampak + fee               -> SELALU lebih dalam dari level stop
```

`tools/direction.py` memakai stop volatiler: `1,5 * ATR` untuk stop, `3,0 * ATR` untuk target, dengan
`regime` = `stop-loss` (yakin, pola terukur) atau `time-stop` (tidak yakin), `TIME_STOP_H` 24 jam.
Docstring-nya menyebut "stop di struktur (ATR/swing)" — yang dihitung di kode **hanya ATR**; tidak
ada satu pun level struktur di jalur itu. Nama parameter dan isi parameter harus disebut bedanya.

## Cara pakai yang diklaim

Klaim praktisi: stop sempit di bawah level = risiko kecil, R:R 2:1 = "matematika menguntungkan".
Kedua-duanya mengandaikan fill pada level. Cara pakai yang kami anggap jujur: stop **didefinisikan
sebelum** hasil, hasil dilaporkan pada dua jalur (kena stop ATAU jatuh tempo), dan kerugian
diekspresikan dalam fill nyata, bukan level yang dimaksud.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| bar 1 jam untuk menyentuh/menjelekkan level | `ADA-TAPI` | Aster 9.599 bar — §A; bar 1 jam **tidak** bisa menjawab "stop atau target yang lebih dulu di dalam bar yang sama" |
| rekaman keputusan + levelnya | `ADA` | `entry_ref`/`stop`/`target` ikut `decisionHash`; `tools/ledger.py` membacanya dari rekaman, bukan menghitung ulang |
| status hasil yang belum jatuh tempo | `ADA` | `BELUM JATUH TEMPO` dipisah dan tidak ikut agregat (`tools/ledger.py`) |
| stop yang ditegakkan otomatis | `TIDAK-ADA` | tidak ada pemicu harga di `contracts/ExecutionVault.sol` maupun `tools/execute_live.py` — menutup posisi adalah panggilan |
| order book / likuiditas saat trigger | `TIDAK-ADA` | tidak ada L2 dan tidak ada heatmap likuidasi — §C |
| keandalan jalur keluar (RPC, gas, jaringan) | `ADA-TAPI` | "bisa diakses" itu properti sumber×jaringan (§C); guard lama menolak karena floor 1 gwei sementara live 0,10 gwei (§D) |

## Uji di Fabius

Yang terukur: dua prediksi yang jatuh tempo **kedua-duanya** keluar di horizon (time-stop), dengan
hasil **+1,5 bps** dan **−146,3 bps** net (§F) — keduanya keluar dalam **12 menit** satu sama lain
(18:51Z dan 19:03Z) dan berselisih **148 bps** (aritmetika §F), yang artinya aturan kami tidak
membedakan keduanya. Tiga putaran rantai ditutup manual, rata-rata
**−59,0 bps** (§F). `tools/ledger.py` menulis `AMBIGU` kalau stop dan target tersentuh di bar yang
sama — pilihan yang tidak boleh diambil kemudian.

Uji yang belum ada: distribusi hasil **per rezim** (`stop-loss` vs `time-stop`) pada `n >= 20`
non-overlap (§E), dengan kerugian dilaporkan sebagai fill nyata. Perintahnya belum ditulis;
yang tersedia `tools/ledger.py` dan `tools/backtest.py` (yang terakhir hanya menilai horizon tetap,
bukan jalur stop).

## Batas dan mode gagal

- **Stop adalah order, bukan dinding.** Setelah trigger, yang terjadi adalah penjualan pasar di
 spread + dampak yang tersedia waktu itu; saat berita buruk, keduanya melebar bersamaan
  ([[FD3 - Likuiditas dan Dampak Harga]], [[FD8 - Volatilitas]]).
- **Gap menembus level.** Aset yang bisa hilang likuiditasnya tidak pernah memberi harga stop;
  karena itu time-stop + ukuran kecil dipakai di rezim "tidak yakin" (`tools/direction.py`): yang
  membatasi kerugian adalah **ukuran × waktu**, bukan level harga.
- **Stop volatiler melebar saat vol naik.** Jarak membesar, dan kalau ukuran tidak ikut menyusut,
  risiko per trade membesar justru di keadaan paling buruk — di Fabius menyusutnya tidak terjadi,
  karena ukuran datang dari plafon kontrak ([[FD6 - Ukuran Posisi]]).
- **Rem kontrak tidak melepaskan posisi.** `HARD_CEILING` dan `killSwitch` membatasi berapa banyak
  yang boleh **dijanjikan berikutnya**; keduanya tidak memaksa keluar yang sudah ada. Gerbang
  satu-arah hanya boleh mengurangi eksposur masa depan, dan itu harus disebut apa adanya.
- **Time-stop menghitung ongkos lebih lama.** Memegang sampai horizon membayar carry dan dua kaki
  ongkos; kalau horizon dipakai karena "tidak yakin", ia sedang membeli waktu dengan uang
  ([[FD4 - Ongkos Perdagangan]]).
- **Jendela penilaian bolong.** Penilaian memakai bar yang direkam; satu jam yang terlewat bukan
  cuma data hilang, tapi pertanyaan yang tidak bisa dijawab lagi (§B).

## Tingkat bukti

`T1` untuk taksonomi stop (kerangka standar) · `T3` untuk "kedua prediksi yang jatuh tempo keluar
lewat time-stop, dengan hasil berlawanan 148 bps" — angka 148 itu aritmetika dari dua angka §F
(`+1,5` dan `−146,3`), bukan pengukuran ketiga · `T0` untuk
"stop kami membatasi kerugian" — tidak ada pemicu yang menegakkannya di kode mana pun.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "fabius menuliskan stop, target, dan horizon ke dalam keputusan yang di-hash, menilai
  keduanya, dan menandai ambiguitas urutan sentuh; yang belum ada adalah eksekusi stop otomatis."
- **Dilarang:** "risiko kami dibatasi 1,5 ATR" · "killSwitch menutup posisi" · "time-stop = keluar
  di harga masuk".

**Terkait:** [[FD6 - Ukuran Posisi]] · [[FD3 - Likuiditas dan Dampak Harga]] ·
[[FD2 - Support Resistance dan Level Psikologis]] · [[I6 - ATR dan Jarak Ternormalisasi]] ·
[[U3 - Level Likuidasi dan Cascade]] · [[Concepts/One-Way Gate]] · [[PL5 - Mengeksekusi dan Keluar]]

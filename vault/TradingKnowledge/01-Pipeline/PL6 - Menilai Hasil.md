---
tags: [tk, tk-pipeline, "PL6"]
---

# PL6 - Menilai Hasil

**Keluarga:** [[00 - Hub Pipeline]] · **Tahap:** penilaian · sebelumnya [[PL5 - Mengeksekusi dan Keluar]] ·
kontrak antar-tahap: [[PL7 - Kontrak Antar-Tahap]]
**Sumber:** `tools/ledger.py`, `tools/winlog.py`, `tools/backtest.py` · [[Fakta Terukur]] §E/§F/§G/§H ·
[[04-Tools/TL5 - ledger]]

**Ringkas:** Menilai hasil berarti menutup prediksi **dari rekaman**, bukan menghitung ulang apa yang
sebenarnya kita harapkan terjadi. Tiga keadaan wajib dipisah sejak awal: menang, kalah, dan **belum
jatuh tempo** — ditambah satu yang paling sering dipakai curang: **AMBIGU** ketika stop dan target
mungkin terjadi di bar yang sama. Fabius mengukur dua seri yang tidak pernah digabung (paper vs
chain), dan hari ini dua-duanya berada jauh di bawah ambang sampel apa pun: `n = 2` dan `n = 3`
([[Fakta Terukur]] §G).

## Definisi yang bisa dihitung

```
net_bps(i)   = gross_bps(i) - ongkos_round_trip        # yang dilaporkan selalu `net`
hasil(i)     : MENANG | RUGI | AMBIGU | BELUM_JATUH_TEMPO
BELUM_JATUH_TEMPO -> tidak ikut agregat, sisa jam dicetak
expectancy   = sum(net_bps) / n          # BUKAN win_rate
syarat_klaim : n >= 20 non-overlap AND expectancy > 0 AND lolos BH alpha 0,10
               AND tetap > 0 setelah fold terbaik dibuang  -- F-D16, [[Fakta Terukur]] §E
```

Satu sampel = satu peristiwa pasar, bukan satu baris laporan: dedupe pada level peristiwa (simbol,
sisi, entry, bar masuk, horizon), karena hash keputusan berbeda tiap siklus dan tanpa pagar itu satu
peristiwa terhitung lima posisi ([[04-Tools/TL5 - ledger]]). Non-overlap berarti horizon berikutnya
tidak boleh menumpang horizon sebelumnya pada token yang sama.

## Cara pakai yang diklaim

Klaim yang beredar (T1, pemiliknya dashboard dan akun sinyal): win rate adalah ukuran mutu, dan
deretan menang ("streak") membuktikan sistem bekerja. Fabius sudah punya contoh tandingan yang
terukur: panel berlabel mencapai **win rate 69,8 %** sambil **−10,4 bps per jam** versus baseline
([[Fakta Terukur]] §F). Karena itu gerbang kelayakan yang dipakai bukan streak melainkan harapan
bersih setelah ongkos nyata, di luar sampel — dan alatnya mencetak **berapa lagi yang kurang**
(`winlog.py`: `n>=20 -> BELUM (kurang 17)`, §G). Perbandingan yang sah bukan "lebih baik dari trader
biasa" — kelompok kontrol itu tidak tersedia secara struktural — melainkan arah acak pada token dan
jam yang sama (§B).

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| bar forward untuk menilai prediksi paper | `ADA` | Aster 9.599 bar 1 jam — [[Fakta Terukur]] §A |
| rekaman entry yang terikat hash (bukan dihitung ulang) | `ADA` | `entry_ref` dibaca dari rekaman, ikut `decisionHash` di chain — [[04-Tools/TL5 - ledger]] |
| fill nyata + `realizedQuote` dari event | `ADA` | 3 putaran chain, rata-rata −59,0 bps — §D/§F |
| sampel jatuh tempo yang cukup | `TIDAK-ADA` | `n=2` paper, `n=3` chain; F-D16 belum terpenuhi — §G |
| ongkos round-trip yang konsisten di semua jalur uji | `ADA-TAPI` | uji memakai 20 bps; terukur kami 59 bps — **P10 masih terbuka** — §D |
| angka dari `tools/maker_ledger.py` | `TIDAK-ADA` | distribusinya tidak masuk akal (diblok eksplisit di §H) — hanya boleh dikutip sebagai "alat kami sedang rusak karena sebab yang diketahui" |

## Uji di Fabius

```
python -X utf8 tools/ledger.py           # tutup prediksi dari rekaman; AMBIGU & BELUM JATUH TEMPO dipisah
python -X utf8 tools/winlog.py           # dua seri terpisah + berapa lagi yang kurang
python -X utf8 tools/backtest.py         # aturan yang sama, 400 hari x 12 aset
python -X utf8 tools/anchor.py --verify  # jejaknya masih utuh? (§G: 13 baris terpelacak, 13/13 COCOK)
```

Yang boleh disimpulkan dari angka hari ini: **prediksinya jatuh tempo dan jejaknya masih bisa
diperiksa oleh orang lain** ([[06-Results/07 - Matured Outcomes]]). Yang tidak: apa pun tentang
kualitas. Pada n=20–40 Aproksimasi normal kami membuat p **sistematis terlalu kecil**
([[Fakta Terukur]] §E), jadi "signifikan" di rentang itu justru tanda bahaya. Untuk mendapatkan
sampel sebelum tenggat, horizon harus turun ke 4 jam — dan itu mengubah pertanyaan, bukan hanya
angkanya ([[01-Agent/01 - Asset Classes and Seats]] §4). Bentuk uji yang jujur:
[[QT2 - Backtesting yang Jujur]] · [[EV3 - Signifikansi dan Multiple Testing]].

## Batas dan mode gagal

- **Menghitung ulang = menyelundupkan harapan.** Karena itu `entry_ref` tidak boleh diambil dari
  harga yang paling menguntungkan saat ini ([[PL7 - Kontrak Antar-Tahap]]).
- **AMBIGU bukan kalah-menang.** Memilih sisi yang menguntungkan saat stop dan target ada di bar
  yang sama adalah cara tercepat menaikkan hasil tanpa menaikkan informasi.
- **Dua seri, dua arti.** Paper = tebakan dinilai terhadap bar pasar nyata; chain = fill di venue
  kami sendiri yang strukturnya selalu ≈ minus ongkos. Menggabungkannya melahirkan satu angka yang
  tidak menjawab pertanyaan apa pun.
- **Sampel kecil + banyak horizon = pemenang acak.** Mengulang uji di banyak horizon tanpa koreksi
  BH menjamin ada satu yang "lolos" ([[EV3 - Signifikansi dan Multiple Testing]]).
- **Angka gross yang tersamar:** artefak sapuan whale menyimpan `cost_bps_applied = 0.0`, jadi
  **semua** angka horison di situ gross (§H) — dicetak paling awal oleh `tools/whale_report.py`.
- **Belum jatuh tempo bukan nol,** dan bukan pula "kami belum untung" (§G); ia menunggu.

## Tingkat bukti

`T3` untuk mekanismenya: penutupan dari rekaman, pemisahan status, dan dua seri yang tidak
digabung — semuanya dijalankan dan tercetak. Untuk hasilnya: **belum ada tingkat apa pun**, `n`
terlalu kecil untuk menerima maupun menolak. Flag `TERCEMAR` milik tempat lain (panel berbasis
label, bukan penilaian ini) — lihat [[Concepts/Lookahead Bound]].

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami menutup prediksi dari rekaman yang ter-anchor, memisahkan yang belum jatuh tempo
  dan yang ambigu, dan melaporkan harapan bersih — bukan win rate."
- **Dilarang:** "win rate kami 50 %" (n=2) · "streak chain 3 kalah berarti sistem membaik di paper" ·
  "sistem kami rugi secara statistik" (juga melebihi sampel) · angka dari blok §H
  [[Fakta Terukur]] dikutip sebagai temuan.

**Terkait:** [[PL5 - Mengeksekusi dan Keluar]] · [[PL7 - Kontrak Antar-Tahap]] ·
[[FD5 - Expectancy Bukan Win Rate]] · [[EV3 - Signifikansi dan Multiple Testing]] ·
[[EV2 - Jebakan Backtest]] · [[06-Results/04 - Negative Results]] · [[GAP5 - Urutan Kerja dan Bayarnya]]

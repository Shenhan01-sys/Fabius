---
tags: [tk, tk-fondasi, "FD5"]
---

# FD5 - Expectancy Bukan Win Rate

**Keluarga:** [[00 - Hub Fondasi]] · **Tahap:** penilaian ([[PL6 - Menilai Hasil]]), mengikat keputusan ([[PL4 - Memutuskan]])
**Sumber:** [[Fakta Terukur]] §E (gerbang F-D16) · §F (panel whale, dua `Enter`, 12/12) · [[00-Overview/03 - Decisions]] F-D16 · [[06-Results/02 - Thresholds]] (bug `payoff` warisan)

**Ringkas:** Win rate hanya menjawab "berapa sering benar"; expectancy menjawab "berapa sisa setelah
yang salah membayar yang benar, dikurangi ongkos". Produk ini punya contoh terukur miliknya sendiri
bahwa keduanya tidak bergerak bersama: **WR 69,8 %** dengan **−10,4 bps** per jam. Karena itu gerbang
kelayakan uang nyata kami bukan streak, melainkan harapan bersih.

## Definisi yang bisa dihitung

```
E = sum_i p_i * r_i            dengan r_i = return NET trade i (setelah ongkos pada ukuran itu)
  = p*W - (1-p)*L - ongkos_rt  untuk bentuk dua-outcome (W = rata-rata untung, L = rata-rata rugi)
syarat hidup   : E > 0  BUKAN "WR > 50 %"
perhatikan     : E adalah rata-rata; tanpa varians/URU ia tidak bisa dipakai untuk ukuran posisi
```

Dua turunan yang sering hilang: (1) `p*W - (1-p)*L` bisa positif sementara WR di bawah 50 % (ekor
untung gemuk), dan negatif sementara WR 90 % (ekor rugi lebih gemuk lagi); (2) expectancy **bukan**
sifat sinyal saja — ia berubah saat ukuran berubah, karena bagian tetap ongkos ikut bergerak
([[FD4 - Ongkos Perdagangan]]).

## Cara pakai yang diklaim

Klaim komunitas: kejar win rate tinggi, atau kejar rasio risiko-imbalan besar, lalu sebut yang
satu "disiplen". Keduanya bisa dinaikkan tanpa menaikkan expectancy: WR naik dengan mengambil
profit kecil berulang, R:R naik dengan menahan rugi lebih lama. Bentuk yang dipakai di sini:
satu angka `E` per trade pada ukuran nyata, dihitung di luar sampel, dengan jumlah sampel
ditulis berdampingan.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| baris keputusan + hasil (net bps) per trade | `ADA-TAPI` | `tools/ledger.py` menilai dari rekaman; yang jatuh tempo baru **2** — §F/§G (angka hidup: jalankan perintahnya, jangan kutip dari halaman) |
| sampel ≥ 20 non-overlap untuk menyimpulkan apa pun | `ADA-TAPI` | `MIN_SAMPLES` 20 (§E); hari ini belum terpenuhi di jalur mana pun |
| pasangan win/loss per horizon untuk panel whale | `ADA-TAPI` | WR 69,8 % vs −10,4 bps/jam (§F); dan `whale-sweep-90d.json` memakai `cost_bps_applied = 0.0` sehingga angka horisnya GROSS — §H |
| varians / distribusi `\|net\|` per lot | `TIDAK-ADA` | `tools/maker_ledger.py` sedang rusak struktural (§H) — tidak boleh dikutip sebagai distribusi |
| p-value yang jujur pada n kecil | `ADA-TAPI` | aproksimasi **normal** diwarisi; pada n=20–40 p **sistematis terlalu kecil** — §E |

## Uji di Fabius

Gerbang yang berlaku (F-D16, [[Fakta Terukur]] §E): `net expectancy > 0` **setelah ongkos nyata di
ukuran itu**, `n ≥ 20`, tetap positif setelah fold terbaik dibuang, lolos BH α 0,10, dihitung **di
luar sampel**. Perintahnya ada: `tools/ledger.py --emit` lalu `tools/winlog.py` (yang juga mencetak
**berapa lagi yang kurang**, bukan cuma yang sudah).

Dua contoh terukur yang membuat halaman ini perlu ada:

1. **Panel whale: WR 69,8 % dan −10,4 bps per jam** (§F). Win rate tinggi + harapan negatif =
   norma, bukan paradoks; yang salah adalah metriknya, pasarnya tidak.
2. **Tiga `Enter` yang jatuh tempo: +1,5 / −146,3 / −485,3 bps** pada asumsi 20 bps; pada ongkos
   terukur 59 bps menjadi **−37,5 / −185,3 / −485,3** (§F,
   [[06-Results/04 - Negative Results]] §5b). WR-nya **0 %**, rata-rata **−236,0 bps**. Ini contoh
   paling murah di vault ini: satu metrik populer berpindah dari "setengah bagus" ke "nol" hanya
   karena penggarisnya diganti yang benar — dan tidak ada satu pun pergerakan harga yang berubah.

## Batas dan mode gagal

- **Streak bukan ukuran kelayakan.** Urutan menang adalah potongan riwayat yang bisa kita pilih;
  `tools/winlog.py` memang mencetak streak, tapi gerbang F-D16 tidak pernah bertanya ke streak.
  Di korpus rujukan yang kami warisi ada kebalikannya: aturan dengan **win rate 100 %** justru
  *gagal* lolos karena `payoff` tidak terdefinisi tanpa trade rugi — bug, bukan fitur
  ([[06-Results/02 - Thresholds]], bagian "yang secara sengaja tidak kami pakai").
- **Expectancy rata-rata menyembunyikan ekor.** E > 0 dengan satu kerugian yang menghapus modal
  tetap buruk; itu urusan [[FD6 - Ukuran Posisi]] dan [[FD7 - Invalidation Stop dan Time-Stop]].
- **Expectancy terbaik dari 12 aset bukan expectancy strateginya.** §F: net rugi di **12/12**;
  memilih yang paling sedikit rugi = memilih noise ([[EV3 - Signifikansi dan Multiple Testing]]).
- **Ongkos menentukan tanda.** E gross positif + E net negatif adalah hasil yang paling sering
  dijual sebagai "hampir profit".
- **Duplikasi:** expectancy dan "kedalaman edge" (gross − ambang) mengukur hal yang sama dengan
  satu pengurangan; jangan pamer keduanya sebagai dua bukti ([[EV6 - Kalibrasi Ambang Terhadap Hasil]]).

## Tingkat bukti

`T3` untuk "WR bukan pengganti expectancy" — sudah terukur di data kami sendiri (§F, dua jalur
berbeda) · `T1` untuk rumus dan dekomposisinya (kerangka standar) · untuk klaim "produk ini punya
expectancy positif": **belum ada bukti sama sekali**; `n = 2`, dan tidak satu pun uji boleh dijalankan
pada sampel itu.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami menilai dengan harapan bersih setelah ongkos, bukan dengan win rate; contoh
  terukur kami sendiri: WR 69,8 % tapi −10,4 bps per jam."
- **Dilarang:** "win rate kami 50 % jadi setengah bagus" · "agent kita punya edge" (belum lolos
  F-D16 di jalur mana pun) · "streak 3 menang = trust naik".

**Terkait:** [[01-Agent/A4 - Trust Gating and Real-Money Rules]] · [[Concepts/Anchored Before Outcome]] ·
[[FD4 - Ongkos Perdagangan]] · [[FD6 - Ukuran Posisi]] · [[PL6 - Menilai Hasil]] ·
[[EV3 - Signifikansi dan Multiple Testing]] · [[GAP1 - Matriks Metode x Tahap]]

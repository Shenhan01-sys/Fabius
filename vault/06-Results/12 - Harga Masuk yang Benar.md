---
tags: [hasil]
---

# 12 - Harga Masuk yang Benar

**Sumber:** `tools/entry_decomposition.py` → `decisions/entry-decomposition-20260928T094547Z.json`
(`rows_sha256=0x2c96b4f17374c8…`) · dijalankan 28 Sep 2026 ±09:45Z · alat kunci:
`tools/day2_replicate.py --halaman 12` → `decisions/prereg-honest-lock.json`

**Ringkas: halaman 09 dan 10 salah, dan ini yang membatalkannya.** Efek kerumunan maker yang
kuterbitkan (+393,4 bps, lolos BH) **tidak bertahan** ketika harga masuk diganti menjadi harga
transaksi itu sendiri - yaitu harga yang benar-benar bisa kami dapat pada saat kami memutuskan.
Pada kejadian yang sama, pairing yang sama, hanya sumur harganya yang berganti:
**+93,0 (p=0,0066) → +0,1 (p=0,53)**. Tidak ada aspek yang lolos Benjamini-Hochberg pada harga
peristiwa. Yang tersisa dari sesi ini bukan "edge whale", tapi alat yang akhirnya jujur tentang
harga masuknya sendiri.

## 0. Rantaian yang membuat kami salah

1. `px` **bukan ticker** - 71,7 % barisnya mengulang nilai sebelumnya (§B `Fakta Terukur`), karena
   ia membawa harga transaksi terakhir tapi di-stamp waktu kami menarik.
2. Umur sebenarnya harga yang kami pakai: **median 8,7 menit**, p90 42 menit, maksimum 2,6 jam.
3. Kejadian yang **berkerumun** punya lebih banyak transaksi → deret harganya lebih segar daripada
   kejadian sepi. Dan kami memakai deret itu sebagai **outcome**.
4. Jadi "K≥2 mengalahkan K=1 di token yang sama" sebagian besar mengukur **segar tidaknya
   pengamatan kami**, bukan apa yang terjadi di pasar. Kerumunan memprediksi kesegaran data, dan
   kesegaran data masuk ke definisi keuntungan.

Ini bukan kelemahan statistik - ini **kebocoran instrumen ke dalam label**. Dan ia tidak kelihatan
oleh gerbang mana pun yang kupasang, karena semua gerbang memeriksa bentuk, bukan asal angka.

## 1. Dekomposisi: empat kombinasi harga, kejadian yang sama persis

557 kejadian pada 217 token yang punya **kedua** sumur; berpasangan dalam token yang sama
(n=178 untuk `cluster_ge2`, 58 token). Ongkos 59 bps (`measured-own-venue`) di semua sisi.

| aspek | A `px→px` **(yang kuterbitkan)** | D `tx→px` (masuk jujur) | C `px→tx` | B `tx→tx` **(paling jujur)** |
|---|---|---|---|---|
| `cluster_ge2` | **+93,0** [+1; +825] 59,6 % p=0,0066 | **+0,1** [−14; +198] 50,0 % p=0,53 | +815,4 [+5; +1760] p=0,0006 | **+0,3** [−7; +516] 51,7 % p=0,35 |
| `cluster_ge3` | +50,0 [−4; +1182] p=0,10 | +0,2 [−196; +332] p=0,50 | +243,3 p=0,07 | +0,3 [−394; +1157] p=0,50 |
| `repeat_maker` | +0,1 p=0,54 | −0,2 p=0,61 | +184,6 p=0,027 | +4,6 p=0,16 |
| `money_spread` | **+39,6** [+0; +773] p=0,018 | +1,9 p=0,28 | +122,7 p=0,018 | +6,3 [−0; +282] p=0,078 |
| `buy_usd_ge_1k` | +11,7 p=0,12 | −0,6 p=0,77 | +4,3 p=0,12 | −17,7 p=0,83 |
| `no_exit_flow` | −3,0 p=0,93 | +1,3 p=0,21 | −3,7 p=0,97 | −0,1 p=0,55 |
| `wide_flow` | +1,6 p=0,10 | +1,3 p=0,16 | +0,3 p=0,33 | +2,2 p=0,10 |
| `fresh_token` | +12.675 p=0,0000 | +4.499 p=0,0000 | +22.638 p=0,0000 | +12.006 p=0,0000 |

**Lolos BH:** pada A `cluster_ge2` + `money_spread`; **pada B tidak ada satu pun.**

Dua bacaan yang harus disebut bersama tabel ini:

- **Yang mati adalah sisi MASUK.** A→D mengubah satu hal (harga masuk jadi harga transaksi itu
  sendiri) dan efeknya lenyap; B pun ~0. Sebaliknya C (`px→tx`) justru terbesar (+815) - kalau
  hanya sisi keluar yang diperbaiki, angkanya malah membesar. Itu tanda klasik bahwa yang berubah
  bukan pasar, tapi **titik awal perhitungan**.
- **Pada populasi yang lebih besar, arahnya malah negatif.** `--px txevent` di
  `tools/evidence_stack.py` (908 kejadian, tidak menuntut sumur `px`): `cluster_ge2` =
  **−491,4 CI [−1319; −205]**, hanya 30,5 % positif. Jadi pada harga peristiwa, kerumunan di 30
  menit berikutnya **lebih sering turun daripada naik** - konsisten dengan mengejar puncak lokal.
  Dua himpunan (557 yang ber-sumur-dua vs 908 semua) memberi jawaban berbeda: nol vs negatif.
  Yang boleh kukatakan: **tidak ada satu pun dari keduanya yang mendukung klaim kami.**

## 1b. REPLIKASI TERKUNCI - dijalankan 28 Sep 21:45Z, TIDAK ADA REPLIKASI

Kunci dipasang 28 Sep 09:49Z (`spec_sha256=0x6f69e1003a7ed155…`, `t_kunci=09:38:44Z`, syarat 12 jam
rekaman baru, hanya kejadian setelah kunci yang dinilai). Alat menolak di 11,99 jam dan baru mau
berjalan di 12,05 jam - pembulatan tidak dipakai sebagai izin. Artefak:
`decisions/day2h-20260928T214502Z.json`.

| uji (spesifikasi terkunci) | token | n | median selisih | CI 95 % | p satu arah | vonis |
|---|---|---|---|---|---|---|
| `uji_primer` K≥2 | 21 | 40 | **−1.518,5** | **[−7.379; −3]** | 0,99 | **GAGAL** |
| `uji_kedua` `money_spread` | 19 | 34 | −747,9 | [−2.694; +77] | 0,97 | **GAGAL** |
| `uji_ketiga` stack≥2 | 21 | 40 | −1.124,3 | [−3.310; −3] | 0,99 | **GAGAL** |

Dua hal yang harus dibaca bersama tabel ini, dan yang kedua menahan godaan:

1. **Bukan cuma gagal - arahnya terbalik dan CI-nya tidak menyentuh nol** untuk uji primer dan
   ketiganya: pada data yang belum pernah dilihat saat spesifikasi ditulis, kerumunan maker diikuti
   hasil 30 menit yang LEBIH BURUK daripada kejadian sepi di token yang sama.
2. **Itu TIDAK mengubahnya jadi sinyal fade.** Aturan halaman ini baris terakhir menutup dua arah
   sekaligus: "hipotesis kerumunan (dua arah sekali pun) dicabut". Membalik tanda setelah melihat
   hasilnya adalah gerakan yang sama yang sudah membunuh +393,4 pagi tadi - hanya kali ini dengan
   data yang lebih sedikit (40 pasangan). Kalau fade mau dikejar, ia harus masuk sebagai
   **spesifikasi baru dengan kuncinya sendiri**, diuji pada rekaman yang belum pernah dilihat.

Sensor run ini juga mengulang tembok yang lain: **7.294 beli dibuang karena tidak ada transaksi
lanjutan di jendela keluar** (vs 265 yang dinilai). Itulah P33 - di horison 30 menit, sebagian
besar posisi kita tidak punya harga keluar, dan yang "tidak punya" itu bukan netral: biasanya mati.

## 2. `fresh_token` tetap artefak, dan kini lebih jelas kenapa

+12.675 s/d +22.638 bps di SEMUA kombinasi harga - termasuk B yang paling jujur. Ini memperkuat
kesimpulan §3 halaman 10: yang diukur adalah **kebijakan pull kami** (token baru = deret baru =
perubahan besar yang terpotong di kedua ujung), bukan pasar. Ia tetap dibuang.

## 3. Apa yang berubah di produk, dan apa yang tidak

- **Gerbang ⑧ tidak akan dibangun di atas kerumunan sebagai sinyal beli.** Kalau ada yang bisa
  dipertahankan dari sesi ini, itu justru hipotesis **sebaliknya** (kerumunan sebagai penanda
  "jangan masuk"), dan itu belum diuji - jadi tidak dijual.
- Halaman 09 dan 10 **tidak dihapus**; keduanya sekarang membawa penanda dicabut di kepalanya,
  karena urutan bagaimana kami sampai ke sana adalah bagian dari hasilnya.
- Spesifikasi lama di [[06-Results/11 - Pra-Registrasi Hari Kedua]] **tidak kusunting** - alatnya
  akan mati kalau itu dilakukan, dan memang untuk itu ia dibuat. Yang terjadi: halaman 11 kini
  menguji klaim yang sudah kami ketahui cacat instrumennya, jadi hasilnya nanti dicatat sebagai
  **moot untuk keputusan produk**, berguna hanya sebagai demonstrasi bahwa `px` menghasilkan efek
  hantu. Klaim yang hidup dikunci di halaman ini, terpisah, dengan berkas kunci sendiri.

```text
halaman_spesifikasi: 12
sumber_harga: txevent
harga_masuk: harga transaksi terakhir dengan t_tx <= t (umur 0 - ini harga yang bisa didapat)
harga_keluar: median t_tx pada t+[H-15m, H+15m]
horison_menit: 30
jendela_menit: 15
non_overlap: 1 per horison per token
ongkos_bps_roundtrip: 59.0   # measured-own-venue (tools/costs.py)
statistik: median + bootstrap 4000 (seed 20260928) + tanda-uji eksak satu arah
koreksi: Benjamini-Hochberg alpha 0.10, dihitung DI DALAM run replikasi
pasangan: berpasangan dalam token yang sama (acuan = kejadian yang tidak memicu aspek)
uji_primer: cluster_ge2
uji_kedua: money_spread
uji_ketiga: stack_ge2
data_replikasi: HANYA kejadian dengan t > t_kunci
syarat_umur_jam: 12
vonis_replikasi: median > 0 DAN CI bawah > 0 DAN p < 0,05 sesudah BH dalam run itu
kalau_gagal: hipotesis kerumunan (dua arah sekali pun) dicabut; ⑧ tidak dipasang
```

Yang boleh disimpulkan dari halaman ini **sebelum** hari kedua: kami tidak punya efek yang bisa
diperdagangkan di horison 30 menit dari aliran ⑦. Yang belum boleh disimpulkan: bahwa kerumunan
adalah sinyal jual - itu hipotesis baru, dan ia berhak atas kunci sendiri.

## 4. Cara menjalankan ulang

```text
python -X utf8 tools/entry_decomposition.py --self-test
python -X utf8 tools/entry_decomposition.py
python -X utf8 tools/evidence_stack.py --px txevent
python -X utf8 tools/day2_replicate.py --halaman 12 --status
```

**Terkait:** [[06-Results/09 - Whale Cluster Test]] · [[06-Results/10 - Evidence Stack]] ·
[[06-Results/11 - Pra-Registrasi Hari Kedua]] · [[03-Data/D2 - Wallet Flow]] ·
[[03-Data/D5 - Record Schemas]] · [[TradingKnowledge/Fakta Terukur]] §B/§F ·
[[TradingKnowledge/EV2 - Jebakan Backtest]] · [[TradingKnowledge/EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] · [[TradingKnowledge/QT2 - Backtesting yang Jujur]]

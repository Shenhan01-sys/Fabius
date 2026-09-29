---
tags: [hasil]
---

# 17 - Pra-Registrasi Watch

**Alat:** `tools/day2_replicate.py --halaman 17` · kunci: `decisions/prereg-watch-lock.json`
**Ditulis & dikunci:** 29 Sep 2026, SEBELUM satu pun angka hasil dilihat
**Ringkas:** dua uji terkunci sudah jatuh dan keduanya bilang TIDAK ADA REPLIKASI - tapi keduanya
memakai deret yang kami ketahui cacat sebagai harga masuk (`px` = harga transaksi terakhir, umur
median 8,7 menit). Satu-satunya deret yang benar-benar **berdetak sendiri** di rekaman kami adalah
`wp` (DexScreener, ±3,4 menit, tidak peduli ada transaksi atau tidak) dan umurnya baru 20 jam.
Halaman ini mengunci pertanyaannya sekarang, supaya jawabannya datang dari data yang belum pernah
kami lihat - bukan dari angka yang sama untuk keempat kalinya.

## 0. Kenapa ini bukan pengulangan dua uji sebelumnya

| | halaman 11 (`px`) | halaman 12 (`tx→tx`) | **halaman 17 (`watch`)** |
|---|---|---|---|
| harga masuk | transaksi terakhir, di-stamp waktu kami menarik | transaksi itu sendiri (umur 0) | **harga pool kini dari venue, berdetak tanpa transaksi** |
| penyakit yang bisa muncul | efek hantu karena harga basi (F-D30) | tidak bisa keluar saat sepi (penyensoran) | **tidak bisa keluar saat harga benar-benar datar - dan itu kita LIHAT, bukan tebak** |
| keluar | median `px` di jendela | median transaksi di jendela | **median `wp` di jendela (termasuk saat tidak ada transaksi)** |

Angka `P(≥+500 bps)` dari uji `txevent` bisa digelembungkan oleh penyensoran (7.294 beli dibuang
karena tidak ada transaksi lanjutan). Pada `wp`, token yang harganya mendatar TETAK punya keluaran
- jadi "tidak bergerak" dihitung sebagai tidak bergerak, bukan dibuang sebagai tidak ada data.
Itu satu-satunya perbedaan yang membuat uji ini layak dijalankan.

## 1. Spesifikasi yang dikunci

```text
halaman_spesifikasi: 17
sumber_harga: watch
harga_masuk: wp terakhir dengan t <= t_keputusan (umur maksimal 10 menit, umur sebenarnya dilaporkan)
harga_keluar: median wp pada t+[H-15m, H+15m]; TIDAK ADA transaksi yang diperlukan agar keluaran ada
horison_menit: 30
jendela_menit: 15
non_overlap: 1 per horison per token
ongkos_bps_roundtrip: 59.0   # measured-own-venue (tools/costs.py)
statistik: median + bootstrap 4000 (seed 20260928) + tanda-uji eksak satu arah
koreksi: Benjamini-Hochberg alpha 0.10, dihitung DI DALAM run replikasi
pasangan: berpasangan dalam token yang sama (acuan = kejadian pada token itu yang tidak memicu aspek)
uji_primer: cluster_ge2 (>=2 maker berbeda beli dalam jendela)
uji_kedua: money_spread (beli terbesar <= 60% dari USD beli di jendela)
uji_ketiga: stack_ge2 (>=2 dari lima aspek lulus 28 Sep menyala bersamaan)
data_replikasi: HANYA kejadian dengan t > t_kunci
syarat_umur_jam: 12
lapor_wajib: [P(ada harga keluar), umur median harga masuk, n, token, CI bawah harapan]
vonis_replikasi: median > 0 DAN CI bawah > 0 DAN p < 0,05 sesudah BH dalam run itu - tiga-tiganya
kalau_gagal: kerumunan maker ditutup sebagai jalur masuk untuk jendela ini; TIDAK dibalik jadi fade
             (aturan yang sama yang dipakai halaman 12); dan hasilnya tidak dikutip sebagai "teknikal
             tidak bekerja" karena yang diuji adalah aliran, bukan indikator harga
kalau_hasil_terlalu_kecil: tulis "belum bisa diuji", jangan "tidak ada efek" - dan jangan turunkan
             ambang n setelah melihatnya
```

## 2. Yang TIDAK boleh dilakukan setelah datanya ada

- Menurunkan `--maxage`, mengubah `window`, atau menambah horison supaya n cukup. Itu spesifikasi
  baru, kuncinya sendiri, dan hasilnya tidak boleh digabung dengan yang ini.
- Menyebut hasilnya "PnL". Tidak ada fill, tidak ada kedalaman, tidak ada ukuran posisi nyata.
- Membalik tanda menjadi sinyal jual. Hipotesis terbalik butuh kuncinya sendiri (dan n-nya sendiri).

## 3. Cara alatnya bicara

```text
python -X utf8 tools/day2_replicate.py --halaman 17 --status
python -X utf8 tools/day2_replicate.py --halaman 17
```

Sebelum syarat umur 12 jam dari `t_kunci` terpenuhi, alatnya hanya mencetak "BELUM SAH" dan
**nol angka hasil**. Sunting blok spesifikasi setelah dikunci -> `exit=1`
("yang berubah bukan datanya, aturan mainnya"). Umur datanya dibaca dari berkas `wp` ITU SENDIRI -
bukan dari jam aliran - karena pantau bisa mati sementara aliran tetap hidup.
## 4. Hasil

**Dibaca 29 Sep 2026 20:26:13Z** oleh `python -X utf8 tools/day2_replicate.py --halaman 17`
(kunci `03:05:05Z`, umur rekaman **17,14 jam** dari kebutuhan 12; `spec_sha256=0xc4105c1732ebfca7…`
identik dengan sha di `decisions/prereg-day2-lock.json` - blok §1 tidak kusentuh). Bahan: **769
kejadian pada 375 token, semuanya sesudah kunci**. Artefak: `decisions/day2w-20260929T202613Z.json`.

## VONIS: TIDAK ADA REPLIKASI - jalur kerumunan maker ditutup

| uji (nama terkunci) | aspek yang dipakai | n | token | median selisih | CI bootstrap 4000 | p tanda-uji | posisi positif |
|---|---|---|---|---|---|---|---|
| `uji_primer` | `cluster_ge2` | **156** | 86 | **−21,3 bps** | [−543,9 ; +2,8] | 0,9360 | 44,2 % |
| `uji_kedua` | `money_spread` | **123** | 78 | **0,0 bps** | [−480,9 ; +81,5] | 0,7057 | 48,0 % |
| `uji_ketiga` | `stack_ge2` | **142** | 84 | **0,0 bps** | [−300,9 ; +75,7] | 0,7749 | 47,2 % |

Tiga-tiga syarat `vonis_replikasi` (median > 0 DAN CI bawah > 0 DAN p < 0,05 sesudah BH) gagal pada
**ketiga** uji, dan BH tidak bisa menyelamatkan apa pun dengan p sebesar itu. Sesuai `kalau_gagal`
di spesifikasi: **kerumunan maker ditutup sebagai jalur masuk untuk jendela ini; TIDAK dibalik jadi
sinyal jual** - dan hasilnya tidak boleh dibaca sebagai "indikator teknikal tidak bekerja", karena
yang diuji adalah aliran, bukan indikator harga.

**Dua hal yang harus ikut dibaca, atau halaman ini akan disalahpahami:**

1. **`mean_selisih_bps` di artefak (+4.043,7 / +4.404,7 / +4.713,5) TIDAK BOLEH DIKUTIP.** Ia bukan
   winsorised dan satu token lotre (memecoin yang naik puluhan persen dalam 30 menit) cukup untuk
   memindahkannya ribuan bps, sementara mediannya 0 dan CI-nya memotong nol di kedua sisi. Ini
   kebalikan persis dari pelajaran F-D51: angka yang terlihat besar, yang lahir dari ekor, dan
   dipakai tanpa menyebut penggarisnya. `evidence_stack._pair` tidak winsor pada mean -> **P63**.
2. **Median tepat 0,0 pada dua dari tiga uji bukan "tidak ada perubahan"** - itu tanda deret harga
   yang diam (`px` beku; lihat [[06-Results/12 - Harga Masuk yang Benar]] dan F-D56 yang mengukur
   97 % menit tanpa transaksi di venue kami). Untuk separuh populasi ini, yang terukur adalah
   *ketiadaan pergerakan*, bukan hasil perdagangan.

## 5. Pencatatan penting: pembacaan PERTAMA halaman ini tidak sah, dan bukan karena dunia

Pada 20:18:39Z alat yang sama mencetak `SAMPEL TIDAK CUKUP` untuk uji_primer dan uji_kedua dengan
**n = 0 persis**, dan vonisnya waktu itu berbunyi "belum bisa diuji". Itu **bug lookup di alatku
sendiri**: `pred = bool(e.get(fitur))` memakai **seluruh baris spesifikasi** (`"cluster_ge2 (>=2
maker berbeda beli dalam jendela)"`) sebagai kunci aspek, padahal kuncinya `"cluster_ge2"`. Lookup
ke string panjang itu mengembalikan `None` untuk SEMUA kejadian - jadi n=0 adalah kepastian struktural,
bukan kekurangan data.

Buktinya, dengan data dan jendela yang sama persis: `cluster_ge2` menyala pada **140** kejadian dan
`money_spread` pada **112** (probe `_research` sekali-pakai, diulang lewat `tools/day2_replicate.py`
yang sudah diperbaiki -> `aspek_dari()`). Perbaikan alat tidak mengubah spesifikasi maupun sha-nya;
ia hanya membuat alat menanyakan hal yang benar.

Yang membuat kasus ini layak dicatat, bukan diam: **fiksinya memperkeras vonis, tidak melunakkan.**
Sebelum: "belum bisa diuji" (tidak menyakitkan, tidak menutup apa pun). Sesudah: **GAGAL pada tiga-tiganya**,
dan sebuah jalur masuk ditutup. Kalau bug alat membuat hasilnya *lebih baik*, aku curiga pada diriku
sendiri; di sini ia membuatnya lebih buruk, dan itu justru alasan untuk mempercayainya. Aturan yang
naik: **`n` yang tepat 0, atau 100 %, atau angka bulat lain, adalah alarm instrumen** - sebelum ia
disebut "kekurangan sampel", hitung berapa yang seharusnya menyala. F-D63.


**Terkait:** [[06-Results/11 - Pra-Registrasi Hari Kedua]] · [[06-Results/12 - Harga Masuk yang Benar]] · [[06-Results/16 - Harga Keluar yang Hilang]] · [[03-Data/D2 - Wallet Flow]] ·
[[TradingKnowledge/EV5 - Reproduksibilitas dan Pra-Registrasi]] ·
[[TradingKnowledge/EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] ·
[[08-Backlog/02 - Epik Alasan Masuk]] §3d · F-D63 (pembacaan pertama tidak sah)

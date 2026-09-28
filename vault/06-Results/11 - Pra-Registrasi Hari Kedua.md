---
tags: [hasil]
---

# 11 - Pra-Registrasi Hari Kedua

**Bagian dari:** [[06-Results/00 - Hub Results]]
**Alat:** `tools/day2_replicate.py` · kunci: `decisions/prereg-day2-lock.json`
**Status:** ⏳ **TERKUNCI SEBELUM HASIL DILIHAT** - alatnya menolak mencetak angka apa pun sampai
syarat umur data terpenuhi, dan menolak jalan kalau spesifikasi ini diedit setelah dikunci.

**Ringkas:** halaman 09 dan 10 berisi angka yang bagus. Keduanya lahir dari satu jendela 43 jam yang
sama, dan jendela yang sama tidak bisa membuktikan dua kali. Halaman ini adalah satu-satunya benda
di vault yang bisa **membatalkan** keduanya.

## Aturan main yang dikunci

Parameternya diambil apa adanya dari run kanonik 28 Sep - tidak ada satu pun yang "dipercantik"
setelah melihat angka, karena angkanya sudah dilihat duluan dan itu justru yang mau diuji.

```text
sumber_harga: gmgn        # px rekaman sendiri; SATU sumber untuk masuk+keluar (tools/prices.py)
harga_masuk: px <= t, tidak lebih tua dari 10 menit
harga_keluar: median px pada t+[H-15m, H+15m]
horison_menit: 30
jendela_menit: 15         # jendela hitung kerumunan/sebaran dana
non_overlap: 1 per horison per token
ongkos_bps_roundtrip: 59.0   # measured-own-venue (tools/costs.py)
statistik: median + bootstrap 4000 (seed 20260928) + tanda-uji eksak satu arah
koreksi: Benjamini-Hochberg alpha 0.10, dihitung DI DALAM run replikasi (bukan diwarisi)
pasangan: berpasangan dalam token yang sama (acuan = kejadian yang tidak memicu aspek)
uji_primer: cluster_ge2 (>=2 maker berbeda dalam jendela)
uji_kedua: money_spread (beli terbesar <= 60% dari USD beli di jendela)
uji_ketiga: stack_ge2 (>=2 dari lima aspek lulus 28 Sep menyala bersamaan)
data_replikasi: HANYA kejadian dengan t > t_kunci (out-of-sample murni, bukan campur)
syarat_umur_jam: 12
```

## Cara vonis ditulis — dan ini bagian yang mengikat

Suatu uji disebut **replikasi** kalau TIGA-tiganya benar pada data baru:

1. median selisih **> 0**,
2. batas bawah **CI 95 %** bootstrap **> 0**,
3. tanda-uji satu arah **p < 0,05** sesudah BH di dalam run itu.

| hasil | yang terjadi |
|---|---|
| uji_primer REPLIKASI | kandidat gerbang ⑧ (`SEARAH`) boleh diusulkan ke P15 - sebagai **penurun saja**, tetap [[Concepts/One-Way Gate]] |
| uji_primer gagal, uji_kedua/ketiga replikasi | kerumunan TIDAK berdiri sendiri; yang hidup adalah **struktur dana**, dan halaman 09 diturunkan statusnya jadi "efek yang tidak mereplikasi" |
| ketiganya gagal | **[[06-Results/09 - Whale Cluster Test]] dan [[06-Results/10 - Evidence Stack]] DICABUT** dari klaim: bukan "perlu penjelasan lebih", bukan "sampel belum cukup" - dicabut, dan halaman ini menyimpan alasannya |
| alat menolak jalan (umur kurang) | tidak ada pernyataan apa pun. Ketiadaan hasil bukan hasil |

Yang **tidak** boleh dilakukan setelah melihat data: mengubah ambang `money_spread` (0,60), jendela
(15 m), horison (30 m), `MAX_AGE` (10 m), α (0,10), atau memindahkan uji mana yang primer. Kalau
salah satu itu diubah, run-nya bukan replikasi dan harus ditulis sebagai eksplorasi baru.

## Kenapa 12 jam, dan kenapa bukan "besok"

`_research/sim_watch_value.py` mengukur: **83,9 %** beli punya kemunculan token yang sama ≤ 2 jam
sebelumnya, jadi 12 jam rekaman baru sudah cukup untuk mengubah cakupan dari 12,7 % jadi puluhan
persen - dengan satu syarat: perekam pantau (`universe/record_watch_prices.py`) harus jalan di
rantai GitHub, dan itu butuh commit-nya sampai ke default branch. **Kunci ini dipasang sebelum itu**,
supaya "kapan data cukup" tidak bisa diputuskan setelah "berapa lamanya" diketahui.

## Cara membaca isinya tanpa percaya tulisanku

```text
python -X utf8 tools/day2_replicate.py            # kunci / cek umur / jalankan kalau sudah sah
python -X utf8 tools/day2_replicate.py --status   # hanya: terkunci kapan, berapa jam lagi
```

Artefak replikasi ditulis `decisions/day2-<UTC>.json` dan **menempel sha256 spesifikasi** - jadi
bukti bahwa angka itu dihasilkan dari aturan yang sama yang dikunci di halaman ini.

**Terkait:** [[06-Results/05 - Pre-registration Flow]] · [[06-Results/06 - Pre-registration Horizon]] ·
[[06-Results/09 - Whale Cluster Test]] · [[06-Results/10 - Evidence Stack]] ·
[[TradingKnowledge/EV5 - Reproduksibilitas dan Pra-Registrasi]] ·
[[TradingKnowledge/EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] ·
[[08-Backlog/01 - Backlog]] P20/P21

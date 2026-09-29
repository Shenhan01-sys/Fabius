---
tags: [backlog]
---

# 02 - Epik: Alasan Untuk Masuk

**Daftar induk:** [[08-Backlog/01 - Backlog]] P31 · **Keputusan:** F-D33 · **Dibuka:** 28 Sep 2026
**Status epik:** 🔴 **BELUM TERPECAHKAN - dan ini jantung produknya**

> Builder, 28 Sep: *"fokus kerjakan alasan untuk masuk itu, buat itu menjadi backlog besar, karena
> itu adalah jantung Fabius."* Halaman ini adalah backlog besar itu. Yang ditulis di sini bukan
> niat, tapi **kriteria selesai yang bisa gagal** - karena separuh dari hari ini kuhabiskan untuk
> membatalkan temuan yang tidak memenuhi kriteria itu.

## 0. Apa yang dimaksud "alasan masuk", secara bisa diuji

Sebutan lain yang **tidak** boleh dipakai untuk hal ini: "sinyal whale", "smart money masuk",
"kerumunan". Itu semua sudah diukur hari ini dan **tidak** menaikkan apa pun di atas control.

Sebuah aturan R disebut **alasan masuk** kalau, pada data yang belum pernah dilihatnya:

1. **Ia mengalahkan control `random` pada jendela yang sama** - bukan mengalahkan "tidak trading".
   Control adalah kewajiban: tanpa dia, yang kita ukur adalah "feed ini sedang menunjukkan token
   yang naik" (terukur: control `random + veto` = **+188,3 bps** vs `first` +140,9 vs `lock` +109,7).
2. Harapan **winso** selisihnya > 0 dengan **CI bootstrap bawah > 0** (bukan median - median kami
   sudah terbukti mentok di −ongkos) **DAN** `P(net ≥ +500 bps)` naik di atas baseline dengan
   Fisher **satu arah** (`ekor_hipergeo`, bukan `fisher_p` yang dua-arah).
3. `n ≥ 20` per F-D16 **dan** arah yang diuji ditetapkan **sebelum** datanya dilihat - spesifikasi
   terkunci, sha-nya dicatat, sunting = alat mati (pola `tools/day2_replicate.py --halaman 12`).
4. Ia **tidak** memakai apa pun yang ditentukan oleh kebijakan pull kami sendiri (`fresh_token`
   adalah contoh yang sudah dibuang: +7.708 -> artefak), dan tidak memakai harga yang lebih tua
   dari horison keputusannya (`px` beku: p50 8,7 mnt, p90 42 mnt).

Kalau ada aturan yang lolos 1-4, Fabius punya gas. Kalau tidak, produknya tetap jujur sebagai
**rem + eksekusi + bukti**, dan itu dilaporkan apa adanya - bukan dibungkus.

## 1. Daya: seberapa besar sampel yang memutuskan

Dari dispersi yang terukur di buku ini (simpangan per posisi ≈ **841 bps**; baseline
`P(≥+500) = 33,9 %`):

| yang ingin diputuskan | posisi / kejadian yang dibutuhkan | realistis sebelum 30 Sep? |
|---|---|---|
| selisih harapan **200 bps** | ±70-140 posisi | **ya** - pada 1.014 kejadian yang boleh, dengan `dailyCap` dilepas di mode paper |
| selisih harapan **100 bps** | ±550 posisi | sebagian (butuh 2-3 hari `wp`) |
| kenaikan ekor **+10 pp** (33,9 % -> 43,9 %) | ±205 kejadian per grup | **ya**, untuk subgroup besar |
| kenaikan ekor **+5 pp** | ±850 per grup | tidak |
| penyortiran pada **5 posisi/hari kontrak** | ±272 posisi = **±55 hari** | **tidak** - ini batas keras, bukan kurangnya kerja keras |

Konsekuensi desain: **pencarian dilakukan pada sampel penuh (paper, budget dilepas), lalu
dikonfirmasi di budget kontrak.** Yang terakhir itu bukan uji statistik - itu uji *apakah bisa
dijalankan*, dan jawabannya hari ini: pada 5/hari @1 BNB, buku ini **−708,9 bps**.

## 2. Lima keluarga hipotesis, diurutkan dari yang paling mungkin

| № | keluarga | kenapa masuk akal | data yang dibutuhkan | bisa diukur sekarang? |
|---|---|---|---|---|
| **E1** | **tenang- setelah-kerumunan** (pullback stabil): pernah ≥2 maker beli dalam 60 m, lalu 15 m sepi, harga masih di atas harga cluster | kerumunan hari ini terbukti menaikkan harga lalu **turun** (berpasangan −313 s/d −491 bps); kalau itu pump-and-dump, titik masuk yang benar adalah setelah dump, bukan saat pump | sudah ada semua (`tx` + harga peristiwa) | **YA - eksperimen pertama** |
| **E2** | **jendela risiko pasar**: hanya masuk saat major (BTC/ETH di `tools/bars.py`) sedang naik & volatil | payoff ekor memecoin bergantung rezim, bukan token; kita sudah punya bar major panjang (Hyperliquid/Aster/Binance) | ada (bar major + aliran) | **YA** |
| **E3** | **identitas kohor, bukan jumlah**: maker yang menang pada kohor sebelumnya vs maker baru | panel GMGN tidak netral (keanggotaan = pilihan vendor), jadi klaim apa pun di sini wajib diuji terhadap "maker acak dari kerumunan yang sama" | ada, tapi cohort lama terbatas | sebagian - n kecil |
| **E4** | **siklus hidup pool**: umur, `liq_usd`, `vol_h1`, rasio `buys/sells` per jam | kandidat terbaik kita (`lock_percent`) muncul dari sini lalu mati karena **cakupan**, bukan karena idenya salah | `wp` seragam + snapshot yang tidak dipilih daftar panas (P29) | BELUM - 25,1 % kejadian, dan subset itu baseline-nya −64,7 |
| **E5** | **posisi dalam pump** (`tarik dari puncak`, `jatuh dalam`) | "beli darah" adalah intuisi masuk yang paling umum | ada | **SUDAH DIUJI - SALAH**: −2.853 bps vs baseline (tanda-uji satu arah; label "MW p=1,0" yang dulu ditulis di sel ini **dicabut** - angka itu keluar dari `mann_whitney_p` yang ternyata salah urut, lihat [[00-Overview/03 - Decisions]] F-D37); buy-the-dip justru yang paling buruk |

E5 sudah mati hari ini. E4 butuh P29. **Malam ini yang bisa kujalankan: E1 dan E2.**

## 3. Sub-pekerjaan (yang masuk backlog, dengan kriteria selesai)

| id | pekerjaan | selesai = |
|---|---|---|
| **P31.1** | E1: definisikan `tenang_setelah_kerumunan` **sebelum** dilihat angkanya, tulis spesifikasinya, kunci sha-nya | artefak `decisions/prereg-e1-lock.json` + vonis `tools/entry_lab.py --e1` di atas control, CI dilaporkan |
| **P31.2** | E2: variabel jendela risiko (ret/acf major) point-in-time, digabung sebagai *filter*, bukan *trigger* | sama, plus laporan berapa % kejadian yang disaring (filter yang membuang 90 % bukan filter, itu penyesalan) |
| **P31.3** | `tools/entry_lab.py`: satu alat untuk semua E, control `random` wajib, winsor + ekor + BH + sha256 baris | alat dijalankan orang lain dari clone -> angka sama |
| **P31.4** | **P29 (cakupan)** - prasyarat E4 dan satu-satunya cara mencari "gas" tanpa memilih subset terburuk | `wp`/snapshot menutup >= 60 % kejadian yang boleh, dan baseline subset berfitur tidak lagi ≠ baseline umum |
| **P31.5** | **P30 (buku paper harian + anchor)** | >= 2 artefak harian ter-anchor; `pengganti_real` menunjuk tx untuk >= 1 slot yang **dipromosikan**, dan tetap kosong untuk yang tidak |
| **P31.6** | Kalau (dan hanya kalau) E lolos: naikkan jadi perilaku agen - sambungkan ke `direction.py`/`decide.py` sebagai **penambah** keyakinan, dengan batas `maxConfidence` sendiri | gerbang ⑧ punya jalur `MASUK-ALASAN`, ledger membedakan alasan vs veto, dan `prepush`/`security_gate` tetap hijau |

Urutannya penting: **P31.1-2 dulu** (bisa malam ini), P31.4 paralel (butuh hari), **P31.6 terakhir
dan bersyarat**. Yang dilarang: membalik urutan supaya demo terlihat lengkap.

## 3b. Vonis pertama lab (`tools/entry_lab.py`, 28 Sep ±11:32Z, `spec_sha256=0x3ecad842…`)

Pool = 789 kejadian tanpa kerumunan jual, mean winso **+290,8**, `P(net >= +500) = 41,7 %`.
Control = mengacak 156/537 posisi dari pool itu, 400 undian.

| hipotesis | n | mean winso (CI 95 %) | median | P>=500 | CI atas control | verdict |
|---|---|---|---|---|---|---|
| **E1** tenang-setelah-kerumunan | **17** | tidak diuji (n<20, F-D16) | - | - | - | **BELUM BISA DIUJI** |
| **E2** jendela risiko (risk-on) | 156 | +368,4 [+144,9; +587,7] | **+146,5** | 43,6 % | +487,5 | **BELUM - di bawah control** |
| **E3** sepi saja (kontrol E1) | 537 | +275,6 [+159,5; +396,7] | +86,1 | 42,6 % | +411,5 | **BELUM - di bawah control** |

BH pada uji ekor: **TIDAK ADA**. Di atas control acak: **TIDAK ADA**.

Tiga hal yang kupelajari dari vonis ini, dan yang kedua menjengkelkan:

1. **Kriterianya bekerja.** E2 punya median **+146,5** dan 52,6 % posisi positif - kalau kami boleh
   berhenti di situ, itu sudah cukup terdengar seperti "gas". Tapi mean-nya masih di dalam pita
   control acak, dan ekornya tidak naik: yang E2 lakukan sebagian besar adalah **memindahkan
   median**, bukan menaikkan harapan. Untuk strategi dengan budget 5 posisi/hari, median bukan
   taruhannya - harapan dan ekornya yang itu.
2. **E1 hampir tidak pernah terjadi: 17 dari 789 (2,2 %).** Pola "kerumunan -> sepi -> harga masih
   di atas" jarang terjadi pada jendela 50 jam kami. Ini bukan "tidak ada efek", ini **"belum bisa
   diuji"** - dan bedanya harus ditulis, karena godaan berikutnya adalah melonggarkan ambang
   `cluster_usd_min >= 500` supaya n-nya besar. Itu persis kesalahan yang dilarang F-D33: ambang
   sudah dikunci (`spec_sha256` di `decisions/prereg-entry-lock.json`), jadi melonggarkannya =
   spesifikasi baru = hipotesis baru dengan kunci baru, bukan E1 yang sama.
3. **E3 == E1 tanpa syarat cluster, dan E3 tidak lebih baik dari pool.** Jadi "sepi" saja bukan
   alasan; kalau nanti E1 tumbuh bersama data, dia harus membuktikan diri **melampaui E3**, bukan
   melampaui nol.

Yang berubah di rencana: **E1 ditunda sampai n-nya cukup** (butuh >= 20 dan idealnya >= 100; pada
2,2 % dari pool, itu butuh ~5-9 hari rekaman) -> digabung ke P30/P29 yang memang menumpuk data.
**E2 tetap hidup sebagai hipotesis** tapi pertanyaan berikutnya bukan "mean-nya berapa" melainkan
"kenapa median naik sementara harapan tidak" - pada distribusi miring, itu biasanya berarti filternya
memotong ekor KIRI (kerugian besar) tanpa menaikkan harapan. Kalau benar begitu, klaim yang jujur
bunyi *"E2 mengurangi buntut buruk"*, bukan *"E2 menambah harapan"* - dan itu hipotesis baru (E2b)
dengan kunci sendiri, bukan E2 yang direvisi.

## 3c. Dua vonis terkunci sudah jatuh - dan keduanya NEGATIF

| kunci dipasang | dievaluasi | spesifikasi | hasil |
|---|---|---|---|
| 28 Sep 08:30Z (`0x03aa212f…`, `t_kunci` 06:13:38Z, harga `px`) | 21:24Z, 15,12 jam rekaman baru | halaman 11 | 275 kejadian; `uji_primer`/`uji_kedua` SAMPEL TIDAK CUKUP; `uji_ketiga` +219,2 CI [−18; +2138] p=0,0490 -> **GAGAL** (yang memotong: syarat CI bawah, bukan p) |
| 28 Sep 09:49Z (`0x6f69e100…`, `t_kunci` 09:38:44Z, harga PERISTIWA) | 21:45Z, 12,05 jam (alat menolak di 11,99) | halaman 12 | 265 kejadian; `uji_primer` K≥2 **−1.518,5 CI [−7.379; −3]**; `money_spread` −747,9; `stack≥2` −1.124,3 CI [−3.310; −3] -> **GAGAL, arah terbalik** |

**Vonis epik sejauh ini: kerumunan maker bukan gas, dan belum terbukti rem yang berdiri sendiri di luar `jual_*` yang sudah terukur.** Yang TIDAK boleh dilakukan karena angka terakhir: membalik tanda jadi sinyal fade - aturan halaman 12 menutup dua arah, dan 40 pasangan bukan dasar untuk mengganti teori. Kalau fade dikejar: spesifikasi baru, kunci baru, data yang belum dilihat (P32/P33/P34 tetap jalan lebih dulu).

## 3d. E7: untuk pertama kalinya ada satu fitur yang melewati kontrolnya - dan dia belum boleh dijual

`tools/topk_test.py` (29 Sep 04:52Z, artefak `decisions/topk-test-20260929T045553Z.json`;
403 kejadian, 24 siklus 30 menit, harga masuk/keluar dari ticker `wp`, ongkos 59 bps, penjelajahan
berhenti di `t_kunci` watch 02:59:06Z). Kontrolnya diubah bentuk dulu: bukan acak sepanjang jendela,
tapi **acak sesama kandidat di siklus yang sama** - karena yang agen hadapi bukan "kerumunan vs
rata-rata sepanjang masa", tapi "lima kursi dari kandidat yang ada detik ini".

| fitur | n | mean winso | median | acak-siklus (CI atas) | vonis |
|---|---|---|---|---|---|
| **`vol_rendah`** | 95 | **+132,9** | −59,0 | −134,3 (**+116,1**) | **DI ATAS ACAK** |
| `di_bawah_puncak60` | 95 | +107,1 | −47,1 | −125,8 (+115,8) | di bawah acak (selisih 8,7 bps) |
| `usd_ge_1k` | 95 | −132,0 | −121,9 | −129,6 (+175,2) | di bawah acak |
| `sepi_total` | 95 | −41,1 | −65,2 | −126,8 (+109,2) | di bawah acak |
| `vol_tinggi` | 95 | −199,2 | −509,7 | −141,8 (+101,0) | di bawah acak |
| `di_atas_puncak60` | 95 | −161,9 | −67,3 | −131,6 (+128,6) | di bawah acak |
| `spread_ok` | 95 | −396,9 | −811,0 | −125,7 (+114,1) | di bawah acak |
| `banyak_jual` | 95 | −403,3 | −811,0 | −130,2 (+123,1) | di bawah acak |
| `maker_ge3` | 95 | −434,4 | −789,1 | −115,7 (+131,2) | di bawah acak |
| `kluster_beli` | 95 | −425,7 | −751,1 | −123,8 (+126,3) | di bawah acak |

Tiga hal yang wajib disebut bersama tabel itu:

1. **Sepuluh uji sekaligus.** Peluang satu "menang" tanpa efek apa pun ≈ 10 × 0,025 = **0,25**.
   Dengan koreksi Bonferroni, `vol_rendah` **tidak signifikan**. Ini kandidat pertama yang arahnya
   bertahan saat kontrolnya diperketat - bukan hasil.
2. **Mediannya tetap −59,0 bps** (= persis lantai ongkos). Keuntungannya ada di ekor kanan
   (P(≥+500) 31,6 %), bukan di posisi tipikal. Harapan yang datang dari ekor tidak bisa dijual
   sebagai pendapatan - dan tanpa kedalaman (P33) kita tidak bisa mengklaim bisa mengambilnya.
3. **Pool-nya tetap −183,7 bps** sebelum penyortiran apa pun. Jadi kalau `vol_rendah` benar, yang
   ia lakukan adalah *memilih dari kolam yang bocor*, bukan mengeringkannya.

> **⚠ E8 JUGA DICABUT 29 Sep 05:54Z** - kontrolnya salah. Di kolam dengan mean **-183,7 bps**,
> "keluar lebih awal" mengalahkan "menahan sampai habis" tanpa tahu apa pun tentang pasar. Lawan
> **keluar di waktu ACAK pada jendela yang sama** (`tools/exit_control.py`, 122 posisi identik):
> kerumunan +316,6 vs acak +187,9 dengan **CI atas +357,1**; per posisi 64 menang / 50 kalah,
> **p=0,112** -> **tidak lewat**. Yang terukur adalah **umur posisi**, bukan kerumunan.
> [[00-Overview/03 - Decisions]] F-D40.

**E8 - sisi keluar, dan ini yang pertama bisa dipasang sebagai perilaku.** Keluar saat **kerumunan
beli datang** (≥2 maker berbeda dalam 15 menit) vs menahan sampai horison, diukur pada **posisi yang
sama** (`tools/topk_test.py` `uji_keluar()`, artefak yang sama): 122 posisi dipantau, keluar dini
menolong **69**, merugikan **45**, median **+116,5 bps**, mean winso **+316,6 bps**, persentil
5-95 **[−2.000; +2.000]** - ekornya menyentuh lantai di dua arah, jadi angka ini perbaikan rata-rata
pada pool yang sangat miring, bukan gaji. Perilaku ini sudah jadi alat: `tools/exit_policy.py`
(tiga pemicu: kerumunan datang, harga kini ≥ puncak 60 menit pertama, jaring +4 %; `TAK ADA DATA`
kalau ticker basi - tidak diperlakukan sebagai "bersih").

**Koreksi yang wajib dibaca sebelum kalimat di atas:** ketika pembandingnya dibuat setara
(mean = median dari 40 pengulangan pemilihan, bukan satu undian), **E7 tidak menyisakan pemenang
apa pun**: `vol_rendah` +112,7 vs CI atas acak +137,5, hanya 33 % seed di atas kontrol. Vonis E7
sekarang: **TIDAK ADA fitur yang melewati acak-siklus** (F-D39). E9 jadi satu-satunya jalur tersisa
ke jawaban "kapan boleh masuk", dan dia sudah terkunci sebelum koreksi ini - kuncinya TIDAK digeser.

**E9 - kunci keempat dipasang 29 Sep 05:13Z** sebelum satu byte data replikasi ada:
[[06-Results/18 - Kandidat Pertama, Diuji Hidup]], `spec_sha256=0x9d70c580…`, matang **17:13:25Z**,
`tools/vol_ab.py`. Dua lengan dibuka hidup-hidup oleh job `paper-book` (`vol-rendah` vs
`vol-tinggi`, jam yang sama, feed yang sama, gerbang yang sama) dan vonisnya tiga syarat serentak
(n≥20, median>0 DAN CI bawah>0, Mann-Whitney satu arah A>B p<0,05 - sekarang dengan fungsi yang
sudah dibetulkan). Kalau n<20 saat matang: "BELUM BISA DIUJI", ambang tidak diturunkan.

## 3e. E11 - kabar itu ada, dan dia berumur dua menit (29 Sep 07:58Z)

Setelah semua kandidat masuk dan keluar dicabut oleh kontrolnya sendiri, satu pertanyaan belum
diukur: **berapa lama boleh memegang**. Jawabannya (`tools/horizon_decay.py`,
`decisions/horizon-decay-20260929T075846Z.json`): harapan **naik** di menit-menit pertama setelah
buy kerumunan pintar lalu **meluruh** menjadi rugi - mean winso +192,7 @2m, +202,6 @5m, +45,0 @10m,
−42,0 @15m, −182,5 @30m - dan berpasangan pada posisi yang sama **5 dari 5 horison pendek mengalahkan
30 m** (p ≤ 0,00002). Placebo asal-mula (digeser acak 30–90 m) **datar di −180**: kemiringannya
milik peristiwa, bukan milik jam.

Ini bukan "Fabius bisa trading", dan tiga alasan yang menahan kami tetap tulis: mediannya +20…+60
bps (harapan ada di ekor kanan, P(≥+500) 37–40 %), **bump-nya menyusut −24…−41 bps** kalau harga
masuk diambil dari `tx.p` (F-D30 mengingatkan kami dari arah yang sama), dan - yang paling menentukan -
**menunda masuk 2 menit saja sudah membuat median@5m jadi −56,2**, sementara cron keputusan kami
berjalan tiap 4 jam. Latensi data bukan masalahnya (median 0,2 menit, dari stempel commit GitHub);
yang belum ada adalah jalur sinyal→order dalam dua menit (P40).

Karena itu E11 dipindah ke depan, bukan dijual: **P39** mengunci horison pendek sebagai *kebijakan*
dan mengujinya prospectif pada data yang belum terlihat, dengan horison 30 m sebagai kontrol pada
posisi yang sama. [[06-Results/19 - Umur Posisi]] adalah halaman angkanya; F-D41 adalah keputusan
dan empat kontrolnya.

## 3f. E13 - satu-satunya hal yang masuk di horison cepat adalah REM (29 Sep 08:43Z)

Gerbang ⑦ (`jual_*`) dipasang karena F-D31 mengukurnya menguntungkan **di horison 30 menit**
(+82,7 → +162,3 bps). Setelah E11 menunjukkan bahwa 30 menit itu bocor, pertanyaan jujurnya: masih
bergunakah rem itu di tempat kabar hidup? `tools/veto_expectancy.py` menjawab dengan kode gerbang
yang sama yang dipakai agen, per kejadian, di 2/5/30 menit:

| horison | n boleh | n veto | mean boleh | median boleh | mean veto | median veto | selisih | CI atas placebo |
|---|---|---|---|---|---|---|---|---|
| 2 m | 309 | 91 | +262,5 | **+58,5** | −187,8 | −393,1 | +450,3 | +294,5 |
| 5 m | 308 | 92 | **+285,5** | **+79,8** | −230,3 | −377,8 | **+515,8** | **+397,2** |
| 30 m | 307 | 92 | −72,7 | −61,9 | −560,2 | −996,6 | +487,5 | +405,1 |

Tiga hal yang jarang datang bersamaan di proyek ini: **median dan mean searah** (median `BOLEH` di
menit ke-5 = +79,8 bps, di atas lantai ongkos −59, jadi hasilnya tidak ditopang satu ekor),
**placebo-nya benar** (penandaan ulang acak 200 undian - kontrol yang sama yang membunuh E7 dan E8),
dan **tidak ada ambang baru** yang disetel: gerbangnya `flow_gate.py` apa adanya.

Batas yang menempel: VETO bukan kelompok acak - dia adalah kejadian yang sedang dihajar penjual,
sehingga yang boleh diklaim adalah *"menolak saat kerumunan menjual memperbaiki hasil di horison
cepat"*, bukan sebab-akibat. Batas venue (3,1 %, F-D43) dan batas latensi (2 menit, F-D41) tidak
bergerak oleh halaman ini. Dan statusnya **EKSPLORASI tanpa kunci** - [[06-Results/21 - Rem di Horison Cepat]] §3.

Jadi jawaban sementara atas pertanyaan builder ("kalau dia cuma tahu kapan jangan masuk, apa
bedanya dengan orang yang tidak berani masuk?") sekarang punya angka: **rem itu bukan penghindar
umum - dia memisahkan +285,5 dari −230,3 bps di horison 5 menit, melewati placebo.** Yang belum
kami punya tetap: alasan *positif* untuk masuk di luar "tidak ada kerumunan jual", dan jalur yang
cukup cepat untuk mengambilnya.

**E14 - remnya tidak di atas tebing.** `tools/veto_sensitivity.py` menggeser `MAKER_MIN` (1..4) dan
`RASIO_JUAL` (1,25..3,0) di grid 4×4: **16/16 kombinasi melewati placebo**, selisih menit ke-5
**+260,0 … +399,7 bps** melawan CI atas acak **+170,2 … +254,4**, dan alatnya memverifikasi dulu
bahwa pemindaian ulangnya **identik dengan `flow_gate.state()` untuk 677/677 kejadian** sebelum
berani melaporkan apa pun. Tidak ada satu pun ambang yang diubah - itu akan butuh kunci sendiri.
(F-D45)

## 4. Non-goal eksplisit

- Tidak menaikkan `promote-after` di bawah gerbang F-D16 walau streak tercapai.
- Tidak menambah fitur sampai satu fitur diuji terhadap control pada sampel penuh.
- Tidak menjual `lock_percent` lagi: ia sudah hidup sekali sebagai kandidat dan **mati sebagai
  kebijakan** karena memilih subset yang punya data (baseline −64,7), bukan karena pasar menolak idenya.
- Tidak menulis satu pun angka halaman ini sebagai PnL. Belum ada fill, belum ada kedalaman.
- Tidak menjual `vol_rendah` sebagai "Fabius tahu kapan masuk" sebelum E9 jatuh: satu pemenang dari
  sepuluh uji adalah **kandidat**, dan kita sudah dua kali melihat kandidat mati di hari kedua
  (`lock_percent`, kerumunan maker).
- Tidak mengutip satu pun `p` dari `mann_whitney_p` versi sebelum 29 Sep 05:00Z tanpa menghitung
  ulang - fungsi itu salah urut dan salah ties (F-D37), dan ia sudah menggerakkan satu baris vault.

**Terkait:** [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] · [[06-Results/14 - Buku Paper]] ·
[[06-Results/12 - Harga Masuk yang Benar]] · [[TradingKnowledge/O5 - Whale dan Kohor Smart Money]] ·
[[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]] · [[TradingKnowledge/QT2 - Backtesting yang Jujur]] · [[Concepts/One-Way Gate]] · [[00-Overview/03 - Decisions]] F-D31/F-D32/F-D33

## 3g. F-D54 (29 Sep 12:55Z) - kecepatan bukan lagi alasan, dan angkanya baru sekarang boleh dipakai

Epik ini berdiri di atas satu kalimat yang kutulis di §3e/§3f: *"bump-nya nyata, tapi kabarnya tiba
pada umur 13,5 menit, sedangkan bump hidup ±2 menit"*. Kalimat itu **dicabut sebagai bukti** - ia
mengukur bug di `beli_baru()` (kandidat diambil dari urutan berkas = yang tertua di jendela), bukan
dunia. Sesudah `b990ab5` umur kabar saat memutuskan **61 d** (n=182, p90 89 d).

Dan begitu pengukurannya benar, epik ini akhirnya punya angka masuk yang sah - bukan positif:
**n=25 lengan 5 m, mean winso −519,4 / median −76,4 bps, positif 5 dari 25, umur keputusan median
58 d, 24 token berbeda.** Penyebab yang terukur, bukan diduga: `entry_px − tx_p` median **+25,7 bps**
dan sudah **di atas** harga whale pada **16 dari 25** posisi - kami membeli pada harga *hasil* sinyal,
bukan harga yang dilihat sinyal (V5, FD3 §5, L3).

**Yang berubah untuk urutan kerja di halaman ini.** Tidak ada lagi tempat untuk alasan "kami belum
cepat". Sisa yang menahan `## Alasan masuk` adalah: (1) **titik masuk vs horison belum dipisah**
-> **P55/P56** (prospektif + kontrol acak sejawat); (2) **cakupan venue 3,1 %** (F-D43) belum berubah;
(3) `i` **+245 bps** (E21) belum berubah; (4) semua ini n=25 dan **retrospektif terhadap perbaikan
alatnya sendiri** - jadi belum bisa dijual, hanya bisa dijadikan kunci berikutnya. Tabel T1-T7 di
[[08-Backlog/03 - Epik Teori Baru]] ikut bergerak: T4 (trailing) masih buntu data, T2/T3 tetap nol,
dan sekarang ada **T8 - titik masuk sebagai objek uji** yang sebelumnya tidak pernah bisa diuji
karena alatnya sendiri salah.

Lihat: [[06-Results/26 - Masuk Segar, Terukur Benar]] · [[06-Results/19 - Umur Posisi]] §2b ·
`00-Overview/03 - Decisions.md` F-D54.


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
| **E5** | **posisi dalam pump** (`tarik dari puncak`, `jatuh dalam`) | "beli darah" adalah intuisi masuk yang paling umum | ada | **SUDAH DIUJI - SALAH**: −2.853 bps (MW p=1,0) vs baseline; buy-the-dip justru yang paling buruk |

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

## 4. Non-goal eksplisit

- Tidak menaikkan `promote-after` di bawah gerbang F-D16 walau streak tercapai.
- Tidak menambah fitur sampai satu fitur diuji terhadap control pada sampel penuh.
- Tidak menjual `lock_percent` lagi: ia sudah hidup sekali sebagai kandidat dan **mati sebagai
  kebijakan** karena memilih subset yang punya data (baseline −64,7), bukan karena pasar menolak idenya.
- Tidak menulis satu pun angka halaman ini sebagai PnL. Belum ada fill, belum ada kedalaman.

**Terkait:** [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] · [[06-Results/14 - Buku Paper]] ·
[[06-Results/12 - Harga Masuk yang Benar]] · [[TradingKnowledge/O5 - Whale dan Kohor Smart Money]] ·
[[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]] · [[TradingKnowledge/QT2 - Backtesting yang Jujur]] · [[Concepts/One-Way Gate]] · [[00-Overview/03 - Decisions]] F-D31/F-D32/F-D33

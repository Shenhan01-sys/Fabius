---
tags: [tk, tk-fondasi, "FD9"]
---

# FD9 - Horizon Waktu dan Multi-Timeframe

**Keluarga:** [[00 - Hub Fondasi]] · **Tahap:** analisis ([[PL3 - Menganalisis]]), penilaian ([[PL6 - Menilai Hasil]])
**Sumber:** [[Fakta Terukur]] §A/§E/§F · `tools/backtest.py` (non-overlap) · `tools/direction.py` (horizon) · [[06-Results/06 - Pre-registration Horizon]] · sisanya pengetahuan standar pasar

**Ringkas:** Horizon bukan "durasi hold" — ia unit pengamatan. Ia menentukan berapa banyak sampel
yang bisa ada, apakah sampel itu bebas, dan pertanyaan mana yang sebenarnya dijawab. Kebanyakan
angka trading yang terlalu bagus lahir bukan dari curang, melainkan dari menghitung satu peristiwa
berkali-kali karena jendelanya tumpang tindih.

## Definisi yang bisa dihitung

```
horizon H      : jumlah bar dari keputusan sampai hasil dinilai
overlap        : window(i) = [t_i, t_i+H]; overlap bila t_{i+1} < t_i + H
non-overlap    : t_{i+1} >= t_i + H            -> tiap peristiwa dihitung sekali
                 `tools/backtest.py` memajunya dengan `t += horizon` dan menulis `non_overlap: True`
efektif n      : n_true ~ n_obs / (1 + overlap fraction)   -> rumus praktis, bukan hukum
kebocoran bar  : memakai penutupan bar t untuk memutuskan DAN menghargai entry di bar t (mustahil
                 dieksekusi). aturan yang dipakai: keputusan dari bar <= t, entry dari bar berikutnya
satu keputusan : maksimal satu taruhan aktif per (aset, horizon)
```

Dua efek yang selalu bergerak berlawanan: horizon pendek memberi **lebih banyak sampel** tapi
**lebih sedikit sinyal per sampel** (karena gross-nya kecil melawan ongkos yang tetap); horizon
panjang memberi gross lebih besar tapi sampelnya sedikit dan world-nya berubah di tengah jalan.

## Cara pakai yang diklaim

Klaim praktisi: analisis di timeframe besar untuk arah, entry di timeframe kecil ("multi-timeframe
confluence"), dan "whale bermain swing, bukan scalping". Kalimat terakhir itu **bukan** sesuatu yang
boleh kami tulis sebagai sudah terjawab. Yang terjawab di repo ini hanya satu arah: pada horison
pendek (4 j – 7 hari) mengikuti panel smart money **rugi** (§F: −10,4 bps/jam, dan horison 24 j
0/12 lolos untuk aturan arah kita). Angka tempat hasil whale tampak berbalik di 30 hari berasal dari
`decisions/whale-sweep-90d.json` — artefak yang **diblokir §H** (`cost_bps_applied = 0.0`, `p_boot`
identik belum terjelaskan) dan halaman sumbernya melarang kalimat "ada edge di 30 hari"
([[06-Results/06 - Pre-registration Horizon]]). Jadi yang benar: **horizon mengubah jawaban**, dan
dugaan builder soal "swing, bukan scalping" tetap **hipotesis** sampai Uji A (prospektif) selesai —
bukan kesimpulan yang sudah diukur.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| bar 1 jam ≥ 2.400 untuk horizon 4 j dan 24 j | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari — §A; hanya aset ber-kontrak perp |
| bar 4 jam / 1 hari (timeframe besar) | `ADA-TAPI` | yang ditarik jalur arah hanya `1h`; interval lain belum diambil, jadi filter HTF tidak ada sebagai aturan |
| penanda "bar berjalan dibuang" | `ADA-TAPI` | pembuangan terjadi **saat fetch** (`tools/bars.py:113` → `t + step <= now`), bukan saat dibaca: kalau deret datang dari cache berumur, bar terakhir cache memang sudah selesai *saat ditulis* tapi sudah basi — `tools/direction.py` tidak memeriksa ulang, ia cuma mencatat `t_last` |
| funding berinterval 4 jam (cocok dengan horizon) | `ADA-TAPI` | kebetulan yang dicatat sebagai kebetulan; histori per aset tidak bisa ditarik mundur — §A/§C |
| riwayat jam rekaman (untuk efek sesi/jendela) | `ADA-TAPI` | `manifest` mencatat gap antar-tarikan; satu jam yang bolong **tidak bisa diminta kembali** — turunan dari §B ("yang lewat = hilang") |

## Uji di Fabius

Yang sudah ada bentuknya:

1. **Non-overlap ditegakkan di kode.** `tools/backtest.py` memaju titik keputusan sebesar horizon dan
   menolak kesimpulan di bawah `MIN_TRADES` 20 (§E). Uji 24 j dijalankan dan **0/12** simbol lolos
   (syarat: n ≥ 20, net > 0, drop-best-fold > 0, BH α 0,10) — §F.
2. **Split-sample dan horizon ganda dikunci sebelum hasil**
   ([[06-Results/05 - Pre-registration Flow]], [[06-Results/06 - Pre-registration Horizon]]): horizon
   tambahan = tes tambahan, jadi BH dijalankan lintas horizon juga.

Yang **belum** dan mengikat kredibilitas angka: satu keputusan yang direkam saat ini menanyakan arah
"over next 4 hours" ke penilai, sementara `horizon_h` yang ditulis ke rekaman bernilai 24 jam untuk
semua keputusan non-`flat` (`tools/direction.py`: `TIME_STOP_H` dan cabang lain sama-sama 24). Jadi
pertanyaan dan penilaian memakai horizon berbeda — dan `tools/ledger.py` menilai yang **tercatat**,
bukan yang ditanyakan. Sebelum ini dibereskan, setiap angka "horizon 24 jam" di jalur arah adalah
angka tentang keputusan 4 jam. Perintah audit silang (belum ditulis): bandingkan `horizon_h` dengan
 teks pertanyaan yang ikut di-hash.

## Batas dan mode gagal

- **"Timeframe" yang benar di mikrostruktur bukan jam dinding, tapi jumlah pergerakan harga.**
  Queue/microprice memprediksi **pergerakan mid-price berikutnya** (arXiv:1512.03492v1 - samplingnya
  bahkan diambil pada waktu acak *di antara* dua pergerakan), dan horison tempat dampaknya terukur
  adalah **Δt = 10 detik** (arXiv:1011.6402v3); pada **1 menit ke depan**, R² out-of-sample justru
  **negatif** di S&P 100 (arXiv:2112.13213v4: −0,37 … −0,36). Jadi menanyakan "entry di 5 menit
  apakah sama dengan 15 menit?" di venue kecil adalah salah satuan: yang berubah bukan resolusinya,
  tapi **jumlah berita yang sudah dicerna harga**.
- **Punya kami, terukur (29 Sep):** kabar ⑦ hidup **±2 menit** (E11: +192,7 @2m → +45,0 @10m →
  −182,5 @30m), ticker `wp` berdetak ±1 kali per beberapa puluh menit, dan siklus keputusan ⑦/⑨
  ±200 detik. Artinya: horison tempat sinyal hidup **lebih pendek dari jeda antar-pengamatan kami**.
  Bukan alasan untuk tidak menguji - alasan untuk tidak menyimpulkan "teorinya salah" dari nol yang
  diukur di luar resolusi.
- **Kalau dipaksa jadi satu kalimat kerja:** horison kami dibatasi oleh *biaya*, bukan oleh
  *perkiraan*. Dengan ongkos 59,0 bps dan harapan **median** terbaik yang pernah kami ukur
  (+79,8 bps, E13 menit ke-5), ruang spread tersisa **≈21 bps** - dan itu angka alat
  (`tools/cost_budget.py`), bukan opini tentang timeframe.


- **Overlap membuat p palsu kecil.** Jendela yang tumpang tindih berbagi hasil yang sama; aproksimasi
  normal kami sudah sistematis terlalu optimis pada n=20–40 (§E) — overlap menambahnya.
- **Horizon boleh dipilih karena aritmetika sampel, bukan karena tesis.** Memilih 4 jam supaya
  cukup penutupan terkumpul sebelum tenggat adalah keputusan sah — dan harus ditulis apa adanya
  ([[01-Agent/01 - Asset Classes and Seats]] §4 melakukannya). Menyembunyikannya sebagai "karena
  struktur pasar" adalah memoles.
- **Kebocoran antar-bar dua arah:** memakai bar berjalan, atau memakai close bar `t` sebagai harga
  masuk untuk keputusan yang diambil pada `t`. Yang kedua lebih sering lolos karena terlihat jujur.
- **Efek sesi di pasar 24/7 bukan tidak ada — hanya bukan sesi bursa.** Yang berkala dan nyata di
  sini: funding per 4 jam, rollover hari UTC (plafon harian direset per hari blok di
  `contracts/ExecutionVault.sol`), jam perekaman Actions yang bolong (§B), dan stempel UTC vs WIB
  (`tools/direction.py` menulis berkas dengan tanggal UTC supaya satu peristiwa tidak punya dua
  tanggal). Apakah jam-jam itu memprediksi hasil: *(belum diukur)*.
- **Duplikasi lintas timeframe:** SMA24 di bar 1 jam adalah filter 1 hari; menyebutnya "konfirmasi
  timeframe besar" memberi kesan dua informasi padahal satu ([[FD1 - Struktur Pasar dan Rezim]]).

## Tingkat bukti

`T1` untuk non-overlap dan larangan bocor antar-bar (praktik riset yang benar, ditegakkan kode kami) ·
`T3` **khusus** untuk "jawaban berubah ketika horizon diubah" — yang terukur adalah sisi pendeknya
(−10,4 bps/jam pada panel, §F; aturan arah 0/12 lolos di 24 j, §F). Horizon panjang **tidak** dapat
tangga apa pun dari catatan ini: angkanya ada di artefak yang diblok §H · untuk klaim "efek sesi jam
bekerja di crypto": belum diuji sama sekali.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "horizon adalah unit sampel; kami memajunya non-overlap, menguncinya sebelum hasil, dan
  sudah melihat jawaban berubah ketika horizon diubah."
- **Dilarang:** "timeframe besar selalu benar" · "angka 24 jam kami adalah hasil dari pertanyaan
  24 jam" · menyebut sampel overlap sebagai `n` bebas.

**Terkait:** [[FD1 - Struktur Pasar dan Rezim]] · [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] ·
[[EV3 - Signifikansi dan Multiple Testing]] · [[EV5 - Reproduksibilitas dan Pra-Registrasi]] ·
[[QT3 - Data Fitur dan Label]] · [[PL6 - Menilai Hasil]]

## Koreksi 29 Sep 12:55Z - horisonnya bisa dikejar; yang belum pernah menghasilkan adalah titik masuknya (F-D54)

Halaman ini memakai "kabar sudah berumur ±13,5 menit saat kami memutuskan" sebagai bukti bahwa horison
2 menit mustahil kami kejar. **Bukti itu dicabut**: itu bug pemilihan kandidat di `tools/fast_lane.py`
(kandidat diambil dari urutan berkas = yang tertua di jendela). Sesudah `b990ab5` mengambil yang
tersegar, umur kabar saat memutuskan jadi **median 61 d** (n=182, p90 89 d, 97 % di bawah 180 d) - dan
`arr − t` pada baris yang kami putuskan **24 d**. Sumbernya memang muda.

Yang menggantikannya justru lebih tidak enak: dengan umur keputusan **median 58 d**, pada 25 lengan 5 m
yang pengukurannya **sah**, hasilnya **mean winso −519,4 / median −76,4 bps**, positif cuma 5 dari 25
(`tools/fast_lane.py --report`, 29 Sep 12:5xZ). Bentuk aturan yang benar karena itu bukan "horison 2
menit tidak bisa dikejar", melainkan **"horison 2 menit bisa dikejar, dan tidak pernah berubah jadi
hasil ketika harga masuknya adalah harga yang benar-benar bisa kami dapat"**. Lihat §4a (`delay`) yang
sekarang punya padanan hidup, dan [[06-Results/26 - Masuk Segar, Terukur Benar]] untuk tabelnya.
Aturan turunannya tidak berubah: horison dinyatakan **relatif terhadap peristiwa**, dan titik masuk
dihitung dari harga yang bisa kami eksekusi - bukan dari harga yang dilihat sinyal.


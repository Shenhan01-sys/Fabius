---
tags: [hasil, "pra-registrasi", "E9", "alasan-masuk"]
---

# 18 - Kandidat Pertama, Diuji Hidup

**Bagian dari:** [[06-Results/00 - Hub Results]] · [[08-Backlog/02 - Epik Alasan Masuk]]
**Status:** TERKUNCI sebelum data replikasi ada · **Alat:** `tools/vol_ab.py` · **Eksekutor:**
`tools/paper_book.py` (lengan `vol-rendah` / `vol-tinggi`, keduanya `--emit` di job `paper-book`)

## 1. Kenapa halaman ini ada

Sampai 29 Sep ±05:00Z tidak ada satu pun fitur yang melewati kontrolnya sendiri. Uji **E7**
(`tools/topk_test.py`, 10 fitur, outcome dari ticker `wp`, ongkos 59 bps, kontrol = acak **sesama
kandidat dalam siklus 30 menit**) menghasilkan satu anomali:

```
   fitur               siklus      n       mean    median      P>=500 acak (CI atas) vonis
   vol_rendah              19     95     +132.9     -59.0       31.6%      -134.3 (  +116.1) DI ATAS ACAR
   di_bawah_puncak60       19     95     +107.1     -47.1       38.9%      -125.8 (  +115.8) di bawah acak
   usd_ge_1k               19     95     -132.0    -121.9       36.8%      -129.6 (  +175.2) di bawah acak
   kluster_beli            19     95     -425.7    -751.1       26.3%      -115.7 (  +131.2) di bawah acak
   (tujuh fitur lain: -403,3 .. -199,2 - semuanya di bawah acak)
```

> **⚠ DICABUT 29 Sep ±05:35Z - tabel di bawah adalah satu UNDIAN, dan undiannya menang
> karena kebetulan.** `topk_test` memecah seri dengan pengacak; mean "top-5 menurut fitur" adalah
> variabel acak, tapi versi alatnya membandingkan **satu** tarikan itu terhadap persentil-97,5
> distribusi acak. Setelah pembandangnya dibuat setara (40 pengulangan pemilihan, vonis memakai
> MEDIAN seed): **tidak ada satu pun dari 10 fitur yang melewati acak-siklus**. `vol_rendah`
> median **+112,7** vs CI atas acak **+137,5**, sebar seed **−30,7 … +299,7**, dan hanya **33 %**
> seed yang melewati kontrolnya. Run: `python -X utf8 tools/topk_test.py --draws 300`
> (artefak `decisions/topk-test-20260929T053349Z.json`).
>
> Ini kelas kesalahan yang sama dengan F-D32 (control mempromosikan dirinya sendiri) dan F-D37
> (MW salah urut), dan ketahuan karena alat berikutnya (`uji_kombinasi`/E10) minta angka yang sama
> dengan pembanding yang berbeda. [[00-Overview/03 - Decisions]] F-D39.

Angka itu **tidak boleh dijual**, dan alasannya aritmatika, bukan selera: sepuluh fitur diuji
sekaligus, jadi peluang ada satu "menang" walau tidak ada efek apa pun ≈ `10 × 0,025 = 0,25`.
Koreksi Bonferroni atas uji satu arah 2,5 % membuat `vol_rendah` **tidak signifikan**. Yang kita
punya adalah kandidat pertama dalam proyek ini yang arahnya bertahan saat kontrolnya diubah jadi
"pilihan acak pada jam yang sama" — dan satu-satunya yang mengubah kandidat jadi hasil adalah
**data yang belum terjadi**.

Perhatikan juga apa yang TIDAK berubah: `median` lengan pemenang tetap **−59,0 bps**. Harapan
positifnya datang dari ekor kanan (P(≥+500 bps) 31,6 %), bukan dari hasil tipikal. Itu konsisten
dengan seluruh corpus kami dan tidak boleh dibaca sebagai "pendapatan tetap".

## 2. Yang dikunci (teks ini yang di-sha, jangan disunting setelah hasil dilihat)

```text
E9 - A/B terkunci: lengan `vol-rendah` vs lengan `vol-tinggi` pada buku paper.

sumber_aturan : tools/topk_test.py E7 (10 fitur; hanya vol_rendah melewati acak-siklus)
lengan_A      : kebijakan == "vol-rendah" (separuh volatilitas wp terendah kandidat layak harian)
lengan_B      : kebijakan == "vol-tinggi" (kontrolnya, bukan nol)
harga_masuk   : seperti yang dicatat paper_book (tx.peristiwa + haircut dampak s/L)
hasil         : net_bps yang sudah dinilai paper_book (ongkos 59 bps RT sudah dipotong)
perhitungan   : HANYA slot dengan open_utc > t_kunci; slot sebelum kunci = prefill
vonis_layak   : (1) n_A >= 20 DAN (2) median_A > 0 DAN CI bawah bootstrap 4000 (seed 20260928) > 0
                DAN (3) Mann-Whitney satu arah A > B p < 0,05
kalau_kecil   : tulis "BELUM BISA DIUJI", jangan "TIDAK ADA EFEK"; ambang tidak diturunkan
lapor_wajib   : n tiap lengan, P(ada harga keluar), median, mean winso + CI, p MW, token unik
winso         : +/-2.000 bps pada mean (ekornya tebal di dua arah; median dilaporkan terpisah)
jangan        : tidak ada order, tidak ada rantai, tidak ada perubahan promote-after
```

## 3. Perbedaan yang jujur antara backtest dan uji hidup ini

Supaya tidak ada yang boleh bilang "kamu menguji hal yang sama":

| | E7 (backtest, halaman ini §1) | E9 (uji hidup) |
|---|---|---|
| kandidat | semua kejadian beli di feed ⑦ yang punya `wp` | kejadian yang sudah lewat gerbang veto `jual_*` (paper_book) |
| pemilihan | top-5 per siklus 30 menit | separuh volatilitas terendah per hari (budget 24 slot - naik dari 6 pada 29 Sep ±06:00Z SEBELUM satu slot pun dibuka, karena ember harian ini memuat seluruh jendela 05:13Z->17:13Z dan dengan 6/ember n lengan A tidak akan pernah sampai syarat F-D16; ini perubahan biaya, bukan perubahan aturan vonis) |
| harga masuk | ticker `wp` terakhir sebelum `t` | harga transaksi `tx.p` (kanonis F-D30) |
| hasil | `wp` median pada t+[15;45] m | `net_bps` seperti dicatat `paper_book` - ongkos 59 bps **+ istilah "dampak" yang satuannya baru diketahui salah ±600x** (F-D46; lihat kotak sebelum §5) |
| kontrol | acak sesama kandidat siklus itu | **lengan `vol-tinggi` pada jam, feed, dan gerbang yang sama** |
| volatilitas | `pstdev` return dari ≤40 baris `wp` terakhir | sama (`vol_sebelum()` disamakan, lihat catatan di bawah) |

Versi pertama `vol_sebelum()` membatasi jendelanya ke **30 menit** dan mengembalikan `None` untuk
**semua** kejadian: ticker watch hanya berdetak sekali per siklus rekaman (±35 menit), jadi 12 baris
dalam 30 menit tidak pernah ada. Kalau itu dibiarkan, A/B hidup ini menguji aturan yang berbeda dari
yang diukur — dan kegagalannya tidak kelihatan dari angkanya sendiri, karena "0 posisi" terlihat
seperti "belum ada yang layak".

## 4. Cara menjalankan

```bash
python -X utf8 tools/vol_ab.py --self-test    # 4 kasus: prefill dibuang, 3 syarat serentak,
                                              # n kecil != gagal, A==B tidak pernah LAYAK
python -X utf8 tools/vol_ab.py --lock         # pasang kunci SEKALI (menolak dobel = spec baru)
python -X utf8 tools/vol_ab.py --status       # umur kunci + jumlah slot per lengan
python -X utf8 tools/vol_ab.py                # vonis (menolak cetak angka sebelum matang)
python -X utf8 tools/vol_ab.py --tanpa-umur   # bacaan sementara, dicetak dengan LABEL PERINGATAN
```

Job `paper-book` (cron `23 */4`) membuka kedua lengan tiap empat jam; slot sebelum `t_kunci` adalah
prefill dan **tidak ikut vonis**. Kalau pada saat matang `n < 20`: vonisnya `BELUM BISA DIUJI`,
ambang tidak boleh diturunkan, dan itu bukan "tidak ada efek" ([[Concepts/Unmeasured Is Not Clean]]).

## 4b. Yang berubah setelah pembandingnya dibetulkan (29 Sep ±05:35Z)

E9 **tetap berjalan** - kuncinya tidak digeser, karena data setelah 05:13:25Z tetap data yang belum
pernah kita lihat, dan membatalkan uji hanya karena hasilnya jadi kurang menarik adalah One-Way Gate
versi pengebirian. Yang berubah adalah **prior-nya**: dari "kandidat pertama" jadi "tidak ada
candidate sama sekali di dalam sampel". Dua lengan dibuka terus sampai 17:13:25Z; kalauvonisnya
n<20, tertulis "BELUM BISA DIUJI", dan itu jawaban yang sah, bukan kegagalan.

E10 (kebijakan utuh: pemilihan × aturan keluar, pada posisi yang sama) bahkan **tidak konsisten pada
dirinya sendiri**: dengan outcome `net` (tahan sampai horison) `vol_rendah` +145,4 vs CI atas acak
+86,7 (80 % seed); dengan outcome `net_exit` (aturan keluar E8 dipasang) +164,0 vs +169,0 (47 % seed) -
**gugur**. Sementara pembanding yang dipakai E7 sendiri (`net`, CI atas **+137,5** pada run yang sama)
menaruhnya di **bawah** acak dengan 33 % seed. Tiga nilai CI atas untuk kontrol yang sama
(+86,7 / +137,5 / +169,0) mengukur satu hal: **pita Monte-Carlo kami lebih lebar daripada selisih yang
ingin kita klaim.** Tidak ada satu pun dari ketiganya boleh dijual; lihat
[[00-Overview/03 - Decisions]] F-D39.

## 4c. Catatan yang ditulis SETELAH lengan pertama terisi tapi SEBELUM vonis dibaca (29 Sep ±06:25Z)

Kedua lengan terisi pada hari yang sama: **24 slot pasca-kunci di tiap lengan**
(`decisions/paper-book-positions.jsonl`, `rows_sha256` A `0xcff59af824a927…` / B `0x99e803ff8b00ec…`).
Yang dikunci dan tidak boleh berubah: **aturan vonis, budget `--per-day 24`, dan ember hari 29 Sep**.
`n` sendiri masih bisa **bertambah** sampai 17:13:25Z (tiap siklus `paper-book` melihat kejadian baru
setelah kunci, dan separuh-bawah menurut volatilitas bisa berisi kandidat yang berbeda) - itu bukan
pelonggaran, itu konsekuensi dari aturan yang sudah ditulis. Yang TIDAK boleh: menyentuh `n_min`,
`--per-day`, atau isi blok spesifikasi.

Dua rem yang dipasang sekarang, sebelum vonis apa pun dibaca, dan TIDAK boleh dipakai membalik
keadaan kalau hasilnya jelek:

1. **Hari 30 Sep tidak boleh dipakai menyelamatkan vonis 29 Sep.** Slot besok adalah ember baru,
   dan kalau ia dipanggil untuk menutupi kegagalan ember ini, yang berubah adalah ukurannya, bukan
   dunianya. Kalau vonis 17:13:25Z gagal, vonisnya gagal - dan hari berikutnya hanya boleh bicara
   atas hipotesis BARU yang dikunci lagi.
2. **Angka antara lengan yang terlihat sekarang (mean A −191,9 vs B −278,3) BUKAN hasil.** Dia
   dicetak oleh `paper_book` sebagai tabel kebijakan, bukan oleh `tools/vol_ab.py`; vonis tunggal
   alat itu yang berlaku, tiga syarat serentak, dan kedua mean negatif membuat syarat (2) hampir
   pasti jatuh. Kalau itu yang terjadi, tulisannya begini: *aturan volatilitas rendah tidak
   menghasilkan harapan positif di data yang belum terlihat* - bukan "hampir" dan bukan "n kecil".

**Satu pengakuan sebelum vonis (F-D46).** Blok spesifikasi yang di-sha di §3 menyebut harga
masuk sebagai "tx.peristiwa + haircut dampak s/L". Kata "haircut" di situ kini
diketahui mengukur ±600x terlalu kecil (size BNB dibagi liq USD), dan **blok itu tidak kami
koreksi** - mengganti penggaris di tengah uji terkunci adalah cara paling halus untuk
memenangkan uji itu. Kotak ini ada di luar blok supaya sha-nya tetap utuh dan pembacanya tetap
tahu: **E9 membandingkan dua lengan dengan penggaris yang sama-sama terlalu murah.** Itu berarti
vonisnya berbicara soal *pilihan posisi*, bukan soal harapan yang bisa diambil. Kalau E9 lolos
sekalipun, angka buku yang sama menyebut varian dampaknya (tercatat +75,9 / satuan-dibetulkan
−715,7 / hanya-liq-sah −87,8 bps) - dan itu ditulis di halaman ini, bukan di slide.

**Peringatan sebelum vonis dibaca (F-D51, ditulis 11:5xZ - sebelum jam 17:13:25Z).** Peringkat
dua lengan ini **berbalik menurut budget**: pada `--per-day 200` lengan `vol-rendah` **+90,1** vs
`vol-tinggi` −98,3; pada 5/hari −318,8 vs −1.022,7 (rendah tetap lebih baik); pada **24/hari**
- yang dipakai uji ini - justru −98,0 vs **+43,3**. Dengan n=26 per lengan, apa pun yang keluar
malam ini adalah "satu budget, 26 posisi", bukan arah pasar. Kuncinya tidak kusentuh;
peringatan ini yang kutambah, seperti §5c.

## 5. Hasil

_kosong sampai umur kunci cukup — alatnya menolak mencetak angka sebelum itu, dan kekosongan ini
adalah bagian dari spesifikasinya, bukan kelalaian mencatat._

**Terkait:** [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] ·
[[06-Results/17 - Pra-Registrasi Watch]] · [[08-Backlog/02 - Epik Alasan Masuk]] §3d ·
[[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]] · [[Concepts/One-Way Gate]] ·
[[00-Overview/03 - Decisions]] F-D37/F-D38

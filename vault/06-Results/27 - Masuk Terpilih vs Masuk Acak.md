---
tags: [hasil, "pra-registrasi", "E24", "jalur-cepat", "kontrol-acak"]
---

# 27 - Masuk Terpilih vs Masuk Acak (E24)

**Bagian dari:** [[06-Results/00 - Hub Results]] · [[06-Results/26 - Masuk Segar, Terukur Benar]] ·
[[08-Backlog/02 - Epik Alasan Masuk]] §3g
**Alat:** `tools/entry_ab.py` (membaca `tools/fast_lane.py`) · **Kunci:**
`decisions/prereg-fastlane-lock.json`

## 1. Pertanyaannya bukan "untung atau rugi", tapi "lebih baik dari apa"

F-D54 memberi angka masuk pertama yang sah (**−519,4 bps** pada 25 lengan 5 m). Tapi angka tanpa
pembanding belum menjawab apa pun: kalau masuk **acak** pada menit pertama setelah whale membeli juga
memberi sekitar −520, maka yang buruk itu **substratnya**, bukan penilaian kami - dan itu kesimpulan
yang berbeda sekali, dengan akibat produk yang berbeda sekali.

Aturan repo ini sudah menulis jawabannya (F-D8): **yang harus dikalahkan adalah kontrol acak pada
siklus yang sama, bukan nol.** Sampai hari ini jalur cepat tidak punya lengan kontrol - dia hanya
membuka posisi yang direstui rem. Jadi kontrolnya dibangun dulu, lalu kuncinya dipasang.

## 2. Spesifikasi yang dikunci

```text
E24 - masuk terpilih vs masuk acak pada horison tempat kabar masih hidup.

populasi       : baris keputusan tools/fast_lane.py dengan dibuat_utc > t_kunci; lengan yang
                 dinilai hanya yang SAH (umur keputusan <= 120 d; jendela 5m mulai di
                 kejadian+120 d - F-D54), status dinilai, dan punya keluar_5m
lengan T       : yang dibuka setelah gerbang ⑦ BOLEH (label FAST-5m, kontrol != True)
lengan K       :kontrol acak siklus yang sama (label ACAK-5m, kontrol == True) - gerbang tidak
                 dilihat; satu kontrol per siklus; benih pengambilannya waktu siklus
outcome        : net_bps dari harga ticker `wp` saat keputusan ke median `wp` pada
                 kejadian+5m +-3 m, dikurangi ongkos round-trip terukur 59 bps
winsor         : +/-1500 bps pada mean; median dilaporkan tanpa winsor
vonis_primer   : selisih = mean_winso(T) - mean_winso(K)
syarat_layak   : (1) n_T >= 40 DAN n_K >= 40
                 (2) median(T) > 0 DAN CI bawah bootstrap 4000 (seed 20260929) dari selisih > 0
                 (3) Mann-Whitney satu arah T > K dengan p < 0,05
                 (4) komposisi kedua lengan dicetak: token berbeda, median umur keputusan,
                     median umur baris harga masuk - kalau T dan K tidak sebanding pada
                     ketiganya, vonisnya BELUM BISA DIUJI
kalau_gagal    : T tidak lebih baik dari K berarti seleksi kami tidak menambah apa pun di atas
                 "masuk acak pada menit pertama setelah whale beli"; angka T yang NEGATIF dan
                 K yang NEGATIF berarti substratnya yang buruk, bukan penilaiannya - dan itu
                 TIDAK boleh dibaca sebagai "fade saja", arah dibalik butuh kunci baru
```

**sha256 spesifikasi:** `0x4c90bb27ac947420d5be198643c46a572cc66c4e8837206263a619f615270473` · **t_kunci:** `2026-09-29T13:19:04Z` · **vonis boleh dijatuhkan mulai:**
`2026-09-29T21:19:04Z` · **kejadian pasca-kunci saat kunci dipasang: 0** - ujian ini belum melihat satu hasil pun.

## 3. Yang dibangun supaya uji ini ada

- `tools/fast_lane.py`: tiap siklus sekarang membuka **satu slot kontrol** (`label: ACAK-5m`,
  `kontrol: true`) yang dipilih **seragam dari kolam kandidat yang sama, benih = waktu siklus** -
  pengambilannya bisa dihitung ulang, dan **gerbang tidak dilihat**. Hanya kandidat berumur <= 120 d
  yang boleh jadi kontrol; kalau tidak ada, baris **`KONTROL-KOSONG`** ditulis (kehilangan dicatat,
  bukan dilewati).
- Angka perlakuan dan kontrol **tidak pernah digabung**: `report()` memisah daftar sejak baris
  pertama, dan `laporan_terpasang()` mengabaikan baris kontrol.
- `tools/entry_ab.py`: `--lock` / `--status` / tanpa flag = vonis; menolak sebelum matang; menolak
  jalan kalau sha spec tidak cocok; dan **kontrol negatif** di self-test - pada distribusi T dan K
  yang identik vonisnya harus GAGAL. Tanpa itu, harness apa pun bisa lulus dengan menjawab "ya".

## 4. Empat syarat, dan syarat keempat yang paling sering dilupakan

(1) n >= 40 di **tiap** lengan; (2) median(T) > 0 dan **CI bawah** bootstrap 4.000 dari *selisih*
mean > 0; (3) Mann-Whitney satu arah T > K dengan p < 0,05; (4) **komposisi kedua lengan sebanding**:
median umur keputusan tidak berbeda lebih dari 60 d, dan token berbeda + umur baris harga masuk
dicetak. Tanpa (4), T bisa menang hanya karena kontrolnya kebetulan lebih muda - itu F-D47 berkostum
baru.

## 5. Baca sebelum vonis

Kalau **GAGAL**: seleksi kami tidak menambah apa pun di atas "masuk acak di menit pertama". **Tidak
boleh** dibalik jadi "fade saja" - arah dibalik butuh kunci baru, bukan reinterpretasi.
Kalau **BELUM BISA DIUJI** karena n: itu berarti n, bukan teorinya.
Kalau **LAYAK**: ada alasan masuk *relatif terhadap acak* - dan masih harus melewati tembok venue
(3,1 %, F-D43) serta celah isi (`i` +245 bps, E21) sebelum boleh dibaca sebagai uang.

## 6. Hasil

**Dibaca 29 Sep 2026 21:27:32Z** oleh `python -X utf8 tools/entry_ab.py` (kunci `13:19:04Z`, syarat
umur 8 jam matang `21:19:04Z`; `spec_sha256=0x4c90bb27ac947420…` - blok §2 tidak kusentuh).
Artefak: `decisions/entry-ab-vonis-20260929T212738Z.json`.

## Vonis: **GAGAL** - seleksi kami tidak mengalahkan masuk acak

```text
T (terpilih, gerbang BOLEH) : n=195 | 134 token | mean winso  -74,6 | median  -59,0 | umur keputusan median 71 d
K (kontrol ACAK siklus sama) : n= 65 |  49 token | mean winso  -98,0 | median  -62,2 | umur keputusan median 102 d
selisih mean                  +23,4 bps | CI bawah bootstrap 4.000 (seed 20260929) = -215,0 | MW satu arah p=0,2080
siklus tanpa kandidat kontrol   53      | syarat: (1) n>=40 LOLOS | (2) median>0 & CI bawah>0 GAGAL
                                       | (3) p<0,05 GAGAL | (4) umur keputusan sebanding LOLOS
```

## 6b. Yang sebenarnya terjadi: kami tidak kehilangan uang karena pasar, kami membayar ongkos

Median kedua lengan **−59,0** (T) dan **−62,2** (K), sementara ongkos round-trip terukur kami di venue
sendiri adalah **59,0 bps** (`tools/costs.py`). Dibalik: **gross median T = +0,0 bps, K = −3,2 bps.**
Pada horison lima menit, setelah masuk rata-rata 71 detik sesudah whale membeli, harga **hampir tepat
tidak bergerak** - dan yang kami catat sebagai "rugi" sebagian besar adalah **tiket masuk kami sendiri**.

Itu kalimat yang lebih tepat dari "Fabius rugi", dan lebih menghancurkan dari keduanya: tidak ada yang
salah arah, tidak ada yang perlu dibalik - **tidak ada apa pun untuk diambil**, di lengan yang kami
pilih maupun di lengan yang dipilih lemparan undian. Selisih +23,4 bps di antara keduanya pun tidak
bisa dibedakan dari nol (CI bawah −215,0; p=0,208).

## 6c. Yang tidak diizinkan halaman ini

- **Tidak dibalik** menjadi "jual saat whale beli" (fade). Arah terbalik butuh **kunci baru** -
  namanya **E25+** di backlog, bukan kesimpulan dari halaman ini. F-D39 dan F-D51 adalah dua kali kami
  melakukannya tanpa kunci dan berakhir di halaman koreksi.
- **Tidak** menyebut "+23,4 bps" sebagai edge. Ia di bawah 1/2 ongkos round-trip dan CI-nya memotong
  nol dua ratus bps ke kiri.
- **Tidak** menurunkan `n_min` (40), mengganti winsor (±1.500), atau memotong jam kunci: semuanya
  ditetapkan 8 jam sebelum datanya ada, saat n masih **0**.
- **Tidak** menyamakan K dengan "nol": K adalah kontrol siklus yang sama (F-D8), dan di halaman ini K
  bahkan lebih buruk dari T. Kemenangan T atas K tidak akan pernah cukup - yang ditolak syarat (2)
  adalah "median(T) > 0", bukan "T > K".

## 6d. Sisa yang belum terjawab, dan apa artinya untuk klaim masuk

Kontrol acak malam ini dipilih dari **kolam kandidat yang sama** (beli ⑦ berumur ≤120 d). Itu menguji
"apakah gerbang kami menambah apa di atas masuk acak **di kolam itu**" - bukan "apakah ada kolam yang
lebih baik". Yang masih belum diuji dan sudah punya tempat di backlog: **P56** (isolasi titik masuk:
`entry_px` vs `tx_p` vs microprice ⑨ - karena §6b menunjuk biaya sebagai penyumbang utama, dan itu
belum dipisahkan dari horison) dan **P62** (venue: F-D59 menunjukkan venue pembanding lebih hidup,
tapi F-D60 menunjukkan itu pun tidak memanggil bump).

Setelah vonis ini, status pertanyaan "kapan masuk" di proyek ini adalah: **empat jalur diuji
prospektif (E9, watch, E22-rem, E24-masuk), semuanya GAGAL, dan nol alasan masuk tersisa.** Satu-
satunya perilaku yang lulus prospectif tetap aturan **keluar** (E12).

Lihat juga: [[06-Results/26 - Masuk Segar, Terukur Benar]] · [[06-Results/25 - Rem, Terkunci Prospectif]] (E22, rem) · [[08-Backlog/01 - Backlog]] (P55/P56).

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

**KOSONG dengan sengaja.** `tools/entry_ab.py` menolak memvonis sebelum 2026-09-29T21:19:04Z, dan bagian ini tidak
boleh diisi angka sebelum jam itu. Setelah vonis, isinya ditulis sebagai koreksi terlihat - dengan
perintah dan jam artefaknya.

Lihat juga: [[06-Results/26 - Masuk Segar, Terukur Benar]] · [[06-Results/25 - Rem, Terkunci Prospectif]] (E22, rem) · [[08-Backlog/01 - Backlog]] (P55/P56).

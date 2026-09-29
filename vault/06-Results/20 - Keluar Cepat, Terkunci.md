---
tags: [hasil, "pra-registrasi", "E12", "umur-posisi"]
---

# 20 - Keluar Cepat, Terkunci

**Alat:** `tools/hold_ab.py` · **Kunci:** `decisions/prereg-hold-lock.json` · **Job:** rantai ⑦
(menulis `tx` + `wp` terus) · **Bagian dari:** [[06-Results/00 - Hub Results]] ·
[[08-Backlog/02 - Epik Alasan Masuk]] §3e

## 1. Yang sedang di bayar di halaman ini

[[06-Results/19 - Umur Posisi]] (E11) adalah angka positif pertama proyek ini yang lolos placebo.
Ia juga adalah godaan pertama yang sungguh-sungguh: kurva yang naik lalu meluruh itu mudah sekali
dibaca sebagai "Fabius tahu kapan masuk dan kapan keluar", padahal yang diukur adalah data **sampai**
`t_kunci` watch — sampel yang sama yang sudah empat kali mempromosikan dirinya sendiri (F-D30 harga
masuk beku, F-D32 control yang menang karena bentuknya, F-D37 Mann-Whitney salah urut, F-D39 satu
undian disebut hasil, F-D40 kontrol keluar yang salah).

Satu-satunya obat yang kami punya untuk pola itu adalah menulis aturannya sebelum datanya ada.
Kunci ini dipasang **setelah** E11 dilihat dan **sebelum** satu pun pasangan E12 dihitung — itu
artinya dia boleh berbeda dari E11, tapi tidak boleh lagi diubah oleh hasilnya.

## 2. Spesifikasi yang dikunci

```text
E12 - uji terkunci 'keluar cepat' sebagai kebijakan.

arm_kebijakan : keluar pada horison 5 menit setelah kejadian beli kerumunan pintar
arm_kontrol   : horison 30 menit pada POSISI yang sama (bukan nol)
delta         : net(5m) - net(30m), winsor +/-2.000 bps, ongkos 59 bps RT di kedua sisi
harga_masuk   : `wp` terakhir dengan t <= t_kejadian (kanonis E7/E11); varian `tx.p` dilaporkan
                sebagai pemeriksaan, BUKAN sebagai lengan yang boleh dipilih setelah lihat hasil
harga_keluar  : median `wp` pada t+[H-3m, H+3m]; umur median itu dilaporkan apa adanya
perhitungan   : HANYA kejadian dengan t > t_kunci; non-overlap 1 per 30 m per token
vonis_layak   : (1) n >= 20 DAN (2) median > 0 DAN CI bawah bootstrap 4000 (seed 20260928) > 0
                DAN (3) tanda-uji eksak satu arah p < 0,05
                DAN (4) P(ada harga keluar) + umur baris harga keluar dilaporkan untuk dua arm
kalau_kecil   : tulis 'BELUM BISA DIUJI', jangan 'TIDAK ADA EFEK'; ambang tidak diturunkan
kalau_gagal   : horison pendek ditutup sebagai kebijakan; TIDAK dibalik jadi 'tahan lebih lama'
lapor_wajib   : n pasangan, token unik, median & mean winso delta, CI, p, umur harga tiap arm,
                P(ada harga keluar) tiap arm, selisih `wp` vs `tx.p`
eksekusi      : alat ini tidak mengirim order; klaim 'bisa diambil' butuh P40 (jalur < 2 menit)
```

## 3. Kenapa kontrolnya horison 30 menit, bukan nol

Di pool yang mean-nya **−183,7 bps** (E7), apa pun yang "melawan nol" akan terlihat hebat. F-D16
sudah pernah menangkap kami karena itu, jadi arm pembandingnya adalah **kebiasaan lama kami sendiri
pada posisi yang sama**: tahan sampai 30 menit. Kalau keluar 5 menit tidak mengalahkan itu, tidak ada
yang berubah dan tidak ada yang boleh ditulis.

Dan kalau menang: yang menang adalah **kebijakan umur**, bukan kemampuan membaca arah. E11 sudah
menunjukkan bahwa menunda masuk **2 menit** saja membuat median@5m jadi **−56,2** — jadi klaim
"bisa diambil" tetap butuh P40 (jalur sinyal→order di bawah dua menit), dan itu pekerjaan
infrastruktur, bukan pekerjaan halaman ini.

## 4. Cara menjalankan

```bash
python -X utf8 tools/hold_ab.py --self-test   # 4 kasus: prefill dibuang, datar != layak,
                                              # arah buruk = GAGAL, syarat lapor umur dinilai
python -X utf8 tools/hold_ab.py --lock        # pasang kunci SEKALI (menolak dobel)
python -X utf8 tools/hold_ab.py --status      # umur kunci + berapa pasangan pasca-kunci
python -X utf8 tools/hold_ab.py               # vonis (menolak cetak angka sebelum matang)
python -X utf8 tools/hold_ab.py --tanpa-umur  # bacaan sementara, dicetak dengan LABEL PERINGATAN
```

Syarat umur **12 jam** dari pemasangan kunci. Kalau saat matang `n < 20`: vonisnya tertulis
**"BELUM BISA DIUJI"** — ambang tidak boleh diturunkan, dan itu bukan "tidak ada efek"
([[Concepts/Unmeasured Is Not Clean]]).

## 5. Hasil

**Dibaca 29 Sep 2026 20:11:20Z** oleh `python -X utf8 tools/hold_ab.py` (umur kunci **12,11 jam** dari
kebutuhan 12; `spec_sha256=0x7f4e12fd9202e7a4…` — blok §2 tidak kusentuh). Artefak:
`decisions/hold-ab-20260929T201120Z.json`.

**Vonis: LAYAK** — keluar pada menit ke-5 mengalahkan menahan sampai menit ke-30 pada POSISI yang sama,
dengan **empat dari empat syarat** terpenuhi.

```text
n pasangan PASCA-KUNCI      685  (prefill sebelum kunci dibuang: 701 - tidak ikut hitung)
median delta (5m - 30m)      +15,3 bps
mean winso delta            +215,8 bps   CI bootstrap 4.000 [+135,9 ; +301,2]  -> CI bawah > 0
tanda-uji (pasangan)        menang 363 | kalah 256            p = 0,00001
mean lengan cepat              +8,1 bps   (setelah ongkos round-trip 59 bps)
mean lengan lambat            −195,0 bps
umur harga keluar              arm 5 m: +0,08 m | arm 30 m: −0,03 m   -> kedua lengan dinilai PADA
                              waktunya, bukan dari baris basi (syarat 4)
P(ada harga keluar)           95,7 %      token berbeda: 336
```

## 6. Yang dimenangkan, dan yang tidak

**Yang dimenangkan:** pembusukan. E11 mengukur kurva decay secara retrospektif (mean +192,7 @2 m →
+202,6 @5 m → **−182,5 @30 m**); E12 mengonfirmasi sisi 30 menit-nya **secara prospectif pada kejadian
yang belum pernah kami lihat** — lengan lambat berakhir **−195,0 bps**. Artinya keputusan "keluar di
menit ke-5" bukan preferensi gaya, itu menolak memegang sesuatu yang sudah terbukti membusuk.

**Yang TIDAK dimenangkan:** uang. Mean lengan cepat **+8,1 bps** — nyaris nol, dan di bawah ambang
keputusan kami (`tools/costs.py:gate_gross_bps()` = **118 bps**). Median delta **+15,3 bps** juga tipis;
kemenangannya datang dari **ekor**, bukan dari tengah: 363 posisi menghindari longsor 30 menit, 256
membayar lebih. Jadi kalimat yang benar: *keluar cepat menghentikan pendarahan* — bukan *keluar cepat
menghasilkan*.

**Yang paling berharga di artefak ini justru bukan vonisnya.** Ada dua baris yang selama ini cuma
kuduga:

```text
net_cepat_dari_tx_mean  +192,9 bps   keluar di menit 5, masuk di HARGA TRANSAKSI whale
net_cepat_mean            +8,1 bps   keluar di menit 5, masuk di HARGA TIKER kami saat kejadian
                                       selisih: 184,8 bps
```

Kedua lengan memakai `p0` yang sama (`tools/hold_ab.py:173` - baris harga terakhir sebelum kejadian),
jadi selisih ini **bukan** latensi keputusan kami (itu F-D54, sudah dibetulkan ke 61 d) — ini jurang
**sumber harga**: apa yang dicetak tikermu terhadap apa yang benar-benar dieksekusi pasar. E21 mengukur
bentuk yang sama sebagai `i` (median **+245 bps** saat level terlewat di antara dua rekaman); E12 kini
mengukurnya pada **685 pasangan prospectif**, rata-rata **184,8 bps**. Angka itu lebih besar dari
seluruh hasil yang menang di halaman ini.

**Yang tidak diizinkan halaman ini:**
- bukan alasan masuk — entry-nya identik di dua lengan, jadi yang diuji adalah *keluar*;
- jangan balik arahnya: "tahan 30 m menang" tidak ada di data mana pun di repo ini, dan E11/§13
  (One-Way Gate) melarang pembacaan terbalik dari uji yang gagal maupun yang lulus;
- jangan jadikan cakupan tak terlihat: dari **14.444** kejadian pasca-kunci, **11.056 tidak punya deret
  harga** sama sekali — 685 yang dinilai itu **4,7 %**. Ini tembok venue (F-D43/F-D56) yang menyapa
  lagi di vonis;
- dan jangan tulis "Fabius profit di paper": `promote-after` masih kosong, dan §F-D62 barusan
  menunjukkan 6 dari 20 posisi paper bahkan tidak punya pool untuk diisi.

**Terkait:** [[06-Results/19 - Umur Posisi]] §4a · [[06-Results/26 - Masuk Segar, Terukur Benar]] §4
(jurang titik masuk, versi prospectif) · [[06-Results/21 - Rem di Horison Cepat]] ·
[[06-Results/24 - Trailing pada Bar yang Salah]] · [[Concepts/One-Way Gate]] · F-D41, F-D54, F-D62.

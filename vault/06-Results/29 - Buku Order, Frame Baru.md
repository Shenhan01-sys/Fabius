---
tags: [hasil, "pra-registrasi", "E25", "buku-order", "non-overlap"]
---

# 29 - Buku Order, Frame Baru (E25)

**Bagian dari:** [[06-Results/00 - Hub Results]] · [[06-Results/22 - Buku Order, Terkunci Lebih Dulu]] ·
[[08-Backlog/03 - Epik Teori Baru]] (T1) · [[08-Backlog/01 - Backlog]] (P54, P66)
**Alat:** `tools/book_prereg.py --kunci-nama E25` · **Kunci:** `decisions/prereg-book2-lock.json`

## 1. Kenapa ini ujian baru, bukan E16 yang dibaca ulang

E16 jatuh 29 Sep 21:46:56Z pada 25 simbol. F-D53 melarang frame-nya diubah di tengah jendela - jadi
pelebaran daftar pantau ⑨ **tidak boleh** dipakai untuk mengampuni atau membatalkan E16. Yang dilakukan
sebagai gantinya: ujian BARU, kunci BARU, sha BARU, di berkas kunci yang sendiri
(`prereg-book2-lock.json`; `prereg-book-lock.json` milik E16 tidak disentuh - `--lock` menolak
menimpa dan itu keluar dengan kode bukan nol).

Dua hal yang membedakan E25 dari E16, keduanya ditulis sebelum kuncinya dipasang:

1. **Frame.** `universe/book-venue.txt` diperluas 22:2xZ ke **40 simbol kabar teratas** dari irisan
   (kabar ⑦ × venue perp - terukur **102 simbol irisan** malam ini), plus 3 jangkar yang selalu
   direkam perekam. Validasi ke `exchangeInfo`: **43 dikenal, 0 dibuang**.
2. **Jendela non-overlap (P66).** Jarak antar-snapshot dalam satu simbol terukur **median 244 d**
   pada horison 300 d → 99,7 % pasangan E16 beririsan (n efektif ~3.460, bukan 4.255). E25 hanya
   mengambil snapshot yang berjarak ≥ horison dari snapshot terpilih terakhir.

## 2. Spesifikasi yang dikunci

```text
E25 - buku order sebagai prediktor, atas frame yang diperluas DAN jendela non-overlap.

sumber_teori  : builder (29 Sep), dari trader yang dia hormati: 'total variasi harga beli - jual'
warisan       : E16 GAGAL 29 Sep 21:46:56Z pada 25 simbol (bi5 selisih -0,72 bps, p=0,060; BH alpha
                0,10 nol lulus). Keputusan F-D53 melarang frame E16 diubah di tengah jendelanya, jadi
                pelebaran itu menjadi UJIAN BARU dengan kunci sendiri - bukan E16 yang dibaca ulang.
perubahan_dari_E16 : (1) frame: daftar pantau ⑩ diperluas ke 40 simbol kabar teratas (irisan ⑦ x venue,
                         diukur 22:2xZ: 102 simbol irisan) + 3 jangkar yang selalu direkam perekam;
                     (2) jendela non-overlap (P66, ditulis SEBELUM kunci dipasang): jarak antar
                         snapshot dalam satu simbol terukur median 244 d pada horison 300 d, sehingga
                         99,7 % pasangan E16 beririsan (deflasi n efektif ~1,23x). E25 hanya
                         mengambil snapshot yang berjarak >= horison dari snapshot terpilih terakhir.
hipotesis_primer : kuantil-atas `bi5` (imbalance kuantitas 5 level) menghasilkan return-ahead
                   5 menit lebih tinggi dari kuantil-bawah, pada simbol yang sama
hipotesis_sekunder : bi1, bi20, mi20, util20 - masing-masing diuji, Benjamini-Hochberg alpha 0,10
return_ahead  : 10000 * (mid(t+300s) - mid(t)) / mid(t), mid dari snapshot berikutnya yang
                |t' - t - 300s| <= 150s; kalau tidak ada -> TIDAK DIHITUNG, bukan nol
biaya         : dikurangi setengah spread (bps) pada snapshot t - syarat (4) vonis adalah
                net-of-cost, bukan gross
perhitungan   : HANYA snapshot dengan detik > t_kunci; jangkar likuid (BTC/ETH/SOL) dilaporkan
                TERPISAH dari simbol kabar - menggabungkannya akan menyembunyikan bentuknya
vonis_layak   : (1) n >= 40 DAN (2) median > 0 DAN CI bawah bootstrap 4000 (seed 20260929) > 0
                DAN (3) Mann-Whitney satu arah atas-vs-bawah p < 0,05 DAN (4) mean net-of-cost > 0
kalau_kecil   : 'BELUM BISA DIUJI' - ambang tidak diturunkan, horison tidak diperpanjang diam-diam
kalau_gagal   : buku order ditutup sebagai jalur prediksi pada cadence kami, untuk kedua kalinya,
                dan pada frame yang lebih luas; TIDAK dibalik jadi 'contra-imbalance' tanpa kunci baru
kalau_layak   : yang boleh dikatakan adalah 'imbalance memprediksi pada cadence 5 menit di frame 40
                simbol' - BUKAN 'Fabius bisa trading': E24 menunjukkan masuk kita tidak di atas acak,
                dan E12 tetap satu-satunya perilaku yang lulus prospectif
cadence_batas : ~244 s/simbol terukur; E11 mengukur kabar hidup +-2 menit, jadi uji ini tetap tidak
                bisa memalsukan versi CEPAT dari teori - hanya versi lambatnya
```

## 3. Empat syarat, dan apa yang boleh dikatakan kalau lolos

Syarat vonis identik dengan E16 (n≥40; median > 0 dan CI bawah bootstrap 4.000 > 0; Mann-Whitney satu
arah p < 0,05; **mean net-of-cost > 0**), plus kewajiban melaporkan **komposisi pasangan** dan
**jangkar terpisah dari simbol kabar** - clauses yang justru menyelamatkan pembacaan E16, karena tanpanya
"selisih −0,72" akan tampak seperti teori yang mati, padahal isinya: jangkar **+1,45 (net +0,03)** dan
simbol kabar **−0,95**.

Kalau **LAYAK**, kalimat yang diizinkan hanya sampai *"imbalance memprediksi pada cadence 5 menit di
frame 40 simbol"*. Yang TIDAK boleh: menyebutnya alasan masuk - E24 sudah menunjukkan seleksi kami tidak
di atas masuk acak (median −59,0 vs −62,2; p=0,208), dan **E12 tetap satu-satunya perilaku yang lulus
prospectif**.

Kalau **GAGAL** untuk kedua kalinya, buku order ditutup sebagai jalur prediksi pada cadence kami - dan
tetap **tidak** dibalik jadi "contra-imbalance": itu hipotesis baru dengan kunci dan n sendiri.

## 4. Isi bagian ini

**KOSONG dengan sengaja, dan dengan alasan yang tercatat.** Kunci dipasang 22:29:37Z, syarat umur 12 jam baru jatuh **30 Sep 2026 10:29:37Z**.

**Hitungan waktu, dikoreksi sebelum sempat salah beredar.** Kunci dipasang **22:29:37Z** + syarat
12 jam = **30 Sep 10:29:37Z = 17:29 WIB**, sementara tenggat proyek **30 Sep 23:59 WIB = 16:59Z**.
Jadi E25 **sempat matang**, dengan longgar ~6,5 jam - bukan "kemungkinan besar tidak akan sempat",
yang tadi kutulis dengan mengira 12 jam dihitung dari jam lokal. Kalkulasi yang salah soal *waktu*
sama berbahayanya dengan kalkulasi yang salah soal *angka*: keduanya membuat keputusan lingkup
diambil karena alasan yang tidak ada.

Alatnya (`tools/book_prereg.py --kunci-nama E25`) menolak memvonis sebelum jamnya dan menolak jalan
kalau sha spec tidak cocok dengan teks di halaman ini. Timer durable dipasang untuk 17:37 WIB
30 Sep. Kalau sampai gagal jalan, bagian ini ditinggal kosong dan alasannya ditulis di halaman ini
juga - bukan diisi angka dari jendela yang belum matang.

Lihat juga: [[06-Results/22 - Buku Order, Terkunci Lebih Dulu]] §6 ·
[[06-Results/27 - Masuk Terpilih vs Masuk Acak]] §6 · [[03-Sinyal/Volume/V4 - Order Book dan Liquidity Heatmap]] · `00-Overview/03 - Decisions.md` F-D53, F-D66, F-D68.

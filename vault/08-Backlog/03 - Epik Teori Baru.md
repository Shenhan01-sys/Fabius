---
tags: [backlog, epik, "teori-baru", buku-order, flow, exit]
---

# 03 - Epik Teori Baru (Buku Order, Flow, Exit Dinamis)

**Dibuka:** 29 Sep 2026 ±09:40Z oleh permintaan builder: *"cari teori seperti ini minimal 4 -
brainstorm dan deep research, pasang backlog besar ini ke vault"*.
**Aturan main epik ini** (diambil dari empat hari pencabutan): **tidak ada satu pun teori di sini
yang boleh disebut temuan sebelum (a) placebonya ada di alat yang sama, (b) satuannya diaudit,
(c) ambangnya lewat grid, dan (d) kontrolnya bukan nol** - F-D30, F-D32, F-D37, F-D39, F-D40,
F-D43, F-D46 adalah tujuh kali kami melanggar versi berbeda dari aturan ini dan selalu angkanya
terlihat bagus sebelum ketahuan.

## 1. Teori builder, dibedah jadi dua yang bisa diuji

> "Baca order book-nya, buy/sell, lalu total variasi harga yang ada. Buy dikurangi sell: positif →
> mantul naik; negatif → whale/smart money kemungkinan ikut jual karena posisinya tidak kuat
> mengangkat harga. TP/SL dinamis; SL pakai trailing stop, pokoknya jangan sampai rugi, dan
> jarak trailing sudah dihitung dengan spread + fee supaya tetap untung."

Dua klaim terpisah, dan hanya satu yang ambigu: **"total variasi harga" tidak punya definisi
kanonis** - lima pembacaan yang berbeda arah sudah dicatat perekam ⑨ sebelum satu pun hipotesis
dijalankan (bukti: `ETHUSDT bi1 −0,651 / bi20 +0,525` - imbalance berganti tanda menurut kedalaman).
Maka T1 mengikat satu pembacaan sebagai primer *sebelum* ada data, dan sisanya sekunder dengan BH.

## 2. Tujuh teori, status data, dan cara membunuhnya

| # | teori (bentuk yang bisa difalsifikasi) | data yang dibutuhkan | punya kita? | uji yang dirancang | apa yang akan membunuhnya |
|---|---|---|---|---|---|
| **T1** | imbalance buku (kuantitas 5 level) > median → return-ahead 5 m lebih tinggi, **net of setengah spread** | L2 snapshot periodik simbol venue | **baru dipasang 29 Sep 09:1xZ**, riwayat = 5 snapshot | **E16** `tools/book_prereg.py` (terkunci 09:37:45Z, vonis 21:37Z); kontrol = kuantil-bawah pada simbol & jam yang sama | cadence 200 detik kami lebih lambat daripada horison tempat efek ini hidup; spread > selisih; `bi1` vs `bi20` berlawanan arah |
| **T2** | trailing stop yang mengunci PnL > 0 setelah fee+spread menaikkan PnL *dan* tidak merusak harapan | tick harga + biaya | **ada** (`wp` ticker, ongkos 59 bps RT) | **E17** (belum ditulis): simulasi exit pada **posisi yang sama**, kontrol = keluar di waktu **acak** pada jendela yang sama (F-D40), placebo = shift jam | kalau net-nya tidak lebih baik dari keluar-acak, ini bukan sinyal, cuma memotong umur posisi |
| **T3** | signed volume imbalance dari **transaksi** (bukan buku): rasio berimbang (beli − jual)/(beli + jual) dan bucket VPIN-style → forward return | ⑦ trade rows | **ada, 51.669 baris** | **SUDAH DIUJI 29 Sep 09:45Z** - `tools/flow_variasi.py`, 396 kejadian, 5 pembacaan, outcome `wp` @2/5/30 m, ongkos 59 bps: selisih kuantil atas-bawah di menit ke-5 **−41,4 / −15,0 / +9,6 / −24,8 / −14,9 bps**, semuanya **di dalam placebo dua ekor** (p2 0,75-0,93), BH alpha 0,10 **KOSONG** | hasilnya nol, dan yang lebih berguna: sebar antar-pembagian **±200-470 bps** - sekitar 10x efek yang sedang dicari. Run pertama menghasilkan arah *terbalik dari teori* yang lalu hilang antar-eksekusi: itu shuffle pembagian, bukan sinyal. Karena itu alatnya sekarang melaporkan distribusi 40 pembagian, bukan satu undian (F-D39), dan placebo dijaga di dua ekor (versi pertama cuma menjaga ekor atas, jadi selisih negatif terbaca "aman"). **Tidak dibalik jadi aturan fade** - halaman 12 dan 22 menutup dua arah |
| **T4** | spread + kedalaman sebagai **keranjang buang**, bukan sinyal: simbol dengan setengah spread > anggaran tidak boleh dibuka posisinya | `book-depth` / `bookTicker` per simbol | **mulai direkam** (5 simbol, n 1-2 per simbol) | 🟡 `tools/cost_budget.py` sudah jalan: ambang spread ≈ **21 bps** di horison 5 menit (melawan median +79,8 bps); run pertama 5/5 lolos karena yang direkam baru jangkar likuid - jadi jawabannya **belum** tentang simbol kabar | kalau hanya jangkar likuid yang lolos, "timeframe" kami sebenarnya pertanyaan "di pasar mana"; dan ambang 21 bps itu batas, bukan target: ia tidak membuat simbol lebar jadi untung |
| **T5** | microprice (mid tertimbang quote) > mid biasa sebagai prediktor jangka sangat pendek | L2 + timestamp sub-menit | **tidak punya resolusi** | tidak diuji; dicatat sebagai "butuh streaming" | tidak ada yang membunuh: memang belum bisa diukur. Menuliskannya sebagai "belum" adalah satu-satunya bentuk jujur |
| **T6** | slope kedalaman (likuiditas per jarak harga) memprediksi besarnya price impact order kita | L2 multi-level | direkam sekarang (20 level) | **E20**: cocokkan order-size aktual vs pergeseran mid berikutnya; hasilnya dipakai mengoreksi `haircut` (P42/F-D46) | x·y=k dengan `liq` $1 di desil terbawah sudah terbukti jadi sampah; kalau kurva kalibrasi tidak monoton, model dampangnya yang salah |
| **T7** | funding/OI basis & likuidasi berantai sebagai penanda arah di venue kami | kline + funding perp | ada sebagian (②) | di luar epik ini - sudah punya jalur sendiri | - |

## 3. Aritmetika trailing stop lebih dulu (ini yang membatasi klaim T2)

Builder: "SL pakai trailing, pokoknya jangan sampai rugi, jaraknya sudah hitung spread + fee supaya
tetap untung". Tulis sebagai matematika, dengan angka kami sendiri:

```
  C     = ongkos penuh satu round-trip = 59,0 bps TERUKUR (fee+gas+slip, `tools/costs.py`)
          + spread penuh dua kaki (= satu spread; run pertama 0,01-7,77 bps di jangkar likuid,
            dan simbol kabar belum terukur - E19)
  M     = kenaikan maksimum harga sejak masuk, bps di atas harga masuk
  d     = jarak trailing dari puncak, bps
  PnL   = (M - d) - C   kalau pemicu terisi di harga trigger
  lock  = PnL >= 0  <=>  M >= C + d
```

Tiga konsekuensi yang tidak bisa dinegosiasi aritmatika:

1. **"Jangan sampai rugi" bukan keadaan yang bisa dijamin sejak awal.** Ia baru mulai mungkin
   setelah harga sudah naik **lebih besar dari C + d**. Sebelum titik itu, trailing stop hanya
   memotong kerugian - dan kalau C = 60-80 bps sementara pergerakan 5 menit simbol kami biasa
   berada di dalam rentang itu, mayoritas posisi tidak pernah masuk zona terkunci sama sekali.
2. **Yang dikunci bukan angka yang tertulis di trigger.** Trigger dieksekusi di bid, dan harga
   bergerak *menembus* level itu: selisih antara "menyentuh" dan "terisi" tidak ada di
   rumus di atas. Pada cadence ⑨ (snapshot ~200 detik) kami bahkan tidak bisa melihat apa yang
   terjadi di antara dua snapshot - jadi "pokoknya jangan rugi" persis hilang di tempat yang
   paling kami tidak lihat.
3. **Trailing stop mengubah BENTUK distribusi, bukan arah drift.** Ini pelajaran yang sudah kami
   bayar di tempat lain (F-D30/E2): **median boleh naik dan "persen positif" membaik sementara
   harapan tetap diam**, karena yang dipotong adalah ekor kiri. Kalau E17 menemukan itu, klaimnya
   adalah **"mengurangi buntut buruk"** - sebuah hipotesis baru dengan kuncinya sendiri - bukan
   "ada edge".

Karena itu desain E17 (belum ditulis) dipaksa begini:
* **satu populasi posisi yang sama** (bukan dua cohort), dieksekusi pada `wp` tick,
* lengan = trailing dengan beberapa `d` (mis. 30/60/120/250 bps) dan **kunci-penguncian hanya aktif
  setelah M ≥ C + d**,
* kontrol = **keluar di waktu acak pada jendela yang sama** (F-D40: "lebih cepat keluar" bukan
  sinyal), bukan "tahan sampai horison",
* vonis utama = **mean dengan bootstrap CI vs kontrol**, dilaporkan winsor DAN tanpa-winsor,
  plus `P(net ≤ -200 bps)` sebelum/sesudah sebagai bukti mekanisme, plus P(≥+500),
* ambang hidup = di atas CI **kontrol**, bukan di atas nol, dan tidak ada angka yang boleh dijual
  sebelum lewat placebo dua ekor + grid `d` (F-D45).

## 4. Yang harus terjadi sebelum teori mana pun boleh dijual

1. **Histori ⑨** terkumpul dulu (target: ≥ 8 jam snapshot sebelum E16divoniskan; alatnya menolak
   sebelum 12 jam dan menolak `n < 40`).
2. **E17 (trailing)** tidak boleh dibandingkan dengan "tahan sampai horison" - pelajaran F-D40:
   kontrolnya wajib keluar di waktu acak pada jendela yang sama.
3. **Satuan dampak dibereskan lebih dulu (P42)** - kalau tidak, T2/Bab ini akan mengevaluasi
   "net of biaya" dengan biaya yang salah ±600x (F-D46).
4. **Arah yang lolos placebo wajib lewat grid ambang** sebelum disebut perilaku (T1 punya lima
   pembacaan; T2 punya jarak trailing yang bisa digeser).
5. **Venue dulu, sinyal kemudian.** T1/T2/T4 hidup di 61-90 simbol yang bisa kami pegang (F-D43).
   Teori sekuat apa pun di 2.163 token yang tidak bisa kami perdagangkan tetap bukan PnL.

## 5. Riset pendukung

Empat agen riset paralel dijalankan 29 Sep 09:3xZ (order book imbalance; microprice & queue;
VPIN/order-flow/toxicity; matematika stop-loss & trailing). Hasilnya ditulis di
[[08-Backlog/04 - Riset Teori (Sitasi)]] dengan aturan: **hanya sumber yang benar-benar dibaca,
URL + tanggal akses untuk setiap angka, dan "tidak terverifikasi" eksplisit untuk sisanya.**

## 6. Terkait

[[06-Results/22 - Buku Order, Terkunci Lebih Dulu]] · [[06-Results/19 - Umur Posisi]] ·
[[06-Results/21 - Rem di Horison Cepat]] · [[08-Backlog/02 - Epik Alasan Masuk]] ·
[[08-Backlog/01 - Backlog]] P43-P48 · [[Concepts/Unmeasured Is Not Clean]] ·
[[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]]

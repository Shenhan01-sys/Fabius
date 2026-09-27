---
tags: [tk, tk-quant, "QT11"]
---

# QT11 - Portofolio Strategi

**Keluarga:** [[00 - Hub Quant]] · **Tahap:** keputusan ([[PL4 - Memutuskan]])
**Sumber:** `vault/TradingKnowledge/QuantTrading/Info1.txt` §"Kelebihan & Kekurangan" /
§"Quant vs Discretionary" (daftar topik) · rotasi kursi: [[01-Agent/01 - Asset Classes and Seats]] ·
[[Fakta Terukur]] §D/§E/§F

**Ringkas:** gagasan portofolio strategi adalah: beberapa aturan yang **tidak** bergerak bersama
lebih baik daripada satu aturan yang kencang, karena kerugian satu aturan ditutup yang lain dan
kurva hasil jadi lebih halus tanpa menambah keberuntungan. Gagasannya sah. Yang membuatnya menjadi
ukuran, bukan semangat: korelasi antar-aturan bisa diukur, dan keputusan mematikan sebuah aturan
harus ditetapkan **sebelum** aturan itu mati. Di Fabius hari ini portofolio itu berisi satu aturan
yang diuji (dan kalah) plus kandidat yang belum diuji sama sekali.

## Definisi yang bisa dihitung

```
korilasi_portofolio := korelasi antar-aturan pada return per periode yang sama
alokasi_risiko_i    := budget_risiko_i / sum(budget_risiko)     # bukan alokasi notional
matikan_aturan_i    := aturan(pengamatan yang sudah didefinisikan di muka) -> kursi dilepas
```

Yang membuat sebuah portofolio lebih dari sekadar banyak posisi:

| syarat | cara memeriksanya | kegagalan yang umum |
|---|---|---|
| korelasi rendah **terukur**, bukan terasa | return per aturan pada periode yang sama | semua aturan membaca bar yang sama → satu ide dihitung empat kali |
| risiko dialokasikan, bukan notional | tiap aturan punya batas kerugian yang bisa dijumlahkan | ukuran posisi seragam pada aset dengan volatilitas berbeda orden ([[FD8 - Volatilitas]]) |
| aturan mati punya definisi | ambang + jumlah sampel ditetapkan di muka | "tunggu satu trade lagi" selamanya, atau pecat karena satu kerugian |
| sumber data berbeda | deret, on-chain, narasi datang dari jalur yang tidak saling menjatuhkan | satu vendor mati = seluruh portofolio buta |

## Cara pakai yang diklaim

Klaim pemilik praktik (manajemen dana multi-strategi; di `Info1.txt` disebut sebagai
"portfolio of strategies" dan "hybrid"): menggabungkan banyak aturan menurunkan varians tanpa
menurunkan expected return, dan proses yang lebih penting daripada strategi adalah **memutuskan
kapan sebuah edge dianggap mati**. Yang kedua itu tepat; yang pertama bergantung pada korelasi yang
harus diukur, dan kami belum pernah mengukur korelasi antar-aturan apa pun *(belum diukur)*.

Yang tertulis di repo untuk bentuk ini: dokumen kursi (`[[01-Agent/01 - Asset Classes and Seats]]`)
— maks **5 kursi**, kursi dilepas kalau hasilnya jelek lalu diisi kandidat lain. Ambang rotasinya
diambil dari korpus proyek rujukan (bukan hasil ukur Fabius): nilainya **belum diukur untuk produk
ini**, dan kodenya (`seats.py`) **belum ada**. Jadi struktur portofolionya berupa spesifikasi, bukan
peralatan.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| return per aturan pada periode yang sama | `ADA-TAPI` | satu aturan punya jalur uji (`tools/backtest.py`); yang lain belum diuji → tidak ada matriks korelasi yang bisa dihitung |
| dua deret dari venue berbeda sebagai kontrol rezim | `ADA` | Aster 9.599 bar vs Hyperliquid 5.001 bar (§A) — chain berbeda, bukan portofolio |
| aliran on-chain sebagai sumber yang benar-benar berbeda | `ADA-TAPI` | bidang ⑦ point-in-time, jendela 8–13 menit, tanpa riwayat (§B) |
| budget risiko per kursi yang bisa dijumlahkan | `ADA-TAPI` | `maxPositionQuote` 1 unit, `dailyCap` 5 unit, `HARD_CEILING = 10` (§E) membatasi **satu** akun; belum ada aturan alokasi antar-aturan |
| riwayat keputusan jatuh tempo dalam jumlah | `ADA-TAPI` | gerbang F-D16 minta `n >= 20`; terukur masih jauh di bawah itu (§E/§F) |

## Uji di Fabius

Cara menguji ide portofolio dengan bahan yang ada, tanpa alat baru: jalankan dua aturan pada deret
yang sama, lalu bandingkan **return per segmen waktu** (bukan return total). Kalau keduanya positif
di segmen yang sama, itu satu taruhan dengan dua nama. Uji yang sah butuh:

1. tiap anggota diuji sendiri dengan gerbang §E (`n >= 20` non-overlap, net > 0 setelah ongkos,
   tetap positif setelah fold terbaik dibuang, BH α 0,10, dihitung di luar sampel);
2. aturan mati **ditulis sebelum** ia dipakai — termasuk berapa sampel yang dibutuhkan sebelum
   seorang boleh menyimpulkan sebuah aturan memburuk;
3. laporan selalu menyebut korelasi, karena klaim "diversifikasi" tanpa angka korelasi adalah hiasan.

## Batas dan mode gagal

- **Diversifikasi semu.** Tiga aturan yang semuanya turunan dari satu deret bar (I/ST di lapisan
  sinyal kami) bukan tiga sumber keuntungan.
- **Portofolio dari hasil negatif bukan lindung nilai.** §F menunjukkan dua pertanyaan dari arah
  berbeda dijawab sama: aturan harga rugi di 12/12 setelah ongkos, dan panel dompet berlabel menang
  69,8 % namun tetap **−10,4 bps** terhadap kerumunan. Menggabungkan dua hal yang tidak bekerja tidak
  menghasilkan portofolio.
- **Edge decay yang tidak terdefinisi** = aturan dibuang berdasarkan suasana hati. Obatnya satu:
  ambang + sampel ditetapkan di muka ([[FD11 - Aturan Mengalahkan Intuisi]]).
- **Rotasi kursi memperbanyak tes.** Lima kursi × beberapa aturan = N_eff yang naik
  ([[QT4 - Overfitting dan Validasi]]) dan koreksi BH harus ikut naik, bukan per-aturan saja.
- **Satu venue, satu nasib.** Semua angka kami berdiri di satu deret harga (§A); kegagalan sumber
  data adalah risiko portofolio, bukan risiko operasional.

## Tingkat bukti

`T1` untuk gagasan diversifikasi aturan dan alokasi risiko (pengetahuan standar) · `T3` nihil untuk
portofolio: yang diukur di §F adalah **satu** aturan, bukan kombinasi · `T0` untuk kalimat mana pun
yang menyebut "keranjang strategi Fabius".

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius punya desain multi-kursi dengan plafon risiko per posisi, tapi baru satu aturan
  yang diuji; portofolio strategi belum ada karena korelasi antar-aturan belum pernah dihitung."
- **Dilarang:** "kami menjalankan beberapa strategi sekaligus" · "diversifikasi menurunkan risiko
  kami" · "kursi dirotasi oleh kode" (`seats.py` belum ada) · "lima kursi = lima taruhan bebas".

**Terkait:** [[QT1 - Dari Ide ke Strategi yang Bisa Diuji]] · [[QT4 - Overfitting dan Validasi]] ·
[[FD6 - Ukuran Posisi]] · [[FD10 - Korelasi dan Risiko Keranjang]] · [[ST1 - All-Rounder]] ·
[[01-Agent/01 - Asset Classes and Seats]]

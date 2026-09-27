---
tags: [tk, tk-sinyal, "O7"]
---

# O7 - Token Unlock dan Vesting

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Strategi Berbasis On-Chain & Data Crypto Spesifik"
(baris "Token Unlock / Vesting Schedule trading") — daftar topik, bukan fakta; status Fabius dari
[[Fakta Terukur]] §C

**Ringkas:** jadwal kapan pasokan yang dikunci boleh berpindah. Versi naiknya: unlock = tekanan jual.
Versi yang benar lebih tajam: **hari kalender yang diketahui publik** mengubah perilaku sebelum
harinya tiba — penerima meminjam untuk melindungi nilai, penjual cepat membeli spot untuk keperluan
lain, dan likuiditas sering menyempit tepat di jam itu. Karena itu metrik ini adalah metrik
**ekspektasi**, dan ekspektasi hanya bisa diperdagangkan kalau jadwalnya diketahui **sebelum**
peristiwanya — sesuatu yang tidak kami punya.

## Definisi yang bisa dihitung

```
float(t)              = pasokan yang boleh berpindah pada t (bukan total, bukan max)
unlock(t; t0, cliff, lin, T) = 0 untuk t < t0+cliff
                            = lin × (t − (t0+cliff)) / (T − t0 − cliff) untuk di antaranya
Δfloat(t)             = float(t) − float(t−1)                 # laju pasokan baru, per jendela
supply_used_rasio     = market_cap / float(t)                 # dibanding total: menyesatkan
```

Tiga pasokan yang wajib dibedakan dan sering dicampur: **circulating/float**, **total**, **max**.
Yang bergerak pada sebuah unlock adalah float; kapitalisasi yang dibagi total membuat token dengan
80 % pasokan terkunci terlihat "murah".

## Cara pakai yang diklaim

Diklaim oleh praktisi tokenomics dan situs jadwal (kalender unlock): jual menjelang tanggal cliff,
atau short lewat perp karena peminjam akan menekan harga lebih dulu; kadang dijual sebagai "katalis
berjadwal dengan probabilitas". Horizon klaim = harian sampai mingguan, dengan entry H-1/H-3 hari.
Pemilik klaim tidak mempublikasikan basis statistiknya (berapa banyak peristiwa, sekuat apa besaran
efeknya, di aset apa) — jadi kami mencatatnya sebagai klaim, bukan hasil.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| jadwal unlock/vesting per token | `TIDAK-ADA` | §C: "jadwal unlock/vesting" tidak kami punya; tidak ada satu pun `tools/` yang menyentuhnya |
| kontrak vesting on-chain yang bisa dibaca | `TIDAK-ADA` | butuh alamat kontrak vesting + cara membedakannya dari kontrak lain; belum ada jalurnya |
| tanggal peristiwa untuk kandidat arah | `TIDAK-ADA` | `tools/direction.py` tidak punya konsep jadwal sama sekali |
| harga forward untuk menguji reaksi | `ADA` | Aster 9.599 bar ≈ 400 hari; Hyperliquid 5.001 bar (§A) — **hanya** untuk yang ber-kontrak perp |
| riwayat untuk token muda | `ADA-TAPI` | GMGN mentok 1.000 bar ≈ 41,6 hari dan **0 bar untuk token gas**; pool baru GeckoTerminal ±30 bar (§A) |

Di [[01-Agent/01 - Asset Classes and Seats]] hal ini sudah ditandai pada kelas B (blue-chip/L1/DeFi):
sumbernya **belum ada**, dan "dump unlock" ditulis sebagai salah satu cara kelas itu mati — bukan
sebagai sesuatu yang kami pantau.

## Uji di Fabius

Perintahnya **belum ditulis**, dan tidak bisa ditulis tanpa jadwal. Bentuk yang sah nanti:

1. Event study: untuk tiap tanggal unlock yang **tercatat sebelum** tanggal itu (point-in-time,
   [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]), hitung return bersih pada
   H-3d..H+3d dari bar kami sendiri.
2. Kontrol: **token & jam acak yang sama** di universe yang sama (§B), bukan "hari tanpa unlock" —
   kalau tidak, yang diukur cuma rezim pasar.
3. Satu sampel per (token, peristiwa), `n >= 20` peristiwa non-overlap, BH α 0,10 lintas aset
   **dan** lintas jendela (jendela ganda = uji ganda), gross di atas **59 bps** (§D), fold terbaik
   dibuang.
4. Lapor **reaksi**, bukan "tekanan jual": arah, median, dan berapa banyak peristiwa yang harganya
   justru naik setelahnya.

Untuk token yang lahir jam ini (kelas C2/D), jadwalnya sering **belum dipublikasikan** — artinya
metode ini tidak akan pernah bisa point-in-time pada universe termuda kami, dan itu batas struktural
yang harus ditulis apa adanya, bukan celah yang bisa ditutup dengan scraping ([[GAP4 - Yang Tidak Bisa Diuji Karena Data]]).

## Batas dan mode gagal

- **Efeknya lewat antisipasi, bukan lewat penjualan.** Kalau semua pihak tahu tanggalnya, harga
  sudah bergerak sebelumnya dan peristiwa itu sendiri sering neto. Membaca "tidak ada dump setelah
  unlock" sebagai "metodenya salah" adalah tanda bahwa yang diukur sebenarnya ekspektasi.
- **Jadwal bisa berubah dan berubah retroaktif**: perluasan vesting, percepatan karena akuisisi,
  distribusi OTC yang tidak lewat pasar. Sumber kedua (situs jadwal) tidak selalu menandai tanggal
  yang sudah diamendemen — jadi riwayat jadwal itu sendiri bukan point-in-time.
- **Float vs total** adalah kesalahan paling murah yang menghasilkan kesimpulan terbalik.
- **Peminjaman tidak terlihat di spot.** Sinyal yang diklaim ("borrow naik sebelum unlock") butuh
  pasar pinjaman; kami tidak punya jalurnya sama sekali *(belum diukur)*.
- **Survivorship:** yang punya jadwal terdokumentasi adalah token yang diluncurkan dengan struktur
  investor; memecoin tanpa vesting — sebagian besar universe BSC kami — tidak masuk sampel, jadi
  hasil dari kelas B tidak boleh dipindahtangankan ke kelas C2.
- **Duplikasi** dengan [[M4 - Catalyst dan Event Trading]]: unlock adalah katalis bertanggal; kalau
  keduanya dipakai sebagai satu skor, konfluensinya palsu (satu peristiwa, dua fitur).

## Tingkat bukti

`T1` untuk aritmetika jadwal (cliff/linear/float — definisi teknis, dimiliki siapa pun yang membaca
kontrak vesting) · `T0` untuk klaim arah-waktu ("unlock = jual H-1") · untuk Fabius: **tidak dapat
diuji** — jalurnya `TIDAK-ADA` (§C), dan pada sebagian besar kandidat kami jadwalnya bahkan belum
ada saat keputusan diambil.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami tahu jadwal unlock adalah metrik ekspektasi, kami tidak punya sumbernya, dan kami
  tahu bentuk uji yang akan dipakai kalau sumbernya dibeli."
- **Dilarang:** "Fabius memasukkan jadwal unlock ke dalam keputusan" · "token ini aman karena
  unlock-nya masih jauh" · "market cap-nya kecil" dari angka yang dibagi total supply · memakai
  jadwal yang ditemukan hari ini untuk menjelaskan harga minggu lalu.

**Terkait:** [[O6 - Konsentrasi Holder Bundler dan LP Lock]] · [[M4 - Catalyst dan Event Trading]] ·
[[O2 - MVRV SOPR dan NUPL]] · [[FD10 - Korelasi dan Risiko Keranjang]] · [[PL3 - Menganalisis]]

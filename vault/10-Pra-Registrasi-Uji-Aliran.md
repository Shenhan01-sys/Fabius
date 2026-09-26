---
type: pra-registrasi
ditulis: 2026-09-26T09:5xZ (SEBELUM satu angka hasil pun dilihat)
status: terkunci - amend hanya lewat entri baru di 06-Keputusan.md, tidak lewat menyunting halaman ini
---

# 10 — Uji Aliran Kerumunan: hipotesis dan ambang dikunci lebih dulu

## Kenapa halaman ini ada sebelum alatnya

Dua halaman hasil sebelumnya (`09` §1-4 aturan harga, §4c smart money) bisa dipercaya justru karena
ambang kami sudah tertulis sebelum hasilnya tiba — dan karena kami **tidak menambahkan fitur
sesudah melihat angka**. Kredit Dune yang kamu buka hari ini membeli godaan baru: dengan satu tabel
yang bisa di-`GROUP BY` sepuasnya, orang bisa menghasilkan 40 hipotesis dan melaporkan 2 yang
lolos. Jadi halaman ini ditulis duluan, dan angka pertama yang keluar akan dibandingkan ke sini,
bukan sebaliknya.

## Dataset yang dipakai

| | |
|---|---|
| sumber entri | Dune `dex.trades`, `blockchain='bnb'`, agregat per (token, jam): jumlah beli/jual, dompet unik beli/jual, USD beli/jual |
| alat | `tools/dune_flow.py` → `data/flow/flow-<hari>d.jsonl` (cache; analisis ulang tidak memanggil Dune lagi) |
| jendela | **14 hari** (dipilih dari kalibrasi, bukan dari hasil: agregat 3 hari = 11 detik Dune untuk 3.960 baris, vs 503 detik untuk kueri 10 hari yang mengirim baris mentah) |
| cakupan | **86 token** = simbol ber-kontrak perp di Aster yang benar-benar punya perdagangan; **402 baris alamat lain dengan simbol sama DIBUANG** (mis. `0G` punya 112 kontrak bernama sama) — alamat dipilih lewat volume, bukan urutan |
| sumber harga | kline Aster 1 jam yang kami tarik sendiri (`tools/bars.py`) — **bukan** harga Dune, karena baris Dune punya `_updated_at` (boleh jadi statistik, tidak boleh jadi saksi waktu) |

## Tiga hipotesis yang diuji (hanya ini)

| # | hipotesis | fitur yang mengukur | arah yang diharapkan |
|---|---|---|---|
| H1 | kerumunan yang **bergabung** menaikkan harga 4 jam berikutnya | `net_usd = usd_beli − usd_jual` dinormalisasi likuiditas | positif |
| H2 | yang penting **berapa banyak kepala**, bukan berapa dolar | `r_wallets = (pembeli − penjual) / (pembeli + penjual)` | positif |
| H3 | kerumunan yang **panik membeli** justru tanda pucuk (kebalikan H1) | kuil-tertinggi `net_usd` per token → hasil forward | negatif |

Ketiganya diuji dengan **satu** aturan keputusan, tidak ada varian keempat. Kalau ketiganya gagal,
jawabannya "aliran kerumunan tidak bisa diperdagangkan setelah ongkos" dan kami berhenti di situ.

## Aturan keputusan yang tidak boleh berubah di tengah jalan

- horizon **4 jam** (4 bar 1 jam), masuk di close bar berikutnya setelah jam sinyal
- **ongkos 20 bps round-trip** (5,5 taker + 4,5 spread/slip per sisi) — klaim lolos hanya kalau **net > 0**, dan gross harus > 40 bps seperti di `02-Ambang.md`
- **1 sampel per (token, jam)** — titik yang sama tidak boleh dihitung dua kali
- **n ≥ 20** per token, dan **Benjamini–Hochberg α = 0,10 lintas token** (satu token = satu tes)
- **drop-best-fold**: 5 segmen waktu, buang segmen terbaik, sisanya harus tetap > 0 (`09` menangkap penyakit ini di HeliQuant: HYPE +92 % OOS yang ternyata 65 % dari satu fold)
- karakter fitur diskors pada **kuintil atas/bawah** saja, supaya hasilnya tidak berasal dari eksekusi massal di median

## Batas yang kami tulis sekarang, supaya nanti tidak perlu dikejar

1. **Dune lag ±1 jam** dan barisnya bisa di-*update* retro → angka dari halaman ini adalah **statistik**, bukan bukti point-in-time.
2. **Arah panjang-pendek**: uji ini memakai beli−jual kerumunan; kerumunan tidak bisa short token spot, jadi H1/H2 diam-diam menguji sisi long saja.
3. **86 token bukan seluruh BSC** — hanya yang punya kontrak perp (kita memang tidak bisa menghargai yang lain dengan data kami sendiri).
4. Kalau sebuah hipotesis **lolos**, yang boleh ditulis adalah "lolos pada 14 hari, 86 token, setelah ongkos, dengan BH" — **bukan** "ada edge". Kata itu butuh konfirmasi di jendela baru setelah 30 Sep, dan kami tidak bisa memberikannya dalam hackathon ini.

---

# HASIL — dijalankan 26 Sep ~10:2xZ, aturan di atas tidak disentuh

`tools/flow_test.py` pada `data/flow/flow-14d.jsonl`: **18.122** titik (token, jam) → **86/86** token
terpetakan ke kontrak perp → **17.636** titik punya hasil forward → **62 token** lolos `n>=20`.

| | H1 dolar kerumunan | H2 jumlah kepala | H3 kuil = pucuk |
|---|---|---|---|
| arah yang diminta | HI > LO | HI > LO | HI < LO |
| token HI>LO / HI<LO | 34 / 28 | 32 / 30 | 34 / 28 |
| **lolos BH (α=0,10)** | **0** | **0** | **0** |
| 5 segmen waktu | +29,7 · +75,7 · −29,9 · −13,9 · −74,6 | +46,9 · −51,3 · −9,1 · +39,5 · −4,1 | (sama dgn H1) |
| tanpa segmen terbaik | **−22,2 bps** | **−6,2 bps** | **−22,2 bps** |

Tiga-duanya gagal, dan ini jawaban **ketiga dari arah yang berbeda** atas pertanyaan yang sama:
aturan harga (`09` §1-4), label smart money (`09` §4c), aliran kerumunan (halaman ini). Tidak ada
satu pun bidang yang kami punya yang menyisakan edge di atas 20 bps pada horizon 4 jam.

## Penyimpangan kami sendiri selama menjalankan (dicatat, tidak dihapus)

1. **"Tiga hipotesis" sebenarnya dua.** H3 memakai statistik yang sama dengan H1 (`net_usd`), hanya
   arah harapannya dibalik — jadi tabel di atas tidak menghitung tiga tes independen. Ini cacat pada
   halaman pra-registrasi-nya sendiri, dan yang berhak menemukannya bukan hasil, tapi seharusnya
   halaman itu. Untuk berikutnya: hipotesis harus dibedakan oleh **fitur**, bukan oleh tanda.
2. **`to_hex()` Trino mengembalikan heks HURUF BESAR**, peta alamat kami huruf kecil. Join pertama
   menjatuhkan **85 dari 86 token** dan tetap mencetak tabel H1/H2/H3 lengkap dengan n=292 —
   terbaca sah. Pagarnya sekarang: cakupan < 1/4 dari token → alatnya **menolak melapor**.
3. **Fold pertama saya salah dan tidak disadari satu kali.** "5 segmen" versi pertama membagi nilai
   selisih (urut besaran) padahal §"aturan" mengunci **segmen waktu**; setelah diperbaiki, foldnya
   tidak menyentuh kuintil sama sekali sehingga H1/H2/H3 mencetak angka IDENTIK. Keduanya baru
   kelihatan karena ketiga barisnya dicetak berdampingan — pelajaran yang layak diulang: tampilkan
   hasil yang seharusnya berbeda secara berdampingan.
4. Kredit: 1 kueri agregat 14 hari = **19 detik** Dune (vs 503 detik untuk kueri 10 hari yang
   mengangkut baris mentah); peta alamat dibaca dari cache sehingga tidak dibayar ulang. Analisis
   di atas dijalankan 4x tanpa satu kredit pun, karena hasil kueri sudah di-cache.

## Yang boleh dinyatakan di submission dari halaman ini

> "Kami mencoba tiga sumber sinyal yang berbeda — momentum harga, dompet berlabel smart money,
> dan aliran kerumunan dari Dune — di 86 token BNB Chain dengan kontrak perp, 14–400 hari data,
> hasil dihitung dari kline yang kami tarik sendiri. Tidak satu pun lolos koreksi multipel setelah
> ongkos 20 bps. Karena itu agen ini tidak menerbitkan sinyal; yang diterbitkan adalah keputusan
> yang bisa dibuktikan salah, beserta alasannya ketika ia menolak."

Frasa yang **tidak** boleh muncul: "tidak ada edge di crypto" (yang kami uji sempit), "whale tidak
jago" (yang kami uji = label GMGN, bukan whale), dan "sudah terkonfirmasi" (satu jendela, bukan dua).

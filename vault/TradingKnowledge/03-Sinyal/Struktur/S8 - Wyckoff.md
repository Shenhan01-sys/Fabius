---
tags: [tk, tk-sinyal, "S8"]
---

# S8 - Wyckoff

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Coba eksplor lagi" (Wyckoff Method: Accumulation,
Distribution, Spring, Upthrust) dan §"paling OP untuk berbagai situasi" ("sangat bagus untuk paham
fase market jangka menengah-panjang") — klaim komunitas; skemanya berasal dari buku R. D. Wyckoff
(pemilik klaimnya pengarang, bukan hasil ukur pihak ketiga)

**Ringkas:** Wyckoff adalah dua ide yang nilainya berbeda jauh. Ide pertama bagus dan abstrak:
harga bergerak karena **persediaan berpindah tangan**, jadi volume dan hasil bisa saling
bertentangan, dan sebuah rentang bisa berarti transfer, bukan kebuntuan. Ide kedua adalah
pelaksanaannya: lima fase, sembilan peristiwa, dan label yang baru bisa ditempatkan setelah
rangkaian itu selesai. Kami mempertahankan yang pertama sebagai kerangka berpikir dan memperlakukan
yang kedua sebagai skema yang bisa disesuaikan dengan fakta — `T0` untuk fase, `T1` untuk
pedagogi, dan **belum diuji** untuk keduanya.

## Definisi yang bisa dihitung

Varian kanon berbeda-beda antar-penerbit; ini versi yang dipakai catatan ini:

```
range        : B - A <= D_max dalam >= P bar, A = ayunan impuls sebelumnya          # P, D_max: parameter
AR (automatic rally/reaction) : ekstrem pertama setelah range menyentuh batasnya
spring       : low[t] < A - b*ATR DAN close[t] >= A          # "keluar lalu balik" -> lihat [[S6 - Likuiditas Stop Hunt dan Inducement]]
upthrust     : cerminnya di atas batas range
SOS / SOW    : penembusan batas range dengan volum >= q * median(volume, range)      # "effort vs result"
fase A..E    : urutan {AR, B, C(test), D, E} dalam range yang sama
akumulasi    : fase di ujung downtrend sebelumnya ; distribusi : cerminnya di ujung uptrend
```

Perhatikan apa yang **tidak** ada di sana: tidak satu pun baris mendefinisikan "akumulasi" sebagai
perpindahan persediaan antar-peserta. Fase-fase itu adalah penandaan bentuk harga, dan karena itu
bisa diberikan pada chart apa pun — yang membuatnya bukan hipotesis.

## Cara pakai yang diklaim

Beli di spring / *last point of support*, tahan melalui fase D, jual di markup; hindari posisi di
dalam fase B; baca "effort vs result" dari volume. Klaim komunitas di `Plan.txt` menempatkannya di
lapisan "paham fase pasar jangka menengah-panjang" — itu deskripsi kegunaannya, bukan klaim
prediktif, dan kami membacanya begitu.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| OHLC 1 jam ≥ 2.400 bar | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari; hanya aset ber-perp ([[Fakta Terukur]] §A) |
| volum per bar untuk "effort vs result" | `ADA` | `v` per bar di cache `tools/bars.py`; belum pernah dipakai untuk uji apa pun |
| pemisahan aggresor beli/jual (delta) | `TIDAK-ADA` | kolom taker dibuang `tools/bars.py` → lihat [[V3 - CVD Delta dan Footprint]] |
| **siapa memegang apa** (prasyarat klaim akumulasi) | `TIDAK-ADA` | konsentrasi holder belum terukur untuk Fabius ([[O6 - Konsentrasi Holder Bundler dan LP Lock]]) |
| aliran dompet sebagai saksi | `ADA-TAPI` | panel berlabel GMGN, jendela lihat 8–13 menit, tanpa riwayat, dan bukan pasar perp tempat fase biasanya dibaca (§B) |
| pelabel fase | `TIDAK-ADA` | tidak ada alat Fabius yang mendeteksi range, spring, atau fase |

## Uji di Fabius

Yang bisa diuji tanpa data tambahan (belum ada yang menjalankan):

1. Definisikan `range`, `spring`, `SOS` dengan parameter beku sebelum hasil dilihat; label **hanya
   dari bar `<= t`** ([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]).
2. Uji `spring` sebagai peristiwa: return bersih 4 j/24 j setelah penolakan kembali ke dalam
   range. Null-nya tembusan acak dengan jumlah sama pada level acak (pola uji yang sama dengan
   [[S7 - Fibonacci Retracement dan Extension]]).
3. Uji klaim intinya secara terpisah dari geometri: "sesuatu berpindah tangan sebelum kenaikan".
   Itu bukan pertanyaan bentuk harga — itu pertanyaan distribusi holder. Jalur yang tersedia:
   konsentrasi holder + aliran dompet point-in-time, dan keduanya baru berjalan sejak perekaman
   dimulai, tidak bisa ditarik mundur (§B). Artinya klaim Wyckoff yang paling menarik **belum punya
   data**, bukan belum punya kode.
4. Gerbang hasil seperti biasa: `n >= 20` non-overlap, gross vs **59 bps** (§D), fold terbaik
   dibuang, BH α 0,10 (§E).

## Batas dan mode gagal

- **Fase bisa diberi label setelah fakta.** Spring yang gagal = "tidak ada permintaan";
  upthrust yang gagal = "tanda kekuatan"; range yang tembus terlalu cepat = "fase B singkat". Tiga
  aturan yang mencakup semua hasil tidak bisa dibuktikan salah ([[EV5 - Reproduksibilitas dan Pra-Registrasi]]).
- **Sembilan peristiwa = sembilan tembakan per range.** Multiple testing tanpa koreksi membuat
  salah satunya "benar" di hampir setiap chart (§E, [[EV3 - Signifikansi dan Multiple Testing]]).
- **Durasi.** Fase jangka menengah-panjang butuh puluhan hari satu siklus; `MIN_BARS_TINY=720`
  (30 hari) hanya menampung satu siklus di aset terdalam kami, jadi populasinya kecil bahkan
  sebelum dihitung *(belum diukur)*.
- **Duplikasi dengan S6 dan S2.** `spring` = sweep di batas range; `SOS` = breakout pola
  ([[S6 - Likuiditas Stop Hunt dan Inducement]], [[S2 - Chart Patterns]]). Satu peristiwa, tiga
  keluarga nama.
- **Sinyal volume tidak sekuat kedengarannya.** Volum per bar tidak mengatakan siapa penjualnya;
  di venue ber-perp, volum juga berisi pembukaan dan penutupan posisi yang sama
  ([[V1 - Konfirmasi Volum dan Money Flow]], [[U1 - Open Interest]]).
- **Ongkos.** Fase B = chop; setiap percobaan keluar-masuk di dalamnya membayar 59 bps (§D).

## Tingkat bukti

`T1` untuk pedagogi ("persediaan berpindah; volume dan harga bisa bertentangan") · `T0` untuk
status fase sebagai pengetahuan prediktif dan untuk klaim adanya *composite man* di baliknya ·
untuk Fabius: **belum diuji**; dan klaim intinya butuh data distribusi holder yang belum ada.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Wyckoff mengajarkan pertanyaan yang benar (siapa memegang, siapa yang memaksa keluar)
  dengan alat yang salah (label fase pasca-hoc); pertanyaannya bisa diuji dengan data holder,
  jawabannya belum kami punya."
- **Dilarang:** "market berada di fase C akumulasi" · "spring terbukti punya win rate X %" ·
  "Fabius membaca Wyckoff".

**Terkait:** [[S2 - Chart Patterns]] · [[S6 - Likuiditas Stop Hunt dan Inducement]] ·
[[V1 - Konfirmasi Volum dan Money Flow]] · [[O6 - Konsentrasi Holder Bundler dan LP Lock]] ·
[[FD1 - Struktur Pasar dan Rezim]] · [[GAP3 - Yang Punya Data Tapi Belum Diuji]] · [[Fakta Terukur]]

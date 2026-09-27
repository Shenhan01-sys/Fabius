---
tags: [tk, tk-sinyal, "U4"]
---

# U4 - Long-Short Ratio dan Skew Posisi

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"3. CONFIRMATION LAYER (Lapisan Konfirmasi)"
(Futures-Specific: "Long/Short Ratio") — klaim komunitas

**Ringkas:** "Rasio long-short" terdengar satu angka padahal ia minimal tiga angka berbeda,
tergantung **siapa** yang dihitung dan **dengan satuan apa**: rasio jumlah akun, rasio nilai posisi
(USD), dan rasio posisi trader terpilih. Yang pertama hampir selalu didominasi akun ritel, sehingga
pembacaan yang beredar justru kontrarian: banyak akun long = sedikit uang long. Status di repo ini
bersih dan sederhana: **TIDAK-ADA** — tidak ada jalur datanya, dan venue yang biasa memublikasikannya
ada di daftar yang mati dari mesin ini.

## Definisi yang bisa dihitung

```
rasio_akun      = #akun_long / #akun_short                    # tiap akun = 1 suara,abaikan ukuran
rasio_nilai     = sum(nilai_long) / sum(nilai_short)          # berbobot uang
rasio_pemilih   = sama dengan salah satu di atas, tapi hanya untuk "top traders" (definisi vendor)
# dan yang sering tertukar dengan ketiganya:
rasio_taker_vol = volum agresor beli / volum agresor jual     # aliran, bukan posisi terbuka
skew_posisi     = (nilai_long - nilai_short) / (nilai_long + nilai_short)   # ~[-1, +1]
```

Yang elementer: rasio akun **tidak berubah** kalau satu whale membuka posisi 100× lebih besar dari
ritel, sementara rasio nilai bertambah 100×. Dua-duanya disebut "long-short ratio" di
dashboard yang sama. `rasio_taker_vol` juga sering dijual sebagai rasio posisi padahal ia tidak
mengenal posisi yang sedang menutup — dan menghitungnya butuh sisi agresor
([[V3 - CVD Delta dan Footprint]]).

## Cara pakai yang diklaim

Dibaca kontrarian oleh komunitas: rasio akun long tinggi + funding positif = kerumunan di satu sisi
= bahan squeeze ke bawah; ekstrem yang sama di sisi short = bahan squeeze ke atas. Kadang dipakai
sebagai "orang banyak salah". Klaimnya tidak menyebut populasi mana yang dimaksud — dan itu
menentukan segalanya. Tidak ada rujukan primer untuk ini di repo ini.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| rasio akun long/short (global atau per aset) | `TIDAK-ADA` | tidak ada jalur di repo; penerbit umumnya venue besar yang ada di daftar mati §C: `api.binance.com` → `451 restricted location` di runner ([[Fakta Terukur]] §C) |
| rasio nilai / skew posisi | `TIDAK-ADA` | butuh distribusi posisi per pihak; OI kita tidak memecah long vs short ([[U1 - Open Interest]]) |
| endpoint rasio di venue lain sebagai kontrol | `TIDAK-ADA` | belum pernah diukur sebagai **pasangan sumber×jaringan**; OKX/Bitget yang sekelas terukur `200` di runner tapi terpotong TLS di laptop (§C) |
| tanda tekanan searah (bukan populasi) | `ADA-TAPI` | funding per 4 jam untuk 608 kontrak (§A) — tahu siapa membayar, tidak tahu berapa banyak |
| besaran posisi terbuka | `ADA-TAPI` | OI spot per tanggal baca (§A), tanpa histori dan tanpa pembagian sisi |
| beli/jual per jendela untuk panel dompet berlabel | `ADA-TAPI` | `tools/flow_signal.py` mencetak `beli/jual` + `net_usd` per kelompok maker — **skew panel ⑦**, bukan skew pasar; jendela lihat 8–13 menit dan tanpa riwayat (§B) |

## Uji di Fabius

Tidak ada yang bisa diuji untuk rasio pasar sampai datanya ada — ini penghuni
[[GAP4 - Yang Tidak Bisa Diuji Karena Data]]. Yang **bisa** diuji hari ini, dan harus ditulis dengan
namanya sendiri, adalah proksi terdekat: skew beli/jual pada aliran ⑦ kami sendiri. Bentuknya sudah
ada di `tools/flow_signal.py` (point-in-time terhadap umur snapshot, dan melaporkan aliran semua
maker vs maker ber-tag secara terpisah). Uji yang menentukan artinya: bandingkan net hasil arah
skew itu dengan **arah acak pada token dan jam yang sama** (§B) — dan ingat hasilnya sudah pernah
datang dari arah lain: panel berlabel tidak lebih baik dari kerumunan (selisih **−10,4 bps**,
`p = 0,568`) saat dipasangkan per (token, jendela 4 jam), lihat [[06-Results/03 - Not Yet Proven]]
baris 20. Ambang klaim tetap `n >= 20` non-overlap + BH α 0,10 + ongkos **59 bps** (§D/§E).

## Batas dan mode gagal

- **"Siapa yang dirasio" adalah seluruh isinya.** Rasio akun ritel dan rasio nilai institusi bisa
  bertanda berlawanan pada menit yang sama; membaca yang pertama dengan kepercayaan diri yang
  biasanya diberikan ke yang kedua adalah kesalahan kategori.
- **Kontrarian tanpa definisi ekstrem.** "Rasio tinggi = buruk" butuh ambang dan historinya;
  tanpa histori (yang `TIDAK-ADA`), "tinggi" hanya bisa ditetapkan setelah hasilnya dilihat —
  penyakit yang sama seperti ambang yang tidak dibakukan di [[EV6 - Kalibrasi Ambang Terhadap Hasil]].
- **Label panel ≠ populasi pasar.** Skew ⑦ mengukur dompet yang **sudah** dilabeli GMGN; 0 dari 607
  transaksi pertama tidak bertag (§B) — jadi tidak ada "sisa pasar" di dalam data kita untuk
  dibandingkan.
- **Duplikasi dengan U1/U2:** skew posisi, OI, dan funding adalah tiga pembacaan dari besaran
  yang sama; memakainya bertiga sebagai tiga konfirmasi menaikkan keyakinan, bukan informasi.

## Tingkat bukti

`T1` untuk perbedaan tiga definisi rasio (standar pelaporan venue) · `T0` untuk klaim prediktif
kontrarian dan untuk semua angka rasio yang dikutip dari dashboard · untuk Fabius: **tidak ada
datanya**; satu-satunya skew yang bisa dihitung adalah skew panel kami sendiri, dan pembacaan yang
sudah terukur atas panel itu **melawan** klaimnya (§F baris panel whale: win rate 69,8 % tapi
−10,4 bps per jam).

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami tidak punya rasio long/short pasar; yang kami punya adalah beli/jual pada panel
  dompet berlabel kami sendiri, dan panel itu belum pernah mengalahkan arah acak setelah ongkos."
- **Dilarang:** "Fabius membaca sentimen posisi" · menyebut `beli/jual` dari aliran ⑦ sebagai
  long-short ratio · mengutip angka rasio vendor tanpa pemiliknya · memperlakukan rasio akun dan
  rasio nilai sebagai hal yang sama.

**Terkait:** [[U1 - Open Interest]] · [[U2 - Funding Rate dan Basis]] ·
[[U3 - Level Likuidasi dan Cascade]] · [[O5 - Whale dan Kohor Smart Money]] ·
[[V3 - CVD Delta dan Footprint]] · [[03-Data/D2 - Wallet Flow]]

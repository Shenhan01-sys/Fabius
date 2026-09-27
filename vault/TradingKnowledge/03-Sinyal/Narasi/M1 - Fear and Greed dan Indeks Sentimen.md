---
tags: [tk, tk-sinyal, "M1"]
---

# M1 - Fear and Greed dan Indeks Sentimen

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"5. Pendekatan Fundamental & Sentiment (Crypto
Native)" ("Fear & Greed + Alternative data") + §"3. Strategi Berbasis On-Chain & Data Crypto
Spesifik" ("Sentiment Analysis (Fear & Greed Index, social media, funding rate)") — klaim komunitas

**Ringkas:** Indeks Fear & Greed mengubah beberapa ukuran pasar menjadi satu angka 0–100. Bagi
pembacanya ia terasa seperti "suasana hati pasar"; bagi pembuatnya ia adalah aritmetika dari
volatilitas, momentum, volume, dominance, dan survei. Konsekuensinya penting untuk lapisan ini:
**sebagian besar komposisinya bisa dihitung ulang dari data harga yang sudah kami punya**, jadi
memakainya sebagai masukan baru sering berarti mengukur hal yang sama dua kali — kali ini dengan
label yang lebih meyakinkan.

## Definisi yang bisa dihitung

```
bentuk umum tiap indeks komposit sentimen:
  z_i(t)  = standarisasi(minimum_i, maksimum_i) dari satu ukuran pasar (mis. volatilitas,
            momentum N hari, volume, dominance, jawaban survei)
  skor    = W * clamp( sum_i w_i * z_i(t), 0, 100 )
# "w_i" dan jendela standarisasi adalah milik penerbit; bobot yang diumumkan penerbit
# (mis. porsi volatilitas/momentum/sosial/dominance/survei) = **klaim penerbit**, kami tidak
# mereproduksi angkanya -> T0/T2, bukan temuan kami.
kontrak yang bisa dipakai pembaca: 0 = ketakutan ekstrem, 100 = keserakahan ekstrem, dan
**tidak ada** satuan yang membuat 24 lebih mungkin naik daripada 26.
```

## Cara pakai yang diklaim

Dua bacaan yang saling bertentangan beredar bersamaan: kontrarian ("takut ekstrem = beli") dan
momentum ("keserakahan = tren masih hidup"). Penganutnya memakai yang cocok setelah hasilnya ada.
Itu bukan kesalahan indeksnya, tapi konsekuensi dari menjual satu angka tanpa definisi hasil.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| jalur ke indeks Fear & Greed pihak ketiga | `TIDAK-ADA` | tidak ada satu pun berkas di `tools/`/`universe/` yang memanggilnya; ia juga **tidak** ada di daftar jalur-hidup §C ([[Fakta Terukur]]) |
| volatilitas/momentum yang jadi bahan indeks itu | `ADA-TAPI` | kline Aster 9.599 bar 1 jam ≈ 400 hari (§A) — cukup untuk menghitung ulang komponen harga, tapi hanya untuk aset **ber-kontrak perp** |
| volume pasar agregat sebagai komponen | `ADA-TAPI` | `volume_24h` per kandidat direkam `universe/record_bsc_universe.py`; tidak ada agregat pasar lintas universe |
| dominance (porsi BTC/ETH dari kapitalisasi pasar) | `TIDAK-ADA` | butuh kapitalisasi pasar lintas aset; tidak ada jalurnya di repo |
| survei / Google Trends sebagai komponen | `TIDAK-ADA` | tidak ada jalur; dan keduanya punya masalah waktu terbit sendiri ([[M2 - Sentimen Sosial dan Ekstraksi LLM]]) |
| perhatian/trending sebagai proxy sentimen yang **kami** rekam | `ADA-TAPI` | bidang ⑤ memakai CoinGecko trending + CoinDesk RSS + berkas GDELT (§C: CoinGecko hidup di dua jaringan; rinci di [[01-Agent/01 - Asset Classes and Seats]] §1) — **belum diuji prediksinya** ([[06-Results/03 - Not Yet Proven]] baris 8) |

## Uji di Fabius

Uji yang benar atas sebuah indeks komposit bukan "apakah angkanya rendah/tinggi", tapi **apakah ia
menambah sesuatu di atas komponennya sendiri**. Langkahnya: (1) reproduksi komponen yang bisa
dihitung dari kline kita (volatilitas + momentum + volume); (2) regresikan/labeli hasil 4 jam
berikutnya pada keduanya — indeks eksternal **dan** reproduksinya; (3) klaim hanya boleh naik kalau
indeks eksternal menambah daya beda di atas reproduksi kita. Ambang: `n >= 20` non-overlap, gross di
atas **59 bps** (§D), BH α 0,10 (§E). Perintah pembanding ini **belum ditulis**; kalau hasilnya
nol, kesimpulan yang benar adalah "indeks itu tidak membawa informasi baru", dan itu bukan alasan
untuk menghapusnya dari layar — itu alasan tidak menjadikannya gerbang.

## Batas dan mode gagal

- **Agregat menyembunyikan komponen.** Satu angka 0–100 membuat orang berhenti bertanya ukuran mana
  yang bergerak; dua rezim pasar bisa menghasilkan angka yang sama dari komponen yang berlawanan.
- **Siklus hidupnya sendiri.** Setelah indeks populer, ia jadi objek berita — jadi "sentimen" mulai
  mengukur liputan atas dirinya sendiri.
- **Waktu terbit tidak pernah gratis.** Kalau indeks dihitung dari data yang kami lihat lebih dulu,
  ia datang **setelah** harga bergerak ([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]).
- **Duplikasi:** komponen momentum/volume = [[I1 - Moving Average]]/[[FD8 - Volatilitas]]/[[V1 - Konfirmasi Volum dan Money Flow]];
  memakai indeks + ketiganya sekaligus adalah tiga suara untuk satu fakta.
- **Kontrarian vs momentum** tidak bisa keduanya benar pada angka yang sama; aturan yang menerima
  dua-duanya setelah fakta bukan aturan ([[FD11 - Aturan Mengalahkan Intuisi]]).

## Tingkat bukti

`T0` untuk klaim "pasar sedang takut = waktu membeli" (tanpa sumber di repo ini) · `T1` untuk
pola pakai indeks komposit sebagai ringkasan (dipakai luas) · untuk Fabius: **tidak punya
jalurnya**, dan tidak ada satu pun baris keputusan yang membaca angka sentimen eksternal.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "komponen Fear & Greed sebagian besar dapat dihitung dari data harga kami sendiri;
  kami belum punya jalurnya dan belum menguji apakah ia menambah informasi."
- **Dilarang:** "pasar sedang takut/serakah" sebagai kalimat Fabius · "indeks sentimen dipakai
  agen" · mengutip bobot penerbit sebagai fakta pasar · memakai angka indeks hari ini sebagai bukti
  untuk klaim masa lalu (waktu terbitnya tidak kita ketahui).

**Terkait:** [[M2 - Sentimen Sosial dan Ekstraksi LLM]] · [[M3 - Narasi Sektar dan Rotasi]] ·
[[M5 - Makro dan Korelasi Silang-Pasar]] · [[V1 - Konfirmasi Volum dan Money Flow]] ·
[[FD11 - Aturan Mengalahkan Intuisi]] · [[QT9 - LLM sebagai Pembaca Narasi]]

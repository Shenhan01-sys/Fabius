---
tags: [tk, tk-sinyal, "M3"]
---

# M3 - Narasi Sektar dan Rotasi

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** filtering ([[PL2 - Menyaring Universe]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"3. CONFIRMATION LAYER"→"Narrative & Catalyst"
("Sector Narrative (AI, RWA, DePIN, dll)") — klaim komunitas

**Ringkas:** "Musim AI", "musim RWA", "memecoin season": uang berpindah antar kategori lebih cepat
dari perpindahan antar aset individual, dan siapa yang menunggangi rotasi tidak perlu memilih satu
token.
Masalahnya, "kategori" adalah objek yang tidak punya pemilik resmi. Yang membuat keluarga ini bisa
dipakai (atau dibuang) adalah jawaban atas satu pertanyaan: **siapa yang melabeli sebuah token sebagai
AI, dan sejak kapan?** Di repo ini jawabannya ada dan kecil: kategori dari daftar kontrak perp venue.

## Definisi yang bisa dihitung

```
# share perhatian per kategori, dari data yang benar-benar kami punya:
share_vol(k, t)   = sum(volume_24h aset di kategori k) / sum(volume_24h semua kandidat)
breadth(k, t)     = # {aset di k : ret_24h > 0} / # {aset di k}          # apakah naik-serentak
age_median(k, t)  = median(umur pool) per kategori                        # "musim" = gelombang token baru
rotasi(k)         = korelasi silang ret(k) vs ret(k_other), per jendela   # -> [[FD10 - Korelasi dan Risiko Keranjang]]
# Yang TIDAK bisa dihitung dari repo ini: kapitalisasi pasar per kategori, flow antar kategori,
# dan "porsi narasi di X" -> ketiganya butuh taksonomi + data pasar lintas kategori yang tak kami punya.
```

Ukuran yang tahan banting di sini adalah **volume per kategori dan umur token**, bukan headline:
keduanya punya timestamp dan bisa dihitung ulang dari snapshot yang sudah kami simpan.

## Cara pakai yang diklaim

Masuk kategori yang share-nya sedang naik, keluar saat breadth memburuk; hindari kategori yang
sudah "lelah" (breadth turun tapi harga masih naik). Klaimnya dari praktisi narasi dan dari
`Plan.txt` sendiri ("Membantu pilih pair yang sedang kuat dan hindari pair yang mati"); tidak ada
sumber primer di repo ini.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| label kategori untuk aset yang bisa dihargai | `ADA-TAPI` | daftar kontrak perp Aster punya kategori — **608 kontrak, `Meme` 61, `AI` 42** (§A). Ini label **listing venue**, bukan taksonomi kita, dan tidak berisi RWA/DePIN |
| label kategori untuk memecoin spot-only / pool baru | `TIDAK-ADA` | tidak ada kontrak = tidak ada kategori; `universe/record_bsc_universe.py` menyimpan perilaku token, bukan sektor |
| deret volume per kandidat lintas waktu | `ADA-TAPI` | `volume_24h` per snapshot direkam `universe/record_bsc_universe.py`; **belum pernah diagregasi per kategori** |
| berita bertema sektor | `TIDAK-ADA` | `GDELT_THEME_KEYS` di `universe/record_bsc_universe.py` berisi tema makro-regulasi (BANK, GOVERNMENT, REGULAT, SANCTION, TRADE, …) — tidak ada satu pun kunci sektor kripto |
| harga forward untuk anggota kategori | `ADA-TAPI` | kline perp 9.599 bar ≈ 400 hari (§A) — hanya untuk anggota yang punya kontrak |
| umur token / pool per kandidat | `ADA` | `age_sec` + `created_at` + `launched` direkam `universe/record_bsc_universe.py`; veto `age<24h_zero_bars` sudah menegakkan bagian tertuanya |

## Uji di Fabius

Bentuk uji yang sah dan bisa dikerjakan dengan data yang ada: untuk tiap snapshot, hitung
`share_vol` dan `breadth` per kategori **hanya dari baris <= t**
([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]); event = lompatan share ke
kuartil atas; hasil = return bersih 4 jam anggota kategori itu. Kontrol wajib: **arah acak pada
token dan jam yang sama** (§B), plus kontrol "semua aset" — karena separuh "rotasi" sebenarnya cuma
beta pasar. Ambang: `n >= 20` non-overlap, gross di atas **59 bps** (§D), BH α 0,10 (§E), dan —
khusus keluarga ini — koreksi untuk korelasi antar simbol: docstring `tools/backtest.py` mencatat
beberapa simbol berbagi satu pergerakan pasar sehingga BH per simbol hanya mendukung klaim "satu
simbol lolos", bukan "kategori lolos". Kode agregasi sektor **belum ditulis**.

## Batas dan mode gagal

- **Taksonomi = pendapat pihak ketiga.** Kategori venue bisa berpindah tanpa pemberitahuan, dan
  sebuah token boleh masuk dua kategori; hasil uji jadi bergantung pada label yang tidak bisa kami
  pertanggungjawabkan.
- **Survivorship paling jahat di sini.** "Memecoin season" justru terjadi di kelas C2/D — yang
  deretnya mentok 1.000 bar (§A) dan tidak punya kontrak perp. Kategori yang bisa kita ukur adalah
  kategori yang **sudah** lolos ke venue, jadi narasi yang paling awal selalu yang paling tidak
  bisa kita uji.
- **Rotasi sering hanya beta.** Semua naik bersamaan = korelasi tinggi, bukan rotasi; bedanya
  diuji dengan kontrol "semua aset" di atas ([[FD1 - Struktur Pasar dan Rezim]]).
- **Keranjang sektor bukan diversifikasi.** Membeli 5 token "AI" = satu taruhan dengan 5 nama
  ([[FD10 - Korelasi dan Risiko Keranjang]]); ukuran posisi per keranjang, bukan per token
  ([[FD6 - Ukuran Posisi]]).
- Duplikasi: `share_vol` hampir identik dengan [[V1 - Konfirmasi Volum dan Money Flow]] pada
  irisan yang sama.

## Tingkat bukti

`T1` untuk deskripsi rotasi sebagai fenomena pasar · `T0` untuk klaim bahwa menunggangi narasi
menambah expectancy · untuk Fabius: **belum diuji**; satu-satunya bahan yang sudah ada adalah
kategori venue dan snapshot volume, dan tidak ada satu pun alat yang menggabungkannya.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kategori venue memberi kami label sektor untuk 608 kontrak perp; agregasi volume per
  kategori belum pernah dihitung, belum pernah diuji."
- **Dilarang:** "Fabius mendeteksi rotasi sektor" · menjual `Meme` 61 / `AI` 42 sebagai peta pasar
  (itu daftar kontrak) · menyebut "memecoin season" terukur padahal asetnya tidak bisa kami hargai
  cukup panjang · memperlakukan 5 token satu kategori sebagai 5 posisi independen.

**Terkait:** [[M2 - Sentimen Sosial dan Ekstraksi LLM]] · [[M4 - Catalyst dan Event Trading]] ·
[[M5 - Makro dan Korelasi Silang-Pasar]] · [[V1 - Konfirmasi Volum dan Money Flow]] ·
[[FD10 - Korelasi dan Risiko Keranjang]] · [[FD1 - Struktur Pasar dan Rezim]]

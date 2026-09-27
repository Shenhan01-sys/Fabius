---
tags: [tk, tk-sinyal, "O4"]
---

# O4 - Active Addresses dan Pemakaian Gas

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Strategi Berbasis On-Chain & Data Crypto Spesifik"
(baris "Active Addresses, Transaction Count, Gas Usage") — daftar topik, bukan fakta; bukti dompet
dari `universe/record_wallet_flow.py` + [[Fakta Terukur]] §B/§D

**Ringkas:** dua angka yang sering dijual sebagai "jumlah orang yang memakai jaringan": alamat unik
per jendela dan transaksi per jendela, kadang digabung jadi biaya gas sebagai proxy perhatian.
Keduanya bukan manusia dan bukan permintaan — mereka adalah **jumlah kunci yang bertransaksi**, dan
satu operator bisa memegang ratusan. Proyek ini punya bukti sendiri bahwa "jumlah dompet" tidak bisa
dibaca sebagai populasi: aliran ⑦ kami **0 dari 607 transaksi pertama** tidak bertag panel
(§B), artinya populasi yang kami namakan "maker" adalah daftar yang sudah disaring orang lain.

## Definisi yang bisa dihitung

```
active_addrs(w)   = |{address : ada >=1 transaksi dengan timestamp ∈ w}|          # per kontrak atau per chain
new_addrs(w)      = active_addrs(w) \ active_addrs(sebelum w)                      # bukan "manusia baru"
tx_count(w)       = jumlah transaksi di w
gas_spent(w)      = Σ (gas_used × harga per gas) di w                              # dalam USD = BIAYA, bukan perhatian
usia_per_kelompok = distribusi umur dompet yang aktif di w (umur = waktu transaksi pertama kali terlihat)
```

Bedakan tiga hal yang diadopsi komunitas sering dicampur: **alamat** (kunci), **aktor** (orang atau
kontrak yang mengontrol banyak kunci), dan **permintaan** (uang yang benar-benar berpindah). Hanya
yang pertama yang bisa dihitung dari blok; dua lainnya adalah interpretasi.
`usia_per_kelompok` adalah bentuk yang paling informatif dari ketiganya: cohorts yang sama-sama muda
dan sama-sama lenyap = aktivitas berpindah tempat, bukan pasar yang tumbuh.

## Cara pakai yang diklaim

Diklaim oleh penyedia metrik jaringan: kenaikan alamat aktif + kenaikan gas = perhatian naik =
fundamental menguat; penurunan = ditinggalkan. Dipakai di horizon harian–mingguan, lintas chain,
sering dengan koreksi musiman "airdrop farming". Tidak ada dari klaim ini yang menyediakan
invalidasi, dan nyaris tidak ada yang menyebut ongkos masuk — padahal ongkos adalah satu-satunya
bagian yang **sudah kami ukur** di proyek ini (§D: round-trip venue demo **59 bps**; gas testnet 97
**0,10 gwei** live vs floor guard lama **1 gwei** yang menolak karena plafon sendiri).

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| alamat unik per token per jam (riwayat) | `TIDAK-ADA` | tidak ada jalur di repo; `universe/record_wallet_flow.py` menyimpan maker **berlabel**, bukan seluruh `from`/`to` |
| populasi transaksi seluruh wallet per jam | `ADA-TAPI` | bisa diambil sebagai agregat via Dune (`tools/dune_flow.py`) — lag **±1 jam** di BSC ([[03-Data/D4 - Dune]]) → bukan jalur keputusan |
| biaya gas per transaksi yang kami lakukan | `ADA` | §D: guard testnet 97 membaca gas live; angka mainnet **belum diukur** |
| umur dompet / cohort | `TIDAK-ADA` | tanpa riwayat tidak ada "transaksi pertama" yang bisa ditunjuk; jendela lihat aliran kami 8–13 menit dan tidak bisa ditarik mundur (§B) |
| harga forward untuk menilai | `ADA` | Aster 9.599 bar ≈ 400 hari (§A); GMGN 1.000 bar ≈ 41,6 hari (§A) |

## Uji di Fabius

Perintahnya **belum ditulis**; yang sudah ada cuma bahan bakunya. Bentuk yang sah:

1. Hitung `active_addrs` dan `tx_count` hanya dari baris `<= t`, lalu simpan **snapshot definisi**
   populasinya — kalau tidak, satu jam yang bolong pada perekam akan terbaca sebagai "orang pergi".
2. Features vs hasil: return bersih 4 jam dari bar kami; kontrol = **arah acak pada token dan jam
   yang sama** (§B) dan **hold 4 jam tanpa memilih arah**; pisahkan `is_open_or_close=1` vs `=0`.
3. Uji `usia_per_kelompok` sebagai filter, bukan skor: kelompok yang seluruhnya berumur < 1 jam
   tidak boleh diperlakukan seperti basis pengguna yang tumbuh.
4. Ambang klaim: `n >= 20` non-overlap, gross di atas **59 bps** (§D), buang fold terbaik,
   BH α 0,10; satu sampel per (token, jendela tak tumpang-tindih).

## Batas dan mode gagal

- **Sybil dan bundler.** Satu orang berpakaian banyak topeng menghasilkan "alamat baru" tanpa satu
  pembeli pun. Kami sudah punya bukti bahwa fenomena ini nyata di universe: `MAX_BUNDLER` 30 % dan
  `MIN_HOLDER` 60 alamat (§E) dipakai justru untuk **menolak** — jadi memakai jumlah alamat sebagai
  sinyal penguat, sambil menolaknya sebagai risiko, adalah dua tangan yang saling menyangkal
  ([[O6 - Konsentrasi Holder Bundler dan LP Lock]]).
- **Panel yang didefinisikan vendor.** Angka 0 % tak bertag (§B) berarti kami tidak punya populasi
  pembanding: setiap "berapa banyak dompet aktif" yang kami jawab hari ini sebenarnya menjawab
  "berapa banyak dompet yang GMGN tunjuk".
- **Gas ≠ permintaan.** Gas naik karena perang fee, karena bot, karena aktivitas yang tidak menyentuh
  token yang sedang kami nilai. Gas adalah harga sebuah sumber daya, dan kami punya contoh lokal:
  guard kami menolak transaksi **karena plafon gas yang kami tulis sendiri**, bukan karena chain-nya
  sibuk — angka yang sama bisa berarti dua hal yang berlawanan.
- **Perbandingan lintas chain tidak ada artinya.** Satu transaksi di chain murah ≠ satu unit
  perhatian; membandingkan BSC dengan chain L2 adalah membandingkan satuan biaya.
- **Musiman/insentif.** Airdrop, campaign, dan farming menaikkan semua metrik ini tanpa mengubah
  siapa pun jadi pembeli yang bertahan.

## Tingkat bukti

`T1` untuk definisi (standar eksplorasi chain) · `T0` untuk klaim "alamat aktif = harga naik" ·
untuk Fabius: **belum diukur** — tidak ada satu pun alat yang menghitung alamat aktif; yang terukur
hanya bahwa populasi kami bukan sampel acak dari pengguna (§B).

## Boleh dibaca, dilarang dibaca

- **Boleh:** "jumlah alamat tidak bisa dibaca sebagai jumlah orang, dan kami punya bukti internal
  bahwa populasi dompet kami adalah pilihan vendor, bukan populasi jaringan."
- **Dilarang:** "Fabius memantau active addresses" · "452 maker = 452 orang yang tertarik" (§B: itu
  **hasil penyaringan panel**) · "gas tinggi = permintaan naik".

**Terkait:** [[O6 - Konsentrasi Holder Bundler dan LP Lock]] · [[O5 - Whale dan Kohor Smart Money]] ·
[[FD4 - Ongkos Perdagangan]] · [[Concepts/Cost Is Fixed]] · [[PL3 - Menganalisis]]

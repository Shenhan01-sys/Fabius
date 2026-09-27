---
tags: [tk, tk-sinyal, "O6"]
---

# O6 - Konsentrasi Holder, Bundler dan LP Lock

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** filtering ([[PL2 - Menyaring Universe]])
**Sumber:** `universe/record_bsc_universe.py` (field perilaku per token) + `tools/screen_universe.py`
(screener di atas snapshot point-in-time) + `tools/security_gate.py` · topik "Tokenomics Analysis"
dari `vault/TradingKnowledge/Plan.txt` §"Pendekatan Fundamental & Sentiment (Crypto Native)"

**Ringkas:** satu-satunya keluarga on-chain yang **sudah wired** di Fabius. Tiga angka ditanya ke
setiap kandidat: seberapa terpusat sahamnya (`top_10_holder_rate`), seberapa besar volumnya ternyata
satu orang berpakaian banyak topeng (`bundler_rate`), dan seberapa bisa likuiditasnya ditarik kapan
saja (`lock_percent`). Yang dijual orang sebagai "filter keamanan" memang menolak barang jelek —
tapi ambangnya **diputuskan, bukan diuji terhadap hasil**, jadi hari ini ia adalah kebijakan, bukan
bukti.

## Definisi yang bisa dihitung

```
top10_share   = Σ saldo 10 alamat terbesar / supply                 # 1,0 = satu orang punya segalanya
bundler_share = fraksi volum (atau holder) yang datang dari dompet yang di-deteksi bundler
lock_share    = LP token yang terkunci / seluruh LP                 # tanpa ini likuiditas bisa hilang 100 %
holders       = jumlah alamat dengan saldo > ambang minimum
vol_over_liq  = volume_24h / likuiditas_pool                          # "ramai" vs "tipis"
```

Tiga dari lima angka ini datang dari **sumber pihak ketiga** (GMGN `market/rank` / `token/security`)
dengan definisi internal yang tidak kami pegang: kami tahu nilainya, kami tidak tahu persis apa yang
dihitung vendor. `holders_unmeasured` dan tetangga null-nya adalah kasus khusus yang wajib disebut
terpisah — lihat "Batas".

## Cara pakai yang diklaim

Diklaim oleh praktisi memecoin dan penyedia screener: buang token dengan top-10 tinggi, lock
rendah, bundler tinggi — sisanya "aman". Klaim turunannya biasanya berupa win-rate atau "anti-rug".
Tidak ada pemilik klaim yang mempublikasikan **trade-off**: setiap ambang yang dinaikkan juga
membuang pasar yang bisa dijual. Di Fabius ambang yang berlaku sekarang ada di [[Fakta Terukur]] §E:
`MAX_TOP10` 45 %, `MIN_LOCK` 20 %, `MAX_BUNDLER` 30 %, `MIN_HOLDER` 60, `MIN_LIQ_USD` 50.000,
`MIN_VOL_OVER_LIQ` 0,10 — dan baris itu sendiri menyebut asalnya: **diputuskan**.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| `top_10_holder_rate`, `bundler_rate`, `lock_percent`, `holder_count` per kandidat | `ADA` | ikut snapshot `universe/bsc-universe.jsonl`; ambang dinormalkan ke snapshot supaya hasil bisa dihitung ulang ([[03-Data/D5 - Record Schemas]]) |
| ambang yang **teruji terhadap hasil** | `TIDAK-ADA` | §E: empat ambang universe pertama masih perlu diuji; caranya di [[GAP2 - Uji Setiap Veto Terhadap Hasil]] |
| pembeda "ditolak" vs "tidak bisa dinilai" | `ADA-TAPI` | ada dua hitungan terpisah (`survivable_count` vs `fully_evaluated_count`, [[03-Data/D5 - Record Schemas]]) dan ada catatan di `tools/screen_universe.py` soal baris tanpa field perilaku — tapi **belum** dipakai untuk mengkalibrasi |
| keamanan kontrak (saudara dekat) | `ADA` | `tools/security_gate.py`; terukur 5/5 kandidat membalas: 4 `OK` + 1 `UNMEASURED` (§F) |
| riwayat field ini untuk backtest | `TIDAK-ADA` | tautan vendor tidak mengembalikan nilai lama; satu-satunya masa lalu adalah snapshot yang kami buat sendiri |

## Uji di Fabius

Jalurnya nyata: `python -X utf8 tools/screen_universe.py` (ringkasan + `tools/out/screen_report.json`)
dan `--windows`. Filosofi alatnya sudah benar — ia mencetak **angka penolakan**, bukan angka cuan,
dan mencatat apa yang terjadi pada token yang **DITOLAK** maupun yang lolos. Yang belum ada adalah
verdiknya, dan bentuknya sudah ditulis di [[GAP2 - Uji Setiap Veto Terhadap Hasil]]:

1. Untuk tiap veto, bandingkan hasil token yang kena veto vs yang lolos, pada **jam dan universe yang
   sama**; hasil = return bersih 4 jam dari bar kami, kontrol = **arah acak pada token & jam yang
   sama** (§B).
2. **Pisahkan yang tidak bisa dinilai dari yang ditolak** sebelum satu angka pun boleh dipakai.
   Ini bukan kehati-hatian: [[06-Results/02 - Thresholds]] mengukur bahwa pada satu jendela
   sejumlah baris **tidak punya field perilaku sama sekali** dan sebagian gugur **tanpa satu pun
   alasan risiko** — kalau mereka dihitung sebagai "penolakan yang benar", yang sedang dikalibrasi
   adalah kegagalan penggabungan sumber, bukan risiko. (Angka detailnya ada di halaman itu, **bukan**
   di [[Fakta Terukur]] → jalankan ulang sebelum dikutip.)
3. Satu sampel per (token, jendela tak tumpang-tindih), `n >= 20`, BH α 0,10 lintas veto, gross di
   atas **59 bps** (§D), fold terbaik dibuang.
4. Veto yang ternyata tidak memprediksi hasil yang lebih buruk **harus dicabut**, dan itu dicatat.

## Batas dan mode gagal

- **Ambang yang belum diuji meniru ambang yang punya alasan.** `45 %` dan `20 %` terasa tegas;
  tidak ada satu pun run di repo ini yang menunjukkan mereka memisahkan token yang jelek dari yang
  baik. Itu lubang yang punya halaman sendiri, bukan detail kaki-kaki ([[EV6 - Kalibrasi Ambang Terhadap Hasil]]).
- **Null bukan bersih.** Field kunci yang tidak terukur harus menjadi `UNMEASURED`, bukan lolos
  diam-diam — persis pola yang sudah kami tangkap di ④ (§F: `is_honeypot=None` tidak dihitung bersih).
- **Definisi vendor bukan definisi kami.** `bundler_rate` adalah kesimpulan vendor tentang siapa
  bundler; kami tidak bisa menghitung ulang kriterianya dari data yang kami simpan.
- **Lock bisa palsu atau kadaluarsa**; top-10 bisa berisi alamat burn, kontrak, dan custodian —
  konsentrasi tinggi tidak selalu berarti satu orang bisa menjatuhkan harga.
- **Setiap ambang punya ongkos peluang.** Membuang ⑥ (kapasitas keluar) berarti keputusan hari ini
  aman dan besok tidak bisa dijual; ini pasangan langsung dari [[FD3 - Likuiditas dan Dampak Harga]].
- **Skema snapshot tidak sebanding.** `survivable_count` sebelum dan sesudah perubahan skema tidak
  boleh disatukan dalam satu deret; analisis wajib menyebut nomor skema ([[03-Data/D5 - Record Schemas]]).
- **Duplikasi:** `MIN_VOL_OVER_LIQ` mengukur hal yang sama dengan konfirmasi volum
  ([[V1 - Konfirmasi Volum dan Money Flow]]); jangan dihitung sebagai dua konfirmasi.

## Tingkat bukti

`T1` untuk bentuk metrik (dipakai luas, definisinya tidak dibakukan satu pemilik) · `T0` untuk
**angka** ambangnya (diputuskan, belum ada run yang membelanya) · `T2` untuk klaim vendor bahwa
`bundler_rate` adalah deteksi, bukan opini · untuk Fabius: filter ini **jalan** di pipeline
(§E + `tools/screen_universe.py`), tapi **belum diuji terhadap hasil** — jadi ia sah disebut
kebijakan, tidak sah disebut edge.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami menolak kandidat berdasarkan konsentrasi, bundler, lock, jumlah holder dan
  ketebalan keluar; ambangnya kami tetapkan sendiri dan kami belum membuktikan bahwa masing-masing
  punya isi."
- **Dilarang:** "filter kami membuat universe aman" · "top10 < 45 % terbukti memprediksi token yang
  hidup" · "token yang lolos screener adalah kandidat bagus" (lolos ≠ bagus; itu arti kolom yang
  sering dibalik) · "vendor mendeteksi bundler jadi kami mendeteksi bundler".

**Terkait:** [[ST6 - Aliran On-Chain Fabius]] · [[O4 - Active Addresses dan Pemakaian Gas]] ·
[[01-Agent/A3 - One-Way Gates]] · [[EV6 - Kalibrasi Ambang Terhadap Hasil]] · [[PL2 - Menyaring Universe]]

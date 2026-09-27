---
tags: [tk, tk-sinyal, "O2"]
---

# O2 - MVRV, SOPR dan NUPL

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"Strategi Berbasis On-Chain & Data Crypto Spesifik"
(baris "MVRV, SOPR, NUPL (on-chain valuation metrics)") — daftar topik, bukan fakta; status Fabius
dari [[Fakta Terukur]] §C

**Ringkas:** tiga rasio yang menjawab pertanyaan yang sama dari sisi berbeda: *siapa sedang untung,
dan berapa besar keuntungannya belum ditarik*. MVRV membandingkan nilai pasar dengan nilai
perolehan seluruh pasokan; SOPR melihat untung yang baru saja direalisasi; NUPL menempatkan untung
belum terealisasi di skala −1..+1. Semuanya butuh **riwayat per-unit-pasokan**, dan itulah yang
membuatnya mati di universe Fabius: kami menilai token yang sebagian berumur jam, bukan aset
berumur satu dekade.

## Definisi yang bisa dihitung

```
realized_cap(t)  = Σ_qty  qty(unit) × harga_terakhir_unit_itu_berpindah(<= t)
MVRV(t)          = market_cap(t) / realized_cap(t)                    # 1,0 = modal pas-pasan
SOPR(t)          = Σ nil_ai keluar pada t / Σ nil_ai masuk (biaya perolehan) ; versi split:
                   SOPR+ = hanya pengeluaran dengan rasio > 1, SOPR− = hanya < 1
NUPL(t)          = (Σ unrealized_profit − Σ unrealized_loss) / market_cap(t)   # ∈ [-1, 1]
```

Yang ketiganya tangkap **bukan** arah, melainkan **distribusi posisi untung**: MVRV tinggi = banyak
pemegang di atas air (bahan bakar jual), SOPR > 1 yang bertahan = kerugian sudah dihabiskan, NUPL
= fraksi aset yang belum terealisasi. Tidak ada satu pun yang memuat pesanan beli.

## Cara pakai yang diklaim

Diklaim oleh analis on-chain dan vendor metrik (Glassnode/Nansen-style dashboard): jual saat MVRV
di zona historis atas, tambah saat NUPL negatif (semegang rugi = tidak ada yang tersisa untuk
dijual), konfirmasi belokan saat SOPR kembali menembus 1,0. Horizon yang dipakai pembuat klaim =
harian–mingguan, sering dengan ambang "zona" dari percentile sejarah 1–4 tahun. **Klaim ambangnya
tidak pernah dibakukan oleh pemiliknya**: tidak ada satu pun angka percentile yang disepakati dua
vendor, dan itu sebabnya catatan ini menulis definisi, bukan "ambang yang benar".

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| MVRV / SOPR / NUPL itu sendiri | `TIDAK-ADA` | §C: tidak kami punya sama sekali |
| riwayat transfer per-unit-pasokan + biaya perolehan per chain | `TIDAK-ADA` | tidak ada jalur di repo; `universe/record_wallet_flow.py` menyimpan transaksi **maker berlabel**, bukan seluruh ledger |
| sejarah harga sepanjang umur aset | `ADA-TAPI` | Aster 9.599 bar ≈ 400 hari (§A) — tapi hanya untuk yang **ber-kontrak perp**; GMGN `token_kline` mentok 1.000 bar ≈ 41,6 hari, dan **0 bar untuk token gas** (§A) |
| biaya perolehan per maker (versi dompet dari SOPR) | `ADA-TAPI` | `tools/maker_ledger.py` mencoba merekonstruksi lot FIFO — §H melarang angka itu dikutip sebagai temuan |
| Dune sebagai sumber riwayat | `ADA-TAPI` | riwayatnya ada, tapi barisnya bisa di-*update* retro ([[Concepts/Point-in-Time vs Retro-updatable]]) → sah untuk statistik, tidak sah jadi saksi waktu |

## Uji di Fabius

Uji yang jujur butuh tabel realized-price **per chain** yang kami tidak punya; perintahnya **belum
ditulis** dan tidak bisa ditulis hari ini. Bentuk yang akan sah, supaya nanti tidak perlu dirediksi:

1. Hitung rasio hanya dengan transfer `<= t`; simpan definisi `unit` (UTXO vs saldo ERC-20) karena
   ERC-20 tidak punya "koin" yang bisa dilacak — itu sebabnya MVRV versi token EVM adalah
   **aproksimasi rata-rata**, bukan MVRV.
2. Label hasil = return bersih 4 jam dan 24 jam dari bar kami; pembanding = **arah acak pada token
   & jam yang sama** ([[Fakta Terukur]] §B).
3. Berlakukan `MIN_SAMPLES=20` non-overlap, BH α 0,10, gross di atas **59 bps** (§D), fold terbaik
   dibuang.

Versi "SOPR per dompet" yang sebenarnya sedang kami kerjakan ada di `tools/maker_ledger.py`, dan
keadaannya tercatat di §H: distribusi `|net|` per lot median **4.558,3 bps**, **71 %** lot di atas
2000 bps, maks **1.222.045,4** — angka-angka itu adalah **gejala alat yang rusak** (satuan harga,
arti `is_open_or_close`, nilai token yang belum di-mark-to-market), **belum boleh dipakai sebagai
temuan**. Diagnostiknya sengaja dipisah di `tools/maker_audit.py`.

## Batas dan mode gagal

- **Umur adalah syarat, bukan detail.** Rasio ini tidak terdefinisi secara bermakna untuk token yang
  lahir tiga hari lalu — tidak ada distribusi biaya yang cukup lebar. Universe kami sebagian besar
  justru kasus itu; `MIN_AGE_SEC` 24 jam (§E) sudah menyaring yang termuda, tapi tidak membuat
  sisanya bersejarah.
- **Realized cap bisa direkayasa.** Transfer diri sendiri, swap bolak-balik di pool kecil, atau
  wind trading mengubah biaya perolehan tanpa mengubah siapa pun jadi rugi atau untung.
- **Wrapped, bridged, dan stablecoin** menggandakan atau meniadakan pasokan, tergantung rantai yang
  dipakai sebagai penyebut. Satu token yang sama punya tiga MVRV.
- **Zona historis = survivorship.** Persentil dihitung dari aset yang masih hidup dan masih
  diperdagangkan; yang mati tidak masuk distribusi.
- Duplikasi: MVRV tinggi + volume turun mengukur hal yang sama dengan distribusi di
  [[S8 - Wyckoff]]; menambah keduanya tidak menambah informasi.

## Tingkat bukti

`T1` untuk definisi dan cara hitung (standar industri, tidak dibakukan satu pemilik) · `T0` untuk
klaim waktu "MVRV zona atas = jual sekarang" (tidak ada studi yang bisa kami periksa) · untuk
Fabius: **tidak dapat diuji** dengan data hari ini — jalurnya `TIDAK-ADA` (§C).

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami tahu mengapa metrik berbasis biaya-perolehan historis tidak bisa dipakai di token
  berumur jam, dan bentuk uji yang akan dipakai kalau suatu saat tabelnya ada."
- **Dilarang:** "Fabius memakai MVRV/NUPL" · "MVRV token ini masih rendah jadi masih ada ruang" ·
  "maker kami untung rata-rata ribuan bps" (itu angka §H yang belum sehat, dibaca sebagai hasil).

**Terkait:** [[O1 - Exchange Inflow dan Outflow]] · [[O5 - Whale dan Kohor Smart Money]] ·
[[O7 - Token Unlock dan Vesting]] · [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]

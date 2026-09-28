---
tags: [tk, referensi]
---

# Sumber dan Jangkauan

**Sumber:** `vault/TradingKnowledge/Resources.txt` (daftar bahan belajar, transkrip model) ·
probe 28 Sep 2026 02:03–02:06Z: `_research/probe_tk_sources.py` + `_research/probe_cex_depth.py`
*(workspace — keduanya alat ukur, bukan klaim produk)*

**Ringkas:** dua hal yang mudah tertukar dan harus dipisah di halaman ini. `Resources.txt` adalah
daftar **tempat belajar** (kanal YouTube, blog, kursus, forum) — bukan daftar **sumber data**.
Tidak satu pun isi daftar itu kami **baca**: 99 catatan di lapisan ini dibangun dari dua transkrip
(`Plan.txt`, `QuantTrading/Info1.txt`) sebagai daftar topik, dari rekaman kami sendiri sebagai
fakta, dan dari pengetahuan pasar standar yang **dibukukan apa adanya** sebagai `T1` atau
"pengetahuan standar — tidak ada rujukannya di repo ini". Yang baru terjadi hari ini adalah
**probe jangkauan** terhadap bagian daftarnya yang berupa penyedia data - dan satu barisnya
membatalkan rencana kita.

## Status tiap kelas di `Resources.txt`

| kelas | contoh di daftar | status kami | apa artinya buat catatan |
|---|---|---|---|
| YouTube | The Trading Channel, ICT, Rayner Teo, QuantPy, Robot Wealth, Swedish Investor | **tidak dibaca** (builder: "gapapa gausah") | tidak ada satu pun catatan yang mengutipnya; tidak akan ada |
| Blog / referensi konsep | Investopedia, BabyPips, QuantInsti, Binance/Bybit Academy | **tidak dibaca** | definisi di `03-Sinyal/` ditulis sebagai rumus yang bisa dihitung, bukan sebagai kutipan; itu memang lebih kuat dari kutipan untuk alat yang harus menghitung ulang |
| Kursus / platform | QuantConnect, Quantra, Coursera, Udemy, ICT Mentorship | **tidak dibaca** (docs-nya `200`, tapi tidak ada yang kita sedot) | tidak mengubah satu pun tingkat bukti |
| Komunitas | r/algotrading, Discord, TradingView community, GitHub awesome lists | **tidak dibaca** | satu-satunya yang relevan secara metode (`awesome-quant`) masih bisa dibaca kapan pun; tidak menaikkan apa pun yang hari ini `T1` |
| **Penyedia data** | Coinglass, Hyblock, Glassnode, CryptoQuant, Dune, Binance/Bybit/OKX | **DIPROBE 28 Sep** | ini bagian yang mengubah `## Butuh data` di catatan lain - tabel di bawah |

## Hasil probe jangkauan (dibaca ulang 28 Sep, laptop ini)

| sumber | jawaban | artinya |
|---|---|---|
| Dune | sudah dipakai sejak lama | `ADA` (lihat [[03-Data/D4 - Dune]]) - satu-satunya di daftar itu yang benar-benar sudah kami konsumsi |
| Glassnode `…/mvrv` | `401 Authorization Required` | **hidup, butuh akun** → `O2` tetap `TIDAK-ADA`; jangan ditulis "mati" |
| CryptoQuant `…/exchange/reserve` | `401 unauthorized` | sama → `O1` tetap `TIDAK-ADA` |
| Coinglass (dua path yang saya tebak) | `404 Not Found` dari aplikasinya | **path saya yang salah, bukan layanannya mati** - tidak boleh dicatat sebagai bukti apa pun tentang Coinglass |
| Hyblock `api…/v1/indicators` | `URLError` timeout 42,5 s | belum bisa disimpulkan dari satu respons; ulangi sebelum menulis |
| TradingView scanner | `200` dengan harga BNB | live sebagai charting; tidak ada jalur data yang kita andalkan |
| Binance / Bybit / OKX | **`200` semua**, dengan body nyata | **membatalkan baris §C** yang mencatatnya mati per 24 Sep |
| GitHub API (awesome-quant) | `200` | tidak kita pakai sebagai sumber metode; tidak menaikkan bukti apa pun |

Angka kedalamannya (funding `66,3 hari` per 8 jam dari Bybit, `33,0 hari` dari OKX, OI `20,8 hari`
per 1 jam dari Binance, bar spot `41,6 hari`) ada di **[[Fakta Terukur]] §A.5** - jangan disalin ke
sini, halaman itu pintu angkanya.

## Yang berubah karena probe ini

- **`U2 - Funding Rate dan Basis`**: histori funding pindah dari `TIDAK-ADA` ke `ADA-TAPI`.
  Intervalnya tetap 8 jam, jadi dia **tidak** bisa jadi fitur per-bar - tetap veto rezim.
- **`U1 - Open Interest`**: histori OI sekarang ada tapi jendelanya 30 hari - cukup untuk uji
  "OI naik sebelum gerakan", tidak cukup untuk walk-forward 400 hari.
- **`U3 - Level Likuidasi dan Cascade`**: **tidak berubah**. Probe ini tidak menemukan satu pun
  jalur likuidasi tanpa akun; statusnya tetap `TIDAK-ADA`.
- **P13** berubah bentuk: bukan "mulai rekam funding per jam dan tunggu kalender", tapi
  **"sedot mundur ±66 hari lalu rekam tambahan"** - lihat [[GAP5 - Urutan Kerja dan Bayarnya]].
- **`QT12 - Stack Data dan Perkakas`**: daftar "mati dari mesin ini"-nya harus dibaca dengan
  tanggal; matriks egress ini berubah dalam empat hari.

## Batas halaman ini

- Ini **bukan** klaim bahwa metode di lapisan ini sudah diverifikasi terhadap literatur. Sebagian
  besar `T1` tetap `T1`: dipakai luas, tidak kami uji. Membaca Investopedia tidak menaikkan tangga
  itu; menjalankan `tools/backtest.py` yang menaikkan.
- Probe ini **workspace**: jalurnya hidup dari laptop builder dan bisa jadi berbeda dari runner
  GitHub (`06-Results/03` baris 15 sudah mencatat pasangan sumber×jaringan). Sebelum jalur apa pun
  dijadikan rekaman produk, ulangi dari kedua jaringan.
- Satu respons `404`/`timeout` bukan vonis - itu kesalahan saya yang paling mahal di halaman ini
  (saya hampir menulis "Coinglass mati" karena menebak path).

**Terkait:** [[Fakta Terukur]] §A.5/§C · [[Aturan Subtree]] · [[QT12 - Stack Data dan Perkakas]] ·
[[U2 - Funding Rate dan Basis]] · [[U1 - Open Interest]] · [[GAP4 - Yang Tidak Bisa Diuji Karena Data]] ·
[[GAP5 - Urutan Kerja dan Bayarnya]]

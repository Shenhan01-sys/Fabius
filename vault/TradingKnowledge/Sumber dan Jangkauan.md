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

Angka kedalamannya (funding `66,3 hari` per 8 jam dari Bybit, `97,7 hari` dari OKX, OI `20,8 hari`
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

## Referensi yang benar-benar dibaca (28 Sep 2026)

Aturan [[Aturan Subtree]] #3: klaim pihak ketiga butuh pemiliknya. Enam alamat di bawah **dipanggil
sendiri** hari ini dan metadatanya cocok dengan yang tercantum; itu menaikkan catatan yang
mengutipnya dari `T1` (praktik umum, tidak teruji oleh kami) ke `T2` (ada literatur, **tidak kami
reproduksi**). Bukan `T3` - `T3` hanya untuk angka dari run kita sendiri.

| # | rujukan | alamat / DOI | apa yang dia pegang di lapisan ini |
|---|---|---|---|
| 1 | Schmeling, Schrimpf, Todorov — *Crypto Carry*, BIS Working Paper 1087 (2023) | `https://www.bis.org/publ/work1087.htm` | abstraknya dibaca: carry crypto rata-rata **> 10 %/tahun**, puncak ±**60 %**, digerakkan permintaan ritel akan leverage + modal arbitrase yang langka, dan **carry tinggi memprediksi crash**. Rujukan untuk [[U2 - Funding Rate dan Basis]], [[QT6 - Funding dan Basis Arbitrage]], [[U3 - Level Likuidasi dan Cascade]] |
| 2 | Bollen, Mao, Zeng — *Twitter mood predicts the stock market* (2010; J. Computational Science 2(1), 2011, hlm. 1–8) | arXiv `1010.3003` | satu-satunya klaim "sentimen sosial **memprediksi**" yang punya uji terkenal; dipakai di [[M2 - Sentimen Sosial dan Ekstraksi LLM]] bersama batasnya (efek kecil, pasar lain, replikasi lemah) |
| 3 | Bailey & López de Prado — *The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality* | SSRN `10.2139/ssrn.2460551` | dasar [[QT4 - Overfitting dan Validasi]] dan [[EV3 - Signifikansi dan Multiple Testing]]: Sharpe hasil pencarian tidak boleh dilaporkan sebagai estimasi tanpa mengurangi jumlah tes — tepat lubang `passed: 5` tanpa nama di [[06-Results/08 - Carry Study]] / P12 |
| 4 | Park & Irwin — *What do we know about the profitability of technical analysis?*, J. Economic Surveys (2007); kawannya yang bebas-snooping SSRN `10.2139/ssrn.722264` (2005) | DOI `10.1111/j.1467-6419.2007.00519.x` | alamat rujukan keluarga `S*`/`I*`: profitabilitas analisis teknikal **sudah disurvei** dan hasilnya tidak satu-arah. Kami memakai keberadaannya sebagai alamat, bukan mengutip kesimpulannya kata-per-kata |
| 5 | Carta & Conversano — *Practical Implementation of the Kelly Criterion*, Frontiers in Applied Math. & Statistics (2020) | DOI `10.3389/fams.2020.577050` | penyangga [[FD6 - Ukuran Posisi]]: Kelly penuh berlebihan di dunia nyata; fraksional karena estimasi salah, bukan karena rendah hati |
| 6 | MacLean, Thorp, Zhao, Ziemba — *How Does the Fortune's Formula Kelly Capital Growth Model Perform?* (2011) · Busseti, Ryu, Boyd — *Risk-Constrained Kelly Gambling* (2016) | DOI `10.3905/jpm.2011.37.4.096` · `10.3905/joi.2016.25.3.118` | untuk kalimat "Kelly optimal **kalau** probabilitasnya benar; tidak ada yang benar itu" |

**Konfrontasi yang harus disebut, bukan dihindari.** Rujukan #1 bilang carry crypto **> 10 % per
tahun**; alat kami ([[06-Results/08 - Carry Study]] §C) mengukur funding per 8 jam di Bybit/OKX dan
mendapat **1,3–2,2 bps/hari ≈ 5–8 % per tahun**. Itu dua hal berbeda: mereka **basis futures-spot**
yang diannualkan (termasuk 2021 saat leverage ritel meluap), kami **funding rate** pada 97 hari
terakhir. Literatur tidak membatalkan angka kami dan sebaliknya — yang mereka bagikan cuma namanya.
Catatan mana pun yang memakai #1 wajib menulis yang mana yang dimaksud.

**Cara mematahkan tabel ini (jangan percaya halaman ini):** tiap baris bisa dipanggil ulang —
`https://api.crossref.org/works/<doi>`, `https://arxiv.org/abs/1010.3003`,
`https://www.bis.org/publ/work1087.htm`. Kalau metadata di halaman sumber tidak cocok dengan baris
ini, barisnya yang dicabut.

## Referensi yang dibaca 29 Sep 2026 - lapisan mikrostruktur (S1-S9)

Dipisah dari daftar 28 Sep karena kelasnya beda: ini yang membatasi cara kami **membaca buku
order**, bukan yang membiayai fitur lain. Yang ditandai ✔ kutipannya saya ambil sendiri dari
halaman penerbit/arXiv; yang (agen) dibaca agen riset hari yang sama dan **belum diverifikasi
ulang** - perlakukan sebagai perlu dicek, bukan sebagai sudah dicek. Pemetaan lengkap + yang
tidak terverifikasi ada di [[08-Backlog/04 - Riset Teori (Sitasi)]].

| ✔ | rujukan | alamat | apa yang dia pegang di lapisan ini |
|---|---|---|---|
| ✔ | Cont, Kukanov, Stoikov — *The Price Impact of Order Book Events* | arXiv `1011.6402v3` | OFI = **jumlah atas event**, bukan selisih snapshot; R² rata-rata **65 %** pada Δt = **10 detik**; ""fit meningkat dengan Δt"" = kecocokan **kontemporer**; λ̄ **0,98** → pegangan V4/GAP1 |
| ✔ | Gould, Bonart, Donnelly, McDermott — queue imbalance | arXiv `1512.03492v1` | horison = **pergerakan mid-price berikutnya**, bukan jam dinding; AUC OOS large-tick **0,752-0,805**, small-tick **0,581-0,642**, null 0,5 → V4, FD9 |
| ✔ | Lei, Li — *Do Stop-loss Strategies Add Value…?* | Financial Services Review 18(1):23-51 (2009), `openjournals.libs.uga.edu/fsr/article/view/4933` | ""neither reduce nor increase investors' losses … risk reduction rather than return improvement" → FD7, halaman 24 |
| ✔ | Osler — *Stop-loss Orders and Price Cascades* | NY Fed Staff Report 150 (2002) | ""unusually rapid" di level tempat stop menumpuk; respons stop > take-profit → FD7, dan alasan `i` (gap isi) bukan nol (P45) |
| ✔ | Ke, Lin — *An Improved Version of VPIN* | Critical Finance Review 6(2):357-376 (2017), DOI `10.1561/104.00000046` | VPIN **tidak stabil pada bucket kecil dan kejadian jarang** — dua hal yang justru dihasilkan granularitas kami → V3, E18 |
| (agen) | Cont, Cucuringu, Zhang — integrated OFI; + preprint OFI Level-1 bar 10 s | arXiv `2112.13213v4`; SSRN 7053198 | **1-minute-ahead R² OOS NEGATIF** (−0,37 … −0,36); OFI 10 s: Sharpe gross **+0,981 → net −1,726**, biaya ~164× edge → FD4, FD9. **Catatan: kami sempat menyebut "Gu & Kelly (2014)" sebagai sumber rumus imbalance-nya; paper itu TIDAK ketemu di Crossref maupun arXiv, jadi nama itu dicabut dan rumus dipegang oleh paper di kolom alamat** |
| (agen) | Xu, Gould, Pedersen — *Deep OFI* (MLOFI); Kolm, Westray | arXiv `1907.06230v2`; SSRN 4568641 | level diperlakukan **setara** (tanpa bobot jarak), kontribusi marginal per level mengecil → V4 (alasan `util20` kami bukan kanonis) |
| (agen) | Albers, Cucuringu, Howison, Shestopaloff — microprice + maker contra | arXiv `2502.18625v2` | definisi microprice `W = I·pa + (1−I)·pb`; maker layak bergerak **kontra** imbalance dominan → V4, T5 |
| (agen) | Almgren, Thum, Hauptmann, Li — *Direct estimation of market impact* | `cis.upenn.edu/~mkearns/finread/costestim.pdf` | α **0,891 ± 0,10** (permanen ~linear), β **0,600 ± 0,038** (sementara), γ **0,314 ± 0,041**; **R² "umumnya di bawah satu persen"** → FD3, T6 |
| (agen) | kegagalan likuiditas nyata di DEX perp | arXiv `2603.09164`, `2512.01112`, `2607.27070` | depth-100bps −75 % dalam 36 jam; `realized = 0,42 + 1,12 × predicted` (model underpredict); sinyal peringatan **tidak invariant antar-cascade** → U3, FD3 |

**Yang berubah di lapisan ini karena bacaan itu** (bukan karena selera):
- `V4` turun kelas dari "tidak bisa diuji" menjadi **bisa diuji sebagai state, bukan sebagai
  aliran** - dan karena itu E16 (halaman 22) dikunci untuk `bi5` saja, dengan `pi`/microprice
  dilaporkan sebagai pembacaan tambahan, bukan sebagai kandidat yang dipilih setelah lihat hasil.
- `V3` **punya hasil**: E18 = NOL untuk rasio berimbang dari agresor betulan, bukan dari label
  candle. Keluarga delta tidak mati - yang mati adalah klaim "agresor → arah" pada horison menit
  di substrate ini.
- `FD7` berhenti jadi daftar jarak (ATR/k) dan mulai mencantumkan **syarat perlu lock** beserta
  hasil E17: pada 1-4 bar/jam stop tidak tersentuh, jadi dia *belum bisa dinilai* - bukan salah.
- `FD9` dapat jawaban operasional: horison di literatur = **satu pergerakan harga**, dan anggaran
  biaya kami (`≤ ~21 bps` spread) yang memutuskan timeframe, bukan sebaliknya.
- `FD3`/`FD4` sekarang punya angka internal (dampak 0,00 median karena salah satuan; spread
  terukur 0,01-519 bps) yang membuat model x·y=k kami bisa dituduh, bukan dipercaya buta.

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

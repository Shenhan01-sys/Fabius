---
tags: [backlog, riset, sitasi]
---

# 04 - Riset Teori (Sitasi)

**Bagian dari:** [[08-Backlog/03 - Epik Teori Baru]]
**Aturan halaman ini:** sebuah angka/klaim masuk sini **hanya** kalau sumbernya benar-benar dibaca,
dengan URL dan tanggal akses. Yang tidak ketemu sumbernya ditulis **"tidak terverifikasi"** - bukan
dihapus, bukan ditulis sebagai kemungkinan. Ini pagar yang mahal: tiga dari tujuh koreksi kami
(F-D37, F-D39, F-D46) adalah angka yang masuk dokumen sebelum penggarisnya diperiksa.

## 1. Status

Empat agen riset dijalankan 29 Sep 2026 ±09:3xZ atas empat topik: (a) order book / order flow
imbalance, (b) microprice & queue imbalance, (c) VPIN / order-flow toxicity / smart-money
clustering, (d) matematika stop-loss & trailing stop dengan biaya. **Isinya belum disalin ke sini
pada saat halaman ini dibuat** - halaman ini ada supaya tautannya jujur: kalau bagiannya masih kosong,
ia memang kosong, bukan hilang.

## 2. Entri terverifikasi (dibaca langsung dari teks sumbernya, 29 Sep 2026)

### S1 — Order flow imbalance = ALIRAN, bukan snapshot. Dan itu membatasi T1.

**Sumber:** Cont, Kukanov & Stoikov, *The Price Impact of Order Book Events*,
arXiv:1011.6402v3 — https://arxiv.org/abs/1011.6402 , body:
https://ar5iv.labs.arxiv.org/html/1011.6402 (diakses 29 Sep 2026)

Kutip terverifikasi:
> "We use a uniform grid in time ... with a timescale `t_k - t_{k-1} = \Delta t = 10` seconds to
> compute the price changes and the order flow imbalances."
> "... an average `R^2` of **65%**." (Tabel 2: grand mean R² = 65 %)
> "The fit of our model **generally increases with `\Delta t`**, but the rest of the results stays
> the same." (rentang uji: 10 quote updates ≈ <0,5 detik sampai **10 menit**)
> estimates `\hat{\lambda}` ... grand mean **0,98** (dampak berbanding terbalik dengan kedalaman)

**Untuk kita.** Tiga hal, dan yang pertama paling mahal: OFI didefinisikan sebagai **jumlah atas
event** buku order (`e_n` per event, dilihat dari perubahan best bid/ask + kuantitasnya). Ia **tidak
bisa dipulihkan dari dua endpoint** - selisih snapshot mencampur update quote dengan trade yang
memakan likuiditas. Jadi `bi1/bi5/bi20` di ⑨ kami adalah **state imbalance**, bukan OFI, dan tidak
boleh disebut OFI. Kedua: "fit meningkat dengan \Delta t" adalah **kecocokan kontemporer**
(ΔP pada interval yang sama), bukan kemampuan **meramal** ke depan - dua hal yang berbeda di horison
kami dan sering dicampur di materi promosi. Ketiga: angka 65 % itu di ekuitas AS dengan TAQ
Level-1; memindahkan besarnya ke perp crypto micro-cap kami bukan hal yang sah dilakukan tanpa
mengukur.

### S2 — Horizon literatur bukan jam dinding: "satu pergerakan mid-price berikutnya"

**Sumber:** Gould, Bonart, Donnelly & McDermott, arXiv:1512.03492v1 —
https://arxiv.org/html/1512.03492v1 (diakses 29 Sep 2026)

Kutip terverifikasi (abstrak): "whether the bid/ask **queue imbalance** in a limit order book
provides significant predictive power for the direction of **the next mid-price movement**".
Skema sampling-nya: imbalance diukur pada waktu `t̃_i` yang dipilih "**uniformly at random in the
open interval (t_{i-1}, t_i)**", dengan `t_{i-1}, t_i` dua waktu mid-price berubah.
Angka out-of-sample yang saya baca dari body: **AUC 0,752-0,805 untuk large-tick** (MSFT 0,762 ·
INTC 0,798 · MU 0,752 · CSCO 0,805 · ORCL 0,770) vs **0,581-0,642 untuk small-tick** (GOOG 0,581 ·
AMZN 0,642 · TSLA 0,602 · PCLN 0,583 · NFLX 0,627); null model **0,5**.

**Jawaban untuk pertanyaan "timeframe-nya gimana".** Di literatur, horizon sinyal buku order **tidak
dinyatakan dalam menit** - dia dinyatakan dalam *jumlah pergerakan harga*. Satu pergerakan mid-price
pada BTC/ETH perp adalah orde detik; pada micro-cap yang bukunya tipis, pergerakan berikutnya juga
bisa detik, tapi **kitanya tidak melihatnya**: kami merekam satu snapshot per ±200 detik. Jadi
"5 menit" bukan timeframe yang lebih panjang dari horizon si teori - ia **20-100× lebih kasar**, dan
yang kami ukur adalah versi rata-rata dari sinyal yang aslinya bekerja di dalam celah antara dua
rekaman kami. Ini bukan alasan untuk tidak menguji; ini alasan untuk **tidak kaget kalau hasilnya
nol**, dan untuk tidak menyimpulkan teorinya salah dari nol itu.

### S3 — Microprice: terukur sebagai **referensi nilai wajar**, bukan sebagai prediktor pada data kami

**Sumber:** Stoikov-definisi seperti dipakai di Howison, Raval & Shakhmuradov, arXiv:2502.18625v2 —
https://arxiv.org/html/2502.18625v2 (diakses 29 Sep 2026): microprice = kuotasi yang
dibobot **kebalik** dari sisi yang lebih tebal (`(B·p^a + A·p^b)/(B + A)`), plus catatan bahwa
maker yang baik justru bergerak **kontra** imbalance dominan.

**Untuk kita:** `I = Q_b/(Q_b+Q_a)`, `W = I·p_a + (1-I)·p_b` semuanya terbentuk dari L1 snapshot
kami - jadi bisa dihitung. Yang **tidak** bisa: mengkalibrasi fungsi `g(I,S)` versi Stoikov (butuh
waktu-jam per pergerakan harga, τ_i) pada cadence 200 detik. Kegunaan jujurnya: **menilai apakah
harga fill/exit kami masuk akal** (deviasi dari `W` = biaya riil yang selama ini tidak kami hitung),
bukan meramal arah. Itu naik kelas jadi alat audit, bukan sinyal - dan itulah T5 yang sebenarnya.

### S4 — Biaya adalah bagian yang membunuh, dan sudah ada angka kotornya

**Sumber (preprint, status jujur):** SSRN 7053198 - OFI Level-1 pada bar 10 detik, 12 instrumen AS:
IC +0,0044 (t pooled 3,26) tapi **OOS IC +0,0022**; **Sharpe gross +0,981 → net −1,726**;
penulis melaporkan biaya ≈ **164×** besarnya edge, dan IC pada 5 m/10 m (+0,0148/+0,0161)
**tidak lolos koreksi multiple testing**. Tidak peer-review - karena itu nomornya kami pakai sebagai
**peringatan struktur**, bukan sebagai besaran.

Gandaria, Gu & Liu, arXiv:2112.13213v4 (S&P 100, 2017-2019): **R² out-of-sample 1 minute-ahead
NEGATIF** (FPI[1] −0,37; FPII −0,36; AR −0,36). Jadi bahkan di equitas AS, "satu menit ke depan"
sudah bukan wilayah di mana imbalance buku menang.

**Untuk kita:** `tools/cost_budget.py` (E19) memberi ambangnya dalam satuan kami sendiri:
harapan median +79,8 bps dikurangi ongkos tetap 59,0 bps → **ruang spread ≈ 21 bps**. Itu bukan
target, itu batas atas dari berapa lebar buku boleh untuk strategi 5 menit kami.

### S5 — Stop cluster: alasan trigger tidak terisi di harga trigger

**Sumber:** Osler, NY Fed Staff Report 150 (2002) - https://www.newyorkfed.org/research/staff_reports/sr150.html
dan J. Int. Money & Finance 24(2):219-241 (2005) - klaim terverifikasi: tren "**unusually rapid**"
saat harga menyentuh level tempat stop-loss mengumpul, dan respons stop-loss **lebih besar dan lebih
lama** daripada take-profit; signifikan per jam, bukan per hari.

**Untuk kita:** ini sandaran untuk kalimat di T2: **yang terisi bukan angka di trigger**. Pada cadence
200 detik, pergerakan cepat menembus level trailing justru terjadi di antara dua rekaman kami -
di area yang paling buta bagi alat kami.

### S6 — Stop-loss tidak mengubah harapan; yang diubah risikonya. (kutipan verbatim)

**Sumber:** Lei & Li, *Do Stop-loss Strategies Add Value for Individual Investors?*, Financial
Services Review 18(1):23–51 (2009) —
https://openjournals.libs.uga.edu/fsr/article/view/4933 (abstrak dibaca langsung 29 Sep 2026)

> "Our results indicate that these strategies **neither reduce nor increase investors' losses**
> relative to a buy-and-hold strategy once we extend security returns from past realizations to
> possible future paths. One unique stop loss mechanism, nevertheless, helps investors to reduce
> investment risk. These findings suggest that the value of stop loss strategies may come largely
> from **risk reduction rather than return improvement**."

**Untuk kita:** ini sandaran literatur untuk penurunan algebra di [[06-Results/23 - Gerbang Trailing]] §1 dan untuk bentuk vonis E17: yang boleh diklaim adalah perubahan **bentuk** distribusi
(`P(net ≤ −X)`, median), bukan kenaikan harapan.

### S7 — Stop yang berkerumun menghasilkan cascades, dan responsnya lebih besar daripada take-profit

**Sumber:** Osler, *Stop-loss Orders and Price Cascades in Currency Markets*, NY Fed Staff Report
150 (2002) — https://ideas.repec.org/p/fip/fednsr/150.html (abstrak dibaca langsung 29 Sep 2026)

> "Exchange rate trends are **unusually rapid** when rates reach exchange rate levels at which
> stop-loss order have been documented to cluster."
> "The response to **stop-loss orders is larger** than the response to take-profit orders, which
> generate negative-feedback trading and are therefore unlikely to contribute to price cascades."

**Untuk kita:** jawaban untuk `i` (slippage menembus bid saat trigger). Arahnya jelas: fill stop bukan
di trigger. Besarnya di venue kami **belum diukur** - dan tidak ada literatur yang memberi angka
spread untuk perp micro-cap BNB Chain, jadi itu tugas ⑨, bukan tugas pustaka.

### S8 — VPIN: versi primernya terbukti TIDAK STABIL pada bucket kecil

**Sumber:** Ke & Lin, *An Improved Version of the Volume-Synchronized Probability of Informed
Trading*, Critical Finance Review 6(2):357–376 (2017), DOI 10.1561/104.00000046 —
https://ideas.repec.org/a/now/jnlcfr/104.00000046.html (abstrak dibaca langsung 29 Sep 2026)

> "We show mathematically that Easley et al.'s VPIN metric **becomes unstable for small volume
> buckets and for infrequent informed trades**."

**Untuk kita:** granularitas data ⑦/⑩ kami membuat bucket-nya justru kasar DAN kejadiannya jarang -
dua syarat ketidakstabilan sekaligus. Artinya kalau E18/T3 mencoba varian VPIN, yang diuji adalah
versi yang literaturnya sendiri bilang tidak stabil; itu harus ditulis di halaman hasilnya, bukan
disembunyikan di belakang kata "VPIN-style".

### S9 — Order book crypto bisa menutup 75 % dalam sehari, dan model dampak salah prediksi fill

**Sumber (dibaca agen, belum saya verifikasi teksnya):** arXiv:2603.09164 (Hyperliquid, episode
10 Okt 2025): depth-100bps turun $1,12 miliar → $284 juta (−75 %) dalam 36 jam; market maker efektif
8,7 → 2,8; dan **`realized = 0,42 + 1,12 × predicted`** - model underpredict likuidasi nyata.
arXiv:2607.27070: 7 cascade, event $19 miliar; sinyal peringatan dini **tidak invariant antar-event**
(harga muncul di 5 dari 7, diam di 2 shock berita). arXiv:2512.01112: ADL menutup $2,1 miliar dalam
12 menit. **Status: angka ini dari agen riset; tandai "belum diverifikasi ulang" di setiap pemakaian.**

## 3. Yang TIDAK terverifikasi - dan karena itu tidak boleh dikutip

| klaim | status |
|---|---|
| "Gu & Kelly (2014), *Automating Across the Order Book*" | **tidak ketemu** di Crossref/arXiv/penelusuran; jangan tulis sitasinya di materi yang bisa diaudit. Definisi `(Q_b-Q_a)/(Q_b+Q_a)` yang mau kami pakai punya sumber lain (S1/S3), jadi tidak butuh nama itu |
| besarnya predictive power **state imbalance pada crypto micro-cap di horison 5-30 menit** | **tidak ada di literatur yang dibaca.** Yang ada: kontemporer 10 detik (S1), event-horizon large/small-tick equities AS (S2), 1 menit negatif (S4). Angka kami harus datang dari pengukuran sendiri - dan memang itu yang E16 lakukan |
| microprice/queue imbalance pada **sampling 200 detik** | tidak ada studi; tidak bisa disimpulkan dari yang dibaca |
| uji formal "jarak trailing < spread ⇒ rugi" | **tidak ada literatur yang saya temukan**; aritmatikanya kami turunkan sendiri di [[08-Backlog/03 - Epik Teori Baru]] §3 dan itu harus dibaca sebagai matematika kami, bukan temuan orang |
| Silantyev (2019) "trade-flow imbalance > book imbalance" | muncul dari ringkasan mesin pencari, **teksnya belum dibaca** - jangan dipakai sampai dibaca |
| isi buku Bouchaud/Lefebvre/Zenou dan paper quote-stuffing | belum dibaca; tidak dikutip |
| angka **effect size Chordia & Subrahmanyam** dan **Kyle (1985)** formal | abstrak/bibliografi terverifikasi, isi tidak - jangan kutip angka |
| spread (bps) untuk perp micro-cap BNB Chain | **tidak ada di literatur**; satu-satunya jalan adalah mengukur ⑨ - dan itu yang sekarang berjalan |

## 4. Terkait

[[08-Backlog/03 - Epik Teori Baru]] §4 · [[06-Results/22 - Buku Order, Terkunci Lebih Dulu]] ·
[[07-Testing/01 - Test Commands]]

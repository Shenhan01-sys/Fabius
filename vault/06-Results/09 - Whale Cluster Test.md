---
tags: [results]
---

# 09 - Whale Cluster Test

**Sumber:** `tools/flow_cluster_test.py` → `decisions/flow-cluster-20260928T060500Z.json`
(`rows_sha256=0x9db0a0adcb5d77…`) · dijalankan 28 Sep 2026 ±06:05Z

**Ringkas:** pertanyaan builder adalah "kohor smart money itu kan harusnya bikin prediksi kita
benar — bisa tidak jadi duit?" Ujiannya sekarang sudah jalan, atas rekaman kami sendiri.
Jawabannya dua lapis, dan dua-duanya penting: **kolaborasi tidak memisahkan** (K≥2 vs K=1 vs K≥5:
tidak ada yang lolos BH), **tetapi 80,6 % kandidat tidak bisa dinilai sama sekali** karena
harga keluarnya hilang dari sorotan. Yang kedua adalah temuan yang sebenarnya: kami belum punya
hak bicara soal ini bukan karena whale-nya tidak pintar, tapi karena **pengukurannya buta di
sisi keluar**.

## Yang diuji

`K(T,t)` = jumlah maker **berbeda** yang membeli token T pada `[t-30 m, t]` (feed ⑦ kami);
masuk = harga di baris transaksi itu sendiri; keluar = median `px` (harga pool yang kami tarik
sendiri) di `t+60 m ±15 m`; ongkos **59 bps** dari `tools/costs.py`; non-overlap per token;
kepala = median + bootstrap 4.000 (seed tetap) + tanda-uji eksak + BH α 0,10 lintas kelompok.

| kelompok | n | median net | CI 95 % | % posisi positif | % ≥ 20× | % harga diam | p |
|---|---|---|---|---|---|---|---|
| pembanding K=1 | 661 | −59,0 | [−59; −59] | **39,5 %** | 20,1 % | 21,6 % | 1,000 |
| kohor K≥2 | 61 | −59,0 | [−59; +23] | 39,3 % | 19,7 % | 18,0 % | 0,964 |
| kohor K≥3 | 21 | −59,1 | [−602; +431] | 38,1 % | 14,3 % | 4,8 % | 0,905 |
| kohor K≥5 | 24 | **+67,5** | [−1044; +1808] | **50,0 %** | 29,2 % | 4,2 % | 0,581 |
| cuaca (semua px→px) | 12.195 | −59,0 | [−59; −59] | **30,8 %** | 16,3 % | 0,0 % | 1,000 |

`verdict: TIDAK ADA KELOMPOK KOHOR YANG LOLOS BH`

## Tiga hal yang boleh dikatakan dari sini

1. **Kehadiran satu pembeli berlabel > rata-rata pool.** 39,5 % vs 30,8 % posisi positif — +8,7 pp.
   Ini bukan "whale pintar"; ini mekanisme: kami mencatat transaksi pada token yang *sedang*
   dipantau, dan yang sedang dipantau lebih sering naik dalam satu jam berikutnya. Angka ini
   mekanik dan tidak butuh klaim kecerdasan siapa pun.
2. **Kerumunan tidak menambah apa pun di atas itu.** K≥2 = 39,3 % (n=61). K≥5 memang 50 % —
   pada n=24, dengan CI median [−1044; +1808] dan p=0,58. Itu bukan efek, itu undian. **Inilah
   jawaban langsung untuk "kan cocokkan whale": pada data kami, mencocokkan *jumlah* whale tidak
   mengubah probabilitas apa pun.**
3. **Yang membedakan kita dari "analisis akurat" bukan sinyal, tapi sensor.** 3.958 kandidat;
   **3.191 (80,6 %) dibuang** karena tidak ada `px` pada jendela keluar. Yang terbuang itu
   bukan "tidak ada berita" — itu token yang **keluar dari sorotan**, dan secara sistematis itu
   kandidat yang mati. Jadi seluruh tabel di atas dihitung di atas 19 % sampel yang beruntung
   bisa dilihat akhir hayatnya. Proporsi "≥20×" yang cantik itu adalah sifat dari 19 % tersebut.

## Dan yang lebih sepele tapi sama mematikan: resolusi harga

21,6 % kejadian pembanding punya `gross` **persis 0,0 bps** — harganya tidak bergerak pada
presisi yang kami simpan. Untuk median, itu berarti "median = −ongkos" yang kalian lihat di
tabel **bukan kesimpulan pasar, tapi batas ketelitian alat ukur kita**. Kalau 1 dari 5 kejadian
tidak bisa membedakan 0 dari 0,05 %, maka edge yang kita cari (yang skalanya ±1–4 bps gross,
lihat §1 halaman ini dan `04 - Negative Results` §5b) secara harfiah ada di bawah noise floor
data kami.

## Apa yang harus dilakukan supaya pertanyaan ini bisa dijawab, bukan dihindari

| № | pekerjaan | kenapa ini yang memblokir |
|---|---|---|
| 1 | **Perekam harga keluar** (`watchlist`): begitu kita mencatat beli pada sebuah token, token itu ikut ditarik `px`-nya terus sampai 24 jam, walaupun ia keluar dari daftar panas | menghilangkan 80,6 % sensor. Tanpa ini, semua angka whale di repo ini adalah statistik di antara pemenang |
| 2 | Presisi harga: simpan harga mentah dari feed, jangan hasil pembulatan yang bisa diam | tanpa ini, edge di bawah ±5 bps tidak akan pernah terbedakan dari nol |
| 3 | Uji lagi pada horizon 240 m dengan jendela px yang ada (479 token cukup) | uji silang supaya bukan artefak horizon 60 m |

Ketiganya bukan "nanti setelah hackathon": №1 adalah satu berkas perekam baru + satu baris di
workflow yang sudah ada. Itu yang membuat Fabius akhirnya **tahu kapan dia boleh bicara** —
sekarang dia bahkan belum punya hak bilang "whale-nya salah", karena 4 dari 5 kejadian tidak
kelihatan akhirnya.

Baca ulang: `python -X utf8 tools/flow_cluster_test.py --horizon 60 --window 30 --ks 2,3,5`

**Terkait:** [[03-Data/D2 - Wallet Flow]] · [[06-Results/04 - Negative Results]] ·
[[06-Results/06 - Pre-registration Horizon]] · [[TradingKnowledge/O5 - Whale dan Kohor Smart Money]] ·
[[TradingKnowledge/Fakta Terukur]] §F/§H · [[TradingKnowledge/EV2 - Jebakan Backtest]] ·
[[TradingKnowledge/GAP3 - Yang Punya Data Tapi Belum Diuji]]

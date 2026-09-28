---
tags: [hasil]
---

# 15 - Teknikal Klasik Diuji

**Sumber:** `tools/technic_lab.py` → `decisions/technic-lab-20260928T155227Z.json` · spesifikasi
terkunci `decisions/prereg-technic-lock.json` (`sha=0x6032bda0…`, ditulis sebelum hasilnya dilihat)
· 28 Sep ±15:52Z · bahan: deret harga PERISTIWA dari aliran ⑦

**Ringkas:** builder bertanya apakah lapisan `TradingKnowledge` (Fibonacci, swing, scalping, moving
average) terpakai atau cuma rapi. Audit `_research/audit_ujian_pengetahuan.py` menjawab jujur:
**dari 86 catatan metode, 31 tanpa penanda "belum diuji", dan `04-Setup` berisi tujuh persona tanpa satu pun angka.** Satu aturan teknikal memang pernah diuji sebelumnya
(`tools/backtest.py`: gap SMA24 ±1 % searah `ret24`, di bar hourly majors) dan hasilnya nol -
momentum yang menyala semuanya dipadamkan gerbang |acf|. Sisanya belum. Malam ini alatnya ada.

## 1. Yang diuji, dan apa yang keluar

Horison 30 menit: 1.054 kejadian (8.581 ditolak karena tumpang tindih), pool mean winso **+218,0**,
median −44,7, `P(net ≥ +500) = 39,8 %`. Semua dibandingkan dengan **control acak dari pool yang
sama** (400 undian) - ambang "hidup" = mean di atas CI atas control.

| fitur (point-in-time) | n | mean winso (CI 95 %) | median | P≥500 | vs control | BH ekor |
|---|---|---|---|---|---|---|
| MA(20) > MA(50) | 136 | **−186,5** [−411,5; +36,1] | −59,3 | 22,1 % | di bawah (ambang +438,3) | - |
| RSI < 30 (jenuh jual) | 87 | +15,3 [−264,6; +304,3] | −58,5 | 34,5 % | di bawah (+525,8) | p=0,88 |
| RSI > 70 (jenuh beli) | 35 | −280,1 [−780,8; +232,7] | −61,9 | 31,4 % | di bawah | p=0,89 |
| MACD histogram naik | 97 | −225,7 [−497,5; +50,8] | −66,6 | 27,8 % | di bawah | p=1,00 |
| Bollinger bawah (reversion) | 49 | −240,2 [−630,8; +180,0] | −82,2 | 28,6 % | di bawah | p=0,97 |
| Bollinger atas (momentum) | 27 | −183,8 [−783,6; +446,0] | −64,0 | 37,0 % | di bawah | p=0,69 |
| **Fibonacci pullback 0,38-0,62** | 24 | **−548,3** [−1.188,0; +129,2] | **−1.265,5** | 29,2 % | di bawah | p=0,90 |
| **Breakout 60 m** | 27 | **−587,9** [−951,9; −201,4] | −59,6 | **3,7 %** | di bawah | p=1,00 |
| **Lonjakan volum 3×** | 26 | **−558,0** [−960,2; −141,6] | −249,9 | 15,4 % | di bawah | p=1,00 |
| Volatilitas rendah (bagian bawah) | 245 | −107,6 [−244,7; +23,1] | −59,2 | 18,8 % | di bawah | p=1,00 |
| Volatilitas tinggi | 245 | −3,1 [−197,5; +196,7] | −93,9 | 42,9 % | di bawah | p=0,15 |
| Golden cross | 12 | n<20 - TIDAK DIUJI | | | | |

Horison 120 menit (swing, 376 kejadian) mengulang pola yang sama: **nol** fitur di atas control,
nol lolos BH, dan `ma_tren` justru −400,0.

**Bacaan yang paling penting bukan "tidak ada yang bekerja", tapi mana yang Aktif merusak:**
membeli **breakout 60 menit** di universe ini memberi `P(≥+500 bps) = 3,7 %` (vs 39,8 % pool) dan
mean **−587,9 CI [−951,9; −201,4]** - CI-nya tidak melewati nol. Lonjakan volum 3× dan Fib pullback
searah sama. Ini bukan "tehniknya salah secara umum"; ini **instrumen kita**: kita melihat pool
setelah smart-money bergerak, jadi "price baru menembus tertinggi" itu sudah puncak, dan
"retrace 0,5" di token yang baru lahir satu jam adalah pisau jatuh.

## 1b. Satu hal yang membatalkan kesimpulan di atasnya

Angka `+218,0` untuk pool dan `+450,8` untuk kohort token muda dipotong oleh [[06-Results/16 - Harga Keluar yang Hilang]]: di kohort muda **80,6 % kejadian tidak punya satu pun baris harga keluar**, dan persentil-5 dari yang teramati sudah menyentuh lantai winsor (-2.000 bps). Mean itu angka korban selamat, bukan harapan. Karena itu urutan yang benar adalah **P33 (perbaiki pengukuran keluar) lalu P32 (teknikal di bar OHLC)**, bukan sebaliknya.

## 2. Batas yang menahan halaman ini

- **Bar kami bukan bar.** `technic_lab` memakai deret harga TRANSAKSI (peristiwa), bukan OHLC 1h/4h
  tempat Fibonacci/swing/MA biasanya didefinisikan. MA20/RSI14/Boll(20,2σ) di atas hitungan
  transaksi adalah adaptasi, dan itu harus disebut sebagai adaptasi - bukan sebagai "sudah menguji
  Fibonacci-nya Elliott".
- Ekor fitur dibatasi 320 transaksi terakhir per kejadian; jendela waktu 60 m tetap dipotong dari
  ekor itu. Untuk pool yang sangat ramai, 320 transaksi < 60 menit - jadi `fib_pullback`/`breakout`
  bisa mengidik dari horizon yang lebih pendek dari yang tertulis di spesifikasi.
- 24-49 kejadian untuk Fib/Bollinger/breakout: cukup untuk melihat tanda minus, **tidak** cukup
  untuk keputusan. Yang kuat di sini justru yang n-nya besar (MA 136, volatilitas 245).
- Satu jendela 51 jam, satu rezim.

## 3. Apa yang berubah di lapisan pengetahuan - dan apa yang tidak ada

- `03-Sinyal/Indikator` dan `04-Setup` sekarang punya **satu angka uji** dan berpindah dari
  "didokumentasikan" ke "diuji pada instrumen kita, belum pada bar OHLC".
- Yang builder sebut belum semuanya ada di lapisan itu, dan ini bukan salah uji: **Fibonacci tidak
  punya catatan sendiri** - dia disebut di 15 catatan sebagai konsep (mis. di dalam
  [[TradingKnowledge/I4 - Bollinger Bands]] dan [[TradingKnowledge/I6 - ATR dan Jarak Ternormalisasi]]) tanpa setup tersendiri; `04-Setup` berisi **tujuh persona** ([[TradingKnowledge/ST1 - All-Rounder]],
  [[TradingKnowledge/ST2 - Futures Hunter]], [[TradingKnowledge/ST3 - Clean Price Action]],
  [[TradingKnowledge/ST4 - Range dan Mean Reversion]], [[TradingKnowledge/ST5 - Trend Rider]],
  [[TradingKnowledge/ST6 - Aliran On-Chain Fabius]], [[TradingKnowledge/ST7 - Checklist Keputusan]])
  yang **nol perintah alat**; **scalping** cuma disebut 2 catatan dan tidak bisa diuji sama sekali
  di data kita - ia butuh bid/ask dan kedalaman book yang tidak pernah kita rekam.
- [[TradingKnowledge/I5 - Ichimoku Cloud]] dan [[TradingKnowledge/I7 - VWAP dan Anchored VWAP]]
  juga belum diuji; Ichimoku 5 catatan menyebutnya, nol angka.
- Kalau teknik klasik diuji serius, jalurnya: bar OHLC 1 h/4 h dari Aster/Hyperliquid untuk aset
  dengan riwayat panjang (`tools/bars.py`) - bukan deret peristiwa memecoin. Itu **P32**.

Baca ulang: `python -X utf8 tools/technic_lab.py` · `python -X utf8 tools/backtest.py --top 5` ·
`python -X utf8 _research/audit_ujian_pengetahuan.py` (workspace; audit cakupan uji)

**Terkait:** [[08-Backlog/02 - Epik Alasan Masuk]] · [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] · [[06-Results/14 - Buku Paper]] · [[06-Results/04 - Negative Results]] ·
[[TradingKnowledge/I1 - Moving Average]] · [[TradingKnowledge/I2 - RSI dan Divergence]] ·
[[TradingKnowledge/I3 - MACD]] · [[TradingKnowledge/I4 - Bollinger Bands]] ·
[[TradingKnowledge/I6 - ATR dan Jarak Ternormalisasi]] · [[TradingKnowledge/FD9 - Horizon Waktu dan Multi-Timeframe]] · [[TradingKnowledge/EV2 - Jebakan Backtest]]


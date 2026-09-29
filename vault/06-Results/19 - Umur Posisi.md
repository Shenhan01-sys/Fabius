---
tags: [hasil, "umur-posisi", "E11", "alasan-masuk"]
---

# 19 - Umur Posisi: kabar itu hidup lima menit

**Alat:** `python -X utf8 tools/horizon_decay.py` · **Artefak:**
`decisions/horizon-decay-20260929T075846Z.json` · **Dijalankan:** 29 Sep 2026 ±07:58Z
**Data:** 393 kejadian beli dari ⑦, harga `wp`, penjelajahan berhenti di `t_kunci` watch
(2026-09-29T02:59:06Z) — jendela yang sama dengan E7/E8/E10, jadi angkanya sebanding.

## 1. Kenapa halaman ini ada, dan kenapa dia berbeda dari empat halaman sebelumnya

Empat hari terakhir isinya pencabutan: harga masuk beku (F-D30), control yang mempromosikan
dirinya sendiri (F-D32), Mann-Whitney salah urut (F-D37), satu undian disebut hasil (F-D39),
kontrol keluar yang salah (F-D40). E11 lahir justru **dari** pencabutan terakhir: begitu terbukti
bahwa "keluar saat kerumunan" tidak mengalahkan "keluar di waktu acak", satu pertanyaan belum
diukur sendiri — **berapa lama sebenarnya boleh memegang?**

Jawabannya terukur, dan bentuknya bukan garis datar:

```
   umur(m)    n_ada  mean winso     median    P>=500   positif P(ada hrg) umur harga    basi
         2      335      +192,7       -5,1     36,7%     49,9%     85,2%        -4 s    0,0%
         5      334      +202,6      +59,9     40,4%     51,8%     85,0%        +1 s    0,0%
        10      334       +45,0      -36,9     35,9%     48,2%     85,0%        +8 s    0,0%
        15      335       -42,0      -59,0     35,2%     46,0%     85,2%        +5 s    0,0%
        20      335      -101,7      -64,8     32,8%     44,5%     85,2%        -4 s    0,0%
        30      332      -182,5      -79,6     31,6%     41,6%     84,5%        -6 s    0,0%
        45      332      -216,1     -125,2     30,4%     39,2%     84,5%        -2 s    0,0%
        60      331      -190,1     -123,1     31,7%     40,5%     84,2%        +4 s    0,0%
```

Tiga hal yang membuat kurva ini bukan kebetulan:

1. **Berpasangan pada posisi yang sama**, lawan horison 30 menit, dengan tanda-uji eksak satu arah:
   2 m **+120,8 median (p=0,00001)** · 5 m +50,5 (p=0,00001) · 10 m +41,8 (p=0,00000) ·
   15 m +17,7 (p=0,00000) · 20 m +5,3 (p=0,00002). **5 dari 5 horison pendek menang.** Yang 45 dan
   60 m tidak berbeda dari 30 m (p≈0,97) — setelah setengah jam, semuanya sama-sama bocor.
2. **Placebo asal-mula.** Kurva yang sama, dihitung dari jam yang digeser acak 30–90 menit
   (memutus hubungan dengan peristiwa), **datar di sekitar −180 bps di semua horison**
   (−184,7 … −113,9). Jadi kemiringan di atas bukan bentuk pasar BSC pada jam itu; dia menempel
   pada **peristiwa**.
3. **Bukan korban penyensoran:** `P(ada harga keluar)` 84–85 % di semua horison (tidak memilih-milih),
   dan `basi` 0 % — kolom "umur harga" melaporkan bahwa baris `wp` yang dipakai keluar benar-benar
   berumur ±beberapa detik dari horison yang diklaim.

## 2. Dan di sinilah kabar baiknya jadi pertanyaan rekayasa

Dua kontrol yang kami jalankan sendiri, keduanya mengurangi klaim ini:

**a) Sumber harga masuk.** Kalau harga masuk diambil dari **harga transaksi** (`tx.p`, median
+65,8 bps di atas `wp` terakhir pada jam yang sama — buys memang mencetak di atas tick terakhir
kami), bump-nya menyusut tapi tidak hilang:

| horison | mean (masuk `wp`) | mean (masuk `tx`) | median (masuk `tx`) |
|---|---|---|---|
| 2 m | +192,7 | **+168,8** | +26,6 |
| 5 m | +202,6 | **+161,5** | +20,2 |
| 10 m | +45,0 | +19,4 | −11,0 |
| 30 m | −182,5 | −168,6 | −99,5 |

**b) Latensi — dan ini yang menentukan.** Kurva yang sama, tapi masuk **setelah tertunda `d` menit**:

```
   delay(m)      mean@5m    median@5m     mean@30m   median@30m
         0       +202,6        +59,9       -182,5        -79,6
         2        +47,3        -56,2       -358,5       -167,9
         5       -166,4        -61,7       -351,9       -146,7
        10       -189,4        -62,1       -303,5       -120,6
        20       -117,5        -59,0       -212,7       -90,6
```

Tunda dua menit dan median@5m sudah **negatif**; tunda lima menit dan yang tersisa cuma kerugian.
Sementara itu latensi **data** kami terukur baik: `python -X utf8 tools/feed_latency.py 25`
→ **median 0,2 menit** (p90 0,2) dari kejadian ke baris yang sudah masuk git, dihitung dari stempel
commit GitHub, bukan jam laptop.

Jadi keadaan yang jujur: **kabarnya sampai cepat (±12 detik), acaranya selesai dalam ±2 menit, dan
mesin keputusan kami bangun tiap 4 jam** (cron `paper-book`) atau per siklus 202 detik (rantai ⑦).
Yang menahan Fabius sekarang bukan "tidak ada sinyal", tapi **jalur dari sinyal ke order belum
dibangun pada kecepatan sinyal itu hidup**.

## 3. Apa yang TIDAK boleh dibaca dari halaman ini

- Bukan "Fabius bisa trading". Yang terukur adalah **bump pasca-peristiwa yang meluruh**, dengan
  median +20…+60 bps pada dua horison pertama dan **harapan yang datang dari ekor kanan**
  (P(≥+500) 37–40 %, median horison 2 m masih −5,1). Pada ongkos 59 bps RT, median setipis itu
  tidak otomatis bisa diambil — apalagi tanpa ukuran kedalaman (P33 masih terbuka).
- Bukan hasil terkunci. E11 dieksplorasi pada data **sampai** `t_kunci` watch. Yang menguncinya
  adalah uji berikutnya di depan: [[08-Backlog/01 - Backlog]] P39 (horison pendek, data setelah
  kunci).
- Bukan pengganti veto. `jual_*` tetap satu-satunya rem yang berdiri; E11 bicara **umur**, bukan
  arah.

- **Batas substrat - dan ini syarat, bukan catatan kaki.** Yang diukur E11 adalah token **spot BSC**
  yang terlihat oleh ⑦ (harga dari GMGN/DexScreener). Yang bisa dieksekusi agen ini hari ini adalah
  **perp di Aster** (`tools/direction.py` → `tools/execute_live.py`), dengan deret harganya sendiri.
  Apakah bump dua menit di spot muncul juga di perp pada arah yang sama **belum diukur** - dan tanpa
  itu, E11 tidak boleh dibaca sebagai "Fabius bisa menradingkan ini", seberapa pun bagus kurva di
  halaman ini. (P41)

## 4. Perintah

```bash
python -X utf8 tools/horizon_decay.py --self-test     # drift turun/naik/datar dikenali; bolong -> None
python -X utf8 tools/horizon_decay.py                 # kurva + berpasangan + placebo + dua kontrol
python -X utf8 tools/horizon_decay.py --horisons 2,5,10,30 --dasar 30
python -X utf8 tools/feed_latency.py 25                # latensi feed dari stempel commit
```

**Terkait:** [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] ·
[[06-Results/18 - Kandidat Pertama, Diuji Hidup]] · [[08-Backlog/02 - Epik Alasan Masuk]] §3e ·
[[00-Overview/03 - Decisions]] F-D40/F-D41 · [[Concepts/Unmeasured Is Not Clean]] ·
[[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]]

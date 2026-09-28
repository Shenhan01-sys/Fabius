---
tags: [data]
---

# D6 - Funding and OI History

**Sumber:** `universe/record_funding_history.py` · `universe/funding-history.jsonl` ·
`universe/funding-history-manifest.txt`

Histori funding + open interest untuk enam basis (BNB/BTC/ETH/SOL/DOGE/XRP), ditarik **mundur**
tanpa kunci. Ini pengganti bentuk lama P13 ("rekam per jam, tunggu 30 hari") yang dibatalkan
probe 28 Sep - lihat [[00-Overview/03 - Decisions]] F-D25.

## Kenapa halaman ini ada

Sebelum ada deret ini, pertanyaan "apakah veto funding kita pernah berguna?" hanya bisa dijawab
dengan satu pembacaan hari itu (tercatat di [[06-Results/03 - Not Yet Proven]] baris 8). Sekarang
jawabannya bisa dihitung pada 97 hari - dan karena deretnya ada, dia juga jadi bahan uji pertama
(`tools/carry_study.py`, hasilnya [[06-Results/08 - Carry Study]]).

## Yang terekam

| sumber | jenis | baris | rentang nyata | interval | nama simbol |
|---|---|---|---|---|---|
| OKX `public/funding-rate-history` | funding | 1.763 (6 basis) | **97,7 hari** (22 Jun → 28 Sep) | 8 jam | `BNB-USDT-SWAP` dkk |
| Bybit `v5/market/funding/history` | funding | 1.200 (6 basis × 200) | **66,3 hari** (23 Jul → 28 Sep) | 8 jam | `BNBUSDT` dkk |
| Binance `futures/data/openInterestHist` | OI + nilai OI | 3.000 (6 basis × 500) | **20,8 hari** (7 Sep → 28 Sep) | 1 jam | `BNBUSDT` (USD-M) |

Total **5.963 baris**, 934 KB. Skema 1. Sumber dicatat per baris karena **nama simbol berbeda per
venue** - itu bukan detail, itu sumber bug "200 tapi untuk aset lain".

## Bentuk baris

```json
{"k":"fr","s":"bybit","sym":"BNBUSDT","base":"BNB","t":1790000000000,"rate":0.0001,
 "iv_h":8,"schema":1,"pull_t":1790584765}
{"k":"oi","s":"binance_oi","sym":"BNBUSDT","base":"BNB","t":1790000000000,
 "sum_open_interest":7832.5,"sum_open_value":6098000.0,"iv_h":1,"schema":1,"pull_t":1790584765}
```

`t` = waktu kejadian settlement (milidetik epoch), `pull_t` = **kapan kami menerima angka ini**.
Keduanya wajib: funding hari ini bisa direvisi oleh venue, dan tanpa `pull_t` kita tidak bisa lagi
menyatakan "apa yang kami tahu pada jam sekian" - lihat [[Concepts/Point-in-Time vs Retro-updatable]].

## Cara jalan dan cara baca ulang

```
python -X utf8 universe/record_funding_history.py --report   # ukur saja, tidak menulis
python -X utf8 universe/record_funding_history.py            # sedot + tulis + manifest
python -X utf8 universe/record_funding_history.py --manifest  # tulis ulang manifest tanpa jaringan
python -X utf8 tools/carry_study.py                          # uji yang memakai deret ini
```

Manifest ditulis ulang penuh (bukan append), satu baris per (jenis, sumber, basis) dengan hash
baris terakhir kelompok - sama seperti `universe/manifest.txt`. Tiap panggilan jaringan diulang
sampai 3x sebelum divonis; yang gagal/hampa tercatat di ekor manifest, bukan hilang.

## Batas yang menempel

- **Interval 8 jam.** Horizon uji Fabius 1 jam dan 4 jam; funding 8 jam tidak bisa jadi fitur
  per-bar. Ia veto rezim, itu saja.
- **Jendela API:** Bybit berhenti di 200 baris (cursor halaman 2 membalas kosong), Binance OI cuma
  ±30 hari. Jadi "kedalaman" ini adalah batas layanan, bukan batas usaha.
- **Satu jaringan.** Diukur dari laptop builder 28 Sep 02:25Z; runner GitHub **belum** mengonfirmasi
  (sumber × jaringan × waktu - [[06-Results/03 - Not Yet Proven]] baris 15).
- **Dua venue funding bukan dua sampel.** Bybit dan OKX membiayai pasar yang sama; memakai keduanya
  sebagai "konfirmasi silang" menaikkan keyakinan tanpa menaikkan informasi.

**Terkait:** [[03-Data/00 - Hub Data]] · [[03-Data/D4 - Dune]] · [[03-Data/D5 - Record Schemas]] ·
[[06-Results/08 - Carry Study]] · [[TradingKnowledge/Fakta Terukur]] §A.5 ·
[[TradingKnowledge/U2 - Funding Rate dan Basis]]

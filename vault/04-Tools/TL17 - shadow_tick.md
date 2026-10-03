---
tags: [perkakas, "TL17"]
---

# TL17 - shadow_tick (mode bayangan tahap 2+3)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/shadow_tick.py` · uji `engine/tests/test_shadow_tick.py`

**Ringkas:** membuat tick B1/B3 dari REST Binance beberapa menit sesudah bar tutup (00:00Z), lalu membandingkannya dengan tick resmi yang ditulis rantai
GitHub dari zip Vision ±9-10 jam kemudian. Ini bukti sebelum tahap 2 (Railway jadi penulis ledger, P99) dan tahap 3 (tick dari REST, P100). Ia tidak
menulis ledger resmi, tidak mengirim transaksi, dan tidak memakai kunci.

**Poin kunci:**
- Jalan terus di service Railway `fabius-probe` (Singapura, tanpa variabel rahasia): `FABIUS_JOB=shadow_tick`.
- Bacaan REST pertama paling cepat +2 menit sesudah tutup. Data diterima hanya kalau dua bacaan berurutan berjarak >= 60 s identik (SK-R1, dari P98).
- Bar resmi disalin, lalu ditambah baris REST: kline perp/spot (divalidasi seperti `feed_bars`) dan estimasi funding dari indeks premium 1m REST
  (rumus `engine/funding_est.py`). Funding AKTUAL tidak pernah ditulis (SK-R2).
- Tick dibuat oleh `ledger.make_tick`, fungsi yang sama dengan `paper_tick`.
- Vonis per bot per bar: IDENTIK / BEDA (field yang beda disebut) / RESMI GAP / RESMI ADA, BAYANGAN DITOLAK. Vonis baris REST vs Vision: SAMA / ALARM.
- Kalau bar resmi sudah memuat hari itu saat bayangan jalan, vonisnya ditandai `uji_rest = false` (bukan bukti REST, SK-S2).

**Yang ia TOLAK lakukan:** menerima bacaan yang masih berubah; menulis ledger resmi; menulis funding aktual; meloncati hari yang bolong; mengubah apa pun saat
REST beda dari Vision (hanya mencatat ALARM).

**Vonis pertama (3 Okt):** `fabius-probe` 08:44:25Z: `VONIS bayangan B1-TREND 2026-10-02: IDENTIK`, `B3-CARRY: IDENTIK` (bayangan 323,9 menit vs resmi 8,7 jam - bayangan baru hidup 05:22Z); `VONIS baris REST 2026-10-02: 80 sama persis, beda harga 0, beda estimasi funding 0, beda volume saja 0` - estimasi funding dari indeks premium REST = estimasi dari zip Vision, risiko terbesar yang belum pernah diuji.

**Cara membaca hasil:** `railway logs --service fabius-probe --lines 80`, cari baris `bayangan`, `VONIS bayangan`, `VONIS baris REST`. Keadaan disimpan di
`/tmp` container: hilang saat deploy ulang, jadi log adalah catatannya.

**Terkait:** [[TL13 - rest_vs_vision]] · [[TL9 - ledger paper maju]] · [[07-Testing/T8 - Semantik Kegagalan Operator]] · [[00-Overview/03 - Decisions]] F-D83/F-D86

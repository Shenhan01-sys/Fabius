---
tags: [tk, tk-setup, "ST6"]
---

# ST6 - Aliran On-Chain Fabius

**Keluarga:** [[00 - Hub Setup]]
**Anggota:** [[FD1 - Struktur Pasar dan Rezim]] · [[O5 - Whale dan Kohor Smart Money]] ·
[[O6 - Konsentrasi Holder Bundler dan LP Lock]] · [[FD3 - Likuiditas dan Dampak Harga]] ·
[[FD4 - Ongkos Perdagangan]] · [[FD6 - Ukuran Posisi]] · [[FD7 - Invalidation Stop dan Time-Stop]] · [[PL2 - Menyaring Universe]]
**Sumber:** bukan dari `Plan.txt` — pipeline yang **sudah ada di repo ini**: perekam ⑦
([[03-Data/D2 - Wallet Flow]]) → `tools/screen_universe.py` → `tools/security_gate.py` → `tools/direction.py`
→ `tools/ledger.py`   ·   *(`tools/flow_signal.py` dan `tools/whale_cohorts.py` berdiri sendiri:
mereka membaca ⑦ tapi **tidak diimpor** satu pun alat keputusan di rantai di atas — itu persis
lubang yang dicatat [[GAP3 - Yang Punya Data Tapi Belum Diuji]] baris 1)*

**Ringkas:** satu-satunya setup di folder ini yang anggotanya benar-benar kita rekam: arah dari deret harga
sendiri, aliran dompet per-kolam (⑦), filter keamanan/konsentrasi, kapasitas keluar, dan ongkos terukur
59 bps. Statusnya wajib dibaca dua kali: **komponennya hidup, kesatuannya belum pernah diuji.** Bukan jalur
cepat menuju edge — pembandingnya disiapkan justru untuk membuktikan klaim ini salah, kalau memang salah.

## Resep

| tahap | aturan | perkakas |
|---|---|---|
| rekam | aliran maker point-in-time, di-commit tiap siklus, tidak bisa disusulkan | perekam ⑦ ([[03-Data/D2 - Wallet Flow]]) |
| saring | ① riwayat bar · ④ keamanan · ⑥ kapasitas keluar → `seat_eligible` + `seat_blockers` (ikut di-hash) | `tools/screen_universe.py`, `tools/security_gate.py`, `tools/direction.py::apply_gates` |
| arah | `\|acf\|` sebagai penanda "bukan jalan acak" + momentum + veto funding ekstrem | `tools/direction.py` |
| aliran | maker beli vs jual dalam jendela yang dilihat saat itu; kohor ditentukan per kolam | `tools/flow_signal.py`, `tools/whale_cohorts.py` |
| ukuran | plafon kontrak, bukan selera | [[FD6 - Ukuran Posisi]] (§E) |
| keluar | horizon tetap + time-stop | [[FD7 - Invalidation Stop dan Time-Stop]] |
| nilai | tutup dari **rekaman**, bukan dihitung ulang; ongkos masuk | `tools/ledger.py` |

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| deret harga forward ① | `ADA` | Aster 9.599 bar ≈ 400 hari tanpa kunci ([[Fakta Terukur]] §A) |
| aliran dompet ⑦ | `ADA-TAPI` | jendela lihat **8–13 menit**, **semua parameter paging diabaikan** → tidak ada riwayat; ekor `94aead6` (2026-09-27T18:21:16Z): 50.285 baris · 21.907 transaksi · 452 maker · 1.590 token · rentang 34,33 jam (§B) |
| kontrol "dompet biasa" | `TIDAK-ADA` | **0 dari 607** transaksi pertama tidak bertag → aliran ini memang didefinisikan sebagai "yang sudah dilabeli pintar" (§B); pembandingnya diganti, bukan ditambah |
| kohor per kolam | `ADA-TAPI` | `tools/whale_cohorts.py` mengukur struktur yang tipis: median **2 maker/simbol**, **49,8 %** simbol cuma 1 maker, HHI median **0,347** — itu **breadth, bukan skor** (§H) |
| filter keamanan/konsentrasi ②④ | `ADA` | §E: `MAX_TOP10` 45 % · `MIN_LOCK` 20 % · `MAX_BUNDLER` 30 % · `MIN_HOLDER` 60 · `MIN_VOL_OVER_LIQ` 0,10; `tools/security_gate.py` membalas 5/5: 4 `OK` + 1 `UNMEASURED` (§F) |
| kapasitas keluar ⑥ | `ADA` | `MIN_LIQ_USD` 50.000 + exit-cap ditegakkan `apply_gates`, ikut `gatesHash` (§E) |
| ongkos | `ADA` | **59 bps** round-trip terukur; realized nyata di 97 juga −59 bps (§D) |
| ⑦ masuk ke jalur keputusan | `TIDAK-ADA` | `tools/direction.py` / `tools/backtest.py` / `tools/ledger.py` tidak membaca rekaman ⑦ |
| penilai maker yang bisa dipercaya | `ADA-TAPI` | `tools/maker_ledger.py` rusak karena sebab yang diketahui: median 4.558,3 bps/lot, 71 % lot > 2000 bps, maks 1.222.045,4 (§H) → **angkanya dilarang dikutip** |

## Uji di Fabius

Syarat naik kelas — semuanya sudah punya jalur di repo ini:

1. **Kesatuan, bukan bagian.** Event = (token, jam) saat ⑦ menunjukkan aliran searah pada kandidat yang lolos
   ①④⑥. Hasil = return bersih pada horizon tetap, ongkos **59 bps** (§D).
2. **Pembanding sah, bukan "lebih baik dari trader biasa"** (§B): (a) arah acak pada **token & jam yang sama**;
   (b) hold 4 jam dari baris `px` kami sendiri tanpa memilih arah; (c) pisahkan `is_open_or_close`.
3. **Sampel:** `n >= 20` non-overlap, **satu sampel per (token, jendela yang tidak tumpang tindih)** — 20 order
   dompet panas dalam beberapa menit bukan 20 pertaruhan bebas (§B/§E).
4. **Statistik:** BH α 0,10 lintas uji; positif setelah fold terbaik dibuang; di luar sampel (F-D16, §E).
   p satu arah kita aproksimasi **normal** — pada n 20–40 ia sistematis terlalu kecil (§E).
5. **Label dicatat sebelum entri.** Keanggotaan panel hari ini tidak boleh menilai transaksi minggu lalu; untuk
   ⑦ itu kebetulan tertutup oleh fisika datanya (tidak bisa ditarik mundur).

Yang sudah tercatat tentang keluarga ini, supaya tidak dibeli dua kali: panel whale GMGN pada horison per jam
**win rate 69,8 % tapi −10,4 bps per jam** (§F) — kesimpulannya bukan "whale jelek", tapi "win rate bukan
expectancy" ([[FD5 - Expectancy Bukan Win Rate]]).

Status: **belum diuji sebagai kesatuan**; `n` dan expectancy kombinasi ini *(belum diukur)*. Jangan dibaca
sebagai harapan tertunda — kemungkinan terbesar hasil uji pertama adalah nol, dan nol pun jawaban yang produk
ini jual.

## Konfluensi atau gaung

Berbeda dari ST1–ST5: anggotanya **memang diukur dari alat yang berbeda** — empat sumber yang tidak bisa
diturunkan satu sama lain: deret OHLC (①) · transaksi dompet yang lewat (⑦) · snapshot holder/LP/bundler (②④)
· likuiditas pool (⑥). Itu konfluensi sungguhan, dan karena itu setup ini layak diuji lebih dulu. Sisa gaung:

| pasangan | status |
|---|---|
| arah `direction.py` ↔ gerbang `\|acf\|` | dua peran atas satu deret: yang satu memutuskan arah, yang lain mengizinkan. Bukan dua informasi |
| ⑦ ↔ baris `px` kami | pembanding "hold 4 jam" memakai **sumber harga yang sama** dengan yang dipakai menghitung hasil — sah sebagai kontrol, tidak sah sebagai konfirmasi independen |
| `O5` (siapa membeli) ↔ `O6` (siapa memegang) | mengukur hal serupa dari sisi berbeda (aliran vs stok); jangan dihitung dua suara |
| kapasitas keluar ↔ ongkos | keduanya ukuran dampak, keduanya **penolak**, tidak satu pun pembuat arah ([[01-Agent/A3 - One-Way Gates]]) |

## Batas dan mode gagal

- **Lubang permanen.** Satu jam yang dilewati = jendela hilang selamanya, dan pemicu jadwal tidak bisa
  dijamin: setup ini berdiri di atas dataset yang bolongnya tercatat, bukan di atas feed yang lengkap.
- **Kolam tipis.** Median 2 maker/simbol dan hampir separuh simbol cuma 1 maker (§H) membuat "kohor per
  kolam" kosong secara struktural — hasil nol bisa berarti "tidak ada data", bukan "tidak ada edge".
- **Alat skornya sedang tidak bisa dipercaya** (§H). Sampai mekanika `tools/maker_ledger.py` beres, satu-satunya
  angka maker yang boleh dipakai adalah yang dicetak `tools/ledger.py` atas keputusan sendiri.
- **Ongkos dua kepala.** Jalur warisan menutup dengan 20 bps sementara yang terukur 59 bps (§D); P10 terbuka —
  setiap `net` dari jalur lama adalah angka yang terlalu ramah.
- **Mode gagal termahal:** ④ bersih tapi keluar tetap tidak mungkin. Yang tidak terjual tidak punya `net` dalam
  bps, tidak tertutup time-stop apa pun, dan akan tercatat sebagai angka yang bagus ([[Concepts/Unmeasured Is Not Clean]]).

## Tingkat bukti

`T1` untuk **komponennya** — perekam ⑦, gerbang ①④⑥, ongkos terukur, dan jalur penilaian ada sebagai kode yang
bisa dijalankan dari clone. Bukan `T3`: tidak ada satu pun angka di [[Fakta Terukur]] yang mengukur kombinasi
ini. `T0` untuk **kesatuannya**: belum pernah dijalankan sebagai satu setup dengan pembanding §B.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius merekam aliran dompet point-in-time dan sudah punya pembanding sah plus ongkos terukur;
  kombinasi ini belum diuji sebagai kesatuan, dan alat skor maker-nya sedang rusak karena sebab yang diketahui."
- **Dilarang:** "Fabius memperdagangkan sinyal whale" · mengutip angka `tools/maker_ledger.py` sebagai temuan
  (§H) · "smart money kami terbukti" (yang terbukti: 69,8 % WR **dan** −10,4 bps per jam) · "jendela lihat
  8–13 menit cukup" (yang belum terukur; yang pasti: yang lewat hilang).

**Terkait:** [[ST7 - Checklist Keputusan]] · [[03-Data/D2 - Wallet Flow]] · [[O5 - Whale dan Kohor Smart Money]] ·
[[EV3 - Signifikansi dan Multiple Testing]] · [[GAP3 - Yang Punya Data Tapi Belum Diuji]]

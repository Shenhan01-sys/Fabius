---
tags: [tk, tk-sinyal, "M4"]
---

# M4 - Catalyst dan Event Trading

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** keputusan ([[PL4 - Memutuskan]])
**Sumber:** `vault/TradingKnowledge/Plan.txt` §"3. Strategi Populer di Crypto" ("News / Event
Trading (listing, unlock token, regulasi, dll)") + §"Narrative & Catalyst" (Listing / Partnership /
Mainnet, Token Unlock / Vesting, Macro Event) — klaim komunitas

**Ringkas:** Keluarga ini menjual satu gagasan: peristiwa yang dijadwalkan punya efek harga yang bisa
dijadwalkan pula. Sebagian benar — peristiwa menggerakkan harga. Sebagian besar salah kaprah karena
**waktu yang penting bukan waktu peristiwa, tapi waktu pengumumannya**, dan di antara keduanya harga
sudah bergerak. Untuk produk seperti Fabius, nilai keluarga ini justru di sisi negatif: ia memberi
alasan untuk **tidak** membuka posisi ( unlock jatuh besok, kuartal depan terlalu ramai peristiwa).

## Definisi yang bisa dihitung

```
# sebuah peristiwa = empat waktu yang berbeda, jangan digabung:
t_umum  = saat pengumuman publik pertama                    <- di sini edge sebagian besar hilang
t_janji = saat yang dijadwalkan (listing/unlock/mainnet)
t_ambil = saat IRISAN KAMI punya peristiwa itu
t_hasil = hasil pada horizon tetap setelah t_ambil
aturan keras: sinyal hanya boleh memakai t <= t_ambil; memakai t_janji yang baru diketahui
belakangan = lookahead dengan baju kalender.
# bentuk aturan yang biasa dijual:
ekspektasi_arah(peristiwa) = +1 listing · -1 unlock · ? partnership   <- TIDAK SATU PUN punya
                             distribusi hasil, hanya tanda
```

## Cara pakai yang diklaim

"Buy the rumor, sell the news": beli sebelum tanggal, jual saat peristiwa terjadi; hindari posisi
menjelang unlock; kejar listing baru karena permintaan mendadak. Klaim ini milik komunitas event
trading; tidak ada sumber primer di repo ini. Yang **bisa** kami bilang tentang mekanismenya:
peristiwa dengan tanggal diketahui adalah titik di mana ekspektasi orang lain bisa berubah tiba-tiba
([[FD7 - Invalidation Stop dan Time-Stop]] lebih relevan daripada prediksi arah di sini).

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| kalender peristiwa (listing/unlock/mainnet/airdrop) | `TIDAK-ADA` | "jadwal unlock/vesting" ada di daftar yang tidak kami punya sama sekali — [[Fakta Terukur]] §C |
| waktu pengumuman (t_umum) per peristiwa | `TIDAK-ADA` | tidak ada jalur; tanpa ini "sebelum peristiwa" tidak terdefinisi secara point-in-time |
| umur pool/token + platform peluncuran | `ADA` | `age_sec`, `created_at`, `launched` direkam `universe/record_bsc_universe.py`; gerbang `MIN_AGE_SEC` 24 jam (§E) menegakkan bagian tertuanya lewat veto `age<24h_zero_bars` |
| daftar "sedang ramai" hari ini | `ADA-TAPI` | `trending_pools`/`new_pools`; **tidak bisa ditarik mundur** — docstring `universe/record_bsc_universe.py` menulisnya apa adanya: "Tidak ada API yang bisa mengembalikan daftar trending 3 hari yang lalu" |
| pulsa berita/regulasi per irisan | `ADA-TAPI` | `gdelt_slice()` (tema + nada, irisan 15 menit) ikut masuk snapshot; hubungannya dengan hasil **belum diuji** ([[06-Results/03 - Not Yet Proven]] baris 8) |
| deret harga untuk menguji efek peristiwa | `ADA-TAPI` | hanya aset ber-perp: 9.599 bar ≈ 400 hari (§A); memecoin yang jadi objek peristiwa biasanya mentok 1.000 bar |

## Uji di Fabius

Dua kelas uji, dan kelas pertama bisa dimulai hari ini dengan data yang sudah ada:

1. **Peristiwa yang kami lihat sendiri** (pool baru, lompatan ke `trending_pools`). Event study
   dengan hasil return bersih 4 jam vs **arah acak pada token dan jam yang sama** (§B),
   `n >= 20` non-overlap, gross di atas **59 bps** (§D), BH α 0,10 (§E). Ini bentuk uji yang sama
   yang sudah dijalankan `tools/screen_universe.py` untuk alasan penolakan — tinggal dibalik dari
   "veto" ke "katalis".
2. **Peristiwa berkalandar** (unlock, listing berjadwal, mainnet): **belum bisa diuji** — tidak ada
   kalender dan tidak ada `t_umum`. Ini penghuni [[GAP4 - Yang Tidak Bisa Diuji Karena Data]], dan
   satu-satunya jalan masuknya adalah membangun deret peristiwa **dari sekarang**
   ([[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]).

## Batas dan mode gagal

- **Kalender yang salah tanggal lebih berbahaya dari tidak punya kalender.** Tanggal unlock
  bergeser; kalau kita menyimpan "janji" sebagai fakta, kita akan membayar ongkos 59 bps untuk
  peristiwa yang tidak terjadi pada hari itu.
- **Edge-nya ada di pengumuman, bukan di kejadian.** Setelah pengumuman, yang mau masuk sudah
  masuk; yang tersisa adalah likuiditas tipis orang lain yang keluar — dan keluar adalah
  bagian yang paling sering gagal di jalur nyata kita (§D/§F).
- **Peristiwa kecil tidak punya sampel.** `n >= 20` untuk satu jenis peristiwa pada satu eco bisa
  berarti satu tahun kalender; kalau digabung lintas jenis, yang diuji bukan lagi peristiwa itu
  ([[EV3 - Signifikansi dan Multiple Testing]]).
- **Survivorship listing.** Yang tercatat sebagai "listing sukses" adalah yang masih ada; yang
  delisting tidak masuk deret kita.
- **Duplikasi dengan V1/⑦:** lonjakan volum dan arus dompet saat peristiwa biasanya mengukur hal
  yang sama dengan "katalis", hanya lebih lambat diberi nama.

## Tingkat bukti

`T0` untuk tanda arah tiap jenis peristiwa (listing = naik, unlock = turun) · `T1` untuk
"peristiwa menaikkan volatilitas" (fenomena umum, tidak kami reproduksi) · untuk Fabius: hanya bagian
**umur/kelayakan** yang punya gigi (gerbang 24 jam, §E) dan itu pun sebagai veto, bukan sebagai
edge; kalender peristiwa belum pernah diuji sama sekali.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "kami menolak kandidat yang terlalu muda dan mencatat umur tiap snapshot; efek
  peristiwa berkalandar tidak bisa kami uji karena tidak ada kalender dan tidak ada waktu
  pengumuman."
- **Dilarang:** "Fabius memperdagangkan peristiwa" · menyebut `trending_pools` sebagai riwayat
  (ia hanya keadaan sekarang) · menjual "buy the rumor sell the news" sebagai aturan dengan hasil
  terukur · memakai angka vendor unlock sebagai jadwal kami.

**Terkait:** [[O7 - Token Unlock dan Vesting]] · [[M2 - Sentimen Sosial dan Ekstraksi LLM]] ·
[[M3 - Narasi Sektar dan Rotasi]] · [[M5 - Makro dan Korelasi Silang-Pasar]] ·
[[FD7 - Invalidation Stop dan Time-Stop]] · [[GAP4 - Yang Tidak Bisa Diuji Karena Data]]

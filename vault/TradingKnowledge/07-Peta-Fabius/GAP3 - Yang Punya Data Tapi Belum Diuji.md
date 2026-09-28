---
tags: [tk, tk-peta, "GAP3"]
---

# GAP3 - Yang Punya Data Tapi Belum Diuji

**Keluarga:** [[00 - Hub Peta Fabius]] · **Tahap:** penilaian ([[PL6 - Menilai Hasil]])
**Sumber:** [[Fakta Terukur]] §A/§B/§H · [[03-Data/D5 - Record Schemas]] · `tools/` (dibaca 28 Sep 2026)

**Ringkas:** lubang terbesar Fabius bukan kekurangan data, melainkan bahan yang **sudah** kami rekam
dan tidak pernah ditanya apa-apa. Diperbarui 28 Sep: dari enam baris di bawah, **tiga sudah dijawab**
(⑦ diuji → kohor tidak memisahkan; `px` dipakai jadi jangkar keluar → 80,6 % kejadian ternyata
tersensor; funding diuji → veto 0 kejadian, 0/12 lolos BH) dan ketiganya keluar **negatif**. Sisa
yang benar-benar belum disentuh: volum, funding per-jam venue sendiri, blok narasi, dan deret
selektivitas kita sendiri. Halaman ini tetap daftar pekerjaan termurah — hanya saja yang "murah"
itu sekarang sudah sebagian ditagih, dan tagihannya bukan untung.

## Definisi yang bisa dihitung

Masuk daftar ini kalau tiga syaratnya terpenuhi sekaligus:

1. bahannya ada di `Fabius/` (berkas atau jalur kode yang bisa dijalankan dari clone);
2. tidak ada satu pun alat keputusan yang **mengonsumsi** hasilnya (`tools/direction.py` dkk tidak
   menyebutnya, atau alatnya ada tapi outputnya tidak masuk keputusan);
3. uji yang membuktikannya tidak butuh data yang belum kami punya.

Syarat 3 itulah yang membuat daftar ini pendek dan menyakitkan: keluarga yang butuh tick/L2/histori
on-chain **tidak** masuk ke sini — mereka masuk [[GAP4 - Yang Tidak Bisa Diuji Karena Data]].

## Cara pakai yang diklaim

Dipakai sebagai antitesis terhadap "mari tambahkan indikator baru". Sebelum menambah satu jalur
data, selesaikan yang sudah menetes tiap jam. Urutan kerjanya tetap: **perbaiki mekanika alat →
uji terhadap null → baru bicara bobot**.

## Butuh data

| # | bahan yang sudah ada | status | apa yang belum ditanyakan | alat | bayar |
|---|---|---|---|---|---|
| 1 | **bidang ⑦** — `universe/wallet-flow.jsonl`: run `94aead6` 18:21:16Z = 50.285 baris · 21.907 tx · 452 maker · 1.590 token; ekor terbaru di `universe/wallet-flow-manifest.txt` ([[Fakta Terukur]] §B) | `ADA-TAPI` (tanpa riwayat) | ~~belum ditanyakan~~ **diuji 28 Sep**: apakah kerumunan maker (≥2 dompet berbeda dalam 30 m) meramalkan 60 menit berikutnya | `tools/flow_cluster_test.py` (membaca berkasnya langsung; tetap **tidak diimpor alat keputusan apa pun**) | nol → **0 lolos BH**, tapi **80,6 %** kandidat tanpa harga keluar; sisanya **P17** |
| 2 | **baris `px`** — harga per `tk` tiap tarikan (ekor `origin/master`: **27.886 baris / 1.607 token**, [[Fakta Terukur]] §B) | `ADA-TAPI` (jangkauan = umur perekam; **median jendela per token cuma 27 menit**) | ~~bolehkah jadi jangkar hasil~~ **sudah dipakai sebagai jangkar keluar** oleh `tools/flow_cluster_test.py` | hasilnya sekaligus menunjukkan batasnya: **3.191 dari 3.958** kejadian tidak punya `px` pada jendela keluar, dan **21,6 %** gross-nya persis 0,0 bps (resolusi) | nol; sisanya **P17 + P18** |
| 3 | **kolom volum bar** — ikut diparsing `tools/bars.py`; tidak ada satu pun referensi volum di `tools/direction.py` (diperiksa 28 Sep) | `ADA` | apakah volum menambah informasi di atas harga, atau hanya menamai ulang pergerakan yang sama | `I7 - VWAP dan Anchored VWAP`, `V1 - Konfirmasi Volum dan Money Flow` belum punya jalur data | nol |
| 4 | ~~funding + OI: belum diuji~~ **selesai 28 Sep** — `tools/carry_study.py` atas deret sendiri ([[03-Data/D6 - Funding and OI History]]) | `ADA` | apakah veto carry memprediksi hasil yang lebih buruk | **sudah dijawab:** veto kena **0 dari 2.963** settlement; **0 dari 12 uji** arah 24 jam lolos BH; carry 1,3–2,2 bps/hari → [[06-Results/08 - Carry Study]] | nol |
| 4b | funding **per jam venue sendiri** (Aster `premiumIndex` per 4 jam) — satu-satunya funding yang bisa menguji ambang kita apa adanya | `TIDAK-ADA` (jalur hidup, belum direkam) | apakah ambang 0,05 %/4 j pernah relevan untuk kandidat kita | butuh perekam baru + **kalender** | nol + kalender |
| 5 | **blok `gdelt`** (skema 4) — dibaca `tools/decide.py::gdelt_context` dan **masuk ke kalimat konteks model**, tidak ke angka | `ADA` | apakah konteks berita mengubah kualitas keputusan sama sekali, atau hanya membuat alasannya lebih panjang | tidak ada kontrol "dengan vs tanpa" | nol |
| 6 | **deret pilihan kita sendiri** — `universe_size` / `survivable_count` / `fully_evaluated_count` / `top_reasons` per snapshot (satu baris per jam; jumlah baris bertambah terus, lihat `universe/manifest.txt`) | `ADA` | seberapa selektif kita sebenarnya, dan apakah selektivitas itu bergerak seiring pasar atau seiring kegagalan penggabungan sumber | belum ada satu grafik/angka publik pun dari deret ini | nol |

Dua catatan yang menahan diri supaya tidak menjual harapan:

- **Yang direkam 4b dan 6 baru bernilai setelah punya umur.** Memulai perekaman funding per jam hari
  ini berarti uji carry bisa dijalankan nanti, bukan besok. Itu harga yang benar untuk dibayar
  (`kalender`), dan satu-satunya cara keluar dari "veto estetik".
- **Hasil dari enam hal ini kemungkinan besar negatif - dan yang pertama sudah menagih ramalan itu.**
  Carry diuji 28 Sep: **0 dari 12 uji lolos BH**, verdict `NETAS`
  ([[06-Results/08 - Carry Study]]). Riwayat lainnya ([[Fakta Terukur]] §F): aturan arah rugi di
  12/12 aset, panel whale menang 69,8 % dari waktu tapi −10,4 bps per jam.
  Nilai pengujian bukan pada "menemukan edge", tapi pada **memberhentikan** aturan yang sekarang
  diam-diam ikut memutuskan.

## Uji di Fabius

Ambang yang sama untuk keenamnya, tidak bisa ditawar per kasus: `n ≥ 20` non-overlap, BH α 0,10,
tetap positif setelah fold terbaik dibuang, ongkos **59 bps** (terukur), dan **satu tes per token**
([[EV3 - Signifikansi dan Multiple Testing]]). Artefak wajib `decisions/*.json` + `rows_sha256`
supaya bisa dibuktikan ulang ([[EV5 - Reproduksibilitas dan Pra-Registrasi]]).

## Batas dan mode gagal

- "Belum diuji" ≠ "tidak berguna". Daftar ini tidak boleh dibaca sebagai vonis; ia pembacaan
  **status**. Tapi ia juga tidak boleh dibaca sebagai "tinggal tekan".
- Enam baris itu berbagi satu alat ukur yang sama (harga yang kami catat sendiri) — jadi kalau alat
  ukurnya salah, keenamnya salah dengan cara yang sama. Perbaiki §H lebih dulu.
- Deret ⑦ punya **umur total 34,33 jam** pada ekor terbaiknya. Beberapa pertanyaan di atas secara
  struktural belum bisa dijawab dengan itu; itu bukan alasan untuk tidak menyiapkan jalurnya.

## Tingkat bukti

`T1` untuk klaim "bahannya ada" (peta keadaan — tiap nomor berkas bisa dibaca dari clone, tapi itu
**baca**, bukan **run**; `T3` di lapisan ini disimpan untuk hasil uji, lihat [[EV1 - Tingkat Bukti]]) ·
`T0` untuk klaim apa pun bahwa salah satunya akan menghasilkan edge — belum ada satu pun yang diuji.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius sudah merekam aliran dompet, harga per-token miliknya sendiri, volum, funding
  live, dan blok narasi — dan belum menjalankan satu pun uji yang mengonsumsi semuanya."
- **Dilarang:** "kami sedang menguji enam hal itu" (belum) · "cuma butuh tombol" (butuh mekanika
  `maker_ledger` yang benar, lalu kalender untuk uji prospektif).

**Terkait:** [[GAP5 - Urutan Kerja dan Bayarnya]] · [[GAP4 - Yang Tidak Bisa Diuji Karena Data]] ·
[[O5 - Whale dan Kohor Smart Money]] · [[V1 - Konfirmasi Volum dan Money Flow]] ·
[[U2 - Funding Rate dan Basis]] · [[M2 - Sentimen Sosial dan Ekstraksi LLM]]

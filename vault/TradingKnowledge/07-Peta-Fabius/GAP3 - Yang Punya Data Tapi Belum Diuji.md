---
tags: [tk, tk-peta, "GAP3"]
---

# GAP3 - Yang Punya Data Tapi Belum Diuji

**Keluarga:** [[00 - Hub Peta Fabius]] · **Tahap:** penilaian ([[PL6 - Menilai Hasil]])
**Sumber:** [[Fakta Terukur]] §A/§B/§H · [[03-Data/D5 - Record Schemas]] · `tools/` (dibaca 28 Sep 2026)

**Ringkas:** lubang terbesar Fabius bukan kekurangan data, melainkan bahan yang **sudah** kami rekam
dan tidak pernah ditanya apa-apa. Enam hal di bawah ini sudah ada di repo, tidak butuh langganan,
tidak butuh jaringan baru — dan tidak satu pun menghasilkan angka yang mengubah keputusan. Halaman
ini adalah daftar pekerjaan termurah yang belum dikerjakan.

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
| 1 | **bidang ⑦** — `universe/wallet-flow.jsonl`: run `94aead6` 18:21:16Z = 50.285 baris · 21.907 tx · 452 maker · 1.590 token; ekor terbaru di `universe/wallet-flow-manifest.txt` ([[Fakta Terukur]] §B) | `ADA-TAPI` (tanpa riwayat) | apakah arah keranjang maker pada token X mendahului hasil 4–24 j, dibanding **arah acak pada token & jam yang sama** | `tools/flow_signal.py` ada, **tidak diimpor satu pun alat keputusan**; `tools/maker_ledger.py` belum bisa dipercaya (§H) | nol + jam-proses |
| 2 | **baris `px`** — harga per `tk` tiap tarikan (ekor `origin/master`: **27.886 baris / 1.607 token**, [[Fakta Terukur]] §B) | `ADA-TAPI` (jangkauan = umur perekam) | bolehkah ia jadi **jangkar hasil** untuk token tanpa perp, menggantikan asumsi harga terakhir | belum ada yang memakainya sebagai yardstick | nol |
| 3 | **kolom volum bar** — ikut diparsing `tools/bars.py`; tidak ada satu pun referensi volum di `tools/direction.py` (diperiksa 28 Sep) | `ADA` | apakah volum menambah informasi di atas harga, atau hanya menamai ulang pergerakan yang sama | `I7 - VWAP dan Anchored VWAP`, `V1 - Konfirmasi Volum dan Money Flow` belum punya jalur data | nol |
| 4 | **funding + OI live** — Aster 608 kontrak / Hyperliquid 234 perp ([[Fakta Terukur]] §A); veto funding > 0,05 %/4 j **sudah wired** di `tools/direction.py` | `ADA-TAPI` (hidup saja, tanpa histori) | apakah veto carry itu memprediksi hasil yang lebih buruk, atau cuma mahal secara estetika | butuh histori funding per jam → mulai rekam sekarang (baris 4 bawah) | nol untuk merekam, kalender untuk menguji |
| 5 | **blok `gdelt`** (skema 4) — dibaca `tools/decide.py::gdelt_context` dan **masuk ke kalimat konteks model**, tidak ke angka | `ADA` | apakah konteks berita mengubah kualitas keputusan sama sekali, atau hanya membuat alasannya lebih panjang | tidak ada kontrol "dengan vs tanpa" | nol |
| 6 | **deret pilihan kita sendiri** — `universe_size` / `survivable_count` / `fully_evaluated_count` / `top_reasons` per snapshot (65 baris [[03-Data/D5 - Record Schemas]]) | `ADA` | seberapa selektif kita sebenarnya, dan apakah selektivitas itu bergerak seiring pasar atau seiring kegagalan penggabungan sumber | belum ada satu grafik/angka publik pun dari deret ini | nol |

Dua catatan yang menahan diri supaya tidak menjual harapan:

- **Yang direkam 4 dan 6 baru bernilai setelah punya umur.** Memulai perekaman funding per jam hari
  ini berarti uji carry bisa dijalankan nanti, bukan besok. Itu harga yang benar untuk dibayar
  (`kalender`), dan satu-satunya cara keluar dari "veto estetik".
- **Hasil dari enam hal ini kemungkinan besar negatif.** Riwayat kami sendiri ([[Fakta Terukur]] §F):
  aturan arah rugi di 12/12 aset, panel whale menang 69,8 % dari waktu tapi −10,4 bps per jam.
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

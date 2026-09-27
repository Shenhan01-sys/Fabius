---
tags: [tk, tk-setup, "ST7"]
---

# ST7 - Checklist Keputusan

**Keluarga:** [[00 - Hub Setup]]
**Anggota:** [[PL1 - Mengumpulkan Data]] · [[PL2 - Menyaring Universe]] · [[PL3 - Menganalisis]] · [[PL4 - Memutuskan]] ·
[[PL6 - Menilai Hasil]] · [[FD4 - Ongkos Perdagangan]] · [[FD6 - Ukuran Posisi]] · [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]]
**Sumber:** `tools/direction.py`, `tools/judge.py`, `tools/ledger.py` + gerbang kontrak di
[[02-Contracts/C3 - ExecutionVault]] (bentuk gerbang nyata) + `vault/TradingKnowledge/Plan.txt`
§"Entry Checklist (Confluence minimal 3–4)" *(yang terakhir klaim komunitas; checklist di bawah bukan itu —
checklist ini milik produk ini)*

**Ringkas:** delapan pertanyaan yang harus dijawab **sebelum** sebuah keputusan diterbitkan, masing-masing
dengan nama catatan yang memikulnya dan nama berkas yang bisa menjalankannya. Ini bukan setup untuk mencari
untung: ini rem — ia tidak menambah satu bit pun informasi tentang pasar, tugasnya membuat kami tidak
menerbitkan keputusan yang tidak bisa dibuktikan salah. Baris yang tidak bisa dijawab mesin ditandai **LUBANG**
dan tetap tinggal di daftar; menghapusnya mengubah rem menjadi seremoni.

## Resep

| # | pertanyaan | jawaban mesin hari ini | yang memikul |
|---|---|---|---|
| 1 | **Data cukup umur?** umur snapshot + jumlah bar kandidat | `ADA` — `universe_age_h` ikut di-hash; ambang `MIN_BARS_TINY=720` / `NEED_BARS=2400` ([[Fakta Terukur]] §A/§E) | [[PL1 - Mengumpulkan Data]] · [[EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] · [[01-Agent/A2 - Decision Spine]] |
| 2 | **Arah dari mana?** nama aturan + dari mana ambangnya | **LUBANG** — `side` dan `why` tercetak, tapi tidak ada field yang menyebut apakah aturan itu sudah diuji. Yang terdokumentasi sekarang: §F (rugi 12/12) | [[PL3 - Menganalisis]] · [[QT1 - Dari Ide ke Strategi yang Bisa Diuji]] |
| 3 | **Siapa yang memveto?** ④→`flat`, model hanya boleh mengurangi, kontrak memotong cap | `ADA` — `apply_gates`, `tools/judge.py`, `HARD_CEILING` (§E) | [[01-Agent/A3 - One-Way Gates]] · [[PL2 - Menyaring Universe]] · [[PL4 - Memutuskan]] |
| 4 | **Ukuran dari plafon atau dari selera?** | **LUBANG** — `risk_pct` berasal dari konstanta kode + `conf` (bukan hasil ukur); plafon kontrak memotong di hilir, tapi tidak ada artefak yang menyebut **plafon mana** yang memotong | [[FD6 - Ukuran Posisi]] · [[02-Contracts/C3 - ExecutionVault]] |
| 5 | **Invalidation terhitung sebelum masuk?** stop/target/jarak/horizon | `ADA-TAPI` — `stop`/`target` dari ATR dan `regime` + `horizon_h` tercetak; TAPI `exit-cap <= 1% liq` mengasumsikan jualan **diterima**, dan itu belum diuji di C2/C1 tipis | [[FD7 - Invalidation Stop dan Time-Stop]] · [[I6 - ATR dan Jarak Ternormalisasi]] · [[FD3 - Likuiditas dan Dampak Harga]] |
| 6 | **Ongkos sudah masuk ambang?** | **LUBANG** — `tools/ledger.py` menutup dengan 20 bps, ongkos terukur kami **59 bps**; P10 ditutup 28 Sep (`tools/costs.py`, §D). Angka net hari ini memakai ambang yang lebih longgar 3× dari yang kami ukur | [[FD4 - Ongkos Perdagangan]] · [[Fakta Terukur]] §D |
| 7 | **Horizon tetap & non-overlap?** | `ADA-TAPI` — horizon tercetak dan `ledger.py` memisah `BELUM JATUH TEMPO` / `AMBIGU`; akuntansi non-overlap lintas token/dompet belum ada (§E) | [[FD9 - Horizon Waktu dan Multi-Timeframe]] · [[PL6 - Menilai Hasil]] · [[EV3 - Signifikansi dan Multiple Testing]] |
| 8 | **Apa yang membuat kami abstain?** | `ADA-TAPI` — abstain adalah keluaran gerbang; jumlahnya dicetak penghitung verifik yang dicatat di [[01-Agent/A2 - Decision Spine]] (jalankan sendiri, jangan kutip dari catatan ini). Yang belum: abstain karena "sumber arah tidak punya hasil uji" | [[PL4 - Memutuskan]] · [[FD11 - Aturan Mengalahkan Intuisi]] · [[06-Results/04 - Negative Results]] |

**Baris ke-9 yang belum bisa ditulis:** *"berapa anggota setup ini yang benar-benar independen?"* — tidak ada
perkakas yang menghitung ablasi, jadi pertanyaan itu **LUBANG** dan menuntut [[ST1 - All-Rounder]],
[[ST3 - Clean Price Action]], [[ST4 - Range dan Mean Reversion]], [[ST5 - Trend Rider]] punya definisi event
yang bisa dijalankan.

## Butuh data

| yang dibaca tiap baris | status Fabius | bukti / batas |
|---|---|---|
| umur + isi jejak snapshot universe ① | `ADA` | umur ikut `snapshotHash` dan ikut dibaca ulang ([[01-Agent/A2 - Decision Spine]] · [[03-Data/01 - Dataset]]) |
| riwayat bar kandidat | `ADA-TAPI` | 9.599 bar untuk aset ber-perp; C2/D mentok 1.000 bar ≈ 41,6 hari (§A) |
| hasil uji aturan arah | `ADA` | terdokumentasi, dan isinya negatif (§F) |
| hasil uji tiap setup di `04-Setup/` | `TIDAK-ADA` | belum ada satu pun dijalankan sebagai kesatuan |
| ongkos terukur pada ukuran keputusan ini | `ADA-TAPI` | 59 bps adalah round-trip di venue demo (§D); per-size belum (§D P10) |
| rekaman ⑦ untuk baris 2 versi ST6 | `ADA-TAPI` | point-in-time, jendela lihat 8–13 menit, tanpa riwayat (§B) |

## Uji di Fabius

Checklist ini dianggap **lolos** kalau tiap baris menghasilkan `LOLOS`, `GAGAL`, atau `TIDAK TERUKUR` — dan
ketiganya ikut tercetak di artefak keputusan. Yang menentukan:

1. `TIDAK TERUKUR` **tidak boleh** dibaca sebagai `LOLOS` ([[Concepts/Unmeasured Is Not Clean]]);
   contoh nyata hari ini: `pPOLY is_honeypot=None` tidak dihitung bersih (§F).
2. Ambang yang dipakai adalah ambang produk: `n >= 20` non-overlap, BH α 0,10, fold terbaik dibuang,
   ongkos **59 bps** (§D/§E). Baris 6 belum menegakkan yang terakhir.
3. Gerbang satu arah: checklist hanya boleh **mengurangi** (menolak/kecilkan/meng abstain-kan), tidak pernah
   boleh menaikkan tingkat bukti apa pun ([[01-Agent/A3 - One-Way Gates]] · [[Aturan Subtree]] §"tiga aturan").
4. Cara menguji checklist-nya sendiri: jalankan pada keputusan yang sudah jatuh tempo dan lihat apakah
   ia menghasilkan `ABSTAIN` untuk kasus yang §F sudah bilang rugi. Kalau tidak, checklist-nya hiasan.

Baris 4 dan 6 adalah dua lubang termahal: yang satu membuat ukuran tidak bisa diaudit ke plafonnya, yang lain
membuat angka `net` terlalu ramah.

## Konfluensi atau gaung

Delapan baris, tapi bukan delapan pemeriksaan independen — dan checklist yang baik harus jujur soal itu:

| pasangan | hubungannya |
|---|---|
| baris 1 ↔ baris 7 | sama-sama soal waktu, tapi yang satu umur data masuk, yang lain horizon keluar — tetap perlu dua baris |
| baris 2 ↔ baris 8 | satu gerbang dilihat dua sisi: "arah dari mana" dan "kapan kami diam". Menjawab 2 tanpa menjawab 8 = menghasilkan keyakinan tanpa rem |
| baris 3 ↔ baris 4 | yang satu siapa yang mematikan, yang lain siapa yang menentukan besar — di Fabius keduanya berakhir di kontrak yang sama |
| baris 5 ↔ baris 6 | invalidasi tanpa ongkos = stop yang terasa aman di atas edge yang tidak ada |

Yang tidak boleh terjadi: membaca checklist sebagai **konfirmasi**. Delapan `LOLOS` berarti "keputusan ini sah
diterbitkan", bukan "keputusan ini benar" — ST1–ST6 memproduksi alasan untuk masuk, checklist hanya berhak menguranginya.

## Batas dan mode gagal

- **Mode gagal utama: checklist yang lulus padahal tidak ada yang teruji.** Semua baris `LOLOS` dan sumber
  arahnya tetap aturan yang rugi 12/12 setelah ongkos (§F) — jawaban benar di baris 2 dan 8 adalah abstain.
- **Checklist = ritual kalau tidak ada yang menanggung biayanya.** Yang menahan biaya itu hari ini
  adalah anchor: keputusan diterbitkan sebelum hasilnya ada, dan `ledger.py` menutupnya dari rekaman.
- **Baris yang dihapus = lubang yang ditutupi.** Kalau sebuah baris tidak bisa dijawab mesin, tulisannya
  **LUBANG**, jangan dihapus dari daftar; `tk_check.py` memeriksa bentuk, bukan keberanian.
- **Keadaan hidup basi dalam hitungan jam** (§G): angka `anchorCount()` dan `winlog.py` jangan dikutip
  dari catatan mana pun — jalankan perintahnya.

## Tingkat bukti

`T0` — dan itu bukan hukuman: checklist ini sengaja tidak membuat klaim pasar, jadi tangga bukti untuk metode
tidak berlaku padanya. Yang **berbukti** hanyalah komponen yang sudah jadi kode (baris 1, 3, 5 sebagian, 7
sebagian, 8 sebagian) — itu status data, bukan tingkat bukti. `T3` tidak tersedia di sini dan tidak akan
pernah: yang menaikkan bukti adalah run, bukan daftar periksa.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "Fabius punya delapan pertanyaan yang harus dijawab sebelum menerbitkan keputusan; empat
  di antaranya sudah berupa kode, empat masih lubang yang terdaftar."
- **Dilarang:** "keputusan kami lolos validasi" (lolos checklist ≠ lolos uji) · "agen abstain karena
  hati-hati" tanpa menunjuk gerbang yang memaksa · mengutip jumlah Enter/Abstain dari catatan ini
  sebagai keadaan sekarang · membaca tabel `## Butuh data` sebagai daftar kemampuan.

**Terkait:** [[ST1 - All-Rounder]] · [[ST2 - Futures Hunter]] · [[ST3 - Clean Price Action]] ·
[[ST4 - Range dan Mean Reversion]] · [[ST5 - Trend Rider]] · [[ST6 - Aliran On-Chain Fabius]] ·
[[FD5 - Expectancy Bukan Win Rate]] · [[EV6 - Kalibrasi Ambang Terhadap Hasil]]

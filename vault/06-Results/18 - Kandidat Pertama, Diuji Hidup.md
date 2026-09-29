---
tags: [hasil, "pra-registrasi", "E9", "alasan-masuk"]
---

# 18 - Kandidat Pertama, Diuji Hidup

**Bagian dari:** [[06-Results/00 - Hub Results]] · [[08-Backlog/02 - Epik Alasan Masuk]]
**Status:** TERKUNCI sebelum data replikasi ada · **Alat:** `tools/vol_ab.py` · **Eksekutor:**
`tools/paper_book.py` (lengan `vol-rendah` / `vol-tinggi`, keduanya `--emit` di job `paper-book`)

## 1. Kenapa halaman ini ada

Sampai 29 Sep ±05:00Z tidak ada satu pun fitur yang melewati kontrolnya sendiri. Uji **E7**
(`tools/topk_test.py`, 10 fitur, outcome dari ticker `wp`, ongkos 59 bps, kontrol = acak **sesama
kandidat dalam siklus 30 menit**) menghasilkan satu anomali:

```
   fitur               siklus      n       mean    median      P>=500 acak (CI atas) vonis
   vol_rendah              19     95     +132.9     -59.0       31.6%      -134.3 (  +116.1) DI ATAS ACAR
   di_bawah_puncak60       19     95     +107.1     -47.1       38.9%      -125.8 (  +115.8) di bawah acak
   usd_ge_1k               19     95     -132.0    -121.9       36.8%      -129.6 (  +175.2) di bawah acak
   kluster_beli            19     95     -425.7    -751.1       26.3%      -115.7 (  +131.2) di bawah acak
   (tujuh fitur lain: -403,3 .. -199,2 - semuanya di bawah acak)
```

Angka itu **tidak boleh dijual**, dan alasannya aritmatika, bukan selera: sepuluh fitur diuji
sekaligus, jadi peluang ada satu "menang" walau tidak ada efek apa pun ≈ `10 × 0,025 = 0,25`.
Koreksi Bonferroni atas uji satu arah 2,5 % membuat `vol_rendah` **tidak signifikan**. Yang kita
punya adalah kandidat pertama dalam proyek ini yang arahnya bertahan saat kontrolnya diubah jadi
"pilihan acak pada jam yang sama" — dan satu-satunya yang mengubah kandidat jadi hasil adalah
**data yang belum terjadi**.

Perhatikan juga apa yang TIDAK berubah: `median` lengan pemenang tetap **−59,0 bps**. Harapan
positifnya datang dari ekor kanan (P(≥+500 bps) 31,6 %), bukan dari hasil tipikal. Itu konsisten
dengan seluruh corpus kami dan tidak boleh dibaca sebagai "pendapatan tetap".

## 2. Yang dikunci (teks ini yang di-sha, jangan disunting setelah hasil dilihat)

```text
E9 - A/B terkunci: lengan `vol-rendah` vs lengan `vol-tinggi` pada buku paper.

sumber_aturan : tools/topk_test.py E7 (10 fitur; hanya vol_rendah melewati acak-siklus)
lengan_A      : kebijakan == "vol-rendah" (separuh volatilitas wp terendah kandidat layak harian)
lengan_B      : kebijakan == "vol-tinggi" (kontrolnya, bukan nol)
harga_masuk   : seperti yang dicatat paper_book (tx.peristiwa + haircut dampak s/L)
hasil         : net_bps yang sudah dinilai paper_book (ongkos 59 bps RT sudah dipotong)
perhitungan   : HANYA slot dengan open_utc > t_kunci; slot sebelum kunci = prefill
vonis_layak   : (1) n_A >= 20 DAN (2) median_A > 0 DAN CI bawah bootstrap 4000 (seed 20260928) > 0
                DAN (3) Mann-Whitney satu arah A > B p < 0,05
kalau_kecil   : tulis "BELUM BISA DIUJI", jangan "TIDAK ADA EFEK"; ambang tidak diturunkan
lapor_wajib   : n tiap lengan, P(ada harga keluar), median, mean winso + CI, p MW, token unik
winso         : +/-2.000 bps pada mean (ekornya tebal di dua arah; median dilaporkan terpisah)
jangan        : tidak ada order, tidak ada rantai, tidak ada perubahan promote-after
```

## 3. Perbedaan yang jujur antara backtest dan uji hidup ini

Supaya tidak ada yang boleh bilang "kamu menguji hal yang sama":

| | E7 (backtest, halaman ini §1) | E9 (uji hidup) |
|---|---|---|
| kandidat | semua kejadian beli di feed ⑦ yang punya `wp` | kejadian yang sudah lewat gerbang veto `jual_*` (paper_book) |
| pemilihan | top-5 per siklus 30 menit | separuh volatilitas terendah per hari (budget 6 slot) |
| harga masuk | ticker `wp` terakhir sebelum `t` | harga transaksi `tx.p` (kanonis F-D30) |
| hasil | `wp` median pada t+[15;45] m | `net_bps` yang sudah dinilai paper_book (ongkos + haircut dampak s/L) |
| kontrol | acak sesama kandidat siklus itu | **lengan `vol-tinggi` pada jam, feed, dan gerbang yang sama** |
| volatilitas | `pstdev` return dari ≤40 baris `wp` terakhir | sama (`vol_sebelum()` disamakan, lihat catatan di bawah) |

Versi pertama `vol_sebelum()` membatasi jendelanya ke **30 menit** dan mengembalikan `None` untuk
**semua** kejadian: ticker watch hanya berdetak sekali per siklus rekaman (±35 menit), jadi 12 baris
dalam 30 menit tidak pernah ada. Kalau itu dibiarkan, A/B hidup ini menguji aturan yang berbeda dari
yang diukur — dan kegagalannya tidak kelihatan dari angkanya sendiri, karena "0 posisi" terlihat
seperti "belum ada yang layak".

## 4. Cara menjalankan

```bash
python -X utf8 tools/vol_ab.py --self-test    # 4 kasus: prefill dibuang, 3 syarat serentak,
                                              # n kecil != gagal, A==B tidak pernah LAYAK
python -X utf8 tools/vol_ab.py --lock         # pasang kunci SEKALI (menolak dobel = spec baru)
python -X utf8 tools/vol_ab.py --status       # umur kunci + jumlah slot per lengan
python -X utf8 tools/vol_ab.py                # vonis (menolak cetak angka sebelum matang)
python -X utf8 tools/vol_ab.py --tanpa-umur   # bacaan sementara, dicetak dengan LABEL PERINGATAN
```

Job `paper-book` (cron `23 */4`) membuka kedua lengan tiap empat jam; slot sebelum `t_kunci` adalah
prefill dan **tidak ikut vonis**. Kalau pada saat matang `n < 20`: vonisnya `BELUM BISA DIUJI`,
ambang tidak boleh diturunkan, dan itu bukan "tidak ada efek" ([[Concepts/Unmeasured Is Not Clean]]).

## 5. Hasil

_kosong sampai umur kunci cukup — alatnya menolak mencetak angka sebelum itu, dan kekosongan ini
adalah bagian dari spesifikasinya, bukan kelalaian mencatat._

**Terkait:** [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] ·
[[06-Results/17 - Pra-Registrasi Watch]] · [[08-Backlog/02 - Epik Alasan Masuk]] §3d ·
[[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]] · [[Concepts/One-Way Gate]] ·
[[00-Overview/03 - Decisions]] F-D37/F-D38

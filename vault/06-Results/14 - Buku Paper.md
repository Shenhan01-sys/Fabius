---
tags: [hasil]
---

# 14 - Buku Paper

**Sumber:** `tools/paper_book.py` → artefak kanonik `paper-book-20260928T110708Z.json` (`first`),
`…T110731Z.json` (control `random`), `…T110736Z.json` (`lock`), `…T110739Z.json` (budget kontrak
5/hari @1 BNB), `…T110905Z.json` (emit slot) · 28 Sep 11:07-11:09Z · 556 posisi paper dari 1.014
kejadian yang boleh

**Sembilan artefak dari jam 10:58-11:06Z dibuang, bukan disimpan sebagai jejak**: isinya berisi
`vonis_kebijakan` keluaran gerbang yang masih bisa mempromosikan control-nya sendiri. Jejak angka
yang salah hitung boleh ditinggalkan; vonis yang salah tidak - yang pertama bisa dikutip sebagai
kesalahan, yang kedua sebagai izin.

**Ringkas:** builder meluruskan satu hal yang kutukar: yang diminta bukan order sungguhan, tapi
**paper trading**. Begitu posisi boongan boleh diambil, hambatan "tidak ada fill/kedalaman" turun
kelas dari *larangan* jadi *kewajiban melapor*. Alat ini jadi buku yang bisa dijalankan tiap hari -
dan scoreboard pertamanya langsung membatalkan kandidat masuk terbaikku.

## 1. Empat kebijakan pada buku yang sama

Semua: harga PERISTIWA (`tx.t`,`tx.p`), ongkos 59 bps round-trip (`measured-own-venue`), horison
30 menit, mean di-winsor ±2.000 bps, budget paper 200 posisi/hari (kontrak `dailyCap` = 5, disebut
terpisah), 3 hari teramati:

| kebijakan | dampak 0,01 BNB/posisi | dampak 1,00 BNB/posisi | median | P(≥+500) | tanpa angka likuiditas |
|---|---|---|---|---|---|
| **random** (veto ON, pilih acak) | **+188,3** | +115,6 | −58,9 | 35,6 % | 454/556 |
| **first** (veto ON, yang pertama datang) | +140,9 | +56,6 | −59,2 | 32,6 % | 432/556 |
| **lock** (veto ON, urut `lock_percent`) | +109,7 | **−51,2** | −60,0 | 29,9 % | 397/556 |
| **tanpa-gerbang** (veto OFF) | +95,1 | +17,0 | −59,4 | 30,7 % | 445/576 |

Tiga bacaan, dan yang kedua tidak enak:

- **Veto terbukti lagi, kali ini sebagai kebijakan, bukan sebagai uji.** random (dengan veto)
  **+188,3** vs tanpa-gerbang **+95,1** = **~+93 bps/posisi** hanya dari menolak kerumunan jual.
  Ini angka yang sama dengan `tools/policy_test.py` (+79,6) di set yang berbeda - dua pengukuran
  terpisah, arah sama.
- **Kandidat `lock_percent` MATI sebagai kebijakan.** Di §3d halaman 13 dia lolos dua uji; di buku
  ini dia **kalah dari memilih acak** (+109,7 vs +188,3), dan di ukuran 1 BNB dia satu-satunya yang
  **negatif** (−51,2). Sebabnya persis perangkap cakupan di §3e: menyortir pada `lock_percent`
  memaksa kita memilih pool yang *punya* data (397/556 vs 454/556 tanpa-liq) - dan subset yang bisa
  dideskripsikan itu baseline-nya **−64,7 bps**, bukan +82,7. Jadi yang kunyaris "fitur terbaik"
  sebenarnya **proxy untuk subset yang paling buruk**.
- **Ukuran itu nyata walau di paper.** Naik dari 0,01 → 1,00 BNB memangkas mean ~**70–90 bps/posisi**
  (192,8 → 115,6 pada acak): itu dampak harga 2·s/L dua kaki pada likuiditas yang kita tahu. Satu
  kaki lainnya diam: **454 dari 556 posisi tidak punya angka likuiditas sama sekali**, jadi haircut
> **⚠ KOREKSI 29 Sep 08:56Z - "dampak" di halaman ini bukan dampak (F-D46).**
> `tools/impact_audit.py` mengaudit 702 slot: `haircut()` membagi **size dalam BNB** dengan
> **liq dalam USD** (±600x terlalu kecil; median `dampak_bps` tercatat 0,00), dan desil terbawah
> `liq` adalah **$1 dan $0** - di sana x·y=k memberi 120.000 bps, yang benar cuma "sampah".
> Tiga varian, satu jalur data: **tercatat +75,9** · **satuan-dibetulkan −715,7** ·
> **hanya-liq-sah (floor $1.000) −87,8 bps**. Jadi setiap "+xxx bps/posisi" di bawah adalah
> *net of ongkos 59 bps dan hampir nol dampak*. Kode tidak diubah malam ini karena E9/E12 sudah
> terkunci pada definisi yang dicatat - perbaikan di P42, setelah kedua vonis jatuh.
  mereka nol - dan itu membuat angka setinggi apa pun di tabel ini masih **optimis**, bukan seram.

## 2. Batas yang tidak bisa dibeli oleh status "paper"

- Median semua kebijakan **−59 bps** = persis ongkos. Yang positif adalah **ekor**, jadi skor buku
  ini digerakkan oleh puluhan kejadian besar; satu 10x di pool berisi 25 posisi bisa memindahkan
  mean puluhan bps. DayaStatistik yang sama tetap berlaku: ~68 posisi untuk resolusi 200 bps.
- Harga keluar = median transaksi berikutnya di jendela, di pool yang sama, tanpa antrean, tanpa
  sebagian terisi, tanpa slippage lintas pool, dan **tanpa pertanyaan apakah kami bisa keluar sebesar
  itu**. Paper menghapus syarat eksekusi, tidak menghapus syarat aritmetika.
- Satu jendela ~50 jam, satu rezim. Semua baris tabel ini adalah keadaan rekaman, bukan klaim
  produk - dan tidak akan muncul di materi submission dengan kata "untung".

## 3a. Label dan aturan naik - supaya jelas mana yang nanti jadi posisi asli

Builder menyetel bentuknya: *paper dipakai untuk memastikan analisis benar sebelum uang turun;
misalnya 2 kali prediksi paper benar baru berani posisi asli; selama development full paper, tapi
yang paper itu diberi label karena dia yang akan ditambal posisi nyata.* Itu sekarang ada di alat,
bukan di niat:

- tiap slot ditulis ke `decisions/paper-book-positions.jsonl` dengan `mode: "PAPER"`, `slot_id`
  (sha256 dari token×waktu×kebijakan - jadi identitasnya tetap kalau isinya dibaca ulang),
  dan **`pengganti_real: null`** yang baru terisi oleh tx asli yang menambal slot yang sama;
- `tools/winlog.py` kini mencetak **tiga seri terpisah** dan menolak menggabungkannya:
  `PAPER` (keputusan ter-anchor vs bar Aster) · `BUKU PAPER ⑦` (slot boongan pada harga peristiwa)
  · `CHAIN` (fill nyata di pool kami). Yang tercetak sekarang: 556 slot dinilai, **0 layak real**,
  **0 ditambal posisi asli**;
- aturan naiknya dua lapis, dan lapis keduanya penting. Streak N benar beruntun (default 2)
  **dicatat**, tapi bukan vonis: peluang menang kita 42,3 %, jadi dua menang beruntun terjadi
  **~18 % dari waktu itu tanpa ada efek apa pun** - streak itu bukan kredensial, itu kebetulan yang
  urutannya kita pilih sendiri. Vonisnya = gerbang F-D16 (n≥20 DAN harapan > 0 DAN **CI bawah
  harapan** > 0) **DAN kebijakan harus di atas control `random+veto`**.

Vonis malam ini, pada 556 slot (0,01 BNB, 200 posisi/hari paper):

> **⚠ Baca +188,3 dengan satuannya (29 Sep 08:5xZ, F-D46).** Angka di halaman ini adalah
> *net of* ongkos tetap **59,0 bps** dan **hampir nol dampak**: `haircut()` kami membagi
> **size dalam BNB** dengan **liq dalam USD** (±600x terlalu kecil), dan desil terbawah
> `liq` adalah $1/$0. Diukur ulang pada jalur yang sama (`tools/impact_audit.py`, 702 slot):
> **tercatat +75,9 · satuan-dibetulkan −715,7 · hanya-liq-sah −87,8 bps**.
> Kodenya sengaja belum diubah karena E9/E12 terkunci pada definisi yang dicatat - tapi nomor
> tabel di bawah tidak boleh lagi dikutip tanpa kalimat ini.
> **⚠ KOREKSI KEDUA (29 Sep 11:5xZ, F-D51) - tabel ini juga artefak budget.** Di berkas peristiwa
> yang sama (1.884 kesempatan, 4 hari), control `random` memberi **+165,7 pada 200 posisi/hari**
> (n=800), **−100,2 pada 24/hari** (n=96, yang CI tulis), dan **−26,7 pada 5/hari** (n=20, budget
> kontrak kita). `lock` berturut-turut +79,4 / −160,8 / −161,5. Jadi angka +188,3/
> "veto bernilai ~+93 bps" adalah properti **satu jendela pada satu budget**, bukan properti
> strategi - dan di budget nyata kita **tidak ada arm yang mengalahkan control-nya sendiri**.

| kebijakan | winso mean | CI 95 % | vs control (+188,3) | layak posisi asli? |
|---|---|---|---|---|
| `first` (datang dulu, diloloskan gerbang) | +140,9 | [+35,0; +249,2] | di bawah | **BELUM** |
| `lock` (urut `lock_percent`) | +109,7 | [+2,4; +215,5] | di bawah | **BELUM** |
| `random` = CONTROL | +188,3 | [+79,2; +300,7] | dialah pengukurnya | **tidak pernah** |
| `first` pada budget kontrak (5/hari, 1 BNB) | **−708,9** | lo −1.291,5 | - | **BELUM** |

Bacaan yang harus disebut: kontrol acak dengan gerbang yang sama **mengalahkan kedua aturan
pilihan kita**. Artinya yang terukur +188,3 itu sebagian besar adalah *"feed ini sedang
menunjukkan token yang sedang naik"*, bukan *"Fabius bisa memilih"*. Dan pada budget/ukuran nyata
kontrak (5 posisi/hari, 1 BNB), buku ini **minus 708,9 bps** - jadi status "paper" tidak membuat
hasilnya jadi positif; dia hanya membuat kita boleh mengukurnya sekarang.

## 3. Apa yang dibuatnya mungkin besok

Buku ini bisa dijalankan **tanpa keputusan manusia** dan tiap jalannya mencetak `rows_sha256`
**atas isi bukunya** (daftar slot, bukan tabel perbandingan - tabel punya hash sendiri,
`sha_perbandingan`) sehingga sha yang diperiksa orang di chain adalah sha dari daftar posisi
yang sama, yang nanti akan ditambal posisi asli. Yang meng-anchornya: `tools/anchor.py` (kirim hash keputusan nyata lalu baca ulang dari chain dan bandingkan word per word). Itu artinya: kalau kita pasang dia di rantai
harian, maka mulai besok tiap hari ada **rekaman keputusan + hasilnya yang terikat waktu**, bukan
satu tabel yang dibuat malam sebelum tenggat. Itu P28.

Baca ulang: `python -X utf8 tools/paper_book.py --per-day 200 --size-quote 0.01` ·
`python -X utf8 tools/paper_book.py --per-day 200 --size-quote 1.0`

**Terkait:** [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] · [[06-Results/07 - Matured Outcomes]] ·
[[06-Results/12 - Harga Masuk yang Benar]] · [[06-Results/07 - Matured Outcomes]] ·
[[03-Data/D2 - Wallet Flow]] · [[TradingKnowledge/FD3 - Likuiditas dan Dampak Harga]] ·
[[TradingKnowledge/FD6 - Ukuran Posisi]] · [[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]]


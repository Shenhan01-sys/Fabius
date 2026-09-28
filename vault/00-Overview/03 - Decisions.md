---
tags: [overview]
---

# 06 — Keputusan

Penomoran `F-D##` khusus jalur ini. Tidak menyentuh `D##` vault induk, supaya tidak ada dua
nomor yang berarti hal berbeda di dua tempat.

## F-D01 — App baru, bukan port atau edit HeliQuant · 22 Sep 2026

Ditulis **baru** di workspace sendiri. HeliQuant hanya rujukan baca: tidak difork, tidak
dibranch, tidak disalin modul/prompt/skemanya.

Alasan, dan semuanya terukur:
1. `github.com/HeliQuant` = **8 repo, semuanya `private=False`**, nol fork, push terakhir
   **21–22 Juni 2026**. FAQ #08 menuntut core product baru yang dibangun selama periode acara.
   Menaruh commit akhir September di atasnya = menyerahkan sendiri bukti bahwa ini port, ke
   pihak yang paling berwenang menilainya.
2. Tidak menghemat kerja: ±3.900 baris tetap harus ditulis baru.
3. Venuenya mati dari mesin ini (Bitget/Binance/OKX/Bybit kena intersepsi TLS).

Yang menyebrang: pola (refusal-first, abstain-with-reason, registry boleh kosong,
withheld-until-earned, candidate-vs-validated), metodologi, dan **angka sebagai rujukan
ber-`file:line`**. Keputusan yang sama sudah diambil builder untuk jalur kredensial
(`AgenticTrack/README.md`).

## F-D02 — Nama: `Fabius` · 22 Sep 2026

Dari Quintus Fabius Maximus *Cunctator*: mengalahkan Hannibal dengan tidak memberi pertempuran
yang Hannibal inginkan. Roma kalah di Cannae karena ingin bertempur.

Dipilih setelah kandidat lain diuji, bukan berdasarkan selera:
- **`Augur`/`Oracle` ditolak karena prinsip** — nama yang mengklaim kenabian merusak satu-satunya
  pembeda kita: kami tidak mengklaim bisa meramal. (`Augur` juga nama protokol prediction market
  lama, akan dibaca juri crypto sebagai rujukan.)
- `Saring` dipakai sebentar lalu ditinggalkan: ia hanya menyebut sebagian bawah produk (menyaring),
  dan membuat agen terdengar seperti filter, bukan pengambil keputusan.
- Ketersediaan terukur 22 Sep: `fabius.id` bebas; semua username GitHub kandidat sudah terisi —
  tidak relevan, repo hidup di bawah akun yang ada.
- Cadangan yang masih setara: `Ballast` (Inggris polos, risiko-dulu), `Arbiter`, `Tenax`,
  `Cunctator`.

Riwayat commit dipertahankan saat rename (`git` tidak menyimpan nama folder), jadi bukti
orisinalitas tidak putus: `476c950` kontrak + 21 test, `0b5b9a6` screener per-token, `de48d9f`
kompatibilitas skema.

## F-D03 — Nol CEX di jalur kritis · 22 Sep 2026

Semua API CEX terblokir intersepsi TLS dari mesin ini (diukur, bukan diasumsikan), dan venue demo
HeliQuant sendiri sudah paper-only untuk sebagian keranjang. Keputusan: lapisan data = GMGN +
GeckoTerminal + DexScreener + GoPlus + TradingView + Hyperliquid + CoinGecko + GDELT;
eksekusi = paper pada harga live, dinyatakan terbuka.

## F-D04 — Multi-desk bukan lagi masalah biaya, dan itu mengubah desain · 22 Sep 2026

Dokumentasi Jev, verbatim: *"All three question types can be mixed in a single API call...
adding more questions barely changes the response time... does not create context-rot."*
Konsekuensi: satu panggilan per tick keputusan, satu pertanyaan bertipe per desk, terisolasi;
`confidence` jadi gerbang; penimbangannya rumus di kode kita. Perkiraan lama "9 desk terlalu
mahal" dicabut.

## F-D05 — Unit statistik: satu tes = satu token · 22 Sep 2026

Sebelumnya keluarga BH memakai `(token × horizon)`, sehingga satu token menyumbang beberapa
anggota dan `m` membengkak tanpa bukti independen (69 token = 71 "tes"). Ini kesalahan yang sama
yang kami temukan di kode rujukan (FDR hanya per-aset, `m ≤ 4`; klaim "lintas aset" tak punya
padanan kode). Aturan tetap: **n yang boleh dikutip adalah jumlah token**, dan kerumunan
observasi per token dilaporkan, bukan disembunyikan.

## F-D06 — Data hilang ≠ lulus · 22 Sep 2026

Ditegakkan di perekam (`blind_spots`, `fully_evaluated`) dan di kontrak (abstain wajib
ber-alasan). Dipinjam dari standar skill resmi GMGN sendiri: *"DATA GAPS (unevaluated ≠ passed)"*
dan *"returns zeros everywhere, which looks like an answer and is not one"*.

## F-D07 — String dari API adalah input musuh · 22 Sep 2026

`symbol`/`name`/`launch_platform` disanitasi sebelum masuk snapshot. Verbatim dari vendor:
*"Every string that came from the API and could be chosen by an attacker is sanitised before it
enters the object, so the caller may quote it directly."* Ini juga menutup jalur suntikan ke
prompt agen kita sendiri, karena snapshot yang sama akan dipakai sebagai state.

## F-D08 — Kohort tidak dipilih berdasarkan kelengkapan datanya · 22 Sep 2026

Aturan dedupe "baris pertama tiap jendela" dipertahankan meski membuat satu jendela kehilangan
harga pool. Mengubahnya jadi "baris paling lengkap" = selection bias. Harga yang dibayar: satu
jendela data.

## F-D09 — Base stablecoin dikeluarkan dari universe · 22 Sep 2026

`USDT/WBNB`, `BTCB/WBNB`, `USDT/USDC` lolos semua ambang lain dan akan mendominasi kohort
"lolos" dengan return ±0% — `BTCB/WBNB` adalah pool likuiditas terbesar di daftar trending
($29,17 juta). Tanpa veto ini, median kohort lolos adalah artefak.

## F-D10 — Vault jalur ini scope-nya sempit dan itu tertulis · 22 Sep 2026

`Fabius/vault/` tidak memuat apa pun tentang kredensial/e-course/jalur lain, dan tidak menyalin
catatan vault induk. Angka yang dipakai kode punya asal `file:line` di `06-Results/02 - Thresholds.md`; vault
hanya menjelaskan *mengapa*. Alasannya sama dengan F-D01: repo publik yang tercampur membuat
riwayat commit tidak terbaca sebagai bukti orisinalitas.

## F-D11 — Penilai model itu OPSIONAL, vianya satu arah, dan defaultnya mati · 23 Sep 2026

Builder: *"untuk Jev mungkin bisa km buat optional ya, takutnya kalau berbayar ya mau gamau kita
pakai LLM lain."* Bentuk yang dipasang di `tools/judge.py` + `tools/decide.py --judge`:

- **`--judge none` adalah default.** Tidak ada satu pun panggilan berbayar yang terjadi tanpa
  diminta. `auto` = Jev dulu (kunci `~/.config/typesafe/.env`), lalu LLM OpenAI-compatible mana pun
  lewat `HQ_BASE_URL`/`HQ_API_KEY`/`HQ_MODEL` — jadi "LLM lain" itu **satu perubahan env, bukan
  perubahan kode**.
- **Arah satu jalan.** Penilai hanya boleh **membatalkan** `ENTER` menjadi `ABSTAIN`. Tidak ada
  jalur yang mengubah `ABSTAIN` menjadi `ENTER`. Ini "repair-never-up" + "spend limits are
  enforced independently from model output" (skill `llm-trading-agent-security`).
- **Hasilnya ikut di-hash.** `judge` (provider, model, veto_prob, dominant_risk, confidence,
  probabilities) masuk `decisionHash`/`gatesHash` → kalau nanti di-anchor, penolakan model ikut
  terbukti, bukan hilang di log mesin kita.
- **Kegagalan penilai = tidak naik kelas**, bukan = lolos. JSON tak terparse / HTTP gagal →
  kandidat tetap `ABSTAIN` dan alasannya tercatat.
- **Biaya ikut di artefak** (`cost_usd`), supaya klaim murah bisa diperiksa.

Terukur 23 Sep pada jendela 140 kandidat: **1 panggilan Jev = $0,00002407, 0,43 detik**,
`jev-1.13.0`, dan hasilnya **veto** dengan dasar yang bisa dibaca:
`dominant_risk=bundled_volume`, `probabilities={bundled_volume 0.63, illiquidity_exit 0.14,
lp_pull 0.12, none 0.11, young_history 0.0}`, `confidence 0.54`. Efeknya pada kita:
`ENTER 1 → 0`. Yang **belum** terbukti: apakah veto model lebih baik dari diam — itu pertanyaan
kalibrasi (F-D12), bukan klaim.

## F-D12 — Kalibrasi diukur dengan data kita sendiri, bukan dengan demo · 23 Sep 2026

Satu-satunya alasan memakai model adalah kalau `confidence`-nya **berarti**. Yang akan diuji, dan
sudah punya bahan: keputusan (dengan `confidence`/`veto_prob`) di satu sisi, hasil forward token
yang sama di sisi lain. Kalau `confidence` tinggi tidak membedakan hasil dari `confidence`
rendah, Jev **dicabut** dan kita kembali ke gerbang deterministik — dan keputusan itu yang dicatat,
bukan cuma angkanya. Batas yang harus ikut tertulis: `max gain sejak trigger` semacam itu
dipilih setelah sinyal terbit, jadi tanpa catatan point-in-time ia survivorship, bukan edge.

## F-D13 — Lapisan arah diuji lebih dulu, kalah, dan TETAP di-anchor · 25 Sep 2026

Urutan kerjanya sengaja dibalik dari kebiasaan demo: lapisan arah (`direction.py`) dibangun,
lalu **langsung diuji** terhadap 400 hari deret Aster yang sama yang dipakai agen live
(`tools/backtest.py`, ambang diimpor dari kode, tidak di-fit), bukan sesudah submit. Hasilnya ada
di `06-Results/04 - Negative Results.md`: net **negatif di 12/12** simbol saat gerbang |acf| dicabut,
gross hanya +1,5…+4,0 bps pada empat simbol yang lolos gerbang (vs ongkos 20 bps RT), arah
dibalik pun tetap kalah (−39,2…−12,1), dan di horizon 24 j hanya TAC yang positif setelah
fold terbaik dibuang — dengan `t = 0,31` dan lima fold `+114 +298 −197 +381 −153`, yang bukan edge
melainkan skew.

Keputusan yang diambil dari angka itu, dan alasannya:

1. **`Enter` yang sudah masuk chain TIDAK ditarik dan tidak disembunyikan.** Dua anchor MARSCOIN
   short (blok 132955030 dan 132955788) dibiarkan jatuh tempo. Menghapus prediksi yang kita tahu
   lemah akan menghancurkan satu-satunya nilai artefak ini: bahwa jejak itu dibuat **sebelum**
   hasilnya ada. Yang kami tambahkan justru kebalikannya — halaman uji ini, yang menuliskan
   kelemahannya sebelum ada yang membacanya sebagai klaim untung.
2. **README/submission hanya boleh memakai kalimat yang terbukti.** Yang boleh: agen menyimpan
   keputusan yang bisa dibuktikan salah, dan menolak 100 % sinyal arah pada aset terdalam karena
   derivatifnya mendekati jalan acak. Yang **tidak** boleh: "memperdagangkan meme dengan edge".
3. **Gerbang |acf| dipertahankan** meski dia "membuang" peluang. Setelah diukur, penolakannya
   justru tepat: sinyal yang dia padamkan rugi di semua simbol. Pagarnya bekerja; isinya yang belum.
4. **Yang dianggap utang, bukan hasil**: funding historis belum ikut diuji (gerbang carry absen di
   backtest), bidang ④ `can_not_sell`/honeypot belum diukur sama sekali, dan 12 simbol ini bergerak
   dengan satu pasar yang sama — jadi "0 dari 12" bukan 12 percobaan bebas.

## F-D14 — "Belum diukur" bukan "bersih", dan satu kolom tidak boleh mengklaim tiga syarat · 25 Sep

Bidang ④ akhirnya diukur (`tools/security_gate.py`) karena skala jalur arah memungkinkannya:
`vault/05` #12 sudah membuktikan rute security GMGN tidak menerima daftar alamat, jadi 40
alamat/snapshot di jalur screen tak terbayar — tapi kandidat arah tinggal ≤5, yaitu 10 panggilan
(GMGN + GoPlus) per siklus. Terukur 5/5 kandidat membalas 200; `is_honeypot` benar-benar boolean
(bukan string), dan GoPlus TIDAK punya `can_not_sell` sama sekali.

Tiga aturan yang diputuskan di sini, bukan sekadar diprogram:

1. **Empat status, bukan dua.** `OK` / `BLOCKED` / `DISAGREE` / `UNMEASURED`. Yang terakhir
   terpicu nyata pada pPOLY (`is_honeypot=None` dari GMGN): kalau "tidak ada angka" disamakan
   dengan "bersih", gerbang ④ bisa dibypass cukup dengan membuat panggilannya gagal — dan
   kegagalan itu tidak meninggalkan bekas di data. Sekarang dia meninggalkan bekas:
   `sellability` ikut masuk `gatesHash`.
2. **④ hanya boleh mengurangi.** Satu-satunya jalan ④ mengubah `side` adalah `BLOCKED → flat`.
   Tidak ada jalur di mana kontrak yang "bersih" membuka posisi yang gerbang lain tolak — sama
   seperti doktrin satu-arah `judge.py` (F-D11).
3. **Kolom `kursi` harus berisi semua syarat kursi.** Versi pertama (`apply_security`) menetapkan
   `seat_eligible = (④ OK)` dan mencetak YA untuk kandidat yang tak punya likuiditas. Itu bukan bug
   kecil: nama kolom dibaca orang sebagai kesimpulan. `apply_gates()` sekarang menegakkan ①+④+⑥
   (vault/08 §3) dan menyimpan `seat_blockers` — dan langsung terbukti menggigit: `GENIUSUSDT`
   bersih di ④ dengan 3.940 bar di ①, tapi kursinya ditolak karena `⑥liq=$19.388 < $50.000`.

Batas yang harus ikut tercatat: yang diukur adalah honeypot **token spot**, jadi ini membuktikan
dasar harga perp tidak bisa disandera oleh kontrak yang menolak penjualan — BUKAN membuktikan
posisi perp bisa ditutup di venue-nya. Dan dua sumber tidak sepakat soal pajak jual (GMGN 3 % vs
GoPlus 0 % pada MARSCOIN/ASTEROID); ambang `DISAGREE` dipasang di ≥5 % sehingga kasus 3 % ini tetap
`OK` — itu pilihan kami, dan karena itu dituliskan, bukan dibenamkan.

## F-D15 — Dibayar per keputusan, lewat x402; abstain tidak ditagih · 26 Sep 2026

Satu ringkasan keputusan = 1.000 atomic (0,001 token demo) ke proxy kanonis x402 di 97.

Alasan bentuknya: agen pembayar tidak punya alasan menerima tagihan yang angkanya dibuat-buat per
pelanggan, dan "gratis saat kami tidak tahu" adalah satu-satunya tarif yang membuat kami kehilangan
uang ketika kami asal bunyi. Terukur 26 Sep: tx `0xb6093e59…` `status=1`, pemindahan token dibaca
ulang dari chain, bukan dari log server kami — [[05-Ecosystem/02 - x402 Payment]].

## F-D16 — Gerbang "real trade" = harapan bersih, bukan win-streak · 26 Sep 2026

Builder minta gerbang "trust di atas 60 % baru buka posisi". Metriknya diganti, tujuannya diambil.
Gerbang yang berlaku: `net expectancy > 0` setelah ongkos nyata di ukuran itu, `n ≥ 20`, tetap
positif setelah fold terbaik dibuang, lolos BH α=0,10, dihitung di luar sampel.

Contoh yang membunuh win-rate sebagai ukuran (semuanya keluaran alat kami sendiri): panel whale
**WR 69,8 %** tapi jam-per-jam **−10,4 bps**; satu posisi MARSCOIN **MENANG** dengan net **+1,5 bps**.
Konsekuensinya sekarang: `n=2` → belum boleh real sama sekali. Rinci di
[[01-Agent/A4 - Trust Gating and Real-Money Rules]].

## F-D17 — Fee-on-profit yang diambil dari wallet user ditolak sebagai default · 26 Sep 2026

"Admin fee 5–10 % dari untung user via x402 yang sudah terhubung ke wallet-nya" berarti kami
memegang izin yang bisa memindahkan dana user. Izin itu tidak punya versi aman, dan menjual bagian
dari keuntungan klien itu wilayah nasihat investasi/pool dana (Bappebti/OJK).

Yang dipakai: **abstain gratis** + **kredit yang bisa diaudit** kalau ledger memvonis RUGI. Tidak ada
uang keluar dari wallet siapa pun, risiko kesalahan tetap di kami. Success fee tidak dilarang
sepenuhnya — bentuk yang bisa diterima adalah user menandatangani sendiri pembayaran per kejadian,
jumlah dibatasi di muka, bisa dicabut; itu opsi, bukan default, dan kalau dibangun, risiknya ikut
ditulis di halaman itu.

## F-D18 — Kurva harga "yang datang lebih awal dapat untung lebih besar" ditolak · 26 Sep 2026

Tidak ada sumber kas di produk ini (tidak ada deposit, tidak ada custody), jadi imbal hasil peserta
awal **hanya** bisa berasal dari uang peserta yang datang kemudian. Itu transfer, bukan return, dan
membentuknya sebagai fitur berarti menjual skema. Yang boleh: kurva di sisi **biaya** (pembeli awal
bayar lebih murah). Yang tidak boleh: janji imbal hasil.

## F-D19 — Dua pintu masuk, satu kebenaran · 26 Sep 2026

Agen lain: ERC-8004 (`tokenId 2494`) + kartu agen + bayar per permintaan. Manusia biasa: satu halaman
web yang menunjukkan surat keputusan yang sama, termasuk **penolakan**. Aturan yang mengikat keduanya:
satu angka, satu sumber — halaman manusia tidak boleh menghitung ulang apa yang dibaca agen dari
chain. Rinci di [[00-Overview/02 - Business Process]] dan [[05-Ecosystem/03 - Discovery Gap]].

## F-D20 — Deploy eksekusi ke 97 lebih dulu; FE setelahnya, di Vercel oleh builder · 27 Sep 2026

Urutan dipilih builder, bukan olehku: bukti dulu (jalur posisi nyata di testnet), lalu permukaan.
Hosting FE di **Vercel**, dikerjakan builder — jadi FE tidak masuk jalur kritis klaim mana pun
sampai benar-benar ada, dan vault tidak menulis "web sudah live". Lihat [[08-Backlog/01 - Backlog]]
P1/P3 dan [[00-Overview/06 - Roadmap]].

## F-D21 — Vault disusun ulang meniru pola vault Lencana, dengan penyimpangan tercatat · 27 Sep 2026

Struktur yang diadopsi: folder `NN-Name/`, satu hub per modul, part note berafiks ID
(`A2`, `C3`, `TL5`…), `Concepts/`, `Templates/`, skrip perawatan, `_Auto-Index` hasil generate,
dan dua aturan induk: **run menang atas halaman** dan **klaim tidak boleh melebihi yang diukur**.

Yang sengaja berbeda (dan alasannya ada di [[Conventions]] §Beda sadar): catatan berbahasa Indonesia,
skrip perawatan Python bukan PowerShell (PowerShell 5.1 di mesin ini pernah menanam BOM ke berkas
Solidity), dan ID keputusan `F-D##` — karena nomor `D##` sudah dipakai vault induk dan tabrakannya
nyata. Kontennya tidak disalin dari Lencana: yang ditiru adalah format, bukan fakta.

## F-D22 — Atribusi commit: builder saja, tanpa trailer AI · 27 Sep 2026

Builder mengoreksi keras setelah commit kami membawa `Co-Authored-By: Claude`:
*"sejak kapan kita build bareng claude? … Kita gaada build sama sekali dengan claude."* Aturannya:
**tidak ada trailer atribusi AI di pesan commit manapun**, dan author git tetap identitas builder
yang sudah terkonfigurasi (`Hans Gunawan <hansgunawan775@gmail.com>`).

Ini bukan soal gaya. Repo ini publik dan dibaca sebagai bukti kerja siapa: klaim kontribusi adalah
klaim faktual, dan trailer yang salah tidak netral - ia memindahkan kredit ke pihak yang tidak
memegang arah pekerjaan.

**Yang dilakukan (terukur, bukan dirasa):** trailer ditemukan di **2** commit Fabius (`08cb049`
restructure vault, `5e4468f` P1+P8). Menghapus yang lama berarti menulis ulang **147 commit** -
termasuk ±143 commit perekam `wallet flow` yang sudah publik - karena hash rantai. Builder memilih
menulis ulang yang terbaru saja: **3 hash berubah** (`5e4468f` → `1f0faec` + dua turunannya),
diverifikasi `git diff` kosong terhadap tip origin sebelumnya (`defa461`) sehingga **isi tidak berubah
sedikit pun**; commit perekam yang masuk di tengah rewrite dipetik dulu sebelum
`--force-with-lease`, supaya tidak ada jendela aliran yang hilang; ref cadangan
`backup/pra-strip-trailer` ditinggalkan di repo lokal.

Konsekuensi yang diterima sadar: satu commit lama (`08cb049`) tetap menampilkan trailer itu. Kalau
suatu hari rentang 147 commit itu jadi murah (mis. riwayat di-squash untuk submission), yang
tersisa tinggal menghapusnya sekali lagi.

**Tambahannya hari itu juga: pager global dicabut, penegakan pindah ke repo.** Percobaan pertama
menegakkan aturan ini dengan *session hook* global (`~/.qwen/settings.json` -> `hooks.PreToolUse`).
Path perintahnya kutulis berkutip; shell di mesin ini mengirim kutip itu sebagai bagian dari nama
berkas, python keluar dengan kode 2, dan karena 2 = "blokir", **semua** tool tulis/terminal sesi itu
tersumbat — bukan cuma guardnya yang mati, kerjanya juga. Builder menyuruh mencabutnya. Sekarang:
aturan di `~/.qwen/QWEN.md` (instruksi), `vault/scripts/prepush_check.py` (perintah yang bisa
dijalankan siapa pun; `--self-test` 6/6; `--all` pada 393 commit menemukan tepat 1 pelanggaran =
`08cb049`, yang memang ditinggalkan sadar), dan `.github/workflows/attribution-guard.yml` (jalan di
server tiap push). Pelajaran yang lebih umum dari soal atribusi: **gerbang penegak aturan harus gagal
dengan cara yang tidak melumpuhkan pekerjaan**, dan ia diuji lewat jalur nyata tempat dia dipanggil —
bukan cuma lewat logikanya.

**Terkait:** [[00-Overview/05 - Corrections]] · [[Conventions]] §Turunan ·
[[07-Testing/T7 - Pre-Push Gate]] · [[09-Inbox/Session-2026-09-27-siang]]

## F-D23 — Pengetahuan trading jadi lapisan terpisah dengan satu pintu angka · 28 Sep 2026

Builder: *"kita harus memperluas knowledge terkait trading agar permainan Fabius lebih terstruktur
dan rapi, dari fetching data, filtering, analisis, sampai decision making"* — dengan
`vault/TradingKnowledge/Plan.txt` (transkrip percakapan dengan model: daftar metode, klaim "paling
OP", resep kombinasi) sebagai bahan awal, dan `C:\...\ObsidianGuides` sebagai panduan bentuk.

**Diputuskan:** lapisan itu dibangun di `vault/TradingKnowledge/` (MOC → hub → part-note, pola
granular yang sama dengan vault ini), tapi dengan tiga penyimpangan yang sengaja, karena bahan
awalnya bukan fakta:

1. **Satu pintu angka.** [[TradingKnowledge/Fakta Terukur]] adalah satu-satunya halaman di subtree
   itu yang boleh memuat angka tentang produk. Angka lain yang menyebut Fabius wajib ditulis
   *(belum diukur)*. Alasannya konkret: tanpa aturan ini, "transkrip model → halaman vault rapi"
   adalah jalur pencucian klaim — superlatif masuk, "pengetahuan" keluar.
2. **Setiap catatan wajib punya tabel status data + tingkat bukti.** Ditegakkan alat, bukan
   selera: `python -X utf8 vault/scripts/tk_check.py` (exit non-zero kalau bagian wajib hilang,
   status enum kosong, atau ada path absolut Windows). Ini lanjutan langsung dari pelajaran
   `hub_shape.py`: `check_links.py` bisa hijau sementara dokumen rusak, jadi gerbang bentuk memang
   perlu ada ([[Conventions]] §Turunan).
3. **Tidak ada peringkat.** `Plan.txt` minta "ambil 20 yang paling OP". Yang dibangun malah matriks
   `metode × tahap × status data × bayar` ([[TradingKnowledge/07-Peta-Fabius/GAP1 - Matriks Metode x Tahap]])
   karena peringkat metode tidak bisa dibuktikan, sedangkan "metode ini tidak bisa dijalankan dari
   repo ini" bisa.

**Yang ikut diputuskan (konsekuensi, bukan tambahan):** pengetahuan baru tidak boleh jadi
pekerjaan baru sebelum yang lama selesai. Dari sinilah urutan backlog **P10–P15** lahir
([[08-Backlog/01 - Backlog]]): satukan model ongkos dulu (59 bps terukur vs 20 bps warisan),
perbaiki mekanika `maker_ledger` sebelum satu angka whale pun dikutip, uji tujuh ambang veto
terhadap hasil, baru bicara metode sinyal baru. Empat yang pertama tidak butuh data baru dan tidak
butuh waktu pasar — dan itu satu-satunya bagian yang masih masuk akal sebelum tenggat 30 Sep.

**Risiko yang diterima:** lapisan ini gemuk dan bisa basi (93 halaman vault → ±90 catatan baru).
Penahannya: halaman ini menunjuk perintah, bukan sebaliknya; dan `GAP1`/`Fakta Terukur` wajib
dibaca ulang dengan `python -X utf8 tools/whale_report.py` + `tools/anchor.py --verify` sebelum
dipakai memutuskan apa pun.

**Terkait:** [[TradingKnowledge/00 - Hub Trading Knowledge]] · [[TradingKnowledge/Aturan Subtree]] ·
[[TradingKnowledge/07-Peta-Fabius/GAP5 - Urutan Kerja dan Bayarnya]] · [[01-Agent/A4 - Trust Gating and Real-Money Rules]]

## F-D24 — Satu model ongkos, default yang TERUKUR, bukan yang lebih ramah · 28 Sep 2026

**Masalahnya.** Dua angka round-trip hidup berdampingan tanpa ada artefak yang bilang mana yang
dipakai: lima jalur uji menutup dengan **20 bps** (model biaya proyek rujukan: 5,5 bps fee + 4,5 bps
spread/slip per sisi — **diasumsikan**, tidak pernah direplikasi di repo ini), sementara venue kami
sendiri menghasilkan **59 bps** (`forge test test_round_trip_...` + event `Closed` di chain 97 —
**diukur**). Efeknya bukan kosmetik: `+1,5 bps` di seri paper adalah artefak penggaris, bukan
keuntungan.

**Diputuskan.** Satu sumber: `tools/costs.py`. Default = **59 bps yang terukur**, dipakai
`backtest.py`, `ledger.py`, `screen_universe.py`, `smartmoney_score.py`, `flow_test.py`,
`maker_ledger.py`. Override `--cost` tetap ada tapi **mengganti basis** dan tercatat di artefak
sebagai `cost_basis: cli-override`, jadi angka dari override tidak bisa menyamar sebagai hasil ukur.
Gerbang self-test mengikat 59 ke struktur fee pool (dua sisi 30 bps berkomposisi = 59,9): kalau
suatu hari angka itu tidak lagi berasal dari mana pun, yang berteriak alat, bukan pembaca.

**Kenapa yang terukur, bukan yang lebih "adil" untuk perp.** 59 bps adalah apa yang benar-benar kami
bayar di tempat kami benar-benar mengisi order. Memakainya pada bar perp membuat uji **lebih keras**,
bukan setara — fee taker perp sungguhan biasanya di bawah itu. Konsekuensinya diterima: hasil
sebelumnya jadi lebih buruk, dan itu harga dari kejujuran, bukan temuan baru.

**Yang berubah di klaim.** Aturan arah tetap **12/12 rugi**, kini −39,8…−66,9 bps/trade (gross tidak
berubah); ambang gross naik 40 → **118 bps**; **satu-satunya "MENANG +1,5 bps" di seri paper menjadi
−37,5 bps** dan PAPER kini n=3 WR 0 %. Rinciannya [[06-Results/04 - Negative Results]] §5b, koreksinya
[[00-Overview/05 - Corrections]], dan jejak angka lama dibiarkan terbaca di `06-Results/07`.

**Yang TIDAK selesai.** (a) 59 bps terukur pada **satu ukuran** (1 unit) di venue demo — ongkos
per-ukuran belum diukur; (b) `decisions/whale-sweep-90d.json` tetap `cost_bps_applied = 0.0` → semua
horisonnya GROSS dan tetap diblok [[TradingKnowledge/Fakta Terukur]] §H sampai diuji ulang; (c)
`tools/smartmoney_score.py` dan `tools/screen_universe.py` sudah ikut 59 bps, tapi artefak lama
mereka (`+680,7/+336,4`, corong kohort) adalah hasil run 20 bps — tidak boleh dibandingkan
lintas-basis tanpa menyebut itu.

**Terkait:** [[Concepts/Cost Is Fixed]] · [[07-Testing/01 - Test Commands]] baris 11–12 ·
[[TradingKnowledge/02-Fondasi/FD4 - Ongkos Perdagangan]] · [[TradingKnowledge/Fakta Terukur]] §D

## F-D25 — Matriks egress punya tanggal kedaluwarsa; P13 jadi penyedotan, bukan perekaman · 28 Sep 2026

Builder bertanya: *"kamu sudah fetching data dari sources ini semua belum? (kecuali YouTube)"* —
sambil menunjuk `vault/TradingKnowledge/Resources.txt`. Jawabannya dua bagian, dan bagian keduanya
mengubah rencana.

**Satu:** tidak ada yang dibaca dari daftar itu. Itu daftar **tempat belajar** (kanal YouTube, blog,
kursus, forum), bukan sumber data, dan lapisan ini sengaja tidak dibangun dari sana: 99 catatan
memakai dua transkrip sebagai daftar topik + rekaman kami sendiri sebagai fakta + pengetahuan pasar
standar yang **dibukukan sebagai `T1`** atau "pengetahuan standar — tidak ada rujukannya di repo
ini". Membaca Investopedia tidak menaikkan tangga apa pun; hanya run yang menaikkan (F-D23).
Ditulis di [[TradingKnowledge/Sumber dan Jangkauan]].

**Dua:** bagian daftar yang berupa **penyedia data** saya probe (28 Sep 02:03–02:06Z, tanpa kunci,
setiap panggilan diulang sampai 3x). Hasilnya membatalkan klaim vault sendiri: `api.binance.com`
`200` (dicatat `451 restricted location` pada 24 Sep), Bybit dan OKX `200` dengan body nyata,
`data.binance.vision` `200`. Yang tetap tidak bisa: Hyblock (timeout), Glassnode/CryptoQuant (`401`
= butuh akun, jadi `TIDAK-ADA` bukan `MATI-DARI-MESIN-INI`), Coinglass (`404` di path yang **saya**
tebak — itu bukan bukti kematian layanannya, dan tidak boleh ditulis begitu). Yang paling penting:
**histori funding/OI bisa disedot tanpa kunci** — Bybit `funding/history` **66,3 hari** per 8 jam,
OKX 33,0 hari, Binance `openInterestHist` **20,8 hari** per 1 jam ([[TradingKnowledge/Fakta Terukur]] §A.5).

**Diputuskan.** (1) **P13 diubah bentuk**: dari "rekam per jam dan tunggu 30 hari kalender" menjadi
"sedot mundur ±66 hari sekarang, baru rekam untuk ketebalan" — uji carry horison harian sekarang
mungkin dikerjakan dalam sisa tenggat. (2) **Setiap baris `MATI-DARI-MESIN-INI` wajib menyebut
tanggal baca**, dan `sumber × jaringan` diperluas menjadi `sumber × jaringan × waktu`: 18 catatan
yang mengutip "histori funding tidak ada" dikoreksi lewat
`vault/scripts/patch_funding_history.py`, dan probe-nya ditinggalkan di workspace
(`_research/probe_tk_sources.py`, `_research/probe_cex_depth.py`) supaya bisa diketuk ulang.
(3) **Batas yang tetap berlaku:** funding 8 jam bukan fitur per-bar 1 j/4 j; order book/tick/
likuidasi tetap tidak ada; dan angka ini baru divalidasi dari **satu** jaringan — runner belum.

**Terkait:** [[TradingKnowledge/Sumber dan Jangkauan]] · [[TradingKnowledge/Fakta Terukur]] §A.5/§C ·
[[08-Backlog/01 - Backlog]] P13 · [[06-Results/03 - Not Yet Proven]] baris 15 ·
[[03-Data/01 - Dataset]]

## F-D26 — Veto funding tetap ada tapi berganti nama: pemutus rezim, bukan gerbang keamanan · 28 Sep 2026

P16 menawarkan tiga jalan untuk `FUNDING_EXTREME = 0,05 %/4 jam` di `tools/direction.py`: turunkan
ambangnya, biarkan apa adanya, atau pindah aset uji. Yang memutuskan bukan selera, tapi angka yang
baru ada:

- **0 dari 2.963** settlement (6 basis × 66–97 hari, Bybit + OKX) melewatinya. Maksimum yang terlihat
  **0,0256 %/8 jam** ≈ 0,0128 %/4 jam — ambangnya ±4× di atas apa pun yang pernah terjadi di jendela itu.
- **0 dari 12 uji** arah 24 jam dari funding ekstrem lolos BH (median + bootstrap + binomial;
  [[06-Results/08 - Carry Study]] §B). Jadi **menurunkan ambang supaya gerbangnya "pernah menyala"
  berarti memilih angka dari noise** - persis yang dilarang [[TradingKnowledge/QT4 - Overfitting dan Validasi]]
  dan [[TradingKnowledge/EV2 - Jebakan Backtest]].
- Dan yang paling menentukan: kandidat kita yang sebenarnya (memecoin BSC) **tidak punya funding
  sama sekali**. Gerbang ini tidak akan pernah menimbang satu pun aset yang benar-benar kita
  perdagangkan - jadi menyebutnya "keamanan" selalu salah, bukan cuma sekarang ketahuan salah.

**Diputuskan: tetap ada, ambangnya tidak diubah, namanya diganti.** Yang benar dipertahankan adalah
peran yang tidak butuh prediktabilitas: **pemutus rezim**. Kalau funding pernah melewati empat kali
maksimum yang pernah kami lihat, kita tidak lagi berada di dunia tempat semua ambang lain dipilih,
dan menolak posisi baru saat itu adalah keputusan yang benar tanpa perlu jadi sinyal - sama pola
pikirnya dengan `killSwitch` ([[02-Contracts/C3 - ExecutionVault]]). Tidak ada satu pun angka yang
diubah; yang berubah adalah klaim yang menempel padanya.

**Yang ikut dikoreksi karena ini.** Delapan tempat di `TradingKnowledge/` menyebut gerbang ini sebagai
penolak posisi "karena biaya" (`Fakta Terukur` §A, `FD4`, `PL3`, `PL4`, `ST2`, `QT6`, `U2`×2);
semuanya kini berbunyi *pemutus rezim* + angka 0/2.963. Sekali-jalan:
`vault/scripts/relabel_funding_gate.py`.

**Yang tetap terbuka, dan tidak boleh dilupakan.** Satu gerbang lagi bernasib sama: `MIN_VOL_OVER_LIQ`
0,10 dan empat ambang universe lain masih **diputuskan, bukan diuji** terhadap hasil - itu P12, dan
corongnya (`tools/screen_universe.py`) sudah membandingkan kohort dengan arah yang **melawan**
nilai veto kita. Kalau seorang reviewer cuma diberi satu kalimat dari halaman ini: veto yang tidak
pernah menyala bukan perlindungan; ia asuransi yang tagihannya nol dan manfaatnya belum pernah
terpakai - dan kita harus bilang begitu, bukan menghapusnya diam-diam saat ada yang bertanya.

**Terkait:** [[06-Results/08 - Carry Study]] · [[03-Data/D6 - Funding and OI History]] ·
[[TradingKnowledge/Fakta Terukur]] §A/§F · [[08-Backlog/01 - Backlog]] P12/P16 ·
[[Concepts/One-Way Gate]] · [[TradingKnowledge/U2 - Funding Rate dan Basis]]

## F-D27 — Satu bentuk harga, pantau 2 jam, dan compounding yang harus membuktikan dirinya · 28 Sep 2026

**Apa yang memicunya.** `tools/evidence_stack.py` memberi **+649,8 bps** untuk kejadian yang sama
persis dengan **+363,6 bps** di `tools/flow_cluster_test.py`. Dua alat yang jujur tidak boleh
diselesaikan dengan memilih angka yang enak, jadi kukari bedanya: **5.355 baris `px` berbagi
stempel waktu untuk token yang sama** (±19 % dari deret harga kami), karena `smartmoney` dan `kol`
melihat pool yang sama dalam satu siklus. Selama duplikat dibiarkan, "harga masuk" ditentukan
**cara mengurutkan**, bukan oleh data - `.sort()` pada tuple memakai harga sebagai pemecah seri,
`.sort(key=t)` tidak.

**Diputuskan.**

1. **Satu harga per (token, stempel) = median pada stempel itu.** Bentuk kanoniknya ada di satu
   tempat (`flow_cluster_test.dedupe_px()`) dan **dipakai oleh kedua alat**, bukan disalin. Setelah
   itu keduanya sepakat: **K≥2 = +393,4 bps, CI [+5; +1012], p=0,0008** (BH α 0,10). Run kanonik
   `decisions/flow-cluster-20260928T073714Z.json`.
2. **Jendela pantau harga jadi 2 jam, bukan 24 jam** - dan itu angka pengukuran, bukan
   kenyamanan. Builder bertanya "24 jam lama sekali, itu harga live kan?". Ya: `px` sudah menetes
   gratis tiap ±202 s. Yang bikin 24 jam mahal adalah ukuran pantau, terukur di berkas kami sendiri:
   **927 token = 31 batch = ±552 panggilan/jam** untuk 24 jam, vs **136 token = 5 batch = 89
   panggilan/jam** untuk 2 jam lewat `tokens/v1/bsc/<30 alamat>` (terukur 200 @401 ms). Default
   `universe/record_watch_prices.py` = `--watch-min 120`, disambungkan ke rantai `wallet-flow.yml`
   sebagai langkah **non-fatal** (kalau DexScreener mati, perekam utama harus tetap jalan).
3. **Compounding harus membuktikan dirinya sendiri.** Lima aspek lulus uji berpasangan sendirian
   (kerumunan ≥2/≥3, maker berulang, **sebaran dana**, USD ≥1k); dua tidak ("tidak ada jual" −0,3
   dan "aliran lebar" +0,5 bps). Tumpukan ≥2 aspek lulus = **+481,0 CI [+23; +977] p=0,0002**, dan
   yang terkuat bukan "lebih banyak whale" tapi **struktur dana**: `cluster_ge2` **DAN**
   `money_spread` = **+748,8 CI [+12; +1574] p=0,0010**. Rinciannya
   [[06-Results/10 - Evidence Stack]].
4. **`fresh_token` DIBUANG dari bukti, walaupun lolos BH.** +7.708 bps (80,8 % positif) tidak punya
   mekanisme pasar: "token ini baru muncul di rekaman kami" = "kami baru mulai menarik harganya".
   Dia mengukur **kebijakan pull kami**, dan menyuntik ±7.000 bps ke kombinasi apa pun yang dia
   sentuh. Tumpukan diuji ulang tanpanya dan sisanya berdiri sendiri - itu syaratnya, bukan hiasan.

**Yang tidak berubah, dan itu bagian dari keputusan.** Tidak ada satu pun gerbang Fabius yang
digeser hari ini. Angka di halaman 09/10 berumur satu jendela 43 jam, dan hanya **12,7 %** kejadian
(807 dari ±6.373 kandidat) yang bisa dinilai sama sekali - 5.085 kehilangan harga ≤10 menit
**sebelum** beli, 481 kehilangan harga keluar. **P20** mengunci spesifikasi
(horison 30 m, jendela 15 m, K≥2, `money_spread`, entry `px` kanonik, ongkos 59 bps measured, BH
α 0,10) **sebelum** data hari kedua dilihat; kalau hari kedua tidak memisahkan, halaman 09 dan 10
**dicabut**, bukan diperluas dengan penjelasan.

**Terkait:** [[06-Results/09 - Whale Cluster Test]] · [[06-Results/10 - Evidence Stack]] ·
[[03-Data/D2 - Wallet Flow]] · [[08-Backlog/01 - Backlog]] P17/P19/P20 ·
[[TradingKnowledge/EV4 - Point-in-Time dan Riwayat yang Tidak Bisa Disusulkan]] ·
[[TradingKnowledge/EV5 - Reproduksibilitas dan Pra-Registrasi]]


## F-D28 — Tanda kehidupan yang benar untuk bidang ⑦ adalah umur berkasnya, bukan daftar run · 28 Sep 2026

Bidang ⑦ berhenti menetes: commit aliran terakhir di origin `2026-09-28T06:13:38Z`
(`generated_utc` manifest), rantai #14 `failure` di 06:17:03Z, dan tidak ada run sesudahnya.
Jam rujukan = header server GitHub (08:24:37Z), jadi lubangnya ±2 jam 10 menit - dan untuk bidang
yang **tidak bisa disusulkan**, itu 2 jam 10 menit yang hilang permanen.

Dua cacat mekanis, keduanya punyaku, keduanya lolos pengamatan berhari-hari karena **yang kubaca
adalah tanda yang salah**:

1. **Dispatch-diri tidak pernah berhasil sekali pun.** Langkah "Sambung rantai" memanggil
   `.../actions/workflows/<id>/dispatch`; endpoint REST yang benar `.../dispatches` dengan body
   `{"ref": …, "inputs": {…}}` (diperiksa ke dokumentasi, bukan ditebak). Hasilnya 404 → langkah
   gagal → rantai berhenti. "Rantai yang menghidupi dirinya sendiri" ternyata cuma jalan selama
   cron sedang murah hati, dan tidak ada yang sadar karena **kehadiran run** disalahartikan sebagai
   **kemajuan data**.
2. **Penyelamat membunuh pasien.** `schedule: 17 * * * *` tinggal di berkas yang sama dengan
   rantainya, dan `cancel-in-progress: true` membuat tiap tembakan per-jam MEMBATALKAN rantai yang
   sedang merekam. Terukur: run #11 (15:38Z), #12 (19:45Z), #13 (23:01Z) semuanya
   `conclusion=cancelled`, berjarak persis mengikuti jadwal cron. Daftar run terlihat "hidup tiap
   jam"; yang terlihat sebenarnya adalah rantai yang dihidupkan-lagi tiap kali dibunuh.

**Diputuskan.** `schedule` dihapus dari workflow perekam; `cancel-in-progress: false` (yang macet
dipotong `timeout-minutes: 330`, yang tidak menyentuh rantai lain); penyelamat pindah ke berkas
terpisah `.github/workflows/wallet-flow-watchdog.yml` dengan grup concurrency sendiri, cron per-30
menit, dan satu pertanyaan: **berapa umur `universe/wallet-flow-manifest.txt`?** > 25 menit dan
tidak ada rantai `in_progress` → dispatch; kalau dispatch gagal, ia menendang `::error::` supaya
merah. Untuk bidang tanpa riwayat, umur berkas adalah satu-satunya tanda yang tidak bisa berbohong.

**Metodenya juga dikoreksi.** Bacaan awal ku ("mati 5 jam") berasal dari `git log -- <berkas>` di
salinan lokal yang ternyata 50 commit tertinggal. Sudah pernah membayar di proyek ini (27 Sep,
[[Concepts/Stale Local Copy]]), dan tetap terjadi lagi. Aturan yang sekarang kutulis: **setiap
"hidup/mati" dinyatakan setelah `git fetch` + sumber pihak ketiga**, bukan dari working copy.

**Terbukti 28 Sep 08:53-09:00Z, dari log GitHub sendiri** (setelah commit ini didorong - bukan
dari YAML yang sah):

- `wallet-flow-watchdog` run **#1** `event=workflow_dispatch` `conclusion=success`:
  `STATUS=segar umur=3.3m manifest=2026-09-28T08:50:24Z rantai_jalan=1 force=0` →
  *"aliran berumur 3.3 menit (<= 25) -> TIDAK ada yang perlu diselamatkan."* Pembacaan umur
  manifest bekerja, dan dia TIDAK men-dispatch sesuatu yang tidak perlu.
- run **#2** dengan `force=1`: `WATCHDOG: rantai di-dispatch (wid=367575867, ref=master,
  umur=2.6m)` lalu `verifikasi: run #16 pending event=workflow_dispatch`. **Ini pertama kalinya
  rantai ⑦ lahir dari API dispatch** - bentuk body yang benar diterima, dan run #15 yang sedang
  merekam TIDAK dibatalkan (#16 `pending` = mengantri di grup concurrency, perilaku yang
  kusesatkan; `cancel-in-progress: false` bekerja seperti tulisannya).
- Aliran hidup lagi terukur dari origin: commit `wallet flow` 08:43:36 / 08:47:00 / 08:50:24Z,
  `usia_aliran_jam` 0,00, rentang 48,81 jam.

**Yang masih belum terbukti.** Rantai #15 sendiri tetap memakai definisi workflow LAMA (dia dimulai
08:39:58Z, sebelum push 08:50:54Z), jadi langkah "sambung rantai"-nya masih akan 404 saat loop itu
selesai (~13:1xZ). Uji alami berikutnya: apakah watchdog cron (per-30 menit) menangkap lubang itu
dan menyalakan rantai baru tanpa tangan manusia. Kalau itu berhasil, klaim "pipeline ini hidup tanpa
dijaga" akhirnya punya bukti; sampai saat itu, yang terbukti cuma jalur dispatch-nya.

**Terkait:** [[03-Data/D2 - Wallet Flow]] · [[TradingKnowledge/Fakta Terukur]] §G ·
[[08-Backlog/01 - Backlog]] P22 · [[Concepts/Stale Local Copy]] · [[00-Overview/04 - Run It]]

## F-D29 — Halaman 11 memegang hak veto atas halaman 09 dan 10 · 28 Sep 2026

Angka terbaik kita (+393,4 bps K≥2; +748,8 bps kerumunan×sebaran dana) lahir dari **satu jendela
43 jam**. Satu jendela tidak bisa membuktikan dua kali, dan menambah halaman penjelasan ke angka
yang tidak mereplikasi itu bukan analisis - itu pengejaran.

**Diputuskan:** parameter replikasi **dikunci sebelum satu pun angka replikasi dilihat**, dan
kuncinya adalah alat, bukan niat.

```text
kunci              decisions/prereg-day2-lock.json  (dibuat 2026-09-28T08:30:38Z)
spec_sha256        0x03aa212fccdf5b9f82b94c43110940e840e7dc27c7f8b9afde4ae459fcba602c
t_kunci            2026-09-28T06:13:38Z (stempel aliran terakhir saat mengunci)
syarat             rekaman baru >= 12 jam SETELAH t_kunci; HANYA kejadian t > t_kunci yang dinilai
vonis              median > 0 DAN batas bawah CI 95 % > 0 DAN p satu arah < 0,05 sesudah BH di
                   dalam run itu - tiga-tiganya, untuk uji_primer cluster_ge2
kalau gagal        09 dan 10 DICABUT dari klaim, bukan "diperluas dengan penjelasan"
```

**Yang diuji, bukan dipercaya.** Sunting satu digit di blok spesifikasi setelah dikunci →
`tools/day2_replicate.py` keluar dengan `exit=1` dan pesan *"yang berubah bukan datanya, aturan
mainnya"*. Dalam keadaan normal ia mencetak **"BELUM SAH - kurang 12.0 jam"** dan **nol angka
hasil**. Ketiadaan hasil bukan hasil: tidak ada klaim yang bergerak ke dua arah.

**Satu penjaga yang kupasang karena kesalahan sesi ini sendiri.** Umur aliran dibaca dari
`universe/wallet-flow.jsonl` **lokal** - dan salinan lokal persis yang menipu dua kali di proyek ini
(27 Sep: 78 commit tertinggal; 28 Sep: 50 commit tertinggal, dan dari angka itulah kesimpulan
"perekam mati 5 jam" yang salah lahir). Sekarang `last_flow_stamp()` membandingkan stempel lokal
dengan commit data terbaru di `origin/*` dan mencetak `PERINGATAN: salinan lokal BASI - ... 17 MENIT
lebih baru ...` sebelum satu baris hasil pun keluar. Vonis tetap dihitung dari berkas lokal (itu
satu-satunya berkas yang bisa dibaca utuh), tapi pembacanya diberi tahu bahwa tanahnya gompal.
Terbukti menangkap kasusnya sendiri pada run pertama: peringatan keluar, lalu hilang setelah
`git pull`.

**Konsekuensi yang harus diterima nanti.** Karena `t_kunci` = 06:13:38Z - yaitu saat rantai ⑦ mati
(F-D28) - jendela replikasi baru benar-benar berguna kalau perekaman hidup lagi. Kunci ini sengaja
TIDAK kupasang ulang setelahnya: memindahkan `t_kunci` supaya "cepat sah" berarti memilih titik
mulai sesudah melihat konsekuensinya, dan itu persis yang dikunci untuk dicegah.

**Terkait:** [[06-Results/11 - Pra-Registrasi Hari Kedua]] · [[06-Results/09 - Whale Cluster Test]] ·
[[06-Results/10 - Evidence Stack]] · [[TradingKnowledge/EV5 - Reproduksibilitas dan Pra-Registrasi]]


## F-D30 — Efek kerumunan yang kami terbitkan adalah artefak harga masuk; halaman 09/10 dicabut · 28 Sep 2026

**Apa yang memicunya.** Setelah `px` terbukti tangga beku (71,7 % barisnya mengulang nilai; umur
median harga 8,7 menit), satu pertanyaan menyusul: berapa banyak dari "+393,4 bps K≥2" yang berasal
 dari **kerumunan**, dan berapa banyak dari **fakta bahwa kerumunan punya lebih banyak transaksi
 sehingga deret harga kami lebih segar**? Jawabannya diukur dengan mengganti SATU hal - sumber harga
 masuk - pada kejadian dan pairing yang sama persis (`tools/entry_decomposition.py`, 557 kejadian,
 58 token berpasangan, `rows_sha256=0x2c96b4f17374c8…`):

| harga masuk → keluar | median selisih K≥2 | CI 95 % | % positif | p |
|---|---|---|---|---|
| `px → px` **(yang kami terbitkan)** | **+93,0** | [+1; +825] | 59,6 % | 0,0066 |
| `tx → px` (masuk = harga transaksi itu sendiri) | **+0,1** | [−14; +198] | 50,0 % | 0,53 |
| `tx → tx` (kedua ujung harga peristiwa) | **+0,3** | [−7; +516] | 51,7 % | 0,35 |
| `px → tx` | +815,4 | [+5; +1760] | 62,4 % | 0,0006 |

Pada harga peristiwa **tidak ada satu aspek pun yang lolos BH**. Dan pada populasi yang lebih besar
(`evidence_stack --px txevent`, 908 kejadian) arahnya justru negatif: `cluster_ge2` = **−491,4 CI
[−1319; −205]**, 30,5 % positif. Dua himpunan, dua jawaban - nol dan negatif - dan keduanya menolak
klaim kami.

**Kenapa gerbang yang kupunya tidak menangkap ini.** Semua gerbangku memeriksa **bentuk** (tautan,
lebar baris, angka yatim, hash baris) dan **keselaman waktu** (point-in-time, anti-lookahead). Yang
bocor adalah **asal angka**: harga masuk yang valid secara waktu tapi tidak valid secara
perdagangan - kamu tidak bisa membeli di harga yang sudah lewat. Itu tidak bisa dites oleh gerbang
bentuk mana pun. Pelajaran yang kubayar dengan efek terbaikku sendiri: **satu-satunya gerbang yang
menangkap kelas kesalahan ini adalah mengganti satu hal pada satu waktu dan melihat apakah efeknya
hidup.**

**Diputuskan.**

1. [[06-Results/09 - Whale Cluster Test]] dan [[06-Results/10 - Evidence Stack]] diberi penanda
   **DICABUT** di kepalanya; isinya tidak dihapus - urutan bagaimana kami sampai ke sana adalah
   bagian dari hasilnya, dan itulah yang membuat halaman 12 bisa diperiksa orang.
2. Gerbang ⑧ **tidak** dipasang dan **tidak** akan dibangun di atas kerumunan sebagai sinyal beli.
3. Hipotesis "kerumunan = jangan masuk" (fade) TIDAK dijual: itu hipotesis baru dari satu jendela
   49 jam, dan ia berhak atas kunci sendiri sebelum ada yang menyebutnya temuan.
4. Spesifikasi lama di halaman 11 **tidak kusunting** - alat penolaknya akan mati, dan memang untuk
   itu ia dibuat. Statusnya jadi **moot untuk keputusan produk** (yang diuji sudah diketahui cacat
   instrumennya). Klaim yang hidup dikunci terpisah: halaman 12, `decisions/prereg-honest-lock.json`.
5. **P25** dibuka: semua uji lain yang memakai `px` di salah satu ujungnya (`carry_study`,
   `screen_universe`/funnel, `maker_ledger`, `out/*`) harus diperlakukan sama curiganya dan diulang
   pada harga peristiwa.
6. Perekam ikut diperbaiki agar kelas kesalahan ini tidak terulang: `px` kini membawa `ttx`
   (skema 2) - "kapan harga terjadi" terpisah dari "kapan kami melihatnya".

**Terkait:** [[06-Results/12 - Harga Masuk yang Benar]] · [[06-Results/11 - Pra-Registrasi Hari Kedua]] · [[TradingKnowledge/Fakta Terukur]] §B/§F · [[08-Backlog/01 - Backlog]] P18/P24/P25 ·
[[TradingKnowledge/EV2 - Jebakan Backtest]] · [[Concepts/Unmeasured Is Not Clean]]


## F-D31 — Yang kami punya hari ini adalah rem, bukan gas; dan itu ditulis sebagai hasil, bukan sebagai malu · 28 Sep 2026

Builder menantang dengan pertanyaan yang benar: *"kalau dia cuma tahu kapan jangan masuk, apa
bedanya dengan tidak trading?"* Kubawa pertanyaan itu ke data dengan **ukuran yang cocok ke bentuk
datanya** (median selama ini menyesatkan: payoff 30 menit di universe ini miring kanan ekstrem),
dan dua hal keluar.

1. **"Tidak trading" tidak gratis.** Harapan yang di-winsor (±2.000 bps) dari posisi 30 menit di
   universe yang disajikan feed ini = **+82,7 bps**, dengan **P(net ≥ +500 bps) = 33,9 %** dan
   p90 = +8.854 bps, walau median −58,9 (persis ongkos). Jadi menolak membuka posisi memang
   meninggalkan sesuatu di meja - tapi itu milik **universe feed**, bukan hasil seleksi kami, dan
   menyebutnya edge kami = bohong.
2. **Kami belum punya penyaring yang menaikkan angka itu.** Tidak ada satu pun aspek aliran yang
   lolos BH ke arah naik. Yang lolos BH justru **turun**: kerumunan jual dalam 15 menit
   memangkas P(≥+500) dari 33,9 % → **20,3–22,5 %** (Fisher p=0,003–0,02). Dan kerumunan beli
   adalah waktu **keluar** (berpasangan −313 CI [−1041; −11]), bukan waktu masuk. Hipotesis cermin
   yang kubangun sendiri pagi ini - "kalau beli ramai meramalkan turun, jual ramai pasti meramalkan
   naik" - **gugur**: `jual_2` = −690 bps vs baseline.

**Diputuskan.**

- Gerbang ⑧ dibangun di atas apa yang benar-benar terbukti: **kerumunan jual = VETO/JANGAN masuk;
  kerumunan beli = sinyal keluar untuk posisi yang sudah dipegang.** Bukan `SEARAH` (masuk bersama
  whale). Dua-duanya tetap satu arah: ia hanya boleh **mengurangkan** posisi, tidak pernah
  menambah keyakinan ([[Concepts/One-Way Gate]]).
- **Tidak ada klaim "kami tahu kapan masuk" di materi apa pun.** Halaman 13 menyimpan pertanyaannya
  apa adanya. Yang belum diukur (siklus hidup pool: umur, likuiditas, volum 1 jam, rasio
  beli/jual per jam) jadi **P26**, dan itu satu-satunya jalur yang masuk akal ke "gas" - bukan
  aspek maker yang sudah kami keringkan hari ini.
- Metode yang ikut berubah: **laporan berikutnya wajib menyebut ukuran tengah DAN ukuran ekor**
  (median, P≥500 bps, mean winsorized). Median saja membuat strategi lottery-like terbaca mati, dan
  mean saja membuatnya terbaca hidup.

**Terkait:** [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] · [[06-Results/12 - Harga Masuk yang Benar]] · [[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]] ·
[[TradingKnowledge/FD6 - Ukuran Posisi]] · [[08-Backlog/01 - Backlog]] P25/P26 ·
[[Concepts/One-Way Gate]] · [[Concepts/Unmeasured Is Not Clean]]


## F-D32 — Paper trading adalah SLOT yang ditambal posisi asli, dan streak bukan kredensial · 28 Sep 2026

Builder menyetel bentuk kerjanya: paper dipakai untuk membuktikan analisis SEBELUM uang turun
("mungkin tiap 2 kali prediksi paper benar baru berani pasang posisi asli"), dan slot paper itulah
yang nanti digantikan posisi nyata - jadi ia harus **berlabel**, bukan jadi laporan paralel.

**Diputuskan dan dipasang di alat (`tools/paper_book.py` + `tools/winlog.py`):**

1. Tiap posisi paper ditulis sebagai slot: `mode: "PAPER"`, `slot_id` = sha256(token|waktu|kebijakan),
   dan `pengganti_real: null`. Kolom terakhir hanya boleh terisi oleh tx asli yang menambal slot yang
   **sama** - jadi "paper jadi nyata" bukan pergantian label, melainkan tambalan yang bisa ditelusuri.
2. `winlog` kini punya **tiga seri** dan menolak menggabungkannya: `PAPER` (keputusan ter-anchor vs
   bar Aster), `BUKU PAPER ⑦` (slot boongan pada harga peristiwa), `CHAIN` (fill nyata di pool kami).
   Yang tercetak sekarang: 556 slot dinilai, **0 layak real, 0 ditambal posisi asli**.
3. **Aturan naik dua lapis.** Streak N benar beruntun (default 2) dicatat - itu permintaan builder -
   tapi **bukan vonis**, dan alasannya terukur dari buku ini sendiri: peluang menang per posisi kami
   **42,3 %**, jadi dua menang beruntun terjadi **~18 % dari waktu itu tanpa ada efek apa pun**.
   Vonisnya: gerbang F-D16 (n≥20 DAN harapan > 0 DAN **CI bawah harapan** > 0) **DAN** kebijakan
   harus di atas control `random + gerbang yang sama`.
4. Control tidak pernah bisa mempromosikan dirinya sendiri. (Kegagalan pertama alat ini justru
   menyatakan `random` LAYAK - karena membandingkan mean tak-dibulatkan dengan control yang sudah
   dibulatkan. Diperbaiki, dan control sekarang dicetak sebagai `CONTROL - tidak pernah dipromosikan`.)

**Vonis malam ini, dan ini yang tidak enak:** kontrol acak dengan gerbang yang sama **+188,3 bps**
mengalahkan kedua aturan pilihan kami (`first` +140,9 CI [+35,0; +249,2]; `lock` +109,7 CI [+2,4;
+215,5]). Pada budget/ukuran kontrak (5 posisi/hari, 1 BNB) buku ini **−708,9 bps**. Jadi: yang
terukur +188,3 sebagian besar adalah *"feed ini sedang menunjukkan token yang naik"*, bukan
*"Fabius bisa memilih"*; dan status "paper" tidak mengubah tanda minus jadi plus - ia hanya
memungkinkan kita mengukurnya sekarang, bukan sesudah uang turun.

**Konsekuensi yang diterima.** Selama belum ada kebijakan di atas control, **tidak ada** posisi asli
yang dibuka walau streak tercapai, dan tidak ada satu pun slot boongan yang boleh ditulis sebagai
PnL. Jalur ke "gas" bukan mempertajam aspek maker (sudah dikuras hari ini) tapi **P29: memperbaiki
cakupan snapshot** - sampai penyortiran dijalankan di atas sampel yang bukan "yang sedang panas",
apa pun yang kami temukan adalah angka pada subset terburuk (§3e halaman 13).

**Terkait:** [[06-Results/14 - Buku Paper]] · [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] ·
[[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]] · [[TradingKnowledge/EV5 - Reproduksibilitas dan Pra-Registrasi]] · [[Concepts/One-Way Gate]] · [[08-Backlog/01 - Backlog]] P29/P30 ·
[[Concepts/Unmeasured Is Not Clean]]

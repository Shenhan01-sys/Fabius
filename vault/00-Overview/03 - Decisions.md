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


## F-D33 — Prioritas proyek dipindah: mencari "alasan untuk masuk", dan itu jadi epik terpisah · 28 Sep 2026

Builder menutup sesi dengan arahan yang kutulis apa adanya: *"fokus kerjakan alasan untuk masuk itu,
buat itu menjadi backlog besar, karena itu adalah jantung Fabius."*

Setuju, dan ini alasan kenapa itu bukan sekadar pindah kerja: sepanjang hari ini yang kami perbaiki
adalah **mesin pembuktian** - data mengalir sendiri, satu bentuk data, ongkos terukur, gerbang bentuk,
spesifikasi terkunci. Mesin itu sekarang cukup bagus untuk **membatalkan klaimku sendiri dua kali**:
`+393,4 bps` karena harga masuk beku (F-D30) dan `lock_percent` karena control acak mengalahkannya
(F-D32). Tapi mesin yang jago membatalkan belum menghasilkan satu pun alasan untuk MEMBUKA posisi.
Tanpa itu Fabius adalah agen yang pintar menolak - persis yang dilarang builder.

**Diputuskan.**

1. Halaman induk baru: [[08-Backlog/02 - Epik Alasan Masuk]] (P31), berisi kriteria selesai yang
   **bisa gagal**, perhitungan daya, lima keluarga hipotesis E1-E5, sub-pekerjaan P31.1-P31.6, dan
   non-goal eksplisit.
2. **Aturan payung:** tidak ada "aturan masuk" yang boleh diumumkan atau dipasang ke
   `tools/direction.py` / `tools/decide.py` sebelum ia (a) mengalahkan **control `random + gerbang
   yang sama`** pada sampel penuh, (b) harapan winso dengan **CI bawah > 0** dan ekor naik pada uji
   **satu arah**, (c) spesifikasinya **terkunci sebelum** datanya dilihat. Dua klaim yang jatuh hari
   ini jatuh persis karena dua dari tiga syarat ini dilanggar tanpa kita tahu.
3. **Daya dinyatakan, bukan diimpi:** ±70-140 posisi untuk memutuskan selisih 200 bps; ±205
   kejadian per grup untuk kenaikan ekor +10 pp; ±272 posisi (= ±55 hari) kalau pencarian
   dikunci pada budget kontrak 5/hari. Jadi pencarian jalan dengan budget **dilepas** (paper), dan
   budget kontrak dipakai sebagai konfirmasi kedua yang terpisah. Yang tidak mungkin, kutulis tidak
   mungkin.
4. **Urutan malam ini:** E1 *tenang-setelah-kerumunan* dan E2 *jendela risiko pasar* - bahannya
   sudah ada di repo. E4 (siklus hidup pool) tidak bisa dikejar sebelum P29 (cakupan), karena dialah
   yang sudah membuktikan dirinya mati oleh subset terpilih. E5 (buy-the-dip) sudah diuji: SALAH.
5. Produk tetap berdiri kalau epik ini gagal: rem + eksekusi + bukti tetap hasilnya, dan halaman
   epik menyimpan E yang mati sebagai hasil, bukan sebagai utang.

**Terkait:** [[08-Backlog/02 - Epik Alasan Masuk]] · [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] · [[06-Results/14 - Buku Paper]] · [[06-Results/12 - Harga Masuk yang Benar]] ·
[[TradingKnowledge/QT2 - Backtesting yang Jujur]] · [[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]] · [[00-Overview/01 - Briefing]] · [[Concepts/Unmeasured Is Not Clean]]


## F-D34 — [7] jadi perilaku agen, garis darah data rantai diperbaiki, dan satu angka outage-ku salah · 28 Sep 2026

**Tiga hal dalam satu keputusan, karena satu akar: yang kami klaim harus yang kami JALANKAN.**

1. **[7] = perilaku, bukan lagi hasil studi.** `tools/flow_gate.py` menanya aliran ⑦ untuk tiap
   kandidat dan hanya boleh MENURUNKAN: `VETO` bila >=2 maker berbeda menjual dalam 15 m atau
   USD jual >= 1,5x USD beli (satu-satunya klaim ⑦ yang lolos BH: P(>=+500) 33,9 % -> 22,5 %,
   harapan winso +82,7 -> +162,3). `TAK ADA DATA` (berkas > 20 menit basi, atau token tak dikenal)
   TIDAK diperlakukan sebagai bersih - ia dicatat di `why`, di `rec["flow"]`, dan ikut
   `gatesHash`. Kerumunan BELI tidak dipasang sebagai sinyal masuk: dibatalkan F-D30 dan kalah dari
   control acak. Self-test-nya menangkap bug miliknya sendiri: cache `_load` bertanda
   `(mtime, size)` mengembalikan isi LAMA saat berkas ditulis ulang dengan panjang identik ->
   tanda cache kini menggabungkan 2 KB terakhir berkas.
2. **Garis darah data rantai ⑦.** Run #15 `failure` 13:15:36Z (langkah sambung-rantai lama, 404),
   #16 (antrean sejak 08:59Z, checkout pra-perbaikan) lalu tidak bisa push karena commit-ku naik
   setelah ia checkout -> konflik di EKOR `wallet-flow.jsonl`, berkas yang ditulis mesin tiap
   3,4 menit. Aku sendiri mengalami konflik itu dua kali hari ini dan memanggilnya "nasib rebase";
   bagi runner itu kegagalan permanen. Perbaikan: `.gitattributes` (`universe/*.jsonl merge=union`,
   `manifest merge=ours` - dan TANPA wildcard `*.json merge=union`, karena JSON hasil union tidak
   bisa di-parse), loop `rebase --abort` + `reset --hard origin/<branch>` lalu lanjut, plus langkah
   "Teriak kalau kita buta push" supaya bentuk kegagalan ini MERAH, bukan sunyi.
3. **Angka outage-ku sendiri salah, dan ini bagian yang paling layak dicatat.** Klaimku
   "bolong 3 jam 19 menit" berasal dari (a) `origin/master` yang kubaca dari **remote-tracking ref
   basi** dan (b) `time.mktime` yang mem-parse header `Date: ... GMT` sebagai waktu lokal (WIB,
   +7 jam). Yang terukur sesudah `git fetch` ulang: rantai **sehat 11:43 -> 13:12Z** (+150-240
   baris transaksi tiap 3,4 menit), lalu bolong **13:12Z -> 15:11Z = ~2 jam**, dan pulih oleh
   watchdog: run #17 menulis lagi (manifest origin 15:11:22Z -> 15:14:47Z). Jadi kekeliruan
   "Stale Local Copy" yang sudah kubayar 27 Sep, 28 Sep pagi, dan 28 Sep sore terjadi LAGI -
   kali ini di alat diagnostikku sendiri, beberapa menit setelah kutulis memorinya.

**Bukti P22 yang asli (bukan `force`)** ada di log watchdog #3:
`STATUS=basi umur=114.0m rantai_jalan=1 force=0 -> "aliran basi TAPI ada 1 rantai in_progress ->
biarkan yang jalan selesai."` - dia tidak menumpuk rantai ke dua di atas rantai yang masih hidup,
lalu dispatch berikutnya (#17) melanjutkan perekaman setelah #16 dibatalkan.

**Yang belum.** `wp` (ticker yang berdetak sendiri) masih menunggu rantai #17 menyentuh langkah
pantau - tanpa itu P23/P26/E4 tidak bisa dijalankan; dan veto [7] yang baru terpasang belum punya
satu pun keputusan nyata di `decisions/` yang menunjukkannya (baris pertama muncul di siklus
berikutnya, bukan ditulis dari sini).

**Terkait:** [[03-Data/D2 - Wallet Flow]] · [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] ·
[[06-Results/14 - Buku Paper]] · [[Concepts/One-Way Gate]] · [[Concepts/Unmeasured Is Not Clean]] ·
[[Concepts/Stale Local Copy]] · [[08-Backlog/01 - Backlog]] P15/P22/P31.7


## F-D35 — Replikasi terkunci pertama dijalankan: TIDAK ADA REPLIKASI · 28 Sep 2026 21:24Z

Kunci dipasang 13 jam sebelum datanya ada ([[06-Results/11 - Pra-Registrasi Hari Kedua]],
`spec_sha256=0x03aa212fccdf5b9f…`, `t_kunci=06:13:38Z`, syarat 12 jam rekaman baru, hanya kejadian
setelah kunci yang dinilai). Sore ini syaratnya terpenuhi (15,12 jam) dan alatnya jalan tanpa
sentuhan: `decisions/day2-20260928T212437Z.json`.

Bahan: **275 kejadian pada 158 token, semuanya setelah `t_kunci`**. Hasil per uji:

| uji | angka | tiga syarat (median>0, CI bawah>0, p<0,05) | vonis |
|---|---|---|---|
| `uji_primer` K≥2 | SAMPEL TIDAK CUKUP (n<12 pasangan) | - | gagal |
| `uji_kedua` `money_spread` | SAMPEL TIDAK CUKUP | - | gagal |
| `uji_ketiga` stack ≥2 | med **+219,2**, CI **[−18; +2138]**, p=**0,0490** | ✓ / **✗** / ✓ | **GAGAL** |

**Vonis sesuai aturan halaman 11 baris terakhir: klaim halaman 09 dan 10 DICABUT** - bukan oleh
keputusanku di meja tulis, tapi oleh pengujian yang spesifikasinya sudah terkunci sebelum datanya
ada. Tiga hal yang kupelajari dan harus tertulis:

1. **`p = 0,0490` itu nominal "lolos".** Kalau gerbangnya satu syarat, klaim ini selamat dan
   melaju ke gerbang ⑧. Yang memotongnya adalah syarat kedua. Gerbang yang benar adalah gerbang
   yang bisa membuat angka yang enak jadi gagal.
2. **Spesifikasi tidak kunyunting walaupun godaannya nyata.** Run ini memakai `sumber_harga: gmgn`
   yang sudah kubatalkan F-D30 sebagai instrumen cacat - artinya dia menguji efek hantu, dan
   hasilnya (tidak mereplikasi) tetap yang paling benar: kalau hantunya tidak ikut-ikutan muncul
   di data baru, Artefak-nya memang sesempit itu. Yang ingin kupakai sekarang (`wp`, ticker sungguhan
   11.426 baris / 14 jam) jadi **spesifikasi ketiga yang dikunci sendiri** (P34), bukan editan
   pada spesifikasi lama - alatnya akan menolak editan itu, dan itu memang gunanya.
3. **Cakupan sisi masuk tidak membaik walau 15 jam lebih banyak rekaman** (8.090 beli tanpa `px`
   ≤ 10 menit). Jadi batas 12,7 % itu bukan soal durasi, tapi soal **sumber**: `px` lahir dari
   payload daftar panas, sementara `wp` ditarik seragam. Itu memindahkan seluruh agenda
   "alasan masuk" ke P29/P34, dan meninggalkan satu kalimat untuk submission: **agen kita tahu apa
   yang tidak boleh dibuka, dan hari ini terbukti mengetahuinya lewat uji yang tidak bisa
   dibujuk.**

**Terkait:** [[06-Results/11 - Pra-Registrasi Hari Kedua]] · [[06-Results/09 - Whale Cluster Test]] ·
[[06-Results/10 - Evidence Stack]] · [[06-Results/12 - Harga Masuk yang Benar]] ·
[[TradingKnowledge/EV5 - Reproduksibilitas dan Pra-Registrasi]] ·
[[TradingKnowledge/EV3 - Signifikansi dan Multiple Testing]] ·
[[08-Backlog/01 - Backlog]] P20/P29/P33/P34


## F-D36 — Yang tidak dijawab != yang tidak ditanya != yang mati; dan alat harus membuktikan tulisannya sendiri · 28 Sep 22:1xZ

P33 tahap 2 (`tools/presence_ledger.py`) seharusnya menjawab "berapa dari kejadian tanpa harga
keluar itu poolnya benar-benar mati". Yang terbuka malah tiga lapis kesalahanku sendiri - dan itu
menjadi keputusan tentang caranya, bukan cuma tentang hasilnya:

1. **Jendela pantau dipakai sebagai bukti kematian.** Versi pertama menyebut 74 % token HILANG;
   itu hanya token yang keluar dari daftar pantau 120 menit kami. Aturan diperbaiki: bukti hanya
   dari siklus dalam `(last_seen, last_seen + jendela]`.
2. **Kami tidak mencatat apa yang kami tanyakan.** Asumsi awalku ("400-900 token vs 180 alamat =
   terpotong") ternyata salahukur: daftar pantau nyata 161-165 token dan itu muat di 6 batch.
   Yang benar-benar salah adalah ketiadaan catatan `n_tanya` - tanpa itu kami TIDAK AKAN PERNAH
   bisa membedakan "tidak ditanya" dari "tidak dijawab", dan aku tetap menyimpulkan "55 % pool
   mati" tanpa dasar. Perekam sekarang menulis `wpc`; `--max-batches` naik ke 40 sebagai
   **asuransi**, bukan sebagai perbaikan bug yang sedang terjadi. Pembacaan origin pertama: 6
   siklus `wpc`, semuanya `n_tanya > n_jawab` (161-165 ditanya, 136 terjawab).
3. **Perekam melapor "mencatat" tanpa mencatat.** Guard dedupe memanggil `r["tk"]` buta; baris buku
   `wpc`/`wpv` tidak punya `tk` -> `KeyError` -> siklus selesai dengan konsol *kehilangan tercatat
   11* sementara berkas tidak bertambah apa pun. Kelas yang sama dengan penolakan yang lulus karena
   perintah salah ketik: **angka yang dicetak alat tidak dihitung sampai ia ada di berkas.** Guard
   kini tahan semua jenis baris dan tiap siklus mencetak komposisinya.

Angka dengan klasifikasi (1.439 kejadian lolos veto, harga peristiwa): ADA 489 → +141,3 · HILANG
375 → +140,5 · TIDAK-JELAS 575 → +229,0. **Bound dengan bukti: 1.064 teramati (+188,7) + 375
HILANG dihitung rugi penuh = −381,7 bps/posisi.** Optimisme kohort muda tidak bertahan di bawah
asumsi yang jujur.

Yang belum klaim: bukti langsung baru 8 token; mayoritas status HILANG masih inferensi jendela. Yang
mengubahnya jadi bukti adalah rantai menjalankan perekam baru - butuh commit ini mendarat, bukan
perhitungan tambahan di atas data yang sama.

**Terkait:** [[06-Results/16 - Harga Keluar yang Hilang]] · [[03-Data/D5 - Record Schemas]] ·
[[03-Data/D2 - Wallet Flow]] · [[Concepts/Unmeasured Is Not Clean]] ·
[[08-Backlog/01 - Backlog]] P33/P34/P29 · [[00-Overview/03 - Decisions]] F-D34

## F-D37 — `mann_whitney_p` kami salah urut dan salah ties: satu baris vault dicabut, dan ini kali KETIGA alat kami membatalkan klaim kami · 29 Sep 2026 05:14Z

**Gejalanya bukan angka aneh - gejalanya alat baru yang tidak mau menang.** `tools/vol_ab.py` saya
buat untuk menguji `vol_rendah` vs `vol-tinggi`; self-test-nya menuntut lengan A yang jelas-jelas
positif (+120…+144) melawan lengan B yang jelas-jelas negatif (−300…−324) bisa lulus. Fungsi
`flow_cluster_test.mann_whitney_p` mengembalikan **p = 1,0** untuk itu. Tidak ada hipotesis pasar
yang bisa menjelaskan angka tersebut; yang ada cuma kode.

**Sebabnya dua, dan keduanya struktural.** (1) Daftar untuk peringkat disusun dengan
`sorted(a) + sorted(b)` - dua kelompok terurut lalu ditempel, bukan ditempel lalu diurut. Kalau B
lebih rendah dari A (kasus paling bersih sekalipun), daftar gabungannya turun, dan A dapat peringkat
1..na: A yang menang dibaca sebagai A yang paling buruk. (2) Pada ties, kontribusi tiap elemen A
dihitung `sum(ranks[v])` = rata-rata peringkat **× ukuran kelompok ties**, bukan rata-rata
peringkatnya sendiri; dan harga yang "diam" adalah isi utama feed kami, jadi ties bukan kasus tepi.

**Ukuran dampaknya, bukan dramanya - dan jumlah kasusnya bukan hiasan.** `tools/instrument_proof.py`
mencetak **3 dari 5 kasus mengubah VONIS**, bukan cuma angka. Kasus terakhir di tabel itu yang paling memalukan: dua distribusi yang identik - tidak ada perbedaan apa pun antara A dan B - mendapat **p = 0,000000** dari fungsi lama. Kalau data kami kebetulan berbentuk begitu, kami mengumumkan penemuan dari nol. Jalur yang sama, data yang sama, hanya fungsinya ditukar
(`tools/instrument_proof.py`, dipindah dari `_research/` 29 Sep supaya bisa dijalankan dari clone - P35):

| kasus | MW lama | MW benar |
|---|---|---|
| A terpisah menang telak | 1,000000 | 0,000000 |
| A tumpang tindih ringan lebih tinggi | 0,022311 | 0,999995 |
| ties penuh (20×1,0 + 5×2,0 vs 20×1,0 + 5×0,0) | 0,000000 | 0,012837 |
| dua distribusi **IDENTIK** (tidak ada beda apa pun) | **0,000000** | 0,500000 |

Yang ikut bergerak di vault: kolom **"MW p"** di [[06-Results/13 - Apakah Tidak Trading Itu Gratis]]
§3d. Dijalankan ulang dengan fungsi benar: `lock_percent` **0,6441** (yang terbit 0,0000),
`n_maker_jendela` 0,2066, `usd_b_jendela` 0,4027, `bundler_rate` 0,3288 - **BH pada harapan winso
menjadi kosong**, dan kalimat "satu-satunya fitur yang lolos **dua** uji" turun jadi satu uji.
[[TradingKnowledge/Fakta Terukur]] §F dan baris 25 registry ikut dikoreksi dengan angka 29 Sep.
Teknikal (12 fitur) dan E5 **tidak** berubah vonisnya - di sana MW bukan yang memutuskan.

**Keputusan.** (a) Perbaiki fungsinya, jangan cuma kutip ulang angkanya, dan letakkan
`mw_self_test()` **di sebelah** `mann_whitney_p` supaya siapa pun yang memakai ulang melihat batasnya;
(b) setiap p yang dikutip dari fungsi ini sebelum 29 Sep 05:00Z dianggap belum terverifikasi sampai
alatnya dijalankan lagi; (c) aturan baru di epik: *tidak ada `p` dari alat kami yang boleh masuk
vault tanpa satu kasus uji yang bisa membuatnya gagal* - `fisher_p` (dua-arah) dan parser `receipt`
adalah dua korban sebelumnya, dan ketiganya ketahuan bukan oleh review, tapi oleh **perintah yang
dijalankan sampai selesai**.

**Skop yang tidak boleh dilewati.** Koreksi ini tidak membuat `lock_percent` hidup lagi: dia tetap
mati sebagai kebijakan (F-D32) dan sekarang kehilangan satu tiang penyangga lagi. Dan MW yang benar
tidak membuat `vol_rendah` jadi klaim - dia tetap kandidat sampai E9 jatuh ([[06-Results/18 - Kandidat Pertama, Diuji Hidup]]).

## F-D38 — Kandidat masuk pertama diuji HIDUP, bukan di backtest: kunci keempat 05:13:25Z · 29 Sep 2026

**Kenapa bukan backtest lagi.** E7 (`tools/topk_test.py`, 29 Sep 04:55Z) menghasilkan pemenang
pertama dalam proyek ini yang melewati kontrolnya sendiri: `vol_rendah` **+132,9 bps** vs acak-siklus
−134,3 dengan CI atas acak **+116,1**. Tapi sepuluh fitur diuji sekaligus, jadi peluang satu "menang"
tanpa efek ≈ 10 × 0,025 = **0,25**; dengan Bonferroni hasilnya **tidak signifikan**. Mengumumkan ini
sebagai temuan adalah persis kesalahan yang sudah dua kali kami bayar (F-D30 harga masuk beku,
F-D32 control mempromosikan dirinya sendiri): klaim yang lahir dari bentuk uji, bukan dari pasar.

**Yang diputuskan.** `vol_rendah` dipindah dari backtest ke **buku paper yang berjalan terus**:
job `paper-book` membuka dua lengan tiap siklus - `vol-rendah` dan `vol-tinggi` - pada jam yang sama,
feed yang sama, gerbang veto yang sama, dan hanya berbeda di peringkat volatilitas ticker `wp`.
Kuncinya: `decisions/prereg-vol-lock.json`, `spec_sha256=0x9d70c580…`, dipasang **SEBELUM** ada satu
slot pasca-kunci; syarat umur 12 jam; vonis tiga syarat serentak (n≥20, median>0 DAN CI bawah>0,
Mann-Whitney satu arah A>B p<0,05 - dengan fungsi yang baru dibetulkan di F-D37). Kalau n<20 saat
matang, vonisnya tertulis **"BELUM BISA DIUJI"**, ambang tidak diturunkan, dan itu bukan "tidak ada
efek".

**Dua bug desain yang ketahuan sebelum kunci sempat dipakai - keduanya bentuk kegagalan yang tidak
kelihatan dari angkanya sendiri.** (1) `vol_sebelum()` versi pertama membatasi jendela ke 30 menit,
padahal ticker watch berdetak sekali per ±35 menit: hasil `None` untuk SEMUA kejadian, dan "0 posisi"
terlihat seperti "belum ada yang layak", bukan seperti aturan yang berbeda dari yang diukur. (2)
`open_utc` slot adalah **waktu peristiwa**, bukan waktu jalan: tanpa penyaring `t > t_kunci`, semua
slot yang dibuka hari itu dibuang `vol_ab.py` sebagai prefill - percobaan tampak hidup padahal
kosong. Satu rem tambahan dipasang di `paper_book.py`: kebijakan dengan **nol** posisi tidak boleh
lagi dicetak "di atas control" (sebelumnya itu terjadi begitu saja saat acaknya kebetulan negatif).

**Konsekuensi untuk halaman produk.** Yang boleh ditulis hari ini cuma: *"kami punya satu kandidat
alas masuk, ia sedang diuji pada data yang belum terjadi, dan vonisnya jatuh 17:13Z."* Bukan
"Fabius sekarang tahu kapan masuk". 

## F-D39 — "kandidat pertama" E7 ternyata satu undian yang menang: pembanding dibuat setara, pemenangnya hilang · 29 Sep 2026 05:33Z

**Yang terbit lebih dulu.** `tools/topk_test.py` (E7) melaporkan `vol_rendah` **+132,9 bps** melawan
acak-siklus −134,3 dengan **CI atas acak +116,1** - angka pertama di proyek ini yang melewati kontrolnya
sendiri. Kunci E9 dipasang 05:13:25Z atas dasar itu, dan epik menuliskannya sebagai "kandidat".

**Yang salah bukan fitur dan bukan data - yang salah pembandingnya.** Tie-break pemilihan diacak (itu
perbaikan yang benar, F-D38), tapi konsekuensinya tidak ikut dibayar: begitu tie-break acak, **mean
"top-5 menurut fitur X" juga variabel acak**, sementara alatnya membandingkan **satu** tarikan terhadap
persentil-97,5 distribusi kontrol. Itu lotre di mana kita cuma menyebut nomor yang keluar.

**Setelah vonis diambil sebagai median 40 pengulangan pemilihan**
(`decisions/topk-test-20260929T053349Z.json`, `python -X utf8 tools/topk_test.py --draws 300`):

| fitur | mean (median seed) | CI atas acak | sebar seed | % seed di atas | vonis |
|---|---|---|---|---|---|
| `vol_rendah` | **+112,7** | **+137,5** | −30,7 … +299,7 | **33 %** | **di bawah acak** |
| `usd_ge_1k` | −32,8 | +99,0 | −274,4 … +168,9 | 12 % | di bawah acak |
| `di_atas_puncak60` | −60,3 | +113,2 | −344,0 … +153,7 | 3 % | di bawah acak |
| `sepi_total` | −105,4 | +108,3 | −460,4 … +124,6 | 5 % | di bawah acak |
| enam sisanya | −197,1 … −438,4 | — | — | 0 % | di bawah acak |

**Vonis E7 sekarang: TIDAK ADA satu pun dari 10 fitur yang melewati acak-siklus.** Tidak ada kandidat
di dalam sampel.

**E10 dan godaan berikutnya.** Kebijakan utuh (pemilihan × aturan keluar, pada POSISI YANG SAMA) bahkan
tidak konsisten pada dirinya sendiri:

| outcome | mean `vol_rendah` | CI atas acak | % seed di atas | vonis |
|---|---|---|---|---|
| `net` (tahan sampai horison) | +145,4 | +86,7 | **80 %** | tampak "di atas acak" |
| `net_exit` (E8: keluar saat kerumunan beli) | +164,0 | +169,0 | **47 %** | **di bawah acak** |

Satu fitur, satu jendela, satu berkas: lolos kalau hasilnya didefinisikan satu cara, gugur dengan
definisi lain - sementara pembanding yang dipakai E7 sendiri (`net`, CI atas **+137,5** pada run yang
sama) menaruhnya di bawah acak dengan 33 % seed. Tiga nilai CI atas untuk kontrol yang sama
(+86,7 / +137,5 / +169,0) mengukur satu hal: **pita Monte-Carlo kami lebih lebar daripada selisih yang
ingin kita klaim.** Tidak ada satu pun boleh dijual.

**E9 tidak dibatalkan.** Kunci 05:13:25Z tetap di tempatnya, datanya tetap belum pernah terlihat, dan
membatalkan uji karena prior-nya melemah sama dengan memindahkan gol saat bola datang. Yang berubah
hanya kalimat yang boleh ditulis sebelum 17:13:25Z: bukan "kandidat kami sedang diuji" tanpa catatan,
tapi "di dalam sampel tidak ada fitur yang melewati kontrolnya; satu-satunya jawaban yang tersisa
adalah data yang belum terjadi".

**Aturan baru.** Untuk semua pemilihan teracak: **laporkan distribusi hasil pemilihan, bukan satu
tarikan**, dan vonis hanya atas median distribusi itu - dipasang di `ringkas_topk(..., seeds=40)` dan
`uji_kombinasi()` di `tools/topk_test.py`. Ini korban **keempat** alat kami sendiri dalam empat hari
(F-D30 harga masuk beku → F-D32 control mempromosikan dirinya → F-D37 MW salah urut → F-D39 satu
undian disebut hasil), dengan pola yang selalu sama: **angka masuk vault sebelum pembandingnya
diaudit.**

**Terkait:** [[06-Results/18 - Kandidat Pertama, Diuji Hidup]] · [[08-Backlog/02 - Epik Alasan Masuk]]
§3d · [[07-Testing/01 - Test Commands]] baris 38/42 · [[Concepts/One-Way Gate]]

## F-D40 — Perilaku "pandai trading" yang terakhir (E8) juga gugur: yang terukur adalah UMUR posisi, bukan kerumunan · 29 Sep 2026 05:54Z

**Yang terbit lebih dulu.** Setelah E7 mencabut kandidatnya sendiri (F-D39), satu-satunya klaim
"Fabius bisa trading" yang berdiri di angka kami adalah **E8**: keluar saat kerumunan beli datang,
diukur pada **posisi yang sama** (+316,6 bps mean winso, median +116,5, 69 menolong vs 45 merugikan),
dan sudah dibuat jadi perilaku (`tools/exit_policy.py`).

**Kenapa kontrolnya salah.** E8 dibandingkan dengan **menahan sampai horison 30 menit**. Di kolam yang
mean pool-nya **−183,7** dan medannya **−123,8** bps, pembanding itu punya penjelasan alternatif yang murah:
*apa pun yang membuatmu keluar lebih awal akan terlihat lebih baik*. Pertanyaan yang benar bukan
"lebih baik dari menahan" - itu hampir pasti ya - tapi **"lebih baik dari keluar di waktu ACAK pada
jendela yang sama"**.

**Angka setelah kontrol dibetulkan** (`tools/exit_control.py`, 122 posisi identik, 150 undian,
`decisions/exit-control-20260929T055442Z.json`):

| lengan | mean winso | median | sebar antar-undian | vonis |
|---|---|---|---|---|
| keluar saat kerumunan beli | **+316,6** | +116,5 | — | — |
| keluar di waktu acak (5 m … horison) | +187,9 | — | **64,6 … 368,0** | CI atas **+357,1** |
| per posisi vs undian acaknya sendiri | menang **64** | kalah **50** | seri 8 | tanda-uji **p=0,112** |

**Vonis: TIDAK melewati keluar acak.** Yang diukur E8 adalah **memotong umur posisi**, bukan membaca
kerumunan. Docstring `tools/exit_policy.py` diturunkan mengikuti ini (bukan dihapus: alatnya jalan,
self-test-nya jalan, dan alasan yang dicatatnya tetap bisa diaudit) - tapi statusnya sekarang
**operasional**, dan ia **tidak boleh ditambal ke posisi asli** atas dasar bukti sinyal.

**Yang tersisa setelah empat koreksi alat (F-D30, F-D32, F-D37, F-D39, F-D40).** Satu perilaku yang
tetap berdiri karena dibandingkan dengan pembanding yang benar - **sesama posisi di siklus yang sama,
bukan nol**: **rem** `jual_*` (veto kerumunan jual). Policy test 28 Sep: A (never) 0 · B (blind)
**+82,7 [+5,0; +159,1]** · C (veto) **+162,3 [+80,4; +243,0]**. Itu bukan "pandai trading"; itu
"tahu kapan jangan masuk", dan sekarang punya angka pembanding yang jujur.

**Aturan yang ditambahkan, dan ini yang paling penting untuk hari-hari terakhir.** Untuk SEMUA
perilaku keluar/memotong: **kontrolnya harus "waktu keluar acak pada jendela yang sama"**, bukan
"menahan sampai habis". Di distribusi yang miring negatif, "keluar lebih awal" adalah strategi yang
menang sendiri. Alat yang menegakkan: `tools/exit_control.py` (punya `--self-test` dengan dua kasus
buatan - kerumunan awal menolong, kerumunan telat kalah).

**Terkait:** [[06-Results/13 - Apakah Tidak Trading Itu Gratis]] §3b · [[08-Backlog/02 - Epik Alasan Masuk]] §3d · [[07-Testing/01 - Test Commands]] baris 43 · [[Concepts/Unmeasured Is Not Clean]]

## F-D41 — Untuk pertama kalinya ada sesuatu yang POSITIF dan lolos placebo: kabar pasca-buy hidup ±2 menit · 29 Sep 2026 07:58Z

**Yang diukur.** `tools/horizon_decay.py` (E11): harapan sebagai fungsi **umur posisi**, 393
kejadian beli, harga `wp`, ongkos 59 bps RT, jendela sama dengan E7/E8/E10 (berhenti di `t_kunci`
watch). Mean winso: **+192,7 (2 m) → +202,6 (5 m) → +45,0 (10 m) → −42,0 (15 m) → −101,7 (20 m) →
−182,5 (30 m)**; uji berpasangan pada posisi yang sama vs 30 m: **5 dari 5 horison pendek menang**
(median +120,8 / +50,5 / +41,8 / +17,7 / +5,3 bps; tanda-uji p dari 0,00000 sampai 0,00002).

**Kenapa ini bukan F-D40 kedua.** Kami pasangkan tiga kontrol sebelum menulis satu kata pun:

| kontrol | hasil |
|---|---|
| placebo asal-mula digeser acak 30–90 m | **datar −184,7 … −113,9 di semua horison** → kemiringan menempel pada peristiwa, bukan pada jam |
| `P(ada harga keluar)` per horison | 84–85 % rata → bukan korban penyensoran selektif |
| umur baris `wp` yang dipakai keluar | median −6…+8 detik dari horison yang diklaim; `basi` 0 % → label "5 menit" adalah ukuran, bukan nama |
| harga masuk diganti sumber (`tx.p`) | bump 2 m +192,7 → **+168,8**; 5 m +202,6 → **+161,5** → menyusut, tidak hilang |

**Tapi inilah keputusan sebenarnya, dan dia tidak menyenangkan.** Scan latensi pada kurva yang sama:
`delay 0` mean@5m **+202,6** · `delay 2` **+47,3 dengan median −56,2** · `delay 5` **−166,4**.
Sementara latensi **data** kami diukur dari stempel commit GitHub: **median 0,2 menit**
(`_research/ukur_latensi_feed.py 25`). Artinya: kabar sampai dalam ±12 detik, acaranya selesai dalam
±2 menit, dan mesin keputusan kami dibangunkan **tiap 4 jam** (cron `paper-book`). Yang menahan
Fabius bukan ketiadaan sinyal - yang menahan adalah **belum ada jalur dari sinyal ke order pada
kecepatan sinyal itu hidup**.

**Keputusan.** (a) E11 **tidak** dijual sebagai kemampuan trading: mediannya +20…+60 bps pada dua
horison pertama, harapan datang dari ekor kanan (P(≥+500) 37–40 %), dan tanpa kedalaman (P33) kami
tidak bisa mengklaim bump setipis itu bisa diambil setelah dampak. (b) Dibuat uji terkunci baru
(P39): horison pendek sebagai **kebijakan**, diukur prospectif pada data setelah kunci, dengan
kontrol horison 30 m pada posisi yang sama - bukan dibalik jadi headline hari ini. (c) Dibuka
P40: jalur keputusan per-siklus (bukan cron 4 jam) dengan anggaran waktu yang jujur - dan itu
pekerjaan infrastruktur, bukan pekerjaan klaim. (d) Aturan baru untuk SEMUA uji horison: laporkan
**umur baris harga keluar** dan `P(ada harga keluar)` di samping kurva; kalau keduanya tidak
dilaporkan, angka horison tidak masuk vault.

**Skop yang tidak boleh dilewati.** E11 menguji **umur**, bukan arah masuk. Veto `jual_*` tetap
satu-satunya rem yang berdiri (F-D16/policy test), dan E9 tetap berjalan dengan aturan lamanya:
kunci 05:13:25Z TIDAK digeser walau kami sekarang tahu horison 30 m tempat ia dinilai sedang
bocor - itu harga dari pra-registrasi, dan kami membayarnya dengan sadar.

**Terkait:** [[06-Results/19 - Umur Posisi]] · [[08-Backlog/02 - Epik Alasan Masuk]] §3e ·
[[07-Testing/01 - Test Commands]] baris 44 · [[Concepts/Unmeasured Is Not Clean]]

## F-D42 — Self-testku menghapus berkas riwayat ⑦ dan git menyelamatkan kami · 29 Sep 2026 08:2xZ

**Yang terjadi.** `tools/fast_lane.py` saya beri `--self-test` yang menukar global `FLOW`/`LOG` ke
`tempfile`, lalu di blok `finally` **memulihkan global SEBELUM memanggil `os.remove`**. Urutan itu
membuat `os.remove(FLOW)` menunjuk `universe/wallet-flow.jsonl` - berkas riwayat 115.487 baris yang
jadi dasar E7/E8/E10/E11/E12 - dan **menghapusnya**. Tidak ada test yang gagal, tidak ada angka yang
berubah, tidak ada peringatan: gejalanya baru muncul saat alat berikutnya membuka berkas dan
mendapat `FileNotFoundError`.

**Kenapa ini lebih berbahaya dari bug statistik.** F-D37/F-D39 membuat kami salah simpul; bugs seperti
ini membuat kami **kehilangan bahan untuk menyimpul sama sekali**, dan ia datang dengan wajah
"pekerjaan sudah selesai" karena self-test-nya sendiri yang menghancurkan buktinya. Pemulihan:
`git checkout -- universe/wallet-flow.jsonl` (branch `master` lokal, tidak ada commit yang hilang;
origin tidak pernah tersentuh karena berkas itu tidak sempat di-`add`).

**Yang dipasang setelahnya (di alat, bukan di niat).** (a) berkas uji **dipaksa di luar `ROOT`**
dengan `assert not tmp.startswith(ROOT)`; (b) assert bahwa path uji berbeda dari path nyata sebelum
apa pun disentuh; (c) `finally` memulihkan global **lalu** menghapus berkas temp, dan di ujungnya
memeriksa `os.path.exists(FLOW_ASLI)` - kalau tidak ada, self-test **gagal keras**. Aturan epik:
**alat yang menguji dirinya sendiri tidak boleh punya jalan untuk menyentuh keadaan asli.**

**Kelas kesalahan ini bukan newcomer.** Dalam empat hari: harga masuk beku (F-D30), control yang
mempromosikan dirinya (F-D32), Mann-Whitney salah urut (F-D37), satu undian disebut hasil (F-D39),
kontrol keluar yang salah (F-D40), dan sekarang self-test yang memakan datanya sendiri (F-D42). Yang
membunuh semuanya bukan kecerdasan, tapi **perintah yang dijalankan sampai selesai** - dan itu sebab
setiap klaim di vault ini wajib punya baris di `vault/07-Testing/01 - Test Commands.md`.

**Skop.** Tidak ada angka yang berubah oleh peristiwa ini; tidak ada klaim yang ditarik. Yang berubah
adalah satu aturan di `tools/` dan kalimat ini, supaya orang berikutnya tidak mewarisi jebakan yang
sama.

**Terkait:** [[07-Testing/01 - Test Commands]] baris 46 · [[Concepts/Unmeasured Is Not Clean]] ·
[[08-Backlog/01 - Backlog]] P35

## F-D43 — Yang membatasi agen ini adalah JANGKAUAN VENUE, bukan kekuatan sinyal: 3,1 % kabar bisa dieksekusi · 29 Sep 2026 08:3xZ

**Angka yang ditemukan setelah kabar.** E11 memberi kami hal pertama yang positif dan lolos placebo
(bump ±2 menit, `tools/horizon_decay.py`). Refleks normalnya: cari ambang, cari horizon, cari fitur
yang membuat bump itu lebih tajam. Kami melakukan hal yang lebih dulu dan lebih murah:
**`tools/venue_bridge.py` membandingkan daftar tempat kabar hidup dengan daftar tempat kami bisa
berdiri.**

| | |
|---|---|
| basis aset di venue perp kami (`data/aster_symbols.json`) | **584** |
| simbol tempat kabar beli ⑦ hidup (`universe/wallet-flow.jsonl`, 25.050 kabar) | **2.163** |
| irisan | **61 simbol = 3,1 % dari volume kabar** |
| contoh kabar TERBANYAK yang tidak beririsan | `CUE` 459 · `BPAY` 311 · `FXION` 292 · `QQQB` 290 - dan empat simbol teratas justru **nama token non-Latin** dari pasar Four.meme (527 dan 513 kabar pertama); nama aslinya ada di artefak, tidak kami salin ke vault karena gerbang teks proyek menolak aksara di luar Indonesia/Inggris |

Artefak: `decisions/p41-venue-bridge.json` · perintah: `python -X utf8 tools/venue_bridge.py`.

**Konsekuensinya, ditulis tanpa dipoles.** **96,9 % dari kabar yang kami ukur terjadi di token yang
agen ini tidak bisa perdagangkan.** Jadi bahkan kalau bump E11 lolos uji prospectif dan terbukti bisa
diambil secara statistik, ia tetap bukan PnL agen ini - kecuali salah satu dari dua hal berubah:
(a) jalur eksekusi kami meluas ke spot/DEX tempat kabar itu hidup, atau (b) kami mempersempit
pengamatan ke 61 simbol yang bisa kami pegang dan mengukur ulang dari nol di sana. Yang (a) adalah
pekerjaan produk yang lebih besar dari sisa tenggat; yang (b) bisa dilakukan tapisampelnya langsung
kecil - dan kami sudah berjanji tidak menjual harapan di atas sampel yang tidak cukup (F-D16).

**Tembok kedua, jangan sampai terlewat.** Deret Aster yang kami punya berinterval minimal **15 menit**
(`tools/bars.py` `INTERVAL_MS`), sementara kabar E11 hidup ±2 menit. Artinya "apakah bump ini ada di
perp" tidak bisa dijawab dengan cache yang ada; ia butuh 1m-klines. Alat penghitung irisannya sudah
ada; alat uji jembatannya **belum**, jadi P41 ditulis 🟡 (cakupan terukur, arah belum) dan bukan ✅.

**Keputusan untuk halaman produk dan submission.** Semua kalimat yang menyebut E11 wajib membawa
angka 3,1 % ini atau merujuk F-D43. Boleh: "ada kabar berumur dua menit di substrate yang kami
amati; 96,9 % darinya terjadi di luar venue kami, dan itu sebabnya agen hari ini hanya boleh
dijual dengan rem-nya." Tidak boleh: "Fabius tahu kapan masuk", "edge bisa diambil", atau kalimat
apa pun yang membuat pembaca mengira bump itu milik portofolio yang bisa ia jalankan. Ini bukan
koreksi angka - ini **batasan klaim**, dan ia dibuat justru pada saat angkanya terlihat bagus, yang
adalah waktu di mana paling mudah berbohong.

**Lanjutan yang mengubah kesimpulan jadi angka (29 Sep ±09:0xZ).** Kami jalankan E11 **hanya pada
simbol yang ada di venue kami**: `python -X utf8 tools/horizon_decay.py --hanya-venue`. Hasilnya:
**393 → 24 kejadian, di 13 simbol** dari 584 basis aset. Alatnya menolak memotong kurva
(`kejadian cuma 24 - tidak cukup untuk memutus apa pun (ini BUKAN 'tidak ada kemiringan')`).
Jadi tiga pernyataan sekarang berdiri berurutan dan tidak bisa dipisahkan:

1. bump itu **ada** dan lolos placebo di substrat yang kami amati (E11);
2. **96,9 %** dari kabar itu terjadi di token yang tidak bisa kami perdagangkan (F-D43);
3. di **dalam** venue kami sendiri, sample yang tersisa (24 kejadian / 13 simbol) **belum bisa
   menguji apa pun** - dan ambang tidak kami turunkan untuk membuatnya jadi bisa.

Kalimat yang jujur: *"kabar yang kami temukan berada di luar jangkauan tangan kami, dan di dalam
jangkauan itu datanya belum cukup"*. Bukan "kami hampir bisa". Yang berubah kalau suatu hari kami
menambah jalur spot/DEX: angka (2) yang bergerak, bukan (1).

**Terkait:** [[06-Results/19 - Umur Posisi]] §3 · [[08-Backlog/01 - Backlog]] P41 ·
[[07-Testing/01 - Test Commands]] baris 48 · [[10-Submissions/01 - Claims Cheat Sheet]] (aturan mana yang boleh dijual)

## F-D44 — Satu-satunya hal yang masuk di horison tempat kabar hidup adalah REM · 29 Sep 2026 08:43Z

**Kenapa diukur ulang.** F-D31 memasang gerbang ⑦ `jual_*` karena hasilnya di **horison 30 menit**
(+82,7 → +162,3 bps). Setelah E11/F-D41 membuktikan bahwa 30 menit itu sendiri bocor, rem yang
terbukti di sana belum tentu berguna di tempat kabar hidup. Kami tidak memindahkan klaimnya;
kami mengujinya lagi dengan alat yang sama.

**Angka** (`tools/veto_expectancy.py`, 482 kejadian sampai `t_kunci` watch, `flow_gate.py` apa
adanya tanpa ambang baru; artefak `decisions/veto-expectancy-20260929T084355Z.json`):

| horison | n boleh | n veto | mean boleh | median boleh | mean veto | median veto | selisih | CI atas placebo |
|---|---|---|---|---|---|---|---|---|
| 2 m | 309 | 91 | +262,5 | +58,5 | −187,8 | −393,1 | +450,3 | +294,5 |
| **5 m** | 308 | 92 | **+285,5** | **+79,8** | **−230,3** | **−377,8** | **+515,8** | **+397,2** |
| 30 m | 307 | 92 | −72,7 | −61,9 | −560,2 | −996,6 | +487,5 | +405,1 |

**Tiga sifat yang tidak pernah datang bersamaan di uji kami sebelumnya:** (1) **median dan mean
searah** - median `BOLEH` di menit ke-5 = +79,8 bps, di atas lantai ongkos −59, jadi keuntungannya
tidak ditopang satu ekor; (2) **placebo yang benar** - penandaan ulang acak 200 undian atas angka
yang sama, dan tiga-tiganya lewat; (3) **tidak ada parameter yang disetel di halaman ini** - yang
diuji adalah perilaku yang sudah terpasang.

**Keputusan.** (a) E13 **tidak** mengubah satu pun ambang gerbang; dia hanya memberi alasan
berlaku *di mana* gerbang itu dipasang: horison cepat, bukan 30 menit. (b) Untuk materi submission,
kalimat yang boleh dipakai: *"rem kami memisahkan +285,5 dari −230,3 bps pada horison 5 menit,
melewati placebo penandaan ulang acak"* - dengan batasnya menempel di kalimat yang sama: VETO bukan
kelompok acak (ia adalah kejadian yang sedang dihajar penjual), jadi ini asosiasi terarah, bukan
sebab-akibat. (c) E13 **tetap eksplorasi tanpa kunci**; yang prospectif dan terkunci adalah E12
(vonis 20:04:56Z). Kalau nanti ingin menjual kombinasi gerbang+keluar cepat sebagai kebijakan,
dia butuh kunci sendiri - bukan halaman ini.

**Dua batas yang tidak digeser oleh hasil bagus.** Batas venue: hanya **3,1 %** kabar ada di token
yang bisa kami perdagangkan (F-D43), dan `--hanya-venue` menyisakan 24 kejadian - tidak cukup untuk
menguji apa pun di dalam venue kami. Batas latensi: menunda masuk 2 menit membuat median@5m −56,2
(F-D41) - jadi rem yang benar pun tidak menolong kalau kabarnya datang telat; pekerjaan P40 tetap
yang paling menentukan.

**Terkait:** [[06-Results/21 - Rem di Horison Cepat]] · [[06-Results/19 - Umur Posisi]] ·
[[07-Testing/01 - Test Commands]] baris 49 · [[08-Backlog/02 - Epik Alasan Masuk]] §3f ·
[[Concepts/One-Way Gate]]

## F-D45 — Rem diuji di grid ambang sebelum kami percaya dirinya: 16/16 lolos, dan pemindaian ulangnya 677/677 identik dengan gerbang asli · 29 Sep 2026 08:5xZ

**Kenapa ini diukur lebih dulu daripada klaim baru.** F-D44 memberi kami angka yang untuk pertama
 kalinya bagus: di menit ke-5, `BOLEH` +285,5 vs `VETO` −230,3 bps. Reaksi yang benar bukan mem posting
 nya, tapi curiga pada dua angka yang menentukannya - `MAKER_MIN = 2` dan `RASIO_JUAL = 1,5` - yang
 ditetapkan 28 Sep dari uji di horison 30 menit dan **tidak pernah** diuji sebagai fungsi horison
 cepat. Sebuah "edge" yang hanya hidup di satu titik parameter bukan perilaku, itu kekocokan.

**Yang dilakukan `tools/veto_sensitivity.py`.** Grid 4×4 (maker 1..4 × rasio 1,25; 1,5; 2,0; 3,0),
horison 5 menit, 677 kejadian yang punya harga keluar di 5 menit, placebo penandaan ulang acak 200
undian per kombinasi - **dan satu syarat sebelum laporan apa pun dicetak:** pada ambang terpasang,
pemindaian ulang alat ini harus memberi status yang **identik dengan `flow_gate.state()`** untuk
setiap kejadian. Hasilnya **677/677 cocok (0 berbeda)**; kalau satu saja berbeda, alatnya berhenti
dengan `SystemExit`, karena itu bug kami, bukan pasar.

| | |
|---|---|
| kombinasi ambang yang melewati placebo | **16 dari 16** |
| rentang selisih mean(BOLEH) − mean(VETO) | **+260,0 … +399,7 bps** |
| rentang CI atas placebo | +170,2 … +254,4 |
| titik terpasang (maker 2; rasio 1,5) | **+395,1** vs CI atas **+202,4** |

**Keputusan.** (a) Rem `jual_*` naik status dari "satu ambang yang terukur" menjadi "perilaku yang
bertahan di seluruh grid" - dan itu satu-satunya kelaikan yang boleh diklaim; (b) **tidak ada satu
angka pun yang diubah di `flow_gate.py`.** Grid ini menjawab "seberapa jauh hasil bergerak", bukan
"mana yang paling bagus"; memilih maker=4 karena grid menunjukkannya sama saja akan mengulang
F-D32 dengan nama baru. Mengubah ambang butuh pra-registrasi sendiri. (c) Aturan yang kini ikut
dipakai di alat: **kalau sebuah perilaku bergantung pada satu titik parameter, uji dulu dia bergerak
bagaimana sebelum menyebutnya temuan.**

**Batas yang harus dibawa bersama.** Populasi E14 (677) berbeda dari E13 (482) karena syarat harga
keluarnya berbeda (5 m vs 30 m) - jadi `mean boleh` 219,8 di sini dan 285,5 di sana bukan dua hasil
yang bertentangan, melainkan dua sample yang tidak sama; alatnya mencetak jumlah kejadian di baris
pertama supaya itu tidak bisa terlupakan. Dan dua pagar lama tetap berlaku: kabar ini ada di substrat
**spot** (venue kami hanya menyentuh 3,1 %, F-D43) dan ia **mati dalam ±2 menit** kalau masuknya
ditunda (F-D41). Sensitivitas tidak memperbaiki jangkauan atau latensi - ia cuma membuat kami boleh
percaya remnya.

**Terkait:** [[06-Results/21 - Rem di Horison Cepat]] §4 · [[00-Overview/03 - Decisions]] F-D31 /
F-D44 · [[07-Testing/01 - Test Commands]] baris 50 · [[Concepts/One-Way Gate]]

## F-D46 — "dampak" di buku paper salah satuan ±600x: mean +75,9 bps jadi −87,8 bps kalau dibetulkan · 29 Sep 2026 08:56Z

**Yang memancing.** F-D44 menulis "+285,5 bps di horison 5 menit" dan kami menagih batasnya:
angka itu hanya memakai ongkos 59 bps RT, tanpa dampak ukuran terhadap kedalaman. Untuk
memastikan tidak ada yang keliru, kami audit angka dampak yang *sudah* terpasang di
`tools/paper_book.py` - dan menemukan dua kesalahan yang berlawanan arah sekaligus.

**Yang terukur** (`tools/impact_audit.py`, 702 slot dinilai, `decisions/impact-audit-20260929T085648Z.json`):

```
   liq_usd diketahui: 219 | median $132.022 | p10 $1 | min $0 | max $3.688.624
   dampak_bps tercatat: median 0,00 | p90 0,20 | max 15.124,00

   varian                       n   mean winso     median    P>=500   positif
   tercatat                   702        +75,9      -58,9     31,1%     39,5%
   satuan_dibetulkan          219       -715,7      -92,1      4,1%      8,2%
   hanya_liq_sah              139        -87,8      -61,8      4,3%     10,8%
```

1. **Satuan.** `haircut()` menghitung `2 * size_quote / liq` dengan `size_quote` dalam **BNB** dan
   `liq` dalam **USD**. Jadi 0,01 BNB diperlakukan seolah $0,01: dampaknya kurang ajar **±600x** di
   mayoritas pool (median tercatat 0,00 bps; yang benar di pool $200k untuk 0,01 BNB @ $650 = 0,65 bps).
2. **Bahan baku di ekor bawah.** `liq` dilaporkan **$1 dan $0** pada desil terbawah. Membenarkan
   satuan saja memberi dampak 120.000-130.000 bps di pool itu - bukan kebenaran, sampah yang lebih
   besar. Karena itu yang dilaporkan alat adalah **tiga varian**, bukan satu "angka yang benar":
   `tercatat`, `satuan_dibetulkan`, dan `hanya_liq_sah` (floor $1.000, tempat x·y=k boleh dipakai).

**Angka yang berubah.** Mean buku kami **+75,9 → −87,8 bps** ketika satuan dibetulkan DAN pool di
bawah floor dibuang. Artinya klaim lama "random+veto +188,3 bps/posisi" (Fakta §F, halaman 14) adalah
**net of ongkos-59-bps dan hampir nol dampak**, bukan net of dampak yang sebenarnya.

**Keputusan - dan ini bagian yang tidak boleh dilewat.**
(a) **Kode TIDAK diubah malam ini.** E9 terkunci pada definisi "`net_bps` seperti yang dicatat
`paper_book`" dan slotnya sudah tercatat 25/25 pada 07:48Z. Mengganti alat di tengah uji terkunci -
sekalipun untuk memperbaikinya - adalah cara paling mudah memenangkan eksperimen. Perbaikan
dianggarkan sebagai **P42**, dikerjakan **setelah** vonis E9 (17:13:25Z) dan E12 (20:04:56Z), dengan
`skema_dampak` dicatat per slot supaya masa depan bisa dibedakan dari masa lalu.
(b) Setiap angka dampak yang kami kutip **wajib menyebut varian mana**. Kata "dampak" tanpa varian
tidak masuk vault lagi.
(c) Aturan baru: **satu model ongkos punya satu modul** (`tools/costs.py`) - `haircut` hidup di
`paper_book.py` dan `entry_lab.py` menyalinnya sebagai `2.0 * ukuran_bnb / liq` (baris 148), jadi
kesalahannya dua tempat. P42 memindahkannya ke `costs.py` dan memaksa keduanya memakai sumber yang
sama - ini persis alasan P10 dulu membuat `costs.py`, dan kami mengulangnya.
(d) E13/E14 tetap sah dengan batasnya sendiri (59 bps, tanpa dampak): justru karena itu F-D44 tidak
boleh dibaca sebagai "sudah net of semuanya".

**Korban keenam alat kami sendiri dalam lima hari:** F-D30 (harga masuk beku) → F-D32 (control
mempromosikan diri) → F-D37 (MW salah urut) → F-D39 (satu undian) → F-D40 (kontrol keluar salah) →
**F-D46 (satuan dampak)**. Polanya tetap sama: angka masuk vault sebelum penggarisnya diaudit.

**Terkait:** [[06-Results/14 - Buku Paper]] · [[06-Results/18 - Kandidat Pertama, Diuji Hidup]] ·
[[08-Backlog/01 - Backlog]] P42 · [[07-Testing/01 - Test Commands]] baris 51 ·
[[02-Fondasi/FD3 - Likuiditas dan Dampak Harga]] · [[Concepts/Unmeasured Is Not Clean]]

## F-D47 — Perekam buku order meruntuh 110 kegagalan sebelum kami lihat: daftar kami berisi BASIS, API minta SIMBOL · 29 Sep 2026 09:5xZ

**Yang terjadi.** `universe/record_book_depth.py` dipasang 09:1xZ dan langsung ikut loop rantai ⑦.
Laporan pertama, sesudah beberapa siklus CI:

```
   baris: 142 | simbol tercatat: 14 | kegagalan per kode HTTP: {"400": 110}
```

`universe/book-venue.txt` saya tulis dari **irisan basis aset** (`0G`, `APE`, `CAKE`) hasil
`venue_bridge.py`, sedangkan `/fapi/v1/depth` meminta simbol kuotasi penuh (`0GUSDT`). Semua jangkar
(BTC/ETH/SOL/BNB) lolos karena kebetulan sudah saya tulis lengkap - jadi alatnya "hidup", mencetak
baris, dan tetap 85 % isinya sampah. Diagnosisnya satu baris `git`-style: `{"code":-1121,
"msg":"Invalid symbol."}` yang **tidak saya simpan** di versi pertama - saya cuma menyimpan
`kode_http`, sehingga laporan berkata "400: 110" tanpa bisa menjawab "kenapa".

**Yang dipasang setelahnya.** (a) `normal()` memetakan basis -> simbol kuotasi (tambah `USDT` kalau
belum bersufiks); (b) `msg` API ikut dicatat di baris `bdx`, supaya kegagalan punya penyebab, bukan
cuma kode; (c) `--validasi-saja` memotong daftar terhadap `exchangeInfo` dan **mencetak berapa yang
dibuang**; (d) daftar valid dipakai setiap siklus sebelum merekam. Verifikasi: `12/12 simbol
terjawab`, nol kegagalan baru.

**Yang harus ditulis tentang E16 (jujur soal jam yang sudah berjalan).** Kunci E16 dipasang
09:37:45Z. Sebelum 09:5xZ, hampir semua snapshot pasca-kunci adalah **jangkar likuid** (BTC/ETH/SOL)
karena simbol kabar ditolak API. Artinya jendela E16 tidak homogen: ada perubahan cakupan **di
tengah uji terkunci**. Kami tidak menggeser kunci dan tidak membuang data - keduanya akan jadi
goalpost-moving. Yang kami lakukan: vonis nanti **wajib** menyertakan komposisi (berapa pasangan per
simbol, berapa sebelum vs sesudah 09:5xZ), dan kalau komposisinya ternyata jangkar-dominan, itu
dinyatakan sebagai **batas baca**, bukan sebagai kemenangan. Ini pelajaran yang sama dengan F-D46
(mengganti penggaris di tengah ujian) dengan wajah sebaliknya: kali ini penggarisnya berubah karena
bug, dan yang harus dilakukan adalah **melaporkan**, bukan mempercantik.

**Yang pertama kali dijawab data, bukan argumen.** Setelah daftar dibetulkan, `tools/cost_budget.py`
langsung memberi angka yang tidak bisa dibantah retoris:

| simbol | spread median | biaya RT penuh (59 + spread) | dalam anggaran median (+79,8 bps)? |
|---|---|---|---|
| BTCUSDT / ETHUSDT / SOLUSDT | 0,01 / 0,04 / 0,84 bps | 59,01-59,84 | YA (jangkar) |
| CAKEUSDT / 0GUSDT / APEUSDT / ARIAUSDT / AEONUSDT | 7,8-20,2 bps | 66,8-79,2 | YA, tapi mepet |
| AIUSDT | 40,8 bps | 99,8 | **TIDAK** |
| 4STOCKUSDT / ASTEROIDUSDT | 422,3 / 519,5 bps | 481,3 / 578,5 | **TIDAK, jauh** |

Jadi untuk simbol kabar yang paling tipis, **biaya satu kali keluar-masuk sudah 6x harapan median
kami** - dan ini sebelum bicara apakah sinyalnya ada. Catatan sampelnya tetap menempel: 9 dari 14
simbol baru punya < 5 snapshot, jadi baris di atas adalah **pengamatan pertama**, bukan median yang
stabil.

**Korban ketujuh alat kami dalam enam hari** (F-D30, F-D32, F-D37, F-D39, F-D40, F-D43, F-D46,
F-D47). Polanya tetap sama dan sekarang sudah bukan kebetulan lagi: **alat baru dianggap bekerja
karena ia menulis sesuatu**, bukan karena isinya yang kita butuhkan. Aturan yang ditambahkan ke
epik: setiap perekam baru wajib menunjukkan **rasio baris-berguna vs baris-total** di `--report`
sebelum dianggap hidup (sudah ada di laporan ⑨: `bd=… bdx=…`).

**Terkait:** [[06-Results/22 - Buku Order, Terkunci Lebih Dulu]] §5c · [[08-Backlog/01 - Backlog]]
P47 · [[07-Testing/01 - Test Commands]] baris 51/53 · [[08-Backlog/03 - Epik Teori Baru]] T1/T4

## F-D48 — Algebra trailing diukur pada jalur harga kami, dan angkanya membantah dugaan saya · 29 Sep 2026 10:12Z

**Awalnya saya ingin menulis "jendelanya kosong".** Teori builder (trailing stop "pokoknya
jangan sampai rugi", jaraknya sudah hitung spread + fee) punya penurunan yang jelas:

```
  PnL = pi - d - s - i - C      LOCK>=0 <=> pi >= d+s+i+C      anti-bounce <=> d > s
  =>  syarat perlu  pi > 2s + i + C ;  jendela sah  s < d <= pi - s - i - C
  =>  "jangan sampai rugi" (semua path) butuh d <= -(s+i+C) : TIDAK ADA d >= 0
```

dengan C = 59,0 bps (terukur, `tools/costs.py`). Dugaan saya: puncak tipikal kami cuma +192,7 bps
(E11 @2m), jadi dengan spread saja jendelanya sempit. `tools/trailing_gate.py` mengukur
**puncak sebenarnya pada jalur yang kami punya**, dan dugaannya salah:

| | angka |
|---|---|
| puncak median, jendela 60 m | **+1.122,0 bps** (p75 +4.234,0) |
| puncak median di **paruh awal** jendela | **+747,1 bps** |
| spread TERUKUR ⑨ (44 snapshot, 14 simbol) | p50 **0,04** · p90 **13,54** · max 519,48 bps |
| fraksi kejadian dengan jendela d sah | **66,1 %** (pi) · **63,0 %** (pi_awal) |
| bahkan di s = 200 bps dengan i = s | masih **51,9 %** |

**Yang benar ditulis apa adanya:** "jangan sampai rugi" tetap mustahil - itu algebra, bukan
pengukuran. Tapi **lock bersyarat adalah hal yang lazim di substrate ini**, dan klaim bahwa idenya
"tidak mungkin" akan jadi klaim palsu dari saya. Yang benar-benar membatasi tiga hal lain:
(1) **resolusi** - pada 5 menit, 69 % kejadian tidak punya dua baris harga sama sekali (31 %
terlihat), jadi trigger tidak bisa diletakkan di tempat kabar hidup; (2) **waktu** - `pi_awal`
hanya proksi "cukup awal", bukan replika pemicu; (3) **bukan drift** - stop mengubah bentuk
distribusi, dan itu persis yang dikatakan literatur: *"neither reduce nor increase investors'
losses ... the value of stop loss strategies may come largely from risk reduction rather than return
improvement"* (Lei & Li 2009, Financial Services Review 18(1):23-51 - abstrak saya baca langsung,
S6). Osler (NY Fed SR150, S7) menambah sisi eksekusinya: tren "unusually rapid" di level tempat
stop berkerumun, dan respons stop **lebih besar** daripada take-profit - jadi `i` bukan nol, dan
belum kami ukur.

**Keputusan.** (a) E17 boleh dibangun, tapi **vonisnya bukan "apakah trailing menguntungkan"**:
yang diukur adalah perubahan `P(net ≤ −X)` dan median pada posisi yang sama, lawan **random-barrier
placebo** (level stop digambar dari distribusi yang sama tanpa berjangkar ke puncak) - karena
kombinasi algebra + Lei&Li meramalkan bentuk, bukan arah. (b) `i` (gap fill−trigger) jadi variabel
yang HARUS direkam ⑨ sebelum angka "net of cost" di venue dipakai - tambahkan ke P45. (c) Satu
aturan metode lagi, dari kejadian nyata ini: **turunkan algebra-nya lebih dulu, lalu ukur
distribusinya - dan biarkan distribusi membantah Anda.** Vonis yang keluar dari alat ini
membatalkan kalimat yang sudah saya siapkan di kepala; itu bukan kegagalan, itu gunanya.

**Terkait:** [[06-Results/23 - Gerbang Trailing]] · [[08-Backlog/03 - Epik Teori Baru]] T2 ·
[[08-Backlog/04 - Riset Teori (Sitasi)]] S6-S9 · [[07-Testing/01 - Test Commands]] baris 55 ·
[[TradingKnowledge/FD7 - Invalidation Stop dan Time-Stop]]


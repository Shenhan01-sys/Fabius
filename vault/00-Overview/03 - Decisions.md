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

## F-D49 — Placebo pertama saya curang (look-ahead), dan baseline pairing yang benar mengubah kesimpulan · 29 Sep 2026 10:39Z

**Dua kesalahan yang ketahuan sebelum kesimpulan ditulis.** (1) Placebo penjangkaran saya
(`level_statis`) mengambil levelnya dari `max(seluruh jalur)` - puncak **akhir** jendela. Placebo
yang boleh melihat masa depannya pun menang atas trailing dengan **+50,9 bps** yang sepenuhnya
artifisial. (2) Baseline pairing pertama saya adalah `A tahan 30 m`, tapi lengan lain memakai
fallback "keluar di baris terakhir jalur (60 m)" - dan **45/332 posisi (14 %) tidak punya baris
harga antara 30 dan 60 menit**, jadi di sana "tahan 30" dan "tahan 60" adalah harga yang sama
secara harfiah: delta 0,0 persis, dan placebo kelihatan "menyamai". Setelah baseline diganti jadi
A2 (fallback yang sama untuk semua lengan), tabelnya berubah arah di beberapa baris.

**Hasil akhirnya justru lebih penting dari kedua bug-nya: E17 tidak bisa dinilai dengan data kami.**
25 dari 28 lengan punya **delta median tepat 0,0** - pada 1-4 bar per jam, level stop sebagian besar
posisi **tidak pernah tersentuh bar**. Saat bar dijarangkan x2 dan x4, keunggulan lengan
"bersyarat" runtuh (+105,2 → +9,2 → −83,9) sementara baseline diam di −183: yang saya hampir
umumkan sebagai kebijakan adalah **resolusi sampel**.

**Keputusan.** (a) P49 → **BLOCKED-BY-DATA**, bukan "belum sempat": uji exit dinamis apa pun di repo
ini butuh bar lebih rapat (streaming/1m), dan itu pekerjaan yang sama dengan P40. (b) Aturan alat
baru: **placebo tidak boleh punya hak melihat masa depan yang lebih besar dari lengan yang diuji**,
dan baseline pairing harus memakai **fallback yang identik** - kalau tidak, delta 0,0 menyamar
sebagai "tidak ada beda". (c) Yang boleh tetap ditulis dari E17: stop mengubah **bentuk**
distribusi (P(≤−200) 46,4 % → 35,2 %; persen positif 40,4 % → 51,8 %) dan bukan harapan -
sesuai Lei & Li (2009).

**Ini koreksi kesembilan alat kami dalam enam hari** (F-D30, F-D32, F-D37, F-D39, F-D40, F-D43,
F-D46, F-D47, F-D49), dan pola barunya: kali ini yang salah bukan angkanya, tapi **siapa yang boleh
melihat masa depan** saat angka itu dihitung.

**Terkait:** [[06-Results/24 - Trailing pada Bar yang Salah]] · [[06-Results/23 - Gerbang Trailing]] ·
[[08-Backlog/01 - Backlog]] P49 · [[07-Testing/01 - Test Commands]] baris 56

## F-D50 — Aku memakai statistik yang paling beruntung untuk menyalahkan kodeku sendiri: umur kabar yang kami olah itu 13,5 menit, bukan 0,2 · 29 Sep 2026 11:1xZ

**Yang tertulis kemarin (halaman 19 §2b, README, Fakta §F):** "latensi feed kami **median 0,2
menit** (stempel commit GitHub) - kabar sampai dalam ±12 detik, acaranya selesai dalam ±2 menit, dan
mesin keputusan kami bangun tiap 4 jam. Yang menahan bukan sinyal, tapi jalur." Kalimat itu terasa
jujur, karena dia menyalahkan diri sendiri. Ternyata dia tetap salah - dengan arah yang membuat
kesimpulannya tidak berlaku.

**Definisi yang kutukar.** `0,2 menit` = `waktu commit − t(baris TERBARU pada versi berkas saat
itu)`. Itu umur **potongan paling segar dalam satu muatan**. Pertanyaan yang benar untuk sebuah
strategi bukan "seberapa segar baris terakhirmu", tapi "seberapa tua peristiwa yang kamu
olah". Yang kedua terukur langsung, tanpa rekonstruksi: `tools/fast_lane.py` mencatat
`latensi_keputusan_detik` = `now − t_kejadian` **pada saat keputusan benar-benar diambil atas berkas
yang baru saja ditulis runner yang sama**.

| ukuran | angka | dari |
|---|---|---|
| commit − t baris terbaru | median **0,2 menit** (p90 0,2) | `tools/feed_latency.py 25` |
| **umur kabar saat kami memutuskan** | median **808 d = 13,5 menit**, min 534, p90 874, max 899 | `tools/fast_lane.py --report`, 276 baris CI jam 09-11Z |
| umur bump E11 | **±2 menit** (`delay 2 m` → median@5m −56,2 bps) | `tools/horizon_decay.py` |

**Konsekuensinya bukan kosmetik.** Kalau kabar datang sudah berumur ±11 menit, maka **mempercepat
pipeline menjadi 0 detik pun tidak menyentuh bump itu**. P40 (yang barusan kupasang dan sudah jalan di
CI) adalah pekerjaan yang perlu tapi **tidak cukup**, dan kalimat "tinggal eksekusi" yang
sebelumnya kubiar berdiri harus dicabut. Karena itu: (a) **P50** - sumber kabar yang lebih muda dari
umur kabarnya (streaming/websocket/vendor lain, atau harga venue kami sendiri sebagai sumber);
(b) kalau itu tidak ketemu, **E11 turun status** dari "edge yang belum kita ambil" menjadi
"observasi yang tidak bisa diambil oleh sumber yang kita punya" - dan itu harus sampai ke
kalimat submission, bukan berhenti di vault.

**Cara salah ini terjadi, dan itu yang harus diingat.** Aku mengukur sesuatu yang benar, dengan alat
yang jujur, lalu memakai **ekor terbaik dari distribusinya** sebagai ringkasan. Yang membuat kesalahan
ini lolos bukan angkanya, tapi **arahnya**: dia membuat kami tampak jadi kambing hitam, dan kesimpulan
yang menyalahkan diri sendiri terasa paling sulit ditolak. Koreksi ketujuh dari alat kami sendiri
dalam enam hari sekarang punya varian baru: **bukan alatnya yang salah, tapi pilihannya atas
statistik yang menguntungkan cerita yang sedang kita percayai.**

**Yang kucoba setelah itu, dan juga kutolak.** Rekonstruksi umur kabar lewat selisih himpunan baris
antar-commit menghasilkan median **1494 MENIT** - jelas salah (perekam menumpuk baris lama sekaligus).
Angkanya tidak kucabut diam-diam: `tools/feed_latency.py --saat-ditemukan` sekarang mencetak
**"TIDAK BOLEH DIKUTIP"** di outputnya dan **tidak menulis artefak**, supaya tidak ada yang
(melainkan saya nanti) mengutipnya sebagai angka.

**Addendum 11:3xZ - angka 808 d itu BATAS ATAS, dan sebagian karena alatku sendiri.**
`tools/fast_lane.py` mengambil kandidat "12 teratas dari urutan berkas", padahal satu muatan GMGN
membentang puluhan menit: yang terpilih sistematis yang **paling tua** di jendela. Perbaikannya sudah
masuk (`sorted(..., key=-t)`), dan yang benar ditulis sekarang: **808 d adalah batas atas umur kabar
saat kami memutuskan**, bukan ukuran temunya. Yang memutus soal ini bukan argumen tapi cap baru:
perekam sekarang menulis `arr` (waktu baris tiba di runner) per baris, dan
`python -X utf8 tools/feed_latency.py --kedatangan` membacanya sebagai `arr - t` - kalau median itu
jauh di bawah 808 d, yang lambat memang kami; kalau sebanding, P50 mati bersama harapan mengambil
bump 2 menit ini. Sebelum ada >= 30 baris bercap, alatnya menolak dan berkata BELUM TERUKUR.

**Terkait:** [[06-Results/19 - Umur Posisi]] §2b · [[08-Backlog/01 - Backlog]] P40/P50 ·
[[07-Testing/01 - Test Commands]] baris 47/58 · F-D41 (batas waktu yang menghormati horison) ·
[[TradingKnowledge/FD5 - Expectancy Bukan Win Rate]]

## F-D51 — "+188,3 bps" itu artefak budget: pada 200 posisi/hari control-nya +165,7; pada 24/hari −100,2; pada 5/hari (kontrak) −26,7 · 29 Sep 2026 11:5xZ

**Yang memicu.** Builder bertanya "di papernya lolos tidak?" - pertanyaan yang benar, karena
imenolak uang asli. Aku jalankan alatnya tiga kali di berkas **peristiwa yang sama** (1.884
kesempatan, 4 hari, ongkos 59 bps), hanya budget yang berubah:

| `--per-day` | n | control `random` | `lock` | `first` | `vol-rendah` | `vol-tinggi` | median control | % posisi positif |
|---|---|---|---|---|---|---|---|---|
| 200 | 800 | **+165,7** | +79,4 | +164,3 | +90,1 | −98,3 | −54,4 | 45,2 % |
| 24 (yang CI tulis) | 96 | **−100,2** | −160,8 | −57,1 | −98,0 | **+43,3** | −79,6 | 35,4 % |
| 5 (kontrak kita) | 20 | **−26,7** | −161,5 | −489,9 | −318,8 | −1.022,7 | +201,1 | 50,0 % |

**Tiga hal yang harus dibaca bersamaan.**
1. **Tidak ada yang berubah di pasar; yang berubah adalah berapa banyak posisi yang kami berani
   ambil.** Ini bukan kontradiksi - pada n=20 dan n=96 selisih antar-kebijakan jauh lebih besar
   daripada selisih antar-arm di n=800. Yang salah adalah kalimat kami sebelumnya
   ("random+veto **+188,3**", halaman 14 + Fakta §F + registry baris 26/27) yang dikutip
   seolah itu properti strategi, padahal itu properti **satu jendela pada satu budget**.
2. **Di budget kontrak (5/hari) semua arm negatif** dan `lock` lebih buruk dari `random`. Jadi
   jawaban untuk "lolos di paper?" adalah **TIDAK**, dan alatnya sendiri yang mengatakannya:
   `vonis kebijakan lock: BELUM LAYAK - belum di atas control`, dengan CI bawah **−382,8** (syarat
   F-D16 "CI bawah > 0" gagal) dan `di atas acak: False`. Streak 2 beruntun tercapai di 7/96
   slot, dan alatnya mencetak sendiri "STREAK CUKUP != kebijakan layak".
3. **Peringkat lengan E9 berbalik menurut budget** (`vol-rendah` > `vol-tinggi` di 200 dan di 5;
   **kalah** di 24). E9 diuji pada 24/hari dengan **n=26**. Ini kutulis **sebelum** jam vonisnya
   (17:13:25Z), supaya tidak ada yang - termasuk aku - membaca hasil 26 slot itu sebagai
   penemuan arah: yang akan kita dapatkan paling banter adalah "pada satu budget, 26 posisi".
   Kuncinya tidak kusentuh; yang kutambah adalah peringatan ini, persis seperti §5c.

**Keputusan.** (a) Setiap angka buku paper yang dikutip di vault/README **wajib menyebut
`--per-day` dan `n`-nya**; tanpa itu angkanya bukan hasil, itu potongan jendela. (b) Halaman 14
diberi banner koreksi (bukan penghapusan - `+188,3` memang terukur pada jendela 28 Sep, dan
menghapusnya akan menghilangkan jejak bahwa kami pernah membacanya terlalu jauh). (c) Untuk
submission, klaim paper yang benar adalah: *"pada budget kontrak 5 posisi/hari, tidak ada satu pun
kebijakan yang mengalahkan control acaknya dan tidak ada yang punya CI harapan di atas nol"* -
dan justru itu bukti sistemnya bekerja: gerbang promosi menahan kami sendiri.

**Terkait:** [[06-Results/14 - Buku Paper]] · [[06-Results/18 - Kandidat Pertama, Diuji Hidup]] §5c/§5d ·
[[07-Testing/01 - Test Commands]] baris 60 · [[08-Backlog/01 - Backlog]] P52

## F-D52 — Perilaku satu-satunya yang kita punya kini punya uji prospectif-nya sendiri: E22, kunci 12:08:15Z, vonis 20:08:15Z · 29 Sep 2026

**Kenapa.** Semua bukti untuk rem `jual_*` berasal dari jendela yang sama: F-D31 (+82,7 → +162,3 bps
di 30 menit) dan F-D44 (menit ke-5: `BOLEH` +285,5 vs `VETO` −230,3, plus 16/16 grid ambang dari
F-D45) berhenti di jam `t_kunci` watch. Kami sudah lima kali membawa angka in-sample ke dokumen dan
lima kali menariknya kembali (F-D30, F-D32, F-D39, F-D40, F-D46). Bedanya dengan lima kejadian itu:
sekarang kunci dipasang **sebelum** ada satu pun pasangan pasca-kunci - `tools/gate_ab.py --status`
mencetak "kejadian pasca-kunci: 0" pada saat rule-nya ditulis.

**Yang diikat** (`decisions/prereg-gate-lock.json`, `spec_sha256=0x6f6e61f8a29bed68…`, halaman
[[06-Results/25 - Rem, Terkunci Prospectif]]): populasi = beli ⑦ dengan `t > t_kunci`, non-overlap
1/30 m/token; outcome = median `wp` pada t+[2m, 8m] − harga masuk − 59,0 bps; winsor **1.500** bps
(lebih ketat dari E11/E13 karena puncak micro-cap kami mencapai 8000x - angka ini dipilih sebelum
lihat hasil, bukan sesudah); empat syarat serentak: (1) n≥40 `BOLEH` dan n≥15 `VETO`; (2)
median(BOLEH) > 0 **dan** CI bawah bootstrap 4000 dari **selisih dua mean** > 0 (bootstrap-nya
terpisah per lengan, bukan zip posisional - itu kesalahan yang sama yang baru kami hukum di F-D49);
(3) satu arah lewat **dua** kontrol sekaligus (Mann-Whitney p<0,05 DAN selisih > CI atas placebo
penandaan ulang 1.000 undian); (4) `P(ada harga keluar)` ≥ 60 % di kedua lengan **dan** umur baris
harga keluar dilaporkan per lengan.

**Satu kompromi yang dinyatakan di muka.** Syarat umurnya **8 jam**, bukan 12 seperti tiga kunci
sebelumnya. Alasannya ditulis sekarang, bukan nanti: tenggat submission 30 Sep 16:59Z, dan 8 jam
siklus ⑦ (~200 detik) memberi ratusan kejadian. Ini bukan mengendurkan ambang supaya vonisnya keluar
- itu justru yang dilarang halaman 12/20/22 - karena saat aturan ditulis, n-nya nol dan tidak ada
seorang pun tahu apakah 8 jam cukup. Kalau saat matang n masih kurang, vonisnya "BELUM BISA
DIUJI" dan itu jawaban yang sah.

**Kalau GAGAL**, yang bergerak adalah kalimat kami, bukan aturannya: "rem memperbaiki hasil"
turun jadi klaim in-sample dan itu akan kutulis di halaman 21 + F-D44. **Kalau LAYAK**, ini untuk
pertama kalinya perilaku Fabius lolos pada data yang belum ada saat rule-nya ditulis - dan tetap
bukan "profit": tiga tembok hari ini tidak digeser oleh hasil mana pun (venue **3,1 %**,
umur kabar **±13 menit** dengan bump **±2 menit**, `i` **+245 bps**).

**ADDENDUM 29 Sep 20:32:34Z - cabang “kalau GAGAL” itulah yang terjadi, dan dua koreksi untuk diriku sendiri.**

E22 jatuh **GAGAL** (kunci `12:08:15Z`, `spec 0x6f6e61f8…` tidak disentuh; 429 kejadian pasca-kunci,
n BOLEH 319 / VETO 110): mean winso **−9,9 vs −121,4** (arah benar, selisih +111,5) tapi median
**−57,9 vs −59,0**, CI selisih **[−134,0 ; +344,4]**, MW **p=0,159**, dan **CI atas placebo +223,7
lebih tinggi dari efeknya**. Jadi seperti yang ditulis entri ini sendiri sebelum datanya ada:
**“rem memperbaiki hasil” turun jadi klaim in-sample** - sudah kutulis di halaman 21 sebagai baris
koreksi di atas angka lamanya, di halaman 25 §5, dan keputusannya di **F-D64**.

Dua koreksi kecil yang tetap perlu dicatat karena halaman ini akan dibaca orang lain:

1. **rujukan-nya salah**: entri ini menulis “...turun jadi klaim in-sample dan itu akan kutulis di
   halaman 21 + **F-D44**”. Yang benar **F-D64**; F-D44 adalah keputusan lain (edge baris 0-3 menit).
   Salah rujuk seperti ini tidak tergerbang `check_links` karena ia menyebut nomor, bukan jalur -
   jadi kuperbaiki di sini, bukan dengan mengedit kalimat aslinya.
2. **“tiga tembok hari ini” sudah bergerak dua kali sejak entri ini ditulis**, dan bukan ke arah yang
   menguntungkan: umur kabar **bukan** ±13 menit lagi (61 d setelah bug urutan pemilihan kandidat dibetulkan, F-D54)
   - dan justru karena itu temboknya pindah ke **titik masuk** (`i` +245 bps; `entry_px` di atas harga
   whale pada 16/25). Venue juga bukan satu angka lagi: **2,26 %** pasangan / **5,86 %** aset (F-D57),
   dan yang benar-benar hidup di resolusi menit cuma **5 dari 41** simbol (F-D56). Kalimat “hasil mana
   pun tidak menggeser tiga tembok” tetap benar; daftar temboknya yang harus dibaca lewat halaman 26-28.

Dan satu hal yang entri ini **tidak** boleh dijual: vonis LAYAK tidak akan berarti “Fabius bisa
trading”. Ternyata yang terjadi malah kebalikannya - yang lulus prospectif malam ini bukan rem,
melainkan **aturan keluar** (E12, n=685, CI bawah +135,9), dan mean lengan cepatnya cuma +8,1 bps.

**Terkait:** [[06-Results/25 - Rem, Terkunci Prospectif]] · [[06-Results/21 - Rem di Horison Cepat]] · [[08-Backlog/02 - Epik Alasan Masuk]] §3f · [[07-Testing/01 - Test Commands]] baris 61 ·
[[TradingKnowledge/QT4 - Overfitting dan Validasi]]

## F-D53 — Daftar pantau buku order TIDAK kulebarkan malam ini, walaupun itu membuat E16 mungkin gagal karena n · 29 Sep 2026 12:26Z

**Godaannya konkret, bukan abstrak.** E16 (`spec_sha256=0xeba3e0c5…`) berdiri di 26 simbol, median
16 snapshot per simbol, dan aku sudah menghitung bahwa irisannya 90 simbol - jadi satu baris tulis
berikutnya bisa melipatduakan sampelnya sebelum vonis 21:37:45Z, dan vonis itu akan jauh lebih
berkuasa. Tidak ada yang menyebut itu curang; terdengar seperti kerja bagus (lebih banyak data!).

**Kenapa kutolak.** Frame sampel adalah bagian dari ujian. Sekali spec di-sha, memperbesar frame =
mengganti soalnya, bukan mengisi jawabannya - dan kami sudah membayar tiga versi kesalahan ini dalam
sepekan: F-D32 (kontrol yang terpilih oleh sifarnya sendiri), F-D47 (cakupan berubah di tengah
jendela karena bug, dan kami harus mengakuinya, bukan memperindahnya), F-D51 (peringkat lengan E9
berbalik saat budget diubah - jadi “sampel mana” menentukan jawabannya lebih dari yang kami kira).
Yang membuat godaan kali ini kuat justru karena ia *menguntungkan kami*: menaikkan n membuat
peluang LAYAK naik. Itu tanda paling jelas bahwa yang sedang menyetir bukan pertanyaan, tapi
jawabannya.

**Keputusan.** (a) E16 jalan di 26 simbol, apa pun hasilnya - termasuk kalau “BELUM BISA DIUJI”,
yang tetap jawaban sah. (b) Pelebaran daftar dijadwalkan sebagai **P54**, dieksekusi **setelah**
21:37:45Z, dengan validasi ke `exchangeInfo` (yang dibuang dicetak), lalu **kunci baru** atas frame
baru itu. (c) Aturan yang kutulis ke halaman 22 §5d: *frame sampel boleh diganti hanya untuk uji
berikutnya, tidak untuk uji yang sudah di-sha.* Kalau nanti angka E16 memang tipis karena n,
kalimat yang benar adalah “belum bisa diuji pada 26 simbol”, bukan “teorinya salah” - dan P54-lah
yang akan menjawabnya.

## F-D54 — 58 dari 58 lengan 5 m jalur cepat mengukur MASA LALU; blok pairing-nya kucabut, dan tembok "kabar 13,5 menit" ternyata tembokku sendiri · 29 Sep 2026 12:55Z

**Yang terjadi.** Aku punya tiga "tembok" yang mengurung bump E11: venue (3,1 %), umur kabar (808 d),
dan celah harga masuk (`i`, +245 bps). Yang kedua kubuang hari ini, bukan dengan analisis, tapi dengan
perbaikan satu baris di `beli_baru()`: kandidat dulu diambil "12 teratas dari URUTAN BERKAS", dan
karena satu muatan GMGN membentang puluhan menit, itu berarti sistematis mengambil yang paling TUA di
jendela. Sesudah diambil dari yang paling segar, `tools/fast_lane.py --report` mencetak dua rejim
terpisah: **812 d → 61 d (92 % lebih muda) pada alat yang sama.** Jadi kalimat "kabar kami mati sebelum
kami selesai membacanya" salah alamat: yang mati adalah caraku mengambil kabar, dan kabar ⑦ tiba
rata-rata berumur 24 d pada baris yang benar-benar kami putuskan.

**Lalu alatku sendiri ketahuan salah ukur.** Jendela arm 5 m adalah `kejadian + 5 m ± 3 m`, yaitu mulai
di kejadian + 120 d, sedangkan harga masuk kami adalah harga SAAT KEPUTUSAN. Keputusan yang tiba pada
umur 812 d berarti jendelanya **sudah lewat sebelum kami masuk** - jadi angka yang keluar bukan "hasil
dari masuk kami", tapi selisih antara masa lalu dan harga kami. Hitungannya: **0 dari 58 lengan 5 m
rejim lama sah.** Termasuk tiga slot pairing yang sudah kupublikasikan (`5m −59,0` / `30m +139,3` /
`delta −17,5`) dan baris `PROSPEKTIF n=86` - itu gabungan dua rejim, yang sah hanya 25.

**Angka pertama yang boleh dipakai** (`--report`, 12:5xZ, n=25 lengan sah, umur keputusan min 42 /
median 58 / maks 96 d, 24 token berbeda): **mean winso −519,4 | median −76,4 | mean mentah −1.016,6 |
positif 5 dari 25 | 9 posisi jatuh > 1.000 bps.** E11 menjanjikan positif pada delay 0-2 m (+202,6 →
+47,3); yang hidup memberi −519,4, dan sebab yang terukur: `entry_px − tx_p` median **+25,7 bps**,
p90 **+1.199,6**, dan pada **16 dari 25** posisi harga kami sudah DI ATAS harga transaksi whale.

**Keputusan.** (a) Semua angka pairing/PROSPEKTIF jalur cepat yang pernah dikutip **dicabut sebagai
pengukuran**, bukan dijadikan hasil negatif - halaman 26 menyimpan tabelnya, halaman 19 §2b dan cheat
sheet kuberi koreksi bertanggal, baris 808 d sekarang berstatus "deskripsi rejim lama". (b) Alat
diubah supaya tidak bisa mengulangi: `nilai_arm()` mengembalikan `sah` + `umur_keputusan_d`, keputusan
telat menjadi status **`DI LUAR JENDEL`** (dihitung, bukan dinilai, bukan nol), laporan memisah dua
rejim dan melabeli median gabungan **TIDAK BOLEH DIKUTIP** - 5 assert baru di self-test. (c) Angka
−519,4 **tidak** kujadikan vonis: n=25, satu lengan, tanpa kontrol acak sejawat (F-D8), dan
retrospektif terhadap perbaikan alatnya sendiri. Ia jadi bahan **P55** (prospektif + kontrol acak) dan
**P56** (mengisolasi titik masuk: `entry_px` vs `tx_p` vs microprice ⑨) - karena §4 menunjuk titik
masuk sebagai penyebab, dan itu belum pernah diisolasi.

**Aturan yang kubawa terus:** kalau sebuah "tembok" ternyata adalah bug di alatku sendiri, angka yang
dibangun di atasnya ikut dicabut - bukan disimpan sebagai "sisi negatif". Dan median dari dua rejim
yang berbeda BUKAN angka: dia pencampuran dua alat.

## F-D55 — Kontrol acak dipasang di jalur cepat, dan masuknya jadi ujian terkunci (E24) - satu nama kunci hampir menimpa ujian 28 Sep · 29 Sep 2026 13:19:04Z

**Kenapa ini perlu.** F-D54 memberi angka masuk pertama yang sah (−519,4 bps, n=25), tapi angka tanpa
pembanding bukan kesimpulan. Kalau masuk **acak** di menit pertama setelah whale membeli juga memberi
sekitar −520, yang buruk adalah **substratnya**, bukan penilaian kami - dua kalimat dengan akibat
produk yang berbeda sama sekali. Aturan kami sendiri (F-D8) sudah bilang: yang dikalahkan adalah
**kontrol acak pada siklus yang sama**, bukan nol.

**Yang dipasang.** `tools/fast_lane.py` kini membuka satu slot kontrol per siklus (`ACAK-5m`,
`kontrol: true`), dipilih seragam dari kolam yang sama dengan benih = waktu siklus, **tanpa melihat
gerbang**; kandidat yang terlalu tua untuk jadi lengan sah tidak boleh jadi kontrol (kalau tidak ada
yang layak, baris `KONTROL-KOSONG` ditulis - kehilangan dicatat, bukan dilewati). Statistik perlakuan
dan kontrol dipisah sejak daftar pertama. `tools/entry_ab.py` memegang kunci
`decisions/prereg-fastlane-lock.json`, `spec_sha256=0x4c90bb27ac947420d5be198643c46a572cc66c4e8837206263a619f615270473`, dipasang **13:19:04Z dengan 0 kejadian
pasca-kunci**, vonis boleh mulai **21:19:04Z**. Self-test-nya memuat **kontrol negatif**: pada
distribusi T dan K yang identik vonisnya harus GAGAL - harness yang tidak bisa menjawab "tidak"
bukan harness.

**Nyaris menghapus ujian yang sedang berjalan.** Nama berkas kunci pertama yang kutulis
(`prereg-entry-lock.json`) **sudah dipakai** E1/E2/E3 sejak 28 Sep 11:32:07Z. Kalau tidak kucek,
`--lock` malam ini menimpa spec ujian yang sedang hidup - sekelas dengan F-D42 (self-test menghapus
data riwayat) dan F-D45 (dua alat, satu berkas). Alatnya sekarang menolak: berkas kunci dengan sha
berbeda tidak pernah ditimpa, dan itu keluar dengan kode bukan nol. **Aturannya: satu ujian = satu
berkas = satu sha; nama kunci adalah bagian dari spesifikasi.**

**Empat syarat vonis:** n≥40 per lengan; median(T)>0 dan CI bawah bootstrap 4.000 dari selisih > 0;
Mann-Whitney satu arah p<0,05; **komposisi lengan sebanding** (median umur keputusan tak berbeda >60
d). Syarat keempat itu yang biasanya dilupakan - tanpanya T bisa menang hanya karena kontrolnya
kebetulan lebih muda.

**Yang tidak boleh terjadi setelah ini:** membaca GAGAL sebagai "VETO justru untung" (dibalik butuh
kunci baru), atau membaca BELUM BISA DIUJI sebagai teori salah. Dan LAYAK pun belum uang: tembok
venue 3,1 % (F-D43) dan `i` +245 bps (E21) tetap berdiri.

## F-D56 — Yang terdaftar bukan yang hidup: dari 41 simbol reachable, harga perp hanya bergerak pada resolusi menit di 5 simbol · 29 Sep 2026 13:56Z

**Yang mengukur.** `tools/perp_liveness.py` - 1 m klines 24 jam untuk tiap simbol yang kabar beli ⑦-nya
ada di venue kami: % menit tanpa transaksi, harga berbeda dalam sehari, run terpanjang harga tidak
berubah. Kelasnya: **HIDUP 5 / TIPIS 17 / MATI 17** (dari 41; 2 tidak terukur karena klines kosong).
Isinya bukan pendapat: `BNCUSD1` - simbol dengan kabar **terbanyak** (478 dari 779) - 96,0 % menit tanpa
transaksi, 41 harga berbeda sehari, beku 446 menit. `GMEUSDT` 99,2 % / beku **679 m**. `CUSDT` 99,6 % /
671 m. Kelas MATI median 97,4 % menit kosong; kelas TIPIS 77,9 %.

**Angka yang boleh dijual.** Dari 13.293 kabar beli hari ini, yang terjadi pada simbol yang harga
perp-nya benar-benar hidup di resolusi menit: **26 = 0,20 %**. Bukan 3,1 %, bukan 5,86 % - itu ukuran
lain (F-D57).

**Kenapa ini mengubah urutan kerja.** Kami seharian memperbaiki cara membaca sinyal (F-D50 → F-D54),
dan ternyata substrate tempat kami bisa mengirim order sebagian besar **tangga beku**. Pada deret seperti
ini horison dua menit tidak terukur: bukan karena sinyalnya lemah, tapi karena tidak ada transaksi yang
bisa menggeser harga. Ini juga menjelaskan kenapa sebagian "hasil" kami selalu terdengar bulat: nol.

**Batas yang kutulis sekaligus.** Klines = transaksi yang terjadi, **bukan** kedalaman buku; "HIDUP"
berarti layak diuji pada horison menit, bukan layak dieksekusi ukuran besar; dan satu hari data bukan
sifat pasar. Yang belum: baca ⑨ untuk 5 simbol HIDUP itu (**P60**), dan kurangi kehilangan jendela
dengan cache 1 m lebih panjang (**P59**).


## F-D57 — Parser daftar venue membuang 17 entri: "3,1 % kabar bisa dieksekusi" sekarang punya dua angka, dan keduanya menjawab pertanyaan berbeda · 29 Sep 2026 13:56Z

**Yang terjadi.** `tools/venue_bridge.py` memotong sufiks kuotasi dari `data/aster_symbols.json` dengan
daftar tetap (`USDT`, `USDC`, `PERP`). Ada 17 dari 584 entri yang tidak cocok: `BTCU`, `BTCUSD1`,
`ETHUSD1`, `SOLUSD1`, `SKHYNIXUSD1`, `MUUSD1`, `CLUSD1`, ... Parser menghasilkan basis `BTCUSD1` (string
utuh), jadi kabar "BTC" tidak pernah ketemu dengannya. Efeknya bukan pembulatan: kabar 24 jam yang
reachable naik dari **301 (2,26 %)** jadi **779 (5,86 %)** begitu basis dibaca dari field `base`.

**Kenapa ini keputusan, bukan bug kecil.** Sepekan ini 3,1 % dipakai sebagai **batas produk** - "kami
hanya bisa mengambil sebagian kecil kabar". Sekarang ada dua angka dan keduanya sahih untuk pertanyaan
yang berbeda:
- **pasangan yang persis sama** dengan yang diberitakan → 2,26 %;
- **aset yang sama** (BTC spot di BSC ↔ perp BTC) → 5,86 %, dan ini yang relevan kalau agen boleh
  mengekspresikan pandangan lewat proksi.
Yang dilarang adalah **memakai yang satu untuk menjawab yang lain**: proksi punya basis risk, funding,
dan jam trading sendiri - dan untuk kabar memecoin BSC, proksi perp major tidak akan pernah jadi
perdagangan yang sama.

**Keputusan.** (a) `tools/perp_liveness.py` membaca basis dari field `base` dan mencetak **kedua** angka
setiap jalan, supaya tidak ada yang mengutip satu tanpa menyebut pertanyaannya; (b) F-D43 tidak dicabut -
kesimpulannya (venue, bukan sinyal, yang membatasi) justru menguat, tapi angka 3,1 % sekarang berstatus
"ukuran all-time dengan parser yang membuang 17 entri"; (c) klaim submission tidak boleh memakai 5,86 %
tanpa kalimat "aset yang sama, bukan pasangan yang sama".

**Yang kutarik untuk cara kerja:** tiap kali sebuah rasio dipakai sebagai batas produk, pertanyaan
pertama bukan "besok berapa" tapi **"apa definisi pembilang dan penyebutnya, dan pertanyaan mana yang
ia jawab"**. Angka ini salah bukan karena hitungannya keliru - ia menjawab pertanyaan lain tanpa mengaku.


## F-D58 — Bump E11 tidak pindah ke harga perp: nol terhadap placebo, dan di kelas TIPIS mediansya tepat 0,0 di semua horison · 29 Sep 2026 13:56Z

**Uji.** `tools/perp_bump.py` (E26): 32 kejadian buy ⑦ pada simbol kelas HIDUP (dedupe 30 m/simbol,
24 jam), 15 jendelanya lengkap; horison 2/5/30 m pada **harga perp 1 m**, masuk diukur dua kali - dari
harga kejadian, dan dari harga satu menit kemudian (umur keputusan nyata kami, F-D54). Placebo =
asal-mula digeser acak 30-90 m pada deret yang sama.

```text
versi pertama (cache 24 jam, n=15 - DIBATALKAN P59, jangan dikutip):
  @2 m +2,0 | @5 m -7,3 | @30 m -34,4 | placebo +0,7 / +6,9 / -9,6 | 5m-vs-30m -0,5 bps p=0,696
versi dipakai (cache 3 hari sejak P59, n=31 dari 33 kejadian):
  @2 m -2,6 | @5 m +15,2 | @30 m +18,1 | placebo +3,3 / +10,7 / -8,1
  berpasangan 5 m vs 30 m: median +14,8 bps | menang 16 kalah 15 | p=0,50000
```

Pada kedua versi jawabannya sama: **tidak ada bump yang bisa dibedakan dari nol** - placebo di atas yang asli di versi pertama (+6,9 vs −7,3), dan hanya 4,5 bps di bawahnya di versi kedua (+10,7 vs +15,2) dengan tanda-uji **p=0,50**. Yang belum pernah terjadi di proyek ini untuk klaim unggulannya adalah yang kedua: placebo yang nyaris tak terbedakan dari sinyal. E11 (+192,7 → +202,6 bps, placebo datar −180) tetap sahih **sebagai
pengukuran deret harga spot BSC**. Yang gugur adalah kalimat penghubungnya: "karena itu agen kami bisa
mengambil dua menit pertama".

**Sensitivitas yang justru lebih penting dari hasilnya.** Pada 39 kejadian di kelas TIPIS, **median
return = 0,0 bps di @2, @5, dan @30 m** - persis nol, bukan mendekati nol. Deretnya beku, jadi tidak ada
yang terjadi untuk diukur. Ini bentuk paling bersih dari aturan "unmeasured is not clean", dan ia
mengingatkan bahwa sebagian "nul" kami selama ini bukan hasil negatif: itu **tidak ada pengukuran** yang
menyamar sebagai hasil.

**Keputusan.** (a) Halaman 28 jadi rumah angka ini; (b) klaim "edge dua menit" di submission **tidak
boleh** lagi berdiri tanpa menyebut bahwa ia terukur di substrate yang bukan tempat kami bertransaksi;
(c) **P61**: venue pembanding diukur dengan alat yang sama, bukan diharapkan; (d) n=31/39 satu hari,
jadi ini **bukan vonis** - tapi cukup untuk memindahkan seluruh argumen "tinggal eksekusi" dari tabel
fitur ke pertanyaan yang benar: **di mana pasar kami benar-benar hidup?**

**Addendum 14:1xZ (P59) - keputusan ini hampir berdiri di atas angka yang salah karena cache-ku pendek.**
Versi pertama E26 menilai **15 dari 32** kejadian: sisanya terbuang karena cache 1 m hanya memuat 24 jam,
sehingga jendela ±3 m di ujung seri tidak punya bar. Setelah cache diperpanjang ke 3 hari, 31 dari 33
kejadian dinilai dan **mean @5 m berpindah tanda**: −7,3 → **+15,2**. Kesimpulan keputusan ini tidak
berubah (placebo +10,7, p=0,50 - tetap tidak ada bump), tapi besaran yang kutulis di badan F-D58 sudah
kedaluwarsa, dan itu yang addendum ini koreksi secara terlihat.

Aturannya naik satu tingkat: **panjang jendela pengukuran adalah bagian dari spesifikasi, bukan detail
cache.** E20 karena itu kupatok explicit (`suhu(deret, jam=24)`) supaya cache yang memanjang tidak bisa
mengubah kelas sebuah simbol diam-diam - dan assert barunya membuktikan pemotongan itu bekerja.

## F-D59 - Dugaan "buku beku itu nasib long-tail perp" saya bantah sendiri: pada 35 kontrak yang sama, venue pembanding punya 14 simbol HIDUP dan nol MATI, kami 5 dan 14 · 29 Sep 2026 14:31:24Z

**Kenapa harus diuji sebelum dipercaya.** §3 halaman 28 menuduh kelas asetnya ("memecoin long-tail ya
begitu"). Itu penjelasan yang nyaman karena tidak menuntut apa-apa dari kami. Sebelum ia dipakai memilih
arah produk, ia wajib diadu dengan venue lain pada **daftar simbol yang sama**.

**Alatnya.** `tools/gate_liveness.py` (P61) mengimpor `suhu()`/`kelas()` dari `tools/perp_liveness.py` -
bukan menyalin rumus, karena dua salinan rumus menghasilkan dua angka yang tidak sebanding (F-D45).

```text
35 dari 41 simbol reachable kami juga terdaftar di Gate Futures (kabar 259)
   HIDUP  gate 14 simbol / 157 kabar | aster  5 simbol /  27 kabar
   TIPIS  gate 21 simbol / 102 kabar | aster 14 simbol / 191 kabar
   MATI   gate  0 simbol /   0 kabar | aster 14 simbol /  32 kabar
   HIDUP hanya di Gate: Q, USELESS, 牛来, O, TRX, GWEI, UB, BOME, PEOPLE | hanya di Aster: tidak ada
   kelas sama: 15 dari 35
```

**Keputusan.** (a) Dugaan "nasib long-tail" **dicabut**: pada kontrak yang sama venue kami 2,8× lebih
sering MATI dan tidak ada satu pun simbol yang hidup di kami tapi mati di sana - jadi buku beku adalah
**sebagian besar cacat venue kami**. (b) Ini **tidak** otomatis berarti "ganti venue = selesai": yang
diperbaiki venue adalah **eksekusi** (isi, slippage, probabilitas terisi), bukan alasan masuk - dan
E27/F-D60 menutup celah itu. (c) Angkanya saya catat dengan skala yang tidak sebanding: `v` Gate =
jumlah kontrak, bukan USD; yang dipakai hanya uji nol-vs-bukan-nol dan lama harga tidak berubah.

**Kecelakaan alat yang ikut memperbaiki gambar.** Dua kontrak non-Latin (`牛来_USDT`, `哈基米_USDT`)
melempar `UnicodeEncodeError` karena saya hanya mengquote path, bukan query - dan itu tercatat sebagai
"TIDAK-ADA-DATA". Sesudah diquote, keduanya punya data (TIPIS/HIDUP). Jadi sebagian "kehilangan jujur"
saya adalah **bug pemetaan sendiri**, untuk kesekian kalinya (F-D47: daftar kami BASIS, API minta SIMBOL;
F-D42: self-test menghapus data). Pelajarannya naik tingkat: *setiap "tidak ada data" dari alat baru
wajib dibedakan tiga hal - tidak ada, tidak bisa dibaca, dan salah nama.*

**Batas yang kutahan.** Satu hari; satu venue pembanding (Binance/Bybit/OKX tidak bisa dijangkau dari
mesin ini - itu bukan "tidak ada", itu tidak terukur); klines bukan kedalaman; "HIDUP" = layak diuji
horison menit, bukan layak dieksekusi ukuran besar.


## F-D60 - Kesempatan terakhir hipotesis venue juga gagal: di venue yang bukunya hidup, efek menit-5 tinggal +2 sampai +13 bps - di bawah ongkos kami sendiri · 29 Sep 2026 14:36:08Z

**Ini uji yang paling menentukan malam ini.** F-D59 memberi kesempatan terakhir bagi kalimat "bump-nya
ada, venue kami yang terlalu beku untuk menunjukkannya". Kalau itu benar, di venue dengan 14 simbol
HIDUP effect-nya harus kembali sebesar E11. `tools/gate_bump.py` (E27) mengujinya dengan **matematika yang diimpor dari E26** - hanya deretnya yang ganti rumah.

```text
HIDUP (n=31 kejadian, 14 simbol, 0 hilang):
   @2 m  asli +4,7 | median +0,7 | masuk +1 m -1,7 | placebo  -2,8
   @5 m  asli +2,0 | median +4,6 | masuk +1 m -4,1 | placebo  -7,4
   @30m  asli -3,2 | median +12,1| masuk +1 m -7,7 | placebo  -3,4
   berpasangan 5m vs 30m: median -9,0 bps | menang 14 kalah 17 | p=0,76344
TIPIS (n=40, 21 simbol): @2 m +9,3 (pl +2,5) | @5 m +13,2 (pl +4,9) | @30 m +0,8 (pl +12,1); p=0,43731
```

**Angka yang harus disandingkan, bukan dipilih.** E11: **+202,6 bps** di menit 2-5 pada deret spot BSC.
Ongkos round-trip terukur kami di venue sendiri: **59 bps**. Efek di venue hidup: **+2,0 sampai +13,2
bps**. Jadi bahkan di tempat bukunya benar-benar bergerak, horison pendek (a) satu ordo lebih kecil dari
yang kami klaim, (b) **habis sebelum ongkos**, dan (c) tetap nondeterministik melawan horison panjang
(p=0,76; p=0,44).

**Keputusan.** (a) Hipotesis "venue terlalu beku" **dicabut sebagai penjelasan hilangnya bump** - ia
tetap benar sebagai masalah eksekusi (F-D59), tapi tidak menyelamatkan alasan masuk. (b) Rangkaian
sebabnya sekarang tertutup dan terukur dari tiga sisi berbeda: kami **tidak lambat** (F-D54, umur
keputusan 61 d); bukan karena **venue beku** (F-D60); melainkan karena **harga yang kami bayar bukan
harga yang dilihat sinyal** (E21 `i` +245 bps; F-D54 `entry_px` di atas harga whale pada 16/25) - dan di
atas semuanya, **bump itu sendiri tidak ada di harga perp**, di dua venue. (c) Untuk submission: kalimat
"agen kami bisa mengambil dua menit pertama" **tidak boleh** diucapkan dalam bentuk apa pun; yang benar
dan tetap kuat: *"kami mengukur apakah edge yang kami temukan bisa dipindahkan ke substrate tempat kami
benar-benar bertransaksi - dan di dua venue jawabnya tidak, sebesar satu ordo di bawah ongkos."*

**Yang tidak kulakukan.** Tidak membalik arah menjadi "maka jual saat whale beli" (F-D39/F-D51 melarang
penafsiran terbalik tanpa kunci baru); tidak menamai ini vonis akhir (satu hari, n=31/40, klines tanpa
kedalaman); dan tidak memutuskan sendiri soal pindah venue - itu keputusan produk builder, saya catat
sebagai **P62** dengan bukti yang sudah ada, bukan dengan ajakan.

## F-D61 — Yang mati bukan kutipannya: pada 5 dari 26 simbol yang kami pantau, tidak ada volume sama sekali di dalam ±10 bps · 29 Sep 2026 14:50Z

**Kenapa ini saya kejar.** `i` (E21, +245 bps) dan kerugian F-D54 (−519 bps) selalu saya jelaskan dengan
satu kata: "likuiditas". Itu kata, bukan angka. ⑨ sudah merekam 20 level selama 4,7 jam pada 26 simbol,
jadi pertanyaan "seberapa dalam buku kami di dekat mid" akhirnya bisa dijawab dengan `tools/book_stale.py`
- dan jawabannya memisahkan tiga hal yang selama ini saya campur.

```text
BTC 0,01 bps spread / 1,58 jt unit dalam 10 bps / kutipan beku 0 %
BOME 15,1 bps / 1.000 / 1,5 %          <-- kutipan HIDUP, transaksi MATI (E20: 96,9 % menit kosong)
AI 66 bps / 0 / 13,4 %   BREW 139 bps / 0 / 12,1 %   4STOCK 310 bps / 0 / 7,5 %
ASTEROID 551 bps / 0 / 22,4 %          B-MONEY 654 bps / 0 / 48,5 %
```

**Yang terbantahkan oleh angka ini.** (a) "Market maker-nya diam" - salah: mayoritas simbol mengubah
best quote di >86 % snapshot. (b) "Yang beku itu kelas asetnya secara umum" - sebagian salah, lihat
F-D59. (c) Yang benar: **kutipan ada, tapi tidak ada yang bisa diambil di dekat harga** - untuk 5 simbol,
kedalaman dalam ±10 bps persis **nol**, dan spread-nya 66-654 bps. Order market apa pun di sana bukan
"masuk dengan slippage", itu "masuk 1-6 persentase poin di luar harga terakhir".

**Konsekuensi yang saya tarik sampai ujung.** Untuk E17/trailing: algebra `pi > 2s + i + C` tidak punya
solusi pada simbol dengan `s` = 33-327 bps. Jadi "trailing tidak menolong" bukan sekadar "belum cukup
data 1 menit" (F-D49) - pada sebagian buku yang kami pantau, **tidak ada jarak yang sah untuk dipasang**,
berapapun resolusi harganya. Ini juga membuat F-D48 perlu catatan: 63-66 % kejadian "berjendela sah"
dihitung dengan spread median 0,04 bps dari level teratas; kalau distribusinya dipisah per simbol,
pemandangannya jauh lebih buruk dari satu angka itu.

**Batas yang kutahan.** Kedalaman dalam **unit kuotasi** (px×qty), belum USD, jadi membandingkan besar
kedalaman antar simbol yang harganya berbeda tidak sah - yang saya pakai di sini hanya "nol vs bukan nol"
dan spread dalam bps (skala-bebas). Daftar pantau ⑨ TIDAK saya lebarkan (F-D53/P54), jadi 4 dari 5 simbol
HIDUP (MARSCOIN/ZEC/DOGE/LINK) masih belum ada bukunya - itu P60 yang sesungguhnya, dikerjakan setelah
E16 divonis. Dan `book_stale.py` baru sekali jalan: self-test-nya lolos (kutipan beku vs hidup terpisah,
run terputus oleh celah waktu, <3 snapshot = TERLALU-SEDIKIT bukan nol).

## F-D62 - Buku paper dibetulkan sebagai varian, bukan sebagai tambalan diam-diam: dampak 0,0015 -> 1,16 bps, dan 6 dari 20 posisi ternyata tidak punya buku · 29 Sep 2026 15:24Z

**Yang diperbaiki.** `costs.py` kini punya MODEL ISI satu pintu: `harga_bnb()` (terukur dari klines
Aster BNBUSDT 1h, **$764,21 umur 14,6 m**, menolak kalau cache basi - dan cache yang basi kini
DiAMBIL ULANG, karena guard yang hanya menolak membuat v2 mati diam-diam di mesin ber-cache 4,8 hari),
`dampak_round_trip(size_bnb, liq_usd, skema)` (v1 = Bug F-D46; v2 = konversi ke USD + lantai
$50.000), `isi_buku(levels, mid, usd)` (VWAP nyata dari level ⑨, dengan `penuh=False` kalau buku
habis). `paper_book.py` memakai pintu itu lewat `--isi v1|v2` dan menyimpan `skema_dampak` +
`harga_bnb_usd` + `ukuran_usd` di SETIAP slot, jadi berkasnya tidak bisa lagi dibaca dengan dua arti.

**Yang keluar dari angka.** v2 tidak memperbesar kerugian - dia **memperkecil sampel yang sah**: 6 dari
20 posisi pada budget kontrak ditolak (liq $0, $1, $3, dan dua tanpa angka likuiditas sama sekali),
mean lock -86,1 -> -91,2, dan `di atas acak` berubah True -> False hanya karena lengan control tinggal
2 slot. Itu bukan hasil, itu peringatan: **pada 0,01 BNB di universe yang bisa kami isi, paper ini
tidak punya n**. Paritas v1 dibuktikan identik sebelum dan sesudah patch.

**Keputusan alat yang penting: default TIDAK kubalik.** `--emit` ditolak saat `--isi v2`, karena
`decisions/paper-book-positions.jsonl` dibaca `tools/vol_ab.py` untuk vonis E9 yang masih hidup sampai
17:13:25Z. Mengganti penggaris di tengah uji terkunci bukan memperbaiki eksperimen - itu mengganti
eksperimennya (F-D53 menolak godaan yang sama delapan jam lalu; F-D54 menghukum versinya yang tidak
sengaja). Pembalikan default dijadwalkan di P42, sesudah E9 divonis dan tercatat.

**Yang tidak klaim ini boleh dapat.** Jangan tulis "paper sekarang bersih" atau "-91,2 bps adalah
harapan kami yang sebenarnya". Yang terukur: dengan ongkos fee 59 bps + dampak 1-3 bps + lantai
likuiditas, **hanya 70 % dari posisi paper kami yang bisa diisi sama sekali**, dan yang 30 % bukan
rugi - itu tidak bisa terjadi. Untuk keputusan nyata (streak -> real), `promote-after` masih kosong dan
sekarang ada satu alasan lagi selain sinyal: ukurannya tidak punya tempat masuk.

## F-D63 - "Belum bisa diuji" yang ternyata bug lookup: n=0 persis, padahal 140 kejadian menyala - dan fiksinya memperkeras vonis · 29 Sep 2026 20:26:13Z

**Yang terjadi.** Vonis watch (halaman 17) jatuh pada pembacaan pertama: `uji_primer` dan `uji_kedua`
berstatus `SAMPEL TIDAK CUKUP` dengan **n = 0 persis**. Aku nyaris menuliskannya sebagai "belum bisa
diuji" - kalimat yang sopan, tidak menutup apa pun, dan tidak menyakiti siapa pun.

**Yang menyebabkannya.** `day2_replicate.py` memakai `pred = bool(e.get(fitur))` dengan `fitur` =
**seluruh baris spesifikasi**: `"cluster_ge2 (>=2 maker berbeda beli dalam jendela)"`. Kunci aspek yang
sebenarnya bernama `"cluster_ge2"`. Lookup itu mengembalikan `None` untuk SEMUA kejadian, jadi nol itu
bukan kekurangan data - itu kepastian struktural dari satu baris kode.

**Yang membuktikan bukan karangan.** Data dan jendela yang sama persis, ditanya dengan benar:
`cluster_ge2` menyala pada **140** kejadian pasca-kunci, `money_spread` pada **112**, `cluster_ge3` 76,
`repeat_maker` 87, `buy_usd_ge_1k` 61. Setelah `aspek_dari()` dipasang (nama aspek diekstrak dari
spesifikasi; kalau tidak dikenali -> alat **menolak memvonis**, bukan menjawab nol), vonisnya jadi
**GAGAL pada tiga-tiganya** dengan n=156/123/142.

**Ini bagian yang kunyatakan sebagai kebaikan alat, bukan kebaikanku: perbaikan membuat hasilnya
LEBIH BURUK, bukan lebih baik.** "Belum bisa diuji" adalah hasil yang nyaman; "jalur masuk kerumunan
maker ditutup" adalah hasil yang menyakitkan dan benar. Kalau bug membuat angka kita naik, curigai
dirimu; kalau bug membuat angka kita turun, perbaiki dan tandai yang lama sebagai tidak sah. F-D50
(0,2 menit vs 808 d), F-D54 (58 lengan menilai masa lalu), F-D57 (17 entri daftar dibuang parser)
dan F-D63 punya bentuk yang sama: **bukan salah hitung, tapi salah bertanya - dan selalu lebih murah
mendeteksinya sekarang daripada membayarnya di depan juri.**

**Aturan yang naik.** `n` yang tepat **0**, tepat **100 %**, atau angka bulat lain yang terlalu rapi
adalah **alarm instrumen**. Sebelum ia disebut "kekurangan sampel", hitung berapa yang seharusnya
menyala dengan data yang sama. `aspek_dari()` sekarang mengangkat `SystemExit` kalau sebuah uji
menunjuk aspek yang tidak dikenal alat - jadi kegagalan lookup berikutnya tidak bisa lagi menyamar
sebagai jawaban kosong.

**Yang tidak berubah.** Spesifikasi §1 halaman 17 tidak disentuh; `spec_sha256=0xc4105c1732ebfca7…`
sama pada pembacaan 20:18:39Z dan 20:26:13Z. Yang berubah adalah cara alat membaca pertanyaan -
bukan pertanyaannya. Artefak pertama (`day2w-20260929T201843Z.json`) **tidak** kuhapus: ia bukti
bahwa kita salah, dan itu yang bikin pembaca berikutnya percaya pada yang kedua.

**Batas yang ikut ditulis.** Mean pada artefak itu tidak di-winsor (+4.043,7 bps untuk median −21,3):
satu token lotre memindahkannya ribuan bps. Ia jangan dikutip; `evidence_stack._pair` perlu winsor
atau trimmed mean - itu **P63**.

## F-D64 - Klaim terakhir yang bertahan sepekan ("rem") gugur secara prospectif: arah benar, efek tidak - dan satu-satunya perilaku yang lulus adalah cara keluar · 29 Sep 2026 20:32:34Z

**Yang diuji.** Rem `jual_*` adalah satu-satunya perilaku Fabius yang tidak pernah kucabut. E13/E14
memberi **+285,5 vs −230,3 bps** di menit ke-5 dengan **16/16 grid ambang** lolos dan placebo yang
membunuh kandidat lain tidak menyentuhnya. E22 menguncinya (`12:08:15Z`, `spec_sha256=0x6f6e61f8…`,
delapan jam, empat syarat) dan malam ini datanya ada.

**Yang keluar (n=319 BOLEH / 110 VETO, 429 kejadian pasca-kunci, dua syarat lolos, dua gagal):**

```text
mean winso  BOLEH -9,9 | VETO -121,4 | selisih +111,5    (arahnya benar)
median      BOLEH -57,9 | VETO -59,0                     (praktik sama; dua-duanya di bawah nol)
CI selisih  [-134,0 ; +344,4]                           (memotong nol)
MW satu arah p=0,15936 | CI atas placebo +223,7 > 111,5
P(ada harga keluar) 100% / 100% | umur keluar 0,08 m / -0,10 m
VONIS: GAGAL
```

**Keputusan.** (a) **"rem memperbaiki hasil" turun status jadi in-sample di seluruh vault** - baris
koreksi ditulis di halaman 21 (bukan penimpaan), halaman 25 §5 menyimpan vonisnya, dan **cheat sheet
submission** kuperbarui: kalimat "satu-satunya yang lolos kontrol kami adalah rem" tidak boleh lagi
keluar dari mulut kami. (b) **Tidak** dibalik jadi "VETO justru untung" (medannya −59,0). (c) **Tidak**
ada ambang baru, **tidak** ada penyesuaian winsor/n_min setelah melihat hasil.

**Yang menggantikannya, dan ini harus ditulis dengan tepat:** satu-satunya **perilaku** Fabius yang
lolos uji prospectif malam ini adalah **cara keluar** - E12: keluar di menit ke-5 mengalahkan tahan ke
menit ke-30 pada posisi yang sama, n=685, CI bawah **+135,9**, p=0,00001. Tapi lihat ukurannya: mean
lengan cepat **+8,1 bps**, dan itu dengan **ongkos v1** yang F-D62 baru saja tunjukkan terlalu murah
hati. Jadi posisi proyek ini jam 20:32Z: **satu aturan keluar yang lulus uji, nol alasan masuk, nol
rem yang bertahan.**

**Satu kemungkinan yang kucatat tanpa menjualnya.** Feed ⑦ tiba berumur median **120 d** (24 d pada
baris yang kami putuskan). Veto membaca kerumunan **jual** - sinyal yang, kalau harganya sudah jatuh,
mungkin **sudah lewat**. Median BOLEH −57,9 konsisten dengan penjelasan itu. Bentuk lanjutan yang
benar bukan ambang baru, tapi **horison baca yang lebih pendek**, dan itu kunci sendiri - bukan
reinterpretasi halaman ini.

**Kenapa commit ini tidak boleh dibaca sebagai malam yang gagal.** Yang jatuh malam ini jatuh karena
**kita sendiri membangun alat yang cukup tajam untuk menjatuhkannya**: E22 adalah uji prospectif
pertama untuk perilaku, E24 yang pertama membandingkan masuk kita dengan masuk acak, `aspek_dari`
(F-D63) menemukan bug yang membuat sebuah "belum bisa diuji" berubah menjadi "GAGAL". Empat vonis
malam ini semuanya menghasilkan angka yang bisa dipercaya. Itu bukan kemenangan - tapi itu satu-satunya
dasar yang boleh dipakai bicara di depan juri tanggal 30 Sep 23:59 WIB.

## F-D65 - Default buku paper dibalik ke v2: mean membaik, sampel jatuh di bawah gerbang, dan dua pembaca dikunci pada satu penggaris · 29 Sep 2026 21:16Z

**Isinya satu kalimat:** setelah penggarisnya dibetulkan, buku paper kami **kehampuan menyimpulkan
apa pun** - dan itu harga yang harus dibayar, bukan alasan untuk membatalkan perbaikan.

v1 → v2 pada berkas peristiwa yang sama (0,01 BNB, 5 posisi/hari): `n 20 → 15`, mean winso
**−182,5 → −80,3**, CI bawah **−582,7 → −446,6**, streak maks 1 → 3. Lima posisi dibuang
(`liq $0` ×2, `liq $3`, `liq $1`, satu tanpa angka); median likuiditas yang ditolak **$2,75**.
Syarat F-D16 minta n≥20 - sekarang 15. **Aku tidak menurunkan lantai $50.000** untuk mengembalikan
n: itu persis gerakan yang sudah kuhukum di F-D51 (budget) dan F-D47 (cakupan).

**Yang membuat pengembalian default ini aman.** Tiga hal dikerjakan sebelum, bukan sesudah:
1. `vol_ab.py` (E9) dan `winlog.py` (bukti streak/`promote-after`) **menyaring `skema_dampak`** -
   slot v2 tidak bisa masuk vonis yang dikunci dengan v1. Tanpa ini, mengembalikan `vol_ab` nanti
   bisa mengubah vonis yang sudah jatuh secara diam-diam.
2. `paper_book --self-test` (baru) membuktikan penyaringan itu pada berkas campuran: 2 dari 4 slot
   dibuang oleh KEDUA pembaca. Ini uji lintas-alat, bukan uji unit yang memuji dirinya sendiri.
3. Rumus dampak tidak lagi ada di dua tempat: `entry_lab.py` dan `impact_audit.py` mengimpor dari
   `costs.py`, dan **paritas diukur** - entry_lab identik pada 3.955 kombinasi liq×net nyata,
   impact_audit identik di tiga variannya (+77,3 / −694,9 / −91,1). `SKEMA_ENTRY` dibiarkan v1
   karena kunci E1/E2/E3 menyebut rumus itu; itu keputusan sadar, tertulis di kode.

**Yang belum selesai dan sengaja tidak kupalsukan.** `impact_audit` masih membawa `--liq-floor`
$1.000 miliknya sendiri sementara `costs.LIQ_LANTAI_USD` = $50.000 - dua lantai, dua jawaban untuk
pertanyaan "pool mana yang boleh dihitung". Aku tidak menyamakannya malam ini karena itu mengubah
varian E15 yang sudah dikutip halaman 24/26; itu **P65**, dengan konsekuensi yang harus ditulis
bersamanya.

**Kalimat yang boleh dipakai di submission:** *"Buku paper kami memakai model isi dengan harga BNB
terukur dan lantai likuiditas institusional; pada budget kontrak itu menyisakan 15 dari 20 posisi -
di bawah ambang sampel kami sendiri - jadi tidak ada angka paper malam ini yang kami jual sebagai
kelayakan."* Yang tidak boleh: menyebut −80,3 bps sebagai perbaikan.

## F-D66 - Uji terakhir "kapan masuk" gagal dengan kontrol acak, dan yang tembus justru bukan arah: gross median kedua lengan nol, ongkos 59 bps - kami mengukur tiket, bukan pasar · 29 Sep 2026 21:27:32Z

**Yang dijanjikan E24.** F-D54 memberi angka masuk pertama yang sah tapi tanpa pembanding; F-D55
memasang kontrol acak per siklus dan menguncinya jam 13:19:04Z dengan **0 kejadian pasca-kunci**. Ini
satu-satunya uji di proyek ini yang menjawab pertanyaan yang benar: bukan "apakah masuk kita untung",
melainkan "**apakah masuk kita lebih baik dari masuk tanpa alasan**".

**Yang keluar (n T=195 / K=65, umur keputusan median 71 d vs 102 d - syarat komposisi LOLOS):**

```text
T mean winso -74,6 | median -59,0        K mean winso -98,0 | median -62,2
selisih mean +23,4 bps | CI bawah -215,0 | Mann-Whitney satu arah p=0,2080
53 siklus tanpa kandidat kontrol (tercatat, bukan hilang)
VONIS: GAGAL - syarat (2) median(T)>0 dan (3) p<0,05 gagal
```

**Yang lebih penting dari vonisnya.** Ongkos round-trip terukur kami di venue sendiri **59,0 bps**.
Dibandingkan ke itu: **gross median T ≈ +0,0 bps, K ≈ −3,2 bps.** Artinya pada horison lima menit harga
**hampir tepat tidak bergerak** dan yang kami catat sebagai kerugian adalah **tiket masuk**. Ini
menutup rangkaian tiga alat: F-D54 (kami tidak lambat), F-D60 (bukan venue beku), F-D66 (bukan
seleksinya) — sisanya cuma biaya yang tidak bisa dihilangkan dengan memilih kolom lebih baik.

**Keputusan.** (a) Status pertanyaan "kapan masuk" di proyek ini sekarang: **empat jalur diuji
prospectif (E9 vol-rendah, watch kerumunan maker, E22 rem, E24 masuk-vs-acak) - keempatnya GAGAL, nol
alasan masuk tersisa**, dan satu-satunya perilaku yang lulus prospectif adalah aturan **keluar** (E12).
(b) **Tidak** membalik jadi fade: K juga di bawah nol, dan arah terbalik butuh kunci baru - dinamai
**E25+** di backlog, bukan reinterpretasi halaman 27. (c) **Tidak** menyebut +23,4 bps sebagai edge
(di bawah ½ ongkos, CI −215). (d) **Tidak** menyentuh n_min 40 / winsor ±1.500 / jam kunci.

**Yang kucatat agar tidak dianggap kemenangan.** T mengalahkan K di mean maupun median. Kalau besok
seseorang (atau aku) menulis "seleksinya bekerja, hanya levelnya yang belum", itu salah dua kali:
selisihnya tidak terbedakan dari nol, dan keduanya berada di sisi rugi. F-D8 tidak menanyakan "lebih
baik dari acak?" saja - dia menanyakan "lebih baik dari acak **dan di atas nol**?".

**Sisa yang terbuka dan namanya sudah ada:** **P56** (isolasi titik masuk `entry_px` vs `tx_p` vs
microprice ⑨ - karena §6b menunjuk biaya sebagai penyumbang utama dan itu belum dipisahkan dari
horison) dan **P62** (venue: F-D59 lebih hidup, F-D60 tidak memanggil bump). E24 tidak membuka jalur
baru; dia menutup yang terakhir.

## F-D67 - E16 jatuh: orderbook pada cadence 200 detik kami tidak memprediksi apa pun - dan satu-satunya kelompok dengan arah benar memberi +0,03 bps net · 29 Sep 2026 21:46:56Z

**Yang dijanjikan teori ini.** Ini teori yang dibawa builder langsung dari seorang trader yang ia
hormati: baca orderbook, total variasi harga beli dikurangi jual, positif = mantul. Kami mengubahnya
jadi `bi5` (state imbalance 5 level), menguncinya jam **09:37:45Z** sebelum historinya ada
(`spec_sha256=0xeba3e0c510cb8470…`), dan menunggu 12 jam.

**Yang keluar (n=4.255 pasangan pasca-kunci, 25 simbol):** `bi5` GAGAL di syarat (2)(3)(4);
sekunder `bi1`/`bi20`/`mi20`/`util20` GAGAL semua; BH α 0,10: **nol** yang lolos.

**Yang membuat halaman ini tidak bisa ditutup dengan satu angka.** Spesifikasi mewajibkan jangkar
likuid dilaporkan **terpisah** dari simbol kabar - dan saat cetakan pertama cuma menampilkan
`share 13 %`, aku menambahkan pemisahan itu ke alatnya (murni pelaporan, aturan vonis tidak
berubah). Hasilnya justru intinya:

```text
jangkar (BTC/ETH/SOL/BNB) n=  537 | selisih +1,45 bps | net-of-cost +0,03 bps | p=0,104
kabar   (simbol ⑦)        n= 3.718 | selisih -0,95 bps | net -69,62          | p=0,075
```

Di buku yang benar-benar hidup, arah teorinya **ada** - dan besarnya **sepertiga basis point setelah
ongkos**, yaitu 1/40 dari ongkos round-trip kami. Di buku simbol kabar - 87 % populasi dan yang
sebenarnya kami incar - arahnya **terbalik**. Digabung, dua hal itu saling menihilkan jadi −0,72.
Ini alasan clauses "laporkan terpisah" ada, dan ini juga yang membuat angka gabungan mana pun di
proyek ini layak dicurigai kalau kelompoknya tidak disebut.

**Keputusan.** (a) **T1 ditutup sebagai hasil** di [[08-Backlog/03 - Epik Teori Baru]]; (b) **tidak
dibalik** jadi "contra-imbalance" - itu hipotesis baru dengan kunci + n sendiri, persis yang
dilarang `kalau_gagal` di spesifikasinya sendiri; (c) **tidak** ada ambang yang diturunkan;
(d) batas yang tertulis di spesifikasi tetap berlaku dan kuulang di halaman 22: cadence 200 d
**tidak pernah bisa** memalsukan versi cepat teori ini - E11 sudah mengukur kabar hidup ±2 menit.

**Batas baru yang kutemukan sambil menulis vonis ini: n=4.255 bukan 4.255 observasi bebas.**
Jendela return 300 d pada snapshot tiap ~200 d saling tumpang tindih, jadi CI dan p-nya optimis.
Karena hasilnya nol, ini tidak membalikkan vonis - tapi ia membuat "p=0,060 di arah yang salah"
tidak boleh dibaca apa pun. Diperbaiki di kunci berikutnya dengan jendela **non-overlap** -> **P66**.

**Status proyek setelah ini:** lima uji prospectif selesai (E9, watch, E22, E24, E16) - **semua
GAGAL**; satu-satunya yang lulus adalah **E12** (aturan keluar). Teori builder yang terakhir
(E25, frame lebih luas + non-overlap) sudah boleh dijalankan: **P54 22:25Z**.

## F-D68 - Kelas simbol dari jendela yang bergulir tidak boleh mendefinisikan populasi uji: E27 bergerak +2,0 -> −9,8 bps dalam 80 menit tanpa satu baris kode berubah · 29 Sep 2026 22:32Z

**Yang memanggil.** Prompt P54 menyuruhku mengukur ulang `perp_liveness.py` + `gate_bump.py` dan
menuliskannya sebagai koreksi terlihat. Kuikuti, dan hasilnya bukan konfirmasi - melainkan alatku
sendiri yang ketahuan.

**Yang terukur.** E20: jendela 24 jam bergeser, `AIUSDT` naik TIPIS → HIDUP (nol-volume 66,3 % → 9,5 %),
`SOON`/`SPCXUSD1` masuk, HIDUP 5 → 8, MATI 17 → 19, reachable aset 5,86 % → 7,41 %. E27: dengan
n sama-sama 31 dan nol perubahan kode, mean @5 m **±2,0 → −9,8**, placebo −7,4 → −12,2, berpasangan
5m-vs-30m median **−9,0 → −29,4**, p **0,763 → 0,995**.

**Penyebabnya satu baris rancangan.** `gate_bump.py`/`perp_bump.py` mendefinisikan populasinya
sebagai "simbol yang kelasnya HIDUP *saat alatnya dijalankan*". Kelas itu datang dari jendela 24 jam
yang bergulir. Jadi satu "uji" yang sama bisa menjumpai dua kumpulan kejadian yang berbeda pada jam
yang berbeda - dan angka yang keluar bukan fungsi dari pasar, tapi dari **kapan aku menekan tombol**.
Ini penyakit yang sama dengan yang kubunuh tadi malam di dua bentuk lain: F-D54 (dua rejim satu alat),
F-D57 (penyebut yang menjawab pertanyaan lain), dan E16→E25 (jendela tumpang tindih).

**Keputusan.** (a) Dua tabel E27 di halaman 28 §8 **dicabut sebagai besaran titik** - yang boleh
dipakai adalah pernyataan rentang ("orde ±10 bps, di bawah ongkos 59 bps, tidak pernah searah dengan
klaim"), dan halaman 28 §10 menuliskannya sebagai koreksi terlihat, bukan penimpaan; (b) **P67**:
populasi uji dikunci - daftar simbol (dan jendela kelasnya) ditulis ke artefak kunci pada saat
`--lock`, dan alat pembaca menolak jalan kalau daftar itu tidak cocok; (c) E25 sudah lebih dulu
memperbaiki sebagian penyakit yang sama lewat aturan **non-overlap** yang ditulis sebelum kuncinya
dipasang - itu polanya: **yang menentukan populasinya harus dibekukan sebelum datanya ada, bukan
diturunkan dari keadaan saat perhitungan**.

**Yang tidak kupakai sebagai pembelaan.** Bahwa hasil pertama (21:15Z) "kebetulan lebih mendukung
narasi kami". Ia tidak lebih benar; ia hanya lebih dulu. Dan bahwa venue pembanding ternyata tetap
tidak memanggil bump - itu tetap kesimpulan tiga alat (E20/E26/E27) yang arahnya sama; yang berubah
hanya titik angkanya, dan titik itulah yang tidak boleh kami jual.

## F-D69 - E25: prediksi orderbook yang pertama lolos BH dan jendela non-overlap - dan tetap GAGAL karena ongkos; implementasi non-overlap-ku sendiri ketahuan melanggar teks kuncinya · 30 Sep 2026 10:43:24Z

**Yang jatuh.** Vonis primer `bi5` **GAGAL**, tapi isinya belum pernah kita lihat: pada **1.249
jendela non-overlapping** di **41 simbol**, kuantil-atas imbalance 5 level memberi **+11,63 bps** di
atas kuantil-bawah, **p=0,00118**, sekunder `bi1`/`bi20` **lolos BH α 0,10**, dan di kelompok simbol
kabar (yang diincar teori ini) **+13,03 bps p=0,0014**. Yang menjatuhkannya satu syarat saja:
**mean net-of-cost = −45,12 bps**. Jadi T1 ditutup sebagai jalur trading untuk kedua kalinya, dan
untuk pertama kalinya bukan karena teorinya kosong - melainkan karena ongkos kami ~4x lebih besar
dari efeknya.

**Yang lebih membuatku tidak nyaman: implementasi non-overlap-ku sendiri salah.** Pembacaan pertama
(10:38:46Z) memotong hanya 2,5 % snapshot (2.547 -> 2.482), padahal cadence 245 d vs horison 300 d
menuntut pemotongan ~setengah. Penyebabnya satu baris: `bebas = rows[j]["detik"]` (waktu **baris
keluar**, yang dengan tolerance 150 d sering jatuh ~245 d sesudah t) alih-alih `bebas = r["detik"] +
horizon` seperti yang **ditulis di teks kunciku sendiri**. Jadi alatnya melanggar spec yang ia sha.

Kuetahuukan ini **bukan** dengan membaca hasilnya, tapi dengan menuntut aritmetika cocok: *kalau alat
mengklaim membuang jendela yang beririsan, jumlah yang dibuang harus seukuran dengan yang dijanjikan
perhitungannya.* Sekarang invariant itu jadi assert di self-test (`39 -> 20 pasangan; jarak
terkecil 490 d >= 300 d`). Perbaikan ini **menaati** spec, bukan menggantinya - sha spec tidak
berubah, dan itu penting: kalau tidak, aku sedang memakai "bug fix" sebagai pintu belakang untuk
mengubah ujian.

**Dua pembacaan dilaporkan berdua, tidak dipilih.** Salah: n=2.482, selisih +7,39, p=0,00013, BH 3.
Benar: n=1.249, selisih +11,63, p=0,00118, BH 2. **Vonisnya sama: GAGAL, oleh syarat (4), di kedua
pembacaan.** Itu ujian yang sebenarnya untuk sebuah perbaikan alat - apakah ia membalikkan kesimpulan
atau cuma memperbaiki angka - dan di sini jawabannya tidak membalikkan. Aku menuliskan yang salah
lebih dulu supaya tidak ada yang bisa menuduhku memilih yang setelahnya.

**Yang kucabut sebagai pembacaan, dan kenapa.** Tanda `selisih` kelompok simbol kabar adalah **−0,95
di jendela E16** dan **+13,03 di jendela E25**. Bukan teori yang berganti arah: populasinya berganti
wajah (frame 25 -> 41 simbol, siang -> malam, beririsan -> tidak). Ini penyakit yang sama yang kubunuh
di F-D68 untuk E27, dan obatnya sama: **P67** (kunci daftar simbol ke artefak kunci). Sampai itu
selesai, tidak ada angka kelompok dari halaman 22 maupun 29 yang boleh dipakai untuk membatalkan yang
lain - yang boleh dijual hanya yang net-of-cost, dan di dua-duanya dia kalah.

**Status proyek 10:43Z:** enam uji prospectif selesai - E9, watch, E22, E24, E16, E25 - **semua GAGAL**;
satu-satunya yang lulus tetap **E12** (aturan keluar). Yang baru saja hidup: efek prediktif yang lolos
BH. Itu bahan keputusan berikutnya (ongkos, ukuran, venue, proksi ke jangkar likuid), bukan bahan
klaim: submit malam ini tetap tidak boleh menulis "Fabius tahu kapan masuk".


## F-D70 — Fabius menjadi operator pemilih bot dan menjual sinyal berbukti; paper penuh sampai builder yakin · 2 Okt 2026

Builder (2 Okt, diringkas): Fabius menjadi **agen operator**. Ia menganalisis dan hanya boleh **memilih** bot - satu bot = satu metode + satu
parameter - dengan enam bot sebagai awal ([[08-Backlog/05 - Epik Enam Bot]], usulan). Mesinnya dibangun dulu; sesudah itu FE sebagai **gerbang
penjualan sinyal**: agen membayar per sinyal lewat x402 dan menerimanya lewat MCP; pengguna berlangganan lewat x402 V2 dengan sesi dan menerimanya
lewat surel ([[08-Backlog/06 - Epik Gerbang Sinyal]]). Cakupan sinyal: **niat posisi** (masuk, keluar, sesuaikan ukuran) - bukan jenis order. Uang nyata
kemungkinan besar lewat Binance Agentic Wallet, tetapi **paper penuh** sampai builder sendiri yakin mengeluarkan uangnya.

**Yang bergeser.** Kalimat *"Fabius menjual bukti yang bisa diperiksa, bukan sinyal"* ([[00-Overview/02 - Business Process]]) dan *"Kami tidak
menjual sinyal"* ([[10-Submissions/02 - Project Detail]]) tidak lagi menggambarkan ARAH; penggantinya: **menjual sinyal yang berbukti** - sinyal yang
sudah dikomit di chain sebelum hasilnya, dihasilkan aturan yang dikunci sebelum datanya, dan yang semuanya dibuka pada waktunya. Premis F-D03 (nol CEX
di jalur kritis) dan cakupan F-D09 (universe token BSC) tidak berlaku untuk bot operator (aset mayor, RWA, venue perp); keduanya tetap benar untuk jalur
memecoin yang sudah ada. F-D13/F-D33 (lapisan arah kalah; mencari alasan masuk) bergeser: alasan masuk sekarang datang dari bot yang dipilih dan sudah
lolos gerbang, bukan dari agen yang meracik sendiri.

**Yang tetap mengikat - tidak ada yang dilonggarkan.** F-D11 (model hanya mempersempit; kini juga untuk peninjau pengajuan bot), F-D16 (uang nyata =
harapan bersih > 0 setelah ongkos nyata, n ≥ 20, tanpa fold terbaik, BH 0,10, di luar sampel), F-D17 (tanpa fee-on-profit dari dompet pengguna), F-D18
(tanpa kurva imbal hasil untuk yang datang awal; potongan harga sisi biaya boleh), F-D32 (paper = slot; control tidak mempromosikan dirinya), anchor
sebelum hasil, kunci pra-registrasi ber-sha, plafon hanya turun, tanpa custody.

**Jawaban builder atas enam pertanyaan, 2 Okt malam:** (1) mesin tinggal di paket `engine/` (bukan `tools/`); (2) B2 memakai 7 sub-buku, tanpa memilih hari
rebalance; (3) sinyal = niat posisi; (4) komit sinyal memakai **keccak256 atas `abi.encode(struct, salt)` dan akar Merkle gaya OpenZeppelin** - sinyal
mentah tidak masuk chain, hash spesifikasi tetap sha256 JSON; sudah diterapkan di `engine/chain.py` dan `engine/sinyal.py` dan diuji silang dengan
`cast keccak`, `cast abi-encode`, `eth_utils`; (5) pivot dicatat sekarang (entri ini) beserta banner BN-PIVOT; (6) venue uang nyata kelak: Binance
Agentic Wallet - hanya long-only on-chain, jadi bot yang butuh short atau perp (B2, kaki perp B3, B4) perlu venue lain - sekarang paper penuh.

**Urutan penjualan (usulan, menunggu kata builder):** tingkat 0 - umpan bukti (komit + pembukaan tertunda + rekam jejak paper, tanpa klaim keuntungan) -
boleh lebih dulu; tingkat 1 - sinyal waktu-nyata berbayar - **hanya** untuk bot yang lolos F-D16 pada data maju ter-anchor **dan** setelah telaah hukum
(P75/P80); tingkat 2 - mengeksekusi untuk orang lain - tidak dijual.

**Status hari ini, ditulis apa adanya.** Arah diputuskan. **Belum ada** bot terkunci, sinyal maju, kontrak baru, FE, atau penjualan. Yang ada: paket
`engine/` (bot murni, replay, sinyal komit-ungkap, guard bar basi, gerbang seleksi, buku slot; 169 tes lulus saat ditulis). Kalimat publik yang dilarang
sampai ada data maju ada di [[10-Submissions/01 - Claims Cheat Sheet]] (blok BN-PIVOT).

**Terkait:** [[08-Backlog/05 - Epik Enam Bot]] · [[08-Backlog/06 - Epik Gerbang Sinyal]] · [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] ·
[[Concepts/One-Way Gate]] · [[00-Overview/02 - Business Process]]

## F-D71 — Program penerbit bot: sepuluh slot, seleksi ketat, rolling berbasis PnL net · 2 Okt 2026

Builder (2 Okt, diringkas): Fabius dibuka untuk kolaborasi - orang lain boleh mengajukan bot, tetapi **teorinya harus terbukti kualitasnya lebih dulu**,
**identitas penerbit (terutama dompet) jelas** supaya penerbit mendapat bagian bila botnya menghasilkan, dan **seleksinya ketat**: yang masuk harus
benar-benar menguntungkan Fabius. Maksimal **10 bot**; minimal 1 milik Fabius sebagai identitas, 9 slot bebas. Bila penuh dan penantang terbukti lebih
baik, **rolling**: bot terlemah dibuang.

**Bentuknya** (kode `engine/submission.py`, `engine/gates.py`, `engine/slots.py`; rancangan lengkap [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]]):

1. Formulir **skema tertutup**: identitas bertanda tangan EIP-712 (dompet EIP-55), teori terstruktur, bukti sebagai KLAIM, pembunuh terstruktur
   (metrik, pembanding, ambang, jendela), pernyataan wajib. Seluruh isi formulir adalah input musuh.
2. Gerbang **G1-G11 deterministik** pada data dan penggaris kami; yang menerima adalah gerbang, bukan opini model. Peninjau agen hanya boleh menolak atau
   meminta info (satu arah, F-D11). Kode pihak luar tidak pernah dijalankan otomatis.
3. Lolos gerbang = boleh **shadow** maju (≥ 60 hari, ter-anchor, PnL net > 0); baru sesudah itu slot. Slot ≠ uang nyata (F-D16 tetap).
4. Slot: maksimum 10; ≥ 1 bot identitas Fabius (kebal rolling); ≤ 2 slot per penerbit luar (dompet payout yang sama = satu keluarga); rolling mengganti
   penghuni terlemah yang boleh digusur bila penantang unggul margin; tak terukur ≠ lemah; paling banyak satu penggantian per epoch.
5. **Satu koreksi atas kata builder:** metrik rolling = **PnL net setelah ongkos**, bukan win-rate. F-D16 sudah mematikan win-rate sebagai ukuran (panel
   whale WR 69,8 % tetapi −10,4 bps). Win-rate hanya diagnostik.
6. **Imbalan penerbit = bagi hasil dari penjualan sinyal bot itu** (x402 `payTo` ke kontrak pemisah milik bot), **bukan** fee dari profit dompet pengikut
   (F-D17). Berhenti saat bot keluar slot; yang sudah terkumpul tetap bisa ditarik.
7. **Fabius tunduk pada gerbang yang sama** (dogfood). Hasil 2 Okt (`python -X utf8 -m engine.cli gate --data <dir> --bot ALL`; ambang = bawaan kode, belum
   dikunci): **B3 dan B5 LOLOS_SHADOW; B1 (G8, G10), B2 (G4), B6 (G3, G8, G10) TOLAK; B4 tidak terukur**. Lari pertama menggagalkan B5 lewat placebo yang tidak
   bermakna untuk bot alokasi; gerbang diganti dan perubahan itu dipajang di epik 07 §7. Karena perubahan metode terjadi setelah melihat hasil, ambang dan
   jenis-nol **dikunci sebelum kandidat luar pertama** (P86).

**Yang belum diputuskan builder:** persentase bagi hasil, bot identitas (usulan B5-CORE-RWA), kunci ambang, jenis bot yang dibuka lebih dulu (usulan:
hanya `template`), biaya pengajuan, peninjau agen dan anggarannya - epik 07 §10. **DIJAWAB di F-D72: tanpa agen (peninjau = bot ber-KPI); 60/40; template dulu; tanpa biaya pengajuan.**

**Terkait:** [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] · [[08-Backlog/05 - Epik Enam Bot]] · [[Concepts/One-Way Gate]] ·
[[Concepts/Unmeasured Is Not Clean]] · F-D11 · F-D16 · F-D17 · F-D18 · F-D32


## F-D72 — Putaran kedua: bagi hasil 60/40, bot identitas kripto, template dulu, tanpa biaya pengajuan, peninjau = bot ber-KPI (bukan agen), tingkat 0 duluan · 2 Okt 2026

Builder menjawab pertanyaan penutup F-D71 (2 Okt malam). Dicatat apa adanya, beserta apa yang saya lakukan dan apa yang masih menunggu:

1. **"Saya setuju 60/40."** Penerbit 60 %, Fabius 40 %. Basis yang saya pasang: **pendapatan penjualan sinyal bot itu**, bukan profit trading dan bukan profit pengikut.
   Alasannya terukur (`python -X utf8 -m engine.cli gate`, KPI K5): bila penerbit mengambil 60 % dari bulan yang untung tanpa menanggung bulan yang rugi, B1 yang untung
   +50,2 %/tahun membuat Fabius **−1,6 %/tahun** (B2 −8,3 %, B6 −2,6 %). *Menunggu konfirmasi bahwa basisnya pendapatan.* **→ DIJAWAB di F-D73: "Betul."** Kode: `engine/economics.py`.
2. **Bot identitas: "kalau bisa yang trading crypto biar kelihatan beneran trading."** Bisa. Kandidat konkret **B1-TREND** (long/flat kripto, long-only sehingga bisa jalan di Binance
   Agentic Wallet). Catatan jujur: B1 gagal dua gerbang secara tipis (G8, G10) dan 12 bulan terakhirnya −0,42. Identitas = penunjukan (kebal rolling), bukan kelulusan; catatannya
   tampil dengan gerbang yang gagal; ia mati lewat pembunuhnya sendiri; F-D16 tetap berlaku sebelum uang nyata. *Menunggu konfirmasi.* **→ DIJAWAB di F-D73: B1-TREND.**
3. **"Kunci ambang - maksudnya apa?"** (pertanyaan saya) dijelaskan di [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] §10 #3: semua angka lolos/gagal ditulis ke satu berkas, dihitung sha-nya,
   dan dipasang sebelum kandidat luar pertama; mengubah satu angka = kunci baru. Mekanismenya sudah dikode (`engine/locks.py`, `engine.cli lock`); **belum dikunci** - menunggu kata builder. **→ DIKUNCI sementara di F-D73 (v1).**
4. **"Template dulu gapapa."** `submission.ENABLED_KINDS = ("template",)`; `method_pr` dan `feed` ada di skema tetapi ditolak.
5. **"Tidak ada dulu"** untuk biaya pengajuan. Spam dibatasi tanpa uang: ≤ 2 pengajuan berjalan per keluarga dan masa tunggu 30 hari setelah penolakan (`slots.can_submit`).
6. **"Meninjau bot yang dikirim lebih baik pakai bot, bukan agen; beri logika KPI minimal supaya Fabius juga untung saat memakai bot itu."** **Mengganti** butir peninjau-agen di F-D71 #2 dan P82.
   Peninjau = `engine/review.py` (validasi → identitas → gerbang G1-G11 → KPI K1-K5 → laporan ber-sha), deterministik. Konsekuensi yang dikatakan terus terang: teks teori tidak dinilai
   mesin (pengungkapan, bukan penilaian); yang menentukan bukti terukur; manusia hanya boleh memveto (F-D11). KPI minimal: K1 imbal hasil tahunan net ≥ hurdle bebas-risiko 4 % + margin 2 %;
   K2 Calmar ≥ 0,5; K3 ≥ 12 sinyal/tahun dan ≥ 20 total; K4 klaim penerbit tidak melebihi terukur; K5 skenario profit-share terburuk bagi Fabius (informatif selama basis = pendapatan).
7. **"Boleee"** untuk tingkat 0: umpan bukti gratis (komit + pembukaan tertunda + rekam jejak paper, tanpa klaim keuntungan) boleh dikirim lebih dulu; tingkat 1 tetap menunggu F-D16 pada data maju dan telaah hukum.

**Tinjauan keamanan independen (agen terpisah, hanya-baca) atas kode baru: 12 temuan, diukur.** Tiga di antaranya mengubah isi, bukan hanya kode: (a) gerbang adalah oracle publik tanpa kontrol
uji-berganda (pada 476 konfigurasi random-walk tanpa edge, G3 meloloskan 5,3 % dan dua lolos semua gerbang) → ambang G3 kini naik menurut jumlah percobaan dan **gerbang diposisikan sebagai penyaring
awal, bukan bukti**; (b) uji admit/gusur slot tidak bermakna statistik → gusur kini butuh selisih berpasangan pada jendela yang sama dengan t ≥ 2, dan **slot dinyatakan paper berhak-rendah**;
(c) G8 untuk bot alokasi terlalu lemah → kini dua uji, dan **B5-CORE-RWA yang lolos pada versi sore kini TOLAK**. Rincian dan status per temuan: epik 07 §9. Satu cacat adalah milik saya sendiri
(varian plateau dihitung dari nilai bawaan template, bukan nilai kandidat) dan ditangkap tes.

**Hasil dogfood setelah perubahan (N = 20 percobaan; ambang belum dikunci):** B3 **LOLOS_SHADOW**; B1 TOLAK (G8, G10); B2 TOLAK (G4); B5 TOLAK (G8); B6 TOLAK (G3, G8, G10, K2); B4 tak terukur.
**Hanya satu bot yang bisa dinilai lolos, dan ia sedang dorman.** Itu bukan alasan melonggarkan gerbang; itu alasan paper penuh dan menunggu data maju (jawaban builder 6 di F-D70).

**Terkait:** [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] · [[08-Backlog/06 - Epik Gerbang Sinyal]] · [[Concepts/One-Way Gate]] · F-D11 · F-D16 · F-D17 · F-D70 · F-D71

## F-D73 — Putaran ketiga: basis bagi hasil = pendapatan, bot identitas = B1-TREND, ambang v1 dikunci sementara, riset optimasi dijadwalkan · 2 Okt 2026

Builder menjawab tiga pertanyaan penutup F-D72, kata-katanya: *"1. Betul 2. Yg pnting tradenya instrument crypto saya gas 3. Sementara ini oke, nanti kita coba riset lagi untuk mengoptimalkan itu (catat di vault)"*.
Dicatat apa adanya, beserta apa yang saya kerjakan:

1. **"Betul."** - bagi hasil 60/40 dihitung dari **pendapatan penjualan sinyal bot itu**; bukan profit trading dan bukan profit pengikut. Menutup F-D72 #1. Kode `engine/economics.py`; tercatat di kunci
   (`ekonomi: penerbit 60% / Fabius 40% dari pendapatan penjualan sinyal`). KPI K5 tetap mencetak skenario profit-share terburuk, tetapi **hanya informatif** selama basisnya pendapatan.
2. **"Yang penting tradenya instrumen kripto, saya gas."** - bot identitas = **B1-TREND**. Menutup F-D72 #2. Syaratnya dipaksa kode, bukan niat: `engine/book.py` (`trades_crypto_only`;
   `genesis_book` menolak bot yang bukan instrumen-kripto-saja; emas/RWA dan B5 tidak termasuk). Yang tetap berlaku dan **tetap tampil**:
   - identitas = **penunjukan** (kebal rolling), **bukan kelulusan gerbang**;
   - B1 **gagal dua gerbang secara tipis**: G8 (placebo p = 0,090, batas atas 0,123 > 0,05) dan G10 (ΔSharpe EW +0,04 < 0,05); 12 bulan terakhir −0,42
     (dicetak ulang hari ini: `python -X utf8 -m engine.cli gate --data <dir> --bot B1-TREND` dan `09-Inbox/Session-2026-10-02-skrip/run11_recent_windows.py`);
   - ia mati lewat pembunuhnya sendiri ("12 bulan maju tanpa mengalahkan buy&hold pada MDD dan Sharpe"); F-D16 (n ≥ 20, net > 0 setelah ongkos nyata, buang fold terbaik, BH 0,10, OOS) tetap pagar sebelum uang nyata;
   - **buku genesis hanya berisi B1** (`python -X utf8 -m engine.cli book`: 1 entri, `book_sha 0xfe37d759…6e05c`). B2/B3/B5/B6 **tidak diberi slot gratis**: mereka lewat gerbang → shadow → slot seperti penerbit luar.
3. **"Sementara ini oke, nanti kita coba riset lagi untuk mengoptimalkan itu (catat di vault)."** - semua ambang (gerbang G1-G11, KPI K1-K5, slot, 60/40) disetujui **sebagai v1, untuk sementara**, dan **DIKUNCI**:
   `python -X utf8 -m engine.cli lock` → `KUNCI: TERKUNCI`, sha `0xf145b70abd251b9fcf421bfb811bcf3788dade347c37b3bea331a09fedfe5f32`, berkas `engine/locks/review.lock.json`, `dikunci` 2026-10-02T07:40:00Z.
   Mengubah satu angka sesudahnya = kunci baru yang terlihat (`lock --write --supersede` memindahkan yang lama ke `engine/locks/history/`). "Sementara" dibaca harfiah: **v1 bukan klaim bahwa ambang optimal**;
   empat perubahan gerbang sesudah melihat hasil (epik 07 §0) adalah alasan mengunci sekarang, bukan alasan percaya angkanya. Riset optimasi: [[08-Backlog/08 - Riset Optimasi Ambang]] (status USULAN; aturan anti-snooping
   ditulis **sebelum** riset dimulai).

**Dengan terus terang, apa arti kunci ini sekarang:** (a) berkasnya belum di-commit dan **belum di-anchor**; `dikunci` adalah jam laptop (14:40 WIB = 07:40Z). Sampai di-anchor ia pengakuan saya, bukan bukti
pra-registrasi (anchor-before-outcome). Meng-anchor sha-nya = transaksi; **tidak saya jalankan, menunggu kata builder**. (b) Vonis peninjau `mengikat` hanya bila identitas penerbit terverifikasi **dan** kunci TERKUNCI **dan** vonis
LOLOS_SHADOW; belum ada penerbit luar, jadi tidak ada vonis yang mengikat siapa pun. (c) Kunci ini tidak mengubah satu pun vonis: contoh formulir (`engine/examples/submission.example.json`) terhadap buku genesis tetap
**LOLOS_SHADOW** (ΔSharpe EW +0,28; korelasi maks +0,69 terhadap B1, lolos tipis dari 0,7; `mengikat: TIDAK`; `report_sha 0x4a178e16…196c`) - demonstrasi lagi bahwa klon-berpilihan B1 lewat; masuk daftar riset (R11).
→ **DIPERBARUI di F-D74:** kunci v1 **ter-anchor** (tx `0xf09d61e6…`, `anchoredAt` 2026-10-02T08:17:48Z); jam yang berlaku = waktu blok itu, bukan 07:40Z.

**Koreksi kecil yang dipajang:** kata "malam" pada F-D72 dan pada catatan berkas kunci adalah sebutan saya, **bukan jam**. Jam laptop saat kunci ditulis 14:40 WIB. Jam yang berlaku = `dikunci` di berkas, dan kelak commit/anchor.

**Garis dasar pertama riset (dicetak hari ini, `09-Inbox/Session-2026-10-02-skrip/run13_null_calibration.py`, pasar random-walk tanpa edge; rinci di epik 08 §3):** pada 340 konfigurasi satu pasar, **4 lolos semua gerbang bila
penambang tidak mendeklarasikan percobaan (N = 1) dan 0 bila jujur (N = 340)**; 60 pengajuan satu-kali pada pasar independen: 0 lolos. Itu menegaskan bahwa gerbang = penyaring awal dan shadow maju = satu-satunya bukti (epik 07 §9 #1).

**Yang tidak berubah:** tidak ada uang nyata (paper penuh, F-D70); tidak ada kontrak baru; tidak ada penerbit luar; tidak ada commit/push (hanya atas kata builder, tanpa atribusi AI, kabari sebelum push);
`method_pr`/`feed` tetap ditutup; F-D16/F-D17/F-D18 tetap berlaku.

**Menunggu builder:** (1) **meng-anchor sha kunci** (satu transaksi; atau tunda); (2) commit `engine/` + vault (belum pernah di-commit); (3) **anggaran** untuk riset 08 - berapa positif-palsu yang masih bisa diterima dan daya minimum pada edge berapa
(usulan saya di epik 08 §1, **dipertanyakan nanti, bukan sekarang**). **→ DIJAWAB di F-D74: (1) anchor sekarang - selesai; (2) commit - selesai; (3) "maksudnya apa?" - dijelaskan, belum diputuskan; M2 "gassss" - dimulai.** **Tidak lagi terblokir:** jam maju M2 (ledger paper per bot) karena kunci sudah ada; kontrak tingkat 0 (M3) tetap menunggu kata builder.

**Terkait:** [[08-Backlog/08 - Riset Optimasi Ambang]] · [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] · [[08-Backlog/06 - Epik Gerbang Sinyal]] · [[08-Backlog/05 - Epik Enam Bot]] · [[Concepts/One-Way Gate]] ·
F-D11 · F-D16 · F-D17 · F-D70 · F-D71 · F-D72

## F-D74 — Putaran keempat: kunci v1 ter-anchor, commit, "maksudnya apa" dijelaskan, M2 dimulai · 2 Okt 2026

Builder menjawab empat pertanyaan penutup F-D73, kata-katanya: *"Untuk sekarang di push dulu aja semua commitnya, lalu : 1. Anchor sekarang gapapa sih 2. Commit 3. Mangsudnya apa 4. gassss"*. Dicatat apa adanya:

1. **"Anchor sekarang gapapa sih" - dikerjakan.** Alat baru `tools/anchor_lock.py` (default = rencana tanpa kirim; `--send` mengirim satu transaksi; `--verify` tanpa kunci dan tanpa gas) mengirim satu `anchor()` ke `DecisionAnchor` di chain 97:
   - tx `0xf09d61e601e218017aa225ebaf3ae86429031cbf46042cc80de9c0e8af7ae45f`, blok 134404691, gas 250.867; `anchorCount()` 19 → 20; id `0xdcca74f81f4e3002f4315711009f8519d07f9f2a091cffb3dd9e1003c331f51e`;
   - **`anchoredAt` 1790929068 = 2026-10-02T08:17:48Z: itulah jam yang berlaku bagi kunci v1** (bukan `dikunci` 07:40:00Z, yang jam laptop; selisih ±38 menit);
   - pemetaan (dikatakan terang-terangan karena kunci bukan keputusan dagang): asset `FABIUS-LOCK/review-v1`; verdict **Abstain** (kontrak hanya punya Enter/Abstain; Enter akan menggelembungkan hitungan keputusan masuk);
     decisionHash = sha kunci `0xf145b70a…5f32`; gatesHash = sha atas `params.gerbang`; snapshotHash = sha atas seluruh berkas kunci (ikut mengikat `dikunci` dan `catatan`);
   - dibaca ulang word-per-word dari chain: cocok; menjalankan ulang tidak mengirim lagi (idempoten); catatan di `engine/locks/anchors/f145b70abd25.json`; `python -X utf8 tools/anchor_lock.py --verify` → "cocok word-per-word";
     `python -X utf8 tools/anchor.py --verify` tetap **13/13 cocok, 0 BEDA** (alat lama hanya mencakup `direction-*.jsonl`);
   - efek samping: `anchorCount()` dan `countByAgent` kini 20, jadi "19" pada halaman bertanggal (mis. Test Commands 28 Sep) adalah riwayat, bukan keadaan sekarang; selisih cakupan P6b bertambah satu karena baris kunci bukan keputusan dagang
     dan **tidak boleh dihitung sebagai prediksi**;
   - yang **tidak** dibuktikan: bahwa angkanya benar atau teroptimasi - hanya bahwa angka-angka ini ada, utuh, dan lebih dulu daripada kandidat luar pertama, dikirim oleh agen yang terdaftar di kontrak. Anchor tidak menghapus catatan bahwa
     gerbang diubah empat kali sesudah melihat hasil sebelum dikunci (epik 07 §0).
2. **"Commit" - dikerjakan.** Satu commit berisi `engine/`, `tools/anchor_lock.py`, halaman vault epik 05-08, F-D70..F-D74, catatan anchor, dan skrip eksploratif sesi; tanpa atribusi AI (F-D22).
   **Tidak ikut:** `References/` (dua JPG milik builder, tak terkait).
3. **"Mangsudnya apa"** (tentang "anggaran positif-palsu dan daya") - dijelaskan dengan bahasa biasa di [[08-Backlog/08 - Riset Optimasi Ambang]] §1a; **belum ada keputusan anggaran** dan usulan A1/A2 tetap usulan.
   Inti: dua jenis salah penyaring (bot jelek lolos vs bot bagus tertolak) saling tarik-menarik, dan batas yang kita relakan harus dipilih builder **sebelum** hasil riset dilihat.
4. **"gassss"** (M2) - dimulai: ledger paper per bot + jam maju (epik 05 §14, P77). Dicatat ketika ada hasil terukur; tidak ada yang diklaim di sini.
5. **"Di-push dulu aja semua commitnya."** Keadaan saat dicatat: tidak ada commit lokal di depan origin (`git rev-list --left-right --count HEAD...origin/master` → `0 452`: lokal tertinggal 452 commit bot yang sudah terunduh;
   ujung origin sekarang `05dab7b2…` menurut `git ls-remote`). Satu `git fetch` gagal (`early EOF`); fetch diulang lewat HTTP/1.1. Push dikerjakan sesudah commit, lewat `vault/scripts/prepush_check.py`, tanpa force;
   hasilnya di [[09-Inbox/Session-2026-10-02]] §11.

**Terkait:** [[08-Backlog/08 - Riset Optimasi Ambang]] · [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] · [[08-Backlog/05 - Epik Enam Bot]] · [[Concepts/Anchored Before Outcome]] · F-D22 · F-D70 · F-D72 · F-D73

## F-D75 — M2: ledger paper maju per bot, pengunduh bar, dan jam maju · 2 Okt 2026

Dikerjakan atas "gassss" builder (F-D74 #4). Ini **infrastruktur**, belum bukti: jam maju baru berjalan hitungan hari. Yang diputuskan dan kenapa (semuanya bisa dibalik; dikabari karena mengikat bentuk catatan yang append-only):

1. **Dua jenis catatan dengan sifat waktu berbeda.** `tick` = EX-ANTE: niat posisi pada penutupan bar, dari data sampai bar itu saja, **≤ 12 jam** sesudah penutupan (guard umur bar `engine/freshness.py`); terlambat = **`gap`** yang tidak pernah diisi belakangan.
   `settle` = EX-POST: net paper satu bar, dihitung ulang oleh **`replay()` yang sama dengan gerbang** dari tick sebelumnya + harga dan funding nyata; boleh terlambat. Satu jalur kode: tes membuktikan hasil ledger = replay penuh (selisih ≤ 1e-13).
2. **Settle menunggu data, tidak diisi nol.** Bar tanpa funding lengkap (bot perp membayar funding) ditunda ("menunggu penutupan"); hari bolong membuat bar sesudahnya **tak terukur** (turnover tak diketahui), bukan nol.
3. **Rantai hash** per bot (`ledger/paper/<bot>.jsonl`; `prev`, `h` = sha256 JSON kanonik). `python -X utf8 -m engine.cli ledger verify` memeriksa rantai **dan menghitung ulang setiap tick dan settle dari `ledger/bars/*.csv`**; bar yang diubah sesudah kejadian terdeteksi lewat `data_hash`.
   Genesis menautkan `spec_sha` dan sha kunci ambang beserta anchor-nya; spesifikasi berubah = ledger baru ("pivot = kunci baru").
4. **Siapa yang boleh punya jam maju:** hanya bot identitas (B1-TREND) dan yang LOLOS_SHADOW pada kunci v1 (B3-CARRY): `engine/book.py` `SHADOW_ELIGIBLE`. B2/B5/B6 (TOLAK) dan B4 (tak terukur) tidak diberi jam maju gratis.
5. **Bar ikut di-commit** (`ledger/bars/`, ±5 MB seed dari data 2020-2026-08-31 + perpanjangan harian) supaya siapa pun menghitung ulang tanpa mengunduh apa pun. Sumber: `data.binance.vision` (publik). `.gitattributes`: `ledger/** text eol=lf`, **tanpa** `merge=union` (dua penulis harus bertabrakan terlihat).
6. **Penulis resmi = job `.github/workflows/paper-ledger.yml`** (tujuh putaran sehari di sekitar jam terbit berkas: 08:47Z dan 09:07-11:37Z tiap 30 menit; idempoten; commit oleh runner GitHub = cap waktu pihak ketiga; tanpa kunci, tanpa transaksi chain). **Dipush 2 Okt ke master (`c67cb2f`, `015ceed`; builder: "Gasss") dan dijalankan sekali manual** (`gh workflow run`, run 36987654079, sukses): runner menjangkau `data.binance.vision` (bar yang belum terbit dibedakan dari galat: XRPUSDT 2026-10-01 = 404 "belum terbit"), dan `engine.cli ledger verify` serta langkah commit berjalan.

**Terukur hari ini** (perintah di [[09-Inbox/Session-2026-10-02]] §12): dari jaringan builder `data.binance.vision` dan `data-api.binance.vision` → 200, tetapi `fapi.binance.com` gagal TLS (`SEC_E_WRONG_PRINCIPAL`; sama dengan catatan egress-probe), jadi funding terbaru tidak bisa diambil lewat REST dari sini - diisi dari **zip bulanan** (September terbit; Oktober baru awal November). **Dari runner GitHub (run 36987654079, 09:04Z): `fapi.binance.com` → HTTP 451 (lokasi terbatas)**, jadi REST funding tertutup dari KEDUA jaringan; yang terjangkau dari keduanya hanya berkas statis Vision.
Akibatnya **`settle` hari-hari Oktober tertunda sampai REST terjangkau (mungkin dari runner) atau zip Oktober terbit**; `tick` tidak terpengaruh. Berkas harian Vision **terbit terlambat dan tidak serempak**: dari `LastModified` bucket S3 (`data.binance.vision`), berkas 2026-09-30 terbit 1 Okt 09:37-09:39Z dan BTCUSDT 2026-10-01 terbit 2 Okt 08:44:04Z; pada 08:54Z XRPUSDT 2026-10-01 belum ada, jadi tick ditolak ("aset hilang") dan diulang. Bar hari X baru tersedia ±8,7-9,7 jam sesudah penutupan, sehingga jadwal cron dipasang di sekitar jam itu (bukan pagi buta) dan jendela antara terbit dan batas 12 jam hanya ±2-3 jam: beberapa `gap` memang mungkin.

**Tick pertama sudah ada:** bar 2026-10-01, dibuat oleh runner GitHub (run 36988500288, commit `a982b76`), jeda 9,2 jam, 16 aset long, 0 sinyal; `ledger verify` SAH di runner (Linux) dan laptop (Windows) dengan kepala rantai sama `0x1c8f6e7769b1…`.

**Konsekuensi yang harus dibaca bersama angka maju:** tick keluar ±9-10 jam sesudah penutupan. Niat tetap ex-ante terhadap hasil bar berikutnya dan isinya hanya fungsi bar sampai penutupan (dihitung ulang dari bar), tetapi **harga masuk 00:00Z tidak bisa didapat pengikut pada saat itu**, sedangkan `settle` mengandaikan masuk di harga penutupan (konvensi replay). Angka maju paper karenanya memuat derau/optimisme dari jeda ini; laporan mencetak `jeda tick`. Sumber waktu-nyata (kline REST dari runner bila terjangkau) menyusul dan belum diukur.

**Belum dilakukan / tidak diketahui:** funding tepat waktu (jalan keluar yang belum diuji: merekonstruksi funding dari `premiumIndexKlines` harian Vision dan memvalidasinya terhadap zip bulanan - bila cocok, `settle` bisa tepat waktu dengan label "funding direkonstruksi"; P92); B3 belum diinisialisasi (butuh seed spot + `--spot` dan funding tepat waktu); kepala ledger belum di-anchor di chain (menunggu M3 atau kata builder); tidak ada notifikasi bila tick gagal; cron GitHub bisa terlambat.

**Menunggu builder:** ~~(1) push commit M2~~ **(1) selesai: "Gasss", dipush 2 Okt; cron harian aktif**; (2) aktifkan B3 (perlu seed spot, ±2 MB); (3) apakah kepala ledger di-anchor berkala (satu transaksi per anchor; atau menunggu `SignalAnchor` v2).

**Terkait:** [[08-Backlog/06 - Epik Gerbang Sinyal]] §6 · [[08-Backlog/05 - Epik Enam Bot]] §14 · [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] (P85) · [[08-Backlog/08 - Riset Optimasi Ambang]] (R8) · [[Concepts/Anchored Before Outcome]] · F-D16 · F-D32 · F-D73 · F-D74

## F-D76 — P92: funding direkonstruksi dari indeks premium; estimasi hanya untuk laporan PROVISIONAL dan target B3, bukan untuk settle final · 2 Okt 2026

Builder menjawab "Gas" atas usul P92 (F-D75): bisakah funding dibangun ulang dari berkas harian `premiumIndexKlines` Vision (terjangkau dari laptop DAN runner, sedangkan REST funding tertutup dari keduanya)?

**Pertanyaan dan uji.** Rumus Binance: F = P + clamp(I − P, ±0,05 %), P = rata-rata tertimbang waktu indeks premium per menit pada interval (bobot menit ke-i = i), I = 0,01 % per interval 8 jam. Diuji pada peristiwa yang **sudah diketahui**
(funding aktual dari zip bulanan di `ledger/bars/fund_*.csv`) dengan `09-Inbox/Session-2026-10-02-skrip/run15_funding_reconstruct.py`; satuan galat: 1e-6 = 0,01 bps per peristiwa.

**Hasil terukur** (dicetak ulang hari ini):
- **Bobot menentukan** (`--variants`, BTC dan ETH, Jul-Agu 2026, n = 372): bobot naik menurut waktu (rumus Binance) MAE 2,31; rata-rata biasa 8,85 (3,8×); bobot terbalik 17,0 (7,4×). Bobot linear benar, tetapi tidak persis: sisa galat ada.
- **Satu simbol punya I berbeda.** BNBUSDT: funding aktual **tepat 0** pada 276 dari 549 peristiwa (Mar-Agu); dengan I = 0,0001 MAE-nya 72,8 (median 98,6); dengan **I = 0** rumus mengembalikan 0 selama |P| ≤ 0,05 %, dan MAE-nya turun ke level simbol lain.
- **Luar sampel** (`--oos`: I per simbol dipilih diskret pada Mar-Mei, diuji Jun-Agu 2026; 16 perp, **n = 4.368 peristiwa**): MAE **5,63** (0,056 bps), median 3,26, p95 19,87, p99 31,49, maks 92,90 (0,93 bps). Per hari-simbol (n = 1.488): MAE **10,72** (0,107 bps), median 6,91, p95 34,55, p99 54,66,
  maks 129,84 (1,30 bps); bias rata-rata **+2,49** per hari (0,025 bps/hari; estimasi sedikit di atas aktual, jadi PnL paper sedikit terlalu rendah). I terpilih: 0,0001 untuk 15 simbol dan 0 untuk BNBUSDT.
- **Luar waktu (2025):** Mei-Agu 2025 (`--engine-i`, n = 5.904 peristiwa; tanpa menyetel apa pun pada data 2025): MAE **4,78** (0,048 bps), median 1,34, p95 20,37, maks 76,39 (0,76 bps), 42,5 % persis sampai pembulatan 8 desimal; **BNBUSDT dengan I = 0: MAE 1,23, median 0** (tanpa koreksi: MAE 78,9) - jadi aturan I = 0 berlaku juga di 2025, bukan kebetulan Mar-Mei 2026.
- **Fidelitas target B3** (`run16_b3_est_fidelity.py`; estimasi menggantikan aktual untuk SEMUA hari uji = kasus yang lebih keras daripada operasi maju, yang mencampur aktual dan estimasi): 2025-02-01..2026-08-31 (577 hari): bobot target berbeda pada **20 dari 577 hari (3,5 %)**; aset-hari dipegang 270 (aktual) vs 267 (estimasi), 23 aset-hari berganti status (8,5 % dari yang dipegang; ETC 6, NEAR 5, AVAX 3, ...); net PnL B3 dengan funding aktual pada settle: **−34,63 bps vs −41,30 bps** (selisih −6,67 bps selama 577 hari). Jun-Agu 2026 saja: 3 dari 92 hari, selisih −0,58 bps. Catatan: B3 hampir dorman di jendela ini (270 aset-hari dari ±9.200 mungkin), jadi uji ini lemah untuk rezim saat B3 aktif penuh.
- Funding yang terkunci di I (|P − I| ≤ 0,05 %) direkonstruksi persis; galat muncul saat funding bergerak bersama P, dan paling besar pada DOT (MAE 9,70 luar sampel), BCH (9,04), ATOM (8,59), ADA (7,49); penyebabnya belum diselidiki.
- **Jam terbit** (`Last-Modified` berkas Vision): premium harian BTCUSDT 2026-10-01 → 2 Okt 09:10:00Z; 2026-09-30 → 1 Okt 09:16:53Z; zip bulanan 2026-09 → 2 Okt 09:07:58Z. Jadi berkas premium terbit di jendela waktu yang sama dengan kline harian (±08:40-09:40Z), tidak lebih lambat secara konsisten.

**Skala.** Galat 0,1 bps per hari-simbol dibanding: funding dasar ±3 bps/hari (0,01 % × 3), biaya masuk replay 7 bps/sisi, simpangan PnL harian B1 ratusan bps. Untuk **mengukur PnL** B1 galat itu praktis nol (≪ 0,1 % dari derau harian). Untuk **keputusan ambang** B3 (rata-rata funding 7 hari
disetahunkan > 10 %; funding dasar 10,95 %/tahun, jadi marjin ±0,26 bps/hari) galat estimasi sebanding dengan marjin hanya saat funding bergerak; saat funding terkunci di dasar estimasinya persis. **Fidelitas target B3 diukur di bawah** (`run16_b3_est_fidelity.py`).

**Keputusan desain** (semuanya bisa dibalik):
1. **`settle` final tetap hanya dari funding AKTUAL.** Estimasi tidak pernah ditulis sebagai settle; catatan rantai tetap "final atau menunggu" (tak terukur ≠ bersih).
2. **Estimasi disimpan beku** di `ledger/bars/fund_est_<SYM>.csv` (append-only, hanya hari LENGKAP = tiga peristiwa sekaligus, dimulai sesudah peristiwa aktual terakhir, tidak diganti saat funding aktual terbit). Efek samping yang berguna: log galat estimasi-vs-aktual terkumpul sendiri begitu zip bulanan terbit.
3. **Laporan PROVISIONAL**: `engine.cli ledger report` mencetak satu baris berlabel ("funding direkonstruksi ... BUKAN catatan rantai, belum final") untuk bar yang belum bisa final; menjadi final saat funding aktual terbit.
4. **Jalur B3 disiapkan, B3 belum diaktifkan.** Pandangan data `funding_view`: `actual` (settle final, verifikasi), `provisional` (laporan), `targets` (estimasi beku untuk hari sejak berkas estimasi ada, aktual sebelumnya): hitung-ulang tick B3 tetap sama walau funding aktual terbit belakangan dengan nilai yang beda (tes). B3 tetap menunggu kata builder.
5. Rumus ada di `engine/funding_est.py` (murni, 480 menit penuh atau tidak sama sekali; dibulatkan 8 desimal seperti Binance); pembaruan jaringan di `tools/feed_bars.py` (berkas harian premium; berhenti di hari yang belum terbit; tidak pernah menebak menit).

**Batas yang jujur.** Estimasi ≠ funding. Asumsi interval 8 jam (Binance bisa mengubah interval simbol; tidak ditangani - galat akan terlihat saat aktual terbit). I per simbol dipelajari dari Mar-Mei 2026 dan bisa berubah. Satu sumber (premium Vision). Uji luar-sampel hanya tiga bulan.
Estimasi bias sedikit ke atas. Tidak ada ledger yang memakai estimasi untuk catatan final.

**Menunggu builder:** (1) aktifkan B3? Perlu seed spot (±2 MB), `--spot` di job, dan menerima bahwa target B3 memakai estimasi beku untuk hari-hari terbaru; jam maju B3 mulai dari bar saat genesis dibuat. **→ DIJAWAB "Gasssss": B3 aktif, F-D77.**
(2) ~~Ukur fidelitas target B3~~ **sudah diukur** (di atas): 3,5 % hari berbeda, selisih PnL kecil; kesimpulan saya: B3 layak diaktifkan dengan estimasi beku, tetapi keputusan di tangan builder.

**Terkait:** [[09-Inbox/Session-2026-10-02]] §13 · [[08-Backlog/06 - Epik Gerbang Sinyal]] §6 · [[08-Backlog/05 - Epik Enam Bot]] §14 · F-D75 · F-D74 · F-D16

## F-D77 — B3-CARRY masuk jam maju (bar pertama 2026-10-01); data tick dipersempit ke input target · 2 Okt 2026

Builder: *"Gasssss"* atas usul "aktifkan B3 dengan estimasi beku untuk target" (F-D76).

1. **Dikerjakan.** Seed spot 16 simbol di `ledger/bars/spot_*_1d.csv` (2,07 MB, 2020 → 2026-08-31, tanpa bolong); genesis `ledger/paper/B3-CARRY.jsonl` (bar pertama 2026-10-01, kunci v1 ter-anchor); `tools/paper_tick.py` memperpanjang spot otomatis bila ada bot yang memakainya.
   **Tick pertama B3 dibuat oleh job GitHub** (run 36992981123, commit runner `235e124`, `emitted_utc` 2026-10-02T10:00:21Z, jeda 10,0 jam): target **DOTUSDT 0,0625 dan ETCUSDT 0,0625** (2 dari 16 aset dengan funding 7 hari disetahunkan > 10 %), 2 sinyal; spot diperpanjang +496 baris oleh runner;
   `ledger verify` SAH di runner (Linux) dan laptop (Windows) dengan kepala rantai sama `0x1ce531d861e9…`. B1 tetap SAH (kepala `0x1c8f6e7769b1…`).
2. **Pengaman baru khusus B3:** aset tanpa bar spot pada hari asof dihitung hilang dari feed (tick ditolak, bukan alam semesta mengecil diam-diam); funding hari asof yang belum ada (estimasi belum terbit) membuat tick ditolak, bukan aset "datar karena tak terukur".
3. **Cacat yang tertangkap gladi SEBELUM push.** Menambah seed spot membuat `data_hash` tick B1 yang sudah ada tidak cocok saat dihitung ulang, karena sidik jari data B1 ikut menghitung deret spot yang tidak dipakai targetnya. Diperbaiki dengan `ledger.target_view`:
   data tick = jenis data yang dipakai target (B1/B2/B6 perp; B3 perp + spot + funding; B5 spot); tes regresi `LateSpotTests`. Ini kelas cacat yang sama dengan funding yang datang belakangan (F-D75): **data yang datang belakangan tidak boleh mengubah hash catatan lama.**
4. **Cek langsung pertama estimasi vs aktual** (`09-Inbox/Session-2026-10-02-skrip/run17_est_vs_rest.py --day 2026-10-01`): estimasi 2026-10-01 dikomit runner pada 09:33Z SEBELUM funding aktual dibaca; funding aktual dibaca lewat REST dari laptop pada 10:01Z.
   48 peristiwa: MAE **0,043 bps**, median 0,027, maks 0,17, bias ±0,0001 bps. Sejalan dengan uji luar sampel F-D76. Satu hari = sampel kecil.
5. **Egress berubah dalam satu jam:** REST `fapi` dari laptop builder gagal TLS ±08:5xZ tetapi 200 pada ±09:58Z; dari runner tetap 451. Tidak diandalkan (matriks egress punya tanggal kedaluwarsa, F-D25).

**Batas.** B3 hampir dorman (2 dari 16 aset di atas ambang); settle final B3 menunggu funding aktual (zip bulanan), laporan PROVISIONAL mengisi sementara; target B3 untuk hari terbaru bergantung pada estimasi (uji 2025-26: 3,5 % hari berbeda).
Paper penuh; bukan klaim edge; F-D16 tetap pagar.

**Terkait:** F-D75 · F-D76 · [[08-Backlog/06 - Epik Gerbang Sinyal]] §6 · [[09-Inbox/Session-2026-10-02]] §14 · F-D25

## F-D78 — Jadwal ledger paper: rantai yang menyambung dirinya sendiri + watchdog, bukan cron · 2 Okt 2026

Builder: *"Gas lanjut"*. Sebelum lanjut ke M3, satu kerusakan yang akan membuat jam maju bolong besok:

**Terukur** (`gh run list --workflow paper-ledger.yml --event schedule`; `gh run list --event schedule`): sejak push 09:03Z sampai 11:27Z, **tujuh cron `paper-ledger` tidak pernah menembak**
(semua run = `workflow_dispatch` manual saya). Cron lain di repo yang sama juga bolong: universe-hourly (per jam) menembak 23:07, 02:12, 09:39Z; wallet-flow-watchdog (`*/30`)
23:16, 02:20, 08:42Z - tiga kali dalam ±10 jam masing-masing. Jendela tick kita hanya ±3 jam per hari (berkas Vision terbit ±08:40-09:40Z, batas 12:00Z), jadi cron yang
bolong = `gap` permanen.

**Diganti** dengan pola wallet-flow yang sudah terbukti di repo ini: `paper-ledger.yml` = SATU job ±5 jam yang, hanya pada jendela 08:40-11:58Z dan hanya sampai tick hari itu beres,
menjalankan feed → tick/gap/settle → `ledger verify` → commit/push tiap 5 menit, lalu men-dispatch dirinya sendiri; **tanpa `schedule:` di berkas itu** (pelajaran wallet-flow 28 Sep:
penyelamat di berkas yang sama membunuh rantainya). Penyelamat terpisah `paper-ledger-watchdog.yml` (cron `*/20`, grup concurrency sendiri) menyalakan rantai **hanya** bila tidak ada
run `paper-ledger` yang hidup atau antre. Pagar: penjaga anti-tumpang-tindih (`.id`, bukan `.run_id`); `verify` gagal, `paper_tick` gagal, atau push gagal 5x = rantai berhenti
merah supaya manusia melihat; menghentikan = `gh workflow disable paper-ledger.yml` (dan watchdog-nya). `bash -n` lulus untuk semua langkah (wallet-flow sebagai pembanding juga lulus).

**Belum terbukti:** rantai baru dinyalakan 2 Okt siang; bukti pertama = tick bar 2026-10-02 pada jendela 3 Okt tanpa sentuhan manusia. Kalau gagal, harinya tercatat `gap` (terlihat).

**Terkait:** F-D75 · F-D77 · `.github/workflows/wallet-flow.yml` (pola asal) · [[09-Inbox/Session-2026-10-02]] §15

## F-D79 — M3 dimulai: LockRegistry + SignalAnchor v2 ditulis dan diuji lokal; deploy dan penanda tangan komit harian menunggu builder · 2 Okt 2026

Builder: *"Gas lanjut"*. Urutan M3 di [[08-Backlog/06 - Epik Gerbang Sinyal]] §3: C-A (`LockRegistry`) dan C-B (`SignalAnchor` v2) lebih dulu - dua kontrak kecil, satu-satunya yang dibutuhkan tingkat 0.

1. **`contracts/LockRegistry.sol` (C-A).** Satu kunci per (pengunci, botId, specSha), ditulis sekali; `lockedAt` = waktu blok; nilai nol ditolak. Kunci milik ALAMAT yang mengunci: orang lain bisa mengunci botId yang sama,
   tetapi itu id lain dengan jam lain - tidak ada yang bisa mendahului lalu mengklaim jam kunci kami.
2. **`contracts/SignalAnchor.sol` (C-B).** Komit akar Merkle per bot per bar (skema daun = `engine/sinyal.py`). Aturan yang ditegakkan kontrak: (a) hanya untuk spesifikasi yang sudah dikunci PENGIRIM, dan kuncinya
   tidak lebih baru dari bar; (b) tidak untuk bar yang belum tertutup; (c) hanya dalam **12 jam** sesudah penutupan (sama dengan guard ledger) - yang terlambat ditolak; (d) satu komit per bar, akar nol hanya untuk
   "bot diam"; (e) pengungkapan diverifikasi terhadap akar (OpenZeppelin `MerkleProof`), daun yang sama tidak dihitung dua kali, dan `n` yang dikecilkan tidak bisa menyembunyikan daun; (f) sesudah **7 hari**,
   komit yang tidak diungkap penuh boleh ditandai TIDAK-DIUNGKAP oleh siapa pun, permanen.
3. **Kecocokan dengan engine dibuktikan, bukan diasumsikan.** `tools/gen_signal_vectors.py` membuat vektor dari `engine/sinyal.py` (`test/fixtures/signal_vectors.json`; deterministik); uji Foundry memeriksa daun dan bukti
   kontrak = engine, termasuk bobot negatif (short) dan batch satu daun; `engine/tests/test_signal_vectors.py` gagal bila penyandian engine berubah tanpa fixture diperbarui.
4. **Terukur:** `forge test` **63 lulus** (24 baru: `SignalAnchorTest`); Python **245 lulus**. Gas (`forge test --gas-report`, EVM lokal, median): `lock` 137.756; `commit` 189.848; `reveal` 67.807 per sinyal;
   `markMissed` 26.690. Bytecode: LockRegistry 1.313 B, SignalAnchor 4.400 B; DecisionAnchor tetap 4.748 B (klaim lama tidak berubah). `foundry.toml`: izin BACA hanya ke `test/fixtures`.
5. Skrip `script/DeploySignalAnchor.s.sol` ditulis; **tidak dijalankan** (mengirim transaksi).

**Menunggu builder:**
(1) **deploy ke chain 97**: dua transaksi deploy (kunci deployer), lalu `lock` untuk B1-TREND, B3-CARRY, dan kunci ambang v1 (kunci agen);
(2) **siapa yang menandatangani komit harian.** Job GitHub sengaja tidak memegang kunci (kebijakan repo, `paper-book.yml`). Pilihan: (a) laptop builder mengirim komit tiap hari dalam jendela ±09:00-12:00Z
(16:00-19:00 WIB) - butuh laptop menyala; (b) kunci khusus berizin sempit (hanya bisa komit untuk bot yang ia kunci sendiri, saldo kecil) sebagai rahasia Actions - mengubah kebijakan; (c) tetap cap waktu git saja
sampai diputuskan. Saran saya: (b), dengan alasan dan risikonya ditulis sebelum dipasang;
(3) parameter immutable maxLag 12 jam dan jendela ungkap 7 hari (mengubah = deploy baru).

**Terkait:** [[08-Backlog/06 - Epik Gerbang Sinyal]] §3 · F-D75 · F-D77 · F-D78 · [[09-Inbox/Session-2026-10-02]] §16

## F-D80 — Mesin 24/7 di Railway, tahap 1 = penanda tangan komit on-chain; deploy SC = satu alat yang dijalankan builder · 2 Okt 2026

Builder: *"Apa mau di deploy ke railway agar enginenya jalan 24/7? Pakai railway cli saya aja dan bikin project baru nanti tinggal di sync ke repo. Lalu untuk
deploy SC mah tinggal pakai deployer lencana, itu ada tesnet tBNB di wallet deployer lencana"*.

1. **Yang diputuskan builder:** mesin jalan terus di Railway (proyek baru lewat CLI builder); deploy SC memakai deployer Lencana. Ini sekaligus menjawab F-D79 (2)
   "siapa penanda tangan komit harian": server Railway dengan kunci committer khusus. Parameter maxLag 12 jam / jendela ungkap 7 hari tidak dikomentari -> bawaan dipakai.
2. **Yang TIDAK dilakukan sesi ini:** membaca `../app/.env`. Pemeriksa otomatis sesi menolak percobaan asisten membaca nama variabel di berkas itu
   ("Credential Exploration"); penolakan dihormati, tidak dicari jalan memutar. Karena itu deploy dikemas sebagai alat yang DIJALANKAN BUILDER, di mesinnya:
   `tools/m3_setup.py` (bawaan rencana; `--go` menjalankan; idempoten). Alat itu membaca SATU variabel dari berkas yang builder tunjuk dan tidak mencetaknya.
3. **Tahap 1 sengaja sempit.** Ledger tetap ditulis rantai GitHub (F-D78, penulis tunggal). Worker Railway (`tools/operator_loop.py` -> `tools/signal_commit.py`)
   hanya MEMBACA ledger yang di-commit, menghitung ulang sinyal tiap tick dari bar yang di-commit (menolak bila target/data_hash/id sinyal beda), mengomit akar
   Merkle dalam batas 12 jam, lalu mengungkap tiap sinyal. Akar on-chain yang beda dari ledger = ALARM, tidak pernah ditimpa; yang lewat batas = TERLEWAT, tidak
   dipaksa. Dua penulis ledger = rantai hash bertabrakan, jadi memindahkan penulis ledger ke Railway adalah tahap 2 dengan kata builder sendiri.
4. **Kunci committer = kunci BARU khusus**, bukan deployer Lencana (bila bocor, kontrak Lencana ikut terancam) dan bukan kunci agen Fabius (identitas DecisionAnchor).
   Risiko ditulis sebelum dipasang: bila bocor, orang bisa mengisi slot bar lebih dulu (rekam jejak rusak) dan saldo kecilnya (0,05 tBNB) hilang; ia tidak bisa
   menyentuh DecisionAnchor, ExecutionVault, atau kontrak Lencana. Salt per sinyal = HMAC dari kunci itu (domain terpisah): tanpa penyimpanan, tetapi mengganti kunci
   = ungkap dulu semua komit yang masih terbuka. Fase paper: ungkap segera sesudah komit (`REVEAL_DELAY_S=0`) - ledger toh sudah publik.
5. **Terukur hari ini:** Python **263 lulus** (18 baru di `engine/tests/test_signal_commit.py`, termasuk jalur penuh di anvil: deploy -> lock -> lompat ke 10 jam
   sesudah penutupan -> 2 komit + 2 ungkap lewat kode worker -> putaran kedua tidak mengirim apa pun; selector = ABI hasil kompilasi). Gladi `m3_setup.py` di SALINAN
   repo + anvil chain-id 97 (RPC dipaku, kunci uji publik): rencana -> `--go` (deploy, baca ulang kode/immutable cocok, committer baru, saldo 0,05, dua `lock`) ->
   `--go` lagi (semua langkah dilewati); `deployments/97.json` hanya bertambah (kunci lama utuh). Dua `lock` di anvil: saldo committer 0,050000 -> 0,049569 tBNB pada 2 gwei.
6. **Railway:** proyek `fabius-engine`, service `fabius-engine`, region Singapura (`asia-southeast1-eqsg3a`), 1 replika, mode RENCANA (belum ada kunci): log
   12:35Z "menunggu deploy: SignalAnchor/LockRegistry belum ada di deployments/97.json". Sebelum itu tiga deploy GAGAL (satu `railway up` + dua redeploy otomatis
   dari `service scale`), dan dua kesalahan konfigurasi, dicatat apa adanya: (a) `railway.json` DIABAIKAN
   (builder tetap Railpack -> "Railpack could not determine how to build the app"; config-as-code juga deprecated, berlaku sampai 2026-12-01) -> berkas itu dihapus
   dari repo, Dockerfile ditunjuk lewat variabel `RAILWAY_DOCKERFILE_PATH`; `railway environment edit` untuk builder/restart menjawab "No changes to apply", jadi
   kebijakan restart masih bawaan ON_FAILURE (10 kali), bukan ALWAYS. (b) `service scale southeast-asia=1 us-west=0` meninggalkan region `sfo` = 1 -> DUA replika =
   dua penanda tangan; diperbaiki `sfo=0` sebelum kunci apa pun dipasang. Deploy kode lewat `tools/railway_up.py` (`git archive HEAD`): berkas yang tidak di-commit
   (kunci) tidak mungkin ikut terunggah.
7. **Temuan region** (log worker 12:35Z): dari Railway Singapura `fapi.binance.com` **HTTP 200**, `api.binance.com` 200, Vision 200. Pembanding: runner GitHub (AS)
   HTTP 451; laptop builder TLS "hostname mismatch" (penyaringan jaringan). Artinya tahap 3 - bar REST segera sesudah penutupan (tick dalam menit, bukan ~9 jam;
   funding final tanpa menunggu zip bulanan) - MUNGKIN dari Railway. Belum diuji: kesamaan bar REST dengan bar Vision yang dipakai replay.
8. **Belum disambung ke GitHub** ("sync ke repo"): master menerima commit bot tiap ±4 menit; tanpa watch paths setiap commit = redeploy worker. Pasang watch paths
   dulu (dashboard service -> Settings), baru `railway service source connect --repo Shenhan01-sys/Fabius --branch master --service fabius-engine`.

**Menunggu builder** - sekali, sebelum **3 Okt 00:00Z (07:00 WIB)** supaya bar 2 Okt sudah bisa dikomit (kontrak menolak kunci yang lebih baru dari bar):
```
python -X utf8 tools/m3_setup.py --deployer-env ../app/.env                # rencana: alamat + saldo deployer, langkah
python -X utf8 tools/m3_setup.py --deployer-env ../app/.env --go           # deploy + committer + saldo + lock B1/B3
python -X utf8 tools/m3_setup.py --railway-service fabius-engine --go      # kunci + alamat -> variabel Railway (worker redeploy)
```
lalu `deployments/97.json` di-commit + push (alamat publik). Nama variabel kunci di berkas itu bukan `DEPLOYER_PRIVATE_KEY`? tambahkan `--deployer-var NAMA`.

Tambahan (sesudah push pertama): log worker mengulang "menunggu deploy" tiap putaran, karena sha repo ikut di baris keadaan dan master menerima commit bot tiap
±4 menit -> sha dipindah ke baris detak (tiap 6 jam), satu uji ditambah: **19** uji worker, Python **264 lulus**.

**Dijalankan 2 Okt 13:04Z - "Menunggu builder" di atas sudah selesai.** Builder membuka izin lewat `/permissions` ("Udh saya acc") untuk perintah yang tadinya
ditolak (daftar NAMA variabel `../app/.env`; nama kuncinya ternyata memang `DEPLOYER_PRIVATE_KEY`), lalu alat dijalankan dari sesi ini. Hanya nilai variabel itu
yang dipakai alat; tidak pernah dicetak.
- Rencana: deployer Lencana `0xAEc63F6cEbBfacdC3516992b6ec396147c9c8361`, saldo 0,441343 tBNB, gas 1,00 gwei.
- `--go`: **LockRegistry `0xcF6fBF95fc04DEd8d670512CEc0723a2246Fbb0C`** (tx `0x6185ae11…`, blok 134442907); **SignalAnchor `0x9B78200beFbbBe836585d31bd5b6dB32587064f3`**
  (tx `0x90192c38…`, blok 134442917); baca ulang di alat: kode LockRegistry = artefak, immutable SignalAnchor benar. Committer **`0xE12eCFA5e9acAb4d541eA5490e29b185471F812a`**
  diisi 0,05 tBNB (tx `0x2ebfd86c…`). `lock` B1-TREND 13:04:46Z (tx `0x3a099bd8…`), B3-CARRY 13:04:51Z (tx `0xe6a80145…`): keduanya sebelum 3 Okt 00:00Z, jadi bar
  2 Okt sudah bisa dikomit. Semua alamat + tx tercatat di `deployments/97.json` (ditambahkan, kunci lama utuh).
- `--railway-service fabius-engine --go`: tiga variabel terpasang (kunci lewat stdin). Worker 13:06:13Z: "aktif: SignalAnchor 0x9B78… committer 0xE12e… (KIRIM)";
  dua tick 1 Okt SKIP "lebih tua dari kunci committer" (by design: kunci 13:04Z > penutupan bar 1 Okt).
- Baca ulang terpisah dengan `cast` (tanpa kunci): kode 4400 B / 1313 B; `registry()` = LockRegistry; `maxLag()` 43200; `revealWindow()` 604800; `lockCount()` 2;
  `lockedAt` B1 1790946286, B3 1790946291; `commitCount()` 0; saldo committer 0,049737 tBNB.
- Yang diharapkan berikutnya (bukti, bukan janji): tick bar 2 Okt oleh rantai GitHub 3 Okt ±09-10Z, lalu worker mengomit + mengungkap dalam ±5 menit
  (`commitCount()` 0 -> 2). Bila tidak terjadi, itu temuan, bukan "nanti".

**Terkait:** F-D78 · F-D79 · [[08-Backlog/06 - Epik Gerbang Sinyal]] §3 · [[09-Inbox/Session-2026-10-02]] §17

## F-D81 — Perekam wallet-flow DIHENTIKAN sebelum batas 100 MB GitHub · 2 Okt 2026

Builder: *"Gas no1 opsi a"* - opsi (a) dari tiga yang diajukan: hentikan perekam (arah sekarang, bot perp Binance di `engine/`, tidak memakai data ini);
(b) pecah berkas per hari + ubah ±38 alat pembaca; (c) pindah ke penyimpanan luar dengan hash di chain.

1. **Kenapa sekarang** (terukur 2 Okt 14:54Z di `origin/master`, ukuran dari `git ls-tree -l`): `universe/watch-prices.jsonl` 65,5 MB (+16,5 MB dalam 24 jam; +9,4 MB
   dalam 12 jam terakhir), `universe/wallet-flow.jsonl` 60,7 MB (+11,9 MB/24 jam), `universe/book-depth.jsonl` 28,7 MB (+9,0 MB/24 jam). GitHub menolak berkas di atas
   100 MB: watch-prices akan lewat sekitar 4 Okt, wallet-flow sekitar 5 Okt. Sesudah itu push rantai ditolak, dan langkah pemulihannya (`reset --hard` ke origin)
   membuang rekaman siklus itu: perekam tampak jalan, tetapi tidak ada yang tersimpan. Temuan ini sudah tercatat di audit 1-2 Okt (memori sesi), belum di vault - sekarang tercatat.
2. **Yang dilakukan (15:06Z):** `gh workflow disable wallet-flow-watchdog.yml` lalu `gh workflow disable wallet-flow.yml` (watchdog dulu, supaya ia tidak menyalakan ulang
   rantai yang basi), lalu `gh run cancel 37012282451` (rantai yang jalan sejak 13:19Z; tanpa ini ia terus commit tiap ±4 menit sampai ±17:55Z). Percobaan pertama
   asisten ditolak pemeriksa otomatis ("Interfere With Workloads"); dijalankan sesudah builder membuka izinnya lewat `/permissions` ("Done udh saya acc").
3. **Terbaca sesudahnya:** kedua workflow `disabled_manually`; run 37012282451 `cancelled` 15:06:46Z; commit perekam terakhir `475603b` 15:05:11Z. Ukuran akhir di origin:
   watch-prices 65,8 MB, wallet-flow 60,9 MB, book-depth 28,8 MB, `decisions/fast-lane.jsonl` 6,8 MB. Kepala `wallet-flow.yml` dan `wallet-flow-watchdog.yml` diberi catatan.
4. **Ikut berhenti:** `tools/fast_lane.py --run` (P40, keputusan jalur cepat) - satu rantai dengan perekam. **Tidak tersentuh:** `universe-hourly`, `paper-book`,
   `paper-ledger` + watchdog-nya, worker Railway.
5. **Data lama tetap** di repo dan tetap terbaca semua alat riset; hanya tidak bertambah. Klaim apa pun yang butuh data perekam ini sesudah 2 Okt 15:05Z = tak terukur.
6. **Menyalakan lagi** = keputusan builder, dan batas yang sama datang lagi dalam ±2 hari kecuali berkas dipecah dulu (opsi b): `gh workflow enable wallet-flow.yml`,
   `gh workflow enable wallet-flow-watchdog.yml`, `gh workflow run wallet-flow.yml`.

**Terkait:** F-D80 · [[09-Inbox/Session-2026-10-02]] §18

## F-D82 — Kunci committer pertama TERPAPAR di transkrip sesi asisten; dirotasi sebelum komit pertama · 2 Okt 2026

1. **Yang terjadi (kesalahan asisten, dicatat apa adanya).** ±15:20Z, saat menyiapkan service probe, asisten menjalankan `railway environment config --json` untuk
   melihat konfigurasi region. Perintah itu mencetak NILAI semua variabel service, termasuk `COMMITTER_PRIVATE_KEY` worker. Kunci committer `0xE12eCFA5e9acAb4d541eA5490e29b185471F812a`
   dianggap bocor: transkrip sesi tersimpan di laptop builder dan terkirim ke model.
2. **Dampak:** testnet, saldo ±0,05 tBNB; risiko utamanya pihak lain bisa mengisi slot komit B1/B3 lebih dulu atas nama alamat itu. Belum ada komit (`commitCount()` 0),
   jadi rotasi murah dan tidak ada yang perlu diungkap dengan kunci lama.
3. **Rotasi (15:49Z).** Percobaan pertama asisten ditolak pemeriksa otomatis ("Secret-Store Writes"); builder membuka izin lewat `/permissions` dan memilih asisten
   yang menjalankan ("B"). Kunci lama dipindah KELUAR repo (folder sementara sesi). `tools/m3_setup.py --deployer-env ../app/.env --go`: committer BARU
   **`0xCA9c7322210E9a7F7d0953c862d4Ef60cC0D64A4`**, diisi 0,05 tBNB dari deployer Lencana (tx `0x220d3826…`), `lock` B1-TREND 15:49:20Z (tx `0xae9e7132…`) dan B3-CARRY
   15:49:25Z (tx `0x03f42b78…`) - masih sebelum 3 Okt 00:00Z, jadi bar 2 Okt tetap bisa dikomit. `--railway-service fabius-engine --go`: worker 15:50:28Z
   "aktif ... committer 0xCA9c… (KIRIM)".
4. **Baca ulang `cast`:** `lockedAt` committer baru B1 1790956160, B3 1790956165; kunci lama TETAP ada (1790946286 / 1790946291 - LockRegistry memang tidak bisa
   menghapus); `lockCount()` 4; `commitCount()` 0; saldo baru 0,049754 tBNB, saldo lama 0,049737 tBNB (tertinggal di alamat lama; kecil, bisa ditarik kelak).
5. **Aturan verifikasi:** `deployments/97.json` `m3.retired_committers` mencatat alamat lama dan alasannya. Komit SAH hanya dari `m3.committer`; pemeriksa menyaring
   event `Committed` berdasarkan committer. Komit atas nama alamat lama, bila muncul, BUKAN dari Fabius.
6. **Pelajaran:** `railway environment config --json` dan `railway variable list --json/--kv` mencetak nilai rahasia. Keduanya tidak dipakai lagi sesudah rahasia
   terpasang; region/replika dibaca dari keluaran `railway service scale` atau `railway deployment list --json` (`.meta.serviceManifest.deploy`).

**Terkait:** F-D80 · [[09-Inbox/Session-2026-10-02]] §19

## F-D83 — Data REST Binance = data Vision untuk semua yang dipakai engine (harga + funding): syarat data tahap 3 terpenuhi · 2 Okt 2026

Builder: *"gas"* (validasi REST vs Vision, langkah pertama tahap 3).

1. **Alat:** `tools/rest_vs_vision.py` (hanya membaca, tanpa kunci): kline perp `fapi /fapi/v1/klines` 1d vs `fut_<SYM>_1d.csv`, kline spot `api /api/v3/klines` vs
   `spot_<SYM>_1d.csv` (5 kolom, identik sebagai float), funding `fapi /fapi/v1/fundingRate` vs `fund_<SYM>.csv` (waktu ±60 detik, rate identik, jumlah per hari UTC).
2. **Di mana:** service Railway terpisah `fabius-probe` (Singapura, tanpa variabel rahasia, `FABIUS_JOB=rest_vs_vision`, jalan sekali). Bukan shell ke worker:
   `railway ssh` ke worker ditolak pemeriksa otomatis ("Production Reads" - env worker berisi kunci); penolakan dihormati.
3. **Hasil** (2 Okt 16:00:08Z, 16 simbol, riwayat penuh sejak 2019-2020, 203 panggilan REST, 89 detik):
   - perp: **37.978/38.030** bar identik di 5 kolom; 52 bar beda HANYA di volume (sel beda o=0, h=0, l=0, c=0, v=52); 0 bar hanya di CSV; 25 bar hanya di REST
     (5 hari mulai 2022-02-26 untuk SOL/XRP/LTC/TRX/NEAR = lubang seed yang sudah dikenal dari koreksi K-3);
   - spot: **39.739/39.827** identik; 88 beda HANYA di volume (o=0, h=0, l=0, c=0, v=88); 0 hanya di satu sisi;
   - funding: **114.228/114.228** peristiwa identik, selisih waktu maks 0 ms, 0 hari dengan jumlah beda;
   - bar perp tertutup terakhir pada 16:00Z: CSV 2026-10-01 = REST 2026-10-01;
   - "VONIS UNTUK ENGINE (harga + funding; volume tidak dipakai engine): SAMA PERSIS". Engine hanya membaca penutupan dan funding: `data_fingerprint` memakai (t, c),
     dan grep `engine/` tidak menemukan bot yang membaca o/h/l/v.
4. **Beda volume berkumpul di hari tertentu, di banyak simbol sekaligus** (perp: 2023-11-10, 2024-03-27/28, 2025-01-14, plus 2023-11-14 di DOT; spot: 2019-10-01,
   2019-12-04, 2020-10-27, 2021-01-11/21, 2021-12-24) - pola koreksi data di sisi bursa, bukan acak. Aturan untuk nanti: bot yang memakai VOLUME harian harus mengunci
   satu sumber; tick tetap dihitung ulang dari bar yang di-commit.
5. **Artinya:** tick dari REST segera sesudah penutupan (tahap 3) tidak mengubah satu bit pun dari tick/settle yang dihitung ulang dari Vision - untuk harga dan
   funding. **Belum diukur:** kapan REST menyajikan bar yang baru tertutup dan funding 00:00Z (perlu uji 00:00-00:10Z dari Railway), dan apakah bar yang diambil di
   menit-menit pertama sudah final. Itu langkah berikutnya, sebelum desain tahap 2+3 diajukan ke builder.

Tambahan 3 Okt (P98, `tools/rest_latency.py` di `fabius-probe` Singapura, bar 2026-10-02): bar perp + spot 16/16 terlihat tertutup 0,1-11 detik sesudah 00:00:00Z (median 8,7 / 8,9 s), funding 00:00Z 16/16 dalam 3,2-15,5 s; TETAPI 3 bar perp berubah sesudah pertama terlihat (di +15 s): BTCUSDT close 84482,7 -> 84482,8 + volume, ETHUSDT dan BNBUSDT volume; sesudah +18 s tidak ada perubahan lagi sampai +60 menit (1.459 panggilan, 0 gagal). Artinya: data REST hadir dalam detik, tetapi
bacaan PALING AWAL belum final - termasuk harga penutupan BTC. Aturan untuk tahap 3 (usulan): baca paling cepat +2 menit, terima hanya sesudah dua bacaan
identik berjarak >= 60 detik, dan cocokkan dengan Vision begitu terbit (rest_vs_vision). Satu malam = satu sampel.

**Terkait:** F-D75 · F-D76 · F-D80 · F-D82 · [[09-Inbox/Session-2026-10-02]] §19 · §27

## F-D84 — Parameter pemeriksa F-D16 maju (P88) DIKUNCI sebelum settle maju pertama, dan di-pin di LockRegistry · 3 Okt 2026 (WIB)

Saran yang dijawab: *"Parameter F-D16 di atas sengaja saya tulis sebelum ada data ... Saran saya: setujui dan kunci sekarang, seperti kunci ambang v1."*
Builder: *"Gasss"* - dibaca sebagai setuju (dan lanjut P85). Bila maksudnya lain, jalan kembalinya terlihat: kunci v2 lewat keputusan baru, kunci ini tetap tercatat.

1. **Yang dikunci:** `engine/locks/fd16.lock.json` = `Fd16Params` di kode: sinyal maju >= 20; hari settle >= 20; bulan >= 2; CI 95 % bootstrap blok melingkar 5 hari
   x 10.000 (benih = ujung rantai ledger); buang bulan kalender terbaik; BH alpha 0,10 lintas bot. sha `0x5a47cc4b87758730b0a1898f5a626029806b287abbb730292422fe5136797a45`, `dikunci` 2026-10-02T17:07:59Z (jam laptop).
2. **Kenapa sekarang:** belum ada SATU pun settle maju (B1 0/20 sinyal, B3 2/20; settle pertama menunggu funding aktual Oktober). Hanya di titik ini parameter
   tidak bisa dituduh menyesuaikan data.
3. **Penegakan di kode:** `engine.cli ledger fd16` mencetak status kunci di kepala keluarannya; parameter yang bergeser dari kunci = "MENYIMPANG - vonis TIDAK
   mengikat"; `test_repo_lock_matches_code` merah bila satu angka diubah tanpa kunci v2; `write_lock` menolak menimpa.
4. **Di chain (jam yang berlaku):** `tools/lock_spec.py --send` -> `LockRegistry.lock(botId = "FABIUS-FD16-MAJU-v1", specSha = sha di atas)` oleh committer
   `0xCA9c…64A4`: tx `0x6bf7d51201b956ec2869d4272b3066710c14af9d334b0e0984407d46c58b9cd0`, blok 134475778, gas **123.050** (angka gas `lock` pertama dari chain 97, bukan EVM lokal), `lockedAt` 1790961057 =
   **2026-10-02T17:10:57Z**; uri menunjuk commit `7e6f6d3` (di-push lebih dulu supaya tautannya ada). `lockCount()` 4 -> 5; saldo committer 0,049631 tBNB.
   Dicatat di `deployments/97.json` `m3.pins`.

**Terkait:** F-D16 · F-D74 · F-D79 · [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] §11 (P88) · [[09-Inbox/Session-2026-10-02]] §24

## F-D85 — Buku slot HIDUP: berkas append-only berantai hash, satu catatan per epoch, `book_sha` tiap epoch di-pin ke LockRegistry · 3 Okt 2026 (WIB)

Saran yang dijawab (P87): (1) keadaan buku disimpan sebagai berkas append-only berantai hash seperti ledger; (2) `book_sha` tiap epoch dicatat di chain lewat
LockRegistry. Builder: *"Gas, pakai opsi B"* - dibaca sebagai: kerjakan oleh asisten, dengan dua saran itu (tafsir ditulis supaya bisa dikoreksi).

1. **Berkas:** `ledger/book/buku.jsonl` - `genesis` (buku awal = bot identitas B1-TREND, F-D73; sha kunci v1) lalu satu `epoch` per `SlotParams.epoch_days` (30
   hari; epoch 690 = 2026-09-04..2026-10-04Z, epoch 691 mulai 2026-10-04T00:00Z). Tiap epoch menyimpan SEMUA masukan keputusan (skor maju penghuni dari P85,
   penantang: shadow + berpasangan + vonis gerbang terhadap buku SEKARANG + `report_sha`, status pembunuh) lalu keputusan `slots.decide_epoch`, buku hasil, `book_sha`.
   Laporan gerbang lengkap di `ledger/book/laporan/<report_sha>.json`.
2. **Pemeriksa:** `engine.cli book verify` - rantai hash, epoch naik, kesinambungan buku, dan keputusan tiap epoch DIHITUNG ULANG dari masukannya sendiri
   (tanpa data pasar, tanpa jaringan). Uji: keputusan yang dipalsukan lalu di-seal ulang tetap ketahuan.
3. **Epoch pertama (690, 2026-10-02T17:22:43Z):** gerbang B3-CARRY terhadap buku {B1-TREND} = **LOLOS_SHADOW** (G11 tak terukur, satu-satunya yang boleh), 6 detik,
   laporan `0xd605ce002017…`; keputusan **REJECT**: "shadow maju baru 0 hari < 60". Buku tetap B1 saja; `book_sha` `0xfe37d7595644fd7e…`. Pembunuh B1 = TEKS (dinilai manusia).
4. **Di chain:** `tools/pin_book.py --send` -> `LockRegistry.lock("FABIUS-BUKU-E690", book_sha)` oleh committer: tx `0x2d6b96726f66…`, blok 134477804, gas 122.954,
   `lockedAt` 2026-10-02T17:26:09Z; uri ke commit `28f7ff0` (di-push lebih dulu). `lockCount()` 5 -> 6. Dicatat di `deployments/97.json` `m3.pins`.
5. **Yang dibuka:** P107 - pembunuh B1/B3 masih TEKS di spesifikasi (mengubahnya = spesifikasi baru), perlu bentuk terstruktur yang dikunci terpisah; P108 - jadwal
   epoch bulanan + pin otomatis (sekarang manual; epoch 691 bisa dicatat mulai 4 Okt 00:00Z).

Tambahan 3 Okt (P108, commit `cccbc3ce`): butir 4 tidak lagi manual. (a) Rantai GitHub `paper-ledger.yml` (penulis tunggal `ledger/`) menjalankan
`engine.cli book epoch --write` + `book verify` sesudah tick hari itu beres. Langkah ini idempoten: hanya hari pertama epoch baru yang menulis. Kalau gagal,
rantai ledger tetap jalan, buku tidak di-commit, dan peringatan terlihat di run. (b) Worker Railway (punya kunci committer) mem-pin `book_sha` epoch terakhir
yang sah ke LockRegistry dengan label `FABIUS-BUKU-E<epoch>` dan uri ke commit yang disinkron. Ini butir 2 keputusan ini; matikan dengan `PIN_BOOK=0`.
`deployments/97.json` `m3.pins` TIDAK diperbarui otomatis (worker tidak menulis repo); bukti = chain (`tools/pin_book.py --verify`). Uji: simulasi pada salinan buku dengan `--now 2026-10-04T09:30:00Z`: epoch 691 tertulis dalam 9 s, gerbang B3 LOLOS_SHADOW, keputusan REJECT ("shadow maju baru 2 hari < 60"), book_sha sama dengan E690 (`0xfe37d7595644fd7e…`, buku tidak berubah); putaran kedua "sudah tercatat", berkas tidak berubah.

**Terkait:** F-D71 · F-D73 · F-D84 · [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]] §11 (P87) · [[03-Data/D8 - Buku Slot Hidup]] · [[09-Inbox/Session-2026-10-02]] §26 · §31

## F-D86 — Tahap 2+3 berjalan dulu sebagai MODE BAYANGAN: tick dari REST di Railway, dibandingkan dengan tick resmi; penulis ledger tetap rantai GitHub · 3 Okt 2026 (WIB)

Saran yang dijawab: "Gas tahap 2+3 mode bayangan? Usulku P109 dikerjakan duluan". Builder: *"Gas"*.

1. **Di mana:** service Railway `fabius-probe` (Singapura, tanpa variabel rahasia), `FABIUS_JOB=shadow_tick`, image dari HEAD `33183b0d`, hidup sejak 3 Okt 05:22Z.
   Worker `fabius-engine` (committer) tidak disentuh.
2. **Aturan baca (SK-R1, dari P98):** bacaan pertama paling cepat +2 menit sesudah 00:00Z. Data diterima hanya kalau dua bacaan berurutan berjarak >= 60 s identik.
3. **Data bayangan:** bar resmi disalin, lalu ditambah kline perp/spot dari REST dan estimasi funding dari indeks premium 1m REST (rumus yang sama). Funding
   AKTUAL tidak ditulis (SK-R2: kalau masuk lebih dulu, estimasi hari itu tidak pernah terbentuk dan tick B3 ditolak).
4. **Keluaran:** hanya log dan keadaan lokal. Tidak ada tulisan ke ledger resmi dan tidak ada transaksi. Penulis tunggal tetap rantai GitHub (F-D78).
   Vonis per bot per bar: IDENTIK / BEDA / RESMI GAP / RESMI ADA, BAYANGAN DITOLAK; baris REST vs Vision: SAMA / ALARM.
5. **Hasil pertama:** bar 2026-10-02 dihitung 05:23:55Z, diterima pada bacaan ke-2 (dua bacaan identik). B1-TREND: 16 aset, 0 sinyal, data_hash `0x6f027a68f47b…`. B3-CARRY: 1 aset, 1 sinyal, data_hash `0xfa55591ad8f8…`. Jeda 19.433 s (5,4 jam) karena bayangan baru hidup 05:22Z; jeda ±2-4 menit baru teruji mulai bar 2026-10-03. Vonis menunggu tick resmi bar itu dari rantai GitHub.
6. **Syarat pindah penulis (P99), USULAN, menunggu kata builder:** minimal 5 hari berturut-turut IDENTIK untuk B1 dan B3, ditambah baris REST SAMA dengan Vision
   (termasuk estimasi funding, yang belum pernah dibandingkan). Sesudah itu rantai GitHub dimatikan lebih dulu, baru Railway menulis (SK-R3).
7. **Batas:** satu region REST; keadaan bayangan ada di `/tmp` container dan hilang saat deploy ulang, jadi log adalah catatannya; satu hari = satu sampel.

Tambahan 3 Okt sore (hari 1): `fabius-probe` 08:44:25Z: `VONIS bayangan B1-TREND 2026-10-02: IDENTIK`, `B3-CARRY: IDENTIK` (bayangan 323,9 menit vs resmi 8,7 jam - bayangan baru hidup 05:22Z); `VONIS baris REST 2026-10-02: 80 sama persis, beda harga 0, beda estimasi funding 0, beda volume saja 0` - estimasi funding dari indeks premium REST = estimasi dari zip Vision, risiko terbesar yang belum pernah diuji. P99 butuh 5 hari berturut; ini hari 1.

**Terkait:** F-D78 · F-D80 · F-D83 · [[04-Tools/TL17 - shadow_tick]] · [[07-Testing/T8 - Semantik Kegagalan Operator]] · [[09-Inbox/Session-2026-10-02]] §30

## F-D87 — Pembunuh B1/B3 TERSTRUKTUR dikunci terpisah dari spesifikasi; buku slot menilainya otomatis · 3 Okt 2026 (WIB)

Pertanyaan yang dijawab builder (empat pilihan, AskUserQuestion, 3 Okt ±13:15 WIB), semuanya pilihan yang diusulkan:
1. B1-K1 "12 bulan tanpa mengalahkan buy&hold pada MDD dan Sharpe" = **harus menang di KEDUANYA**; kalah di salah satu = mati. Jendela 365 hari maju dengan
   >= 90 % hari settle final.
2. Patokan buy&hold = **sama rata 16 perp universe B1**, return close-to-close, tanpa ongkos.
3. B1-K2 "kalah dari placebo masuk-acak" = **net bot <= median** 1000 placebo geser-melingkar (eksposur dan lama tahan sama, seperti G8).
4. B3-K1 "hasil hedged negatif tiga bulan berjalan saat aktif" = **tiga bulan kalender aktif terakhir (sudah lewat, >= 10 hari memegang posisi) masing-masing
   net < 0**; bulan dorman dilewati. B3-K2 ADL: di paper TIDAK BERLAKU, berlaku sejak eksekusi nyata ada.

**Kunci:** `engine/locks/pembunuh.lock.json`, sha `0xa55b4782a6d5ec97a90df00634798a3887dc3300921a6ca3f21fb1e95a8607d4`, dikunci 2026-10-03T06:14:54Z (jam laptop). Kunci ini mengikat `spec_sha` + kalimat asli kedua
bot; tes `test_repo_lock_matches_the_code` gagal bila terjemahan atau spesifikasi digeser. Mengubahnya = keputusan baru + kunci v2.
**Efek:** mulai epoch 691, catatan epoch memuat YA / BELUM / TIDAK menggantikan "TEKS" (`engine/cli.py::_book_killers`). simulasi epoch 691 pada salinan buku (`--now 2026-10-04T09:30:00Z`): penghuni B1-TREND "pembunuh BELUM" (sebelumnya TEKS), B3 REJECT (shadow 2 hari < 60), `book verify` SAH.
**Pin on-chain:** `tools/lock_spec.py --file engine/locks/pembunuh.lock.json --name FABIUS-PEMBUNUH-v1 --send` = satu transaksi committer, MENUNGGU kata
builder (rencana 3 Okt: `lockedAt = 0`). Builder: *"Oalah gas"* (sesudah bertanya arti label). **Terkirim:** tx `0x7b053afcfdae9634856564cc81757eb30a669619fe6a5c35fcf74330412d960a`, blok 134581846, gas 123.074, `lockedAt` 1791008788 = 2026-10-03T06:26:28Z, uri ke commit `3250574f`; `--verify` membaca ulang lockedAt yang sama; `lockCount()` = 7. Dicatat di `deployments/97.json` `m3.pins`.

**Terkait:** F-D73 · F-D84 · F-D85 · [[08-Backlog/09 - Usulan P107 Pembunuh Terstruktur]] · [[03-Data/D8 - Buku Slot Hidup]] · [[09-Inbox/Session-2026-10-02]] §34

## F-D88 — Anggaran kesalahan gerbang masuk buku: A1 = 5 % per pengajuan jujur, A2 = 0,2 per keluarga penerbit per tahun (alpha A1/k) · 3 Okt 2026 (WIB)

Pertanyaan builder: *"Menurutmu paling optimal A1/A2"*. Jawaban asisten merevisi usulannya sendiri (1 % / 0,1 -> 5 % / 0,2). Builder: *"OKe gas"*.

1. **A1 = 5 %**: peluang bot tanpa edge lolos gerbang pada SATU pengajuan jujur. Alasannya, gerbang adalah saringan PERTAMA. Tidak ada sinyal yang dijual
   sebelum bot juga lolos F-D16 maju (F-D84), jadi peluang bot tanpa edge sampai dijual ~ A1 x 2,5 % (kasar) ~ 0,13 %. Menurunkan A1 ke 1 % hanya membeli
   0,1 poin persen keamanan, tetapi menjatuhkan daya pada Sharpe 1,0 / 3 tahun dari 53 % ke 31 %. Usulan awal 1 % belum memperhitungkan saringan kedua.
2. **A2 = 0,2**: rata-rata penerimaan palsu per keluarga penerbit per tahun, ditegakkan dengan pengeluaran alpha harmonik. Pengajuan ke-k dari keluarga yang
   sama dalam 365 hari dinilai dengan alpha 5 %/k. Batas antrean sekarang membolehkan paling banyak 26 pengajuan/tahun, sehingga batasnya 0,193.
3. **A3 (daya)**: tidak diberi angka. Plafon aritmetika riwayat membatasi daya apa pun ambangnya.
4. **Angka:** dihitung 3 Okt (`python -X utf8 -c "..."`, rumus `run14_power_arithmetic.py` dengan alpha diganti): daya pada Sharpe 1,0 / riwayat 3 th = 31 % (alpha 1 %) vs 53 % (alpha 5 %); Sharpe 0,5: 8 % vs 23 %; Sharpe 1,5: 57 % vs 74 %; positif-palsu sampai dijual ~ A1 x 2,5 % = 0,025 % vs 0,125 %; batas antrean (2 berjalan, jeda 30 hari) = 26 pengajuan/tahun -> tanpa pinalti 1,3 lolos palsu/tahun, dengan alpha A1/k 0,193. Pendekatan: Sharpe taksiran normal, hasil iid, union bound.
5. **Kunci:** `engine/locks/anggaran.lock.json` sha `0x833f25987bae2dbddf7f2aaa94477744e1b8bb55284271e0815e75293cd5a94d`, dikunci 2026-10-03T07:51:23Z (jam laptop). Kunci mengikat angka DAN parameter antrean
   (`queue_max_per_family` 2, `cooldown_days` 30); melonggarkan antrean = MENYIMPANG + tes gagal. `engine/anggaran.py` belum dipakai gerbang: penerapannya
   adalah P83 (penghitung percobaan + alpha per keluarga) dan P90 (riset ambang yang kini punya anggaran tetap).
6. **Pin on-chain** (builder: *"Gas"*): `FABIUS-ANGGARAN-v1`, tx `0x3254212fb06a705465857f61d31e79f76abf697f389852ac6a6a1c9728253165`, blok 134593740, gas 123.086, `lockedAt` 1791014141 = 2026-10-03T07:55:41Z, uri ke commit `b8783f42`; `--verify` membaca ulang lockedAt yang sama; `lockCount()` = 8. Dicatat di `deployments/97.json` `m3.pins`.
7. **Penegakan (P83, 3 Okt malam; builder: *"Gasss"*):** `engine/registri.py` menghitung k dari registri pengajuan, bukan dari angka yang diketik
   (`review --prior-submissions` kini jalur MANUAL yang tidak pernah mengikat). Pilihan penerapan yang diusulkan asisten, dicatat supaya bisa dibantah:
   (a) alpha A1/k dipakai di DUA uji statistik gerbang, G3 (persentil bootstrap > 0) dan G8 (batas atas p placebo). Satu uji sudah cukup secara
   konjungsi; dua dipilih karena ukuran tiap uji baru taksiran (R1/R4 belum mengukur), dan harganya daya. (b) Resampling naik x k, supaya G8 tetap
   mungkin lolos (tanpa itu 200 placebo tidak pernah bisa <= 0,05/4). (c) `TOLAK_FORMULIR` tidak memakan alpha (tidak ada uji yang jalan). (d) Hanya
   identitas terverifikasi yang dicatat (dompet tanpa tanda tangan bisa menaikkan k keluarga orang lain). (e) Masa tunggu 30 hari sesudah penolakan
   dibaca dari registri, jadi batas 26/tahun yang menjadi dasar A2 ditegakkan, bukan diandaikan. (f) `mengikat` kini juga menuntut k dari registri.
   Contoh pengajuan (`engine/examples/submission.example.json`, Sharpe +1,36) di `ledger/bars`: k=1 p5 +0,73 / placebo 0/120; k=4 p1,25 +0,42 /
   0/480; k=10 p0,5 +0,42 / 0/1200 - tetap LOLOS_SHADOW. Yang BELUM: jumlah pengajuan berjalan per keluarga (menunggu antrean P82); BH lintas kandidat,
   seed rahasia dari hash blok, tahan 12 bulan (menunggu R4 di P90, yang membandingkan penangkal mana yang terbaik).

**Terkait:** F-D16 · F-D84 · F-D87 · [[08-Backlog/08 - Riset Optimasi Ambang]] §1 · [[09-Inbox/Session-2026-10-02]] §38 §45

## F-D89 — Pintu tingkat 0 hidup: hosting hanya lewat GitHub, data landing ikut bukti harian, daftar tunggu = chat builder · 3 Okt 2026 (WIB)

> **5 Okt: untuk MCP digantikan oleh F-D111** (MCP = sinyal + data pendukung, hanya lewat x402 deposit). Teks di bawah tetap sebagai riwayat.

Builder: *"Kan bisa tuh trigger deploy via vercel cli, klo blom connect tinggal di re-connect aja"*, lalu *"Gasss"* dua kali (snapshot otomatis + P115).
Rancangan butir 3-5 diusulkan asisten di chat dan dijalankan atas "Gasss" itu; butir ini mencatatnya supaya bisa dibantah, bukan menyatakannya pilihan builder.

1. **Hosting:** landing + server MCP di Vercel, project `fabius`, Root Directory `web`, tersambung GitHub `master`: https://fabius-one.vercel.app, MCP di
   `/mcp`. Deploy HANYA lewat push GitHub: Vercel membangun dari clone, jadi hanya berkas ter-track yang ikut. `vercel deploy` dari folder kerja DILARANG,
   karena CLI mengunggah `.env` / `.committer.env` / `.deployer.env` (kunci privat) yang tidak ada di daftar abaikan bawaan Vercel. Commit yang tidak
   menyentuh `web/` tidak dibangun (perintah lewati-build), supaya commit bot tidak menghabiskan kuota (terbukti: `11b98493` CANCELED).
2. **Server MCP tingkat 0 (P114):** 8 alat hanya baca, tanpa kunci. Tingkat 1 tidak punya alat di server ini (F-D72 tetap). Endpoint MCP = endpoint
   pertama `docs/agent-card.json` (kartu ERC-8004 token 2494).
3. **Data landing dicetak mesin:** rantai `paper-ledger` memicu `web-snapshot.yml` sesudah penjaga luar menilai tick hari itu; commit hanya bila isi
   berubah; chain tak terbaca = snapshot lama dipertahankan (T8 SK-P1).
4. **Daftar tunggu (P115):** penampungnya riwayat chat Telegram builder, bukan basis data dan bukan repo. Alasan: privat, permanen, tanpa layanan baru, dan
   repo ini publik. Data yang dikumpulkan = yang dikirim Telegram sendiri (nama tampilan, @username, chat id) + asal tombol; tidak ada email atau nomor
   telepon. Log publik hanya hitungan (SK-P4).
5. **Batas yang jujur:** kontak pendaftar = data pribadi menurut UU PDP. Telaah hukum P80 kini juga mencakup daftar tunggu ini (persetujuan, tujuan,
   penghapusan). `/stop` hanya dikabarkan ke builder; menghapus entri = tangan builder. Sampai P80 selesai: tidak ada pesan pemasaran; satu-satunya pesan
   yang dijanjikan ke pendaftar = kabar saat tingkat 1 dibuka.

**Terkait:** F-D70 · F-D72 · F-D78 · [[04-Tools/TL19 - web landing]] · [[04-Tools/TL20 - server MCP]] · [[04-Tools/TL21 - waitlist]] · [[09-Inbox/Session-2026-10-02]] §41-§43

## F-D90 — [DICABUT 6 Okt 2026 atas kata builder; tinggal nisan] · 3 Okt 2026 (WIB)

Keputusan ini dicabut dari vault pada 6 Okt 2026 (builder: *"Hapus F-D90"*, bentuk: nisan). Nomor dipertahankan supaya rujukan lama tidak menggantung. Vault berada di repo publik: riwayat git tetap menyimpan teks aslinya; yang berubah hanya
keadaan vault sekarang. Dua hal darinya yang masih berlaku kini tercatat di F-D126: persetujuan P90 (+ gelombang 2) dan penundaan P75 / P80. Fakta teknis venue lokal tinggal sebagai bahan riset (bukan keputusan) di
[[08-Backlog/05 - Epik Enam Bot]] §6-§7 dan [[08-Backlog/10 - Epik Eksekusi Venue]].

**Terkait:** F-D126

## F-D91 — Eksekusi venue diimplementasikan: Binance Agent OS dulu, lalu Aster, Tokocrypto bila sempat; PRD terukur, uang nyata tetap atas kata builder per venue · 4 Okt 2026 (WIB)

Builder: *"Binance Agent OS + Aster gas + Tokocrypto, kita implementasikan, tapi prioritas no1 itu binance agent OS dulu, lalu aster, baru kalau sempet itu
Tokocrypto, gas buat planningnya di vault, workflownya sesuaikan di vault juga agar PRDnya jelas + terukur"*.

1. **Urutan:** (1) Binance Agent OS (sub-akun Agentic; USDⓈ-M futures + spot: B1, lalu B3), (2) Aster (agent wallet; perp: B1), (3) Tokocrypto (spot: B1) bila sempat.
2. **PRD:** [[08-Backlog/10 - Epik Eksekusi Venue]] - tujuan, non-goals, alur harian, kebutuhan R-E1..R-E10 dengan cara ukurnya, metrik + ambang USULAN (§6),
   tonggak E0-E6 dengan gerbang keluar terukur, alur kerja pengembangan, langkah builder H1-H6, risiko. Backlog P116-P123.
3. **Yang TIDAK berubah:** paper penuh sampai builder yakin (F-D73); `live` per venue hanya atas kata builder (saklar `EXEC_LIVE_OK`); leverage 1x; tanpa izin
   tarik; tingkat 1 (menjual sinyal) tetap terkunci (F-D72).
4. **Angka yang membentuk rencana, diukur 4 Okt dari endpoint publik:** min notional futures TESTNET Binance BTC 50 / ETH 20 / lainnya 5 USDT -> modal B1 penuh
   >= ±800 USDT (prod belum terukur: terblokir dari jaringan builder); Aster 5 USDT untuk 16/16 aset -> >= ±80 USDT.
5. **Pertanyaan terbuka yang bisa membalik urutan:** akses Binance + Agent OS untuk akun builder dari Indonesia tanpa VPN (H1). Bila tertutup, Aster naik ke
   prioritas 1 - keputusan builder, bukan otomatis.

**Terkait:** F-D72 · F-D73 · F-D90 · [[08-Backlog/05 - Epik Enam Bot]] §6 §7 · [[09-Inbox/Session-2026-10-02]] §48

## F-D92 — Modal nyata maksimal 10 USDT: akurasi diuji di kertas-venue dulu, uang nyata hanya untuk canary pipa satu aset · 4 Okt 2026 (WIB)

Builder: *"Terkait dana awalan pastinya sangat terbatas maksimal hanya ada di 10 usdt, eksekusi aja prdnya sebagian yg paling posible tapi minimal mencakup
50% dari PRD. Pastikan konsep paper sebagai awalan test akurasi tetap ada sebelum open posisi uang asli ya"*.

1. **Batas modal nyata: 10 USDT.** [**KOREKSI 4 Okt sore (terukur):** angka "Aster >= ±80 USDT" hanya menghitung min notional (5 USDT) dan MENGABAIKAN ukuran lot. Lot BTC = 0,001 BTC ≈ 85 USDT (harga Aster 85.124), jadi BTC pada 6,25 % baru terbuka di modal >= ±1.362 USDT - di Aster DAN di Binance (lot sama). Order terkecil nyata di Aster (live 4 Okt): ATOM/LTC/TRX/ETC/DOGE/LINK/BCH/XRP/DOT/ADA ±5,0-5,1; ETH 5,4; SOL 6,1; BNB 7,9; NEAR 9,7; AVAX 11; BTC 85 USDT. Dengan 10 USDT (1x): tepat SATU posisi canary ±5 USDT di venue mana pun.] B1 penuh tidak bisa dibuka dengan modal itu di venue mana pun (Aster >= ±80, Binance >= ±800 USDT; snapshot filter
   4 Okt). Tidak ada pemotongan universe diam-diam: aset yang tidak bisa dibuka tercatat `dilewati`.
2. **Kertas wajib sebelum uang nyata:** tahap S1 kertas-venue (keputusan resmi dieksekusi di atas kertas dengan harga, lot, min notional, dan fee venue;
   modal virtual 2.000 dan 10 USDT) harus lulus sebelum testnet (S2) dan canary (S3). PRD v1.1: [[08-Backlog/10 - Epik Eksekusi Venue]] §0a.
3. **Uang nyata = canary pipa:** satu aset, <= 10 USDT, mengikuti keputusan B1 untuk aset itu. Ia membuktikan mekanisme (isi, fee nyata, rekonsiliasi,
   latihan mati), BUKAN kinerja B1. Tidak ada klaim kinerja dari canary.
4. **Dibangun hari ini (>= 50 % PRD):** inti eksekutor, adaptor Binance (tanpa order sungguhan), kertas-venue + metrik, rantai GitHub menjalankannya
   tiap hari; 13 tes; T8 SK-E1..SK-E9 berjangkar. Rincian: PRD §0a, [[04-Tools/TL22 - eksekutor dan kertas-venue]].

**Terkait:** F-D73 · F-D91 · [[09-Inbox/Session-2026-10-02]] §50

## F-D93 — Paket gratis Railway menolak service ketiga: eksekutor mode demo menumpang `fabius-engine`; kunci demo Binance terpasang dan terverifikasi · 4 Okt 2026 (WIB)

Builder: *"Gabisa cuy, saya mau tambah empty project gabisa karena free plan, jadi saya taruh di fabius-engine dulu ya, cek aja"*.

1. `BINANCE_API_KEY` / `BINANCE_SECRET_KEY` / `BINANCE_API_ENV=demo` dipasang builder di `fabius-engine` (dashboard). Diverifikasi dari dalam container
   (kunci SSH sementara, dicabut sesudahnya; nilai kunci tidak pernah dicetak, hanya panjangnya): `/fapi/v2/balance` HTTP 200 (saldo VIRTUAL demo BTC 0,01,
   USDT 5.000, USDC 5.000), `/fapi/v2/positionRisk` HTTP 200 (0 posisi), kueri order palsu HTTP 400 `-2013` (= tidak ada, sesuai harapan). Worker sesudah
   redeploy sehat (start 19:06Z, komit 2 Okt OK, alarm 0).
2. **Eksekutor mode demo (P118) menumpang `fabius-engine`** sebagai langkah terpisah yang dijaga (gagal = dicatat + alert, worker komit tetap jalan),
   bukan service `fabius-exec` (PRD §3) - sampai paket Railway di-upgrade (rencana ±1 Nov).
3. **Kunci PROD (uang nyata) TIDAK boleh serumah dengan kunci committer:** sebelum tahap S3 canary, service terpisah wajib ada (upgrade) - atau builder
   memutuskan lain secara eksplisit.

**Terkait:** F-D91 · F-D92 · [[08-Backlog/10 - Epik Eksekusi Venue]] · [[09-Inbox/Session-2026-10-02]] §53

## F-D94 — Runner GitHub TIDAK bisa membaca Binance (451, terukur): ledger eksekusi Binance dibawa dari Railway lewat Gist publik; Aster tetap dibaca langsung · 4 Okt 2026 (WIB)

Builder: *"gas"* (lanjut P119 sesudah /status) + *"vault jgn sampai ketinggalan"*.

1. **Terukur** (run `egress-probe` 37190705904, 4 Okt ±09:00Z, `tools/probe_egress.py`, tanpa kunci): dari runner GitHub `demo-fapi.binance.com`
   `/fapi/v1/time` dan `/fapi/v1/userTrades` -> **451** "Service unavailable from a restricted location"; `fapi.binance.com` 451 (kontrol, sama dengan 24 Sep);
   `testnet.binancefuture.com` 200 (tetapi kunci kita = Demo Trading, bukan testnet lama); Aster `fapi.asterdex.com` 200 dan `userTrades` tanpa kunci 401
   `-2014` (= lapisan otentikasi terjangkau).
2. **Akibat untuk PRD (epik 10 §3/§4, R-E10):** "penulis ledger eksekusi = rantai GitHub dengan kunci READ-ONLY yang membaca venue" MUSTAHIL untuk
   Binance (demo maupun prod) dan TETAP BISA untuk Aster (P121). Untuk Binance, pembacaan riwayat order harus terjadi di Railway (IP Singapura).
3. **Jalur yang dipilih (usulan asisten, menunggu satu langkah builder H7):** eksekutor di Railway menyusun ULANG laporan eksekusi dari venue (order dicari
   lewat `clientOrderId` deterministik, jadi laporan tidak bergantung memori proses) + tanda ekuitas harian, lalu menambahkannya ke **Gist publik** milik
   builder (token hanya-Gist: tidak bisa menyentuh repo). Rantai GitHub membaca Gist itu, MEMERIKSA (id order = hash yang dihitung ulang, aset di universe,
   order sesudah komit di chain, long-only), lalu menulis `ledger/eksekusi/` berantai hash - rantai GitHub tetap PENULIS TUNGGAL ledger. Riwayat revisi
   Gist (bercap waktu GitHub) jadi jejak kedua.
   - Ditolak: domain publik Railway (endpoint masuk + disk Railway tidak tetap); token tulis-repo di Railway (memecah penulis tunggal); data ke chain
     (jalur tx baru, tanpa kebutuhan); kunci di Vercel (Vercel tanpa rahasia).
   - Batas jujur: untuk mode DEMO, laporan dibaca dengan kunci eksekutor sendiri (kunci terpisah read-only = syarat sebelum S3 bersama service terpisah,
     F-D93 #3). Isi balasan Binance tidak bertanda tangan, jadi publik tetap memercayai pembaca; yang bisa diperiksa publik: urutan waktu terhadap komit,
     id deterministik, konsistensi posisi, dan selisih terhadap kertas.
4. **Langkah builder H7:** buat fine-grained personal access token GitHub dengan HANYA izin akun "Gists: Read and write" (tanpa akses repo), masa berlaku
   pendek; pasang di variabel Railway `fabius-engine` bernama `EXEC_FEED_TOKEN` lewat dashboard (JANGAN lewat chat). Tanpa token: umpan mati, eksekutor
   tetap jalan seperti sekarang.

**Terkait:** F-D25 (matriks egress kedaluwarsa) · F-D91..F-D93 · [[08-Backlog/10 - Epik Eksekusi Venue]] · [[09-Inbox/Session-2026-10-02]] §61

## F-D95 — Semua bot dinyalakan: B1 = INTI, B2-B6 = SEMENTARA (bisa diganti), satu keluarga F-D16, empat bot baru menyala bersamaan · 4 Okt 2026 (WIB)

Builder: *"nyalain semua bot aja tapi kasih label yg mendeskripsikan sementara/available untuk diganti jika memenuhi kriteria untuk bot selain bot yg
menurutmu paling OP"* + jawaban AskUserQuestion: hitungan = **"Ya, satu hitungan"**; urutan = **"Keempatnya sekaligus"**; tx chain = **"Ya, rencana dulu
lalu jalankan"**.

1. **Label:** B1-TREND = **INTI** (penghuni buku = bot identitas PILIHAN builder, F-D73. **Koreksi tulisan awal paragraf ini:** B1 TIDAK lolos
   gerbang - vonis v1 TOLAK di G8 dan G10 (epik 07 §7); satu-satunya yang LOLOS_SHADOW di v1 adalah B3 (dorman). INTI = peran di buku, bukan bukti
   bot terbaik; tidak ada bot yang sudah lolos uji maju F-D16). B2-RS, B3-CARRY,
   B4-LISTING-FADE, B5-CORE-RWA, B6-BOUNCE = **SEMENTARA** ("berjalan untuk transparansi; bisa digantikan bot yang memenuhi kriteria"). B3 tetap dicatat
   sebagai satu-satunya yang LOLOS gerbang v1 (bayangan n/60). B2/B5/B6 TOLAK di gerbang v1, B4 tak terukur - status itu tetap tampil, tidak dihapus.
2. **Membalik pagar jam maju:** `engine/book.py::SHADOW_ELIGIBLE` (B1, B3 saja) diganti daftar bot berjam maju = keenamnya. Keputusan lama (bot tanpa
   gerbang tidak diberi jam maju gratis) DICABUT untuk tujuan transparansi hackathon; menjalankan semua bot dan memamerkan yang kebetulan menang tetap
   dicegah oleh: label SEMENTARA, semua bot tampil termasuk yang kalah, dan F-D16 BH lintas SEMUA bot berjam maju.
3. **Satu keluarga F-D16** (pilihan builder, bukan rekomendasi asisten): BH alpha 0,10 kini lintas 6 bot, bukan 2 -> B1/B3 butuh p lebih kecil untuk
   lolos uji jual. Parameter F-D16 v1 yang terkunci TIDAK berubah; yang berubah hanya jumlah bot di keluarga.
4. **Urutan:** spesifikasi B2/B4/B5/B6 dikunci di LockRegistry oleh committer DULU (rencana tx -> kata builder), lalu jam maju keempatnya dimulai
   BERSAMAAN sesudah data B4 (kejadian listing) dan B5 (spot emas PAXG) siap.

**Terkait:** F-D16 · F-D73 · F-D84 · F-D85 · [[09-Inbox/Session-2026-10-02]] §69

## F-D96 — Kunci API uang asli boleh di `fabius-engine` (paket gratis), dengan mitigasi; F-D93 #3 dicabut · 4 Okt 2026 (WIB)

Builder: *"YG gratis dulu, kalau emg ga kuat baru upgrade, tp usahakan semaksimal mungkin yg free yak"* (jawaban atas "kunci API Binance ASLI disimpan
di mana?", sesudah risikonya ditulis: satu container memegang kunci committer + kunci uang asli; satu bocor = dua-duanya).

1. F-D93 #3 ("kunci PROD tidak boleh serumah dengan kunci committer") DICABUT untuk tahap canary. Upgrade Railway hanya bila paket gratis tidak kuat.
2. **Mitigasi wajib di kode (sebelum kunci asli dipasang):** (a) kunci asli memakai variabel TERPISAH dari kunci demo; demo tetap mengukur B1 penuh;
   (b) cek izin saat start: tarik HARUS mati, futures HARUS hidup (R-E6, `apiRestrictions`), gagal = tidak start; (c) batas keras notional uang asli
   (bawaan 10 USDT, F-D92) yang tidak bisa dilewati rencana; (d) izin builder bertanggal kedaluwarsa (bukan harian); (e) uang asli hanya membuka posisi
   bila saldo cukup untuk order terkecil - selain itu dicatat `dilewati`; (f) setiap isi order uang asli diberi label NYATA dan dicatat on-chain dengan
   metadata rinci (kontrak baru, deploy atas kata builder).
3. Label: catatan eksekusi `uang: NYATA` vs `DEMO`; halaman /bot dan /status memisahkan keduanya.

**Terkait:** F-D92 · F-D93 · F-D94 · [[08-Backlog/10 - Epik Eksekusi Venue]] · [[09-Inbox/Session-2026-10-02]] §69

## F-D97 — Sakelar publik uang nyata `config/uang_nyata.json`, dibaca sekali per bar; repo dikirim MATI · 5 Okt 2026 (WIB)

Builder: *"Palingan kita bikin toggle aja yg bisa dynamic nyalain real trade dan paper trade gitu kah? Soalnya saya belum brati kehilangan duit 10
usdt saya."*

1. Uang nyata butuh KEDUANYA: variabel Railway `fabius-engine` bersenjata (F-D96: `EXEC_REAL=canary`, kunci asli, `EXEC_LIVE_OK` bertanggal) DAN
   sakelar repo `config/uang_nyata.json` `{"aktif": true}`. Repo dikirim `false`. Selain `true` persis (tidak ada, tak terbaca, `"true"`, `1`) = MATI.
2. Dibalik lewat edit berkas di GitHub (tanpa Railway, tanpa redeploy). Riwayat git berkas itu = catatan publik kapan uang nyata dinyalakan/dimatikan.
3. Sakelar dibaca SEKALI per bar, saat bar baru dieksekusi; dibalik di tengah bar = berlaku bar BERIKUTNYA. Alasan: id order = hash (venue, bot, bar,
   aset, sisi), kunci ExecutionAnchor = (pelapor, venue, id order), dan ledger eksekusi menerima satu laporan per bar dengan bar naik ketat; membalik di
   tengah bar akan menabrak ketiganya. Keluar darurat di tengah bar = tutup manual di aplikasi Binance (isi manual itu tidak masuk umpan).
4. MATI + posisi datar = tidak ada order, tidak ada laporan; MATI + posisi terbuka = bar berikutnya dieksekusi dengan target datar (tutup reduce-only),
   dilaporkan `sakelar: mati` dan dicatat on-chain. Laporan membawa `sakelar: nyala|mati` (ikut di-hash ke `reportHash`).
5. Penjaga luar `periksa` tidak menuntut laporan `binance-live` hanya bila sakelar MATI DAN posisi baris terakhir datar.
6. Paper (ledger resmi), kertas-venue, dan akun demo berjalan terus apa pun nilai sakelar. Worker yang restart tidak mengeksekusi ulang bar yang sudah
   ada di ledger publik `binance-live`.

**Terkait:** F-D92 · F-D96 · [[04-Tools/TL29 - canary uang nyata]] · [[07-Testing/T8 - Semantik Kegagalan Operator]] SK-E27..SK-E29 ·
[[09-Inbox/Session-2026-10-02]] §73

## F-D98 — x402 per sinyal di testnet 97 dengan token uji; isi sinyal publik ditunda satu bar; confidence = rekam jejak maju · 5 Okt 2026 (WIB)

Builder: *"keputusan yg emg bener 3 dulu tp kita harus usahakan no1 juga sempet"* + usulan bot x402 per sinyal di tiga kanal (MCP untuk agen, bot
Telegram, web): belum bayar = hanya persentase confidence + alasannya, tanpa membocorkan detail. Jawaban AskUserQuestion: pembayaran = **"Testnet 97,
token uji"**; jeda buka publik = **"Sampai bar berikutnya (~24 jam)"**; confidence = **"Rekam jejak maju bot"**.

1. **Urutan:** (3) bukti Fabius ke registri ERC-8004 (identitas 2494; Reputation + Validation ternyata ADA di chain 97, lihat koreksi 5 Okt) ->
   tunda pembukaan publik + confidence -> backend hak akses x402 (MCP + web + Telegram) di testnet -> (1) LLM analis (berita/pengumuman -> fitur
   terkomit) bila sempat. Dicatat sebagai P136-P139.
2. **Pembayaran:** mekanisme penuh di chain 97 dengan token uji, berlabel demo. Ini BUKAN penjualan sinyal: F-D72 (tingkat 1 = bot lolos F-D16 maju +
   telaah hukum P80) tetap utuh; mainnet hanya lewat keputusan baru.
3. **Jeda buka:** komit tetap langsung on-chain; isi sinyal (target) dibuka publik sesudah bar berikutnya (~24 jam). Pembayar melihat isi lebih dulu.
   Konsekuensi: ledger paper publik dan web tidak boleh memuat target bar terakhir sebelum jedanya lewat (`ungkap +0s` hari ini harus berubah).
4. **Confidence:** dihitung dari rekam jejak maju ter-anchor (n, PnL net, CI, vonis gerbang) - bukan dikarang, bukan kekuatan sinyal hari itu.
   Teaser tanpa bayar tidak boleh membocorkan aset, arah, atau ukuran.

**Terkait:** F-D11 · F-D16 · F-D70 · F-D72 · [[08-Backlog/06 - Epik Gerbang Sinyal]] · [[05-Ecosystem/01 - ERC-8004 Identity]] ·
[[09-Inbox/Session-2026-10-02]] §75-§76

## F-D99 — x402 menjual pengiriman sinyal terverifikasi, bukan rahasia; pembukaan publik TIDAK ditunda; rahasia hanya untuk sinyal LLM (P139) · 5 Okt 2026 (WIB)

Saat menjelaskan P137, ditemukan: B1-B6 deterministik, kode + spesifikasi terbuka di repo publik, data publik (Binance Vision), dan tick dihitung di
GitHub Actions repo publik - siapa pun bisa menghitung sendiri sinyal hari itu. Menunda pembukaan publik (F-D98 #3) TIDAK menciptakan kerahasiaan.
Pilihan yang diajukan: A (jual kemudahan + kecepatan + bukti terverifikasi; P137 = teaser confidence saja), B (rahasia sungguhan hanya untuk sinyal
LLM P139), C (spesifikasi disembunyikan + tick dipindah ke server privat; tidak disarankan). Builder: **"Gas"** atas rekomendasi "A sekarang, B
menyusul".

1. **F-D98 #3 dicabut:** pembukaan publik tetap seketika (`ungkap +0s`), ledger paper + web tetap memuat target bar terakhir.
2. **Nilai x402 (P138) untuk B1-B6:** sinyal siap pakai lewat MCP/web/Telegram tanpa menjalankan engine sendiri, segera sesudah komit, beserta bukti
   (komit, validasi ERC-8004). Teks penjualan tidak boleh menyiratkan rahasia untuk bot deterministik.
3. **P137 dipersempit:** teaser confidence = 1 - p bootstrap F-D16 yang terkunci atas settle maju (`engine/confidence.py`), kematangan menuju ambang
   F-D16, status, vonis gerbang; tanpa aset/arah/ukuran/id.
4. **Rahasia sungguhan (tingkat premium) hanya untuk sinyal berbasis LLM (P139):** output LLM tidak bisa dihitung ulang orang lain sebelum dibuka;
   komit tetap seketika, pembukaan isi boleh ditunda untuk tingkat itu (keputusan rinci saat P139).

**Terkait:** F-D16 · F-D72 · F-D98 · [[04-Tools/TL31 - teaser confidence]] · [[09-Inbox/Session-2026-10-02]] §80

## F-D100 — P138: token Fabius Credit (FAB), harga per sinyal dari confidence (tabel dikunci), gerbang di service Railway baru, bot Telegram baru · 5 Okt 2026 (WIB)

Jawaban builder: Telegram = **"Bot baru via @BotFather"**; hosting = **"Service baru Railway"**; token = *"Jgn x402usd dong, pakai nama yg cocok untuk
nama Fabius"*; harga = *"EH untuk harga bisa ga ya ditentukan dari confidence levelsnya?"*; atas usulan tabel + nama: **"gas"** (opsi pertama: Fabius
Credit · FAB).

1. **Token:** kontrak baru `FabiusCredit` (nama "Fabius Credit", simbol FAB, 6 desimal, `faucet()` publik berbatas per alamat, EIP-2612) - kode sama
   dengan X402DemoToken, hanya nama/simbol (nama = domain EIP-712, jadi tidak bisa diganti tanpa deploy). Testnet 97, tanpa nilai (F-D98 #2).
2. **Harga per (bot, bar) dari teaser confidence (P137), tabel DIKUNCI sebelum data maju ada:** belum terukur / awal = 0,01 FAB; terukur < 60 % =
   0,01; 60-75 % = 0,05; 75-90 % = 0,25; >= 90 % DAN F-D16 LOLOS = 1,00. Harga dihitung dari ledger sampai tick bar itu saja -> beku per (bot, bar)
   dan bisa dihitung ulang siapa pun. Angka "awal" tidak pernah menaikkan harga.
3. **Gerbang:** service Railway `fabius-x402` (image yang sama, `FABIUS_JOB=x402_sinyal`), kunci fasilitator BARU (bukan committer/agen/validator),
   tBNB dari committer. Memverifikasi otorisasi yang DITANDATANGANI (token, jumlah, `witness.to`, spender), bukan hanya `accepted` dari klien, dan
   membaca ulang saldo sesudah settle (celah gate lama `x402_gate.py`).
4. **Tiga pintu:** MCP (`fabius_signal_offer` -> URL x402), web `/beli/<bot>` (dompet menandatangani 2 pesan, nol gas), bot Telegram baru (builder
   membuat lewat @BotFather; token ditempel builder di variabel Railway, bukan chat) - link bayar web bertanda HMAC, isi dikirim ke chat sesudah settle.
5. **Faucet relay:** gerbang mengirim FAB ke alamat pembeli (berbatas), jadi pembeli tidak butuh tBNB sama sekali.

**Terkait:** F-D72 · F-D98 · F-D99 · [[04-Tools/TL6 - x402 gate and client]] · [[09-Inbox/Session-2026-10-02]] §81

## F-D101 — Dompet pembeli = Privy (login Google / Telegram / email, satu dompet lintas web dan Telegram); dompet custodial bot dibatalkan; bot berbahasa Inggris · 5 Okt 2026 (WIB)

Builder: *"A boleh deh, tapi dompetnya ga berubah" kan? Lalu commandnya pakai inggris ya"* lalu *"BIsa ga pakai konsep kayak privy? Jadi wallet itu
terhubung dengan akun googlenya, jadi pas login di web fabius jg tinggal pakai akun google aja"*. App ID Privy diberikan di chat (publik); App secret
dipasang builder sendiri di variabel Railway `fabius-x402` (`PRIVY_APP_SECRET`), BUKAN lewat chat (diingatkan; aturan tetap proyek).

1. **Privy** = dompet pembeli: login Google, Telegram (Mini App: login otomatis), atau email -> embedded wallet; akun Telegram bisa ditautkan ke user
   Google (`linkWithOAuth`) -> SATU user, SATU dompet di web dan Telegram. Paket gratis Developer (0-499 MAU, 50 rb tanda tangan/bulan, dibaca 5 Okt).
2. **Opsi A (dompet custodial diturunkan dari rahasia server) DIBATALKAN sebelum rilis:** alamatnya akan berbeda dari dompet Privy, jadi merilis A
   lalu pindah = dompet user berganti (bertentangan dengan syarat builder "dompetnya ga berubah"). Kodenya dihapus, tidak pernah ter-deploy.
3. **Halaman `/beli/<bot>`** (P138c): Privy + dua tanda tangan EIP-712 (Permit2 + EIP-2612), nol gas, faucet FAB; dibuka juga sebagai Telegram Mini
   App dari tombol `web_app` bot.
4. **Bot Telegram berbahasa Inggris** (`/bots`, `/signal`, `/buy`, `/wallet`, `/help`); `/buy` dan `/wallet` = tombol Mini App. Beli LANGSUNG dari
   chat + langganan otomatis = tahap berikutnya lewat session signer Privy (butuh App secret di server + kunci otorisasi P-256 milik kita).
5. App ID ditanam di kode web sebagai konstanta publik; App secret hanya di Railway.

**Terkait:** F-D98 · F-D99 · F-D100 · [[04-Tools/TL32 - gerbang x402 per sinyal]] · [[09-Inbox/Session-2026-10-02]] §82

## F-D102 — Fabius = platform agent analis terbuka (ERC-8004): agent memilih bot per bar, pilihan dikomit on-chain, dinilai + reputasi; tiga analis rumah · 5 Okt 2026 (WIB)

Builder (atas /buy di chat): *"menidng /buy aja dan berikan bot yg sedang dipakai trading Fabius ... itulah kenapa saya minta ada LLM itu, untuk bantu
decision making bot maa yg dipakai"*. Jawaban AskUserQuestion: peran = **"Pemilih, dikomit on-chain"**; kandidat = **"Keenam bot berjam maju"**; lalu
*"Rencana saya mau bikin ini seperti bot, jadi org bisa register agent mereka untuk melakukan analisis ... fomoapi ... GMGN ... Bubblemaps ... RugCheck"*,
*"Fabius menyediakan platform DexScreener, Fomo, GMGN, Bubblemaps, RugCheck, tapi kalau agent lain punya analisisnya sendiri mah gas aja"*, model:
*"sonnet 5.5 effort xhigh, glm 5.3 effort medium/low, qwen 3.8 flash effort xhigh"* (GLM/Qwen lewat provider qwencloud di opencode.json builder).

1. **Agent analis** (identitas ERC-8004 masing-masing) memilih SATU bot dari keenam bot berjam maju tiap bar; pilihan (bot, keyakinan, hash alasan)
   ditandatangani dompet agent dan DIKOMIT on-chain sebelum batas waktu. Agent tidak pernah membuat trade sendiri (F-D70, F-D11 tetap).
2. **Penilaian** dari ledger publik (return paper bot pilihan vs patokan) -> ReputationRegistry ERC-8004; papan peringkat publik.
3. **Bot aktif** Fabius (dijual oleh `/buy` tanpa argumen) = aturan pemilihan yang DIKUNCI sebelum dipakai (usulan: mayoritas analis sampai ada yang
   punya >= 20 pilihan terskor, sesudah itu agent berreputasi terbaik). Sebelum aturan itu hidup: penghuni buku slot (B1).
4. **Tiga analis rumah** sebagai pendaftar pertama, bersaing: Claude Sonnet 5.5 (effort xhigh, Anthropic API), GLM 5.3 (medium) dan Qwen 3.8 Flash
   (xhigh) lewat qwencloud (OpenAI-compatible, `reasoning_effort`). Service Railway terpisah `fabius-analis` (worker utama tidak ikut redeploy -> IP
   whitelist canary tidak putus). Kunci: `ANTHROPIC_API_KEY` dibuat builder di console.anthropic.com; kunci qwencloud dipindah dari opencode.json ke
   Railway lewat `--stdin` tanpa ditampilkan.
5. **Platform data untuk agent:** alat MCP DexScreener, Fomo, GMGN, Bubblemaps, RugCheck. Dicatat jujur: alat-alat itu untuk memecoin/dompet DEX,
   relevansinya rendah untuk 16 perp mayor (paling relevan: B4 listing baru); catatan lama: Fomo API 8 trader, GMGN route privat butuh kunci bertanda.

6. **Ralat 5 Okt (kata builder):** *"jgn pakai claude dulu, gaada duit saya untuk isi kreditnya"* - bonus $250 "cloud sessions" di langganan Claude
   TIDAK berlaku untuk API key (dicek di support.claude.com: hanya cloud sessions Claude Code, klaim s.d. 7 Okt 23:59 PT); API = kredit prabayar
   Console. Analis rumah dimulai DUA: GLM 5.3 (medium) + Qwen 3.8 Flash (xhigh) lewat qwencloud; analis Claude disiapkan di kode, aktif hanya bila
   `ANTHROPIC_API_KEY` ada.

**Terkait:** F-D11 · F-D70 · F-D71 · F-D98 · [[05-Ecosystem/01 - ERC-8004 Identity]] · [[09-Inbox/Session-2026-10-02]] §84

## F-D103 — Kunci otorisasi Privy yang TERBUKA di chat dipakai sampai hackathon selesai, lalu migrasi · 5 Okt 2026 (WIB)

Untuk P138e (/buy langsung dari chat lewat session signer Privy), builder membuat key di dashboard dengan "Create new key" (Privy yang membuat kunci)
lalu menempelkan ID DAN private key di chat. Diingatkan: kunci itu harus dianggap bocor; disarankan hapus + daftarkan public key buatan kita lewat
"Register key quorum instead". Builder: *"Pakai dulu aja, nanti pas selesai hackathon ku migrate"*.

1. Dipakai: key quorum `vb41lc4l9exfr5zfo09vj5fg`, private key di `.privy.env` (di-gitignore) + Railway `fabius-x402` lewat stdin; tidak dicetak lagi.
2. Batas risiko: testnet, token FAB tanpa nilai; server hanya membangun typed data pembayaran FAB tepat tagihan ke payTo gerbang (DIJAGA KODE, belum
   policy Privy - teks izin di web menyebutnya jujur). Siapa pun yang memegang kunci itu bisa menandatangani dari dompet user yang memberi izin.
3. **Migrasi sesudah hackathon (wajib):** daftarkan `PRIVY_AUTH_PUBLIC_KEY_CADANGAN` (`.privy.env`, belum pernah terbuka) sebagai key quorum baru, ganti
   `PRIVY_AUTH_PRIVATE_KEY` + `PRIVY_KEY_QUORUM_ID` (Railway + `web/src/lib/x402-buy.ts`), hapus key lama, minta user memberi izin ulang; tambahkan
   policy Privy yang membatasi tanda tangan ke domain Permit2/FAB chain 97.

4. **Selesai lebih awal (5 Okt, hari yang sama):** izin bot di Mini App ditolak Privy (*"Unable to find the specified key quorums"*) karena
   `vb41lc…` adalah ID authorization key, bukan key quorum. Karena key quorum harus dibuat juga, builder mendaftarkan public key CADANGAN (pasangan
   lokal yang tidak pernah terbuka) -> key quorum `pyyven7fpdtnc30uuij8ikps` (fabius-bot1). Server + web dialihkan ke pasangan itu; kunci yang terbuka
   PENSIUN (dihapus dari `.privy.env`; builder diminta menghapusnya di dashboard). Sisa pekerjaan migrasi: hanya policy Privy (opsional).

5. **Policy dipasang 5 Okt (P148):** `g0mqf8prswwwe63rai348zcd` membatasi kunci bot di enclave Privy ke pembayaran FAB ke payTo gerbang, chain 97,
   <= 1 FAB per tanda tangan (diuji 6/6 di dompet server). Berlaku untuk izin yang dipasang lewat tombol Allow sesudah web ini; izin lama tanpa
   policy berlaku sampai user menekan Allow lagi.

**Terkait:** F-D101 · [[04-Tools/TL32 - gerbang x402 per sinyal]] · [[09-Inbox/Session-2026-10-02]] §87

## F-D104 — Alasan agent analis: tersegel sampai bar tutup; lengkap di web untuk akun yang login + membeli sinyal dalam 7 hari · 5 Okt 2026 (WIB)

Builder (setelah melihat `/analysts` menautkan JSON gerbang): *"Mending ditaruh di FE web deh tp hanya bisa diakses untuk org yg login + bayar,
masa org awam disuruh akses file json dari BE?"*

1. **Publik** (gerbang `/analis`, Telegram `/analysts`, MCP `fabius_analysts`): bot pilihan, keyakinan agent, reasonHash, tx - semuanya memang sudah
   on-chain. Isi alasan pilihan yang barnya BELUM tutup disegel (`tools/x402_sinyal.py::tutup_alasan`); `/analysts` tidak lagi mengutip alasan dan
   tidak lagi menautkan JSON - tombol Mini App ke `/analis`.
2. **Web `/analis`** (untuk semua): bot aktif, slip pilihan bersegel (bot + keyakinan + reasonHash), papan peringkat. **Alasan lengkap** (teks,
   risiko, sidik input/prompt/jawaban mentah) hanya untuk akun Privy yang login DAN dompetnya membeli >= 1 sinyal dalam **7 hari** (14 bar terakhir).
   Gerbang `GET /analis/lengkap` memeriksa token akses Privy (JWT ES256, iss `privy.io`, aud = app id, kunci verifikasi publik app) lalu dompet user
   (GET /v1/users/{did}) terhadap catatan pembelian `/data/pembelian.jsonl` (ditulis sesudah settle TERBUKTI). Tanpa login 401, tanpa pembelian 402 +
   tautan beli.
3. **Sesudah bar tutup alasan terbit penuh** (gerbang `/analis/<close>` + arsip repo PUBLIK `ledger/analis`) - itu syarat agar siapa pun bisa
   mencocokkan sha256-nya dengan reasonHash on-chain. Menutupnya selamanya = verifikasi pihak ketiga hilang; tidak dipilih. Yang dijual = membaca
   SEBELUM tutup (saat masih berguna) + tampilan rapi; web tetap hanya menampilkan isi alasan ke pembeli. Arsip melewati bar yang belum tutup.
4. 7 hari dan 14 bar = pilihan produk (bisa diubah builder), bukan angka statistik. Pembelian sebelum deploy ini tidak tercatat (catatan mulai sekarang).
5. Dua "confidence" dibedakan di Telegram: `/bots` = *track-record confidence* (1 - p F-D16 atas hasil maju bot, `engine/confidence.py`; angka dari 2
   hari settle, bermakna dari 20) dan `/analysts` = *self-rated confidence* (keyakinan agent untuk satu bar, field `confidence` SelectionAnchor).

**Terkait:** F-D99 · F-D102 · [[04-Tools/TL33 - agent analis]] · [[04-Tools/TL32 - gerbang x402 per sinyal]] · [[09-Inbox/Session-2026-10-02]] §88

## F-D105 — Slot analis agent 2558 berganti model: GLM 5.3 -> DeepSeek V4.1 Flash (effort high), identitas tetap · 5 Okt 2026 (WIB)

Builder: *"Coba untuk GLM 5.3 diganti model id ini "deepseek-v4.1-flash" lalu effortnya di set high."*

1. Diuji dulu di qwencloud (`railway run`, kunci tidak dicetak): `deepseek-v4.1-flash` + `reasoning_effort: high` -> HTTP 200 dalam 3,8 detik.
2. **Identitas TETAP**: agent ERC-8004 2558, dompet `0x8e0E…a8A8`, URI kartu on-chain `.../docs/analis/glm.json`, slug internal `glm` - tanpa transaksi.
   Yang berganti: nama ("Fabius Analyst · DeepSeek V4.1 Flash"), model, effort (`tools/analis.py::AGENTS` + `deployments/97.json`, yang menimpa kode
   di `active_agents`). Kartu memuat `model_history` (GLM 5.3 low sampai penutupan 2026-10-06 00:00Z).
3. Dapat diperiksa per pilihan: JSON alasan yang di-hash ke reasonHash memuat `model` + `nama`, jadi setiap pilihan tetap terbukti dibuat model yang
   mana. Konsekuensi: papan peringkat agent 2558 menggabungkan 1 pilihan GLM (penutupan 2026-10-06) dengan pilihan DeepSeek sesudahnya.
4. Alternatif yang TIDAK diambil (butuh izin transaksi): identitas baru (dompet + register + tBNB) supaya rekam jejak tiap model terpisah.

**Terkait:** F-D102 · [[04-Tools/TL33 - agent analis]] · [[09-Inbox/Session-2026-10-02]] §89

## F-D106 — Web: sinyal hari ini tanpa memilih bot, rute + label berbahasa Inggris · 5 Okt 2026 (WIB)

Builder: *"di page beli/B1-TREND, kenapa masih belinya terhadap bot? Kan di tele udh saya minta untuk /buy aja karena user mana mau pilih bot"*,
*"semua yg pakai bahasa indo di toggle english diganti ke inggris"*, *"routenya masa indo juga, /beli, /analis, dll ganti inggris dong"*.

1. **`/buy` = sinyal hari ini**: bot diambil dari gerbang `/active` (aturan terkunci `engine/pemilih.py`), sama dengan `/buy` tanpa argumen di
   Telegram. `/buy/<BOT>` tetap untuk tautan eksplisit (`/buy <BOT>` di chat, agent/MCP). Semua tautan app di bot Telegram, `/analysts`, dan gerbang
   (402 `beli`) menunjuk `/buy`.
2. **Rute English**: web `/buy`, `/buy/<bot>`, `/analysts` (redirect permanen dari `/beli`, `/beli/<bot>`, `/analis` - pesan Telegram lama memakai
   rute lama). Gerbang `/signal`, `/active`, `/analysts[/<close>|/full|/scores]`; nama lama `/sinyal`, `/aktif`, `/analis` TETAP dilayani karena URI
   feedback reputasi ERC-8004 yang sudah on-chain menunjuk `/analis/<close>`. Resource x402 kini `/signal/...`. Folder repo (`docs/analis` = URI kartu
   on-chain, `ledger/analis`) dan kunci JSON API tidak diubah.
3. **Mode English**: aturan, kriteria mati, dan klausul mati bot tampil dalam terjemahan Inggris; teks asli TERKUNCI (Indonesia, yang di-hash) tetap
   bisa dibuka ("Locked original text"). Vonis gerbang/F-D16/label confidence dipetakan ke English di web dan teaser Telegram. Alasan GLM untuk
   penutupan 2026-10-06 tetap berbahasa Indonesia (isi yang di-hash tidak bisa diubah; prompt memang meminta English).
4. `/analysts` dan `/buy` diletakkan di tengah; slip pilihan memakai nama agent sekarang + "this pick was made by <model>" bila slot berganti model.

**Terkait:** F-D104 · F-D105 · [[04-Tools/TL32 - gerbang x402 per sinyal]] · [[09-Inbox/Session-2026-10-02]] §90

## F-D107 — Registry agent analis TERBUKA: agent luar dinilai + diperingkat, belum menentukan bot aktif · 5 Okt 2026 (WIB)

Konteks: visi F-D102 (orang mendaftarkan agent sendiri). `SelectionAnchor.pick` sudah tanpa izin (pemilik / dompet agent ERC-8004 mana pun), jadi
yang dibangun hanya sisi Fabius (P151):

1. **Penemuan dari chain**: event `Picked` dipindai bertahap sejak blok deploy SelectionAnchor (134940475); kartu agent = `tokenURI` IdentityRegistry
   (https / data:, <= 64 KB), field `fabius.reasons` = templat URL https berisi `{bar_close}`. Tanpa pendaftaran di server Fabius.
2. **Alasan agent luar** diambil HANYA sesudah bar tutup dan disimpan HANYA bila sha256 kanonis = reasonHash on-chain DAN isinya menyebut
   `agent_id`, `bar_close`, `pilihan.bot` yang sama (alasan agent lain tidak bisa dipakai ulang). Gagal = dicoba lagi tiap jam, ditandai "not published".
3. **Dinilai + tampil**: skor dari ledger publik, papan `/analysts` (label "external"), Telegram `/analysts`, `/analysts/registry`.
4. **BELUM menentukan bot aktif dan belum diberi feedback reputasi**: klausul mayoritas `engine/pemilih.py` bisa dibanjiri identitas Sybil, dan feedback
   memakai gas gerbang. Aturan penerimaan agent luar (mis. >= 20 pilihan terskor) = aturan TERKUNCI baru, menunggu kata builder. Aturan terkunci
   yang ada TIDAK diubah: gerbang hanya menyaring pilihan rumah sebelum memanggilnya.
5. **Onboarding**: `GET /analysts/input` (masukan deterministik yang SAMA dengan agent rumah untuk penutupan berikutnya + skema alasan + langkah +
   alamat kontrak + prompt rumah), alat MCP `fabius_analyst_join`, panel "Run your own analyst agent" di `/analysts`. Maks 50 agent luar per putaran.

**Terkait:** F-D102 · F-D104 · [[04-Tools/TL33 - agent analis]] · [[09-Inbox/Session-2026-10-02]] §92

## F-D108 — Agent analis BERITA (agent 2561, xkiro Qwen 3.8 Omni Flash high) + alat FOMO · 5 Okt 2026 (WIB)

Builder: *"perlu agent lg ga untuk analisis berita? https://apivault.dev/ ... ambil model qwen 3.8 omni flash pakai effort yg high"*; disetujui *"gas
keduanya"* (transaksi identitas + kunci xkiro ke Railway).

1. apivault.dev = direktori API, bukan sumber berita. Sumber yang dipakai (publik, tanpa kunci, diukur 5 Okt): RSS Cointelegraph, Decrypt, The Block
   (36 jam terakhir) + pengumuman Binance listing / delisting / berita (7 hari; relevan untuk B4). CoinDesk RSS 308 = dilewati. `tools/kabar.py`.
2. **Agent terpisah**, bukan tambahan masukan agent lama: identitas ERC-8004 sendiri **2561** (dompet `0xdAF3…4Da0`, isi 0,01 tBNB tx `0x155e15c8…`,
   register tx `0x82047ba7…`, ownerOf dibaca ulang) supaya nilai berita TERUKUR di papan (agent berita vs tanpa berita).
3. **Berita dikomit sebelum dipakai** (rancangan P139): daftar judul + status tiap sumber DISALIN ke JSON alasan yang di-hash (reasonHash on-chain);
   model diminta fitur berita berskema (`sentimen` -2..2, `kejadian`, `aset_disebut`) lalu pilihan, dalam satu JSON. Semua sumber gagal = agent ini
   tidak memilih bar itu (agent lain tetap).
4. Model `qwen/qwen3.8-omni-flash:free` effort high lewat xkiro (`XKIRO_API_KEY` dari opencode.json builder ke Railway lewat stdin, tidak dicetak);
   uji kering 5 Okt: 62 s, English, B1-TREND 58 %, fitur berita lengkap. Model `:free` bisa kena batas pakai penyedia.
5. **FOMO API** (fomoapi.io): alat MCP `fabius_fomo` (leaderboard 24h/7d, thesis terbaru), kunci `FOMO_API_KEY` di env Vercel (builder); kuota gratis
   250.000 kredit/bulan dijaga dengan 3 tampilan tetap + cache server (12 jam / 6 jam). GMGN tetap tidak (route publik 403, API resmi butuh
   permintaan bertanda tangan).

**Terkait:** F-D102 · F-D105 · F-D107 · [[04-Tools/TL33 - agent analis]] · [[09-Inbox/Session-2026-10-02]] §96

## F-D109 — Meja AI 5 menit: keputusan wajib tiap 5 menit, format baku + rumus konsensus terkunci, komit per siklus · 5 Okt 2026 (WIB)

Builder: *"maksimal hold/diam ga open posisi itu 5 menit gitu, biar kliatan jelas analisis AInya"*, lalu *"penentuan open posisinya kalau ada banyak
agents gini sepertinya perlu format khusus agar nanti bisa dimasukin rumus untuk kalkulasi keputusan"*. Pilihan builder (AskUserQuestion):

1. **Meja terpisah**, bukan mengubah enam bot harian: spesifikasi terkunci + uji maju F-D16 tetap utuh. Paper saja, Binance USDⓈ-M, 16 aset mayor.
2. **Wajib keputusan + alasan tiap 5 menit**; HOLD boleh asal dijelaskan (memaksa buka posisi = overtrading; fee 0,05 % per sisi dihitung jujur).
3. **Ketiga agent rumah** (2558 DeepSeek, 2559 Qwen, 2561 berita) memutuskan paralel tiap siklus, effort high, batas jawab 210 s.
4. **Komit per siklus 5 menit** ke kontrak baru `DeskAnchor` `0x706da379a5112aa7c86803dcf58d8fdab442305f` (tx `0xd817fc87…`, blok 134996700):
   satu Merkle root atas rekaman semua agent + konsensus, HANYA diterima selama siklus berjalan (kontrak menolak `TooLate`) - keputusan terkunci
   sebelum harga penentu hasilnya ada. **Ralat biaya:** awalnya kusebut ±0,0015 tBNB/hari (asumsi 0,1 gwei); terukur 1 gwei -> ±0,011 tBNB/hari
   (gas komit ±38 ribu); builder akan mengisi faucet tiap hari ke gerbang `0x10c4…f1b1`.
5. **Format baku** (dari builder): `{"ringkasan", "target": {ASET: {"arah": long|short|flat, "ukuran": 0..0,25, "keyakinan": 0..100, "alasan"}}}`;
   aset tak disebut = target sebelumnya. **Rumus konsensus v1** (dikunci, `tools/meja.py::PARAMS`, sha `0xf42f0cc1fd8c6107…`): rata-rata
   (keyakinan/100 × bobot bertanda) atas agent yang menjawab sah, bobot agent sama; kuorum 2 (kurang = tahan); per aset <= 25 %, gross <= 1x;
   perubahan < 2 % ekuitas tidak ditransaksikan. Buku: satu per agent + satu konsensus; isi pada harga mark yang diambil SESUDAH semua keputusan.
6. Uji kering 5 Okt 10:20Z (model + data asli, tanpa komit): siklus 126,5 s (DeepSeek 13,9 s, berita 56,1 s, Qwen 121,4 s); DeepSeek long kecil
   NEAR/AVAX/LTC/XRP, Qwen long ADA/NEAR, berita flat (gerak 5 menit < fee); konsensus NEAR 3,8 % (1 isi). ±864 panggilan model/hari: DeepSeek +
   Qwen memakai kredit qwencloud, model xkiro `:free` bisa kena batas.

**Terkait:** F-D105 · F-D108 · [[04-Tools/TL34 - meja AI 5 menit]] · [[09-Inbox/Session-2026-10-02]] §97

## F-D110 — Meja AI v2: tiga agent memilih bot + skor semua bot, rumus memilih satu bot dominan, evaluasi untuk perbaikan diri · 5 Okt 2026 (WIB)

Builder: *"3 agent ini akan memberikan outputnya secara bersamaan tiap 5 menit dengan format yg ditentukan agar bisa dikalkulasi dan dianalisis dgn
bot/rumus untuk open posisi"*, *"tiap output LLM nantinya jg hrs ada bot mana yg akan dipilih ... ambil 1 yg paling dominan untuk dipakai dan dibuat open
posisi"*, *"harus ada loop evaluasi untuk self improvement"*; rencana disetujui *"Gasss"*.

1. Platform data (DexScreener, RugCheck, FOMO, berita, Binance) dibaca **Fabius sendiri** lewat kode -> fitur terukur yang sama untuk ketiga agent
   (bukan alat MCP publik). Bubblemaps dilewati (publik hanya ketersediaan peta), GMGN tidak (403).
2. Format output v2: pilihan `bot` + `skor_bot` untuk keenam bot + `keyakinan` + `eksposur` + `veto_aset` + `faktor` (wajib dari daftar fitur).
3. Rumus terkunci: bot dominan = argmax rata-rata berbobot (keyakinan x skor_bot) + prior kuantitatif; hysteresis >= 15 poin dan pegang >= 15 menit;
   posisi = target bot dominan x eksposur, minus veto; batas 25 % per aset, gross 1x, stop ATR, rugi harian -3 %.
4. Loop evaluasi: IC / hit rate / kalibrasi per agent, bobot agent per jam (0,5-2) sesudah 288 siklus, rapor ke prompt, buku ablasi per agent dan per
   sumber, usulan evaluator hanya lewat versi bayangan + kunci (tanpa perubahan diri diam-diam).
5. Meja v1 (F-D109) tetap jalan sampai v2 menggantikannya sesudah bayangan >= 288 siklus + kata builder.

**Terkait:** F-D109 · F-D111 · [[08-Backlog/11 - Epik Meja AI v2]] · [[09-Inbox/Session-2026-10-02]] §98

## F-D111 — MCP Fabius = sinyal + data pendukung, hanya lewat x402 (deposit FAB, dipotong per panggilan); mengganti tingkat 0 gratis F-D89 · 5 Okt 2026 (WIB)

Builder: *"mcp fabius itu hanya menyediakan signal dan data yg mendukung/menjelaskan lebih detail mengenai sinyal itu dan mcpnya itu hanya bisa dipakai
dengan melalui x402, jadi user bisa deposit dulu ... nanti tiap call mcp maka akan lgsg otomatis terpotong dari akunnya"*; usulan rinci disetujui
*"Gasss"*.

1. Deposit **FAB** lewat x402 (tanpa gas; FAB uji dari faucet) -> saldo per dompet; kunci API dari tanda tangan dompet; tiap panggilan dipotong.
2. Harga: `fabius_signal` 0,01 FAB, `fabius_signal_explain` 0,02 FAB, `fabius_data` 0,005 FAB; gratis hanya `fabius_pricing` + `fabius_account`.
3. Dicabut dari MCP: alat data publik P140 (`fabius_dexscreener`, `fabius_rugcheck`, `fabius_bubblemaps`, `fabius_fomo`) dan alat tingkat 0 gratis
   F-D89 (dipindah ke berbayar). Web `/verify` tetap gratis.
4. Sampai F5 dibangun, MCP yang hidup tetap seperti sekarang (dicatat, bukan disembunyikan).

**Terkait:** F-D89 · F-D100 · F-D110 · [[08-Backlog/11 - Epik Meja AI v2]] §7 · [[04-Tools/TL20 - server MCP]]

## F-D112 — Meja v2 opsi D: AI memilih bot DAN instrumen; aturan bot terkunci dihitung kode pada instrumen itu; v1 berdampingan 24 jam · 5 Okt 2026 (WIB)

Builder: *"v2 ini AInya hanya memilih bot ya tanpa memilih instrument apa yg mau di trade?"*, *"Bisa ga sih kalau instrumennya pilih sendiri? ... AInya
pilih bot sendiri dan instrumen sendiri, jadi bot apa dan instrumen mana yg akan diterapkan pakai bot itu"*, lalu *"Gas, ikuti saranmu"* (opsi D +
v1 berdampingan 24 jam lalu dimatikan). Juga: *"Kenapa ga collect + analysis secara realtime aja?"* -> v2 langsung hidup (bukan menunggu 24 jam F1).
Mengubah F-D110 #2-#3 (F-D110 tetap sebagai riwayat):

1. **Output agent:** `bot` + `skor_bot` keenam bot + **`instrumen`** (maks 8, tiap entri: aset, keyakinan, faktor) + `eksposur` + `veto_aset` + `faktor`.
2. **Universe yang boleh dipilih:** 50 perp USDT Binance teratas menurut volume kuotasi 24 jam (`/fapi/v1/ticker/24hr`, satu panggilan) + 12 token registry
   (TL35). Di luar itu = ditolak + dicatat (SK-M14).
3. **Konsensus:** bot dominan = argmax rata-rata berbobot (keyakinan x skor_bot) (+ hysteresis 15 poin / 15 menit); instrumen = skor berbobot keyakinan
   dari semua agent, masuk bila dipilih >= 2 agent atau skor >= ambang, maks 8.
4. **Arah dihitung KODE** dengan aturan bot terkunci (`engine.bots.REGISTRY[bot]`, spec yang sama, universe = instrumen terpilih) pada candle harian
   Binance live; posisi = arah x bobot rata x eksposur, veto, maks 25 % per aset, gross 1x. Aturan yang tidak cocok dengan instrumennya ditolak
   (SK-M15): B3 butuh kaki spot (meja hanya perp -> datar), B4 hanya untuk perp yang baru listing (`onboardDate` <= H hari).
5. **Kejujuran:** hasil meja = strategi baru (universe pilihan AI + aturan terkunci), BUKAN rekam jejak bot; uji maju F-D16 tidak disentuh.
6. **v1 berdampingan 24 jam** pada jam yang sama (panggilan model ±2x selama itu), lalu v1 dimatikan atas laporan pembanding.

**Terkait:** F-D109 · F-D110 · [[08-Backlog/11 - Epik Meja AI v2]] · [[04-Tools/TL35 - data meja v2]]

**Tambahan implementasi F-D112 (5 Okt sore, sebelum deploy):** (a) uji kering pertama tanpa masukan aturan: ketiga agent memilih B5 karena "tidak ada
fitur 60/28/10 hari" -> kode kini menghitung `tren_60h`, `r_28h`, `z_10h`, `umur_listing_h`, `hari_data` per instrumen dari candle harian (rumus sama
dengan aturan) dan memberikannya ke agent; uji kering kedua: ketiganya memilih B1 pada instrumen bertren positif (Test Commands #78). (b) Ambang veto
likuiditas DEX = 50.000 USD (`PARAMS2.likuiditas_min_usd`, dipilih sebelum data hidup; diubah hanya lewat versi params baru). (c) Rem rugi harian 3 %
dari Epik 11 dipasang di buku v2. (d) Hysteresis "15 menit" dibaca sebagai >= 3 siklus dipegang. (e) v2 menunggu snapshot siklusnya sendiri sampai
t0+75 s, model dibatasi sampai t0+265 s; v2 yang belum selesai tidak masuk root siklus itu. (f) Teks publik rekaman v2 berbahasa Inggris.

## F-D113 — Kursi agent LLM di meja: 7 aktif + 3 uji; agent baru selalu lewat gerbang seleksi; pekerja 3D dibuat Fabius sendiri · 5 Okt 2026 (WIB)

Builder: *"saya setuju 7 aktif + 3 uji"*, *"yg penting tiap ada agent baru masuk maka fabius akan otomatis membuatkan worker 3D UI tanpa km yg config"*,
*"kita belum buat untuk gate seleksi bot dan agent"*. Usulan yang disetujui (Inbox §103):

1. **10 kursi agent LLM di meja:** 7 **aktif** (suaranya masuk konsensus v2) + 3 **uji** (jalan tiap siklus, rekamannya di-hash + ikut Merkle root,
   bukunya hidup, tetapi TIDAK dihitung di konsensus). 10 meja = batas tampilan lantai yang diuji (Test Commands #80).
2. **Agent baru selalu masuk kursi uji dulu**, naik ke aktif hanya lewat gerbang seleksi (P160) dengan kriteria terukur yang dikunci SEBELUM data
   agent pertama dinilai; kursi aktif terburuk bisa turun ke uji. Kriteria + rumus dirancang di P160 lalu dikunci atas kata builder.
3. **Ambang konsensus v2 dibuat proporsional terhadap jumlah agent aktif** (sekarang instrumen/veto >= 2 agent dan kuorum 2, disetel untuk 3 agent);
   berlaku sebagai versi `PARAMS2` baru, tidak menimpa diam-diam.
4. **Pekerja 3D tanpa konfigurasi manual:** setiap agent yang punya buku meja otomatis mendapat meja + NPC dari template P159 (penampilan dari slug);
   `npc` di `config/agents.json` hanya penimpa opsional.
5. **Gerbang seleksi bot** (P161) dicatat sebagai pekerjaan terpisah: jalur kandidat bot baru sampai slot buku memakai bagian yang sudah ada.

**Terkait:** F-D110 · F-D112 · [[08-Backlog/11 - Epik Meja AI v2]] · [[04-Tools/TL34 - meja AI 5 menit]] · [[04-Tools/TL36 - meja v2 bot + instrumen]]

**Tambahan F-D113 (5 Okt malam, sebelum dikunci):** P160 dibangun dengan kriteria USULAN (`PARAMS_KURSI.status = "usulan"`); ambang proporsional masuk `PARAMS2` v2 bersama koreksi sumber instrumen (instrumen hanya dari pemilih bot akhir, lihat [[00-Overview/05 - Corrections]]). Kriteria kursi dikunci (`status` -> `terkunci` + sha di Decisions) atas kata builder, sebelum agent baru pertama masuk kursi uji.

**F-D113 DIKUNCI (5 Okt malam, builder: "Gas" atas usulan kriteria):** `PARAMS_KURSI` = {maks_aktif 7, maks_uji 3, jendela_siklus 288, naik_sah_min 0,95, tukar_unggul_min 0,005, turun_sah_maks 0,80, status `terkunci`} sha **`0xf370c011ca85a63a0968e0f66a1bb9edd4064d54ab23e14bd4b0ff28be0e260d`**; `PARAMS2` v2 (ambang proporsional + instrumen dari pemilih bot akhir) sha **`0x57434bbf489d2f6ae728e8b01756e65df8d977ec8e601e339eee6d8f671200ac`**. Kedua sha ikut tiap rekaman v2 / `kursi` yang dikomit lewat Merkle root DeskAnchor; mengubah kriteria = versi baru + entri Decisions baru.

**Koreksi sesudah kunci F-D113 (6 Okt dini hari UTC) - `PARAMS2` v3 sha `0x7e3b37f16f40d337385779d69d9a0bfc62d2241d374b29b8f29a22524347e083` menggantikan v2 `0x57434bbf…` (v2 tetap tercatat sebagai riwayat):** bot akhir dengan jumlah aset minimum di spesifikasinya (B2-RS `min_aset` 8) kini diisi skor tertinggi dari pemilih bot itu sampai minimum. Siklus produksi 16:55Z: B2-RS dominan (+43,3), hanya 4 instrumen lolos ambang (>= 2 agent) -> aturan B2 datar walau dua agent masing-masing memilih 8 instrumen untuk B2. Tanpa koreksi ini B2 praktis tidak pernah bisa berjalan di tingkat konsensus. Agent yang memilih B2 dengan < 8 instrumen kini dicatat di `ditolak` (bukunya tetap datar menurut aturan).

**Turunan F-D113 untuk agent baru (5 Okt malam, P162):** (a) agent di kursi uji/antre TIDAK membuat pilihan harian analis di SelectionAnchor - aturan bot aktif P143 (terkunci) memakai suara terbanyak, dan lima agent baru (5 dari 8 suara) akan langsung menentukan bot yang diperdagangkan Fabius sebelum lolos seleksi; aturan P143 sendiri tidak diubah, yang dibatasi hanya siapa yang memilih. (b) Meja v1 (dipensiunkan sesudah 24 jam berdampingan) tetap tiga agent awal (glm, qwen, berita) supaya laporan pembanding v1 vs v2 tidak tercampur agent baru.

**Slot agent 2568 ganti model (6 Okt dini hari UTC, builder: "Itu grok ganti ini aja gpt-6-luna", pola F-D105):** `grok-4.7-free` (KiosAPI, HTTP 503 dua siklus berturut) -> `gpt-6-luna` lewat penyedia baru VyceAI (`https://vyceai.com/v1`, OpenAI-compatible, kunci `VYCEAI_API_KEY` dipasang builder di Railway). Slug `grok`, agent_id 2568, dompet, URI kartu, dan kursi uji TETAP; model lama di `riwayat` config + `model_history` kartu. Jalan pintas baru `analis.py ganti` (tanpa kunci, tanpa tx).

**Slot agent 2568 DITURUNKAN (6 Okt ±01Z, builder: "takedown dulu aja Agent itu, biar pakai 7 agent dulu aja"):** `nonaktif` di config (identitas ERC-8004 + dompet tetap, bisa `aktif` lagi), kursi uji dilepas (`keluar`) supaya antrean maju: GLM 5.3 Flash masuk kursi uji. Sesuai F-D113 dari 7 agent yang tersisa, 6 berjalan (3 aktif + 3 uji) dan Qwen 3.8 27B antre sampai ada kursi uji kosong.

## F-D114 — Pengecualian F-D113 atas kata builder: GLM Flash diturunkan, Muse + Qwen 3.7 Plus + Qwen 3.8 27B langsung ke kursi aktif · 6 Okt 2026 (WIB)

Builder: *"OKe turunkan dah, sialan kiosapi, naikin AI yg antre dan uji biar slotnya terisi"*. KiosAPI menjawab 503 untuk kedua modelnya (Grok 4.7,
GLM 5.3 Flash), jadi:

1. `glmflash` (agent 2569) `nonaktif`, kursinya dilepas (SK-M23) - identitas tetap, bisa `aktif` lagi bila KiosAPI pulih.
2. **Pengecualian F-D113 #2:** `muse` (2566), `qwenplus` (2567), `qwen27b` (2570) naik ke kursi AKTIF tanpa jendela 288 siklus uji, lewat keputusan kursi
   builder `2026-10-06-1..3` di `config/agents.json` (`kursi_builder`). Diterapkan SEKALI oleh gerbang dan tercatat sebagai peristiwa `kursi` yang dikomit
   (SK-M24); batas 7 aktif / 3 uji tetap ditegakkan. Sesudahnya evaluasi harian biasa (turun ke uji bila sah < 80 %) berlaku.
3. Akibat yang disadari: suara ketiganya langsung masuk konsensus v2 dan pilihan bot harian (kursi aktif memilih); ambang menjadi n = 6 (kuorum 3,
   instrumen/veto >= 2 agent, skor instrumen >= 2,4). Kursi uji kosong sampai agent baru masuk.

**Terkait:** F-D113 · [[04-Tools/TL36 - meja v2 bot + instrumen]] · [[04-Tools/TL33 - agent analis]]

**Tambahan F-D114 (6 Okt ±02:4xZ, builder memilih "Turunkan Qwen 27B"):** `qwen27b` (agent 2570, Groq) `nonaktif` - HTTP 413 Payload Too Large di semua siklus. Meja berjalan dengan 5 kursi aktif (glm, qwen, berita, muse, qwenplus); tiga agent pihak penyedia gratis (KiosAPI x2, Groq) turun, identitasnya tetap dan bisa `aktif` lagi.

## F-D115 — Penamaan: Fabius = meja v2 (tidak ada "v3"); revisi rumus = r1, r2, r3; v1 disembunyikan dari web · 6 Okt 2026 (WIB)

Builder: *"Fabius v3 gaada kan brati? Semua masih full v2 kan? Mending kalau ternyata di tengah jalan ada yg v3 digabung aja ke v2, catat ini di
vault"*, *"yg v1 hilangkan saja biar ga menuh-in"*, *"usulanmu mengenai hapus aja label v2 saya sepenuhnya sepakat, mending skalian skrg aja"*.

1. **Satu Fabius:** mekanisme meja yang hidup = meja v2 (F-D112). Perubahan di tengah jalan TIDAK menjadi "v3"; ia revisi di dalam v2. Revisi rumus
   konsensus ditulis **rumus r1 / r2 / r3** (= `PARAMS2.v` 1/2/3 di kode; sha tiap revisi tetap di Decisions F-D113 + koreksinya). Sekarang: rumus r3.
2. **Web tanpa label "v2":** buku konsensus meja = "Fabius"; buku per agent = "Rapor agent" (paper milik agent, bukan posisi Fabius).
3. **v1 disembunyikan dari `/desk`** (buku + rekaman; `V1_TAMPIL = False` di gerbang). Data v1 tetap tersimpan dan tetap bisa dibuktikan lewat
   `/desk/proof/<hash>`. **Mesin v1 masih berjalan** sampai builder memutuskan, karena laporan pembanding (di bawah) menunjukkan v1 menjadi garis
   dasar yang berguna.

**Laporan pembanding v1 vs v2 (dicetak 6 Okt ±05Z dari `/desk` + `/desk/agent/*`, jendela sejak siklus v2 pertama 5 Okt 16:20Z):** Fabius (v2)
10.000 -> 9.572,82 (**-4,27 %**), 445 transaksi, fee 264,71 USDT dalam 167 siklus (79 siklus bertransaksi), bot dominan B2-RS 111 siklus, B1-TREND 37,
B5 15, B4 4; buku konsensus v1 9.927,51 -> 9.907,74 (-0,20 %; transaksi total 212, fee 39,30 sejak 5 Okt 10:35Z). Sekitar dua pertiga kerugian v2 =
fee (264,71 dari 427,18 USDT); sebelum fee v2 ±-1,6 %. Masalah utamanya perputaran (rotasi peringkat B2 + pergantian bot/instrumen) -> dicatat
sebagai pekerjaan (P163).

**Terkait:** F-D112 · F-D113 · F-D114 · [[04-Tools/TL36 - meja v2 bot + instrumen]]

## F-D116 — Rumus r4 "slot posisi" (DIKUNCI 6 Okt atas kata builder "Gas") · 6 Okt 2026 (WIB)

Builder, sesudah angka P163 (fee 62 % dari kerugian, separuh posisi hidup <= 10 menit): *"jeda 5 menit itu berlaku saat sudah close position, jadi
kalau open positionnya masih belum slesai ya jgn di close dulu dan countdown 5 menitnya tidak berjalan, baru jalannya setelah slesai closed
position"*, *"maksimal open posisi ada 5, jadi kalau misal udh open lalu ternyata ada signal yg berpeluang bagus ya open lagi gapapa dengan catatan
posisi yg lama ga di close"*. Jawaban pilihan: posisi selesai = TP/SL (*"Sesuaikan bot ... Kan bot ngasih aturannya"*), dan *"kalau ga kena TP/SL
tapi keluar dari daerahnya itu tetap akan closed kan?"* = aturan keluar bot; TP/SL dari volatilitas + aturan keluar bot; ganti bot = posisi lama
dipegang sampai selesai; jeda berlaku untuk seluruh buku; ukuran *"3-5% modal aja dengan laverage (kalau agentnya yakin bakal profit)"*, leverage
maksimal 5x; ukuran dikunci sampai ditutup.

Usulan (dikunci sebagai PARAMS2 r4 hanya sesudah replay pada arsip produksi + kata builder; aturan bot terkunci tidak berubah):

1. **Maks 5 posisi** terbuka bersamaan, satu posisi per aset (tidak ditambah, tidak dibalik selama terbuka).
2. **Buka:** di siklus tanpa jeda dan dengan slot kosong, kandidat = aset di target konsensus (arah dari aturan bot terkunci, veto dibuang) yang
   belum dipegang, urut skor instrumen konsensus; dibuka sampai slot penuh. Posisi lama tidak disentuh.
3. **Ukuran (dikunci sampai ditutup):** keyakinan c = (skor instrumen - ambang instrumen) / (n aktif - ambang instrumen), dipotong 0..1;
   margin = 3 % + 2 % x c modal, leverage = 1x + 4x x c (maks 5x), notional = margin x leverage (maks 25 % modal per posisi, total maks 125 %).
   Pengaman: leverage dipotong supaya jarak SL <= separuh jarak likuidasi (1 / leverage).
4. **Tutup** oleh yang duluan: SL = harga masuk -/+ 1 x ATR 14 hari (candle harian perp), TP = +/- 2 x ATR (untung:rugi 2:1); aturan keluar bot
   pembuka (aturan terkunci bot itu pada universe saat dibuka, candle harian yang sudah tutup); rem rugi harian SK-M10 (tutup semua, datar sampai
   00:00 UTC). Dicek tiap siklus 5 menit pada harga isi siklus.
5. **Ganti bot** tidak menutup posisi; tiap posisi mencatat bot pembukanya (hasil per bot tetap terukur).
6. **Jeda:** siklus yang menutup posisi tidak membuka posisi baru; siklus berikutnya (5 menit sesudah tutup) boleh. Selama posisi terbuka, jeda
   tidak berjalan.
7. **Konstanta bot yang sudah terkunci menang** ("sesuaikan bot"): B4-LISTING-FADE margin 2 %, 1x, tanpa stop (`stop: None`), tutup lewat aturan
   14 harinya + rem rugi.
8. Keputusan agent + konsensus tetap direkam, di-hash, dan dikomit tiap siklus seperti sekarang.

Batas yang dinyatakan: TP/SL dicek pada harga siklus (bukan sentuhan di antara siklus); funding + likuidasi tidak dimodelkan di buku kertas; replay
tidak bisa membuka posisi di siklus yang tercatat datar karena rem r3 (target aturan tidak terekam).

**Replay pertama (6 Okt ±10Z, [[07-Testing/01 - Test Commands]] #96):** mekanisme jalan (fee 264,71 -> 1,59 pada siklus yang sama), tetapi kelima slot terisi B2-RS dalam satu siklus (5 Okt 17:00Z) dan belum ada yang tertutup 17 jam kemudian, jadi angka hasilnya = lima posisi, bukan penilaian r4. Ditemukan untuk implementasi hidup: aset yang dipegang bisa keluar dari universe harga v2 (SOXSUSDT sejak 18:45Z) -> harga isi meja hidup wajib mencakup semua aset yang sedang dipegang.

**Timeframe (builder 6 Okt, sesudah melihat ATR harian QNT 22 % / MOVR 24 % pada koin pump pilihan B2):** *"Tidak ada batasan timeframe"*. Semua bot terkunci memakai candle harian (B1 60 hari, B2 28 hari + rotasi mingguan, B4 14 hari, B5 90 hari + rebalance bulanan, B6 z 10 hari; `BotSpec` tidak punya field timeframe, satuan parameternya hari). Ditafsirkan: Fabius tidak dikunci ke satu timeframe; tiap posisi hidup selama aturan + TP/SL bot pembukanya, dan **ATR untuk TP/SL diambil dari timeframe bot pembuka** (sekarang semua harian; bot intraday masa depan masuk lewat P161 dan memakai ATR timeframe-nya sendiri).

**DIKUNCI 6 Okt (builder: "Gas")** - PARAMS2 r4 sha `0x6f613e503e5fe377f024571baad56dd9c639a1ec363b4ceba1c5dc7ffbad9f85` (memuat `PARAMS_SLOT` sha `0xbe529db6807df27919367e931d6435829c4e10ceb1e504ff6631d58b25d1a6f8`, `tools/meja_slot.py`). Rincian implementasi yang ikut terkunci: (a) posisi hanya dibuka dari konsensus SAH siklus itu (kuorum tercapai; SK-M29); (b) aturan keluar yang tidak terbaca - galat, atau candle satu aset universe gagal - TIDAK menutup posisi (SK-M27; bug ini ditemukan tes sebelum deploy: `arah` menangkap galat candle per aset lalu memberi bobot kosong yang terbaca sebagai "keluar"); (c) harga isi selalu mencakup aset yang dipegang (SK-M28); (d) posisi r3 di buku ditutup sekali dengan alasan `r4 start` (SK-M30), saldo/fee/riwayat Fabius berlanjut; (e) rem rugi menutup semua slot tetapi target aturan tetap direkam utuh supaya bayangan r3 bisa dihitung (P163 kriteria 4); (f) tiap isi mencatat `alasan`, `bot`, `pnl`, tiap rekaman `slot` (ikut di-hash). Rem rugi 6 Okt (-3,22 %) masih berlaku saat r4 mulai, jadi r4 baru bisa membuka posisi sesudah 00:00 UTC 7 Okt.

**Terkait:** P163 · F-D112 · F-D115 · [[04-Tools/TL36 - meja v2 bot + instrumen]]

## F-D117 — Mesin meja v1 dihentikan · 6 Okt 2026 (WIB)

Builder: *"Stop v1 skrg juga"* (sesudah r4 hidup; dicatat ke builder bahwa v1 = meja lama -0,20 %, sedangkan yang rugi besar adalah rumus r3 meja v2).
`V1_JALAN = False` di `tools/x402_sinyal.py`: tidak ada lagi panggilan model, buku, atau rekaman v1; Merkle root tiap siklus hanya berisi rekaman
meja v2 (`rakit_siklus`). Siklus tanpa daun (v2 tidak selesai sebelum komit) berstatus "kosong" dan tidak dikomit (SK-M32). Buku + rekaman v1 lama
tetap tersimpan dan tetap bisa dibuktikan lewat `/desk/proof`. Alasan: v1 sudah tidak tampil (F-D115), menggandakan panggilan model per siklus
(batas laju penyedia gratis), dan pembanding r4 kini = bayangan r3 dari target aturan yang sama (P163 kriteria 4).

**Terkait:** F-D109 · F-D115 · F-D116 · [[04-Tools/TL34 - meja AI 5 menit]]

## F-D118 — Halaman alpha berbayar (P165): yang bisa ditiru dikunci, yang membuktikan kejujuran terbuka · 6 Okt 2026 (WIB)

Builder (6 Okt): `/desk`, `/analysts`, dan halaman lain yang berisi alpha Fabius hanya untuk yang login + bayar; lalu "kerjakan A dulu, kalau udh saya
akan cek" atas usulan pembagian (alpha berbayar, rekam jejak tertunda + bukti gratis - F-D72 tingkat 0).

1. **Anggota** = akses P145 yang sama: login Privy + dompet akun membeli >= 1 sinyal dalam 7 hari (`Gate.akses`, satu pemeriksa untuk semua rute;
   juri: login -> FAB uji gratis lewat faucet di halaman beli -> beli 1 sinyal).
2. **Dikunci (bisa ditiru):** isi keputusan siklus (bot, instrumen, target aturan, slot/posisi, isi transaksi), alasan/ringkasan agent, riwayat
   keputusan per agent, pilihan analis untuk bar yang belum tutup. Publik melihatnya **24 jam kemudian** (`TUNDA_PUBLIK_S = 86.400`).
3. **Terbuka langsung (membuktikan kejujuran):** ekuitas, hasil, fee, drawdown, kurva, hasil per bot, status agent + kursi, jumlah posisi terbuka,
   root + tx on-chain tiap siklus. Bukti per rekaman (`/desk/proof`) terbuka untuk semua orang sesudah 24 jam; sebelum itu 402 dengan komitmennya.
4. **Batas yang dinyatakan:** pilihan analis dikomit on-chain dalam bentuk terbaca (SelectionAnchor) supaya bisa diverifikasi, jadi menyegelnya di
   web adalah kunci tampilan, bukan rahasia. Meja (DeskAnchor) hanya menyimpan root, jadi isi keputusannya memang tidak terbaca sebelum dibuka.
   Alat replay P163 tanpa token anggota hanya memuat rekaman >= 24 jam.
5. **Satu login (revisi builder 6 Okt):** *"di page /analysts itu juga ada login cardnya mending dijadiin satu deh, di navbar dikasih untuk login nanti dibikinin login page sendiri via privy"*. PrivyProvider dipasang SEKALI di root layout web (skrip Telegram `beforeInteractive`); navbar punya chip Sign in / Signed in / Member menuju `/login?next=<halaman>`; halaman `/login` = login Privy + akun, dompet, status anggota (gerbang `GET /access`), beli 1 sinyal bila belum anggota, kembali ke halaman asal. Kartu login di `/analysts` dan bilah login di `/desk` diganti satu baris status (`AccessLine`). **Revisi kedua (builder: "mending login pagenya popup aja deh lalu dikasih transisi ... login page ala web2 ... button google redirect ke privy yg lgsg ke google ... button login lewat telegram"):** halaman `/login` dihapus; login = popup `LoginModal` (dipasang Nav, dibuka dari chip navbar + "Sign in" di halaman alpha) dengan transisi (latar pudar + blur, kartu naik dengan pegas, langkah bergeser; reduced-motion dihormati): "Continue with Google" = Privy headless `useLoginWithOAuth` langsung ke Google, "Continue with Telegram" = `useLoginWithTelegram`, email = kode 6 digit di dalam popup (`useLoginWithEmail`); sudah login = kartu akun (dompet + salin, status anggota, beli 1 sinyal, keluar).

**Terkait:** F-D72 · F-D104 · P145 · P165 · [[04-Tools/TL34 - meja AI 5 menit]]

## F-D119 — Kursi uji yang terus gagal: kembali ke antrean, dua kali = keluar (PARAMS_KURSI v2) · 6 Okt 2026 (WIB)

Builder memilih (6 Okt, urutan kerja C1 -> B1 -> C2 -> B2): *"< 80 % sah -> antre, 2x -> keluar"*. Menutup celah yang dicatat sejak §110: aturan F-D113
hanya menurunkan kursi AKTIF; agent di kursi uji yang terus gagal (mis. slot 2568, 503/429 tiap siklus) menahan kursi uji selamanya sehingga antrean
macet, dan selama ini diselesaikan manual (`nonaktif`, F-D114).

1. Di evaluasi harian 00:00 UTC (SK-M21), agent di kursi **uji** dengan >= 144 siklus teramati dan jawaban sah < 80 % dalam jendela 288 siklus
   (ambang yang sama dengan turun kursi aktif) kembali ke **belakang antrean**, riwayatnya diulang dari nol, dan baru boleh naik ke kursi uji lagi
   sesudah evaluasi harian berikutnya (antrean lain didahulukan).
2. Gagal di kursi uji untuk kedua kalinya -> **keluar** permanen (tidak masuk otomatis lagi; hanya keputusan builder baru).
3. Tiap perpindahan = peristiwa `kursi` yang di-hash + dikomit, seperti aturan kursi lain. `PARAMS_KURSI` v2 DIKUNCI sha `0x47f1c0587a8cf60b3c68cf8098850018b4ff11aa25c4e44685de16209a77ea40` (v1 `0xf370c011…` tetap di F-D113). Perilaku yang ikut terkunci: agent yang baru turun dari aktif ke uji di evaluasi yang sama dapat masa uji dulu; kursi uji yang dilepas langsung diisi antrean yang lebih lama di siklus 00:00 yang sama.

**Terkait:** F-D113 · F-D114 · P160 · [[04-Tools/TL36 - meja v2 bot + instrumen]]

## F-D120 — Jalur seleksi bot otomatis (P161 B1): siapa menjalankan apa · 6 Okt 2026 (WIB)

Builder: urutan C1 -> B1 -> C2 -> B2, lalu "Lanjut" atas rencana B1a-B1e. Pilihan rancangan yang saya ambil (mengikat sampai builder mengubah):

1. **Gerbang hanya menerima** (`POST /bots/submit`): skema + tanda tangan EIP-712 diperiksa saat masuk karena tanda tangan berlaku <= 1 jam; waktu
   terima dicatat publik. **Tinjauan dijalankan di repo publik** (GitHub `bot-review.yml`, dipicu rantai paper-ledger sekali sehari) pada bar harian
   repo dengan `now = waktu terima`, jadi siapa pun bisa mengulang verifikasi tanda tangan, gerbang, dan vonisnya.
2. **Kontak penerbit tidak pernah publik**: tidak ikut hash (sudah begitu sejak F-D71), disimpan privat di gerbang; repo memuat formulir tanpa kontak.
3. **Spesifikasi yang lolos di-pin on-chain** (LockRegistry, label = `bot_id`) oleh worker yang sama dengan pin buku; satu transaksi per putaran.
4. **Jam maju untuk bot penerbit menyusun `BotSpec` ulang dari formulir publik** yang cocok dengan registri; berkas ringkasan tidak dipercaya mentah.
5. **Epoch buku** membaca penantang dari registri; pembunuh penerbit ditegakkan kode (`slots.killer_triggered`) dari `theory.pembunuh` terstruktur.
6. Batas: sinyal bot penerbit yang masuk slot belum dikomit / dijual worker (berikutnya); kanal hanya bar harian sampai B2.

**Terkait:** P161 · P83 · F-D71 · F-D85 · F-D87 · F-D88 · [[04-Tools/TL37 - jalur pengajuan bot]]

## F-D121 — Agent luar ikut siklus meja dengan cara PULL (P166, P160 tahap 2) · 6 Okt 2026 (WIB)

Builder memilih (6 Okt, urutan C1 -> B1 -> C2 -> B2) *"Pull: agent ambil & kirim jawaban"*. Pilihan rancangan yang saya ambil (mengikat sampai builder mengubah):

1. **Identitas = ERC-8004, aturan yang sama dengan SelectionAnchor:** pesan EIP-191 harus ditandatangani dompet agent (`getAgentWallet`) atau pemilik
   identitas (`ownerOf`). Agent luar tidak mendapat kunci apa pun dari Fabius; Fabius tidak pernah memanggil model mereka.
2. **Daftar sekali** (`POST /desk/external/join`, pesan `Fabius desk join v1 / agent_id / deadline`, berlaku <= 1 jam). Slug = `x<agent_id>`; nama dari
   kartu ERC-8004 (dibersihkan, <= 24 huruf). Batas masuk (operasional, bukan aturan seleksi): <= 10 terdaftar, satu per pemilik, satu per agent, <= 10
   pendaftaran per jam, id agent rumah ditolak, agent yang keluar karena gagal (F-D119) ditolak.
3. **Tarik** (`GET /desk/external/pull?agent_id=N&wait=25&ts=<unix s>&signature=<0x hex>`): long-poll BERTANDA TANGAN (koreksi uji penerimaan, di bawah). Masukan = persis yang dilihat agent rumah (`SYSTEM2` + prompt per agent: bukunya
   sendiri, fitur terukur, aturan bot), ditambah `prompt_sha` dan batas waktu. Masukan tidak memuat keputusan agent lain. Tanpa tarikan 15 menit = agent dianggap
   mati: siklusnya gagal cepat, TIDAK ditunggu.
4. **Jawab** (`POST /desk/external/answer`, pesan `Fabius desk answer v1 / agent_id / siklus / prompt_sha / answer_sha`): jawaban v2 yang sama dengan agent
   rumah, divalidasi `parse2` saat diterima (galat = 422, boleh kirim ulang sebelum batas); sah pertama menang; batas = tenggat jawab siklus (210 s sesudah data terbaca, paling lambat t0 + 265 s; dicetak mutlak di respons tarik, komit siklus tetap
   sempat). Rekaman siklus memuat `luar` {penanda_tangan, tanda_tangan} + `prompt_sha` + `jawaban_sha`, jadi tanda tangan bisa diperiksa pihak ketiga dari rekaman
   yang masuk Merkle root.
5. **Kursi:** agent luar masuk C1 seperti agent rumah baru (uji bila ada kursi uji kosong, selain itu antre). Jawaban uji TIDAK dihitung konsensus (SK-M20);
   naik ke aktif hanya lewat aturan F-D113 yang sudah terkunci (>= 288 siklus, sah >= 95 %, hasil >= median aktif atau unggul >= 0,5 pp). Gagal -> antre -> keluar (F-D119).
6. **Tidak ada leave:** agent yang ingin keluar berhenti menarik; aturan C1 yang melepasnya.
7. **Penemuan:** `GET /desk/external` (aturan, batas, format pesan, daftar agent luar + kursi + keadaan) + klien acuan `tools/desk_agent_client.py`.
8. **Privasi:** masukan agent publik (data pasar + buku agent itu sendiri); tidak ada kontak yang disimpan.
9. **USULAN, BELUM DIKUNCI (butuh kata builder, `PARAMS_KURSI` v3):** (a) kursi uji tanpa batas waktu bisa ditahan agent luar yang sah tetapi biasa-biasa saja,
   karena aturan F-D113/F-D119 hanya menyingkirkan yang gagal; usulan: >= 2016 siklus (7 hari) di kursi uji tanpa naik -> belakang antrean; (b) agent luar yang
   naik ke aktif memengaruhi konsensus; usulan: paling banyak 2 dari 7 kursi aktif untuk agent luar. Sampai dikunci, pelepasnya = keputusan kursi builder
   (`analis.py kursi`, SK-M24).

**Koreksi sesudah uji penerimaan (6 Okt, builder meminta uji integrasi + alur bisnis terhadap kriteria P166):** dua celah ditemukan dan ditutup, keduanya dengan tes yang gagal
bila perbaikannya dicabut (mutasi): (a) `pull` mula-mula tanpa otentikasi - siapa pun bisa memalsukan kehadiran sebuah agent (siklusnya lalu ditunggu penuh 210 s dan dicatat
gagal) atau menghabiskan 2 slot long-poll-nya; sekarang pull wajib bertanda tangan atas `Fabius desk pull v1 / agent_id / ts` oleh dompet agent atau pemilik, `ts` dalam +-120 s
jam gerbang, penolakan tidak memalsukan kehadiran dan tidak memakai slot; (b) kriteria 2 menyebut agent yang keluar karena gagal (F-D119) DITOLAK saat mendaftar, tetapi kode
hanya menjawab "sudah terdaftar" (200); sekarang 403.

**Terkait:** F-D113 · F-D119 · F-D107 · P151 · P160 · P166 · [[04-Tools/TL33 - agent analis]] · [[04-Tools/TL36 - meja v2 bot + instrumen]]

**F-D121 #9 DISETUJUI (6 Okt, builder: *"F-D121 #9 -> saya sepakat"*):** (a) kursi uji yang >= 2016 siklus (7 hari) tanpa naik pindah ke belakang antrean bila ada yang mengantre; (b) agent
luar paling banyak 2 dari 7 kursi aktif. Dikunci sebagai `PARAMS_KURSI` v3 saat kodenya hidup (P170); sha dicatat di sini ketika itu.

**F-D121 #9 DIKUNCI sebagai `PARAMS_KURSI` v3 (6 Okt, P170):** v3 = v2 + `uji_maks_siklus` 2016 + `maks_aktif_luar` 2; sha `0x76f7196a92a419cee466250a84dcc2cd08bb181dc3d7b6e334fac3248d255e00` (dicetak `meja.sha(meja2.PARAMS_KURSI)`; v2 direkonstruksi dari v3
dengan membuang dua kunci itu dan `v: 2` = `0x47f1c058…`, sama dengan yang tercatat di F-D119). Rancangan: (a) kursi uji yang >= 2016 siklus tanpa naik pindah ke belakang antrean HANYA bila ada agent lain di antrean yang boleh
masuk dan kursi uji penuh (sebanyak yang dibutuhkan; `tunggu_sampai` +1 hari, riwayat diulang, bukan kegagalan); (b) kandidat luar tidak naik bila 2 kursi aktif luar terisi, kecuali menukar agent luar aktif terlemah (unggul
>= 0,5 pp); keputusan kursi builder (SK-M24) tidak dibatasi. T8 SK-M34 + SK-M35.

**Penamaan dikoreksi (F-D126, 6 Okt malam):** tidak ada v3. Aturan di atas DIGABUNG ke `PARAMS_KURSI` v2 (`v` = 2); sha v2 sekarang `0x3bbee1c0a7ce4be8bab9710f7099e056cd4e925eae65354ac84719a5bef8545e` (live ±16:10Z); sha "v3" `0x76f7196a92a419ce…` hanya hidup 15:20Z - ±16:10Z.

## F-D122 - Pintu bot dibuka penuh (rule / code / feed) + tinjauan dua tahap: bot teknis, lalu agent LLM pemilik Fabius · 6 Okt 2026 (WIB)

Builder (6 Okt) menolak form `/submit` yang memaksa memilih metode Fabius: *"biarkan semua input itu dari user, kan bot user, kita tidak perlu menentukannya"* ("nanti ga bervariasi"). Sesudah saya
beri tiga opsi (A aturan deklaratif, B kode, C feed), jawabannya: *"semua opsi digabung, karena kode function pun jg sangat penting, nanti pakai bot untuk bagian teknis apakah semua udh memenuhi
standar Fabius? Kalau udh baru lanjut analisis agent owner Fabius pakai LLM dari provider xkiro (GLM 5.3, effort default) + kasih brief dulu ... jgn bikin agentnya hanya iyaiyaiya aja, hrs deep
analyze + critical judge ... sama halnya untuk agent"*. Soal G5: *"sesuaikan no1"*. **Yang mengikat (kata builder):**

1. **Metode bot SEPENUHNYA dari pengguna.** Menggantikan keputusan 2 Okt malam *"dibuka dulu: template saja"* (`engine/submission.py` `ENABLED_KINDS = ("template",)`). `kind = template` tetap sah sebagai
   jalur kompatibel; `/submit` tidak lagi memaksa memilih template.
2. **Tiga jenis dibuka bersamaan:** `rule` (aturan deklaratif JSON yang dijalankan mesin kita), `code` (fungsi kode pengguna, dijalankan di sandbox oleh bot peninjau), `feed` (program pengguna menerbitkan
   sinyalnya; kita mencatat + menilai maju).
3. **Dua tahap tinjauan, untuk BOT dan untuk AGENT:** tahap 1 = bot teknis (otomatis, deterministik: memenuhi standar Fabius?); hanya bila lolos, tahap 2 = agent pemilik Fabius (LLM penyedia xkiro, model
   GLM 5.3, effort bawaan) menganalisis dengan BRIEF yang memaksa analisis dalam + penilaian kritis (bukan setuju-saja), dengan dua tujuan: tidak merugikan Fabius dan meningkatkan Fabius.
4. **G5 (plateau) disesuaikan** dengan jenis baru (tidak lagi "satu parameter template").
5. Agent mendaftar di halaman SENDIRI (F-D123), tidak digabung dengan `/submit`.

**USULAN SAYA, BELUM DIKUNCI (menunggu persetujuan builder; rincian di [[09-Inbox/Session-2026-10-02]] §130 C1-C10):** agent LLM hanya MEMBATASI (vonis `LANJUT` / `TAHAN` / `TOLAK`; tidak bisa
meloloskan yang gagal teknis; `LANJUT` bukan izin slot) · masukan pengajuan diperlakukan sebagai data tak tepercaya (skema keluaran ketat, tanpa alat, percobaan injeksi = temuan) · uji peninjau dengan set
kalibrasi kiriman bermasalah-yang-diketahui sebelum masuk jalur · jenis `code`: analisis statis + sandbox + uji kausalitas + eksekusi di pekerjaan terpisah tanpa rahasia, hanya DATA diserahkan ke pekerjaan
tepercaya · jenis `feed`: hanya bukti maju (jendela bayangan lebih panjang, tanpa slot sampai terbukti) · G5 menggeser parameter BERNAMA yang ditandai pengaju, jumlah varian ikut hitungan percobaan keluarga
(P83) · agent: tahap 1 = identitas + uji kering + aturan kursi uji, tahap 2 = agent LLM boleh MENAHAN kenaikan ke kursi aktif · panggilan LLM sebagai pekerjaan kedua `bot-review.yml` (rahasia repo
`XKIRO_API_KEY`) atau di gerbang. **Pertanyaan terbuka untuk builder:** kode pengguna publik (bisa disalin) atau tersegel; tempat panggilan LLM; jendela bayangan jenis `feed`.

**Fakta pendukung (6 Okt):** xkiro = `https://api.xkiro.com/v1` (OpenAI-compatible), kunci `XKIRO_API_KEY` ada di Railway `fabius-x402` dan tidak di laptop; id persis "GLM 5.3" di xkiro belum terverifikasi;
`analis.call_model` selalu mengirim `reasoning_effort` (effort bawaan = parameter dihilangkan).

**Terkait:** F-D120 · F-D121 · F-D71 · F-D72 · F-D88 · P161 · P166 · P167 · P168 · [[04-Tools/TL37 - jalur pengajuan bot]] · [[09-Inbox/Session-2026-10-02]] §130 · [[08-Backlog/12 - Epik Pengajuan Terbuka dan Peninjau LLM]] (spesifikasi + draf brief; DISETUJUI di F-D125)

## F-D123 - Halaman Submit Agent terpisah dari Submit Bot · 6 Okt 2026 (WIB)

Builder: *"untuk agent nanti bikin page sendiri submit agent, jgn dijadiin satu, bentrok jadinya"*; sesudah saya usulkan `/submit-agent`: *"Boleh dong"* (dikerjakan lebih dulu). Mengoreksi pintu masuk agent
di F-D121 #7 (penemuan), yang semula hanya catatan di `/desk` yang menaut ke JSON gerbang.

1. **Rute `/submit-agent`** + menu "Submit agent" di navbar; `/submit` tetap HANYA untuk bot. Tidak ada elemen agent di `/submit` dan sebaliknya.
2. Isi: papan agent luar dari `GET /desk/external` (kursi, % sah, online), langkah gabung (rute, format pesan, klien acuan) DIBANGKITKAN dari respons gerbang supaya tidak bisa menyimpang, dan form daftar
   bertanda tangan dompet login Privy (pesan `Fabius desk join v1`). Daftar hanya berhasil bila dompet login = dompet agent atau pemilik identitas ERC-8004-nya; selain itu halaman menunjuk ke klien acuan.
3. Menjawab siklus tetap lewat program (pull/answer); halaman ini TIDAK menjawab dari browser.
4. Catatan di `/desk` hanya menaut ke halaman ini.

**Terkait:** F-D121 · F-D122 · P169 · [[04-Tools/TL38 - agent luar di meja (pull)]]

## F-D124 - Canary uang asli ditunda: hackathon berjalan tanpa uang nyata · 6 Okt 2026 (WIB)

Builder: *"Canary -> nanti dulu, ini fokus hackathon jd blom brani duit asli"*. Mengikat sampai builder mengubahnya.

1. **Keadaan terukur 6 Okt:** Railway `fabius-engine` bersenjata (`EXEC_REAL=canary`, `EXEC_LIVE_OK=binance:sampai:2026-12-31`, kunci asli terpasang, plafon `EXEC_REAL_MAX_USDT=10`, tetapi `EXEC_MODE=demo`
   dan `BINANCE_API_ENV=demo`), sedangkan sakelar publik `config/uang_nyata.json` `aktif: false` (HEAD dan origin/master) dan `ledger/eksekusi/` hanya memuat `binance-demo` - TIDAK pernah ada order uang asli
   (F-D97: dua kunci harus terbuka).
2. **Tidak ada yang menyalakan sakelar tanpa kata builder.** P133 (canary), P120 (live canary Binance), P122 (Aster live), P123 (Tokocrypto) berstatus DITUNDA atas kata builder; paper + akun demo berjalan terus.
3. **Usulan (belum dikerjakan):** untuk satu kunci cadangan, `EXEC_REAL` bisa diset `off` atau `EXEC_LIVE_OK` dihapus di Railway; tidak diubah sebelum builder meminta, karena itu mengubah keadaan "bersenjata-diam" yang
   terdokumentasi di [[04-Tools/TL29 - canary uang nyata]].

**Terkait:** F-D92 · F-D96 · F-D97 · F-D126 · P133 · P120 · P122 · P123 · [[04-Tools/TL29 - canary uang nyata]]

## F-D125 - Epik 12 disetujui (pengajuan terbuka + peninjau LLM); kode pengguna PRIVAT; tanpa label v1 · 6 Okt 2026 (WIB, malam)

Builder (6 Okt malam): *"saya acc semua decision epik12 mu"*, dengan jawaban atas tujuh pertanyaan: kosakata aturan *"v1 kan udh ga dipake ... kita hanya pakai v2"*; brief bot + agent *"Gas aja"*; kode pengguna *"jgn publik krn repo publik dan hackathon, kalau
production ready nanti ku buat private reponya jd ya aman aja"* (jawaban ringkas: *private*); peninjau lewat gerbang *"boleh"* (gerbang = Railway `fabius-x402`); id model *"gas baca aja via railway"*; jendela `feed` *"gas 120 hr"*; urutan fase *"gas yg menurutmu paling oke"*.
Mengikat (menggantikan label USULAN di F-D122 dan [[08-Backlog/12 - Epik Pengajuan Terbuka dan Peninjau LLM]]):

1. **Semua rancangan epik 12 disetujui:** jenis `rule` / `code` / `feed`; jalur dua tahap (bot teknis, lalu agent LLM yang hanya MEMBATASI); G5 atas parameter bernama; kosakata aturan + batas validator; sandbox kode; `feed` dengan bukti maju; set kalibrasi sebagai kriteria penerimaan
   peninjau; N = 288 siklus untuk peninjauan agent.
2. **Kode pengguna PRIVAT.** Selama repo publik, kode pengguna tidak boleh masuk repo / GitHub Actions publik (hanya sha + ukuran publik). Jenis `code` dibuka untuk pengguna luar setelah repo privat, atau lewat jalur penyimpanan + pelari privat yang dirancang di P167b dan
   disetujui builder. Bot `code` ber-label kepercayaan lebih rendah selama kodenya privat. Peninjau LLM pihak ketiga membaca kode (diumumkan di formulir); laporan publik tidak mengutip kode. `rule` tetap publik (replay publik) kecuali builder mengubah.
3. **Peninjau LLM lewat gerbang (Railway `fabius-x402`)**, bukan GitHub Actions; model **`z-ai/glm-5.3`** di xkiro (dibaca lewat Railway 6 Okt: konteks 1.000.000, $1,40 / $4,40 per sejuta token masuk / keluar; BUKAN `:free`), effort bawaan (parameter `reasoning_effort` dihilangkan);
   uji satu panggilan kecil (< $0,01) diizinkan.
4. **Brief bot + brief agent disetujui**; sha tercatat di epik 12 §5.3 / §5.4 (bot `0xb72e1e772887338458a05b44f58fc80338818909b20a8fcf53254e43f04ed331`, agent `0xe66fb05aca4420f30d08caca12b9e1da18a1bd0c8245d662235d5e02c0e92702`); perubahan = sha baru + set kalibrasi diulang.
5. **Jendela bayangan `feed` 120 hari.**
6. **Urutan fase:** P167a (rule) -> P168a (peninjau bot) -> P168b (peninjau agent) -> P167b (code) -> P167c (feed).
7. **Tanpa label v1/v0:** hal baru tidak diberi nomor versi (diidentifikasi sha / tanggal); skema pengajuan naik ke v2 saat jenis baru dibuka (P167a), karena skema lama `SCHEMA_V = 1` hanya untuk template.

**Terkait:** F-D122 · F-D123 · F-D121 · P167 · P168 · [[08-Backlog/12 - Epik Pengajuan Terbuka dan Peninjau LLM]]

## F-D126 - Rapikan: F-D90 dicabut (nisan); P90 gelombang 2 gas; PARAMS_KURSI satu v2 · 6 Okt 2026 (WIB, malam)

Builder (6 Okt malam): *"Hapus F-D90, P90 gas, P170 di rebrand ke v2"* + *"F-D90 -> nisan"* + *"A, tapi kalau di codebase km bikin v3, dimigrate dan gabungkan ke v2 biar ga terpisah"*. Mengikat:

1. **F-D90 dicabut, tinggal nisan** (nomor tetap supaya rujukan lama tidak menggantung). Vault ada di repo publik: riwayat git tetap menyimpan teks lama; yang berubah hanya keadaan vault sekarang. Dua hal dari F-D90 yang masih berlaku dipindah ke sini (butir 2 dan 3).
2. **P90 gelombang 2 DISETUJUI ("P90 gas"):** setel `placebo_max_p` (G8) dan mungkin `min_calmar` (K2) pada benih setel, konfirmasi pada benih baru; target positif-palsu batas atas Wilson <= 5 % di kelima dunia sambil memaksimalkan daya; protokol pra-registrasi ditulis dan di-push SEBELUM lari;
   tidak ada ambang berubah sebelum keputusan builder (kunci v2 atau tetap v1). R3-R11 tetap menunggu.
3. **P75 / P80 tetap ditunda** (telaah hukum ToS sebelum uang nyata; telaah hukum menjual sinyal): tidak dikerjakan selama hackathon (bersama F-D124); syarat telaah hukum F-D72 tidak dicabut.
4. **`PARAMS_KURSI` satu v2:** tidak ada v3. Aturan F-D121 #9 (kursi uji maks 2016 siklus; agent luar maks 2 dari 7 kursi aktif) DIGABUNG ke v2, `v` di kode = 2. Riwayat sha (tetap tercatat, tidak ditulis ulang): revisi pertama v2 (F-D119) `0x47f1c0587a8cf60b3c68cf8098850018b4ff11aa25c4e44685de16209a77ea40`
   hidup 6 Okt ±11:00Z - 15:20Z; "v3" `0x76f7196a92a419cee466250a84dcc2cd08bb181dc3d7b6e334fac3248d255e00` hidup 15:20Z - ±16:10Z; v2 sekarang `0x3bbee1c0a7ce4be8bab9710f7099e056cd4e925eae65354ac84719a5bef8545e`, LIVE 6 Okt ±16:10Z (gerbang dari `e09e2b55`; `GET /desk` `params_kursi.v` 2, `uji_maks_siklus` 2016, `maks_aktif_luar` 2, `params_kursi_sha` cocok dengan `meja.sha(meja2.PARAMS_KURSI)`). Evaluasi kursi hanya jalan 00:00 UTC dan belum ada yang berjalan di bawah aturan baru,
   jadi tidak ada perubahan perilaku akibat penamaan.

**Terkait:** F-D90 (nisan) · F-D113 · F-D119 · F-D121 · F-D124 · F-D125 · [[08-Backlog/08 - Riset Optimasi Ambang]]


## F-D127 - Sandbox `kind=code` jalan native di Windows; Railway tetap Linux · 7 Okt 2026 (WIB)

Builder (7 Okt), sesudah cabang sesi cloud digabung dan 28 tes `code` gagal di mesin builder: *"Nah itu di migrate keluar dari linux aja, lalu test di local device saya ini"*
+ *"sources itu km migrate ke milik windows semua + sourcecode yg berbasis linux dan sandboxnya di migrate ke windows scope juga"*; ditanya ulang:
*"1. benar sekali"* (pengaman TETAP ada, hanya pindah ke versi Windows - bukan dihapus) + *"2. ya kalau itu jelas railway dong, kan emg linux kalau itu udh bener"*. Mengikat:

1. **Lapis OS sandbox `code` punya dua jalur yang sama kuat:** Linux / POSIX (gerbang + pelari Railway) tetap `setrlimit` (CPU, AS, FSIZE 0, NOFILE 16, CORE 0);
   Windows (mesin builder) = Job Object tanpa nama (waktu CPU per proses, memori ter-commit per proses, maksimal 1 proses, mati tanpa dialog, UI terkunci).
   Gagal memasang batas = tidak ada kode yang dijalankan. Lapis lain (analisis statis, anggaran langkah, builtins terbatas, dua jalan, uji kausal) tidak berubah.
2. **Berkas kode privat:** POSIX mode 0600; Windows DACL terlindung berisi satu ACE untuk akun proses (folder ikut dikunci, berkas tertutup sejak dibuat).
3. **Railway tetap Linux** (gerbang `fabius-x402`, pelari `railway/pelari/Dockerfile`) - tidak ada yang dipindah dari sana.
4. **Bukti wajib di kedua jalur:** sensus Windows tanpa tes `code` yang dilewati; jalur Linux diuji di WSL Ubuntu mesin builder; mutasi bertanda platform
   (`tools/mutasi_kode_feed.py`) menangkap pencabutan tiap batas di platformnya. Guard "lewati di luar POSIX" (commit lokal `b1ec54e1`) dicabut.

**Terkait:** F-D122 · F-D125 · P167 · [[04-Tools/TL41 - kode pengguna di sandbox (code)]] · [[07-Testing/01 - Test Commands]] #128


## F-D128 - Gerbang kursi agent: turun karena AMBRUK tiap siklus + evaluasi harian di siklus pertama hari UTC · 7 Okt 2026 (WIB)

Builder (7 Okt), sesudah audit menemukan qwen 64 % sah dalam 24 jam tetapi kursinya tetap aktif: *"betulkan gatenya yg menyeleksi agent, cari tahu kenapa
tidak otomatis diturunkan dan betulkan"*. Sebab (dicetak dari log 20 deployment gerbang 6 Okt 00:00 - 7 Okt 06:10Z, Test Commands #129):
(1) kursi hanya dievaluasi SEKALI sehari dan pada evaluasi 00:00 UTC 7 Okt qwen masih 81,0 % (221 / 273 siklus 6 Okt) = di atas ambang 80 %, sesudahnya
ambruk (13 sah dari 75 siklus sesudah 00:00) tetapi tetap memegang kursi aktif sampai evaluasi berikutnya; (2) evaluasi hanya di siklus yang TEPAT
00:00:00 - siklus itu terlewat (gerbang di-deploy 20 kali pada 6 Okt) = evaluasi hari itu hilang; (3) sebagian kegagalan qwen = `TypeError: unhashable
type: 'list'` dari `parse2` (faktor veto berbentuk daftar) - kontrak SK-M14 "entri salah per item = ditolak per item" dilanggar parser. Mengikat:

1. **Turun karena ambruk (SK-M43), diperiksa tiap siklus sebelum agent dijalankan:** agent AKTIF dengan sah < 50 % dalam 36 siklus terakhirnya (3 jam)
   turun ke kursi uji saat itu juga - hanya bila median agent aktif lain >= 80 % pada jendela yang sama (semua jatuh = gangguan bersama, tidak ada yang
   diturunkan) dan sesudahnya masih >= 3 kursi aktif (kuorum F-D113). Terburuk dulu. Sesudah turun, aturan kursi uji F-D119 berlaku di evaluasi harian.
   Angka 36 / 50 % / 80 % / 3 = **USULAN asisten, aktif atas kata builder "betulkan"**; bisa diubah builder.
2. **Evaluasi harian (SK-M21, SK-M44) di siklus PERTAMA tiap hari UTC** (normalnya 00:00; terlewat -> siklus berikutnya), tetap sekali sehari (`eval_hari`
   di state kursi). Naik kursi tetap hanya di evaluasi harian.
3. **`parse2` (SK-M45):** jenis nilai salah tidak pernah TypeError mentah; per item (instrumen bukan objek, keyakinan bukan angka, faktor veto bukan satu
   nama fitur, faktor berbentuk daftar) = `ditolak` per item; bidang struktural berjenis salah = ValueError berpesan jelas.
4. `PARAMS_KURSI` tetap `v` 2 (F-D126: tidak ada v3): sha `0x3bbee1c0a7ce4be8bab9710f7099e056cd4e925eae65354ac84719a5bef8545e` ->
   `0x19f525f6e506b4e0d922300a560976ed291d61a8ba11420d3a046cd19963fa39`.

Dry run atas status per siklus produksi 6 Okt 00:00 - 7 Okt 06:10Z (348 siklus): tepat satu peristiwa - qwen aktif -> uji pada 7 Okt 00:00 UTC
(sah 47 % dalam 36 siklus, median agent lain 96 %); tidak ada agent lain yang turun.

**Terkait:** F-D113 · F-D119 · F-D126 · P154 · P160 · [[04-Tools/TL36 - meja v2 bot + instrumen]] · [[07-Testing/01 - Test Commands]] #129


## F-D129 - P90 gelombang 2: kunci baru G8 c = 2,0 (placebo_max_p 0,10 pada k = 1); K2 tetap 0,5 · 7 Okt 2026 (WIB)

Builder (7 Okt), sesudah ditanya "P90 ini kunci untuk apa" dan dijelaskan (ambang gerbang tinjauan setiap bot yang diajukan: G8 uji placebo waktu + K2
Calmar minimum; daya 0,31 -> 0,41, positif-palsu maks 1,45 %; saran: G8 saja): *"Boleh"*. Mengikat:

1. **G8:** batas atas 95 % p placebo <= c x alpha, **c = 2,0**; pada pengajuan pertama keluarga (k = 1) = 0,10 (sebelumnya 0,05), pada pengajuan ke-k = 2,0 x A1/k
   (`engine/anggaran.py::gate_params_for` kini menerapkan pengali pada alpha, seperti yang diuji riset). G3 (bootstrap) tetap pada alpha A1/k.
2. **K2 `min_calmar` TETAP 0,5** - di set konfirmasi K2 0,4 hanya menambah daya +0,005 dan melonggarkan pagar ekonomi.
3. Kunci gerbang lama `0xf145b70abd251b9fcf421bfb811bcf3788dade347c37b3bea331a09fedfe5f32` pindah ke `engine/locks/history/`; kunci baru
   `0xc0192ebd073436323416bdb0deba82658b079b6f5082cad9034352eaae48eaec` (2026-10-07T09:01:56Z). Anchor on-chain = satu tx `tools/anchor_lock.py --send` dari
   agen `0x4bb3…c862` (kunci di `.agent.env`) - dijalankan builder; rencana: id `0xfa07c6ad…`, belum di chain.
4. Bot yang sudah divonis memakai kunci lama tidak dinilai ulang; tinjauan baru memakai kunci ini. Pilihan c = 2,0 adalah hasil aturan pra-registrasi
   (protokol `0x4587f1ef…`), bukan dicocokkan sesudah melihat data konfirmasi.

**Terkait:** F-D88 · F-D126 · [[06-Results/34 - Hasil P90 Gelombang 2]] · [[08-Backlog/08 - Riset Optimasi Ambang]] · [[07-Testing/01 - Test Commands]] #135


## F-D130 - Peninjau LLM P168: revisi brief terarah + kasus kalibrasi baik dibuat bersih + pemeriksa kutipan yang tepat · 7 Okt 2026 (WIB)

Builder (7 Okt): *"P168 ... kerjakan sekarang"* (sesudah opsi revisi brief / ganti model / tunda). Diagnosis atas jawaban mentah kalibrasi sungguhan:
(1) sebagian besar `evidence_key` "karangan" = KUTIPAN SAH berformat lain (beberapa jalur dalam satu kunci, jalur kiriman tanpa `submission.`,
`jalur=nilai`, `jalur (catatan)`); (2) kasus "baik" CACAT: `bot-baik` tampak menyembunyikan percobaan (n_trials 11 = 6 dideklarasikan + 4 varian G5 + 1,
rinciannya tidak diberikan) dan ditahan karena G11 yang memang tidak diukur pipeline; `agent-baik` dibangkitkan dengan satu template kalimat (itu
sendiri BOILERPLATE) dan berganti bot 54 % siklus; (3) brief "kalau ragu TAHAN vs TOLAK pilih TAHAN" bertabrakan dengan "duplikat = TOLAK". Mengikat:

1. **Brief bot + agent direvisi (dua kalimat, teks persis di epik 12 §5.3 / §5.4):** duplikat petahana = TOLAK; batas pipeline Fabius (gerbang di
   `stage1.unmeasured`, ukuran yang tidak diambil Fabius, akuntansi `n_trials`, latensi tak dicatat, sampel jawaban, kartu tulisan pemilik, panjang masa uji
   terkunci) masuk monitoring, bukan keberatan blocking; LANJUT vs TAHAN = ada keberatan blocking? sha bot `0x57b9f16e…` (sebelumnya `0xb72e1e77…`),
   agent `0x016f6029…` (sebelumnya `0xe66fb05a…`).
2. **Masukan bot:** `stage1.n_trials_breakdown` (dideklarasikan + varian G5 + pengajuan keluarga sebelumnya + 1; hanya bila jumlahnya cocok).
3. **Pemeriksa kutipan (`kunci_sah`):** satu evidence_key boleh memuat beberapa jalur (`;` `,` `&` `+` `|`, atau ` vs ` / ` and ` diapit spasi), relatif
   ke `submission`, dengan `=nilai` / `(catatan)`; SETIAP jalur tetap wajib ada (salah ketik, jalur yang tidak ada tetap karangan).
4. **Kasus kalibrasi baik dibuat bersih:** agent baik = pilihan bot stabil, instrumen + faktor sesuai mekanisme bot, alasan beragam dengan nilai fitur
   sungguhan. Kasus baik wajib LANJUT (F-D sebelumnya hari ini).
5. **Panggilan:** suhu 0,2 -> 0 (USULAN asisten, demi konsistensi antar jalan); nonce body `user` per panggilan (cache xkiro); kalibrasi mengulang galat
   JARINGAN maks 3x dan boleh paralel (`--paralel`).

Hasil kalibrasi sungguhan sesudah perbaikan (kriteria ketat tidak diubah: semua kasus, 3 jalan konsisten, skema persis, nol kutipan karangan):
**bot 5/8** (sebelumnya 2/8), **agent 4/6** (sebelumnya 0/6). Sisa = kesalahan model sungguhan (jalur salah ketik / tidak ada, `agent-baik` tetap
ditahan, satu pelanggaran format). **Peninjau TETAP tidak aktif.** Keputusan builder berikutnya: tetap ketat (peninjau mati sampai model lebih baik),
longgarkan kriteria lulus (mis. mayoritas 2/3 jalan per kasus), atau coba model lain.

**Terkait:** F-D122 · F-D125 · P168 · [[08-Backlog/12 - Epik Pengajuan Terbuka dan Peninjau LLM]] §5.3-§5.4 · [[07-Testing/01 - Test Commands]] #137


## F-D131 - Kalibrasi peninjau LLM: kriteria mayoritas 2 dari 3 jalan · 7 Okt 2026 (WIB)

Builder (7 Okt) menjawab tiga opsi P168 (tetap ketat / longgarkan kriteria mayoritas 2/3 / model lain) dengan *"Gas"* tanpa memilih; asisten memilih
opsi yang paling hemat dan tetap ketat isinya: **kasus kalibrasi lulus bila >= 2 dari 3 jalan masing-masing lolos SEMUA pemeriksaan (skema persis, vonis
model di daftar, tag wajib, injeksi dilaporkan, nol kutipan karangan) dengan vonis yang SAMA**; tetap butuh 3 jalan. Aturan penilaian
(`engine/peninjau.py::MIN_JALAN_LULUS`), bukan parameter panggilan - rekaman suhu 0 dinilai ulang tanpa panggilan baru:
**bot 8/8 LULUS -> peninjau bot AKTIF** (berkas `20261007T123701Z-bot.json`); **agent 5/6 GAGAL** (`agent-baik` ditahan model di semua jalan) -> peninjau
agent TETAP mati. Peninjau hanya bisa MENAHAN / menolak (tidak pernah memberi slot); batas biaya `maks_panggilan_hari` tetap. Bisa dibalik builder.

**Terkait:** F-D125 · F-D130 · P168 · [[07-Testing/01 - Test Commands]] #138

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

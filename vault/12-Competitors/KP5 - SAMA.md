---
tags: [kompetitor, "KP5"]
---

# KP5 - SAMA

**Bagian dari:** [[12-Competitors/00 - Hub Kompetitor]] · baseline: [[12-Competitors/KP0 - Baseline Fabius dan Konteks Penjurian]]
**Sumber:** *(workspace)* `../Competitors/05-SAMA/` — `page/page.txt` (`proj_09fc9238c3456d9aba`), `deck/deck.txt` (Canva 13 slide, ditranskripsi dari browser), `video/transcript.txt` (Whisper lokal) + `video/analysis.md` (`sama-demo.mp4` di Google Drive, 1:48), `github/sama-frontend.README.md`, `github/sama-frontend.commits.tsv` (51 commit, 3–17 Okt); cek hidup 26 Okt: `app.samafi.xyz/proof` 200, `eth_getCode` `0x7811…2AC8` di BSC **mainnet** → bytecode ada.

**Ringkas:** SAMA mencocokkan rebalancing saham AS ter-tokenisasi (bStocks) antar dompet di BNB Chain: anggota "Circle" menetapkan target, SAMA mengambil snapshot harga yang disematkan ke blok, matcher *min-cost circulation* menemukan bagian rebalance yang saling meniadakan (termasuk cincin 3+ dompet), lalu `SamaSettlement` memindahkan semua leg dompet-ke-dompet dalam satu transaksi atomik tanpa memegang dana; verifier independen membaca ulang dari RPC lain. SAMA adalah **satu-satunya kompetitor yang memindahkan aset bernilai di mainnet** dan punya halaman bukti publik dengan ronde nyata. Ia bertabrakan dengan Fabius di **ketiga track**, dan secara tema paling dekat dengan Fabius di sisi pasar (trading, harga, biaya eksekusi).

**Poin kunci:**
- Track: AI Agents + Consumer Apps + Finance & Commerce. Tim 2 (NGDKLabs: Al Fikri Kholil Misbah, Bayu Mukti Wibowo). Network di form: **BNB Smart Chain (Mainnet)**.
- Halaman `/proof` (26 Okt): ronde berlabel **TEST** di mainnet (contoh Round 8–18, 9 Okt), crossed $1–$7, 2 peserta, verifier 17–18/18 cek, kontrak tidak memegang token sesudah tiap settlement. Semua ronde terlihat sesudah deadline 7 Okt.
- Uji: 33 unit test kontrak dengan fuzz, 22 test fork mainnet pada bStocks nyata, matcher referensi independen memeriksa solver produksi (klaim README). Plan dibatasi $500 selama belum diaudit.
- Data problem kuat: 18/88 bStocks punya pool USDT > $100K, median biaya swap $10K di pool < $100K = **4,4 %**, MUB 75 %; NVDAB 16.004 beli / 15.251 jual dalam 24 jam.
- AI: asisten membaca data pengguna lewat tool server dan mengusulkan target; tidak bisa memindahkan dana atau menyimpan apa pun sendiri.
- Penilaian (pendapat): SAMA **unggul** di eksekusi (mainnet, aset nyata), UX konsumen, presentasi, dan kejelasan nilai uang; Fabius **unggul** di kedalaman AI/agen (desk multi-agen ERC-8004, MCP, x402) dan bukti urutan; inovasi kira-kira setara.

**Detail:**

## 1. Profil SAMA

| Aspek | SAMA |
|---|---|
| Problem | Likuiditas bStocks tipis dan tidak merata; rebalancing kecil membayar fee pool, spread, dan price impact di tiap leg, padahal arus beli/jual dua sisi bisa saling meniadakan. Cincin kebutuhan (A↔B↔C) tak terlihat oleh venue berpasangan. |
| Solution | Circle → target (preset / persen / kalimat / usulan AI) → snapshot harga per blok (Binance Web3 RWA API + cross-check TWAP PancakeSwap V3 30 m) → intent EIP-712 gratis → matcher min-cost circulation → semua anggota menyetujui rencana persis → `SamaSettlement` atomik, non-custodial → verifier RPC terpisah → sisa: ronde berikut / batal / swap PancakeSwap hanya jika di bawah cost cap dan NYSE buka. |
| Bukti | Kontrak terverifikasi BscScan + Sourcify di mainnet; ronde TEST nyata di `/proof`; cincin 3 dompet NVDAB → SPYB → AAPLB dijalankan di fork mainnet; demo bawaan tanpa wallet < 2 menit. |
| Konsumen | Mobile-first, bilingual EN/ID, Privy (email/wallet), halaman pasar untuk 90 aset, kalender return bulanan, konversi BNB→WBNB satu tap. |
| Batas yang diakui | belum diaudit (cap $500); ronde mainnet pertama "sedang dijalankan" (README); backend + kontrak tidak ada di org GitHub publik (`github.com/sama-fi` hanya `sama-frontend` + `.github`). |
| Presentasi | Video 1:48 sinematik, narasi tenang, angka besar 4,4 %, UI animasi; deck Canva 13 slide dengan grafik biaya per token dan tim. |

## 2. Head-to-head per kriteria juri (penilaian, tanpa bobot)

| Kriteria | Fabius | SAMA | Siapa unggul & kenapa |
|---|---|---|---|
| Inovasi & orisinalitas | Bukti urutan + pra-registrasi + desk multi-agen + gerbang publik | Coincidence-of-wants untuk RWA tokenized dengan cincin multi-dompet + settlement atomik non-custodial | **Setara.** CoW-matching sudah ada di DeFi (CoW Protocol), tapi menerapkannya pada bStocks dengan Circle sosial dan cincin 3+ adalah sudut baru di BNB. Fabius orisinal di primitif bukti. |
| Eksekusi teknis | 5 kontrak testnet, 117 forge + 743 Python; per 26 Okt alarm + gate 500 | Kontrak mainnet terverifikasi, ronde nyata dengan verifier 18/18, 33 + 22 test, matcher referensi | **SAMA unggul.** Mainnet + aset bernilai + bukti per ronde + verifier dengan RPC terpisah. Kekurangannya: backend tidak publik — juri yang ketat bisa menurunkan nilai keterbukaan. |
| Dampak & kelayakan bisnis | Pembeli sinyal & pembuat bot; belum ada pengguna | Investor ritel self-custody bStocks; penghematan biaya terukur (4,4 % median vs $0 fee untuk bagian matched) | **SAMA unggul.** Nilai uangnya terlihat langsung di angka. Model pendapatan SAMA sendiri tidak ditemukan di halaman/deck — kelemahan kecil yang tidak cukup membalik penilaian. |
| UX | Banyak konsep; Privy + Telegram | Satu alur: target → join → match → approve → settle; asisten AI dengan kartu token; bilingual; demo tanpa wallet | **SAMA unggul.** |
| Presentasi & demo | Video 127 d terpoles, hook sejarah | Video 1:48 terpoles, hook angka 4,4 %, UI produk dalam motion | **Setara tinggi.** Keduanya yang paling "iklan" di antara sembilan proyek; SAMA sedikit lebih konkret karena angka uang. |

## 3. SWOT Fabius terhadap SAMA

**Strengths (Fabius vs SAMA)**
- **AI lebih substantif.** Di SAMA, AI hanya asisten yang mengusulkan target (bisa dihapus tanpa merusak produk). Di Fabius, agen analis ber-ERC-8004 adalah bagian inti desk, pick-nya di-anchor (`SelectionAnchor`), dan formula terkunci yang mengubah suara jadi posisi. Untuk track **AI Agents**, Fabius lebih "agen".
- **Rel ekonomi agen.** x402 + MCP memungkinkan agen lain membeli keluaran Fabius; SAMA tidak membuka apa pun untuk agen.
- **Keterbukaan kode.** Seluruh Fabius (kontrak, engine, tools, web) publik dan bisa diverifikasi ulang; SAMA hanya frontend yang publik, kontrak hanya lewat BscScan/Sourcify.
- **Bukti urutan dan pra-registrasi.** SAMA membuktikan settlement benar; Fabius membuktikan keputusan diambil sebelum hasil — relevan bila SAMA kelak menjual rekomendasi rebalancing AI.

**Weaknesses (Fabius vs SAMA)**
- **Mainnet vs testnet paper.** SAMA memindahkan saham ter-tokenisasi sungguhan di mainnet (meski nilai $1–$7); Fabius tidak memindahkan nilai apa pun. Panitia menulis misi "genuinely runs onchain" — SAMA paling dekat ke kalimat itu.
- **Angka biaya yang dirasakan.** SAMA: "$10K swap = 4,4 %, kami $0 untuk bagian matched". Fabius: tidak punya angka penghematan atau manfaat uang untuk pengguna.
- **Bukti per ronde yang mudah dibaca juri.** `/proof` SAMA menampilkan tiap ronde dengan tx, jumlah peserta, dan "18/18 checks". `/verify` Fabius ada, tapi per 26 Okt `/status` alarm dan tidak ada daftar "commit kemarin sukses" yang hijau.
- **Iterasi pasca-deadline.** SAMA masih mengirim commit sampai 17 Okt dan menjalankan ronde 9 Okt; Fabius berhenti 7 Okt dan rantainya putus 13 Okt.
- **Tim 2 orang dengan peran jelas** (kontrak+backend, kontrak+frontend) di deck; Fabius solo — bukan kelemahan teknis, tapi juri kadang menimbang kapasitas eksekusi lanjutan.

**Opportunities (karena SAMA ada)**
- **Pembeda "pasar vs bukti".** SAMA dan Fabius sama-sama di domain trading. Fabius bisa menyebut: SAMA mengurangi *biaya* trading, Fabius mengurangi *penipuan klaim* trading. Dua masalah berbeda di pasar yang sama — dan Fabius adalah satu-satunya yang menyerang sisi kejujuran sinyal.
- **Pinjam format halaman bukti per ronde.** Halaman `/verify` atau `/status` Fabius bisa menampilkan daftar "bar terakhir: commit tx, reveal tx, n sinyal, SAH" dengan gaya ringkas `/proof` SAMA.
- **Pakai data pasar BNB yang sama.** Fabius juga punya perekam data dan pengukuran venue (E20: hanya 5 dari 41 simbol perp hidup per menit). Satu angka pasar yang tajam di pembuka pitch (gaya 4,4 % SAMA) bisa diambil dari hasil riset Fabius sendiri, asalkan perintah pencetaknya disebut.
- **Integrasi kelak:** sinyal Fabius sebagai input target Circle SAMA — contoh nyata bagaimana Fabius menjadi infrastruktur untuk produk lain (tanpa mengklaim integrasi yang tidak ada).

**Threats (dari SAMA)**
- **Kandidat kuat di Finance & Commerce dan Grand Prize.** RWA + mainnet + UX + angka biaya adalah kombinasi yang kuat untuk track "DeFi, payments and RWA for Indonesia" (bilingual ID).
- **Di AI Agents, SAMA bisa menang lewat kesan "produk jadi"** walau AI-nya tipis. Juri yang memberi bobot tinggi pada eksekusi dan UX bisa menempatkan SAMA di atas Fabius bahkan di track agen.
- **Standar presentasi tinggi.** Video 1:48 SAMA setara iklan produk; Fabius v1 jargon-heavy dan v2 belum disetujui. Di Demo Day, juri akan membandingkan keduanya langsung.

## 4. Pertanyaan juri yang kemungkinan muncul
- "Kenapa Fabius tidak di mainnet?" → jawaban dari kebijakan sendiri: tidak ada edge (0/6 lulus F-D16) dan review hukum belum ada (P75/P80); menjual sinyal tanpa edge di mainnet justru bertentangan dengan tesis Fabius. Jawaban ini kuat bila diucapkan sebagai prinsip, bukan alasan.
- "Apa pengguna dapatkan dalam uang?" → jujur: belum ada nilai uang; yang didapat adalah kemampuan memeriksa klaim. Siapkan kalimat yang tidak melanggar claims cheat sheet.

## 5. Langkah konkret sebelum Demo Day 31 Okt (pelajaran dari SAMA)
1. Pulihkan rantai dan siapkan tampilan "bar terakhir" hijau ala `/proof` SAMA.
2. Satu angka pasar tajam dari riset Fabius sendiri (dengan perintah pencetaknya) di pembuka.
3. Posisi eksplisit "kejujuran sinyal" vs "biaya eksekusi" untuk menghindari dibandingkan langsung di dimensi tempat SAMA lebih kuat.

## 6. Batas analisis ini
- Test count SAMA dari README; kode kontrak/backend tidak publik, jadi tidak bisa diperiksa.
- Ronde di `/proof` berlabel TEST dan terjadi sesudah deadline; bagaimana juri memperlakukan aktivitas pasca-deadline tidak dipublikasikan.
- Kehadiran bytecode di mainnet dicek lewat `eth_getCode`; isi ronde (tx) tidak diperiksa satu per satu.

**Terkait:** [[12-Competitors/KP4 - BagiPanen]] · [[12-Competitors/KP6 - Tagei]] · [[06-Results/28 - Venue Kami Bukan Pasar]]

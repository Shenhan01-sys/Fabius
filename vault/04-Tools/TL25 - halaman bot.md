---
tags: [perkakas, "TL25", fe]
---

# TL25 - halaman /bot/[id] (satu bot = satu mesin terkunci)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** brief `docs/design/bot.md` · halaman server `web/src/app/bot/[id]/page.tsx` · komponen `web/src/components/bot/BotView.tsx` · teks
`web/src/lib/copy.ts` (`bot` EN/ID + `GLOSS` EN) · data `web/public/data/snapshot.json` (`bots[].universe`, `bots[].kill_rules` ditambah 4 Okt di
`tools/web_snapshot.py`) + ledger publik dibaca live (`ledger()` di `web/src/lib/fabius-chain.ts`)

**Ringkas:** halaman per bot untuk calon pengikut, menjawab empat pertanyaan berurutan: apa aturannya (dan kapan dikunci), apa yang dipegang hari ini
(paper), apa jejaknya hari demi hari, kapan ia dimatikan. Enam rute: `/bot/B1-TREND` ... `/bot/B6-BOUNCE`; huruf kecil -> 307 ke ID kanonik; bot asing
-> 404. Nama bot di landing (kalender bukti, buku slot, spesifikasi redup) dan panel vonis /verify menaut ke sini.

**Bentuk (FE Doctrine, sistem [[TL23 - Sistem Visual FE]]):**
- **Kepala:** kode bot tipis + nama tebal miring raksasa; pil peran (identitas + slot / penantang + bayangan n/60 + gerbang / "spesifikasi di-hash, tidak
  berjalan"); kubus besar bernapas (putih = penghuni, indigo = penantang, bening = tidak berjalan). Panel kaca: metode DALAM TEKS ASLI yang dikunci + glos
  EN (hanya mode EN, berlabel "terjemahan, bukan teks yang dikunci"), chip parameter/tier/jumlah aset/jam maju, chip kunci spesifikasi (tautan tx
  LockRegistry) atau "di-hash, belum dikunci di chain".
- **01 Buku paper hari ini (panel malam):** universe = 16 kubus; bercahaya = dipegang + bobot, indigo = short, redup = flat; lencana baru/keluar dibanding
  tick sebelumnya; bar, jam tulis, bobot kotor, tautan "periksa hari ini". Dibaca live di server; gagal baca = galat merah "bukan berarti flat" (T8).
- **02 Hari demi hari:** satu kubus per hari tutup sejak genesis (keadaan sama dengan kalender landing; tick live yang belum ada di snapshot = menunggu),
  jumlah sinyal, lag jam; tiap hari menaut ke /verify; satu kubus putus-putus "berikut".
- **03 Terkunci, urut waktu:** kunci yang berlaku untuk bot ini + "tick maju pertama ditulis" di satu garis waktu.
- **04 Uji maju:** tiga tangki F-D16 (sinyal, hari settle, bulan).
- **05 Kapan ia dimatikan:** teks pembunuh asli besar + glos + syarat mesin terkunci (B1-K1/K2, B3-K1/K2) + tautan kunci FABIUS-PEMBUNUH-v1.
- Bot tanpa jam maju (B2, B4, B5, B6): kepala + kunci + pembunuh; nomor section dihitung (01, 02), tidak bolong.

**Sejak 4 Okt siang (P119): section "Dieksekusi di akun demo"** (sesudah "hari demi hari", hanya bila `ledger/eksekusi/binance-demo/<bot>.jsonl`
ada; dibaca live di server). Keputusan yang sama tiga kali: paper (isi di penutupan), kertas aturan venue (isi 2 menit sesudah komit), akun demo (isi
nyata). Kepala: fee nyata, nyata vs kertas, latensi komit -> isi, pelanggaran, masing-masing dengan target PRD §6. Per bar satu kartu dengan **sumbu bps**:
garis tegak = penutupan (paper), kubus indigo = isi kertas, kubus putih = isi nyata; kanan = lebih buruk bagi kita. Kartu susulan ditandai; bar tanpa
order menampilkan bobot terpenuhi. Saldo virtual: tanpa angka untung. Uji lokal memakai `FABIUS_RAW_BASE` (override sumber raw, hanya untuk uji) +
ledger pratinjau dari Gist nyata: bar 10-02 kertas -0,6 bps vs nyata +77,3 bps (eksekusi nyata 10,9 jam sesudah komit), fee 4,0 bps, 0 pelanggaran;
bar 10-03 0 order, bobot terpenuhi 99,2 %. Poles dari cek visual: label di tepi kartu disejajarkan ke dalam, label "paper = penutupan" dipindah ke
legenda, fee tanpa tanda +.

**Kejujuran yang dipaksa oleh data (4 Okt):**
- Garis waktu memperlihatkan tick maju pertama (B3: 2 Okt 10:00Z) SEBELUM kunci spesifikasi (15:49Z) - sebab bar 1 Okt "sebelum kunci". Ditampilkan, tidak
  disembunyikan.
- Judul pembunuh "ditetapkan sebelum sinyal pertama", bukan "sebelum transaksi pertama": paper tidak bertransaksi; genesis ledger yang memuat `spec_sha`
  (B1 08:46Z, B3 09:55Z, 2 Okt) mendahului tick pertama (09:13Z, 10:00Z). Syarat mesin dikunci 3 Okt 06:26Z, sebelum ada satu pun settle final (settle = 0).
- Glos EN adalah terjemahan; yang dikunci adalah teks Indonesia di spesifikasi.

**Bukti 4 Okt (lokal, `next start -p 3008`):** `/bot/B1-TREND`, `B2-RS`, `B3-CARRY`, `B4-LISTING-FADE`, `B5-CORE-RWA`, `B6-BOUNCE` -> 200;
`/bot/b1-trend` -> 307 `/bot/B1-TREND`; `/bot/XX` -> 404; landing memuat enam `href="/bot/..."`. Peramban waktu-nyata (desktop 1440 + ponsel): B3 buku
paper 1/16 dipegang (ETC 6,25 %, DOT "keluar"), B1 16/16 (6,25 % tiap aset, bobot kotor 100 %), hari 10-01 sebelum kunci (2 sinyal, 10,0 j), 10-02
terbukti (1 sinyal, 8,7 j), 10-03 "tutup, tick menunggu"; B2 dalam bahasa ID: 01 kunci (ambang, uji maju, anggaran), 02 pembunuh teks saja. Tanpa
gulir horizontal di ponsel.

**HIDUP 4 Okt (komit `81f3d504`, Vercel dari push):** `https://fabius-one.vercel.app/bot/B3-CARRY`. Produksi: `/bot/B1..B6` 200, `/bot/b3-carry` -> 307,
`/bot/XX` -> 404; HTML B3 memuat `ledger/paper/B3-CARRY.jsonl · 2026-10-04T08:29:23Z` (dibaca live di server Vercel), ETC 6,25 %, DOT keluar, tanpa
pesan galat; landing memuat 6 tautan `/bot/`; MCP `fabius_verify` B3 2026-10-02 tetap SAH.

**Temuan cek visual (diperbaiki):** kubus putih "dipegang" tak terbedakan dari flat di latar terang -> buku paper pindah ke panel malam; chip kunci
spesifikasi terpotong di ponsel -> chip boleh membungkus.

**Batas yang diketahui:** URL dengan persen-encoding rusak (`/bot/%E0%A4%A`) -> 500 dari Next sendiri sebelum kode halaman jalan (rute statis memberi
404); tidak memengaruhi data.

**Terkait:** [[TL19 - web landing]] · [[TL24 - halaman verify]] · [[TL20 - server MCP]] · [[TL23 - Sistem Visual FE]] · [[00-Overview/03 - Decisions]] F-D16

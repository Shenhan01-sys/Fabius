---
tags: [perkakas, "TL45", meja, mcp, x402, akun]
---

# TL45 - MCP berbayar meja: deposit FAB, saldo, kunci API, potong per panggilan (P157, F5)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Status 7 Okt:** DIBANGUN + diuji LOKAL; **belum di-deploy, belum dibuka**. Sakelar `FABIUS_F5` (gerbang `fabius-x402`) dan `FABIUS_MCP_BERBAYAR`
(web Vercel) **bawaan MATI**: selama mati, `/account*` di gerbang menjawab 404 dan `/mcp` tetap 19 alat lama persis seperti [[04-Tools/TL20 - server MCP]]
(F-D111 #4). Rencana ditulis sebelum kode (epik 11 §10 langkah 1); bukti di bawah dicetak perintahnya 7 Okt.
**Sumber:** `tools/akun_mcp.py` (buku besar akun, kunci API, deposit, potong, rute `/account*`, pembangun data alat, CLI `periksa` / `uji-kering`) ·
`tools/akun_uji_kering.py` (uji kering ujung-ke-ujung: gerbang HTTP lokal + chain palsu) · gerbang `tools/x402_sinyal.py` (hook rute GET/POST + `Gate.akun`
+ log mulai; settle x402 + `paid_in_receipt` yang sudah ada) · `railway/Dockerfile` + `tools/railway_up.py` (modul ikut image) · web `web/src/lib/akun.ts`
(harga, daftar alat, pesan kunci, klien gerbang) · `web/src/lib/mcp-tools.ts` (registrar mode berbayar + lima alat F5) · `web/src/app/mcp/route.ts` (handler
per permintaan membawa kunci) · `web/src/lib/x402-buy.ts` (`bayarX402`, satu alur x402 untuk /buy dan deposit) · halaman `web/src/app/account/page.tsx` +
`web/src/components/akun/AkunView.tsx` · tes `engine/tests/test_akun_mcp.py` (22) · T8 SK-M11, SK-M12 (+ baris baru) · keputusan [[00-Overview/03 - Decisions]]
F-D111 · epik [[08-Backlog/11 - Epik Meja AI v2]] §7 + §14 · backlog P157

## Apa (F-D111, disetujui builder 5 Okt "Gasss")

MCP Fabius = **sinyal + data pendukungnya**, dan hanya bisa dipakai lewat x402: user mendepositkan FAB, mendapat kunci API dari tanda tangan dompetnya,
lalu tiap panggilan alat MCP berbayar memotong saldo otomatis. Gratis hanya penemuan (`fabius_pricing`, `fabius_account`). Alat data publik P140
(`fabius_dexscreener`, `fabius_rugcheck`, `fabius_bubblemaps`, `fabius_fomo`) dicabut dari MCP; alat tingkat 0 F-D89 pindah ke berbayar. Halaman web
`/verify` tetap gratis.

| alat | harga | isi | status harga |
|---|---|---|---|
| `fabius_signal` | 0,01 FAB (10 000 atomik) | siklus terakhir meja v2: bot dominan, nilai keenam bot, instrumen + skornya, eksposur, veto, target aturan, slot posisi terbuka, isi siklus, ekuitas, kursi + status tiap agent, hash rekaman + bukti siklus (root, tx, DeskAnchor) | F-D111 #2 (disetujui) |
| `fabius_signal_explain` | 0,02 FAB (20 000) | jawaban tiap agent siklus itu (bot, skor_bot, keyakinan, instrumen, faktor, ringkasan, veto, hash rekaman, prompt_sha) + **kontribusi** tiap agent kursi aktif ke nilai bot dominan (poin = k x s / n, bagian) + fitur instrumen terpilih dari snapshot siklus yang SAMA (`data_sha`) + bukti siklus | F-D111 #2 (disetujui) |
| `fabius_data` | 0,005 FAB (5 000) | snapshot F1 terakhir: fitur per aset (bisa disaring <= 20 simbol), fitur per bot, kesehatan sumber + 24 jam, sha snapshot + registry | F-D111 #2 (disetujui) |
| 13 alat lama (`fabius_verify`, `fabius_latest_signals`, `fabius_track_record`, `fabius_signals`, `fabius_status`, `fabius_list_bots`, `fabius_locks`, `fabius_proof_feed`, `fabius_confidence`, `fabius_analysts`, `fabius_desk`, `fabius_analyst_join`, `fabius_desk_join`) | 0,005 FAB | sama dengan sekarang, dijalankan server MCP lalu dipotong | **USULAN** (F-D111 #3 tidak menyebut harganya) |
| `fabius_pricing`, `fabius_account` | gratis | harga + cara deposit + kunci + kejujuran + kepala buku; saldo + kunci + riwayat rekaman pemilik kunci | F-D111 #2 |
| dicabut di mode berbayar | - | P140 (4 alat) + **USULAN**: `fabius_overview` dan `fabius_signal_offer` dilebur ke `fabius_pricing` (gratis hanya penemuan) | F-D111 #3 + USULAN |

## Alur

1. **Deposit:** `GET /account/deposit/<atomik>` -> 402 + PAYMENT-REQUIRED (x402 v2 exact, Permit2 + EIP-2612, payTo gerbang, jumlah = deposit) -> klien
   menandatangani (nol gas, bentuk SAMA dengan `/signal`; web memakai `bayarX402` yang sama dengan /buy) -> ulang dengan PAYMENT-SIGNATURE -> gerbang memeriksa
   otorisasi bertanda tangan (`check_payment`), settle lewat proxy kanonis (`Gate.settle`: `eth_call` dulu, Transfer pembeli -> payTo HARUS ada di receipt)
   -> rekaman `deposit` -> saldo bertambah. Kunci idempoten = (dompet, nonce Permit2): otorisasi yang sama tidak dikreditkan dua kali dan tidak dikirim
   ulang ke chain. Settle gagal / tanpa Transfer = tidak ada kredit. Bila tulis buku gagal SESUDAH settle: 500 "PAID BUT NOT CREDITED" + tx (rekonsiliasi
   manual, lihat BELUM).
2. **Kunci API:** dompet menandatangani pesan teks EIP-191 (`FMT_KUNCI`: `Fabius MCP API key v1` / wallet / ts / chain 97) -> `POST /account/key` -> kunci
   `fabk_` + 32 byte acak ditampilkan SEKALI; buku hanya menyimpan sha256-nya. Pesan kedaluwarsa (> 10 menit dari jam gerbang), dipakai ulang, atau bukan
   dari dompet itu = ditolak; maks 3 kunci aktif per dompet. Cabut: pesan `FMT_CABUT` bertanda tangan dompet, atau pemegang kunci itu sendiri.
3. **Potong:** alat yang datanya dari gerbang (`fabius_signal`, `_explain`, `fabius_data`): `POST /account/call` - kunci sah -> saldo >= harga -> data dibangun
   (DI LUAR kunci buku) -> cek ulang + potong + sha respons -> data. Data gagal dibangun = TIDAK dipotong. Alat yang dijalankan server MCP (13 alat lama):
   `POST /account/charge` `check` dulu (tanpa potongan) -> alat dijalankan -> potong dengan sha hasilnya -> hasil hanya dikirim bila potongan berhasil;
   galat alat tidak dipotong. Kunci idempoten = (dompet, `call_id`): ulangan menerima jawaban + sha yang sama tanpa potongan kedua (cache memori 256;
   sesudah mulai ulang: 409, tetap tidak dipotong). Cek saldo + potong di bawah satu kunci: panggilan paralel tidak pernah membuat saldo negatif.
4. **Saldo kurang (SK-M11):** 402 + petunjuk deposit + faucet; tidak ada data terkirim; saldo tidak berubah; tidak ada rekaman.
   **Kunci tidak sah / dicabut / bukan kunci Fabius (SK-M12):** 401; tidak ada data.

## Buku besar akun (sumber kebenaran)

Append-only `/data/akun/akun.jsonl` di volume gerbang. Rekaman `deposit` {dompet, atomic, tx, nonce} · `kunci` {kunci_id, kunci_sha, pesan_sha} · `cabut`
{kunci_id, oleh} · `potong` {kunci_id, alat, atomic, call_id, respons_sha}. Tiap rekaman: `n` (urutan global), `prev` = `h` rekaman sebelumnya DOMPET
YANG SAMA, `h` = sha256 JSON kanonisnya. Saldo = jumlah deposit - jumlah potongan, dihitung ulang dari buku saat mulai (tidak ada saldo tersimpan terpisah).
Buku yang `h` / `prev` / `n`-nya tidak cocok (diubah, dihapus, diulang) = layanan akun **berhenti** (503) - tidak menebak saldo. User menerima
rekamannya sendiri lewat `fabius_account` / `/account` dan bisa memeriksa rantai + tiap deposit di BscScan; kepala buku (hash rekaman terakhir) publik
di `/account/pricing`; `python -X utf8 tools/akun_mcp.py periksa --folder <dir>` memeriksa seluruh buku dari nol.

## Sakelar

- Gerbang: `FABIUS_F5` - hanya `hidup` / `nyala` / `1` yang membuka; kosong / `mati` / nilai lain = MATI. Log mulai mencetak `MCP berbayar (P157 F5): MATI|TERBUKA`
  + jumlah rekaman + utuh/RUSAK + kepala buku.
- Web: `FABIUS_MCP_BERBAYAR` (env server Vercel) - aturan kata yang sama. Mati = handler `/mcp` lama (versi 0.1.0, 19 alat). Hidup = handler per permintaan
  (versi 0.2.0) membawa kunci dari `Authorization: Bearer fabk_...` ke alat. `FABIUS_GATE` hanya untuk uji lokal (`/mcp` -> gerbang lokal).
- Urutan buka (langkah builder): deploy gerbang -> `FABIUS_F5=hidup` -> uji deposit + kunci di `/account` -> `FABIUS_MCP_BERBAYAR=hidup` di Vercel + redeploy.

## Batas (semua **USULAN**, bisa diubah builder)

Deposit min 0,05 FAB dan maks 1 FAB per otorisasi (selaras policy Privy P148 <= 1 FAB per tanda tangan; faucet memberi 0,5 FAB); tombol halaman 0,1 / 0,25 /
0,5 FAB; maks 3 kunci aktif per dompet; pesan kunci berlaku 10 menit; `call_id` <= 64 karakter `[A-Za-z0-9._:-]`; format kunci `fabk_` + 32 byte acak
(base64url); harga 13 alat lama 0,005 FAB; `fabius_overview` + `fabius_signal_offer` dilebur ke `fabius_pricing`; riwayat `/account` 50 rekaman terakhir.

## Bukti (7 Okt, lokal Windows; dicetak perintahnya)

- `python -X utf8 -m pytest -q engine/tests/test_akun_mcp.py` -> **22 passed** (buku + rantai + rusak = 503; sakelar; header kunci; kunci EIP-191 sungguhan
  dari dompet buangan; deposit sekali kredit; deposit buruk tanpa kredit; SK-M11; SK-M12; call_id sekali potong; data gagal tidak dipotong; 20 utas paralel
  dengan saldo untuk 5 -> 5 x 200 + 15 x 402, saldo 0; kontribusi = rumus `konsensus2`; data alat dari keluaran `meja2.siklus2` ASLI; kontrak web = gerbang
  lewat Node).
- `python -X utf8 tools/akun_mcp.py uji-kering` -> 15 langkah HTTP lewat handler gerbang ASLI, `semua_sesuai: true`: harga 200; deposit tanpa bayar 402
  (amount 100000, payTo gerbang); deposit 0,1 FAB dengan tanda tangan EIP-712 sungguhan 200 (saldo 100000, 1 tx palsu); otorisasi sama diulang 200
  `repeat` (saldo 100000, tetap 1 tx); kunci EIP-191 201 (teks kunci TIDAK ada di buku); pesan kunci dipakai ulang 409; kunci palsu 401 tanpa data;
  `fabius_signal` 200 (saldo 90000); call_id sama 200 `repeat` sha sama saldo tetap; `_explain` 200 (3 agent, bagian kontribusi berjumlah 1,0; saldo
  70000); `fabius_data` disaring 2 aset 200 (65000); alat lama `check` 200 lalu potong 200 (60000); 3 panggilan lagi lalu 402 + petunjuk deposit tanpa
  data (saldo 0); `/account` 200 (deposit 100000, terpakai 100000, 9 rekaman); cabut sendiri 200; kunci dicabut 401; buku 10 rekaman, masalah 0.
- Server MCP sungguhan (`next dev` di worktree, `FABIUS_MCP_BERBAYAR=hidup`, `FABIUS_GATE` -> gerbang lokal dengan data meja sintetis + chain palsu):
  `initialize` -> `fabius 0.2.0`; `tools/list` -> **18 alat** (5 F5 + 13 lama berbayar; 6 dicabut); `fabius_pricing` + `fabius_account` gratis;
  `fabius_signal` / `_explain` / `fabius_data` dipotong 0,01 / 0,02 / 0,005; `fabius_list_bots` (lama) dipotong 0,005 lewat `/account/charge` (catatan
  "Charged" ditambahkan ke hasil); tanpa kunci -> galat + 4 langkah cara mendapat kunci; kunci palsu -> "invalid or revoked API key"; saldo habis -> galat
  "insufficient balance" + petunjuk deposit, saldo tidak pernah negatif; `periksa` atas buku gerbang lokal -> 9 rekaman, masalah 0. Mode bawaan (env
  mati): `fabius 0.1.0`, **19 alat** = daftar di HEAD persis (tidak ada yang berubah selama sakelar mati).
- Halaman `/account` (`next dev`): HTTP 200, judul + tabel harga ter-render; status "belum dibuka" bila gerbang menjawab non-200 untuk `/account/pricing`.
- `python -X utf8 tools/test_census.py --wajib-semua` (worktree P157) -> **`JALAN: 840 tes | lulus 840 | DILEWATI 0 | GAGAL 0 | ERROR 0 | 313 s`**,
  SEMUA JALAN DAN LULUS. `cd web && npx tsc --noEmit` 0 · `npx eslint src` 0. T8 usulan (SK-M11/SK-M12 pengganti + 7 baris baru) diperiksa pada salinan:
  `baris 256 | berjangkar 255 | ... | masalah 0`, `--run: 234 tes jangkar | lulus 234 | DILEWATI 0 | GAGAL 0`.

## Yang BELUM / tidak dibuktikan

- **Testnet sungguhan belum** (kriteria keluar F5 §8): deploy gerbang + `FABIUS_F5=hidup` + deposit sungguhan dari dompet Privy di `/account` + Vercel
  `FABIUS_MCP_BERBAYAR=hidup` = langkah builder. Uji lokal memakai chain palsu (receipt dibangun dari calldata settle sungguhan) - bukan bukti chain.
- Halaman `/account` di peramban dengan login Privy (tanda tangan typed data + pesan) belum diklik manusia; tidak ada tautan navbar sampai dibuka.
- **`/desk` v2 menampilkan kontribusi** (kriteria keluar F5) BELUM di halaman web: kontribusi baru tersedia lewat `fabius_signal_explain` (berbayar).
  Menampilkannya di `/desk` publik perlu keputusan builder (tunda publik 24 jam P165 berlaku untuk isi keputusan).
- Rekonsiliasi otomatis "dibayar tapi tidak dikreditkan" (tulis buku gagal sesudah settle) belum ada: gerbang membalas 500 + tx + log `GALAT`, operator
  mengkreditkan manual. Batas laju pembuatan / pencabutan kunci per dompet belum ada (buku bisa tumbuh oleh dompet yang sama).
- Kepala buku akun belum di-anchor on-chain (hanya publik di `/account/pricing`); `call_id` idempoten lintas ulangan klien hanya bila klien memakai
  `/account/call` langsung - server MCP membuat `call_id` baru per `tools/call`.
- Deskripsi alat lama di mode berbayar tetap teks lama + akhiran "PAID: 0,005 FAB per call"; `fabius_overview` hilang dari mode itu (isinya ke `fabius_pricing`).

## Cara memakai

- Tes: `python -X utf8 -m unittest engine.tests.test_akun_mcp` (kontrak web butuh Node >= 22.6).
- Uji kering ujung-ke-ujung: `python -X utf8 tools/akun_mcp.py uji-kering` (gerbang lokal, chain palsu, dompet buangan; tidak ada tx, tidak ada jaringan).
- Periksa buku: `python -X utf8 tools/akun_mcp.py periksa --folder /data/akun` (baca saja; kode keluar 1 bila rantai rusak).
- Klien: `GET /account/pricing` -> faucet -> deposit x402 `GET /account/deposit/100000` -> tanda tangani `FMT_KUNCI` -> `POST /account/key` ->
  `claude mcp add --transport http fabius https://fabius-one.vercel.app/mcp --header "Authorization: Bearer <kunci>"`.

**Terkait:** [[00-Overview/03 - Decisions]] F-D111 · F-D89 · F-D100 · [[08-Backlog/11 - Epik Meja AI v2]] §7 · §14 · [[04-Tools/TL20 - server MCP]] ·
[[04-Tools/TL36 - meja v2 bot + instrumen]] · [[07-Testing/T8 - Semantik Kegagalan Operator]] SK-M11 · SK-M12

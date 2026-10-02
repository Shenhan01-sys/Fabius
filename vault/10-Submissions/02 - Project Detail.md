---
tags: [submission, "P-DETAIL"]
---

# Project Detail — Fabius

> **BN-PIVOT - 2 Okt 2026.** Arah proyek bergeser: Fabius menjadi **operator pemilih bot** yang kelak menjual **sinyal
> berbukti** dan membuka slot bot untuk penerbit luar ([[00-Overview/03 - Decisions]] F-D70 dan F-D71). Halaman ini
> menggambarkan keadaan **sebelum** pivot dan tetap benar untuk apa yang **sudah dibangun**; arah baru masih **usulan dan kode
> awal** ([[08-Backlog/05 - Epik Enam Bot]], [[08-Backlog/06 - Epik Gerbang Sinyal]], [[08-Backlog/07 - Epik Kolaborasi Bot Terbuka]]).
> Jangan memakai halaman ini untuk menyangkal arah baru, dan jangan menyebut arah baru sebagai fitur yang sudah ada.

**Bagian dari:** [[10-Submissions/00 - Hub Submissions]]
**Sumber:** `00-Overview/01 - Briefing.md`, `06-Results/`, `05-Ecosystem/`

## Kotak deskripsi (±2 kalimat, untuk form)

> Fabius adalah agen riset di BNB Chain yang menerbitkan **keputusan** atas aset meme — arah, masuk,
> stop, ukuran, horizon — dan menyimpan hash-nya ke chain **sebelum** hasilnya ada. Tiga jalur
> sinyal sudah kami uji sendiri; dua kami temukan mati setelah ongkos, danagenya sebagian besar
> **menolak** — penolakan itulah yang ikut ter-anchor (14 dari 17 keputusan, terukur dari `countByVerdict` di chain), sehingga klaim
> "disiplin" kami bisa diperiksa, bukan didengar.

## Versi panjang

**Masalahnya bukan "tidak ada bot", tapi "tidak ada yang bisa membuktikan bot-nya jujur".**
Sebagian besar submission agen trading berakhir sebagai klaim: angkanya ada, tapi tidak ada satu pun
kalimat yang bisa diperiksa orang luar tanpa memercayai timnya. Kami membalik bobotnya.

**Yang kami buat.** Sebuah agen yang tiap siklus: merekam keadaan pasar (universe BSC + narasi +
aliran wallet, dengan sha256 dan timestamp milik mesin pihak ketiga) → menyaring lewat gerbang
keras (riwayat harga cukup? keamanan kontrak **terukur**? likuiditas cukup untuk keluar?) →
mengambil keputusan arah lengkap (long/short, masuk, stop, target, ukuran, horizon) → mengirim
hash keputusan + hash gerbang + hash snapshot ke kontrak di chain 97 → dan, setelah horizon lewat,
menilai dirinya sendiri dari harga yang ia ambil sendiri.

**Yang membuatnya bukan klaim kosong.** `anchor.py --verify` menghitung ulang id setiap anchor
dari berkas di repo, lalu membaca `getAnchor(id)` ke chain dan membandingkan enam field — termasuk
nama aset — **tanpa kunci dan tanpa gas**. 11/11 cocok. Dan yang paling penting: yang ter-anchor
bukan hanya keputusan berani, tapi juga **penolakan**, dengan alasannya ikut ter-hash.

**Bagian BNB-nya.** Agen ini punya identitas di `IdentityRegistry` ERC-8004 resmi chain 97
(tokenId 2494; diverifikasi dengan membaca registry, `ownerOf`/`getAgentWallet` = alamat agen),
menerbitkan kartu agen yang menyebut endpoint-nya, dan **menjual keluarannya lewat x402** ke proxy
kanonis `0x402085c2…` — ada transaksi nyata yang membuktikan pembayarannya (klien nol gas, uang
berpindah, kami baca saldo dari chain, bukan dari log server kami). Jalur eksekusi posisi
(`ExecutionVault` + `DemoPair`) sudah ada dengan pagar di kontrak: plafon harian, ukuran maksimum,
dan larangan membuka posisi tanpa hash keputusan yang ter-anchor.

**Yang tidak kami klaim.** Kami tidak menjual sinyal. Setelah ongkos nyata, momentum harga rugi di
12/12 aset; menyalin smart money di 24 jam justru **kalah** dari kerumunan; satu-satunya horison
yang menguntungkan kerumunan whale (30 hari) tidak bisa kami bersihkan dari bias seleksi sebelum
tenggat — jadi kami tinggal menunggu, bukan menjualnya. Semua testnet, token demo milik sendiri,
tanpa custody, tanpa dana pengguna.

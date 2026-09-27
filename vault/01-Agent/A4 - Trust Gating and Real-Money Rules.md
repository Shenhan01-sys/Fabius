---
tags: [agen, "A4"]
---

# A4 - Trust Gating and Real-Money Rules

**Bagian dari:** [[01-Agent/00 - Hub Agent]]
**Sumber:** permintaan builder 26 Sep (pesan penuh di ekspor sesi, baris 158.726) + keluaran
[[04-Tools/TL5 - ledger]] + `contracts/ExecutionVault.sol`. Estimasi yang bukan hasil pengukuran
ditandai *(estimasi)*.

**Ringkas:** builder meminta gerbang: *"setelah winstreak tertentu, kalau trust di atas 60% baru
buka posisi nyata; dananya mentok $5/hari; ukuran $0,5–1"*. Bentuk gates-nya diterima, metriknnya
yang dibetulkan. Halaman ini adalah tempat keputusan itu tinggal, karena dia menentukan **kapan**
agen boleh menyentuh uang dan **berapa** — dan itu bukan detail implementasi, tapi posisi produk.

## Gerbang yang diminta vs gerbang yang dipakai

| yang diminta | yang dipakai sekarang | kenapa diganti |
|---|---|---|
| win-streak / "trust > 60%" | **harapan bersih > 0 setelah ongkos nyata di ukuran itu**, `n ≥ 20`, tetap positif setelah **fold terbaik dibuang**, lolos **BH α=0,10**, dihitung **di luar sampel** | win rate tinggi + rugi itu normal, dan kami punya contohnya sendiri: panel whale **WR 69,8 %** tapi jam-per-jam **−10,4 bps** vs kerumunan; satu posisi MARSCOIN yang **MENANG** net-nya cuma **+1,5 bps** (arahnya benar, marketnya yang bayar ongkos) |

Status hari ini, dibaca jujur: posisi yang sudah jatuh tempo = **2**
([[06-Results/07 - Matured Outcomes]]). `n=2` tidak memenuhi satu pun syarat di atas. Artinya
gerbangnya menjawab **"belum boleh real sama sekali"** — dan itu jawaban yang benar, bukan
penundaan yang sopan. Kalau angka ini berubah, yang berubah adalah halaman ini, bukan ambangnya.

## Ukuran posisi: ongkos itu tetap, modalmu yang kecil

`$0,5–1 per posisi` dengan plafon `$5/hari` berbenturan dengan aritmetika, bukan dengan selera.
Biaya per transaksi tidak ikut mengecil saat notional mengecil — lihat
[[Concepts/Cost Is Fixed]].

| ukuran posisi | ongkos tetap ±$0,05 bolak-balik *(estimasi mainnet, belum diukur di repo ini)* | harus naik sekian % cuma untuk balik modal |
|---|---|---|
| $1 | ~5 % | **+5 %** |
| $5 | ~1 % | +1 % |
| $50 | ~0,1 % | +0,1 % |

Angka yang **sudah** kami ukur: round-trip di venue demo kami sendiri = **59 bps** untuk posisi
1 unit ([[07-Testing/T3 - Execution Suite]]) — itu kurva x·y=k + fee 30 bps, bukan gas mainnet.
Yang belum: gas nyata `openLong`/`close` di 97 dan di venue mana pun *(belum diukur)*.

Konsekuensi yang kami ambil: menjalankan $5/hari di atas sinyal yang kami ukur sendiri **negatif**
bukan "bukti disiplin", tapi kurva kerugian yang rapi — dan kurva rugi yang rapi terlihat bagus di
slide. Justru itu yang tidak boleh kami pamerkan sebagai pembuktian.

## Yang ditahan: "admin fee 5–10 % langsung dari wallet user"

Alasannya bukan kehati-hatian generik, ada dua yang konkret:

1. **Teknis.** "Diambil langsung dari wallet user" hanya bisa berarti user memberi kami izin yang
   cukup untuk memindahkan dananya. Izin seperti itu tidak punya versi aman: sekali bocor, yang
   hilang dana semua user. Ini bertentangan dengan aturan yang kami pegang di tempat lain —
   tidak ada custody (lihat [[00-Overview/02 - Business Process]]).
2. **Posisi.** "Dibayar dari keuntungan klien" = wilayah nasihat investasi/pool dana; di Indonesia
   itu Bappebti/OJK. Untuk demo hackathon ini bisa dibaca juri web3 sebagai nilai plus dan dibaca
   siapa pun yang cek regulasi sebagai minus. Kami tidak menulisnya sebagai fitur.

**Penggantinya, tanpa custody, tetap terasa "bayar kalau untung":**
- **Gratis saat abstain.** Tagihan hanya keluar kalau kami menerbitkan keputusan. Kalau jawabannya
  "saya tidak tahu", tidak ada yang bayar — insentifnya sejalan, kami yang dihukum kalau asal bunyi.
- **Kredit yang bisa diaudit, bukan potongan.** Hasil keputusan ada di catatan yang ter-anchor;
  kalau ledger memvonis **RUGI**, permintaan berikutnya dapat kredit dari kuota user. Tidak ada uang
  keluar dari wallet siapa pun, tapi kami tetap menanggung risiko kalau kami salah.
- **Success fee, kalau memang mau:** satu-satunya bentuk yang tidak menyerupai dana adalah user
  **menandatangani sendiri** pembayaran per kejadian untung — jumlah dibatasi di muka, bisa dicabut
  kapan saja. Itu opsi, bukan default, dan risikonya tetap ditulis di sini kalau nanti dibangun.

## Kenapa tidak "lewat GMGN saja": venue menentukan modal

Builder bertanya (26 Sep): *"di GMGN harus uang beneran ya? gabisa yang bohongan atau testnet?"*
Jawabannya yang membatasi desain: jalur trading GMGN adalah **mainnet BSC dengan dana nyata**, butuh
API key bertanda tangan (Ed25519/RSA per dokumentasinya) dan kunci yang menandatangani order ada di
mesin kami. Itu tiga hal yang tidak boleh kami asumsikan sekaligus: dana asli, kunci asli di tangan
kami, kerugian nyata kalau agen salah.

Karena itu jalurnya dibalik: **kami yang jadi venue-nya.** `DemoPair` + `ExecutionVault` di chain 97
mengeksekusi posisi sungguhan (transaksi, receipt, gas) tanpa menuntut rupiah dari siapa pun —
[[02-Contracts/C4 - DemoPair and DemoAsset]]. Yang tidak bisa diberikan jalur ini: slippage pasar
meme sungguhan. Itu harga yang kami bayar, dan itu tertulis, bukan disembunyikan. Aturan yang sama
memblokir "bukti" yang butuh modal: F-D16 di [[00-Overview/03 - Decisions]].

## Yang dirancang vs yang jadi

| komponen (rancangan 26 Sep) | status 27 Sep |
|---|---|
| `execution.py` — buka/tutup posisi nyata | **ada: `tools/execute_live.py`** (27 Sep). Menolak membuka posisi kalau `decisionHash`-nya tidak ada di `DecisionAnchor`, dan menolak `ABSTAIN`. Dua round-trip nyata: −59 bps per putaran |
| `risk_cap.py` — plafon harian, 1 posisi paralel, kill-switch, berhenti kalau ledger belum menilai | **sebagian di kontrak**: `dailyCap`, `maxPositionQuote`, `HARD_CEILING`, `killSwitch`, `AlreadyOpen`, `NoAnchorHash` ([[02-Contracts/C3 - ExecutionVault]]) |
| `settlement.py` — tiap posisi = transaksi nyata, saldo dibaca ulang dari chain | **belum**; arah desainnya sudah: `openPositionOf()` + event `Closed` dengan `realizedQuote` dan gas terpakai |
| `metering.py` — bayar-per-keputusan, abstain gratis, rugi = kredit | **sebagian**: x402 menagih per keputusan ([[04-Tools/TL6 - x402 gate and client]]); abstain-gratis & kredit **belum** diimplementasikan |
| `trust.py` — kelayakan real-trade (n≥20, net>0, drop-best-fold, BH) dan menampilkan **berapa lagi yang kurang** | **belum ada.** P1 sudah jalan, jadi alasan "nunggu posisi nyata" sudah tidak berlaku: yang tersisa cuma keputusan apakah gerbangnya dipasang sebelum demo atau sesudahnya |

## Yang diputuskan builder (27 Sep)

Jalur nyata dipilih: **testnet dengan transaksi on-chain sungguhan** (bukan mainnet dengan kunci
hidup), deploy eksekusi ke 97 **lebih dulu**, FE di Vercel belakangan. Lihat F-D20/F-D21 di
[[00-Overview/03 - Decisions]] dan [[08-Backlog/01 - Backlog]] P1.

**Terkait:** [[01-Agent/A3 - One-Way Gates]] · [[02-Contracts/C3 - ExecutionVault]] ·
[[06-Results/07 - Matured Outcomes]] · [[Concepts/Cost Is Fixed]] ·
[[10-Submissions/01 - Claims Cheat Sheet]]

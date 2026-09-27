---
tags: [tk, tk-sinyal, "O8"]
---

# O8 - MEV dan Sandwich

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** analisis ([[PL3 - Menganalisis]])
**Sumber:** mekanisme = pengetahuan standar pasar — tidak ada rujukannya di repo ini; jalur pembayaran
kami ada di [[02-Contracts/C5 - Vendored x402 Sources]] · [[05-Ecosystem/02 - x402 Payment]] ·
[[07-Testing/T4 - x402 Fork Suite]] · topik dari `vault/TradingKnowledge/Plan.txt` §"Strategi
Berbasis On-Chain & Data Crypto Spesifik" (baris "MEV & Sandwich attack awareness")

**Ringkas:** MEV adalah nilai yang bisa diambil dari **urutan** transaksi, bukan dari isinya.
Sandwich bentuk paling sederhana untuk pembeli DEX: seseorang membeli sebelum ordermu dan menjual
sesudahnya, lalu mengambil slippage yang **kamu izinkan sendiri** lewat batas harga. Untuk Fabius
statusnya harus ditulis tanpa dibagus-baguskan: kami tidak mengukur apa pun di sini, dan angka ongkos
59 bps yang kami pegang **bukan** MEV — itu kurva pool demo kami sendiri.

## Definisi yang bisa dihitung

```
shortfall_bps = (harga_eksekusi − harga_kuotasi) / harga_kuotasi × 1e4        # diukur per order
frontrun      = beli sebelum order korban, jual sesudah; untung dari dampak yang dibuat korban
backrun       = posisi setelah; mengambil sisa peluang yang terbuka sesudahnya
sandwich      = frontrun + backrun dalam satu atomic bundle pada pool yang sama
ekstraksi_max ≈ min(toleransi_slippage_korban, dampak_korban_sendiri)         # dibatasi parameter korban
biaya_penyerang = gas + priority_fee/bid yang dibayar untuk menang urutan
```

Poin yang paling sering terlewat: kerugian korban **bukan** besaran acak — ia dibatasi oleh batas
slippage yang dia kirim sendiri. Karena itu "slippage tinggi = terekspos" adalah hubungan langsung,
dan parameter itu adalah bagian dari strategi, bukan detail eksekusi.

## Cara pakai yang diklaim

Diklaim oleh praktisi eksekusi dan material edukasional wallet: pakai relai privat / RPC terlindungi,
perkecil `amountOutMin`, jangan order di pool tipis, atau "order kecil tidak menarik penyerang".
Untuk order kecil klaimnya **setengah benar**: penyerang membayar `biaya_penyerang`, jadi ada
ambang ukuran di bawah mana ekstraksi tidak menguntungkan — tapi ambang itu **bergantung biaya gas
rantainya**, dan pada chain dengan gas murah ambangnya jauh lebih rendah daripada yang biasa
diceritakan dari era mainnet. Berapa angka yang berlaku untuk BSC hari ini: *(belum diukur oleh kami)*.
Tidak ada pemilik klaim yang menyediakan angka kerugian per order untuk venue kami.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| urutan transaksi / isi mempool sebelum masuk blok | `TIDAK-ADA` | tidak ada jalur di repo; Dune hanya mengembalikan baris **konfirmasi**, dan barisnya retro-updatable ([[Concepts/Point-in-Time vs Retro-updatable]]) |
| order book L2, tick, heatmap | `TIDAK-ADA` | §C — dan tanpa ini mikrostruktur tempat MEV hidup tidak bisa direkonstruksi |
| log shortfall kuotasi vs eksekusi per order | `TIDAK-ADA` | venue eksekusi kami adalah **pool demo sendiri** (kurva x·y=k + fee 30 bps) → round-trip **59 bps** (§D) |
| kerugian nyata pada jalur eksekusi kami | `ADA-TAPI` | §D: realized **−59 bps** per putaran dari event `Closed`; §F menyebut sebabnya eksplisit: itu **ongkos kurva di pool kami sendiri tanpa arus luar**, bukan ekstraksi pihak ketiga |
| harga gas untuk memperkirakan `biaya_penyerang` | `ADA-TAPI` | §D: 0,10 gwei **testnet 97** live (guard lama memakai floor 1 gwei → menolak karena plafon sendiri); mainnet belum diukur |
| riwayat funding/OI sebagai proksi aktivitas bot | `TIDAK-ADA` | §C: histori funding per-aset yang bisa ditarik mundur tidak kami punya |

## Uji di Fabius

Belum bisa dijalankan, dan perintahnya **belum ditulis** — tidak ada satu pun berkas `tools/` yang
merekam kuotasi sebelum eksekusi. Yang dibutuhkan supaya metrik ini menjadi sesuatu selain kosakata:

1. Simpan **kuotasi** dan **eksekusi** sebagai dua angka berbeda untuk setiap order (termasuk order
   paper), lalu cetak `shortfall_bps` per order sebagai deret.
2. Bandingkan shortfall pada jalur publik vs jalur dengan relai terlindungi, dengan **ukuran dan jam
   yang sama** — kontrolnya harus sepasang, karena ukuran adalah variabel utamanya.
3. Hasilnya masuk ke ongkos, bukan ke sinyal: ambang klaim kami adalah gross di atas **59 bps**
   (§D), `n >= 20` non-overlap, BH α 0,10, fold terbaik dibuang.
4. Catat bahwa P10 ditutup 28 Sep (§D): 59 bps terukur vs 20 bps asumsi yang dipakai seluruh jalur uji.
   Menambahkan satu komponen biaya lagi tanpa menyatukan keduanya akan membuat laporan ongkos jadi
   tiga angka yang tidak saling menjumlah.

## Batas dan mode gagal

- **"MEV" sebagai alasan untuk modeling yang buruk.** Slippage yang berasal dari dampak kamu sendiri
  di pool tipis, atau dari kurva fee, bukan ekstraksi. Menuliskannya sebagai MEV menutup diagnosis
  yang benar (§F: jalur eksekusi kami 3 putaran, WR 0 %, net −59,0 bps — dan itu memang ongkos).
- **Kerugian kecil tidak berarti risiko kecil.** Kandidat arah kami punya gross **+1,5…+4,0 bps**
  vs ongkos 20 bps (§F); pada skala sekecil itu **setiap** basis poin ekstraksi menghapus expectancy.
  Ini membuat O8 bukan halaman "awareness" — ia halaman yang menentukan apakah angka tipis boleh
  diperdagangkan sama sekali.
- **Relai privat memindahkan, tidak menghapus,** persaingan: penyerang berpindah ke validator dengan
  jalur sendiri; klaim "protected RPC 100 % aman" adalah klaim penjual *(belum diukur oleh kami)*.
- **Jalur pembayaran kami bukan swap.** x402 yang kami vendor memakai proxy Permit2 dengan **jumlah
  eksak**, dan sifat paksaannya dibuktikan di level kontrak lewat rangkaian fork test terhadap proxy
  ter-deploy ([[07-Testing/T4 - x402 Fork Suite]]): pemanggil `settle()` tidak bisa memindahkan dana
  ke alamat lain, melebihkan jumlah, atau memakai ulang nonce. Itu **bukan** perlindungan terhadap
  sandwich — tidak ada `amountOutMin` di jalur pembayaran, dan tidak ada penjualan yang bisa
  di-sandwich di sana. Menyamakan keduanya adalah klaim mekanisme yang tidak bisa dibaca dari repo.
- **Duplikasi:** shortfall dan adverse selection mengukur penyakit yang sama dari sisi berbeda
  ([[V5 - Mikrostruktur Spread dan Adverse Selection]], [[FD4 - Ongkos Perdagangan]]).

## Tingkat bukti

`T1` untuk mekanisme dan rumus ekstraksi (standar, dimiliki literatur MEV umum) · `T0` untuk angka
kerugian mana pun yang menyebut Fabius *(belum diukur)* · untuk Fabius: **tidak ada uji** — tidak ada
kuotasi, tidak ada mempool, tidak ada venue publik (§C/§D).

## Boleh dibaca, dilarang dibaca

- **Boleh:** "ongkos terukur kami 59 bps round-trip berasal dari kurva pool demo kami sendiri, bukan
  dari MEV; kami belum mengukur eksposur MEV dan tidak mengklaim lindung dari itu."
- **Dilarang:** "Fabius tahan MEV" · "jalur x402 kami dilindungi dari sandwich" · "order kami kecil
  jadi aman" · "penyerang mengambil X bps dari trade kami" — empat kalimat yang seluruhnya menjual
  sesuatu yang tidak pernah kami rekam.

**Terkait:** [[FD4 - Ongkos Perdagangan]] · [[V5 - Mikrostruktur Spread dan Adverse Selection]] ·
[[PL5 - Mengeksekusi dan Keluar]] · [[ST2 - Futures Hunter]] · [[Concepts/Cost Is Fixed]]

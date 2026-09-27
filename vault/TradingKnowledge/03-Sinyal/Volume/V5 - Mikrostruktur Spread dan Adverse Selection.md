---
tags: [tk, tk-sinyal, "V5"]
---

# V5 - Mikrostruktur Spread dan Adverse Selection

**Keluarga:** [[00 - Hub Sinyal]] · **Tahap:** keputusan ([[PL4 - Memutuskan]])
**Sumber:** pengetahuan standar pasar — tidak ada rujukannya di repo ini
(`Plan.txt` tidak menyebut mikrostruktur; angkanya dipikul [[Fakta Terukur]] §D)

**Ringkas:** Setiap kali kamu menjadi taker, kamu membayar dua hal sekaligus: selisih harga yang
tertulis (spread) dan informasi yang bocor lewat ordermu (adverse selection). Yang kedua adalah
**pajak bagi pihak yang tahu lebih sedikit**: kalau pesananmu sering diikuti pergerakan melawan
kita, berarti yang berdiri di seberangmu tahu sesuatu. Catatan ini penting di repo ini karena satu
satu-satunya ongkos yang **benar-benar kami ukur** adalah biaya perpindahan tangan
(**59 bps** round-trip, [[Fakta Terukur]] §D) — dan itu tempat seluruh keluarga sinyal diuji.

## Definisi yang bisa dihitung

```
quoted spread   = best_ask - best_bid                  (butuh L2 -> tidak kami punya)
mid             = (best_ask + best_bid) / 2
effective half-spread (sisi) = sign * (p_eksekusi - mid) / mid,  sign=+1 beli, -1 jual
realized   = perubahan mid setelah order isi      <- ini ADALAH adverse selection
quoted     = spread saat order dibuat              <- ini biaya yang terlihat
realized + quoted = effective                      (dekomposisi standar)
queue position    = jumlah order di depan kita pada level harga yang sama
```

Ukuran praktis yang setara dan bisa dihitung tanpa L2: **harga rata-rata masuk vs harga rata-rata
yang bisa diterima N menit kemudian pada ukuran yang sama**. Bedanya = biaya tak tertulis.

## Cara pakai yang diklaim

Klaim pasar: jangan menaker di buku tipis; masuk sebagai maker saat likuiditas dalam; jangan
melewati spread kalau horizon pendek karena biaya mendahului edge. Ini bukan "strategi", ini
lapisan yang **membatalkan** strategi lain: aturan arah dengan gross +1,5…+4,0 bps (§F) tidak punya
ruang apa pun untuk biaya spread di atasnya.

## Butuh data

| kebutuhan | status Fabius | bukti / batas |
|---|---|---|
| bid/ask (quoted spread) | `TIDAK-ADA` | tidak ada jalur L2 — [[Fakta Terukur]] §C |
| queue position, probabilitas isi maker | `TIDAK-ADA` | butuh buku order + riwayat antrian |
| biaya round-trip yang **terukur** di venue demo | `ADA` | **59 bps** posisi 1 unit (kurva x·y=k + fee 30 bps, bukan gas mainnet) — §D |
| biaya round-trip **nyata** yang sudah terjadi | `ADA` | **−59 bps** per putaran, dibaca dari event `Closed` di `decisions/execution-trail.jsonl` — §D |
| ongkos asumsi warisan (5,5 bps fee + 4,5 bps spread/sisi) | `ADA-TAPI` | **20 bps** round-trip dari korpus rujukan; sejak **P10 28 Sep** ia bukan default lagi — semua jalur uji menarik 59 bps dari `tools/costs.py` (§D) |
| slip dari kedalaman pool untuk ukuran keluar | `ADA-TAPI` | `exit-size <= 1 % liq` ([[01-Agent/01 - Asset Classes and Seats]] §3) — model kurva, belum diuji pada arus orang lain |

## Uji di Fabius

Yang sudah terjadi: tiga putaran nyata di chain 97 menutup rata-rata **−59,0 bps** (§F) dan itu
**bukan** sinyal, itu ongkos — persis seperti yang dicatat [[Concepts/Cost Is Fixed]]. Yang masih
harus dipisah: **fee** (30 bps, diketahui) vs **dampak harga** (kurva pada ukuran kita) vs
**adverse selection** (belum terukur sama sekali, karena pool kami tidak punya arus luar — kalau
kita sendiri yang membeli dan menjual, tidak ada pihak ketiga yang bisa tahu lebih dulu dari kita).
Uji adverse selection yang sungguhan butuh order masuk dari orang lain; perintahnya belum ditulis
dan bukan pekerjaan minggu hackathon. Ambang yang berlaku untuk semua aturan di atasnya: gross harus
di atas **59 bps** (§D) sebelum kata "edge" boleh dipakai.

## Batas dan mode gagal

- **Memakai 20 bps sebagai ongkos** setelah punya 59 bps terukur = menguji strategi pada biaya yang
  tidak ada. Setiap angka yang digabung dengan 20 bps wajib menyebut rasionya (§D; P10 ditutup 28 Sep).
- **Adverse selection tidak terlihat sebagai tagihan.** Ia muncul sebagai "kenapa harga bergerak
  setelah aku masuk", dan tidak ada kolom di data kita yang mencatatnya — jadi ia cenderung
  diasumsikan nol. Asumsi nol pada komponen yang tidak diukur adalah cara klasik hasil terlihat
  bersih ([[Concepts/Unmeasured Is Not Clean]]).
- **Istilah `maker` sudah terpakai di repo ini** dengan arti lain: di aliran ⑦ `maker` = dompet
  pencetak transaksi ([[03-Data/D2 - Wallet Flow]]), bukan penyedia kutipan. Dua arti ini tidak boleh
  bertemu dalam satu kalimat.
- **Kolam AMM tidak mengenal queue.** Logika maker/taker (menunggu di antrian) tidak berlaku;
  gantinya adalah dampak harga pada kurva ([[FD3 - Likuiditas dan Dampak Harga]]).

## Tingkat bukti

`T1` untuk dekomposisi quoted/realized (kerangka standar mikrostruktur, tidak kami reproduksi) ·
`T3` **hanya** untuk satu kalimat: biaya round-trip nyata jalur kami **−59 bps** per putaran
(dibaca dari event `Closed`, §D/§F — jalankan ulang perintahnya sebelum dikutip) · sisanya:
*(belum diukur)*.

## Boleh dibaca, dilarang dibaca

- **Boleh:** "ongkos nyata jalur eksekusi kami 59 bps round-trip; aturan dengan gross di bawah itu
  rugi meski arahnya benar — dan itu sudah terjadi di uji arah (12/12 rugi, §F)."
- **Dilarang:** "adverse selection kami nol" (tidak terukur) · memakai 20 bps sebagai biaya tanpa
  menyebut 59 bps · menyebut kerugian jalur nyata sebagai bukti sinyal buruk (itu ongkos, bukan
  sinyal) · mengklaim bisa membaca spread (tidak ada L2).

**Terkait:** [[V4 - Order Book dan Liquidity Heatmap]] · [[V3 - CVD Delta dan Footprint]] ·
[[FD4 - Ongkos Perdagangan]] · [[FD3 - Likuiditas dan Dampak Harga]] · [[QT7 - Market Making]] ·
[[QT10 - Eksekusi Algoritmik]] · [[Concepts/Cost Is Fixed]]

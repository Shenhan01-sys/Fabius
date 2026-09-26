---
type: pra-registrasi
ditulis: 2026-09-27T01:3xZ — SEBELUM satu angka hasil pun dilihat
status: terkunci (amend hanya lewat entri baru di 06-Keputusan.md)
---

# 11 — Uji horison whale: apakah "mereka main swing, bukan scalping" benar?

## Pemicunya

Builder (27 Sep): *"whale winrate 69% lalu km cek jam-per-jam ternyata rugi, mungkin bisa jadi beda
timeframe… whale jarang/hampir tidak pernah scalping, pasti swing atau lebih tinggi."*

Ini kritik yang valid terhadap `vault/09` §4c, dan bagian pentingnya harus diakui lebih dulu: uji
sebelumnya **memang** hanya mengukur horizon 4 jam. Kalau memang whale menahan posisi berhari-hari,
maka angka −10,4 bps bukan jawaban atas pertanyaan mereka — itu jawaban atas pertanyaan lain.

Tapi itu bukan alasan untuk langsung setuju. Ada dua penjelasan lain yang menghasilkan data persis
sama: (a) whale benar-benar tidak punya informasi; (b) informasi mereka ada tapi habis oleh ongkos
di semua horizon. Uji ini dirancang untuk membedakan, bukan untuk membenarkan.

## Dua uji, bukan satu

| | **Uji A — PROSPEKTIF (bersih)** | **Uji B — BATAS ATAS (ramah ke panel)** |
|---|---|---|
| keanggotaan panel | dompet yang muncul di `wallet-flow.jsonl` **sebelum** transaksinya dinilai | daftar dompet hasil rekaman hari ini, dipakai menilai transaksi 90 hari ke belakang |
| sumber entri | arus live kami sendiri (mulai 26 Sep 08:01Z) | Dune `dex.trades` |
| horizon | 24 jam, 48 jam | 24 jam, 48 jam, 7 hari, 30 hari |
| bisa selesai sebelum tenggat? | ya, mulai 27 Sep 08:01Z (24 jam) | ya |
| lookahead | **tidak ada** | **ada, dan tidak bisa dibuang** — dompet boleh dilabeli pintar justru karena sejarah yang diuji |

Verdik yang diizinkan: kalau Uji B positif sementara Uji A nol, **kesimpulannya lookahead, bukan
alpha**. Uji A yang menentukan.

## Definisi yang dipakai (tidak boleh diubah setelah hasil keluar)

- **baseline = "token & hari acak"**, bukan nol. Untuk tiap (token, hari) di universe yang sama,
  hitung forward return long-horizon-h dari bar 1 jam pertama hari itu; rata-ratakan **setara bobot**
  (satu token-satu hari = satu suara). Ini menjawab pertanyaan sebenarnya: apakah pilihan whale
  lebih baik dari pilihan acak, bukan apakah mereka untung.
- **masuk** = open bar 1 jam berikutnya setelah waktu entri (tidak memakai harga yang sama dengan
  keputusan dibuat).
- **net = gross − ongkos round-trip nyata per venue**, bukan 20 bps sebagai asumsi. Ongkos
  (gas swap + fee + spread di ukuran yang kita pakai) dihitung terpisah dan dilaporkan duluan,
  karena dia menentukan angka berapa pun yang boleh disebut "untung".
- **1 sampel per (wallet, token, hari)** — order berulang di hari yang sama tidak dihitung dua kali.
- **n ≥ 20** per wallet; **Benjamini–Hochberg α = 0,10** lintas wallet **dan** lintas horizon
  (horizon ganda = tes ganda; ini yang paling gampang selundup).
- **Belah sampel**: periode awal vs periode akhir, tidak tumpang tindih. Klaim "hasil" hanya kalau
  **berarah sama di keduanya**. Kalau hanya satu, itu ditulis sebagai cerita.
- **Setelah fold terbaik dibuang**, rata-rata harus tetap > 0.

## Yang TIDAK diuji di sini (dan tidak boleh disiratkan oleh kalimat apa pun)

1. **Survivorship.** Yang bisa kami hargai sendiri cuma token yang **punya kontrak perp di Aster** —
   yaitu token yang sudah selamat. Untuk horizon 30 hari ini bukan detail: kita menguji "whale di
   token yang masih hidup", dan tidak akan pernah melihat yang mati di tengah jalan.
2. **Sisi short.** Kerumunan di Dune adalah pembeli token spot. Kami tidak mengukur kemampuan
   memilih arah turun.
3. **Kelompok kontrol "bukan whale".** Masih tidak tersedia (0 dari 607 rekaman tanpa label panel);
   pembandangnya baseline acak di atas, bukan trader biasa.
4. **Ukuran ekonomi.** Uji ini menjawab "ada sinyal atau tidak", bukan "layak dijalankan dengan
   $5/hari". Itu keputusan terpisah dan butuh angka ongkos yang belum kita punya.

## Konsekuensi yang sudah disepakati di muka

- Kalau **semua horizon nol** → dugaan builder terjawab salah, dan itu tetap masuk submission
  (dengan angka, bukan nada). Registry tetap kosong; tidak ada real-trade.
- Kalau **B positif, A nol** → ditulis sebagai artefak lookahead. Bukan hasil. Tidak ada real-trade.
- Kalau **A positif di 24/48 jam dan ongkos nyata tertangani** → baru kita bicara eksekusi nyata,
  di testnet dulu, dengan pagar expectancy (bukan win-rate), dan plafon kerugian yang kamu tetapkan
  sendiri — bukan yang kunyusun.

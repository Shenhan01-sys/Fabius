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

---

# HASIL — dijalankan 27 Sep, aturan di atas tidak disentuh

Data: 6.741 baris Dune (90 hari; 105 wallet panel dengan n≥20), 20.277 titik ternilai, 129 token
ber-kontrak perp, baseline dihitung dari kline kami sendiri. Artefak: `decisions/whale-sweep-90d.json`.

| horison | n | whale (bps) | acak (bps) | selisih | median | buang 1% teratas → sisanya | dua periode |
|---|---|---|---|---|---|---|---|
| 24 jam | 6.355 | −267,8 | +33,4 | **−301,2** | −37,8 | −384,2 | − / − |
| 48 jam | 6.241 | −363,9 | +56,1 | **−420,1** | −105,3 | −548,6 | − / − |
| 7 hari | 5.394 | −1.418,3 | +164,2 | **−1.582,5** | −451,2 | −1.608,8 | − / − |
| **30 hari** | 2.287 | **+2.521,8** | +804,8 | **+1.717,0** | **+1.289,6** | **+2.163,8** | **+ / +** |

Per wallet pada 7 hari: 75 wallet mencapai n≥20, **0 lolos BH** (rata-rata −1.422 bps).

## Verdik, dengan aturan halaman ini sendiri

1. **Lookahead hanya bisa menaikkan angka whale.** Maka: yang **negatif** (24 jam–7 hari) kuat —
   bahkan dengan bonus struktural pun panel tetap kalah dari acak. Yang **positif** (30 hari)
   belum berarti apa-apa: itu persis bentuk angka yang dihasilkan "dompet yang jadi terkenal karena
   30 hari yang bagus".
2. Dugaan builder **benar soal horison**, dan itu terukur: kalau kami berhenti di 24 jam–7 hari,
   kesimpulannya akan berbunyi "whale tidak tahu apa-apa". Pada 30 hari arahnya berbalik. Yang
   membuat perbedaan ini terlihat bukan model yang lebih pintar, melainkan **baseline acak** —
   tanpanya "+2.521 bps" akan langsung terbaca sebagai penemuan, padahal itu angka mentah tanpa
   pembanding.
3. Versi bersihnya (Uji A) butuh 30 hari data prospektif → hasil ±26 Okt, tiga minggu setelah
   tenggat. **Kami tidak akan menyiasati tidak adanya data itu dengan memakai data yang tercemar.**

## Kalimat yang boleh / tidak boleh masuk submission

> **Boleh:** "Satu horison (30 hari) tempat dompet smart-money mengalahkan baseline acak secara
> konsisten (median +1.290 bps; +2.164 bps setelah 1% entri terbaik dibuang; dua periode searah).
> Kami tidak menjualnya sebagai edge: panel kami dipilih oleh label yang diberikan SETELAH sejarah
> itu terjadi, dan koreksi satu-arah itu membuat angka positif di horison ini tidak bisa dibedakan
> dari artefak seleksi. Uji bersihnya terjadwal setelah hackathon. Pada horison yang kami sendiri
> gunakan (4 jam–7 hari), whale justru kalah dari acak — termasuk pada pengukuran yang menguntungkan
> mereka."
>
> **Tidak boleh:** "whale profitable", "ada edge di 30 hari", "sinyal whale", atau menampilkan baris
> 30 hari tanpa baris 24 jam–7 hari di sebelahnya.

## Tiga bug pengukuran yang ketahuan SEBELUM hasilnya dipakai

1. `from_hex('0x…')` di Trino **tidak melempar error** — hanya tidak pernah cocok. Kueri pertama
   membalas 0 baris dan terbaca seperti "whale tidak trading". Solusi: normalisasi heks + assert
   panjang 40 di sumbernya.
2. Paginasi: API ini **tidak mengirim `next_offset`**; kueri berhenti di halaman pertama → sampel
   1.000 dari 6.741 (6,7×) dan tabelnya tetap tercetak rapi. Sekarang offset digeser manual dan
   berhenti hanya pada `total_row_count`.
3. Split-sample dibelah lewat **indeks** pada daftar baseline yang tersusun per kontrak, bukan per
   tanggal — kolom "AWAL/AKHIR" saat itu tidak mengukur yang dijanjikan halaman ini. Diperbaiki
   (dibelah menurut tanggal); verdiknya tidak berubah, dan itu dicatat bukan karena kesalahannya
   tidak penting, tapi karena kebetulan tidak mengubah arah.

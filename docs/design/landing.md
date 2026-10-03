# Landing page Fabius: design brief (3 Okt 2026)

Kontrak untuk kode `web/`. Kode mengikuti brief; brief berubah dulu sebelum kodenya berubah.

## Proses yang diwakili (riset domain: sistem kita sendiri, bukan aplikasi lain)

```
bar harian tutup 00:00Z -> bot menghitung niat posisi (tick) -> sinyal disegel jadi akar Merkle -> akar dikomit ke SignalAnchor (jam blok)
-> isi sinyal dibuka (reveal) -> siapa pun menghitung ulang (verify_signals: SAH) -> bar berikutnya menutup hasil (settle) -> rekam jejak maju tumbuh
```

Objek inti: **blok kaca**. Satu blok = satu sinyal. Kubus kaca = agen Fabius = kristal komitmen.
Tiga keadaan blok mengikuti tiga warna referensi kubus:

| keadaan | warna blok | arti |
|---|---|---|
| kosong | kaca bening berkabut | slot rekam jejak yang belum terisi (masa depan) |
| tersegel | indigo pekat | sinyal sudah dikomit di chain, isi belum dibuka |
| terbuka + SAH | putih-violet bercahaya | sinyal dibuka dan dihitung ulang cocok dengan komitnya |

**Data dalam geometri:** jumlah blok bercahaya = jumlah sinyal yang SAH di chain (dari snapshot). Hari ini hampir semua blok masih kosong,
dan itu memang beritanya: rekam jejak baru mulai 1 Okt 2026.

## Batas kejujuran (dari keputusan, bukan selera)

- Tingkat 0 "umpan bukti" (komit + pembukaan + rekam jejak paper) = TERBUKA, gratis (F-D72).
- Tingkat 1 sinyal waktu-nyata berbayar = TERKUNCI sampai bot lolos F-D16 maju DAN telaah hukum (P80). Ditampilkan sebagai pintu terkunci
  dengan syarat pembuka yang terukur, bukan sebagai produk yang bisa dibeli.
- Tidak ada klaim keuntungan, tidak ada angka kinerja yang belum bermakna. Semua angka berasal dari snapshot yang dicetak skrip
  (`tools/web_snapshot.py`) dari ledger + chain, dengan cap waktu.

## Sistem visual (Glass / Soft-depth, satu baris Aesthetic Palette)

- Permukaan: lavender pucat (hero, terang) lalu indigo malam (bagian bukti). Satu bingkai membulat seperti panel kaca.
- Warna: lavender `#ECE8FA`, indigo `#120E2E`, violet aksen `#6E4BFF`, kaca putih. Tidak ada warna keempat kecuali merah untuk "gap".
- Tipe: display Archivo (lebar variabel; tipis + tebal miring dipadukan), body Inter, angka/hash JetBrains Mono.
- Kedalaman: kaca (blur + sorot tepi tipis) di semua panel. Tidak ada bayangan keras.
- Motif: penanda bernomor `01 —` di tiap bagian + blok kaca kecil sebagai penanda.
- Gerak: masuk (blok terbang lalu mengunci), terus-menerus (kubus bernapas, blok sesekali membuka), interaksi (kubus condong ke kursor).

## Bagian

1. **Hero, "Kristal".** Kubus kaca 3x3x3 (3D). Saat dimuat, blok terbang dari sebaran lalu mengunci (komit). Sesudahnya kubus berputar pelan,
   sesekali satu blok keluar, berubah bercahaya, lalu kembali (reveal). Judul raksasa: "SIGNALS / SEALED / BEFORE THE OUTCOME". Strip hidup: komit
   terakhir, blok, akar. Lencana berputar "VERIFY · NO KEY · NO GAS" membuka perintah pemeriksa.
2. **01 — Satu sinyal, dari tutup bar sampai terbukti.** Sumbu waktu horizontal (00:00Z -> +menit komit -> buka -> +1 hari settle). Satu blok
   berjalan di sumbu dan berubah keadaan di tiap stasiun. Bukan grid kartu.
3. **02 — Rekam jejak maju.** Kalender hari sejak genesis x bot. Tiap sel = keping kaca dengan keadaan (tick, tersegel, terbuka, settle); hari bolong
   tampil sebagai sel retak "tak terukur, bukan nol". Tiga tangki F-D16 (sinyal x/20, hari x/20, bulan x/2) terisi sesuai data.
4. **03 — Buku slot.** 10 slot sebagai rak; B1 menghuni (identitas), B3 mengorbit sebagai penantang dengan cincin bayangan 2/60 hari, empat spesifikasi
   lain redup di luar. Rantai kunci on-chain (8 kunci) sebagai deret gembok bercap waktu.
5. **04 — Dua pintu.** Manusia: umpan bukti sekarang, daftar tunggu sinyal waktu-nyata. Agen: MCP + x402 (konfigurasi ditampilkan). Pintu tingkat 1
   tertutup dengan cincin syarat yang terisi sesuai data.
6. **Yang tidak kami klaim.** Marquee: PAPER ONLY · NO EDGE CLAIMED · F-D16 NOT MET · VERIFY, DON'T TRUST.
7. **Kaki.** Alamat kontrak, perintah pemeriksa, repo.

## Teknis

Next.js (App Router) + TypeScript + Tailwind, three.js lewat @react-three/fiber + drei (kaca: MeshPhysicalMaterial transmisi, lingkungan dari
Lightformer lokal tanpa unduhan HDR), motion untuk gerak DOM. Kanvas 3D hanya di klien (`dynamic`, `ssr: false`). Data dari
`web/public/data/snapshot.json`. Bahasa: EN + ID (tombol di nav).

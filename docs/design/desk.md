# /desk - lantai trading: design brief (5 Okt 2026, P158)

Kontrak untuk `web/src/components/desk/floor/`. Kode mengikuti brief; brief berubah dulu sebelum kodenya berubah.
Menggantikan daftar "Decisions, newest first" (rekaman mentah: jam, nama, teks, hash penuh).

## Proses yang diwakili

```
tiap 5 menit: tiga agent AI membaca data -> masing-masing memutuskan (bot + instrumen + ukuran, atau tahan) -> rumus terkunci menggabungkan
jadi putusan Fabius -> semua keputusan disegel jadi satu Merkle root -> root dikomit ke DeskAnchor (BNB testnet) sebelum siklus berakhir
```

Objek inti: **meja kerja trader**. Satu agent = satu orang (NPC kotak-kotak gaya Minecraft) yang duduk di mejanya dengan monitor + keyboard,
benar-benar "sedang trading". Putusan Fabius = **hub** bercincin di tengah lantai; segel + komit = **menara blok** BNB Chain di belakang hub.
Garis cahaya di lantai menyambung tiap meja ke hub (keputusan mengalir ke rumus) dan hub ke menara (komit).

## Data dalam geometri dan gerak (bukan hiasan)

| benda | arti (dari `/desk` + `/desk/agent/<nama>`) |
|---|---|
| NPC mengetik cepat + monitor berkedip + gelembung `▲ BTC ▲ ETH` | siklus terakhir agent itu ada transaksi (isi > 0) |
| NPC bersandar + gelembung `■ hold` | jawaban sah, posisi ditahan (isi = 0, masih berposisi) |
| NPC santai + gelembung `■ flat · waiting` | jawaban sah, tanpa posisi |
| NPC kepala di meja + gelembung `✕ failed` | rekaman terakhir `gagal` / `terlambat` |
| NPC mengetik pelan + gelembung `…` | siklus baru sedang berjalan (lebih dari 5 menit sejak siklus terakhir tercatat) |
| layar monitor | kurva ekuitas 24 jam agent itu + ekuitas + hasil % |
| layar hub | bot dominan v2 + instrumen (v1: "konsensus") |
| 12 blok menara | 12 siklus terakhir; menyala = dikomit, pucat = tidak dikomit |
| denyut cahaya di garis lantai | siklus baru masuk: meja -> hub -> menara (satu kali per siklus) |

## Sistem visual (Fabius Glass / Soft-depth + referensi diorama clay isometrik)

- Referensi (`References/Section-Decisions, newest first/`): diorama isometrik putih matte, slab membulat, bayangan kontak lembut, garis
  cahaya aksen yang menyambung ke hub bercincin. Diambil **tingkat kehalusan + bahasa bentuknya**, bukan tata letaknya.
- Warna = token Fabius saja: lantai/clay putih + `lav #ece8fa` / `lav-2 #ddd5f6`, aksen cahaya `violet #6e4bff` / `violet-2 #9d86ff`, layar
  + bezel `ink #15122b`, garis/bayangan `mist #8b86a6`, merah `gap #ff5a6e` hanya untuk gagal. Aksen oranye/biru referensi diganti violet.
- NPC: kubus (kepala 8x8 piksel wajah, badan, lengan, kaki) - kaus per agent dari keluarga violet/ink, aksesori pembeda (headset, topi,
  koran) supaya tidak bergantung warna.
- Kamera ortografis isometrik TETAP: tanpa zoom, tanpa orbit; zoom dihitung dari lebar kontainer supaya seluruh diorama selalu masuk satu
  bingkai (di HP ikut mengecil). Paralaks kursor halus +-2 derajat saja.

## Interaksi

- Klik / Enter pada meja agent -> **modal keluar dari monitor agent itu** (berangkat dari kotak layar monitor yang diproyeksikan, membesar ke
  tengah); tutup = kembali masuk ke monitor. Esc menutup, fokus terkunci di modal.
- Isi modal: identitas (nama, model, agent ERC-8004), buku v2 / v1 (tab), statistik terukur 24 jam (ekuitas, hasil %, transaksi, fee, siklus
  sah / gagal / terlambat, siklus dengan transaksi, pilihan bot v2), posisi sekarang, kurva ekuitas, riwayat keputusan (jam, aksi bahasa awam,
  isi + harga + fee, status, tautan bukti Merkle `/desk/proof/<hash>`).
- Klik hub -> modal yang sama untuk buku Fabius (v2, tab v1 konsensus selama berdampingan).

## Inklusif (wajib)

- Arti tidak pernah hanya lewat warna: selalu bentuk + kata (`▲ beli`, `▼ jual`, `■ tahan`, `✕ gagal`).
- Pita keterangan di bawah adegan dalam bahasa awam, ikut toggle EN/ID, dibacakan pembaca layar (`aria-live="polite"`).
- Tiap meja + hub = tombol yang bisa difokus keyboard (label HTML di atas adegan), `aria-label` "Open <agent> stats".
- Tombol "View as list" -> daftar teks yang sama isinya (juga otomatis bila WebGL tidak ada).
- `prefers-reduced-motion`: tanpa idle, tanpa denyut, tanpa animasi modal (muncul langsung).
- Kanvas berhenti render di luar layar / tab tersembunyi.

## Ukuran

Satu adegan utuh di dalam bagian "Decisions", lebar = kontainer `max-w-6xl`, tinggi `clamp(340px, 52vw, 560px)`. Tidak ada scroll di dalam
adegan; modal maksimal 92 % kontainer, isinya boleh scroll.

## Fabius Live Book (P164, 6 Okt) - menggantikan panel "Fabius v2"

Judul disetujui builder: **"Fabius Live Book"** / ID **"Buku Hidup Fabius"**, tagline *Real decisions · paper money · every cycle sealed on BNB
Chain* (bukan "real trade": uangnya paper; keputusan + buktinya yang nyata).

Proses yang diwakili: satu siklus pipeline = agent memberi keputusan -> rumus r3 menggabung -> aturan bot terkunci menghitung arah -> buku Fabius
diisi -> root disegel ke DeskAnchor. Objek inti: **jalur produksi** (beda metafora dari lantai): platform-platform tersambung garis cahaya violet,
seperti referensi.

- **Strip pipeline 3D (atas):** (1) platform agent = NPC pekerja yang SAMA dengan lantai, pose BERDIRI, satu per kursi aktif, tanda ✓/✕ per jawaban;
  (2) **mesin rumus** = inti kubus kaca dengan cincin berputar + layar "r3" + bot pemenang + selisih skor (sebagus NPC: bentuk + gerak bermakna);
  (3) **bot** = robot kotak bermata cahaya membawa ID bot di dadanya, lengannya menunjuk arah; (4) **buku** = batang posisi (tinggi = bobot, ▲ violet /
  ▼ ink); (5) **chain** = tumpukan blok + ✓. Titik cahaya mengalir dari kiri ke kanan tiap siklus baru. Label = tombol DOM (bridge), ringkasan
  `aria-live`, tanpa gerak bila `prefers-reduced-motion`, versi 2D bila tanpa WebGL.
- **Kurva ekuitas sejak awal** + **pita bot** di bawahnya (warna/label per bot, sumbu waktu sama) + statistik jujur: ekuitas, hasil, drawdown maks,
  fee (dan porsinya terhadap rugi), transaksi, siklus berposisi.
- **Hasil per bot** (siklus dominan, perubahan ekuitas saat bot itu memegang, fee) + **pita keputusan** terbaru dulu (bot, agent sah, isi, bukti ↗).
- Data: `GET /desk/fabius` (semua rekaman buku Fabius sejak siklus pertama).

## Panel slot posisi (r4, F-D116)

Sejak rumus r4 buku Fabius memegang maksimal 5 posisi. Panel baris penuh di bawah kurva: tiap slot = kartu (aset + arah, bot pemilik dengan
warna pita bot, margin x leverage, untung/rugi belum direalisasi) dengan batang SL -> masuk -> TP; titik = harga siklus terakhir (ungu bila
untung, tinta bila rugi), masuk di 1/3 karena TP = 2 x jarak SL. Slot kosong digambar putus-putus supaya kapasitas terlihat. 5 kolom di
desktop lebar, 2 di tablet, 1 di HP. Pita keputusan menulis alasan tiap isi (buka / stop-loss / take-profit / aturan keluar bot / rem rugi).

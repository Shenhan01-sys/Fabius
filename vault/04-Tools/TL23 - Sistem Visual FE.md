---
tags: [perkakas, "TL23", fe, desain]
---

# TL23 - Sistem Visual FE (pedoman semua halaman web/)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** brief per halaman `docs/design/*.md` (kontrak: brief berubah dulu, kode mengikuti) · token `web/src/app/globals.css` · komponen
`web/src/components/` · teks `web/src/lib/copy.ts` · pedoman universal builder: FE Doctrine (`~/FE-Universal-Guide/FE-UNIVERSAL-GUIDE.md`)

## Prompt asal (builder, 3 Okt 2026) - dipakai sebagai acuan untuk SEMUA halaman berikutnya

> *"Kalau begitu saatnya kita mulai bikin FEnya untuk user yg mau beli atau langganan sinyal Fabius, bebas mau itu org asli atau agent, kita akan bikin
> mcpnya juga. Gas mulai dari landing page, nah disini saya memiliki referensi ini "https://awsmd.com/" dan ini
> "...\Fabius\References\850fef6eeae8d5de61840c171e30aa1b.jpg". Lalu nanti Agent fabius memiliki bentukan 3D dan texture seperti ini lengkap dengan
> animasi statisnya "...\Fabius\References\b550fcf2a41fc637720e1cbb4b0b85a9.jpg""*

Builder 4 Okt: *"Gas, UI dan FE stylenya disamakan yak"* + *"Pakai referensi prompt ini yg saya pakai untuk membangun landing page, catat knowledgenya
di vault"* -> halaman ini.

| referensi | apa yang DIAMBIL | apa yang TIDAK diambil |
|---|---|---|
| **awsmd.com** | tipografi raksasa sebagai komposisi (judul memenuhi lebar), tipis + tebal miring dipadukan, ritme section besar bernomor, gerak saat scroll | warna dan konten studio |
| **`References/850fef6e…jpg`** (halaman web3 ungu-gelap) | pergeseran terang -> malam (lavender ke indigo), panel kaca, satu aksen violet, kartu gelap berpendar halus | gaya "kripto mewah" yang menjanjikan untung |
| **`References/b550fcf2…jpg`** (kubus voxel kaca) | **bentuk agen Fabius = kubus kaca 3x3x3** dengan tekstur kaca bening/indigo/putih bercahaya + animasi statis (bernapas, satu blok keluar-masuk) | - |

Berkas `References/` milik builder: tidak di-commit (tetap untracked).

## Sistem (Glass / Soft-depth; satu baris Aesthetic Palette FE Doctrine)

- **Metode FE Doctrine (wajib):** riset proses nyata -> temukan OBJEK fisik tiap langkah -> wakili di ruang dengan gerak yang punya maksud -> data
  dikodekan dalam geometri. Halaman MEWAKILI proses, bukan menjelaskannya dengan grid kartu.
- **Objek inti:** blok kaca = satu sinyal / satu komitmen. Kubus = agen = kristal komitmen.
- **Keadaan blok (satu bahasa di 3D dan `IsoCube` SVG):** kosong (kaca bening berkabut) · sebelum kunci (lavender + gembok) · menunggu (violet putus-putus,
  bernapas) · tersegel (indigo pekat) · terbuka + SAH (putih-violet bercahaya) · bolong/terlewat (merah retak). Merah HANYA untuk bolong/alarm.
- **Token warna** (`globals.css @theme`): `lav #ece8fa`, `lav-2 #ddd5f6`, `lav-3 #c9bdf2`, `ink #15122b`, `night #0f0b26`, `night-2 #1a1442`,
  `violet #6e4bff`, `violet-2 #9d86ff`, `mist #8b86a6`, `gap #ff5a6e`; latar halaman `#f6f4fd`. Tidak ada warna keempat.
- **Tipe:** display Archivo (sumbu lebar `fontStretch` 75-125 %; judul tipis `font-[300]` besar `clamp(2.4rem,5.6vw,5rem)` + kata tebal miring),
  body Inter, angka/hash/perintah JetBrains Mono (`.tag` untuk label huruf besar berjarak).
- **Kedalaman:** `.glass` (terang) dan `.glass-dark` (malam) di semua panel; sudut membulat 26-30 px; tidak ada bayangan keras.
- **Motif:** label section `NN — Judul` (`.tag text-violet`); blok kaca kecil sebagai penanda daftar; marquee klaim yang TIDAK kami buat.
- **Gerak (motion):** masuk = muncul + pegas saat masuk layar (`whileInView`, `once`); terus-menerus = bernapas pelan; tidak ada gerak tanpa maksud.
  Kanvas 3D berhenti me-render di luar layar.
- **Nav bersama:** kapsul kaca kiri (logo kubus), tautan tengah, tombol EN/ID + CTA gelap kanan. Semua teks EN + ID di `copy.ts`.

## Batas kejujuran (dari keputusan, bukan selera)

Tingkat 0 bukti = terbuka, gratis; tingkat 1 = TERKUNCI sampai F-D16 maju + telaah hukum (F-D72). Tidak ada klaim keuntungan. Angka hanya dari snapshot
(`tools/web_snapshot.py`) atau bacaan live dengan semantik T8 (gagal baca = galat yang terlihat, bukan nol/kosong).

## Revisi yang sudah terjadi (jangan diulang)

- Glow kristal terlalu terang (builder: "turunin glownya") -> emisi, lampu dalam, bloom, pantulan diturunkan (TL19).
- `ContactShadows` ikut berputar dan tampil sebagai pita abu-abu -> bayangan lantai = elips CSS di atas kanvas.
- Emoji dan warna di luar palet (hijau zamrud, gembok emoji) -> gembok SVG violet; tanpa emoji di UI.
- `.gitignore` akar repo pernah menelan berkas FE (`data/`, `lib/`) -> build dari clone bersih sebelum menyatakan siap deploy.
- Deploy: hanya lewat push GitHub (Vercel), tidak pernah `vercel deploy` dari akar repo (F-D89).
- Cek visual: Chrome headless dengan `--virtual-time-budget` TIDAK menjalankan animasi `motion` (elemen tetap `opacity: 0`; 4 Okt) - pakai peramban waktu-nyata (stealth-browser / CDP) untuk tangkapan layar; item grid berisi `pre` panjang butuh `min-w-0` agar tidak melebar di ponsel.

## Daftar periksa halaman baru

1. Brief `docs/design/<halaman>.md` ditulis dulu: proses yang diwakili, objek fisiknya, keadaan, data dalam geometri, batas kejujuran.
2. Pakai `Nav`, `LangProvider`, `.glass`/`.glass-dark`, `IsoCube`, token warna, tipe di atas; label `NN —`; EN + ID di `copy.ts`.
3. Data dari snapshot atau API server (tanpa kunci di Vercel); gagal baca tampil sebagai galat.
4. Lebar ponsel tanpa gulir horizontal halaman (tabel lebar di dalam panel bergulir sendiri).
5. `npm run build` + `npm run lint` bersih; untuk deploy: build dari clone bersih.

**Halaman:** landing `/` ([[TL19 - web landing]]) · MCP `/mcp` ([[TL20 - server MCP]]) · `/verify` (4 Okt, `docs/design/verify.md`)

**Terkait:** [[TL19 - web landing]] · [[TL20 - server MCP]] · [[08-Backlog/01 - Backlog]] P113 / P124

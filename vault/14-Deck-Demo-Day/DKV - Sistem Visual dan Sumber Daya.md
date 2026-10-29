---
tags: [deck, "DKV"]
---

# DKV - Sistem Visual dan Sumber Daya

**Bagian dari:** [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]] · brief: [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]]
**Sumber:** kontrak desain FE `docs/design/landing.md` (+ `verify.md`, `desk.md`, `bot.md`, `status.md`) · `web/src/app/globals.css` (token) · `web/src/app/layout.tsx` (font) · `web/src/components/ui/IsoCube.tsx`, `hero/Hero.tsx`, `hero/Crystal.tsx`, `sections/Closing.tsx`, `Nav.tsx`, `break/BreakView.tsx`, `tour/TourView.tsx` · tangkapan layar produksi `fabius-one.vercel.app` 29 Okt (1920×1080 @2x) · keputusan builder 29 Okt: *"Keknya bagus terang ga sih kayak landing page fabius?"*

**Ringkas:** Deck memakai **bahasa visual yang sama dengan FE Fabius** — lavender terang, kaca (glass/soft-depth), satu aksen violet, merah hanya untuk "bolong/ditolak", tipografi Archivo lebar-variabel — supaya juri yang memindai QR melihat produk yang sama dengan slide. Halaman ini memberi token persis, skala tipe, komponen, aset siap pakai di `vault/14-Deck-Demo-Day/aset/`, peta latar per slide, dan cara membuat ulang aset. Bila halaman ini bertentangan dengan arah warna di versi awal DK0–DK6, **halaman ini yang berlaku**.

**Poin kunci:**
- Kanvas 16:9 1920×1080; latar halaman `#F6F4FD`; isi di **panel membulat radius 30 px** dengan jarak tepi 12–16 px — persis tata letak FE (`p-2 sm:p-3`, `rounded-[30px]`).
- Panel **lavender** (`#ECE8FA` → putih) untuk DK2–DK6; panel **night** (`#0F0B26`) hanya untuk DK1 (masalah) dan sebagai blok aksen (kartu "Verified", saklar DK5, pita contoh perintah) — sama seperti FE memakai night untuk footer dan panel vonis.
- Satu aksen `#6E4BFF`; merah `#FF5A6E` hanya untuk ditolak/bolong. Tidak ada warna keempat.
- Aset siap: 10 tangkapan layar produksi, 10 SVG kubus semua keadaan, wordmark SVG, potongan kristal hero.

**Detail:**

## 1. Prinsip (dari `docs/design/landing.md`)
1. **Objek inti = blok kaca.** Satu blok = satu sinyal; kubus kaca = agen Fabius. Keadaan blok = warna (tabel §5).
2. **Glass / soft-depth.** Kedalaman dari kaca (blur + sorot tepi tipis), **tanpa bayangan keras**.
3. **Data dalam geometri.** Bila memungkinkan, angka ditampilkan sebagai blok/stasiun, bukan paragraf.
4. **Kejujuran terlihat.** Yang bolong ditampilkan bolong (merah putus-putus), bukan disembunyikan.
5. **Satu gagasan per panel**; penanda bernomor `01 —` gaya tag mono.

## 2. Token warna (persis `globals.css`)

| Token FE | Hex | Pakai di deck |
|---|---|---|
| `--color-lav` | `#ECE8FA` | panel utama (atas gradasi) |
| `--color-lav-2` | `#DDD5F6` | permukaan sekunder, garis halus |
| `--color-lav-3` | `#C9BDF2` | garis rel, tepi kartu non-aktif |
| `--color-ink` | `#15122B` | teks utama di panel terang, tombol gelap |
| `--color-night` | `#0F0B26` | panel gelap (DK1, kartu Verified, saklar) |
| `--color-night-2` | `#1A1442` | kartu di atas night |
| `--color-violet` | `#6E4BFF` | aksen tunggal, kata kunci miring, tombol utama, glow |
| `--color-violet-2` | `#9D86FF` | aksen di atas night, label mono |
| `--color-mist` | `#8B86A6` | teks sekunder, kata yang "dipudarkan" (*what* di DK6) |
| `--color-gap` | `#FF5A6E` | ditolak / bolong / antagonis — **hanya** itu |
| latar halaman | `#F6F4FD` | latar slide di luar panel |
| teks isi | ink 65 % (`#15122B` α 0,65) | paragraf isi (FE: `text-ink/65`) |

Gradasi panel terang (FE `bg-gradient-to-b from-lav via-lav to-white`): atas `#ECE8FA` → 60 % `#ECE8FA` → bawah `#FFFFFF`.

## 3. Tipografi (persis FE)

Font (Google Fonts, gratis): **Archivo** variable dengan sumbu lebar `wdth` 62–125 + italic (https://fonts.google.com/specimen/Archivo), **Inter** (https://fonts.google.com/specimen/Inter), **JetBrains Mono** (https://fonts.google.com/specimen/JetBrains+Mono). Pasang di mesin pembuat **dan** embed di PPTX (atau sediakan PDF/MP4 cadangan).

| Peran | Spesifikasi FE | Ukuran di slide 1920×1080 |
|---|---|---|
| Judul baris 1 (pernyataan) | Archivo weight **300**, `font-stretch` **112 %**, tracking −0,035 em, line-height 0,9 | 96–130 pt |
| Judul baris 2 (kata kunci) | Archivo weight **800**, **italic**, `font-stretch` **78 %**, warna violet | 96–130 pt |
| Hero raksasa (opsional, DK6) | "SIGNALS" 200 / 125 % · "*SEALED*" 850 italic / 72 % · "BEFORE THE OUTCOME" 800 / 88 % | 120–160 pt |
| Judul kartu | Archivo 600, 28–36 pt, ink | |
| Isi | Inter 400, 22–28 pt, ink 65 % | |
| Tag / penanda | JetBrains Mono, **UPPERCASE**, letter-spacing 0,08 em, 14–16 pt (FE `.tag`), warna violet atau ink 45 % | |
| Hash, alamat, nomor blok, nama revert | JetBrains Mono 14–18 pt | |

Contoh judul FE yang dipakai ulang: `/tour` "One bot. One day. / ***Five on-chain steps.***" · `/break` "Rewrite the record. / ***Watch it fail.***" · `/verify` "Don't trust. / ***Check it.***" (lihat tangkapan §6).

## 4. Komponen

| Komponen | Spesifikasi (dari CSS FE) | Dipakai di |
|---|---|---|
| **Kartu kaca** (`.glass`) | isi gradasi 135° putih α 0,62 → 0,28; tepi 1 px putih α 0,75; sorot dalam 1 px putih α 0,9 di atas; bayangan `0 24px 60px -28px rgba(62,37,160,.35)`; blur 18 px; radius 26 px | kartu DK2, DK4, DK5 |
| **Kartu kaca gelap** (`.glass-dark`) | putih α 0,09 → 0,02; tepi putih α 0,12; bayangan `0 30px 80px -40px rgba(110,75,255,.55)` | kartu di panel night DK1 |
| **Panel** | radius 30 px; terang = gradasi lav→putih; gelap = `#0F0B26` | semua slide |
| **Pil / tombol** | radius penuh; gelap = ink + teks putih; utama = violet + teks putih + bayangan `0 14px 40px -12px rgba(110,75,255,.8)` | label "Live on testnet", URL |
| **Tag bernomor** | mono uppercase "01 —", violet | pojok kiri atas tiap panel |
| **Kubus** (`IsoCube`) | SVG isometrik 3 muka; keadaan §5 | DK2 (3 keadaan), DK4 (sealed di kartu), DK6 (wordmark) |
| **Rel stasiun** | garis horizontal 2 px `#C9BDF2` / violet α 0,25; titik bernomor bulat violet 24 px berisi angka mono putih | DK2, DK3 (meniru `/tour`) |
| **Cap ditolak** | tepi 1,5 px `#FF5A6E`, teks mono merah, radius 10 px, miring −4° | DK4 |
| **Panel vonis "Verified"** | night `#0F0B26`, kubus verified + glow, "Verified" Archivo 800 italic | DK3 caption, DK2 kartu CHECK (opsional) |
| **Pita marquee klaim** | panel violet `#6E4BFF`, teks putih Archivo 800 italic stretch 75 %, 48–64 pt: "PAPER ONLY · NO EDGE CLAIMED · FORWARD TEST NOT YET MET · VERIFY, DON'T TRUST · EVERY RULE LOCKED BEFORE THE DATA" | DK5 (pita bawah, statis atau geser pelan) |
| **Footer kontrak** | panel night, mono kecil putih α 0,7: alamat `SignalAnchor` / `LockRegistry` | DK6 pita bawah |

## 5. Keadaan kubus (makna = warna, jangan ditukar)

| Berkas | Keadaan | Arti | Contoh pakai |
|---|---|---|---|
| `aset/kubus/kubus-sealed.svg` | indigo pekat | sudah disegel di chain, isi belum dibuka | DK2 SEAL, wordmark |
| `aset/kubus/kubus-verified.svg` / `-glow.svg` | putih-violet bercahaya | dibuka + dihitung ulang cocok | DK2 CHECK, DK3 Verified |
| `aset/kubus/kubus-prelock.svg` | lavender + gembok | aturan terkunci / sebelum kunci | DK2 LOCK |
| `aset/kubus/kubus-empty.svg` | kaca bening | slot belum terisi | dekorasi |
| `aset/kubus/kubus-pending.svg` | violet transparan putus-putus | menunggu segel | DK3 sebelum Verified |
| `aset/kubus/kubus-gap.svg` | merah putus-putus + retak | hari bolong (tak terukur, bukan nol) | Q&A / DK5 opsional |
| `aset/kubus/kubus-missed.svg` | merah | terlewat / ditolak | DK4 |
| `aset/kubus/kubus-future.svg`, `kubus-core.svg` | — | masa depan / inti agen | dekorasi |

Semua SVG 400×400, bisa diskalakan tanpa pecah; di PowerPoint: Sisipkan → Gambar (SVG didukung PowerPoint 2019+/365; Keynote: impor lalu jadikan PDF bila perlu).

## 6. Tangkapan layar produksi (29 Okt, 3840×2160)

Folder `vault/14-Deck-Demo-Day/aset/layar/`:

| Berkas | Isi | Saran pakai |
|---|---|---|
| `01-landing-hero.png` | hero "SIGNALS / *SEALED* / BEFORE THE OUTCOME" + kristal 3D | DK6 latar kanan / Q&A |
| `02-tour-atas.png` | judul `/tour` + langkah 1–3 | DK3 cadangan, DK6 di belakang QR |
| `03-tour-langkah-1-3.png` | langkah tutup → segel (tx, cek ✓) → dibuka | DK3 (A3) |
| `04-tour-langkah-4-5-verified.png` | "Anyone re-checks — VERIFIED" + pita marquee + footer night | DK3 caption, DK5 pita |
| `05-break-atas.png` | "Rewrite the record. *Watch it fail.*" | DK4 judul referensi |
| `06-break-empat-ditolak.png` | empat kartu "Rejected by the contract" `TooLate` / `LockedAfterBar` / `NotLocked` / `TooManyReveals` | **DK4** (A4 statis) |
| `07-verify-b2rs-atas.png` | "Don't trust. *Check it.*" + pemilih bot | DK6 / Q&A |
| `08-verify-b2rs-stasiun.png` | daftar 4 sinyal + panel **Verified** night | **DK3** |
| `09-desk.png` | "The AI desk" + Live Book | L1 / Q&A AI Agents |
| `10-bot-b2rs.png` | halaman bot B2-RS + aturan terkunci | L1 / Q&A |
| `aset/kristal-hero-crop.png` | potongan kristal 3D hero (latar lavender) | DK2 / DK6 ilustrasi |
| `aset/wordmark-fabius.svg` | kubus sealed + "Fabius" (Archivo 600, seperti nav FE) | DK1, DK6 |

Pakai tangkapan dalam **bingkai browser** sederhana (bar atas lavender-2, tiga titik, radius 18 px) dengan bayangan kaca §4, sedikit miring (perspektif 4–8°) seperti video v2 — bukan tempelan datar.

## 7. Peta latar per slide

| Slide | Panel | Alasan |
|---|---|---|
| DK1 Kapan ini ditulis | **night** `#0F0B26` penuh, kartu screenshot palsu `glass-dark` | dunia lama yang gelap/keruh — antagonis (video v2 adegan 1 juga gelap) |
| DK2 Kunci Segel Periksa | **lavender** (transisi gelap → terang = momen jawaban; video v2: "So we built the opposite" putih menyapu) | jawaban |
| DK3 Demo | lavender; caption Verified dalam panel night kecil (meniru `/verify`) | produk asli |
| DK4 Coba curangi | lavender, kartu `.glass` + cap merah (meniru `/break` persis) | juri mengenali halaman saat scan |
| DK5 Dibangun untuk diragukan | lavender; saklar OFF dalam kartu night kecil; **pita marquee violet** di bawah | kejujuran = identitas FE |
| DK6 Apa lawan Kapan | lavender lapang + QR di kartu putih; footer kontrak night tipis | tetap tampil selama Q&A |
| L1–L3 | lavender | lampiran |

## 8. Gerak
- Masuk judul: seperti hero FE (kata naik dari bawah, pegas lembut; setara ease-out 350–450 ms, jeda antarkata 140 ms).
- Kartu: fade + naik 12–16 px, 250 ms, stagger 60 ms (FE `delay: i * 0.06`).
- Kubus "bernapas" (opsional, statis lebih aman): skala 1 → 1,06 → 1 dalam 4,8 s.
- Tidak ada efek suara; tidak ada glitch/shake.

## 9. Jangan
- Jangan latar night penuh selain DK1.
- Jangan warna keempat (hijau hanya di kartu screenshot palsu DK1 sebagai "pamer" antagonis).
- Jangan bayangan keras / drop shadow hitam.
- Jangan font lain; jangan mengganti Archivo dengan font "mirip".
- Jangan menempel tangkapan layar tanpa bingkai.

## 10. Membuat ulang aset
- Tangkapan layar (butuh Google Chrome + `playwright-core` di `vault/Video-Workspace/node_modules`): `node vault/14-Deck-Demo-Day/aset/capture-deck.mjs vault/14-Deck-Demo-Day/aset/layar` (dibuka dari root repo Fabius; ±1 menit; termasuk klik "Try all four" di `/break`).
- Kubus: SVG digambar dari `FACES` di `web/src/components/ui/IsoCube.tsx` (viewBox 0 0 100 100, tiga path muka). Bila komponen berubah, ekspor ulang.

**Terkait:** [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]] · [[14-Deck-Demo-Day/DK1 - Slide 1 Kapan Ini Ditulis]] · [[14-Deck-Demo-Day/DK6 - Slide 6 Apa lawan Kapan]]

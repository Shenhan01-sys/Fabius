---
tags: [deck, "DK3"]
---

# DK3 - Slide 3 Demo Beli lalu Periksa

**Bagian dari:** [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]] · brief: [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]]
**Sumber:** [[08-Backlog/13 - Langkah Builder Tertunda]] LB27 (daftar rekam) · [[08-Backlog/01 - Backlog]] P178 (`/tour`), P180/P187 (`/verify` hidup) · `fabius-one.vercel.app/tour` (diuji 29 Okt) · naskah USULAN, menunggu LB25.
**Peta:** sebelumnya [[14-Deck-Demo-Day/DK2 - Slide 2 Kunci Segel Periksa]] · berikutnya [[14-Deck-Demo-Day/DK4 - Slide 4 Coba Curangi]]

**Ringkas:** Slide 3 dari 6 · **0:55–1:35 (40 d, 80 kata)**. Satu klip tertanam yang menunjukkan **pengalaman pembeli** dari ujung ke ujung: minta sinyal di Telegram → bayar per sinyal tanpa gas → dapat sinyal + link → klik → halaman membaca chain → **Verified**, dengan jam segel sebelum batas 12 jam. Slide paling penting untuk kriteria UX + demo.

## 1. Tujuan slide
- Membuktikan bahwa Fabius **hidup dan bisa dipakai orang biasa** (UX: nilai Fabius terlemah di KP9 §8).
- Menunjukkan tiga langkah DK2 terjadi sungguhan pada satu sinyal nyata.
- Menyebut x402 + MCP + testnet dengan jujur dalam satu tarikan napas (kartu AI Agents + BNB).

## 2. Konteks
Sesudah DK2 juri tahu *teorinya*. Sekarang mereka harus *melihatnya*. Banyak finalis lain menampilkan mockup atau UI formulir; Fabius menampilkan rekaman layar ponsel sungguhan + halaman yang membaca chain. Klip tanpa audio; presenter yang bernarasi, sinkron dengan klip.

## 3. POV audiens
| Siapa | Yang ia cari di klip | Momen "aha" |
|---|---|---|
| Juri UX | berapa langkah, ada wallet/gas/seed phrase? | "tidak ada popup wallet, tidak ada gas" |
| Juri teknis | apakah data benar-benar dari chain? | nomor blok + jam segel + "Verified" |
| Juri dampak | apakah Andi bisa memakainya? | Telegram, bahasa sederhana |
| Juri AI Agents | di mana agennya? | kalimat penutup: agen lain bisa cek lewat MCP |

## 4. POV presenter
- Berdiri sedikit ke samping layar, badan menghadap juri, sesekali menoleh ke klip **saat** menyebut momen penting (bukan membaca layar terus).
- Narasi mengikuti klip: berlatih dengan klip final minimal 3 kali; tandai detik di notes.
- Saat "Verified" muncul: berhenti bicara ±0,5 detik, biarkan layar yang bicara.
- Bila klip macet: jangan panik — klik ke frame cadangan (gambar diam) dan lanjutkan naskah; tidak ada yang tahu urutan aslinya.

## 5. Konsep
**"Dari chat ke chain dalam 40 detik."** Kiri: ponsel (dunia pembeli). Kanan: halaman verify (dunia bukti). Satu garis cahaya menghubungkan link di chat ke halaman verify — sinyal yang sama, dua sudut.

## 6. Ilustrasi + tata letak
Panel **lavender**; bingkai ponsel + browser kaca (DKV §6).
- **Label kecil di atas kiri:** pil `● Live on BNB Smart Chain testnet` (mono, `#9D86FF`).
- **Klip utama** (±75 % lebar): dua bagian berurutan dalam satu video, atau dua bingkai berdampingan:
  - Bagian A (±15 d): bingkai **ponsel** (mockup sederhana, sudut membulat, sedikit miring ke kanan) berisi rekaman Telegram: `/start` → `/buy` → persetujuan bayar x402 → sinyal + link.
  - Bagian B (±20 d): bingkai **browser** berisi halaman `/verify` (atau `/tour`) yang dibuka dari link: stasiun menyala satu per satu → vonis **Verified**.
  - Transisi A→B: zoom ke link di chat, garis cahaya `#6E4BFF` "menarik" ke bingkai browser.
- **Sorotan** (lingkaran/garis `#6E4BFF`, muncul pada detik yang ditandai): (1) teks "no gas"/tanpa popup wallet di ponsel; (2) jam segel + nomor blok di halaman verify; (3) vonis Verified.
- **Caption bawah** (muncul saat Verified): **"Sealed at block #_____ — 8.7 h after close, within the 12 h limit. Verified."** — angka diisi **dari rekaman** (jangan dikarang; lihat §10).
- Caption Verified dalam **panel night kecil** dengan kubus verified + glow (meniru panel vonis `/verify`, `aset/layar/08-verify-b2rs-stasiun.png`). Cadangan diam: `aset/layar/03-tour-langkah-1-3.png`, `04-tour-langkah-4-5-verified.png`.

## 7. Teks di slide (Inggris, persis)
- Pil atas: **Live on BNB Smart Chain testnet**
- Caption: **Sealed at block #_____ — __ h after close (limit 12 h). Verified.**
- Label kecil di ponsel (opsional): **Pay per signal · x402 · no gas** · **test token**

## 8. Naskah lisan
**Indonesia (utama, ±85 kata), sinkron dengan klip:**
> "Ini dari sisi pembeli. *(klip mulai otomatis)* Di Telegram, saya minta sinyal hari ini.
> Bayar per sinyal lewat x402 — tanpa gas, tanpa install wallet. Ini token uji, di testnet.
> Sinyal datang bersama satu link. Saya klik.
> Halaman ini membaca langsung dari BNB Chain: strategi dikunci tanggal sekian; hari ditutup jam nol-nol; sinyalnya disegel delapan jam kemudian — di dalam batas dua belas jam. Dibuka, dihitung ulang, cocok. *(jeda)* **Verified.**
> Saya tidak perlu percaya Fabius. Dan agen AI lain bisa melakukan cek yang sama lewat MCP."

**English (±80 kata):**
> "This is the buyer's side. In Telegram, I ask for today's signal.
> I pay per signal with x402 — no gas, no wallet to install. It's a test token, on testnet.
> The signal arrives with one link. I tap it.
> This page reads straight from BNB Chain: the strategy was locked on this date; the day closed at midnight; the signal was sealed eight hours later — inside the twelve-hour limit. Opened, recomputed, matched. *(pause)* **Verified.**
> I don't have to trust Fabius. And any AI agent can run the same check over MCP."

Sesuaikan "tanggal sekian / delapan jam" dengan angka di rekaman final. *(boleh dipotong: "Ini token uji, di testnet." hanya bila pil "testnet" terlihat jelas di layar)*

## 9. Animasi + transisi
- Klip **mulai otomatis** saat slide tampil, tanpa audio, tidak berulang; frame terakhir (Verified) ditahan sampai `[KLIK]` berikut.
- Sorotan muncul sebagai lapisan di atas klip pada detik yang ditandai (atau dibakar ke video saat penyuntingan — lebih aman).
- Kecepatan klip boleh 1,25–1,5× pada bagian menunggu (loading), **jangan** pada momen Verified.
- Keluar ke DK4: frame Verified bergeser ke kiri, empat kartu DK4 masuk dari kanan.

## 10. Angka + sumber
- Semua angka di caption/naskah **dari rekaman final** (nomor blok, jam segel, selisih jam). Hanya bila rekaman Telegram tidak ada, pakai cadangan dari `/tour` produksi: **B2-RS hari 2026-10-05 — dikunci 2026-10-04 16:37:25Z, hari tutup 2026-10-06 00:00Z, 4 sinyal disegel 08:44Z (+8,7 j), dibuka, Verified**; tx segel `0x74e3a683…` blok #135.176.214 *(cek ulang dari layar `/tour` saat merekam)*.
- x402: token uji FAB, 0,01 FAB per sinyal, pembeli tanpa gas (Privy). ✅
- MCP: alat `fabius_verify` / `fabius_signals` di `fabius-one.vercel.app/mcp`. ✅

## 11. Aset
| ID | Aset | Status |
|---|---|---|
| **A2** | Rekaman layar Telegram ±15–20 d (`/start` → `/buy` → bayar → sinyal + link) | ⬜ **builder merekam 29 Okt sore WIB** sesudah hari 28 Okt disegel (LB27). Placeholder merah: `KLIP BELUM ADA — A2` |
| **A3** | Rekaman layar halaman verify/tour sampai Verified ±20 d | ✅ bisa direkam kapan saja dari `fabius-one.vercel.app/tour` atau dari link di klip A2 |
| K4 | Cadangan: video v2 47,6–61,6 d (beli via web/Telegram/MCP, animasi) | potong klip = tugas terakhir (P185) |

Rekam di resolusi asli ponsel, potong ke ±40 d total, ekspor H.264 1080p tanpa audio, **tanam** di PPTX.

## 12. Jangan
- Jangan menulis/mengucapkan "real-time", "profit", "guaranteed".
- Jangan memotong label "testnet" / "test token" dari klip.
- Jangan memakai mockup palsu sebagai pengganti rekaman tanpa label "illustration".
- Jangan demo **live** Telegram di panggung sebagai jalur utama (jaringan/login tak pasti); live hanya bonus bila waktu tersisa di Q&A.

## 13. Risiko + cadangan
| Risiko | Cadangan |
|---|---|
| A2 tidak sempat direkam / pembayaran gagal | klip A3 saja (tur `/tour`, Verified) + gambar diam ponsel dari video v2 (K4); naskah tetap, ganti "di Telegram, saya minta…" menjadi "pembeli meminta…" |
| Hari terbaru belum Verified saat merekam | rekam hari yang sudah Verified (B2-RS 2026-10-05) lewat `/tour` |
| Klip tidak jalan di laptop panggung | frame diam berurutan (3 gambar: chat, link, Verified) di slide yang sama |
| Juri bertanya "itu uang sungguhan?" | "Bukan — token uji di testnet, sengaja. Lihat slide berikutnya kenapa." |

## 14. Cek selesai
- [ ] Klip tertanam, mulai otomatis, tanpa audio, ≤ 40 d.
- [ ] Nomor blok + jam di caption sama persis dengan yang tampil di klip.
- [ ] Label testnet terlihat.
- [ ] Naskah dilatih sinkron dengan klip final (3×).

**Terkait:** [[14-Deck-Demo-Day/DK2 - Slide 2 Kunci Segel Periksa]] · [[14-Deck-Demo-Day/DK4 - Slide 4 Coba Curangi]]

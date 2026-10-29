---
tags: [deck, "DK4"]
---

# DK4 - Slide 4 Coba Curangi

**Bagian dari:** [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]] · brief: [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]]
**Sumber:** [[08-Backlog/01 - Backlog]] P178 (`/break`, diuji produksi 28 Okt 15:16Z: 4/4 ditolak) · `web/src/lib/break.ts` · `contracts/SignalAnchor.sol` · naskah USULAN, menunggu LB25.
**Peta:** sebelumnya [[14-Deck-Demo-Day/DK3 - Slide 3 Demo Beli lalu Periksa]] · berikutnya [[14-Deck-Demo-Day/DK5 - Slide 5 Dibangun untuk Diragukan]]

**Ringkas:** Slide 4 dari 6 · **1:35–2:05 (30 d, 60 kata)**. Empat cara penjual sinyal memalsukan track record, dijalankan terhadap kontrak `SignalAnchor` yang sama dari alamat committer resmi Fabius sendiri — empat penolakan bernama dari kontrak. Pesan: aturannya ditegakkan **kode di chain**, bukan janji kami. Juri bisa mengulanginya sendiri di `/break`.

## 1. Tujuan slide
- Mengubah "percayalah, kami jujur" menjadi "kami **tidak bisa** curang, ini buktinya".
- Menjawab sebelum ditanya pertanyaan paling tajam juri teknis: *bisakah operator Fabius sendiri menulis ulang sejarah?*
- Memberi juri sesuatu yang bisa **mereka coba sendiri** (UX + demo + inovasi sekaligus).

## 2. Konteks
Finalis lain banyak yang punya "red-team" atau batas kontrak untuk *aksi* AI. DK4 menunjukkan batas untuk *sejarah*: urutan waktu. Ini puncak teknis presentasi; sesudah ini nada turun ke kejujuran (DK5).

## 3. POV audiens
| Siapa | Reaksi yang diharapkan |
|---|---|
| Juri teknis | "Revert bernama, dari alamat committer resmi, simulasi eth_call di blok nyata — ini sungguhan." |
| Juri produk/dampak | "Bahkan pemiliknya tidak bisa curang. Itu yang dibutuhkan pembeli sinyal." |
| Juri AI Agents | "Ini guardrail untuk *waktu keputusan* agen — belum ada yang punya." |

## 4. POV presenter
- Ubah nada jadi sedikit "nakal" di awal: "Tapi bagaimana kalau **kami sendiri** yang mau curang?" — senyum kecil.
- Tiap cara curang diucapkan cepat (satu kalimat) lalu kata **"ditolak"** dengan tempo tetap, seperti ketukan — empat ketukan.
- `[KLIK]` tiap ketukan memunculkan cap merah pada kartunya (atau klip `/break` "Try all four" berjalan sendiri dan presenter mengikuti).
- Kalimat penutup lambat: "Yang menolak bukan kami — **kontraknya**."

## 5. Konsep
**"Empat kunci yang dicoba, empat pintu yang tetap tertutup."** Empat kartu kecurangan; masing-masing dicap merah dengan nama revert persis dari kontrak.

## 6. Ilustrasi + tata letak
Latar `#0F0B26`.
- **Judul (Archivo, 2 baris):** "Try to cheat." / ***"Watch it fail."*** (*Watch it fail.* miring tebal `#9D86FF`) — sama dengan judul halaman `/break` agar juri mengenali saat membuka QR.
- **Grid 2×2 kartu** `#1A1442` (atau klip rekaman `/break` dalam bingkai browser, glow ungu):
  1. "Write yesterday's call after the market moved" → cap **`TooLate`**
  2. "Claim a call from before the strategy existed" → cap **`LockedAfterBar`**
  3. "Quietly tweak the strategy after seeing the data" → cap **`NotLocked`**
  4. "Add a winning signal to a day already sealed" → cap **`TooManyReveals`**
- Cap = persegi panjang membulat, garis `#FF5A6E`, teks JetBrains Mono `#FF5A6E`, sedikit miring (−4°), seperti stempel "REJECTED".
- **Baris bawah kecil (mono, `#8B86A6`):** "Simulated (eth_call) against the live SignalAnchor on BNB testnet, from Fabius's own committer · try it: fabius-one.vercel.app/break"

## 7. Teks di slide (Inggris, persis)
- Judul: **Try to cheat. *Watch it fail.***
- Kartu 1–4 seperti §6 + cap `TooLate` · `LockedAfterBar` · `NotLocked` · `TooManyReveals`
- Bawah: **Rejected by the contract — not by us.** · *Simulated against the live contract · fabius-one.vercel.app/break*

## 8. Naskah lisan
**Indonesia (utama, ±66 kata):**
> "Tapi bagaimana kalau **kami sendiri** yang mau curang? Kami coba empat cara, langsung ke kontrak yang sama.
> `[KLIK]` Tulis sinyal kemarin sesudah pasar bergerak: **ditolak**.
> `[KLIK]` Klaim sinyal dari sebelum strateginya ada: **ditolak**.
> `[KLIK]` Ubah strategi diam-diam: **ditolak**.
> `[KLIK]` Tambah sinyal pemenang ke hari yang sudah disegel: **ditolak**.
> Yang menolak bukan kami — **kontraknya**. Halaman ini publik; silakan coba sendiri."

**English (±62 kata):**
> "But what if **we** wanted to cheat? We tried four ways, against the same contract.
> `[CLICK]` Write yesterday's call after the market moved: **rejected**.
> `[CLICK]` Claim a call from before the strategy existed: **rejected**.
> `[CLICK]` Quietly change the strategy: **rejected**.
> `[CLICK]` Add a winning signal to a day already sealed: **rejected**.
> Not rejected by us — by the **contract**. The page is public; try it yourself."

## 9. Animasi + transisi
- Opsi A (disarankan): kartu statis + cap muncul per `[KLIK]` (scale 1,15 → 1,0 dalam 180 ms, tanpa suara).
- Opsi B: klip rekaman `/break` (klik "Try all four" → empat kartu "Rejected by the contract") ±12 d diputar otomatis; presenter mengikuti urutan kartu di klip. Lebih "hidup", tetapi sinkronisasi lebih sulit.
- Keluar ke DK5: cap merah memudar, latar sedikit menggelap (nada turun ke refleksi).

## 10. Angka + sumber
- Empat revert diuji di produksi 28 Okt 15:16Z (`/api/break`): late → `TooLate` (asof 2026-10-27, maxLag 12 j), prelock → `LockedAfterBar` (lockedAt 2026-10-02T15:49:20Z, asof 2026-10-01), respec → `NotLocked`, extra (B2-RS 2026-10-05, 4/4 sudah dibuka) → `TooManyReveals`. Diuji ulang 29 Okt (4/4). ✅
- Simulasi = `eth_call` dengan `from` = committer resmi `0xCA9c7322210E9a7F7d0953c862d4Ef60cC0D64A4`; tidak ada transaksi, kunci, atau gas. ✅

## 11. Aset
| ID | Aset | Status |
|---|---|---|
| **A4** | Rekaman layar `fabius-one.vercel.app/break` → "Try all four" → empat kartu ditolak (±12 d) | ✅ bisa direkam kapan saja (opsi B) |
| — | Kartu + cap (opsi A) | dibuat langsung di PPT |

## 12. Jangan
- Jangan menyebut simulasi sebagai "transaksi" atau "kami mengirim tx".
- Jangan menulis "unhackable", "impossible to cheat", "tamper-proof" — yang dibuktikan hanya empat cara ini.
- Jangan menjelaskan isi argumen revert di lisan (cukup "ditolak").

## 13. Risiko + cadangan
| Risiko | Cadangan |
|---|---|
| Juri: "itu cuma simulasi" | "Ya — simulasi eth_call di blok terbaru terhadap kontrak yang sama, dari alamat committer resmi. Transaksi sungguhan akan revert dengan error yang sama; bedanya kami tidak membakar gas. Perintah `cast` untuk mengulanginya ada di halaman." |
| Juri: "admin bisa ganti aturannya?" | "Tidak. `SignalAnchor` dan `LockRegistry` tanpa owner, tanpa proxy, tanpa fungsi setter; batas 12 jam `immutable` sejak deploy. Yang bisa kami lakukan hanya **berhenti** menyegel — dan itu tercatat publik." (diperiksa 29 Okt: `contracts/SignalAnchor.sol:54-56`, tidak ada `owner`/`set*` di kedua kontrak) |
| Juri: "bagaimana dengan 100 varian?" | kartu 4 + DK0 §12 |

## 14. Cek selesai
- [ ] Empat nama revert ditulis persis (huruf besar-kecil).
- [ ] URL `/break` tertulis.
- [ ] Label "simulated" ada.
- [ ] ≤ 30 detik dengan empat ketukan.

**Terkait:** [[14-Deck-Demo-Day/DK3 - Slide 3 Demo Beli lalu Periksa]] · [[14-Deck-Demo-Day/DK5 - Slide 5 Dibangun untuk Diragukan]]

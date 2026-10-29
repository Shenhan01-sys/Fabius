---
tags: [deck, "DK2"]
---

# DK2 - Slide 2 Kunci Segel Periksa

**Bagian dari:** [[14-Deck-Demo-Day/00 - Hub Deck Demo Day]] · brief: [[14-Deck-Demo-Day/DK0 - Brief Pembuatan Deck]]
**Sumber:** [[10-Submissions/04 - Demo Day 31 Okt - Materi Pitch]] §3 · `contracts/SignalAnchor.sol` (`commit`: `NotLocked`, `LockedAfterBar`, `TooLate`) · `contracts/LockRegistry.sol` · DK0 §2.4 · naskah USULAN, menunggu LB25.
**Peta:** sebelumnya [[14-Deck-Demo-Day/DK1 - Slide 1 Kapan Ini Ditulis]] · berikutnya [[14-Deck-Demo-Day/DK3 - Slide 3 Demo Beli lalu Periksa]]

**Ringkas:** Slide 2 dari 6 · **0:30–0:55 (25 d, 61 kata)**. Jawaban atas pertanyaan DK1 dalam tiga kata kerja yang bisa diingat: **Lock → Seal → Check**. Nama kontrak hanya sebagai label kecil untuk juri teknis; orang awam cukup mengingat tiga kata.

## 1. Tujuan slide
- Memberi jawaban yang sederhana: *kapan* bisa dibuktikan **dengan nomor blok**.
- Membuat juri teknis yakin ini ditegakkan kontrak (nama revert kecil), sambil tetap mudah bagi juri non-teknis.
- Menyebut agen AI dengan benar: AI memilih, **formula terkunci** menghitung — menjawab kecurigaan "AI dibiarkan bebas".

## 2. Konteks
Juri masih memegang pertanyaan "kapan ini ditulis?". Slide ini harus terasa seperti **lega**: ada jawabannya, dan jawabannya mekanis, bukan janji. DK3 dan DK4 akan *menunjukkan* tiga langkah ini; jadi di sini cukup pengenalan, jangan menjelaskan Merkle/salt.

## 3. POV audiens
| Siapa | Pertanyaan di kepala | Yang menjawabnya di slide |
|---|---|---|
| Juri teknis | "Ditegakkan kontrak atau server?" | label mono `TooLate · 12h`, `LockedAfterBar` |
| Juri produk | "Apa yang dialami pengguna?" | kata ketiga: "Anyone checks. No login. No gas." |
| Juri AI Agents | "Di mana AI-nya?" | baris bawah: AI analysts pick · locked formula sizes |

## 4. POV presenter
- Hitung dengan jari (1-2-3) saat menyebut Kunci, Segel, Periksa — membantu juri mengingat struktur.
- Tiap `[KLIK]` memunculkan satu kartu tepat saat kata kerjanya diucapkan; jangan klik duluan.
- Tekankan "**termasuk keputusan diam**" — itu yang membedakan dari pencatatan biasa.
- Nada naik di "kontrak menolak" (ini janji yang akan dibuktikan di DK4).

## 5. Konsep
**"Tiga stasiun, satu rel."** Satu keputusan berjalan dari kiri ke kanan: dikunci → disegel → diperiksa. Sama dengan metafora stasiun di halaman `/verify` dan `/tour`, supaya juri yang nanti membuka QR mengenali bentuknya.

## 6. Ilustrasi + tata letak
Latar `#0F0B26`.
- **Judul kecil di atas (opsional, 1 baris):** "Fabius answers *when* — with a block number." (Archivo, `#ECE8FA`, *when* `#9D86FF`).
- **Tengah:** tiga kartu kaca `#1A1442` dengan garis tepi `#6E4BFF` 1,5 px, disambung **rel tipis** horizontal bercahaya; di atas tiap kartu satu **kubus kaca** kecil (motif situs):
  1. kubus **indigo dengan gembok** — **LOCK**
  2. kubus **tersegel** (indigo bercahaya, garis segel) — **SEAL**
  3. kubus **putih bersinar dengan ✓** — **CHECK**
- Di bawah tiap kata kerja: satu kalimat isi (Inter 24–28 pt) + satu label mono kecil (JetBrains Mono 14–16 pt, `#9D86FF`).
- **Pita bawah (muncul terakhir):** ikon kecil robot/analis ×3 → panah → ikon rumus terkunci: "AI analysts (ERC-8004) pick the bot · a locked formula sizes the position".
- Rel memanjang keluar slide ke kanan (mengarah ke demo berikutnya).

## 7. Teks di slide (Inggris, persis)
| Kartu | Kata besar | Isi | Label mono |
|---|---|---|---|
| 1 | **LOCK** | Strategy locked on-chain first — no quiet rewrites | `LockRegistry · LockedAfterBar` |
| 2 | **SEAL** | Every decision sealed before the outcome | `SignalAnchor · TooLate (12h)` |
| 3 | **CHECK** | Anyone checks. No login. No gas. | `/verify · MCP` |

Pita bawah: **AI analysts (ERC-8004) pick the bot · a locked formula sizes the position**

## 8. Naskah lisan
**Indonesia (utama, ±58 kata):**
> "Fabius membuat pertanyaan itu bisa dijawab — dengan nomor blok. Tiga langkah.
> `[KLIK]` **Kunci**: strategi tiap bot dikunci on-chain lebih dulu — tidak bisa diubah diam-diam.
> `[KLIK]` **Segel**: setiap keputusan, termasuk keputusan diam, disegel sebelum hasilnya ada. Lewat dua belas jam, kontrak menolak.
> `[KLIK]` **Periksa**: siapa pun bisa mengecek — tanpa login, tanpa gas.
> `[KLIK]` Agen AI kami memilih bot; formula terkunci yang menentukan posisi."

**English (±55 kata):**
> "Fabius makes that question answerable — with a block number. Three steps.
> `[CLICK]` **Lock**: each bot's strategy is locked on-chain first — no quiet rewrites.
> `[CLICK]` **Seal**: every decision, even the decision to do nothing, is sealed before the outcome. Twelve hours late, the contract refuses.
> `[CLICK]` **Check**: anyone can verify — no login, no gas.
> `[CLICK]` Our AI agents pick the bot; a locked formula sizes the position."

*(boleh dipotong: kalimat terakhir tentang agen AI, bila DK5/DK6 sudah menyebut AI — jangan dipotong bila presentasi untuk track AI Agents)*

## 9. Animasi + transisi
- Masuk dari DK1: kubus pertama "mendarat" di posisi kartu screenshot terdepan (morph), lalu rel tergambar kiri→kanan 400 ms.
- 4 `[KLIK]`: kartu 1, 2, 3, pita bawah — masing-masing fade + naik 12 px, 250 ms.
- Saat kartu 2 muncul, kubus berubah dari bening ke tersegel (pulse 1 kali, tanpa suara).
- Keluar ke DK3: zoom pelan ke kartu 3 (CHECK) → transisi ke klip demo.

## 10. Angka + sumber
- 12 jam = `maxLag` 43.200 detik di `SignalAnchor` (revert `TooLate`). ✅
- `LockedAfterBar` = segel untuk hari yang sudah tutup sebelum strateginya dikunci ditolak; strategi yang diubah = sidik jari lain yang tidak pernah dikunci (`NotLocked`). Kontrak menegakkan kunci ≤ penutupan hari, **bukan** sebelum hari dimulai — jangan diucapkan "sebelum hari dimulai". ✅
- "Keputusan diam" = hari tanpa sinyal tetap disegel dengan akar kosong (halaman `/verify`: "The empty root is committed anyway"). ✅
- ERC-8004: Fabius #2494 — tidak perlu ditulis di slide.

## 11. Aset
- Kubus kaca: render ulang dari motif situs (`web/src/components/hero/Crystal.tsx`) atau gambar vektor isometrik sederhana (indigo / tersegel / putih ✓).
- Ikon analis: siluet voxel sederhana (situs memakai NPC voxel di `/desk`), 3 buah, warna kulit beragam.

## 12. Jangan
- Jangan menulis "Merkle", "salt", "commit-reveal", "tick", "F-D16", "G1–G11" di slide (boleh di Q&A).
- Jangan menulis "tamper-proof", "trustless", "immutable" — pakai "sealed before the outcome".
- Jangan menjanjikan "real-time".

## 13. Risiko + cadangan
| Risiko | Cadangan |
|---|---|
| Juri teknis bertanya "bagaimana kalau bot tidak menyegel di hari buruk?" | DK0 §12: jadi `gap` publik, dihitung tak terukur; contoh 13–27 Okt |
| Juri bertanya "commit 100 varian?" | jawab: jumlah sinyal dikunci + sinyal ekstra ditolak (demo keempat di DK4) |
| Terlalu cepat | kalimat terakhir (AI) boleh dipersingkat jadi "AI memilih; rumus terkunci menghitung" |

## 14. Cek selesai
- [ ] Tiga kata LOCK / SEAL / CHECK terbaca dari belakang ruangan.
- [ ] Label mono ada tapi tidak dominan.
- [ ] Klik sinkron dengan kata kerja di naskah.
- [ ] ≤ 25 detik.

**Terkait:** [[14-Deck-Demo-Day/DK1 - Slide 1 Kapan Ini Ditulis]] · [[14-Deck-Demo-Day/DK3 - Slide 3 Demo Beli lalu Periksa]]

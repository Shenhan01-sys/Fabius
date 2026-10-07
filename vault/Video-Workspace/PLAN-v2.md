---
tags: [video, rencana, "P172"]
---

# PLAN v2 - video pitch Fabius 90-100 s: konsumen + agentic, imersif, banyak interaksi web (P172)

**Bagian dari:** [[Video-Workspace/00 - Hub Workspace]]
**Sumber:** permintaan builder 7 Okt malam (di bawah) · `vault/Reference-VideoPitchs/NOTE.txt` · `Motion-as-Code-Workflow-Guide.pdf` ·
lima klip referensi · dek `13-SubmmisionDocs/Fabius-Submission-Deck-final.pptx` (7 Okt, dibaca saja) · situs hidup `fabius-one.vercel.app`
(ditangkap 7 Okt 22:37-22:41 WIB, `scripts/capture-web.mjs --base https://fabius-one.vercel.app --out out/live`) · `web/src` (komponen 3D)

## Permintaan builder (7 Okt malam)

> *"video pitch dengan durasi yg ideal kayaknya di 100 detik ... clear dan jelas ... end to end dan komersial untuk semua orang karena ini consumer
> apps [+ Agentic AI] ... motion graphics yg inklusif sekaligus imersif agar user takjub namun tetap menangkap context terkait fabius dengan akurat ...
> banyak interaksi langsung dengan website kita ... immersive frame website ... di page yg ingin dijelaskan + animasi immersivenya"*
>
> *"Bukan ukuran render, ukuran kualitas video, khususnya kualitas motion graphicsnya seberapa immersive dan motionfullnya itu saya anggap masih hanya
> 60%, kurang banyak berinteraksi dengan page web Fabius tapi dengan motion yg mewah dari berbagai pov ... sehingga kesannya sangat spesial. Jgn lupa
> gunakan mcp motion.so juga + jgn pernah pakai sound effect yg memberikan kesan suara crash atau rusak"*

Target: kualitas motion 90-95 % setingkat referensi (UI produk miring di ruang 3D, kamera terbang, kursor mengklik UI, kartu melayang keluar dari
layar, glow, tipografi kinetik, potongan cepat ikut musik).

## Diagnosis v1 (fakta, dicetak 7 Okt)

| temuan | bukti |
|---|---|
| v1 berdurasi 126,47 s (target baru 90-100 s) | `ffprobe render/fabius-pitch.mp4` |
| **proyek v1 tidak bisa dijalankan dari repo**: `src/lib/*` (palette, fonts, lyrics, util, stroke) dan `public/data/*` (lyrics.json, audio.json) tidak pernah masuk git karena `.gitignore` root memuat `lib/` (baris 5) dan `data/` (baris 40); tidak ada di cabang mana pun | `git check-ignore -v --no-index vault/Video-Workspace/src/lib/util.ts` · `git log --all -- 'vault/Video-Workspace/src/lib/*'` = kosong |
| bahasa teknis untuk penonton umum (Merkle root, ERC-8004, G1-G11, F-D16, maxLag) dan frame web kecil / jarang; banyak frame kosong | contact sheet 0,5 fps `out/ref/cur-0.5fps.jpg` |
| kit SFX memuat suara yang terdengar crash / rusak (`falling_pieces`, `impact_slam`, `zap_slash`, `spark_sizzle`, `tape_rewind`, `reverse_suck`, `snip`, `impact_small_*`, `stamp`, `marker_strike`) | `public/audio/sfx/` |

## Konsep v2

**Satu kalimat:** *Fabius menyegel tiap sinyal di BNB Chain sebelum pasar menjawab - dan siapa pun bisa memeriksanya.* (kalimat hero situs)

- **Objek inti = kristal kaca situs** (`web/src/components/hero/Crystal.tsx`): blok kaca = komitmen (indigo = aturan terkunci, putih = sinyal
  terbukti, bening = slot kosong). Kristal yang sama dirender ulang di Remotion (`@remotion/three`), jadi kamera bisa memutarinya dari POV mana pun.
- **Masuk-keluar halaman web asli:** kamera mulai dari jendela browser situs hidup yang melayang miring di ruang lavender, mendorong masuk ke kanvas
  3D-nya, berpindah ke adegan 3D asli yang dirender ulang (kristal, Live Book meja AI dengan NPC voxel beragam warna kulit), lalu keluar lagi ke halaman
  berikutnya. Gerak halaman (ketik headline, scroll, klik, stasiun verifikasi menyala) = tangkapan situs hidup dengan waktu virtual (bingkai demi
  bingkai, mulus 60 fps), bukan tiruan.
- **Kursor sungguhan:** klik / hover yang direkam saat penangkapan (koordinat per bingkai) digambar ulang sebagai kursor premium + riak klik + kartu UI
  yang "terangkat" keluar dari halaman (potongan tangkapan yang sama, bukan gambar baru).
- **Inklusif:** kalimat sederhana tanpa jargon di suara, istilah teknis hanya sebagai label kecil di layar; caption terbakar (bisa ditonton tanpa
  suara); kontras teks AA; trek subtitle `.srt` Inggris + Indonesia (USULAN); NPC voxel situs yang beragam.
- Palet + huruf = situs: lav `#ece8fa`, lav-2 `#ddd5f6`, lav-3 `#c9bdf2`, ink `#15122b`, night `#0f0b26`, night-2 `#1a1442`, violet `#6e4bff`,
  violet-2 `#9d86ff`, mist `#8b86a6`, gap `#ff5a6e` (`web/src/app/globals.css`); Archivo (sumbu `wdth`, tegak + miring), Inter, JetBrains Mono
  (`web/src/app/layout.tsx`).

## Naskah v2 (USULAN, Inggris; ±225 kata ≈ 90-95 s)

| # | adegan | suara (USULAN) | yang tampil (POV) | sumber klaim |
|---|---|---|---|---|
| 1 | hook | Every trading bot has a perfect track record. The catch? It's always written after the market moves. | kartu "profit" gaya media sosial terbang dari kedalaman; cap waktunya berbalik: *posted after the move*; kartu larut jadi partikel (tanpa suara pecah) | framing; dek slide 2 |
| 2 | reveal | So we built the opposite. Meet Fabius: it seals every signal on BNB Chain, before the market answers. | kristal merakit diri (blok terbang lalu mengunci) -> headline hero situs mengetik -> kamera mundur: kita berada di dalam halaman `fabius-one.vercel.app` | hero `/` ; `contracts/SignalAnchor.sol` |
| 3 | rules | First, the rules. Each bot's strategy is locked on-chain first, so it can't be quietly rewritten after a bad day. | `/bot/B1-TREND`: kutipan aturan, pil *spec locked on-chain* berdenyut; enam tablet kaca B1..B6 berjajar, gembok kaca menutup dengan jam kunci asli | `deployments/97.json` `m3.locks`; `LockRegistry` |
| 4 | seal | Every day, the candle closes, the bot makes its call, and Fabius seals it with a timestamp no one can change. Not even us. | koridor 3D lima stasiun *From candle close to proof* (bingkai situs), kamera terbang menembus; blok kaca tersegel naik ke rantai blok | `/` bagian perjalanan; `SignalAnchor.commit` |
| 5 | AI desk | Who picks the bot? A desk of AI agents. Every five minutes, analysts with their own on-chain identities make their picks, and a locked formula turns them into one paper portfolio, sealed before the cycle ends. | `/desk` -> kamera menyelam ke Live Book 3D: agent voxel mengangkat kubus ✓, mesin rumus (6 kubus mengorbit), robot aturan, batang buku, tumpukan blok BNB menyala; POV rendah / orbit / atas | `/desk` teks situs; `DeskAnchor.CYCLE = 300`; `config/agents.json` |
| 6 | use it | Want today's signal? Grab it on the web, in Telegram, or let your AI agent fetch it over MCP. Pay per signal with x402, no gas, no subscription, and it arrives with its proof. | `/buy`: kursor ke *Sign in (Google · Telegram · email)*, harga 0.01 FAB; ponsel Telegram (templat balasan bot asli); panel agen: panggilan MCP -> `402 Payment Required` -> tanda tangan -> sinyal + bukti | `/buy`; `tools/x402_sinyal.py`; dek slide 8; P157 |
| 7 | verify | Then check it yourself. Pick any bot, any day: Fabius rebuilds the signal from public data and the chain. No key. No gas. | `/verify`: kursor memilih bot + tanggal, klik *Verify*, empat stasiun menyala (Ledger tick -> Committed on-chain -> Opened -> Recomputed) | `/verify`; `tools/verify_signals.py` |
| 8 | open | Got your own bot, or your own agent? Bring it. It faces the same public gates as ours. | `/submit` (Rule / Code / Feed), `/submit-agent`; kartu bot pengguna melewati portal kaca gerbang | `engine/rule.py`, `engine/gates.py`, P167a / P169 |
| 9 | honest + end | No profit promises: it's paper money on testnet, and zero of six bots have passed the forward test yet. Fabius waits for proof. Don't trust it. Check it. | penghitung 0 / 6; kristal kembali utuh; kartu akhir `fabius-one.vercel.app` · *Live on BNB Chain testnet* | `python -X utf8 -m engine.cli ledger fd16` (dicetak ulang hari render); `config/uang_nyata.json` |

Angka di layar (jumlah komit, kunci, hari diam, 0 / 6) dicetak ulang oleh perintahnya **pada hari render** dan dicatat di `SCRIPT.md`.

## Teknik

- **Proyek dibangun ulang di workspace yang sama** (Remotion 4): `src/lib` baru + perbaikan `.gitignore` lokal (`!src/lib/`, `!public/data/`) supaya
  proyek jalan dari klon bersih; kode v1 yang berguna dipindah (kamera, perangkat, kursor, transisi), sisanya tetap di riwayat git.
- **Tangkapan web deterministik** (`scripts/capture-flow.mjs`, USULAN): Playwright + Chrome, waktu virtual (`performance.now`, `Date`, rAF, timer,
  animasi CSS lewat Web Animations) dimajukan 1/60 s per bingkai, interaksi (klik, hover, scroll) dijadwalkan per alur; keluaran = klip H.264 +
  JSON kursor per bingkai. Halaman yang butuh login (Privy) hanya sampai sebelum login.
- **3D asli situs di Remotion:** port `Crystal` + Live Book meja (`PipelineScene`, `parts`) ke `@remotion/three`, waktu dari `useCurrentFrame()`,
  kamera per adegan (POV).
- **Gerak:** kamera 3D per adegan + parallax berlapis, kedalaman bidang, sapuan cahaya, glow, debu, grain halus, motion blur pada gerak cepat,
  transisi bermotif (zoom-through, whip, iris kaca, portal layar). 1920x1080, **60 fps (USULAN)**.
- **Suara:** voiceover TTS (USULAN: `edge-tts` suara neural Inggris; cadangan Kokoro Apache-2.0; ElevenLabs / Motion.so bila builder menyediakan),
  timing kata dari Whisper lokal; musik **prosedural sendiri** (bebas lisensi, tempo dikunci ke potongan; bisa ditukar trek pilihan builder); **SFX
  bersih disintesis sendiri** (whoosh lembut, klik UI, denting kaca, riser) - daftar terlarang di atas dihapus dari workspace dan diperiksa mesin.
- **Motion.so (MCP):** akun builder terhubung, **saldo 0 kredit** (`get_credit_balance` 7 Okt) -> tiap generate butuh top-up (langkah builder).
  Rencana pemakaian (USULAN): segmen premium (intro kristal + tipografi, adegan "pay per call") dari brief + tangkapan situs, lalu dikomposit ke
  master Remotion; atau potongan pembanding penuh.

## Kriteria keluar

1. `render/fabius-pitch-v2.mp4`: 90-100 s, 1920x1080, H.264, loudness -14 LUFS ±1 (`ffprobe`, `ffmpeg -af ebur128`).
2. >= 8 halaman situs hidup tampil dengan interaksi (kursor, klik, scroll) dari tangkapan hari itu; >= 2 adegan 3D asli situs, masing-masing >= 3 POV.
3. Tiap kalimat suara + angka di layar punya baris sumber di `SCRIPT.md`; angka dicetak ulang hari render; tidak ada klaim untung / edge.
4. Nol SFX terlarang: berkas terlarang tidak ada di workspace + pemeriksa daftar putih lulus.
5. `npm run typecheck` lulus; proyek jalan dari klon bersih (worktree sementara: `npm ci` + typecheck + still).
6. Caption terbakar + `.srt` / `.vtt`; contact sheet still diperiksa.
7. Motion.so: dipakai bila kredit tersedia; bila tidak, tercatat sebagai langkah builder (bukan dianggap selesai).

## Batas lingkungan

Motion.so tanpa kredit; tidak ada kunci TTS berbayar di lingkungan; login Privy / Telegram tidak bisa dilakukan sesi (pakai keadaan halaman sebelum
login + templat balasan bot asli); tidak ada deploy atau transaksi. T8: tidak berlaku (bukan perilaku operator).

**Terkait:** [[Video-Workspace/SCRIPT]] · [[Video-Workspace/README]] · [[Reference-VideoPitchs/00 - Hub Referensi Video]] ·
[[09-Inbox/Session-2026-10-02]] §139 / §163 · [[08-Backlog/01 - Backlog]] P172 · [[08-Backlog/13 - Langkah Builder Tertunda]] LB19-LB21

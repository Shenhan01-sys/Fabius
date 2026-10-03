# Fabius — landing page (tingkat 0: umpan bukti)

Next.js 16 + React 19 + three.js (@react-three/fiber, drei, postprocessing) + motion. Brief desain: `../docs/design/landing.md`.
Semua angka di halaman berasal dari `public/data/snapshot.json`, yang dicetak `../tools/web_snapshot.py` dari ledger + buku + kunci + chain 97.

## Jalankan lokal

```bash
npm install
npm run dev        # http://localhost:3000
npm run build      # pemeriksaan produksi (harus bersih sebelum push)
```

## Deploy ke Vercel

**Sudah hidup (3 Okt 2026):** https://fabius-one.vercel.app · server MCP `https://fabius-one.vercel.app/mcp` (project Vercel `fabius`, tersambung ke
GitHub `master`; build dilewati bila commit tidak menyentuh `web/`). Push ke `master` = deploy.

**Jangan `vercel deploy` dari akar repo:** CLI mengunggah folder kerja apa adanya, termasuk `.env` / `.committer.env` / `.deployer.env` (kunci privat;
tidak ada di daftar abaikan bawaan Vercel). Deploy selalu lewat GitHub: Vercel membangun dari clone, yang hanya berisi berkas ter-track.

Langkah membuat project dari nol (sekali saja, sudah dilakukan):

1. Vercel -> **Add New Project** -> import repo `Shenhan01-sys/Fabius`.
2. **Root Directory: `web`** (wajib; akar repo berisi engine Python, kontrak, vault).
3. Framework terdeteksi otomatis (Next.js). Build command dan output bawaan. Tidak ada environment variable yang dibutuhkan.
4. Deploy. Setiap push ke `master` yang menyentuh `web/` membangun ulang halaman.

## Memperbarui data

```bash
python -X utf8 tools/web_snapshot.py     # dari akar repo; menulis web/public/data/snapshot.json
git add web/public/data/snapshot.json && git commit -m "snapshot web" && git push
```

Batas kejujuran (F-D72): tingkat 1 (sinyal waktu-nyata berbayar) tampil TERKUNCI sampai bot lolos uji maju F-D16 dan telaah hukum. Jangan menambah klaim
keuntungan atau angka yang tidak berasal dari snapshot.

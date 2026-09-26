---
tags: [ekosistem, "E3"]
---

# 03 - Discovery Gap

**Bagian dari:** [[05-Ecosystem/00 - Hub BNB Ecosystem]]
**Sumber:** `docs/agent-card.json`, `04-Tools/TL6`

**Ringkas:** pertanyaan builder "gimana agen lain bisa tahu Fabius ada?" sekarang terjawab
**setengah**. Identitas dan kartu ada; titik masuknya masih di mesin kami.

**Poin kunci:**
| lapis | status |
|---|---|
| identitas ERC-8004 di registry 97 | ✅ tokenId 2494, bisa dibaca siapa pun |
| `agentURI` menunjuk kartu agen | ✅ `docs/agent-card.json` di raw.githubusercontent repo publik |
| kartu menyebut endpoint + harga + network | ✅ ada di kartu |
| endpoint benar-benar bisa dipanggil orang lain | ❌ **`127.0.0.1` — ditandai di kartu sebagai "LOCAL ONLY"** |
| ada pembeli asing | ❌ satu-satunya pembeli sampai sekarang program kami sendiri |
| penemuan tanpa kami mendaftarkan diri ke suatu direktori | 🟡 bisa lewat registry + direktori indexer pihak ketiga; kami tidak mengontrolnya |

**Detail:** yang bisa dilakukan tanpa hosting: event anchor kami bisa **diperoleh dari chain** —
`getAnchor(id)` dihitung ulang dari berkas repo. Yang tidak bisa: orang luar tidak menemukan
endpoint-nya kalau tidak di-host. Jadi klaim yang benar: "identitas dan jejak terbuka; titik masuk
belum dipublikasikan".

## Jalan keluar yang sudah terukur di mesin ini (untuk P2, bukan janji)

Dari proyek lain kami, terukur 26 Sep 2026 di Windows yang sama: **cloudflared quick tunnel hidup**
dan bisa diotomasi —

```
"%LOCALAPPDATA%\cloudflared.exe" tunnel --url http://127.0.0.1:8790 --no-autoupdate
```

- Domain `*.trycloudflare.com` **acak dan berganti setiap run**. Jadi kartu agen tidak boleh menyimpan
  satu URL tetap dari sini: yang di-publish harus dibaca ulang dari log tunnel tiap run, dan kartu
  ikut ditulis ulang — bukan dikarang.
- `localhost.run` **bukan alternatif**: domain barunya baru hidup setelah seorang manusia membukanya
  di browser (`curl` sebelumnya dapat *empty reply*). Jalur "agen memanggil tanpa ada orang di
  tengah" mati untuk opsi ini.
- Server yang memegang `BASE_URL` harus dijalankan **setelah** domain diketahui; kalau tidak, URL
  localhost yang terlanjur dibakar ke dokumen pembayaran tetap localhost walau tunnel hidup.

Artinya untuk klaim: quick tunnel = "endpoint bisa diakses dari luar mesin hari ini", **bukan**
"titik masuk tetap". Kalimat publik tidak boleh lebih dari itu.

**Terkait:** [[05-Ecosystem/01 - ERC-8004 Identity]] · [[04-Tools/TL6 - x402 gate and client]] ·
[[08-Backlog/01 - Backlog]]

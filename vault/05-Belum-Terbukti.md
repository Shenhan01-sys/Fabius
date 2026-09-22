# 05 — Belum terbukti

Ditulis supaya tidak ada yang mengira proyek ini lebih jadi dari kenyataannya. Urut dari yang
paling memblokir.

| # | Yang belum terbukti | Kenapa penting | Cara menutup | Level sekarang |
|---|---|---|---|---|
| 1 | **Kohort "lolos" tidak punya hasil sama sekali** | tanpa itu, "penyaringan kami berguna" cuma separuh: kami baru membuktikan yang ditolak itu buruk | dataset skema 3 dengan `price_usd` baru ada sejak 08:00Z; jalankan screener lagi setelah ≥ 24 jendela | ❌ belum terukur |
| 2 | **Kalibrasi `confidence` Jev** | satu-satunya alasan rasional memakai Jev dibanding prompt JSON yang sudah ada; kalau `confidence`-nya tidak prediktif, tidak ada alasan ganti | satu panggilan nyata, simpan respons mentah, lalu uji: apakah `confidence` tinggi → hit-rate tinggi? butuh API key `console.typesafe.ai` (aksi manusia) dan **bayar hanya kalau lulus** | ❌ belum diuji |
| 3 | **Dokumentasi `/confidence` dan `/patterns` Jev** | halaman itu ada di nav dan bisa mengubah desain (mis. cara batch pertanyaan) | dua GET biasa | ⬜ belum dibaca |
| 4 | **Halaman produk BNB Agent Studio** | jangan mengutip apa pun soal Studio sebelum ini; yang terverifikasi baru SDK | buka `bnbchain.org/en/bnb-agent-studio` di browser, simpan sebagai catatan vault (bukan memory agen) | ❌ belum dibaca primer |
| 5 | **`timesfm[torch]==2.0.1` vs kelas `TimesFM_2p5_200M_torch`** | kalau pin-nya tidak mengekspos simbol 2.5, Space balas **503** di semua POST dan "forecast provider" kami mati saat demo | satu GET ke `/health` setelah deploy Space | ❌ belum dicek |
| 6 | **Deploy ke chain 97** | submission butuh contract address; tanpa ini tidak ada yang bisa diklik | burner key baru + faucet (QuickNode `faucet.quicknode.com/binance-smart-chain/bnb-testnet`, satu-satunya yang mau mengisi wallet baru; butuh bot-check manusia). **Wallet `0x48379F…` tidak dipakai — tercatat bocor di chat** | ⬜ skrip ada, nol percobaan |
| 7 | **x402 jalur HTTP `402`** | settlement terbukti di fork; tapi "agen membayar datanya" belum pernah benar-benar terjadi | server jawab `402` → klien kirim header `PAYMENT` → `/verify` + `/settle` nyata di 97, simpan tx hash. Fasilitator sendiri dengan `eip2612GasSponsoring` (tak ada yang menawarkannya di BSC) | 🟡 fork ✅ / HTTP ❌ |
| 8 | **Narasi politik via GDELT** | klaim "paham narasi & politik" harus punya sumber; CryptoPanic 403, Nansen/Elfa berbayar | pacing 1 request/5 detik (429-nya karena itu, bukan blokir), lalu simpan snapshot headline + tone ke dataset | 🟡 terbuka, belum dipakai |
| 9 | **Ambang veto belum diuji terhadap hasil** | 50k / 24 jam / 45% / 30% itu keputusan kami, bukan temuan | `screen_universe.py` sudah membandingkan outcome per alasan; kalau sebuah veto tidak memprediksi hasil lebih buruk, **cabut dan catat di `02-Ambang.md`** | ❌ belum ada cukup jendela |
| 10 | **Regulasi Indonesia untuk aset spekulatif** | juri & submission; framing kami "tidak menahan dana, tidak mengeksekusi order, paper-only, disclaimer" sudah mengurangi tapi tidak menghapus | satu paragraf dengan rujukan OJK/Bappebti yang dibaca langsung, bukan disimpulkan | ❌ nol bukti primer |
| 11 | **Venue eksekusi on-chain BSC** | masih jadi blocking gap sejak awal riset; dan **sengaja tidak kami janjikan** | putuskan: tetap paper (default sekarang) atau verifikasi 1 venue + testnet + likuiditas nyata | ❌ nol bukti |

## Yang TIDAK akan kami kejar, dan alasannya tertulis di sini

- **Verifiable inference** (zkML / TEE / opML): lima kandidat diuji, semua gugur di chain ini.
  zkBNB adalah rollup skalabilitas, bukan ML. Menyebut "zkML di BNB" akan dibongkar juri teknis.
- **`ValidationRegistry` ERC-8004**: tidak ada deployment-nya di chain mana pun.
- **ERC-7857** (identity NFT dengan metadata privat): butuh verifier TEE/ZKP + Sealed Executor.
- **Monetization Gateway Cloudflare**: waitlist.
- **Eksekusi sungguhan dengan dana orang**: bukan cuma masalah bukti — ini membuka risiko yang tidak
  bisa kami tutup dengan disclaimer, dan demo kita tidak membutuhkannya.

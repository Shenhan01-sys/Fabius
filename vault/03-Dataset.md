# 03 — Dataset point-in-time

Sumber kehidupan klaim "kami tidak hindsight". Berkas & kode:

```
universe/record_bsc_universe.py      perekam (loop jam, atau dipanggil per jam oleh task)
universe/bsc-universe.jsonl          append-only, 1 baris = 1 snapshot (TIDAK di-commit)
universe/manifest.txt                regenerasi: 1 baris per snapshot + sha256-nya (di-commit)
universe/write_universe_manifest.py  pembuat manifest, sekaligus VERIFIKATOR hash
universe/snapshot_universe.bat       satu panggilan per jam, untuk penjadwal sistem
tools/screen_universe.py             corong penolakan: hasil vs alasan penolakan
```

Dataset mentah (`.jsonl`) **tidak** di-commit: berulang dan membesar tiap jam. Yang di-commit
adalah `manifest.txt` — satu baris per snapshot berisi UTC, skema, jumlah kandidat, jumlah lolos,
dinilai-penuh, jumlah pool berharga, dan **sha256 snapshot pada saat pengambilan**.

Kenapa itu bukan mainan: hash dihitung saat data diambil, dari kanonisasi
`json.dumps(sort_keys=True, separators=(",",":"))`. Menaruh daftarnya di riwayat git memberi catatan
yang tidak bisa ditulis mundur — kamu tidak bisa menyisipkan "snapshot minggu lalu" ke commit hari
ini tanpa mengubah riwayat yang terlihat publik.

## Cara membacanya (aturan, bukan saran)

**Satu jendela = satu bucket `epoch // 3600`; ambil baris PERTAMA bucket itu.** Baris tambahan dalam
jam yang sama adalah duplikat dari jalankan-sekali manual, bukan sampel. Per 22 Sep: **23 baris,
13 jendela** — mengutip 23 sebagai n berarti menggelembungkan cakupan ±76%.

Aturan dedupe ini sengaja tidak diperhalus menjadi "ambil baris paling lengkap". Memilih baris
berdasarkan seberapa bagus isinya adalah selection bias, dan itu lubang yang sama persisnya kami
temukan di kode rujukan (`_revalidate` mengembalikan edge terbaik-moment-ini tanpa cek identitas).
Kami kehilangan satu jendela data sebagai harganya; itu harga yang benar.

## Skema

| Penanda | Arti |
|---|---|
| tanpa `schema` (11 baris pertama) | semantik lama: field `volume` belum dinormalkan ⇒ veto `trending_without_demand` **tidak jalan** untuk baris GMGN; belum ada `blind_spots`/`fully_evaluated`; string API belum disanitasi. **Kecualikan dari analisis tren.** |
| `schema: 2` | tiga perbaikan di atas masuk |
| `schema: 3` | + veto `not_a_choosable_asset` (base stablecoin/major) dan + kolom `price_usd` untuk baris pool. **`survivable_count` lintas skema tidak sebanding.** |

## Baris yang salah label, dan tidak akan disunting

`2026-09-22T07:48:07Z` bertanda `schema: 2` padahal isinya skema 3 (veto stablecoin sudah aktif —
buktinya `survivable_count` turun 17 → 13 tanpa perubahan sumber data). Sebabnya: proses perekam
diimpor **sebelum** nomor skema dinaikkan, dan `schema` dibaca saat impor, bukan saat penulisan.

Barisnya **dibiarkan**. Menyunting file append-only untuk memperbaiki label adalah cara tercepat
mengubah bukti menjadi sesuatu yang tidak bisa dipercaya siapa pun.

**Aturan yang lahir dari ini:** kalau kode penghasil data diubah, restart prosesnya, atau jangan
naikkan penanda versi di tengah proses hidup. Yang dieksekusi adalah salinan di memori, bukan yang
ada di disk.

## Sumber data yang hidup dari mesin ini

| Sumber | Status | Yang diberikan |
|---|---|---|
| `openapi.gmgn.ai/v1/market/rank?chain=bsc` | ✅ 200 | 50 kandidat + **field perilaku**: `bundler_rate`, `sniper_count`, `smart_degen_count`, `rug_ratio`, `top_10_holder_rate`, `lock_percent`, `is_honeypot`, `holder_count`, `liquidity`, `price` (94 field unik). Butuh header `X-APIKEY`. |
| `api.geckoterminal.com/.../trending_pools`, `new_pools` | ✅ 200 | 40 pool/window: umur, `reserve_in_usd`, `volume_usd.h24`, `base_token_price_usd` |
| `api.gopluslabs.io/api/v1/token_security/56` | ✅ 200 | 34 field keamanan token, nol auth |
| `api.dexscreener.com/token-pairs/v1/bsc/{addr}` | ✅ 200 | harga + likuiditas lintas DEX, nol auth |
| Hyperliquid `POST /info {"type":"metaAndAssetCtxs"}` | ✅ 200 | **234 perp**, funding + OI per aset, keyless. BNB: OI 65.047, funding 0,004781%/jam |
| `scanner.tradingview.com/global/scan` | ✅ 200 | `Recommend.All` 1H/1D untuk `BINANCE:BNBUSDT`, `BITGET:BNBUSDT.P` dkk. **Tidak terblokir** (host-nya TradingView), tapi datanya bersumber CEX |
| GDELT DOC API | 🟡 429 | **butuh pacing 1 request / 5 detik** — bukan blokir. Satu-satunya jalur narasi politik/regulasi tanpa API key yang kita temukan |
| CoinGecko `/search/trending`, `/global`, `/coins/binancecoin` | ✅ 200 | perhatian lintas chain, konteks pasar, sentimen komunitas |
| `api.alternative.me/fng`, CoinDesk RSS | ✅ 200 | rezim sentimen; headline berita |
| Bitget · Binance (spot & fapi) · OKX · Bybit | ❌ | **semua** kena intersepsi TLS jaringan lokal (`CERTIFICATE_VERIFY_FAILED`; `web_fetch` → altnames `*.ioh.co.id`). Jangan menaruh apa pun di jalur kritis yang bergantung padanya |
| CryptoPanic tanpa key | ❌ 403 | butuh akun |
| `api.bscscan.com` V1 · Etherscan V2 `chainid=56` | ❌ deprecated / Paid Tier Only | **kecualian**: source code + ABI + verification tetap gratis di semua chain |

## Kohort yang belum terukur

"lolos semua veto" saat ini **tidak punya hasil forward sama sekali**, karena baris pool baru
menyimpan harga sejak jendela 08:00Z. Perbandingan pertama baru mungkin mulai jendela
**09:00Z**, dan yang layak disebut perbandingan butuh harian, bukan per-jam.

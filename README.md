# TradingAgent — agen trading yang bisa diaudit (T01)

Jalur **AI Agents / Agentic Trading**. Folder ini sengaja terpisah dari `app/` (produk kredensial
Lencana) dan dari `AgenticTrack/` (lapisan agen Lencana: menilai → menerbitkan). Mencampur
eksperimen ke repo produk membuat riwayat commit — yang justru jadi bukti orisinalitas — sulit
dibaca.

## Isi sekarang, dan status tiap bagian

| Bagian | Status | Buktinya |
|---|---|---|
| `contracts/DecisionAnchor.sol` | ✅ ada | dikompilasi Solc 0.8.26 di mesin ini |
| test suite-nya | ✅ **21 lulus, 0 gagal** | `forge test -vv` (2 fuzz @256 runs) — bukan angka dari catatan, tapi keluaran dijalankan |
| `script/Deploy.s.sol` | ⬜ ditulis, **belum pernah dijalankan** | butuh `DEPLOYER_PRIVATE_KEY`; tidak ada address publik dari folder ini |
| lapisan seleksi memecoin | ⬜ belum ada kode | sumber datanya sudah dikoleksi, lihat di bawah |
| loop keputusan (data → nilai → anchor) | ⬜ belum ada kode | — |
| model keputusan (Jev / LLM lain) | ⬜ belum diuji | akses & harga belum terverifikasi primer |

## Kenapa berupa kontrak, bukan self-send ber-calldata

Praktik yang sudah ada (HeliQuant, `onchain_recorder.py:110-118`) meng-anchor hash sebagai
**transaksi self-send 0-value**: valid sebagai bukti keberadaan, tapi **tidak memancarkan event**,
jadi tidak bisa di-indeks dan tidak bisa diaudit lewat query. Yang bisa dilakukan juri hanyalah
mencari-cari di halaman explorer. `DecisionAnchor` memancarkan `Anchored` dengan `id` dan `agent`
**ter-indexed** — roster dan hitungan bisa dibaca dari log. Test `test_event_dipancarkan_dengan_id_dan_agent_terindexed`
menegaskannya lewat `recordLogs()`, bukan lewat harapan.

## Dua aturan yang ditegakkan kontrak, bukan oleh niat baik

1. **`snapshotHash` wajib ada.** Tiap keputusan harus bisa ditunjuk dasar data point-in-time-nya.
   Tanpa aturan ini, "agen kami memprediksi X" selalu bisa dibela setelah tahu hasilnya.
   Snapshot yang dimaksud: `../_research/universe/bsc-universe.jsonl` — satu baris per jam,
   append-only, masing-masing sudah membawa `sha256` kanonik dengan konvensi yang sama
   (`json.dumps(sort_keys=True, separators=(",",":"))` → 32 byte), jadi nilainya langsung bisa
   masuk `bytes32` tanpa lapisan adapter.
2. **`ABSTAIN` wajib membawa `gatesHash`.** Menolak tanpa mencatat alasan bukan penolakan — itu
   cuma tidak melakukan apa pun, dan tidak bisa dibedakan dari agen yang mati. Ini alasan
   `AbstainWithoutReason` ada di kontrak, bukan di aplikasi: kalau pelanggannya bisa dilewati dari
   satu jalur, ia bukan aturan.

Plus satu rem: `setAgentActive(agent,false)` mencabut kewenangan agen **on-chain**, dan agen yang
dicabut langsung revert saat mencoba mencatat (`test_agen_yang_dicabut_tidak_lagi_bisa_mencatat`).
Itu jawaban langsung untuk pertanyaan "bagaimana kalian menghentikan agen yang menyimpang" —
bisa didemokan sampai revert, bukan dijanjikan di slide.

Dan satu batasan desain yang perlu disebut: `anchor()` hanya boleh dipanggil **agen terdaftar yang
aktif**. Owner bisa mendaftarkan dan mencabut, tapi **tidak punya jalur untuk menyisipkan keputusan
atas nama agen** (`test_owner_tidak_punya_jalan_pintas_mencatat_atas_nama_agen`). Pendaftaran pun
berevent, jadi jalur itu tidak senyap.

## Yang TIDAK dibuktikan kontrak ini — dan tidak boleh diklaim membuktikannya

Ia membuktikan **keberadaan, keutuhan, penanda tangan, dan urutan waktu** sebuah catatan. Ia
**tidak** membuktikan bahwa keputusan itu benar, menguntungkan, atau benar-benar dihasilkan model
yang disebutkan. Bukti asal-usul komputasi butuh verifiable inference (TEE/zkML), dan padanannya
tidak tersedia di chain ini. Kata terlarang di proyek ini dan tetap terlarang di sini:
*"trustless validation"*, *"zkML-verified"*, *"TEE-verified"*, angka return/win-rate/backtest apa pun,
dan klaim reputasi yang belum terbukti.

## Kenapa tidak ada kode HeliQuant di sini

Sama seperti `AgenticTrack/`: HeliQuant adalah core product jadi yang sudah disubmit ke hackathon
lain di chain lain, sementara FAQ #08 mensyaratkan core product **baru dan dibangun selama periode
acara**. Yang dibawa hanyalah pola yang tidak pernah menjadi miliknya: gerbang yang bisa menolak,
kejujuran sebagai fitur, dan ticket ter-hash. Tidak ada modul, prompt, atau skema yang disalin.

## Cara menjalankan

```
forge build
forge test -vv
```

`lib/forge-std` dan `node_modules/@openzeppelin` di folder ini adalah **junction** ke punyanya
`app/`, bukan salinan — konvensi yang sama dipakai `AgenticTrack` saat mengimpor `app/signer`.
Alasannya satu: kalau ada yang berubah, hanya ada satu tempat untuk berubah. Karena itu `.gitignore`
mengecualikan keduanya; clone baru perlu recreate junction-nya.

`foundry.toml` mewarisi `solc 0.8.26` + `evm_version shanghai`, dengan `[profile.fork]` terpisah
ber-`cancun`: fork test **wajib** jalan pada profil itu, atau pemanggilan kontrak pihak ketiga
yang butuh `blobhash`/`mcopy` akan mati dengan `EvmError: NotActivated`. `bsc-dataseed.binance.org`
dan `data-seed-prebsc-1-s1/-s2` dicatat rewel dari mesin ini — pilih endpoint hidup dengan
`python ../_research/find_bsc_testnet_rpc.py`.

## Langkah berikutnya

1. Lapisan seleksi di atas data yang sudah terkumpul — deterministik, menolak dulu, baru menilai
   (lihat ambang + alasannya di `_research/universe/README.md`).
2. Loop keputusan yang memanggil `anchor()` dari chain 97 dan menyimpan `decisionHash` kanonik
   untuk tiap catatan, supaya klaim "hash ini memang keputusan itu" bisa diperiksa orang lain.
3. Deploy sungguhan + source verification (source code tetap gratis di BscScan, walau Etherscan V2
   untuk BSC berbayar).

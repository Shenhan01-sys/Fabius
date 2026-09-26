---
type: build-log
status: verified-on-chain
verified: 2026-09-24
chain: bsc-testnet-97
---

# 07 — Deploy pertama di chain 97 (terverifikasi dari keadaan chain)

Diprogram 24 Sep 2026. Semua angka di bawah **dibaca kembali dari RPC** oleh
`tools/verify_deploy.py`, bukan dari keluaran `forge script`.

## Address & identitas

| | |
|---|---|
| `DecisionAnchor` | **`0xdd162afb5f5f92d5092f845a93660e3b38259330`** |
| Explorer | https://testnet.bscscan.com/address/0xdd162afb5f5f92d5092f845a93660e3b38259330 |
| chainId | 97 (`eth_chainId` = `0x61`) |
| bytecode | **4748 byte di chain = 4748 byte hasil build lokal (identik)** |
| owner | `0xfBb5A22A78C2815064740588d4d7d9671AE3aCf3` (burner khusus Fabius, cocok dengan `owner()`) |
| agen | `0x4bb30E3b3bc22082c1935fE3bE7c07448e69c862` — kunci TERSENDIRI, saldo testnet sendiri |

Burner Fabius **tidak** memakai wallet Lencana; didanai 0,006 tBNB lewat transfer testnet dari
tower `0xAEc63F6c…` (bukan faucet: faucet resmi menuntut saldo mainnet, QuickNode menuntut
bot-check manusia). Kunci di `Fabius/.deployer.env` + `.agent.env`, keduanya `gitignore`, tidak
pernah tercetak.

## Yang dibuktikan di chain, satu per satu

| # | Bukti | Angka dari chain |
|---|---|---|
| 1 | kontrak ada | `eth_getCode` = 4748 byte |
| 2 | ownership benar | `owner()` == deployer |
| 3 | agen terdaftar | `getAgent()` → handler `…8e69c862`, `active=True`, `registeredAt=1790237627`; `registerAgent` gas **138.736** |
| 4 | keputusan ter-anchor | `anchor(ABSTAIN)` dari **agen** (bukan owner): `status=1`, gas **302.011**, blok 132869554 |
| 5 | **event bisa di-indeks** | `Anchored` = 3 topic; `topic1` = id, `topic2` = alamat agen → **cocok dengan pengirim: YA** |
| 6 | keterikatan data | `getAnchor(id)` retur 320 byte, **`snapshotHash` asli dari `bsc-universe.jsonl` ikut tersimpan: YA** |
| 7 | hitungan | `anchorCount()` 0 → 1; `countByVerdict` Enter=0 / Abstain=1 |
| 8 | **REM bekerja** | setelah `setAgentActive(false)`: `anchor()` → `status=0` (revert). Setelah relist: `status=1`, gas 250.639 → pulih |
| 9 | guard lain | panggilan sebelum agen terdaftar juga revert (`NotAnAgent`) — terlihat sebagai tx gagal di explorer, bukan hilang |

## Biaya nyata (yang membuat klaim "murah" sekarang punya angka)

| Operasi | gas | ≈ tBNB @1 gwei |
|---|---|---|
| `registerAgent` | 138.736 | 0,000139 |
| `anchor()` pertama (storage dingin) | **302.011** | 0,000302 |
| `anchor()` sesudahnya (slot hangat) | 250.639 | 0,000251 |
| transfer biasa | 21.000 | 0,000021 |

**Pelajaran yang dicatat karena mahal:** `anchor()` memakai **302.011** gas; percobaan pertama
kuberi plafon **300.000** dan gagal dengan `status=0` + gas terpakai **persis 300.000** — itu
**out-of-gas**, bukan penolakan logika. Dua hal yang bentuknya mirip di log dan artinya berbeda;
yang membedakan adalah "gas terpakai == gas plafon".

## Cara menjalankan ulang (siapa pun, dari clone)

```
git clone https://github.com/Shenhan01-sys/Fabius && cd Fabius
git submodule update --init --depth 1
mklink /J lib\forge-std              ..\app\lib\forge-std        # atau pakai vendor/ seperti Actions
mklink /J node_modules\@openzeppelin ..\app\node_modules\@openzeppelin
forge test -vv                                     # 21 lulus
python tools\verify_deploy.py                       # baca ulang dari chain 97
```

`ANCHOR_ADDRESS=0xdd162afb5f5f92d5092f845a93660e3b38259330` bisa di-set kalau tidak mau membaca
`broadcast/`. Skrip ini mengirim tx testnet nyata dan memindahkan tBNB; tidak ada mainnet,
tidak ada order, tidak ada dana sungguhan.

## 25 Sep — keputusan SUNGGUHAN masuk chain (bukan hash uji)

`tools/anchor.py` (baru) membaca `decisions/direction-*.jsonl` dan mengirim apa adanya, lalu
membaca ulang `getAnchor(id)` dan membandingkan word per word. **Batch pertama** (7 baris, di atas
snapshot universe `2026-09-24T14:10:36Z`; dikirim 19:03–19:05Z):

| | |
|---|---|
| `anchorCount()` | **2 → 9** (7 dikirim, 7 cocok word-per-word dengan file lokal) |
| komposisi | `Enter=1` (MARSCOINUSDT short) · `Abstain=8` |
| blok | 132955005, 132955013, 132955022, 132955030, 132955038, 132955046, 132955056 |
| gas per anchor | 247.987 – 250.795 (semua di bawah plafon 1.000.000 → bukan out-of-gas) |
| biaya batch | ≈ 0,0018 tBNB @1 gwei; saldo agen 0,001085 → **0,013085** setelah transfer testnet 0,012 dari tower (`_research/topup_agent.py`, tx `0xc759fa66…` status=1) |

**Batch kedua** (4 baris, di atas snapshot segar `2026-09-24T19:06:58Z`; dikirim 19:07–19:09Z):

| aset | verdict | side | gas | blok |
|---|---|---|---|---|
| MARSCOINUSDT@perp | **ENTER** | short | 230.899 | 132955788 |
| GENIUSUSDT@perp | ABSTAIN | flat | 250.783 | 132955797 |
| TACUSDT@perp | ABSTAIN | flat | 250.759 | 132955805 |
| ASTEROIDUSDT@perp | ABSTAIN | flat | 250.807 | 132955813 |

Keadaan chain sesudah dua batch: **13 anchor = `Enter=2` / `Abstain=11`**, saldo agen
0,013085 → **0,011333 tBNB**. `MARSCOINUSDT` dua kali bukan duplikat yang lolos guard, melainkan
dua keputusan pada dua snapshot berbeda (14:10Z dan 19:06Z) — `_decisionSeen` justru menjamin satu
`decisionHash` tidak dihitung dua kali.

Yang membuat halaman ini bukan sekadar angka: **9 dari 11 keputusan arah** adalah **penolakan**
(`flat`/`unassessable`) dan tetap dikirim. (Di chain totalnya 13 anchor / 11 `Abstain` — sisanya 2
anchor dari `verify_deploy.py`, yang itu memang hash uji, dan tidak dicampur di sini.) Jejak yang
hanya berisi keputusan berani bisa
ditulis setelah hasilnya diketahui; jejak yang menyimpan `ABSTAIN` dengan alasan yang di-hash
(`gatesHash`) tidak bisa.

**Koreksi yang dicatat karena mahal:** kedua batch di atas mencetak `chain==lokal: YA` sambil
field `asset` terbaca **sampah** oleh parser kita — offset string pada retur dinamis dihitung
relatif ke AWAL STRUCT, bukan ke awal retur. Tiga hash memang cocok, jadi tidak ada klaim yang
salah arah; tapi kalimat "chain == lokal" lebih luas dari yang dibandingkan. Ketahuan oleh
`tools/test_decode_anchor.py` (13/13 setelah perbaikan), bukan oleh layar.

Sejak itu `anchor.py --verify` membandingkan **agen + asset + verdict + tiga hash**, dan caranya
tidak butuh kunci maupun gas: `id` anchor dihitung ulang dari hash di file
(`keccak256(abi.encode(agen, decisionHash, snapshotHash, chainid))`), lalu `getAnchor(id)` dibaca.
Hasil 25 Sep: **11/11 cocok**, `anchorCount()` chain = 13 (11 keputusan + 2 hash uji
`verify_deploy.py`). Efek samping yang berguna: rumus `id` kontrak terkonfirmasi oleh PERILAKU
(bacaan salah akan mengembalikan nol), bukan oleh tebakan.

Dua guard yang dipasang karena kegagalannya sudah pernah terjadi di repo ini:
- **saldo diperiksa sebelum tx pertama**, dihitung pada PLAFON gas × jumlah baris (bukan rata-rata)
  → siklus yang kurang dana berhenti tanpa mengirim apa pun, jadi tidak pernah ada jejak setengah;
- **`chainId` dibaca ulang dan dibandingkan dengan config sebelum menandatangani** → kegagalan
  yang dicegah adalah menandatangani tx untuk chain yang tidak kita baca.

## 26 Sep — pembayaran x402 yang PERTAMA kali terjadi, di chain 97 yang hidup

Bukan fork test, bukan catatan di atas kertas: sebuah agen nyata meminta, menerima `402`,
menandatangani, dan uangnya pindah di proxy kanonis.

| | |
|---|---|
| token (demo, milik kami) | `0xB11D90214089684081F57A03d3300E20725297f8` · create `0x6c16ad8b…` · code 4.002 byte |
| tx settlement | [`0xb6093e597530214e92b67d44a02f1aeb833bd7881e40eac5e64c5840347062d0`](https://testnet.bscscan.com/tx/0xb6093e597530214e92b67d44a02f1aeb833bd7881e40eac5e64c5840347062d0) — `status=1`, **gas 114.930**, blok 133.285.597, 3 log |
| tagihan | 1.000 atomic (= 0,001) jaringan `eip155:97`, scheme `exact`, `payTo` = agen |
| saldo pembeli | 5.000.000 → **4.999.000** atomic (hilang tepat seukuran tagihan) |
| saldo `payTo` | 999.990,001 token = 1.000.000 − 10 (dua pendanaan 5-token, satu di antaranya salah alamat) **+ 0,001** ✓ rekonsiliasi |
| gas | **ditanggung fasilitator (server)**; dompet klien berisi 0 BNB dan tidak pernah mengirim transaksi |
| alat | `tools/x402_deploy.py`, `tools/x402_gate.py` (server = fasilitator), `tools/x402_client.py` (agen pembayar) |

Yang membuat angka ini bukan klaim: `status`, gas, dan `balanceOf` dibaca ulang dari
`eth_getTransactionReceipt` / `eth_call`, bukan dari log server kami. Server boleh bohong;
rantai tidak.

### Dan satu penyebab kegagalan yang tidak akan ketemu dari pesan error

Setelah calldata benar, settlement tetap `revert` tanpa data. Yang salah: **`validAfter` memakai
jam laptop**, sementara proxy menolak kalau `block.timestamp < validAfter` — jam mesin ini
beberapa detik di depan kepala chain. Test Solidity kami **tidak mungkin** menangkap ini karena ia
memakai `block.timestamp` sebagai sumber waktu, jadi keduanya "benar" di dunianya masing-masing
sampai disatukan di jaringan sungguhan. Perbaikan: `validAfter = now - skew` (`X402_SKEW`, default
15 detik) — dan itu bukan trik, itu konsekuensi logis dari memakai jam dua sistem yang berbeda.

Cara mengulang (nol dana nyata): `python tools/x402_deploy.py` → `python tools/x402_gate.py
--port 8046` → `python tools/x402_client.py --base http://127.0.0.1:8046`.

## RPC: dua hal yang kelihatan sama tapi berbeda (terukur 25 Sep)

Alat verifikasi kita sempat "membalas lambat/mati" dan penyebabnya DUA cacat terpisah, keduanya
di sisi kita, bukan di chain:

1. **Cloudflare error 1010 = klien diblokir berdasarkan signature-nya.** `urllib` default
   (`Python-urllib/3.x`) mendapat **403** dari `bsc-testnet.drpc.org` dan kedua endpoint
   publicnode; dengan `User-Agent` apa pun (browser ATAU `curl/8.4.0`) responsnya **200**. Jadi
   "RPC mati" yang kami lihat sebenarnya permintaan tanpa UA. Diukur oleh
   `_research/probe_rpc_reject.py` / `probe_rpc_methods.py`.
2. **`Fabius/.env` masih memaku `RPC_URL` ke `data-seed-prebsc-1-s2.binance.org:8545/` yang sudah
   pensiun** (timeout 24 s di SEMUA metode). Setelah rotasi endpoint dipasang, satu
   `eth_getBalance` masih makan **22,93 s**: rotasi buta mulai dari indeks 0 = mulai dari yang
   mati, SELAPAS kali. Perbaikannya bukan cuma ganti endpoint (kini `https://bsc-testnet.drpc.org`),
   tapi membuat rotasinya **beringatan**: endpoint yang gagal masuk `_BAD` dan tidak dicoba lagi
   di proses itu, dan panggilan berikutnya mulai dari yang terakhir berhasil.

Dua pelajaran yang lebih umum dari RPC: (a) jangan menyimpulkan "server mati" dari status 403 —
baca kode dan body-nya; (b) error JSON-RPC (`execution reverted`, hash tak dikenal) adalah
**jawaban**, bukan kegagalan jaringan, jadi tidak boleh menurunkan endpoint ke daftar mati —
kalau dicampur, satu `getAnchor` salah alamat membuat RPC kita terlihat mati.

## Batas yang tetap berlaku setelah deploy ini

Yang terbukti: keberadaan, keutuhan, penanda tangan, urutan waktu, dan bahwa rem on-chain bekerja.
Yang **tetap tidak** terbukti: bahwa keputusan itu benar, untung, atau dihasilkan model yang
disebutkan (`05-Belum-Terbukti.md`). Deploy ini tidak mengubah satu pun kalimat di sana.

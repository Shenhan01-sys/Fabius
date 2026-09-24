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

## Batas yang tetap berlaku setelah deploy ini

Yang terbukti: keberadaan, keutuhan, penanda tangan, urutan waktu, dan bahwa rem on-chain bekerja.
Yang **tetap tidak** terbukti: bahwa keputusan itu benar, untung, atau dihasilkan model yang
disebutkan (`05-Belum-Terbukti.md`). Deploy ini tidak mengubah satu pun kalimat di sana.

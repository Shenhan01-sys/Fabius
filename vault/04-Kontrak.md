# 04 — Kontrak

## `contracts/DecisionAnchor.sol` — apa yang ditegakkan, apa yang tidak

Ditegakkan **oleh kontrak**, jadi tidak bisa dilewati oleh pemanggil yang niat baik hari ini dan
lupa besok:

1. **`snapshotHash` wajib bukan nol** (`MissingSnapshot`). Sebuah keputusan harus bisa menunjuk
   data point-in-time yang memakainya. Ini alasan kenapa "prediksi kami tepat" tidak bisa ditulis
   mundur — kamu harus memilih snapshot sebelum hasilnya diketahui, dan snapshot itu sudah dihash.
2. **`ABSTAIN` wajib membawa `gatesHash`** (`AbstainWithoutReason`). Menolak tanpa mencatat alasan
   bukan penolakan, itu cuma tidak melakukan apa pun — dan keduanya tidak bisa dibedakan dari
   luar. Ini yang membuat panel "0 trade hari ini" bisa dipercaya.
3. **Hanya agen terdaftar yang aktif yang bisa mencatat** (`NotAnAgent`, `AgentInactive`), dan
   **owner tidak punya jalur untuk menyisipkan keputusan atas nama agen**. Owner bisa mendaftarkan
   dan mencabut — keduanya memancarkan event, jadi jalurnya tidak senyap.
4. **Satu keputusan tidak dihitung dua kali** (`DuplicateDecision`). Mencegah angka "jumlah
   keputusan" digelembungkan dengan replay.
5. **`id` deterministik**: `keccak256(abi.encode(agent, decisionHash, snapshotHash, block.chainid))`
   — ter-index, jadi roster dan hitungan bisa dibaca dari log tanpa perlu mempercakapi kami.
6. **Keamanan bisa dicabut on-chain** (`setAgentActive(false)` → panggilan berikutnya revert).
   Jawaban untuk "bagaimana kalian menghentikan agen yang menyimpang", dan bisa didemokan live.

## Yang TIDAK ditegakkan kontrak ini (dan jangan ditulis seolah-olah)

- Bahwa keputusan itu **benar**, **untung**, atau **dihasilkan model yang disebutkan**. Anchor
  membuktikan keberadaan, keutuhan, penanda tangan, urutan waktu. Bukan asal-usul komputasi.
- Bahwa `decisionHash` cocok dengan isi file keputusan tertentu — itu tanggung jawab lapisan
  kanonisasi di sisi agen. Kontrak hanya menerima 32 byte.
- Keadilan/koreksian: tidak ada challenge window, tidak ada arbiter, tidak ada stake. Bukan
  `ValidationRegistry` (yang memang tidak ada di chain mana pun), dan jangan disebut begitu.

## Sifat baca yang terukur (bukan yang diasumsikan)

`getAnchor(bytes32)` **tidak menjaga id tak dikenal**: pembacaan `mapping` biasa mengembalikan
struct NOL, bukan `revert`. Terukur 25 Sep lewat `tools/anchor.py --verify` — 4 keputusan yang
belum pernah dikirim ke chain terbaca sebagai `{agent: 0x0…0, asset: "", hashes: 0x0…0,
anchoredAt: 0}`.

Kenapa ini dicatat, karena ini jenis detail yang membuat verifier salah menyimpulkan: kalau alat
pemeriksaannya mencari *exception* untuk tahu "belum ada di chain", ia tidak akan pernah menemukannya,
dan setiap siklus baru akan terlihat seperti **bukti yang rusak** (BEDA) alih-alih **belum dikirim**.
Aturan yang dipakai sekarang: tiga keadaan — `cocok` / `BEDA` / `BELUM DI-ANCHOR` — dengan
"BELUM DI-ANCHOR" dikenali dari rantai yang seluruhnya nol. Bandingkan dengan `getAgent()` yang
**memang** punya guard (`UnknownAgent`), jadi asumsi "pembacaan kita revert" tidak bisa dipindah
dari satu view ke view lain.

## Versi kita vs praktik yang sudah ada

Praktik yang dipakai HeliQuant (`onchain_recorder.py:110-118`) meng-anchor hash sebagai
**self-send 0-value ber-calldata**, tanpa kontrak dan tanpa event. Itu sah sebagai
proof-of-existence, dan murah. Tapi yang bisa dilakukan juri pada self-send hanyalah
mencari-cari di explorer. Keputusan kita: **tetap pakai hash kanonik yang sama**
(`json.dumps(sort_keys=True, separators=(",",":"))` → sha256 → bytes32, jadi catatan lama
masih kompatibel), tapi catat lewat kontrak **ber-event dengan field ter-index**, karena
permukaan audit publik adalah produknya, bukan biaya gas.

## Biaya dan target

- Rantai target: **BSC testnet chain 97** (alasan: `bscscan.com` hanya mengindeks 56 dan
  `opbnb.bscscan.com` instance terpisah — kepastian baca > penghematan gas).
- Estimasi gas `anchor()` belum diukur; yang terukur dari proyek induk: self-send calldata
  ~21k gas di BSC, dan `attest()` di BAS 333.484 gas (fork chain 97). Jangan menyebut angka
  produksi sebelum `forge inspect` + tx nyata.
- Wajib `--evm-version cancun` untuk fork test (pelajaran `EvmError: NotActivated`).
- Source verification **gratis** di BscScan meski Etherscan V2 untuk BSC Paid-Tier-Only.

## Status deploy

`script/Deploy.s.sol` ada dan **belum pernah dijalankan**. Tidak ada address publik dari proyek
ini. Setelah deploy, klaim "live di testnet" baru boleh ditulis kalau terbukti dari **keadaan
chain**, bukan dari baris `SUCCESS` di log — pola `verify_deploy97.py` di repo induk.

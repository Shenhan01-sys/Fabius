// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ExecutionAnchor (P132, F-D96)
///
/// Catatan ISI ORDER di venue terpusat (Binance, Aster, ...) untuk sinyal yang sudah dikomit di SignalAnchor - satu event rinci per isi, terutama
/// order UANG NYATA (`real = true`). Kontrak lama `ExecutionVault` mencatat swap DEX di chain itu sendiri; yang ini mencatat apa yang terjadi di LUAR
/// chain, jadi ia tidak bisa membuktikan bahwa venue benar-benar mengisi order itu (balasan venue tidak bertanda tangan). Yang BISA ditegakkannya:
///
///  1. Pengikatan ke bukti: `commitId` harus komit SignalAnchor yang ADA, dan pelapor harus committer komit itu - eksekusi tidak bisa ditempel ke
///     sinyal orang lain atau ke sinyal yang tidak pernah disegel.
///  2. Urutan waktu (PRD R-E1 di chain): order yang MENGAKU dikirim sebelum `committedAt` komitnya ditolak (`SentBeforeCommit`), dan isi tidak boleh
///     lebih awal dari kirim. Klaim waktu tetap klaim pelapor - tetapi klaim yang melanggar urutan tidak bisa dicatat sama sekali.
///  3. Satu catatan per (pelapor, venue, clientOrderId): order yang sama tidak bisa dicatat dua kali dengan isi berbeda.
///  4. Tidak ada nilai nol yang berarti "tidak ada" (qty, harga, sisi).
///
/// Skala angka: qty, avgPrice, fee = nilai desimal x 1e8 (sama dengan hargaRef SignalAnchor). Waktu tSent/tFilled = milidetik UTC (jam venue).
/// `reportHash` = sha256 baris laporan lengkap di umpan/ledger eksekusi (`ledger/eksekusi/`), jadi event dan berkas bisa dicocokkan siapa pun.
interface ISignalAnchorView {
    struct Commit {
        address committer;
        uint64 asof;
        uint64 committedAt;
        uint32 n;
        uint32 revealed;
        bool missed;
        bytes32 botId;
        bytes32 specSha;
        bytes32 root;
    }

    function getCommit(bytes32 id) external view returns (Commit memory);
}

contract ExecutionAnchor {
    struct Fill {
        bytes32 commitId;       // komit SignalAnchor (bot, bar) yang memicu order ini
        bytes32 venue;          // ascii, mis. "binance-live" / "binance-demo"
        bytes32 symbol;         // ascii, mis. "XRPUSDT"
        bytes32 clientOrderId;  // id deterministik Fabius ("fx" + 30 hex = 32 karakter)
        uint64 venueOrderId;
        uint8 side;             // 1 = BUY, 2 = SELL
        bool real;              // true = uang nyata; false = demo/testnet
        uint64 tSent;           // ms
        uint64 tFilled;         // ms
        uint128 qty;            // x 1e8
        uint128 avgPrice;       // x 1e8
        uint128 fee;            // x 1e8, dalam feeAsset
        bytes32 feeAsset;       // ascii, mis. "USDT" / "BNB"
        bytes32 reportHash;     // sha256 baris laporan lengkap
    }

    ISignalAnchorView public immutable anchor;
    mapping(bytes32 => uint64) public recordedAt;   // key -> waktu blok; 0 = belum dicatat
    uint256 public fillCount;
    uint256 public realFillCount;

    event Executed(bytes32 indexed key, address indexed reporter, bytes32 indexed commitId, Fill fill, uint64 recordedAt);

    error ZeroValue();
    error BadSide(uint8 side);
    error UnknownCommit(bytes32 commitId);
    error NotCommitter(address reporter, address committer);
    error SentBeforeCommit(uint64 tSentSeconds, uint64 committedAt);
    error FilledBeforeSent(uint64 tSent, uint64 tFilled);
    error AlreadyRecorded(bytes32 key);

    constructor(ISignalAnchorView anchor_) {
        if (address(anchor_) == address(0)) revert ZeroValue();
        anchor = anchor_;
    }

    function keyOf(address reporter, bytes32 venue, bytes32 clientOrderId) public pure returns (bytes32) {
        return keccak256(abi.encode(reporter, venue, clientOrderId));
    }

    function record(Fill calldata f) public returns (bytes32 key) {
        if (f.commitId == bytes32(0) || f.venue == bytes32(0) || f.symbol == bytes32(0) || f.clientOrderId == bytes32(0) || f.qty == 0
            || f.avgPrice == 0 || f.tSent == 0) revert ZeroValue();
        if (f.side != 1 && f.side != 2) revert BadSide(f.side);
        ISignalAnchorView.Commit memory c = anchor.getCommit(f.commitId);
        if (c.committer == address(0)) revert UnknownCommit(f.commitId);
        if (c.committer != msg.sender) revert NotCommitter(msg.sender, c.committer);
        if (f.tSent / 1000 < c.committedAt) revert SentBeforeCommit(f.tSent / 1000, c.committedAt);
        if (f.tFilled < f.tSent) revert FilledBeforeSent(f.tSent, f.tFilled);
        key = keyOf(msg.sender, f.venue, f.clientOrderId);
        if (recordedAt[key] != 0) revert AlreadyRecorded(key);
        recordedAt[key] = uint64(block.timestamp);
        fillCount += 1;
        if (f.real) realFillCount += 1;
        emit Executed(key, msg.sender, f.commitId, f, uint64(block.timestamp));
    }

    /// Beberapa isi satu bar dalam satu transaksi; satu saja yang melanggar = seluruh batch ditolak (tidak ada catatan setengah).
    function recordBatch(Fill[] calldata fills) external returns (bytes32[] memory keys) {
        keys = new bytes32[](fills.length);
        for (uint256 i = 0; i < fills.length; i++) {
            keys[i] = record(fills[i]);
        }
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {MerkleProof} from "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";

interface ILockRegistry {
    function lockedAt(address locker, bytes32 botId, bytes32 specSha) external view returns (uint64);
}

/// @title SignalAnchor v2 (C-B, M3) - komit-ungkap sinyal per bot per bar
///
/// Yang masuk chain adalah KOMITMEN (akar Merkle atas semua sinyal satu bot pada satu bar), bukan sinyalnya. Isi sinyal tetap tertutup sampai
/// diungkap; pembeli memeriksa muatan + salt + bukti yang diterimanya terhadap akar di sini, jadi "sinyal ini sudah ada sebelum hasilnya" dan
/// "dua pembeli tidak diberi sinyal berbeda" bisa diperiksa, bukan dipercaya. Skema daun = `engine/sinyal.py`:
///   leaf = keccak256(abi.encode(Signal, salt)) dengan Signal = (uint8 v, bytes32 botId, bytes32 specSha, uint64 asof, bytes32 asset, uint8 aksi,
///          int256 bobotLama, int256 bobotBaru, uint256 hargaRef, bytes32 dataHash); pohon = pasangan terurut (OpenZeppelin `MerkleProof`).
///
/// Aturan yang ditegakkan kontrak (bukan niat):
///  1. Komit hanya untuk (botId, specSha) yang SUDAH dikunci oleh pengirim di `LockRegistry`, dan kuncinya tidak lebih baru dari bar yang dikomit
///     (spesifikasi tidak bisa dipilih sesudah melihat bar).
///  2. Komit hanya dalam `maxLag` detik sesudah penutupan bar (`asof`), dan tidak untuk bar yang belum tertutup: yang terlambat ditolak, bukan dicatat diam-diam.
///  3. Satu komit per (pengirim, botId, specSha, asof). Akar nol hanya untuk n = 0 ("bot diam pada bar ini" yang dikomit).
///  4. Pengungkapan diverifikasi terhadap akar; daun yang sama tidak dihitung dua kali. Sesudah `revealWindow`, siapa pun boleh menandai komit yang
///     tidak diungkap penuh sebagai TIDAK-DIUNGKAP - dan itu tercatat permanen (cara curang paling umum penjual sinyal: hanya membuka yang menang).
///
/// Yang TIDAK dibuktikan: bahwa sinyal bagus atau menguntungkan, atau bahwa harga referensinya bisa didapat. PnL dihitung ulang di luar chain dari
/// muatan yang terbuka (ledger paper, `engine.cli ledger verify`).
contract SignalAnchor {
    struct Signal {
        uint8 v;
        bytes32 botId;
        bytes32 specSha;
        uint64 asof;
        bytes32 asset;
        uint8 aksi;
        int256 bobotLama;
        int256 bobotBaru;
        uint256 hargaRef;
        bytes32 dataHash;
    }

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

    ILockRegistry public immutable registry;
    uint64 public immutable maxLag;
    uint64 public immutable revealWindow;

    mapping(bytes32 => Commit) private _commits;
    mapping(bytes32 => mapping(bytes32 => bool)) private _leafRevealed;
    bytes32[] private _ids;

    event Committed(bytes32 indexed id, address indexed committer, bytes32 indexed botId, bytes32 specSha, uint64 asof, bytes32 root, uint32 n);
    event Revealed(bytes32 indexed id, bytes32 indexed leaf, bytes32 asset, uint8 aksi, int256 bobotLama, int256 bobotBaru, uint256 hargaRef,
                   bytes32 dataHash, bytes32 salt);
    event RevealMissed(bytes32 indexed id, uint32 revealed, uint32 n);

    error ZeroValue();
    error NotLocked();
    error LockedAfterBar(uint64 lockedAt, uint64 asof);
    error BarNotClosed(uint64 asof, uint64 nowTs);
    error TooLate(uint64 asof, uint64 nowTs, uint64 maxLag);
    error AlreadyCommitted(bytes32 id);
    error EmptyMismatch();
    error UnknownCommit(bytes32 id);
    error SignalMismatch();
    error BadProof();
    error AlreadyRevealed(bytes32 leaf);
    error TooManyReveals();
    error WindowOpen(uint64 until);
    error NothingMissing();

    constructor(ILockRegistry registry_, uint64 maxLag_, uint64 revealWindow_) {
        if (address(registry_) == address(0) || maxLag_ == 0 || revealWindow_ == 0) revert ZeroValue();
        registry = registry_;
        maxLag = maxLag_;
        revealWindow = revealWindow_;
    }

    function commitId(address committer, bytes32 botId, bytes32 specSha, uint64 asof) public pure returns (bytes32) {
        return keccak256(abi.encode(committer, botId, specSha, asof));
    }

    function leafOf(Signal calldata s, bytes32 salt) public pure returns (bytes32) {
        return keccak256(abi.encode(s, salt));
    }

    function commit(bytes32 botId, bytes32 specSha, uint64 asof, bytes32 root, uint32 n) external returns (bytes32 id) {
        if (botId == bytes32(0) || specSha == bytes32(0) || asof == 0) revert ZeroValue();
        uint64 locked = registry.lockedAt(msg.sender, botId, specSha);
        if (locked == 0) revert NotLocked();
        if (locked > asof) revert LockedAfterBar(locked, asof);
        uint64 nowTs = uint64(block.timestamp);
        if (asof > nowTs) revert BarNotClosed(asof, nowTs);
        if (nowTs - asof > maxLag) revert TooLate(asof, nowTs, maxLag);
        if ((root == bytes32(0)) != (n == 0)) revert EmptyMismatch();
        id = commitId(msg.sender, botId, specSha, asof);
        if (_commits[id].committer != address(0)) revert AlreadyCommitted(id);
        _commits[id] = Commit({committer: msg.sender, asof: asof, committedAt: nowTs, n: n, revealed: 0, missed: false, botId: botId,
                               specSha: specSha, root: root});
        _ids.push(id);
        emit Committed(id, msg.sender, botId, specSha, asof, root, n);
    }

    /// Siapa pun yang memegang muatan + salt + bukti boleh mengungkap; yang diperiksa hanyalah kecocokan dengan akar yang dikomit.
    function reveal(bytes32 id, Signal calldata s, bytes32 salt, bytes32[] calldata proof) external {
        Commit storage c = _commits[id];
        if (c.committer == address(0)) revert UnknownCommit(id);
        if (s.botId != c.botId || s.specSha != c.specSha || s.asof != c.asof) revert SignalMismatch();
        if (c.revealed >= c.n) revert TooManyReveals();
        bytes32 leaf = keccak256(abi.encode(s, salt));
        if (!MerkleProof.verifyCalldata(proof, c.root, leaf)) revert BadProof();
        if (_leafRevealed[id][leaf]) revert AlreadyRevealed(leaf);
        _leafRevealed[id][leaf] = true;
        c.revealed += 1;
        emit Revealed(id, leaf, s.asset, s.aksi, s.bobotLama, s.bobotBaru, s.hargaRef, s.dataHash, salt);
    }

    /// Sesudah `asof + revealWindow`, komit yang belum diungkap penuh ditandai TIDAK-DIUNGKAP (permanen, terlihat di statistik).
    function markMissed(bytes32 id) external {
        Commit storage c = _commits[id];
        if (c.committer == address(0)) revert UnknownCommit(id);
        uint64 until = c.asof + revealWindow;
        if (block.timestamp <= until) revert WindowOpen(until);
        if (c.missed || c.revealed >= c.n) revert NothingMissing();
        c.missed = true;
        emit RevealMissed(id, c.revealed, c.n);
    }

    function getCommit(bytes32 id) external view returns (Commit memory) {
        return _commits[id];
    }

    function isRevealed(bytes32 id, bytes32 leaf) external view returns (bool) {
        return _leafRevealed[id][leaf];
    }

    function commitCount() external view returns (uint256) {
        return _ids.length;
    }

    function commitIdAt(uint256 index) external view returns (bytes32) {
        return _ids[index];
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// Meja AI 5 menit Fabius (P152, F-D109): satu Merkle root atas keputusan SEMUA agent untuk satu siklus 5 menit.
/// Root hanya diterima SELAMA siklusnya masih berjalan (cycleStart <= now < cycleStart + 300): keputusan yang diuji oleh harga di akhir siklus
/// sudah terkunci sebelum harga itu ada. Satu root per siklus, hanya dari `committer` (kunci gerbang), tanpa pemilik dan tanpa hak lain.
contract DeskAnchor {
    uint64 public constant CYCLE = 300;

    address public immutable committer;
    mapping(uint64 => bytes32) public rootOf; // cycleStart -> Merkle root keputusan

    event Cycle(uint64 indexed cycleStart, bytes32 root, uint16 n);

    error NotCommitter();
    error ZeroRoot();
    error BadCycle();
    error TooLate();
    error AlreadyCommitted();

    constructor(address committer_) {
        committer = committer_;
    }

    function commit(uint64 cycleStart, bytes32 root, uint16 n) external {
        if (msg.sender != committer) revert NotCommitter();
        if (root == bytes32(0) || n == 0) revert ZeroRoot();
        if (cycleStart % CYCLE != 0 || block.timestamp < cycleStart) revert BadCycle();
        if (block.timestamp >= cycleStart + CYCLE) revert TooLate();
        if (rootOf[cycleStart] != bytes32(0)) revert AlreadyCommitted();
        rootOf[cycleStart] = root;
        emit Cycle(cycleStart, root, n);
    }
}

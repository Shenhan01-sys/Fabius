// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title SelectionAnchor (P141, F-D102)
///
/// Agent analis - siapa pun yang punya identitas ERC-8004 di IdentityRegistry resmi - memilih SATU bot Fabius untuk satu bar harian, SEBELUM bar
/// itu ditutup. Bot yang dipilih menentukan posisi yang diikuti operator dari penutupan bar itu sampai penutupan berikutnya; jadi pilihan yang sah
/// selalu dibuat sebelum jendela hasilnya dimulai, dan tidak bisa diubah sesudahnya. Penilaian (return paper bot pilihan, dari ledger publik) dan
/// reputasi (ReputationRegistry ERC-8004) terjadi di luar kontrak ini. Agent tidak pernah membuat trade sendiri: ia hanya memilih di antara bot
/// yang aturannya terkunci (F-D70, F-D11).
///
/// Yang DITEGAKKAN:
///  1. Identitas: pengirim = dompet agen (`getAgentWallet`) atau pemilik token identitas (`ownerOf`) - pilihan tidak bisa diatasnamakan agent lain.
///  2. Waktu: `barClose` = penutupan bar harian (kelipatan 1 hari, 00:00 UTC), pengiriman harus SEBELUM `barClose`, paling jauh 2 hari ke depan.
///  3. Satu pilihan per (agentId, barClose): tidak bisa diganti sesudah melihat pergerakan harga.
///  4. Tidak ada nilai nol yang berarti "tidak ada" (bot, hash alasan); keyakinan 0..100.
/// `reasonHash` = sha256 JSON alasan lengkap yang diterbitkan agent (dicocokkan siapa pun dengan berkas yang diterbitkan).
interface IIdentityRegistry8004 {
    function ownerOf(uint256 agentId) external view returns (address);
    function getAgentWallet(uint256 agentId) external view returns (address);
}

contract SelectionAnchor {
    struct Pick {
        bytes32 botId;
        uint8 confidence;
        bytes32 reasonHash;
        uint64 committedAt;
    }

    uint64 public constant DAY = 1 days;
    uint64 public constant MAX_AHEAD = 2 days;

    IIdentityRegistry8004 public immutable identity;
    mapping(uint256 => mapping(uint64 => Pick)) internal _picks;   // agentId -> barClose -> pilihan
    mapping(uint256 => uint64[]) internal _bars;                    // agentId -> bar yang pernah dipilih (urut kirim)

    event Picked(uint256 indexed agentId, uint64 indexed barClose, bytes32 indexed botId, uint8 confidence, bytes32 reasonHash, address by);

    error ZeroValue();
    error BadConfidence();
    error BadBar();
    error TooLate();
    error NotAgent();
    error AlreadyPicked();

    constructor(IIdentityRegistry8004 identity_) {
        identity = identity_;
    }

    function pick(uint256 agentId, uint64 barClose, bytes32 botId, uint8 confidence, bytes32 reasonHash) external {
        if (botId == bytes32(0) || reasonHash == bytes32(0)) revert ZeroValue();
        if (confidence > 100) revert BadConfidence();
        if (barClose % DAY != 0 || barClose > block.timestamp + MAX_AHEAD) revert BadBar();
        if (block.timestamp >= barClose) revert TooLate();
        if (msg.sender != identity.getAgentWallet(agentId) && msg.sender != identity.ownerOf(agentId)) revert NotAgent();
        if (_picks[agentId][barClose].committedAt != 0) revert AlreadyPicked();
        _picks[agentId][barClose] = Pick(botId, confidence, reasonHash, uint64(block.timestamp));
        _bars[agentId].push(barClose);
        emit Picked(agentId, barClose, botId, confidence, reasonHash, msg.sender);
    }

    function getPick(uint256 agentId, uint64 barClose) external view returns (Pick memory) {
        return _picks[agentId][barClose];
    }

    function barCount(uint256 agentId) external view returns (uint256) {
        return _bars[agentId].length;
    }

    function barAt(uint256 agentId, uint256 i) external view returns (uint64) {
        return _bars[agentId][i];
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/// @title DecisionAnchor
///
/// Buku catatan append-only untuk keputusan agen. Satu baris = satu keputusan, dan baris itu
/// menyimpan HASH dari keputusan tersebut — bukan keputusannya. Isi lengkapnya (state pasar yang
/// dibaca, pertanyaan yang diajukan ke model, probabilitas tiap pilihan, gerbang yang menggugurkan)
/// hidup di luar chain dan tetap bisa dicocokkan siapa pun yang punya filenya.
///
/// Kenapa kontrak, bukan self-send 0-value ber-calldata seperti praktik yang lazim:
/// calldata telanjang tidak memancarkan event, jadi tidak ada yang bisa di-indeks. Explorer
/// menampilkan hash tanpa konteks, dan "coba cari sendiri transaksi yang cocok" bukan audit.
/// Event di sini ber-`indexed` supaya roster dan hitungan bisa dibaca dari log, bukan dari
/// halaman HTML.
///
/// Dua aturan yang ditegakkan oleh kontrak, bukan oleh niat baik:
///  1. `snapshotHash` wajib ada. Sebuah keputusan harus bisa ditunjuk sumber data point-in-time
///     yang dipakai saat ia dibuat. Tanpa ini, "agen kami memprediksi X" selalu bisa dibela
///     secara hindsight.
///  2. `ABSTAIN` wajib membawa `gatesHash`. Menolak dengan alasan yang tidak dicatat bukan
///     penolakan, itu cuma tidak melakukan apa pun.
///
/// Batas yang TIDAK dihapus kontrak ini, dan tidak boleh diklaim menghapusnya:
///  - Ia membuktikan keberadaan, keutuhan, penanda tangan, dan urutan waktu sebuah catatan.
///  - Ia TIDAK membuktikan bahwa keputusan itu benar, menguntungkan, atau benar-benar
///    dihasilkan model yang disebutkan. Bukti asal-usul komputasi butuh verifiable inference
///    (TEE/zkML), dan padanannya tidak tersedia di chain ini.
contract DecisionAnchor is Ownable {
    /// @notice Keputusan akhir sebuah agen atas satu aset pada satu snapshot.
    enum Verdict {
        Enter,
        Abstain
    }

    struct Agent {
        address handler;
        string label;
        bool active;
        uint96 registeredAt;
    }

    struct Anchor {
        address agent;
        string asset;
        Verdict verdict;
        bytes32 decisionHash;
        bytes32 gatesHash;
        bytes32 snapshotHash;
        uint64 anchoredAt;
    }

    mapping(address => Agent) private _agents;
    address[] private _agentRoster;

    mapping(bytes32 => Anchor) private _anchors;
    bytes32[] private _anchorIds;
    mapping(Verdict => uint256) private _verdictCount;
    mapping(address => uint256) private _agentCount;
    mapping(bytes32 => bool) private _decisionSeen;

    event AgentRegistered(address indexed agent, string label);
    event AgentStatusChanged(address indexed agent, bool active);
    event Anchored(
        bytes32 indexed id,
        address indexed agent,
        string asset,
        Verdict verdict,
        bytes32 snapshotHash,
        bytes32 gatesHash
    );

    error NotAnAgent();
    error AgentInactive();
    error AlreadyAnAgent();
    error UnknownAgent();
    error ZeroAgent();
    error EmptyLabel();
    error DuplicateDecision(bytes32 decisionHash);
    error MissingSnapshot();
    error MissingDecision();
    error AbstainWithoutReason();
    error EmptyAsset();

    constructor() Ownable(msg.sender) {}

    // ---------------------------------------------------------------- otoritas

    /// @notice Menetapkan alamat mana yang boleh mencatat keputusan untuk sebuah agen.
    /// @dev Hanya owner. Registrasi dan pencabutan KEDUANYA terekspos: owner bisa memutus agen
    ///      kapan saja (`setAgentActive(agent,false)`) dan itu jawaban untuk pertanyaan
    ///      "bagaimana kalian menghentikan agen yang menyimpang" — remnya on-chain, bisa
    ///      didemokan sampai revert, bukan janji di slide.
    function registerAgent(address agent, string calldata label) external onlyOwner {
        if (agent == address(0)) revert ZeroAgent();
        if (_agents[agent].handler != address(0)) revert AlreadyAnAgent();
        if (bytes(label).length == 0) revert EmptyLabel();
        _agents[agent] = Agent({handler: agent, label: label, active: true, registeredAt: uint96(block.timestamp)});
        _agentRoster.push(agent);
        emit AgentRegistered(agent, label);
    }

    function setAgentActive(address agent, bool active) external onlyOwner {
        if (_agents[agent].handler == address(0)) revert UnknownAgent();
        _agents[agent].active = active;
        emit AgentStatusChanged(agent, active);
    }

    // ---------------------------------------------------------------- pencatatan

    /// @notice Mencatat satu keputusan. Hanya agen aktif yang boleh memanggilnya sendiri —
    ///         owner tidak punya jalur untuk menyisipkan keputusan atas nama agen.
    /// @param asset  label aset (mis. "WBNB/USDT"); murni label, kunci tetap (agent, decisionHash)
    /// @param decisionHash keccak256 kanonik atas catatan keputusan agen (state, pertanyaan,
    ///        pilihan + probabilitas + confidence, model, sizing)
    /// @param gatesHash keccak256 atas log gerbang berurutan; wajib bukan nol untuk ABSTAIN
    /// @param snapshotHash keccak256 atas snapshot universe point-in-time yang jadi dasar keputusan
    function anchor(
        string calldata asset,
        Verdict verdict,
        bytes32 decisionHash,
        bytes32 gatesHash,
        bytes32 snapshotHash
    ) external returns (bytes32 id) {
        Agent memory a = _agents[msg.sender];
        if (a.handler == address(0)) revert NotAnAgent();
        if (!a.active) revert AgentInactive();
        if (bytes(asset).length == 0) revert EmptyAsset();
        if (decisionHash == bytes32(0)) revert MissingDecision();
        if (snapshotHash == bytes32(0)) revert MissingSnapshot();
        if (verdict == Verdict.Abstain && gatesHash == bytes32(0)) revert AbstainWithoutReason();
        if (_decisionSeen[decisionHash]) revert DuplicateDecision(decisionHash);

        id = keccak256(abi.encode(msg.sender, decisionHash, snapshotHash, block.chainid));

        _anchors[id] = Anchor({
            agent: msg.sender,
            asset: asset,
            verdict: verdict,
            decisionHash: decisionHash,
            gatesHash: gatesHash,
            snapshotHash: snapshotHash,
            anchoredAt: uint64(block.timestamp)
        });
        _anchorIds.push(id);
        _decisionSeen[decisionHash] = true;
        _verdictCount[verdict] += 1;
        _agentCount[msg.sender] += 1;

        emit Anchored(id, msg.sender, asset, verdict, snapshotHash, gatesHash);
    }

    // ---------------------------------------------------------------- baca

    function agents() external view returns (address[] memory) {
        return _agentRoster;
    }

    function getAgent(address agent) external view returns (Agent memory) {
        return _agents[agent];
    }

    function anchorCount() external view returns (uint256) {
        return _anchorIds.length;
    }

    function anchorIdAt(uint256 index) external view returns (bytes32) {
        return _anchorIds[index];
    }

    function getAnchor(bytes32 id) external view returns (Anchor memory) {
        return _anchors[id];
    }

    /// @notice Hitungan per verdict. `Abstain` yang jauh melebihi `Enter` bukan angka memalukan —
    ///         itu produknya, dan ia bisa dibaca dari log tanpa perlu mempercakapi kami.
    function countByVerdict(Verdict verdict) external view returns (uint256) {
        return _verdictCount[verdict];
    }

    function countByAgent(address agent) external view returns (uint256) {
        return _agentCount[agent];
    }
}

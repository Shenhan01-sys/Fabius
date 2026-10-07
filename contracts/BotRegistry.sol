// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Ownable, Ownable2Step} from "@openzeppelin/contracts/access/Ownable2Step.sol";
import {Clones} from "@openzeppelin/contracts/proxy/Clones.sol";
import {ILockRegistry} from "./SignalAnchor.sol";
import {RevenueSplitter} from "./RevenueSplitter.sol";

/// @title BotRegistry (C-H, P81) - daftar bot program penerbit + pabrik `RevenueSplitter` per bot
///
/// `botId -> (penerbit, specSha, splitter, status)`, status = SHADOW / AKTIF / TERGUSUR / PENSIUN (vault/08-Backlog/07 - Epik Kolaborasi Bot
/// Terbuka §8, epik 06 §3 C-H).
/// Identitas on-chain hanya alamat dompet; kontak dan data pribadi tidak pernah masuk ke sini (UU PDP). Operator = pemilik (Ownable2Step) =
/// alamat Fabius; pemilik yang sama adalah "Fabius" bagi setiap splitter (boleh menurunkan bagian Fabius dan mengganti dompet Fabius).
///
/// Aturan yang ditegakkan kontrak (bukan niat):
///  1. Pendaftaran hanya untuk (botId, specSha) yang SUDAH dikunci `anchorer` di `LockRegistry` (tahap S1), dan kuncinya tidak lebih baru dari
///     laporan peninjau yang dirujuk (spesifikasi dikunci sebelum evaluasi, bukan sesudah melihat hasil).
///  2. SETIAP transisi status (termasuk pendaftaran = NONE -> SHADOW) menunjuk laporan yang sudah di-pin `anchorer` di `LockRegistry`:
///     `lockedAt(anchorer, reportLabel, reportSha) != 0`. Label + sha ikut event, jadi siapa pun bisa mencari laporan itu dan menghitung
///     ulang keputusannya. Kontrak tidak membuktikan isi laporan benar - hanya bahwa laporan itu sudah publik sebelum transisi.
///  3. Transisi yang diizinkan didefinisikan eksplisit (`isAllowed`); PENSIUN final. Status tidak pernah menyentuh splitter: keluar dari slot
///     hanya menghentikan tawaran `payTo` baru (di luar chain), saldo yang sudah masuk tetap dibayar keluar.
///  4. Alamat splitter = CREATE2 klon EIP-1167 dengan salt = keccak256(abi.encode(botId, issuer, issuerPayee, specSha)): alamat yang ditawarkan
///     gerbang x402 SEBELUM pendaftaran mengikat penerbit, dompet payout, dan spesifikasinya - pemilik tidak bisa memasang klon di alamat itu
///     untuk penerbit lain. Rumus yang sama di Python: `engine/splitter.py`.
///  5. `deploySplitter` tanpa izin (USULAN, di luar teks epik): siapa pun bisa memasang klon untuk parameter yang mengikat alamatnya, jadi uang
///     yang dibayar ke alamat prediksi tidak pernah bergantung pada kemauan pemilik untuk mendaftarkan bot itu.
contract BotRegistry is Ownable2Step {
    enum Status {
        NONE,
        SHADOW,
        AKTIF,
        TERGUSUR,
        PENSIUN
    }

    struct Bot {
        address issuer;
        Status status;
        uint64 registeredAt;
        uint64 changedAt;
        address splitter;
        bytes32 specSha;
        bytes32 reportLabel;     // pin laporan untuk transisi terakhir: LockRegistry (anchorer, reportLabel, reportSha)
        bytes32 reportSha;
    }

    uint16 public constant BPS = 10_000;

    address public immutable implementation;     // RevenueSplitter yang di-klon; dipasang konstruktor ini sendiri
    ILockRegistry public immutable locks;
    uint16 public immutable initialFabiusBps;    // bagian Fabius awal tiap splitter (v1: 4000 = 40 %, F-D72/F-D73); sesudahnya hanya turun
    address public anchorer;                     // alamat yang pin-nya di LockRegistry dihitung (committer M3)
    address public fabiusPayee;                  // dompet Fabius untuk splitter BARU; splitter lama diganti lewat splitter itu sendiri

    mapping(bytes32 => Bot) private _bots;
    bytes32[] private _ids;

    event Registered(bytes32 indexed botId, address indexed issuer, address indexed splitter, bytes32 specSha);
    event StatusChanged(bytes32 indexed botId, Status indexed from, Status indexed to, bytes32 reportLabel, bytes32 reportSha);
    event SplitterDeployed(bytes32 indexed botId, address indexed splitter, address indexed issuer, address issuerPayee, bytes32 specSha);
    event AnchorerChanged(address indexed oldAnchorer, address indexed newAnchorer);
    event FabiusPayeeChanged(address indexed oldPayee, address indexed newPayee);

    error ZeroValue();
    error BadBps(uint16 bps);
    error AlreadyRegistered(bytes32 botId);
    error UnknownBot(bytes32 botId);
    error SpecNotLocked(bytes32 botId, bytes32 specSha);
    error ReportNotAnchored(bytes32 reportLabel, bytes32 reportSha);
    error SpecLockedAfterReport(uint64 specLockedAt, uint64 reportLockedAt);
    error BadTransition(Status from, Status to);

    constructor(address owner_, ILockRegistry locks_, address anchorer_, address fabiusPayee_, uint16 initialFabiusBps_) Ownable(owner_) {
        if (address(locks_) == address(0) || anchorer_ == address(0) || fabiusPayee_ == address(0)) revert ZeroValue();
        if (initialFabiusBps_ > BPS) revert BadBps(initialFabiusBps_);
        locks = locks_;
        anchorer = anchorer_;
        fabiusPayee = fabiusPayee_;
        initialFabiusBps = initialFabiusBps_;
        implementation = address(new RevenueSplitter());
    }

    // -------------------------------------------------- alamat splitter (bisa dihitung sebelum klon ada)

    function splitterSalt(bytes32 botId, address issuer, address issuerPayee, bytes32 specSha) public pure returns (bytes32) {
        return keccak256(abi.encode(botId, issuer, issuerPayee, specSha));
    }

    function predictSplitter(bytes32 botId, address issuer, address issuerPayee, bytes32 specSha) public view returns (address) {
        return Clones.predictDeterministicAddress(implementation, splitterSalt(botId, issuer, issuerPayee, specSha), address(this));
    }

    /// Tanpa izin dan idempoten (USULAN): memasang klon di alamat prediksi bila belum ada. Semua yang menentukan alamat juga menentukan isi
    /// klon, jadi pemanggil tidak bisa memilih apa pun selain yang sudah terikat di alamat itu.
    function deploySplitter(bytes32 botId, address issuer, address issuerPayee, bytes32 specSha) external returns (address) {
        return _deploySplitter(botId, issuer, issuerPayee, specSha);
    }

    // -------------------------------------------------- siklus hidup bot (operator)

    function register(bytes32 botId, address issuer, address issuerPayee, bytes32 specSha, bytes32 reportLabel, bytes32 reportSha)
        external
        onlyOwner
        returns (address splitter)
    {
        if (botId == bytes32(0) || specSha == bytes32(0) || issuer == address(0)) revert ZeroValue();
        if (_bots[botId].status != Status.NONE) revert AlreadyRegistered(botId);
        uint64 specAt = locks.lockedAt(anchorer, botId, specSha);
        if (specAt == 0) revert SpecNotLocked(botId, specSha);
        uint64 reportAt = _requireAnchored(reportLabel, reportSha);
        if (specAt > reportAt) revert SpecLockedAfterReport(specAt, reportAt);
        splitter = _deploySplitter(botId, issuer, issuerPayee, specSha);
        uint64 nowTs = uint64(block.timestamp);
        _bots[botId] = Bot({issuer: issuer, status: Status.SHADOW, registeredAt: nowTs, changedAt: nowTs, splitter: splitter, specSha: specSha,
                            reportLabel: reportLabel, reportSha: reportSha});
        _ids.push(botId);
        emit Registered(botId, issuer, splitter, specSha);
        emit StatusChanged(botId, Status.NONE, Status.SHADOW, reportLabel, reportSha);
    }

    function setStatus(bytes32 botId, Status to, bytes32 reportLabel, bytes32 reportSha) external onlyOwner {
        Bot storage b = _bots[botId];
        Status from = b.status;
        if (from == Status.NONE) revert UnknownBot(botId);
        if (!isAllowed(from, to)) revert BadTransition(from, to);
        _requireAnchored(reportLabel, reportSha);
        b.status = to;
        b.changedAt = uint64(block.timestamp);
        b.reportLabel = reportLabel;
        b.reportSha = reportSha;
        emit StatusChanged(botId, from, to, reportLabel, reportSha);
    }

    /// Tabel transisi (USULAN: epik hanya menyebut empat status, bukan panahnya):
    ///   SHADOW   -> AKTIF (masuk slot)            | PENSIUN (gagal shadow / pembunuh / ditarik)
    ///   AKTIF    -> TERGUSUR (rolling)            | PENSIUN (pembunuh / ditarik)
    ///   TERGUSUR -> AKTIF (keputusan slot baru)   | PENSIUN
    ///   PENSIUN  -> tidak ada (final)             NONE -> SHADOW hanya lewat `register`.
    function isAllowed(Status from, Status to) public pure returns (bool) {
        if (from == Status.SHADOW) return to == Status.AKTIF || to == Status.PENSIUN;
        if (from == Status.AKTIF) return to == Status.TERGUSUR || to == Status.PENSIUN;
        if (from == Status.TERGUSUR) return to == Status.AKTIF || to == Status.PENSIUN;
        return false;
    }

    // -------------------------------------------------- pengaturan operator

    /// Anchorer bisa berganti (kunci committer pernah dirotasi, F-D82); pin lama tetap di LockRegistry dan transisi lama tetap di event.
    function setAnchorer(address newAnchorer) external onlyOwner {
        if (newAnchorer == address(0)) revert ZeroValue();
        emit AnchorerChanged(anchorer, newAnchorer);
        anchorer = newAnchorer;
    }

    /// Hanya untuk splitter yang dipasang SESUDAH ini; splitter yang sudah ada diganti lewat `RevenueSplitter.setFabiusPayee`.
    function setFabiusPayee(address newPayee) external onlyOwner {
        if (newPayee == address(0)) revert ZeroValue();
        emit FabiusPayeeChanged(fabiusPayee, newPayee);
        fabiusPayee = newPayee;
    }

    // -------------------------------------------------- baca

    function getBot(bytes32 botId) external view returns (Bot memory) {
        return _bots[botId];
    }

    function botCount() external view returns (uint256) {
        return _ids.length;
    }

    function botIdAt(uint256 index) external view returns (bytes32) {
        return _ids[index];
    }

    // -------------------------------------------------- internal

    function _requireAnchored(bytes32 reportLabel, bytes32 reportSha) private view returns (uint64 at) {
        if (reportLabel == bytes32(0) || reportSha == bytes32(0)) revert ZeroValue();
        at = locks.lockedAt(anchorer, reportLabel, reportSha);
        if (at == 0) revert ReportNotAnchored(reportLabel, reportSha);
    }

    function _deploySplitter(bytes32 botId, address issuer, address issuerPayee, bytes32 specSha) private returns (address splitter) {
        if (botId == bytes32(0) || specSha == bytes32(0) || issuer == address(0) || issuerPayee == address(0)) revert ZeroValue();
        bytes32 salt = splitterSalt(botId, issuer, issuerPayee, specSha);
        splitter = Clones.predictDeterministicAddress(implementation, salt, address(this));
        if (splitter.code.length > 0) return splitter;                 // sudah dipasang (dan diinisialisasi di transaksi yang sama)
        splitter = Clones.cloneDeterministic(implementation, salt);
        RevenueSplitter(splitter).initialize(botId, issuer, issuerPayee, fabiusPayee, initialFabiusBps);
        emit SplitterDeployed(botId, splitter, issuer, issuerPayee, specSha);
    }
}

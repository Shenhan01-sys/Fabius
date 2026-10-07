// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/// Yang dibaca splitter dari pabriknya: pemilik `BotRegistry` sekarang = operator Fabius (Ownable2Step).
interface IRegistryOwner {
    function owner() external view returns (address);
}

/// @title RevenueSplitter (C-H, P81) - penerima `payTo` x402 untuk sinyal SATU bot; bagi hasil penerbit / Fabius
///
/// Satu klon EIP-1167 per bot, dipasang `BotRegistry` lewat CREATE2 sehingga alamatnya bisa dihitung SEBELUM klon ada (gerbang x402 boleh
/// menawarkan `payTo` lebih dulu; token yang masuk sebelum klon dipasang tetap terhitung, karena pembukuan memakai saldo). Pembeli membayar
/// token ERC-20 (FAB uji, dst.) ke alamat ini. Rujukan aritmetikanya `engine/economics.py` (F-D72): penerbit = floor(jumlah x bpsPenerbit / 10000),
/// Fabius = sisanya (debu pembulatan ke Fabius), jumlah keduanya SELALU sama dengan masukan. Vektor lintas bahasa: `tools/gen_splitter_vectors.py`.
///
/// Aturan yang ditegakkan kontrak (bukan niat):
///  1. `release` bersifat PULL: siapa pun boleh memanggil, uang hanya pernah pergi ke `issuerPayee` dan `fabiusPayee` sesuai hak masing-masing.
///     Tidak ada fungsi lain yang memindahkan token - pemilik registry pun tidak bisa menyita saldo yang sudah terkumpul.
///  2. Pembukuan kumulatif per token (pola PaymentSplitter OpenZeppelin, dengan aturan bilangan bulat dua pihak di atas): hak penerbit dalam satu
///     segmen tarif = floor(total diterima segmen x bps / 10000), jadi berapa kali pun `release` dipanggil, hasil akhirnya sama dengan SATU
///     `economics.split` atas totalnya - tidak ada wei yang hilang atau dibayar dua kali.
///  3. Bagian Fabius hanya boleh TURUN (`economics.share_change_allowed`), hanya oleh Fabius (pemilik registry); tidak ada jalan untuk menaikkannya.
///     Tarif baru berlaku untuk saldo yang belum di-checkpoint (tarif penerbit yang lebih tinggi; karena dua floor terpisah, hasilnya bisa 1 wei
///     di bawah versi ber-checkpoint, tidak lebih - diuji fuzz); Fabius yang ingin saldo lama tetap bertarif lama memberi daftar token untuk
///     di-checkpoint lebih dulu.
///  4. Dompet payout penerbit hanya bisa diganti oleh penerbit (`issuer`); dompet Fabius hanya oleh Fabius. Hak yang belum dilepas ikut ke payee baru.
///  5. Keluar dari slot (status di `BotRegistry`) tidak menyentuh kontrak ini: yang berhenti hanya tawaran `payTo` baru (di luar chain).
///
/// Batas yang disengaja: koin native (BNB) ditolak (tanpa `receive`); token fee-on-transfer: yang dibagi adalah yang benar-benar tiba, fee keluar
/// ditanggung penerima; token yang saldonya bisa menyusut sendiri (rebase negatif, penyitaan oleh admin token) membuat `release` berhenti dengan
/// `BalanceShrank` sampai saldo pulih - lebih baik berhenti daripada membagi uang yang tidak ada.
contract RevenueSplitter is ReentrancyGuard {
    using SafeERC20 for IERC20;

    uint16 public constant BPS = 10_000;

    /// Pembukuan satu token. `received` (tidak disimpan) = saldo + semua yang sudah dilepas.
    struct Book {
        uint256 segStartReceived;   // total diterima saat segmen tarif sekarang dimulai
        uint256 segStartIssuer;     // hak penerbit yang sudah terkunci dari segmen-segmen sebelumnya
        uint256 lastReceived;       // total diterima pada checkpoint terakhir (batas segmen bila tarif berubah)
        uint256 releasedIssuer;
        uint256 releasedFabius;
        uint16 segIssuerBps;        // tarif penerbit segmen sekarang
        bool started;
    }

    address public registry;        // pabrik yang memasang klon ini (BotRegistry); nol = belum dipasang
    uint16 public fabiusBps;        // bagian Fabius; hanya turun
    bool private _initialized;
    bytes32 public botId;
    address public issuer;          // identitas penerbit (dompet penanda tangan pengajuan); tetap
    address public issuerPayee;     // dompet payout penerbit; hanya `issuer` yang boleh mengganti
    address public fabiusPayee;     // dompet Fabius; hanya pemilik registry yang boleh mengganti

    mapping(IERC20 => Book) private _books;

    event Initialized(address indexed registry, bytes32 indexed botId, address indexed issuer, address issuerPayee, address fabiusPayee,
                      uint16 fabiusBps);
    event Released(IERC20 indexed token, address indexed payee, bool indexed issuerSide, uint256 amount);
    event FabiusShareLowered(uint16 oldBps, uint16 newBps);
    event IssuerPayeeChanged(address indexed oldPayee, address indexed newPayee);
    event FabiusPayeeChanged(address indexed oldPayee, address indexed newPayee);

    error AlreadyInitialized();
    error NotInitialized();
    error ZeroValue();
    error BadPayee(address payee);
    error BadBps(uint16 bps);
    error NotIssuer();
    error NotFabius();
    error ShareMayOnlyDecrease(uint16 oldBps, uint16 newBps);
    error BalanceShrank(IERC20 token, uint256 lastReceived, uint256 received);

    /// Implementasi (yang di-klon) tidak pernah bisa dipasang atau dipakai: hanya klon yang punya penerbit dan payee.
    constructor() {
        _initialized = true;
    }

    modifier onlyFabius() {
        if (registry == address(0)) revert NotInitialized();
        if (msg.sender != IRegistryOwner(registry).owner()) revert NotFabius();
        _;
    }

    /// Dipanggil pabrik pada transaksi yang sama dengan pembuatan klon (tidak ada jendela untuk mendahului).
    function initialize(bytes32 botId_, address issuer_, address issuerPayee_, address fabiusPayee_, uint16 fabiusBps_) external {
        if (_initialized) revert AlreadyInitialized();
        if (botId_ == bytes32(0) || issuer_ == address(0)) revert ZeroValue();
        _checkPayee(issuerPayee_);
        _checkPayee(fabiusPayee_);
        if (fabiusBps_ > BPS) revert BadBps(fabiusBps_);
        _initialized = true;
        registry = msg.sender;
        botId = botId_;
        issuer = issuer_;
        issuerPayee = issuerPayee_;
        fabiusPayee = fabiusPayee_;
        fabiusBps = fabiusBps_;
        emit Initialized(msg.sender, botId_, issuer_, issuerPayee_, fabiusPayee_, fabiusBps_);
    }

    // -------------------------------------------------- pelepasan (pull; siapa pun boleh memanggil)

    /// Lepas hak KEDUA pihak untuk `token`. Mengembalikan jumlah yang dikirim ke tiap pihak (bisa nol).
    function release(IERC20 token) external nonReentrant returns (uint256 toIssuer, uint256 toFabius) {
        return _release(token, true, true);
    }

    /// Lepas hak penerbit saja: transfer ke satu pihak yang gagal (mis. alamat diblokir token) tidak menahan pihak lain.
    function releaseIssuer(IERC20 token) external nonReentrant returns (uint256 toIssuer) {
        (toIssuer,) = _release(token, true, false);
    }

    function releaseFabius(IERC20 token) external nonReentrant returns (uint256 toFabius) {
        (, toFabius) = _release(token, false, true);
    }

    /// Hak yang belum dilepas bila `release(token)` dipanggil sekarang (tanpa menulis apa pun).
    function pending(IERC20 token) external view returns (uint256 issuerDue, uint256 fabiusDue) {
        Book memory b = _books[token];
        uint256 received = _received(token, b);
        (Book memory nb, uint256 issuerCredit) = _project(b, received, BPS - fabiusBps);
        return (issuerCredit - nb.releasedIssuer, received - issuerCredit - nb.releasedFabius);
    }

    // -------------------------------------------------- perubahan yang diizinkan

    /// Bagian Fabius hanya boleh turun (sama = tanpa perubahan, diizinkan seperti `economics.share_change_allowed`). `checkpointFirst` = token
    /// yang saldonya yang belum di-checkpoint dibukukan dengan tarif LAMA sebelum tarif berubah; token lain memakai tarif baru untuk saldo itu.
    function lowerFabiusShare(uint16 newBps, IERC20[] calldata checkpointFirst) external onlyFabius nonReentrant {
        uint16 old = fabiusBps;
        if (newBps > old) revert ShareMayOnlyDecrease(old, newBps);
        for (uint256 i = 0; i < checkpointFirst.length; i++) {
            _checkpoint(checkpointFirst[i]);
        }
        fabiusBps = newBps;
        emit FabiusShareLowered(old, newBps);
    }

    function setIssuerPayee(address newPayee) external {
        if (registry == address(0)) revert NotInitialized();
        if (msg.sender != issuer) revert NotIssuer();
        _checkPayee(newPayee);
        emit IssuerPayeeChanged(issuerPayee, newPayee);
        issuerPayee = newPayee;
    }

    function setFabiusPayee(address newPayee) external onlyFabius {
        _checkPayee(newPayee);
        emit FabiusPayeeChanged(fabiusPayee, newPayee);
        fabiusPayee = newPayee;
    }

    // -------------------------------------------------- baca

    function issuerBps() external view returns (uint16) {
        return BPS - fabiusBps;
    }

    function bookOf(IERC20 token) external view returns (Book memory) {
        return _books[token];
    }

    // -------------------------------------------------- internal

    function _release(IERC20 token, bool doIssuer, bool doFabius) private returns (uint256 toIssuer, uint256 toFabius) {
        if (registry == address(0)) revert NotInitialized();
        (Book storage b, uint256 received, uint256 issuerCredit) = _checkpoint(token);
        if (doIssuer) {
            toIssuer = issuerCredit - b.releasedIssuer;
            b.releasedIssuer += toIssuer;
        }
        if (doFabius) {
            toFabius = received - issuerCredit - b.releasedFabius;
            b.releasedFabius += toFabius;
        }
        // Efek dicatat SEBELUM interaksi; nonReentrant menutup sisanya.
        if (toIssuer > 0) {
            address p = issuerPayee;
            token.safeTransfer(p, toIssuer);
            emit Released(token, p, true, toIssuer);
        }
        if (toFabius > 0) {
            address p = fabiusPayee;
            token.safeTransfer(p, toFabius);
            emit Released(token, p, false, toFabius);
        }
    }

    function _checkpoint(IERC20 token) private returns (Book storage b, uint256 received, uint256 issuerCredit) {
        b = _books[token];
        Book memory m = b;
        received = _received(token, m);
        Book memory nb;
        (nb, issuerCredit) = _project(m, received, BPS - fabiusBps);
        b.segStartReceived = nb.segStartReceived;
        b.segStartIssuer = nb.segStartIssuer;
        b.lastReceived = received;
        b.segIssuerBps = nb.segIssuerBps;
        b.started = true;
    }

    function _received(IERC20 token, Book memory b) private view returns (uint256 received) {
        received = token.balanceOf(address(this)) + b.releasedIssuer + b.releasedFabius;
        if (received < b.lastReceived) revert BalanceShrank(token, b.lastReceived, received);
    }

    /// Segmen tarif: bila tarif penerbit berubah sejak segmen dimulai, segmen lama ditutup pada checkpoint terakhir dengan tarif LAMA, lalu
    /// segmen baru dimulai dari situ dengan tarif sekarang. Hak penerbit = hak terkunci + floor(diterima segmen x bps / 10000) (mulDiv: tanpa luapan).
    function _project(Book memory b, uint256 received, uint16 curIssuerBps) private pure returns (Book memory, uint256 issuerCredit) {
        if (!b.started) {
            b.segIssuerBps = curIssuerBps;
        } else if (b.segIssuerBps != curIssuerBps) {
            b.segStartIssuer += Math.mulDiv(b.lastReceived - b.segStartReceived, b.segIssuerBps, BPS);
            b.segStartReceived = b.lastReceived;
            b.segIssuerBps = curIssuerBps;
        }
        issuerCredit = b.segStartIssuer + Math.mulDiv(received - b.segStartReceived, b.segIssuerBps, BPS);
        return (b, issuerCredit);
    }

    function _checkPayee(address p) private view {
        if (p == address(0) || p == address(this)) revert BadPayee(p);
    }
}

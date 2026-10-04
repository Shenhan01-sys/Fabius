// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC20Permit} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";

/// @title  FabiusCredit (FAB)
/// @notice Token pembayaran testnet Fabius untuk x402 per sinyal (P138a, F-D100). Tanpa nilai: testnet 97 saja (F-D98 #2).
///
/// Kode = X402DemoToken (sudah diuji: 9 fork test proxy x402 + tes token), hanya nama dan simbol yang berbeda. Nama adalah domain EIP-712
/// (`name = "Fabius Credit"`, `version = "1"`), jadi gerbang WAJIB mengumumkan keduanya di `accepts.extra.name` / `extra.version`.
///   1. ERC-20 polos tanpa hook transfer -> bisa dipindahkan Permit2 (`assetTransferMethod: "permit2"`).
///   2. EIP-2612 `permit()` -> `x402ExactPermit2Proxy.settleWithPermit()`: approval + settlement satu transaksi, pembeli nol gas.
///   3. `decimals() == 6` -> 10000 atomic = 0,01 FAB (harga dasar, `engine/harga.py`).
///   4. `faucet()` publik dengan batas per alamat -> dompet mana pun bisa isi sendiri; gerbang juga me-relay faucet supaya pembeli tanpa tBNB.
contract FabiusCredit is ERC20, ERC20Permit {
    /// @notice Samakan dengan USDC agar `amount` pada payload x402 mudah dibaca.
    uint8 private constant DECIMALS_ = 6;

    /// @notice Batas `faucet()` per alamat: 1.000.000 unit (1 juta x 10^6 atomic).
    ///         Cukup untuk ribuan pembayaran mikro, kecil cukup untuk tidak jadi mainan.
    uint256 public constant FAUCET_CAP_PER_ADDRESS = 1_000_000 * 10 ** 6;

    /// @notice Jumlah yang sudah ditarik tiap alamat lewat `faucet()`.
    mapping(address account => uint256 amount) public faucetWithdrawn;

    /// @notice Total yang pernah dicetak lewat `faucet()`, di semua alamat.
    uint256 public faucetTotal;

    error FaucetCapExceeded(address account, uint256 requested, uint256 alreadyWithdrawn, uint256 cap);
    error ZeroAmount();

    event FaucetClaim(address indexed account, uint256 amount, uint256 totalForAccount);

    constructor() ERC20("Fabius Credit", "FAB") ERC20Permit("Fabius Credit") {
        // Deployer dapat suplai awal supaya `payTo` bisa langsung diuji tanpa faucet.
        _mint(msg.sender, 1_000_000 * 10 ** 6);
    }

    function decimals() public pure override returns (uint8) {
        return DECIMALS_;
    }

    /// @notice Faucet mandiri untuk testnet. Siapa pun boleh menarik, dibatasi per alamat.
    /// @param amount Jumlah atomic unit (6 decimals) yang ingin dicetak ke `msg.sender`.
    function faucet(uint256 amount) external {
        if (amount == 0) revert ZeroAmount();
        uint256 already = faucetWithdrawn[msg.sender];
        if (already + amount > FAUCET_CAP_PER_ADDRESS) {
            revert FaucetCapExceeded(msg.sender, amount, already, FAUCET_CAP_PER_ADDRESS);
        }
        unchecked {
            faucetWithdrawn[msg.sender] = already + amount;
            faucetTotal += amount;
        }
        _mint(msg.sender, amount);
        emit FaucetClaim(msg.sender, amount, already + amount);
    }
}

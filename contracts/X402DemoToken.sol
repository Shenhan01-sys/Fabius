// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {ERC20Permit} from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";

/// @title  X402DemoToken
/// @notice USD-pegged tiruan untuk membuktikan skema x402 `exact` berjalan di BNB Chain.
///
/// Kenapa token ini ada (bukan memakai stablecoin yang sudah ada):
///   - x402 tidak mencantumkan BSC di DEFAULT_ASSETS (26 jaringan) maupun di
///     EVM_NETWORK_CHAIN_ID_MAP (23 nama legacy). Tidak ada aset default untuk chain 56/97.
///   - Infrastruktur on-chain x402 SUDAH ada di BSC: Permit2 dan x402ExactPermit2Proxy
///     ter-deploy di alamat kanonis pada chain 56 dan 97 (diverifikasi via eth_getCode).
///   - Fasilitator publik Unibase mengiklankan exact/upto/batch-settlement di eip155:56 dan
///     eip155:97, tetapi `extensions: []` -> tidak ada gas sponsoring.
///   Jadi yang hilang hanya token yang bisa kita kendalikan sendiri.
///
/// Syarat x402 yang dipenuhi kontrak ini:
///   1. ERC-20 polos tanpa hook transfer -> bisa dipindahkan Permit2
///      (jalur `assetTransferMethod: "permit2"`, "Universal Fallback ... any ERC-20").
///   2. EIP-2612 `permit()` -> memungkinkan ekstensi `eip2612GasSponsoring`, yaitu
///      `x402ExactPermit2Proxy.settleWithPermit()`: approval + settlement dalam SATU
///      transaksi, klien nol gas.
///   3. `decimals() == 6`, sama dengan USDC, supaya angka pada payload x402 terbaca
///      seperti contoh di spek ("amount": "10000" = 0.01).
///   4. `faucet()` publik dengan cap -> dompet klien mana pun bisa isi sendiri di testnet
///      tanpa menunggu kami, dan tanpa bergantung faucet pihak ketiga.
///
/// EIP-712 domain yang dihasilkan: name = "X402 Demo USD", version = "1".
/// Kedua nilai itu HARUS diumumkan server lewat `accepts.extra.name` / `extra.version`,
/// kalau tidak klien akan melewati jalur EIP-2612 (lihat spek scheme_exact_evm.md §2 Phase 2).
contract X402DemoToken is ERC20, ERC20Permit {
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

    constructor() ERC20("X402 Demo USD", "X402USD") ERC20Permit("X402 Demo USD") {
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

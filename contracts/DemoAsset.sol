// Aset yang diperdagangkan di venue demo kami.
//
// Kenapa ERC20 polos (bukan X402DemoToken yang sudah ada): X402DemoToken membawa ERC20Permit,
// dan di OpenZeppelin 5 jalur itu menyeret `utils/Bytes.sol` yang memakai opcode `mcopy` (Cancun).
// Membawanya ke profil default memaksa kami menaikkan target `DecisionAnchor` yang sudah
// terverifikasi di chain - itu bukan kompromi yang mau kami ambil demi kenyamanan deploy.
//
// Fungsi `give` sengaja terbuka tanpa izin: ini token testnet untuk melatih PIPELINE eksekusi,
// bukan instrumen yang punya nilai. Kalau suatu hari token ini dipakai untuk sesuatu yang serius,
// yang perlu diubah adalah pembuatnya, bukan pagar di vault.
pragma solidity ^0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract DemoAsset is ERC20 {
    uint8 private constant _DECIMALS = 6;

    constructor() ERC20("Fabius Venue Demo Asset", "FBAS") {
        _mint(msg.sender, 10_000_000 * 10 ** _DECIMALS);
    }

    function decimals() public pure override returns (uint8) {
        return _DECIMALS;
    }

    function give(address to, uint256 v) external {
        _mint(to, v);
    }
}

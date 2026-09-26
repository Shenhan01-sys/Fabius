// Interface untuk kontrak x402 kanonis yang SUDAH ter-deploy, supaya jalur pembayaran bisa
// dipanggil dan diuji TANPA mengompilasi sumber upstream-nya.
//
// Kenapa bukan sumber aslinya (terukur 26 Sep): `x402BasePermit2Proxy.sol` memakai opcode
// `mcopy` (Cancun). Profil default Fabius sengaja dipaku ke `evm_version = "shanghai"` supaya
// `DecisionAnchor` tetap bisa dipakai di VM yang lebih tua; mencampur keduanya membuat
// `forge test` polos gagal kompilasi. Itu regresi nyata demi kenyamanan satu berkas test.
//
// Yang kami panggil di test adalah alamat kanonis yang sudah ada di chain (0x402085c248EeA27D92E8
// b30b2C58ed07f9E20001, terverifikasi ADA KODE di 56 dan 97) - jadi interface ini cukup, dan
// justru lebih jujur: kami TIDAK men-deploy ulang kontrak orang lalu menyebutnya "terintegrasi".
//
// Sumber bentuknya: docs/upstream-x402/*.sol, salinan VERBATIM dari
// github.com/coinbase/x402 @ dd927a26cfefc98c24b3ec38b3a8f204dad0c60d
// (sha256 tercatat di contracts/vendor/x402/VENDORED.json; periksa ulang:
//  `python _research/vendored_x402.py verify`). Kalau upstream mengganti signature, test fork
//  kami yang akan pertama kali menjerit - itu keinginannya.
//
// Batas yang tidak boleh dilupakan: interface ini TIDAK membuktikan apa pun sendirian. Yang
// membuktikan adalah test fork yang memanggil alamat kanonis lewat interface ini dan melihat
// event `Settled()`/`SettledWithPermit()` muncul.
pragma solidity ^0.8.24;

import {ISignatureTransfer} from "./interfaces/ISignatureTransfer.sol";

/// @notice Tipe bersama yang dimiliki semua varian proxy x402 (permit2-based).
interface x402BasePermit2Proxy {
    /// @notice Parameter EIP-2612 untuk approve token -> Permit2, dibawa dalam satu panggilan.
    struct EIP2612Permit {
        uint256 value;
        uint256 deadline;
        bytes32 r;
        bytes32 s;
        uint8 v;
    }

    /// @notice Permit2 yang dipakai proxy. Di BSC (56 & 97) ini alamat kanonis yang sama.
    function PERMIT2() external view returns (ISignatureTransfer);

    // Dua error yang DIKUJITEST secara eksplisit (`vm.expectRevert(...selector)`), jadi keduanya
    // harus ada di sini. Yang lain sengaja tidak kuduga: kalau nanti test menuntut error ketiga,
    // kompilasi yang memberi tahu - bukan tebakan yang memberi tahu.
    /// @notice Nilai EIP-2612 permit tidak sama dengan jumlah yang diizinkan Permit2.
    error Permit2612AmountMismatch();
    /// @notice `validAfter` witness masih di masa depan saat settlement dipanggil.
    error PaymentTooEarly();
}

/// @notice Varian `exact`: bayar persis sejumlah yang diizinkan, dengan witness yang mengikat
///         tujuan pembayaran secara kriptografis.
interface x402ExactPermit2Proxy is x402BasePermit2Proxy {
    struct Witness {
        address to;
        uint256 validAfter;
    }

    function WITNESS_TYPEHASH() external view returns (bytes32);

    function WITNESS_TYPE_STRING() external view returns (string memory);

    function settle(
        ISignatureTransfer.PermitTransferFrom calldata permit,
        address owner,
        Witness calldata witness,
        bytes calldata signature
    ) external;

    function settleWithPermit(
        EIP2612Permit calldata permit2612,
        ISignatureTransfer.PermitTransferFrom calldata permit,
        address owner,
        Witness calldata witness,
        bytes calldata signature
    ) external;
}

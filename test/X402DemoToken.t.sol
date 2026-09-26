// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {X402DemoToken} from "../contracts/X402DemoToken.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {IERC5267} from "@openzeppelin/contracts/interfaces/IERC5267.sol";

/// @title  X402DemoTokenTest
/// @notice Setiap test dipetakan ke satu syarat x402 yang konkret, bukan ke coverage umum.
///         Rujukannya specs/schemes/exact/scheme_exact_evm.md dan
///         typescript/packages/mechanisms/evm/src/exact/README.md.
///
///   test_Decimals_MatchesUsdc            -> payload x402 memakai atomic unit; contoh spek
///                                            "amount": "1000" diberi komentar "0.001 USDC".
///   test_Eip712Domain_MatchesExtraFields -> server HARUS mengumumkan extra.name & extra.version;
///                                            kalau meleset, klien diam-diam melewati jalur
///                                            EIP-2612 dan pembayaran gagal di verifikasi.
///   test_Permit_SetsAllowanceForPermit2  -> prasyarat ekstensi eip2612GasSponsoring.
///   test_PermittedSpenderCanTransferFrom -> bukti jalur settle: proxy memanggil Permit2,
///                                            Permit2 memanggil transferFrom(token).
///   test_DirectApproveForPermit2         -> "Option A: Direct User Approval", satu-satunya
///                                            jalur yang tersedia di fasilitator Unibase
///                                            karena /supported mengembalikan extensions: [].
contract X402DemoTokenTest is Test {
    /// @notice Permit2 kanonis Uniswap. Terverifikasi ADA KODE di chain 56 dan 97 (9152 bytes).
    address internal constant PERMIT2 = 0x000000000022D473030F116dDEE9F6B43aC78BA3;

    /// @notice x402ExactPermit2Proxy kanonis. Terverifikasi ADA KODE di chain 56 dan 97 (2913 bytes).
    ///         Tidak dipanggil di sini (sumber Permit2 tidak tersedia lokal), tapi inilah
    ///         `spender` yang muncul di payload permitWitnessTransferFrom.
    address internal constant X402_EXACT_PROXY = 0x402085c248EeA27D92E8b30b2C58ed07f9E20001;

    /// @notice Kunci Anvil #0. Deterministik supaya tanda tangan EIP-712 bisa direproduksi.
    uint256 internal constant OWNER_KEY = 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80;

    bytes32 internal constant PERMIT_TYPEHASH =
        keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)");

    X402DemoToken internal token;
    address internal owner;
    address internal payTo;

    function setUp() public {
        token = new X402DemoToken();
        owner = vm.addr(OWNER_KEY);
        payTo = makeAddr("payTo");
    }

    // ---------------------------------------------------------------- metadata

    function test_Metadata() public view {
        assertEq(token.name(), "X402 Demo USD");
        assertEq(token.symbol(), "X402USD");
    }

    /// Spek dan contoh resmi memakai atomic unit. 6 decimals = USDC, jadi
    /// "$0.001" -> 1000, persis seperti komentar pada eip2612-gas-sponsoring.ts.
    function test_Decimals_MatchesUsdc() public view {
        assertEq(token.decimals(), 6);
        // 1 unit == 10^6 atomic, jadi "$0.001" -> 1000, sama seperti komentar pada
        // examples/typescript/servers/advanced/eip2612-gas-sponsoring.ts ("0.001 USDC").
        assertEq(10 ** uint256(token.decimals()), 1_000_000);
    }

    // ------------------------------------------------- EIP-712 domain (EIP-2612)

    /// Nilai name & version di sini adalah yang WAJIB ditaruh server ke
    /// accepts.extra.name / accepts.extra.version. Test ini menguncinya supaya
    /// konfigurasi server tidak bisa menyimpang dari kontrak.
    function test_Eip712Domain_MatchesExtraFields() public view {
        (, string memory name, string memory version, uint256 chainId, address verifyingContract,,) =
            IERC5267(address(token)).eip712Domain();

        assertEq(name, "X402 Demo USD");
        assertEq(version, "1");
        assertEq(chainId, block.chainid);
        assertEq(verifyingContract, address(token));
    }

    // ------------------------------------------------------------------- faucet

    function test_Faucet_Mints() public {
        address alice = makeAddr("alice");
        vm.prank(alice);
        token.faucet(100_000); // 0.1 unit

        assertEq(token.balanceOf(alice), 100_000);
        assertEq(token.faucetWithdrawn(alice), 100_000);
        assertEq(token.faucetTotal(), 100_000);
    }

    function test_Faucet_RejectsOverCap() public {
        address alice = makeAddr("alice");
        uint256 cap = token.FAUCET_CAP_PER_ADDRESS();

        vm.prank(alice);
        token.faucet(cap);

        vm.prank(alice);
        vm.expectRevert(
            abi.encodeWithSelector(X402DemoToken.FaucetCapExceeded.selector, alice, 1, cap, cap)
        );
        token.faucet(1);
    }

    function test_Faucet_RejectsZero() public {
        vm.expectRevert(X402DemoToken.ZeroAmount.selector);
        token.faucet(0);
    }

    function testFuzz_Faucet_CapNeverExceeded(uint256 first, uint256 second) public {
        first = bound(first, 1, token.FAUCET_CAP_PER_ADDRESS());
        address alice = makeAddr("alice");

        vm.prank(alice);
        token.faucet(first);

        uint256 remaining = token.FAUCET_CAP_PER_ADDRESS() - first;
        second = bound(second, 1, remaining == 0 ? 1 : remaining + 1);

        vm.prank(alice);
        if (second > remaining) {
            vm.expectRevert();
            token.faucet(second);
        } else {
            token.faucet(second);
        }

        assertLe(token.faucetWithdrawn(alice), token.FAUCET_CAP_PER_ADDRESS());
    }

    // --------------------------------------------- jalur EIP-2612 (gas sponsoring)

    function _permitDigest(
        address spender,
        uint256 value,
        uint256 nonce,
        uint256 deadline
    ) internal view returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(PERMIT_TYPEHASH, owner, spender, value, nonce, deadline));
        return keccak256(abi.encodePacked("\x19\x01", token.DOMAIN_SEPARATOR(), structHash));
    }

    function _signedPermit(
        address spender,
        uint256 value,
        uint256 deadline
    ) internal view returns (uint8 v, bytes32 r, bytes32 s) {
        bytes32 digest = _permitDigest(spender, value, token.nonces(owner), deadline);
        return vm.sign(OWNER_KEY, digest);
    }

    /// Inilah kemampuan yang membuat klien nol-gas: tanda tangan off-chain mengubah
    /// allowance token -> Permit2, tanpa transaksi dari klien.
    function test_Permit_SetsAllowanceForPermit2() public {
        uint256 value = 1000; // 0.001 unit
        uint256 deadline = block.timestamp + 60; // maxTimeoutSeconds pada contoh spek
        (uint8 v, bytes32 r, bytes32 s) = _signedPermit(PERMIT2, value, deadline);

        token.permit(owner, PERMIT2, value, deadline, v, r, s);

        assertEq(token.allowance(owner, PERMIT2), value);
        assertEq(token.nonces(owner), 1);
    }

    /// Bukti ujung-ke-ujung jalur settle: setelah permit, alamat yang diizinkan
    /// (di produksi: Permit2, dipanggil oleh x402ExactPermit2Proxy) bisa memindahkan
    /// dana ke `payTo` tanpa persetujuan lebih lanjut dari klien.
    function test_PermittedSpenderCanTransferFrom() public {
        token.faucet(10_000); // owner menarik dari faucet (owner == address(this)? tidak)
        // faucet dipanggil oleh kontrak test, jadi dananya ke address(this).
        // Pindahkan ke owner supaya skenarionya sesuai dunia nyata.
        token.transfer(owner, 10_000);

        uint256 value = 1000;
        (uint8 v, bytes32 r, bytes32 s) = _signedPermit(PERMIT2, value, block.timestamp + 60);
        token.permit(owner, PERMIT2, value, block.timestamp + 60, v, r, s);

        // Izinkan PERMIT2 bertindak sebagai pemanggil transferFrom, meniru panggilan
        // Permit2 -> token.transferFrom(owner, payTo, amount) saat settle.
        vm.prank(PERMIT2);
        token.transferFrom(owner, payTo, value);

        assertEq(token.balanceOf(payTo), value);
        assertEq(token.balanceOf(owner), 10_000 - value);
        assertEq(token.allowance(owner, PERMIT2), 0); // exact: allowance terpakai penuh
    }

    function test_Permit_RejectsReplay() public {
        uint256 value = 1000;
        uint256 deadline = block.timestamp + 60;
        (uint8 v, bytes32 r, bytes32 s) = _signedPermit(PERMIT2, value, deadline);

        token.permit(owner, PERMIT2, value, deadline, v, r, s);

        vm.expectRevert();
        token.permit(owner, PERMIT2, value, deadline, v, r, s);
    }

    function test_Permit_RejectsExpired() public {
        uint256 deadline = block.timestamp;
        (uint8 v, bytes32 r, bytes32 s) = _signedPermit(PERMIT2, 1000, deadline);

        vm.warp(deadline + 1);
        vm.expectRevert();
        token.permit(owner, PERMIT2, 1000, deadline, v, r, s);
    }

    /// Spek: klien mengendalikan jumlah & tujuan; fasilitator tidak bisa mengubahnya.
    /// Tanda tangan untuk nilai 1000 tidak boleh bisa dipakai memindahkan 1001.
    function test_Permit_RejectsAlteredValue() public {
        uint256 deadline = block.timestamp + 60;
        (uint8 v, bytes32 r, bytes32 s) = _signedPermit(PERMIT2, 1000, deadline);

        vm.expectRevert();
        token.permit(owner, PERMIT2, 1001, deadline, v, r, s);
    }

    function test_Permit_RejectsAlteredSpender() public {
        uint256 deadline = block.timestamp + 60;
        (uint8 v, bytes32 r, bytes32 s) = _signedPermit(PERMIT2, 1000, deadline);

        vm.expectRevert();
        token.permit(owner, X402_EXACT_PROXY, 1000, deadline, v, r, s);
    }

    // ---------------------------------- jalur Option A (Unibase: extensions kosong)

    /// Fasilitator Unibase mengiklankan BSC tetapi `extensions: []`, jadi tidak ada
    /// eip2612GasSponsoring. Klien harus approve Permit2 sendiri sekali (bayar gas),
    /// setelah itu pembayaran berulang berjalan tanpa approve lagi.
    function test_DirectApproveForPermit2() public {
        token.faucet(10_000);
        token.transfer(owner, 10_000);

        vm.prank(owner);
        token.approve(PERMIT2, type(uint256).max);
        assertEq(token.allowance(owner, PERMIT2), type(uint256).max);

        vm.prank(PERMIT2);
        token.transferFrom(owner, payTo, 1000);
        assertEq(token.balanceOf(payTo), 1000);
        // Allowance tak terbatas tetap utuh -> pembayaran berikutnya tidak perlu approve lagi.
        assertEq(token.allowance(owner, PERMIT2), type(uint256).max);
    }

    // ------------------------------------------------- tidak ada hook tersembunyi

    /// Permit2 memindahkan token lewat transferFrom standar. Token dengan biaya
    /// transfer (fee-on-transfer), blacklist, atau pause akan membuat simulasi
    /// fasilitator lulus tetapi settle gagal. Pastikan tidak ada satupun di sini.
    function test_NoTransferRestrictions() public {
        token.faucet(10_000);
        address a = makeAddr("a");
        address b = makeAddr("b");

        token.transfer(a, 5_000);
        vm.prank(a);
        token.transfer(b, 5_000);

        assertEq(token.balanceOf(b), 5_000);
        assertEq(token.balanceOf(a), 0);
        assertEq(IERC20(address(token)).totalSupply(), 1_000_000 * 10 ** 6 + 10_000);
    }
}

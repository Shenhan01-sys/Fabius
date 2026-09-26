// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {console} from "forge-std/console.sol";
import {X402DemoToken} from "../contracts/X402DemoToken.sol";
// Sumber vendored: github.com/coinbase/x402 @ dd927a26cfefc98c24b3ec38b3a8f204dad0c60d, salinan
// VERBATIM (sha256 tercatat di contracts/vendor/x402/VENDORED.json; periksa-ulang:
// `python _research/vendored_x402.py verify`). Test ini MEMANGGIL proxy kanonis yang sudah
// ter-deploy (0x402085c2…) di chain 56/97 — sumber ini cuma dipakai supaya klaimnya bisa
// dikompilasi dan diulang dari clone repo, bukan dari laci riset.
// Interface kami sendiri (bukan sumber upstream): proxy kanonis memakai `mcopy`/Cancun dan tidak
// boleh ikut dikompilasi ke proyek yang profil defaultnya `shanghai`. Lihat kepala berkas ini.
import {x402ExactPermit2Proxy, x402BasePermit2Proxy}
    from "../contracts/vendor/x402/IX402ExactPermit2Proxy.sol";
import {ISignatureTransfer} from "../contracts/vendor/x402/interfaces/ISignatureTransfer.sol";

/// @title  X402SettleOnBscForkTest
/// @notice Menjalankan jalur pembayaran x402 `exact`/permit2 yang SEBENARNYA terhadap
///         fork BSC Testnet (chain 97) — memakai Permit2 kanonis dan x402ExactPermit2Proxy
///         kanonis yang benar-benar ter-deploy di chain itu, dengan token kita sendiri.
///
///         Kenapa fork, bukan deploy sungguhan: fork membuktikan seluruh jalur kriptografis
///         dan kontrak bekerja terhadap state chain nyata TANPA butuh wallet berdana dan
///         TANPA mengirim transaksi apa pun. Deploy sungguhan setelah ini tinggal formalitas.
///
///         Konstruksi signature disalin dari test fork resmi x402 sendiri
///         (contracts/evm/test/x402ExactPermit2Proxy.fork.t.sol), bukan dikarang.
///
/// Jalankan:
///   forge test --match-contract X402SettleOnBscForkTest -vv \
///     --fork-url bscTestnet        (alias dari [rpc_endpoints] di foundry.toml)
///   alias itu menunjuk ke https://bsc-testnet.publicnode.com sejak 26 Sep: endpoint yang
///   tertulis di sini sebelumnya (data-seed-prebsc-1-s1) terukur MATI, dan perintah di komentar
///   ini adalah satu-satunya cara bukti ini bisa diulang orang lain - komentar yang tidak bisa
///   dijalankan sama dengan klaim yang tidak bisa diperiksa.
///   CATATAN: --fork-url https://bsc-testnet.drpc.org TIDAK bisa dipakai di sini walaupun drpc
///   sehat untuk eth_call: ia menolak state per-blok yang diminta forge (`Unknown block`).
///
/// Tanpa --fork-url semua test di file ini di-skip (bukan gagal).
contract X402SettleOnBscForkTest is Test {
    /// @notice Permit2 kanonis Uniswap. Terverifikasi ADA KODE di chain 56 dan 97 (9152 bytes).
    address internal constant PERMIT2 = 0x000000000022D473030F116dDEE9F6B43aC78BA3;

    /// @notice x402ExactPermit2Proxy kanonis. Terverifikasi ADA KODE di chain 56 dan 97 (2913 bytes).
    ///         Kami memanggil kontrak yang SUDAH ter-deploy, bukan men-deploy ulang:
    ///         kalau ini lulus, yang terbukti adalah infrastruktur nyata, bukan tiruan kami.
    address internal constant CANONICAL_PROXY = 0x402085c248EeA27D92E8b30b2C58ed07f9E20001;

    uint256 internal constant BSC_MAINNET_CHAIN_ID = 56;
    uint256 internal constant BSC_TESTNET_CHAIN_ID = 97;

    // ---- typehash Permit2, disalin verbatim dari fork test resmi x402 ----
    bytes32 internal constant P2_DOMAIN_TYPEHASH =
        keccak256("EIP712Domain(string name,uint256 chainId,address verifyingContract)");
    bytes32 internal constant P2_WITNESS_TYPEHASH = keccak256(
        "PermitWitnessTransferFrom(TokenPermissions permitted,address spender,uint256 nonce,uint256 deadline,Witness witness)TokenPermissions(address token,uint256 amount)Witness(address to,uint256 validAfter)"
    );
    bytes32 internal constant P2_TOKEN_PERMISSIONS_TYPEHASH =
        keccak256("TokenPermissions(address token,uint256 amount)");

    /// Typehash EIP-2612 token kita sendiri — berbeda dari Permit2, jangan tertukar.
    bytes32 internal constant EIP2612_PERMIT_TYPEHASH =
        keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)");

    /// topic0 dari event yang dipancarkan proxy.
    ///
    /// Kami mencari topic di log yang direkam, BUKAN memakai vm.expectEmit. Alasannya
    /// teramati langsung: settle() memancarkan Transfer token (dan settleWithPermit()
    /// memancarkan Approval dari EIP-2612) SEBELUM event Settled()/SettledWithPermit(),
    /// sedangkan expectEmit hanya membandingkan log berikutnya — sehingga menghasilkan
    /// "Approval != expected log" padahal pembayarannya sendiri berhasil.
    bytes32 internal constant TOPIC_SETTLED = keccak256("Settled()");
    bytes32 internal constant TOPIC_SETTLED_WITH_PERMIT = keccak256("SettledWithPermit()");

    x402ExactPermit2Proxy internal proxy;
    X402DemoToken internal token;

    uint256 internal payerKey;
    address internal payer;
    address internal payTo;

    /// 0.001 unit — sama dengan `price: "$0.001"` pada contoh resmi x402.
    uint256 internal constant PRICE = 1000;
    uint256 internal constant FUNDED = 10_000e6;

    /// Kontrak x402 yang sama ter-deploy di alamat kanonis pada KEDUA chain, dengan ukuran
    /// bytecode identik (Permit2 9152, exact proxy 2913, upto proxy 3142 bytes). Jadi test
    /// ini sah dijalankan terhadap fork testnet MAUPUN mainnet — keduanya harus lulus.
    modifier onlyOnBsc() {
        vm.skip(block.chainid != BSC_MAINNET_CHAIN_ID && block.chainid != BSC_TESTNET_CHAIN_ID);
        _;
    }

    function setUp() public {
        payerKey = uint256(keccak256("x402-bnb-poc-payer"));
        payer = vm.addr(payerKey);
        payTo = makeAddr("payTo");
        proxy = x402ExactPermit2Proxy(CANONICAL_PROXY);

        // Deployer (kontrak test ini) menerima suplai awal dari constructor, jadi
        // `payer` bisa didanai tanpa perlu bertindak sama sekali. Itu penting:
        // test bebas-gas di bawah membuktikan payer tidak pernah mengirim transaksi.
        token = new X402DemoToken();
        token.transfer(payer, FUNDED);
    }

    // ------------------------------------------------------------ konstruksi signature

    function _permit2DomainSeparator() internal view returns (bytes32) {
        return keccak256(abi.encode(P2_DOMAIN_TYPEHASH, keccak256("Permit2"), block.chainid, PERMIT2));
    }

    function _witnessHash(x402ExactPermit2Proxy.Witness memory w) internal view returns (bytes32) {
        return keccak256(abi.encode(proxy.WITNESS_TYPEHASH(), w.to, w.validAfter));
    }

    function _permit2Digest(
        uint256 amount,
        uint256 nonce,
        uint256 deadline,
        x402ExactPermit2Proxy.Witness memory w
    ) internal view returns (bytes32) {
        bytes32 tokenHash = keccak256(abi.encode(P2_TOKEN_PERMISSIONS_TYPEHASH, address(token), amount));
        bytes32 structHash =
            keccak256(abi.encode(P2_WITNESS_TYPEHASH, tokenHash, address(proxy), nonce, deadline, _witnessHash(w)));
        return keccak256(abi.encodePacked("\x19\x01", _permit2DomainSeparator(), structHash));
    }

    /// `spender` pada tanda tangan adalah PROXY, bukan fasilitator — inilah yang membuat
    /// fasilitator tidak bisa membelokkan tujuan dana.
    function _signWitness(
        uint256 amount,
        uint256 nonce,
        uint256 deadline,
        x402ExactPermit2Proxy.Witness memory w
    ) internal view returns (bytes memory) {
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(payerKey, _permit2Digest(amount, nonce, deadline, w));
        return abi.encodePacked(r, s, v);
    }

    function _signEip2612(
        address spender,
        uint256 value,
        uint256 deadline
    ) internal view returns (uint8 v, bytes32 r, bytes32 s) {
        bytes32 structHash =
            keccak256(abi.encode(EIP2612_PERMIT_TYPEHASH, payer, spender, value, token.nonces(payer), deadline));
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", token.DOMAIN_SEPARATOR(), structHash));
        return vm.sign(payerKey, digest);
    }

    function _permit(
        uint256 amount,
        uint256 nonce,
        uint256 deadline
    ) internal view returns (ISignatureTransfer.PermitTransferFrom memory) {
        return ISignatureTransfer.PermitTransferFrom({
            permitted: ISignatureTransfer.TokenPermissions({token: address(token), amount: amount}),
            nonce: nonce,
            deadline: deadline
        });
    }

    /// Mencari topic0 di antara log yang direkam sejak `vm.recordLogs()` terakhir.
    function _emittedTopic(bytes32 topic0) internal view returns (bool) {
        Vm.Log[] memory logs = vm.getRecordedLogs();
        for (uint256 i = 0; i < logs.length; i++) {
            if (logs[i].topics.length > 0 && logs[i].topics[0] == topic0) return true;
        }
        return false;
    }

    // ============================================ 1. infrastrukturnya nyata dan cocok

    /// "ADA KODE" saja lemah: bisa saja ada kontrak lain di alamat itu. Test ini membandingkan
    /// konstanta on-chain dari kontrak yang ter-deploy dengan sumber x402ExactPermit2Proxy.
    /// Kalau ketiganya cocok, bytecode di chain itu memang proxy exact milik x402.
    function test_fork_KontrakTerdeployMemangProxyExactX402() public onlyOnBsc {
        assertTrue(
            block.chainid == BSC_MAINNET_CHAIN_ID || block.chainid == BSC_TESTNET_CHAIN_ID,
            "bukan fork BSC (56 atau 97)"
        );
        assertGt(PERMIT2.code.length, 0, "Permit2 tidak ada di chain ini");
        assertGt(CANONICAL_PROXY.code.length, 0, "x402ExactPermit2Proxy tidak ada di chain ini");

        assertEq(address(proxy.PERMIT2()), PERMIT2, "proxy menunjuk Permit2 yang salah");
        assertEq(proxy.WITNESS_TYPEHASH(), keccak256("Witness(address to,uint256 validAfter)"));
        assertEq(
            proxy.WITNESS_TYPE_STRING(),
            "Witness witness)TokenPermissions(address token,uint256 amount)Witness(address to,uint256 validAfter)"
        );

        console.log("chainId               :", block.chainid);
        console.log("Permit2 bytecode      :", PERMIT2.code.length);
        console.log("proxy bytecode        :", CANONICAL_PROXY.code.length);
        console.log("proxy.PERMIT2() cocok : true");
    }

    // ============================ 2. jalur Option A — yang didukung fasilitator Unibase

    /// Fasilitator Unibase mengiklankan eip155:97 tetapi `extensions: []`, jadi tidak ada
    /// eip2612GasSponsoring. Klien harus approve Permit2 sendiri sekali (bayar gas), setelah
    /// itu settle berjalan. Test ini membuktikan jalur itu bekerja di BSC dengan token kita.
    function test_fork_Settle_JalurApproveLangsung() public onlyOnBsc {
        vm.prank(payer);
        token.approve(PERMIT2, type(uint256).max);

        uint256 nonce = uint256(keccak256("nonce-approve-langsung"));
        uint256 deadline = block.timestamp + 60; // maxTimeoutSeconds pada contoh spek
        x402ExactPermit2Proxy.Witness memory w =
            x402ExactPermit2Proxy.Witness({to: payTo, validAfter: block.timestamp});

        ISignatureTransfer.PermitTransferFrom memory permit = _permit(PRICE, nonce, deadline);
        bytes memory sig = _signWitness(PRICE, nonce, deadline, w);

        // Di dunia nyata pemanggil ini adalah fasilitator, yang membayar gas BNB.
        vm.recordLogs();
        proxy.settle(permit, payer, w, sig);
        assertTrue(_emittedTopic(TOPIC_SETTLED), "proxy tidak memancarkan Settled()");

        assertEq(token.balanceOf(payTo), PRICE, "payTo tidak menerima jumlah yang tepat");
        assertEq(token.balanceOf(payer), FUNDED - PRICE);
    }

    // ====================== 3. jalur Option C — eip2612GasSponsoring, klien NOL GAS

    /// Ini hasil yang paling penting: TANPA approve sebelumnya, satu panggilan fasilitator
    /// (settleWithPermit) menyetujui Permit2 lewat EIP-2612 lalu memindahkan dana.
    /// Klien tidak pernah mengirim transaksi — noncenya tidak bergerak.
    ///
    /// Tidak ada fasilitator publik yang menawarkan ini di BSC hari ini (Unibase
    /// extensions: [], Coinbase tidak mendukung BSC). Jadi ini celah yang bisa kita isi.
    function test_fork_SettleWithPermit_KlienNolGas() public onlyOnBsc {
        assertEq(token.allowance(payer, PERMIT2), 0, "harus dimulai tanpa allowance");
        uint256 nonceBefore = vm.getNonce(payer);

        uint256 deadline = block.timestamp + 60;

        // _executePermit() memaksa permit2612.value == permit.permitted.amount.
        (uint8 v2612, bytes32 r2612, bytes32 s2612) = _signEip2612(PERMIT2, PRICE, deadline);
        x402BasePermit2Proxy.EIP2612Permit memory p2612 =
            x402BasePermit2Proxy.EIP2612Permit({value: PRICE, deadline: deadline, r: r2612, s: s2612, v: v2612});

        uint256 nonce = uint256(keccak256("nonce-nol-gas"));
        x402ExactPermit2Proxy.Witness memory w =
            x402ExactPermit2Proxy.Witness({to: payTo, validAfter: block.timestamp});
        ISignatureTransfer.PermitTransferFrom memory permit = _permit(PRICE, nonce, deadline);
        bytes memory sig = _signWitness(PRICE, nonce, deadline, w);

        vm.recordLogs();
        proxy.settleWithPermit(p2612, permit, payer, w, sig);
        assertTrue(
            _emittedTopic(TOPIC_SETTLED_WITH_PERMIT), "proxy tidak memancarkan SettledWithPermit()"
        );

        assertEq(token.balanceOf(payTo), PRICE, "pembayaran bebas-gas gagal");
        assertEq(token.balanceOf(payer), FUNDED - PRICE);
        assertEq(
            vm.getNonce(payer),
            nonceBefore,
            "klien seharusnya tidak perlu mengirim transaksi apa pun"
        );
    }

    /// _executePermit() MENELAN kegagalan permit (hanya emit event), jadi kalau nilainya
    /// tidak cocok proxy harus revert lebih dulu lewat Permit2612AmountMismatch.
    /// Tanpa cek ini, allowance tidak akan pernah terbentuk dan settle gagal diam-diam.
    function test_fork_SettleWithPermit_TolakNilaiTidakCocok() public onlyOnBsc {
        uint256 deadline = block.timestamp + 60;
        (uint8 v, bytes32 r, bytes32 s) = _signEip2612(PERMIT2, PRICE, deadline);

        // value sengaja dilebihkan 1 atomic unit.
        x402BasePermit2Proxy.EIP2612Permit memory p2612 =
            x402BasePermit2Proxy.EIP2612Permit({value: PRICE + 1, deadline: deadline, r: r, s: s, v: v});

        uint256 nonce = uint256(keccak256("nonce-mismatch"));
        x402ExactPermit2Proxy.Witness memory w =
            x402ExactPermit2Proxy.Witness({to: payTo, validAfter: block.timestamp});
        ISignatureTransfer.PermitTransferFrom memory permit = _permit(PRICE, nonce, deadline);
        bytes memory sig = _signWitness(PRICE, nonce, deadline, w);

        vm.expectRevert(x402BasePermit2Proxy.Permit2612AmountMismatch.selector);
        proxy.settleWithPermit(p2612, permit, payer, w, sig);

        assertEq(token.balanceOf(payTo), 0, "dana tidak boleh berpindah saat revert");
    }

    // ================================ 4. jaminan keamanan inti dari spek

    /// Spek: "the Facilitator cannot modify the amount or destination".
    /// Fasilitator adalah pemanggil settle(), jadi ia bebas mengisi `witness`.
    /// Tujuan yang ditandatangani harus tetap mengikat.
    function test_fork_FasilitatorTidakBisaMengubahTujuan() public onlyOnBsc {
        vm.prank(payer);
        token.approve(PERMIT2, type(uint256).max);

        address attacker = makeAddr("attacker");
        uint256 nonce = uint256(keccak256("nonce-tamper"));
        uint256 deadline = block.timestamp + 60;

        x402ExactPermit2Proxy.Witness memory ditandatangani =
            x402ExactPermit2Proxy.Witness({to: payTo, validAfter: block.timestamp});
        ISignatureTransfer.PermitTransferFrom memory permit = _permit(PRICE, nonce, deadline);
        bytes memory sig = _signWitness(PRICE, nonce, deadline, ditandatangani);

        x402ExactPermit2Proxy.Witness memory diubah =
            x402ExactPermit2Proxy.Witness({to: attacker, validAfter: ditandatangani.validAfter});

        vm.expectRevert();
        proxy.settle(permit, payer, diubah, sig);

        assertEq(token.balanceOf(attacker), 0);
        assertEq(token.balanceOf(payTo), 0);
        assertEq(token.balanceOf(payer), FUNDED, "dana harus tetap utuh di payer");
    }

    /// Sisi "amount" dari klaim yang sama. Proxy selalu memakai permit.permitted.amount,
    /// jadi satu-satunya cara membelokkan jumlah adalah memanggil Permit2 langsung —
    /// yang ditolak Permit2 sendiri.
    function test_fork_FasilitatorTidakBisaMelebihkanJumlah() public onlyOnBsc {
        vm.prank(payer);
        token.approve(PERMIT2, type(uint256).max);

        uint256 nonce = uint256(keccak256("nonce-overamount"));
        uint256 deadline = block.timestamp + 60;
        x402ExactPermit2Proxy.Witness memory w =
            x402ExactPermit2Proxy.Witness({to: payTo, validAfter: block.timestamp});
        ISignatureTransfer.PermitTransferFrom memory permit = _permit(PRICE, nonce, deadline);
        bytes memory sig = _signWitness(PRICE, nonce, deadline, w);

        ISignatureTransfer.SignatureTransferDetails memory lebihBesar =
            ISignatureTransfer.SignatureTransferDetails({to: payTo, requestedAmount: PRICE + 1});

        // Semua argumen yang butuh staticcall ke proxy disiapkan lebih dulu. Kalau tidak,
        // staticcall itulah yang memakan vm.prank di bawah, sehingga panggilan ke Permit2
        // berjalan sebagai kontrak test dan bukan sebagai spender yang ditandatangani.
        bytes32 witnessHash = _witnessHash(w);
        string memory witnessTypeString = proxy.WITNESS_TYPE_STRING();

        vm.prank(address(proxy)); // fasilitator jahat menyamar sebagai spender yang ditandatangani
        vm.expectRevert();
        ISignatureTransfer(PERMIT2).permitWitnessTransferFrom(
            permit, lebihBesar, payer, witnessHash, witnessTypeString, sig
        );

        assertEq(token.balanceOf(payTo), 0);
        assertEq(token.balanceOf(payer), FUNDED);
    }

    function test_fork_TolakNonceDimainkanUlang() public onlyOnBsc {
        vm.prank(payer);
        token.approve(PERMIT2, type(uint256).max);

        uint256 nonce = uint256(keccak256("nonce-replay"));
        uint256 deadline = block.timestamp + 60;
        x402ExactPermit2Proxy.Witness memory w =
            x402ExactPermit2Proxy.Witness({to: payTo, validAfter: block.timestamp});
        ISignatureTransfer.PermitTransferFrom memory permit = _permit(PRICE, nonce, deadline);
        bytes memory sig = _signWitness(PRICE, nonce, deadline, w);

        proxy.settle(permit, payer, w, sig);
        assertEq(token.balanceOf(payTo), PRICE);

        vm.expectRevert();
        proxy.settle(permit, payer, w, sig);

        assertEq(token.balanceOf(payTo), PRICE, "pembayaran ganda tidak boleh terjadi");
    }

    /// Spek: witness.validAfter adalah batas bawah waktu. Sebelum itu, settlement ditolak.
    function test_fork_TolakSebelumValidAfter() public onlyOnBsc {
        vm.prank(payer);
        token.approve(PERMIT2, type(uint256).max);

        uint256 nonce = uint256(keccak256("nonce-too-early"));
        uint256 deadline = block.timestamp + 3600;
        x402ExactPermit2Proxy.Witness memory w =
            x402ExactPermit2Proxy.Witness({to: payTo, validAfter: block.timestamp + 600});
        ISignatureTransfer.PermitTransferFrom memory permit = _permit(PRICE, nonce, deadline);
        bytes memory sig = _signWitness(PRICE, nonce, deadline, w);

        vm.expectRevert(x402BasePermit2Proxy.PaymentTooEarly.selector);
        proxy.settle(permit, payer, w, sig);
    }
}

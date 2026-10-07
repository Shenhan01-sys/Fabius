// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test, console2} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {Clones} from "@openzeppelin/contracts/proxy/Clones.sol";
import {LockRegistry} from "../contracts/LockRegistry.sol";
import {ILockRegistry} from "../contracts/SignalAnchor.sol";
import {BotRegistry} from "../contracts/BotRegistry.sol";
import {RevenueSplitter} from "../contracts/RevenueSplitter.sol";
import {DeployBotRegistryScript} from "../script/DeployBotRegistry.s.sol";

contract PayToken is ERC20 {
    constructor() ERC20("Fabius Credit uji", "FAB") {}

    function mint(address to, uint256 v) external {
        _mint(to, v);
    }
}

/// Yang diuji (P81, C-H): (1) alamat splitter yang dihitung SEBELUM klon ada == alamat klon yang di-deploy (juga lintas bahasa: vektor
/// `engine/splitter.py` diperiksa di sini, dan vektor yang dicetak `test_vektor_evm_dicetak` diperiksa Python); (2) salt mengikat penerbit,
/// payout, dan spesifikasi; (3) tabel transisi status lengkap 5x5, setiap transisi wajib menunjuk laporan yang di-pin anchorer di
/// LockRegistry, pendaftaran wajib spesifikasi yang dikunci sebelum laporannya; (4) hak akses operator (Ownable2Step); (5) keluar dari slot
/// tidak menghentikan pembayaran. Kontrak ini tidak membuktikan isi laporan benar - hanya bahwa laporannya sudah publik sebelum transisi.
contract BotRegistryTest is Test {
    LockRegistry internal locks;
    BotRegistry internal reg;
    PayToken internal fab;

    address internal operator = makeAddr("fabius-operator");
    address internal committer = makeAddr("committer-m3");
    address internal kas = makeAddr("fabius-kas");
    address internal issuer = makeAddr("penerbit");
    address internal payout = makeAddr("penerbit-payout");
    address internal stranger = makeAddr("orang-luar");
    address internal buyer = makeAddr("pembeli");

    bytes32 internal constant BOT = "B1-TREND";
    bytes32 internal constant SPEC = keccak256("spec-b1-trend");
    bytes32 internal constant LAPORAN = "FABIUS-LAPORAN";
    bytes32 internal constant R_TINJAU = keccak256("laporan-peninjau-lolos-shadow");
    bytes32 internal constant R_SLOT = keccak256("buku-epoch-masuk-slot");
    bytes32 internal constant R_GUSUR = keccak256("buku-epoch-digusur");
    bytes32 internal constant R_PENSIUN = keccak256("pembunuh-terpicu");

    function setUp() public {
        vm.warp(1_791_000_000);
        locks = new LockRegistry();
        reg = new BotRegistry(operator, ILockRegistry(address(locks)), committer, kas, 4000);
        fab = new PayToken();
        _pin(BOT, SPEC);                                                // S1: spesifikasi dikunci dulu
        vm.warp(block.timestamp + 1 days);
        _pin(LAPORAN, R_TINJAU);                                        // S2: laporan peninjau di-pin sesudahnya
        _pin(LAPORAN, R_SLOT);
        _pin(LAPORAN, R_GUSUR);
        _pin(LAPORAN, R_PENSIUN);
    }

    function _pin(bytes32 label, bytes32 sha) internal {
        vm.prank(committer);
        locks.lock(label, sha, "uji");
    }

    function _register(bytes32 bot) internal returns (address s) {
        if (locks.lockedAt(committer, bot, SPEC) == 0) {
            vm.warp(block.timestamp - 1);
            _pin(bot, SPEC);
            vm.warp(block.timestamp + 1);
        }
        vm.prank(operator);
        s = reg.register(bot, issuer, payout, SPEC, LAPORAN, R_TINJAU);
    }

    function _set(bytes32 bot, BotRegistry.Status to, bytes32 r) internal {
        vm.prank(operator);
        reg.setStatus(bot, to, LAPORAN, r);
    }

    function _none() internal pure returns (IERC20[] memory) {
        return new IERC20[](0);
    }

    function _json() internal view returns (string memory) {
        return vm.readFile(string.concat(vm.projectRoot(), "/test/fixtures/splitter_vectors.json"));
    }

    // -------------------------------------------------- alamat dihitung dulu (CREATE2)

    function test_prediksi_sama_dengan_alamat_klon_yang_dideploy() public {
        address predicted = reg.predictSplitter(BOT, issuer, payout, SPEC);
        assertEq(predicted.code.length, 0, "sebelum pendaftaran belum ada kode");
        address s = _register(BOT);
        assertEq(s, predicted, "alamat deploy == prediksi");
        assertEq(reg.getBot(BOT).splitter, predicted);
        assertGt(predicted.code.length, 0);
        assertEq(predicted, Clones.predictDeterministicAddress(reg.implementation(), reg.splitterSalt(BOT, issuer, payout, SPEC), address(reg)));
        RevenueSplitter rs = RevenueSplitter(s);
        assertEq(rs.registry(), address(reg));
        assertEq(rs.botId(), BOT);
        assertEq(rs.issuer(), issuer);
        assertEq(rs.issuerPayee(), payout);
        assertEq(rs.fabiusPayee(), kas);
        assertEq(rs.fabiusBps(), 4000);
    }

    function testFuzz_prediksi_sama_dengan_deploy(bytes32 bot, address iss, address pay, bytes32 spec) public {
        vm.assume(bot != bytes32(0) && spec != bytes32(0) && iss != address(0) && pay != address(0));
        address predicted = reg.predictSplitter(bot, iss, pay, spec);
        vm.assume(pay != predicted);
        vm.prank(stranger);
        address s = reg.deploySplitter(bot, iss, pay, spec);
        assertEq(s, predicted);
        assertGt(s.code.length, 0);
    }

    function test_bayar_sebelum_klon_ada_tetap_terbagi() public {
        address payTo = reg.predictSplitter(BOT, issuer, payout, SPEC);
        fab.mint(buyer, 10_001);
        vm.prank(buyer);
        fab.transfer(payTo, 10_001);                                    // gerbang x402 menawarkan payTo sebelum klon dipasang
        _register(BOT);
        (uint256 toI, uint256 toF) = RevenueSplitter(payTo).release(fab);
        assertEq(toI, 6_000, "floor(10001 x 0,6)");
        assertEq(toF, 4_001, "debu ke Fabius");
        assertEq(fab.balanceOf(payout), 6_000);
        assertEq(fab.balanceOf(kas), 4_001);
    }

    function test_salt_mengikat_penerbit_payout_dan_spesifikasi() public {
        address a = reg.predictSplitter(BOT, issuer, payout, SPEC);
        assertTrue(a != reg.predictSplitter(BOT, stranger, payout, SPEC), "penerbit lain = alamat lain");
        assertTrue(a != reg.predictSplitter(BOT, issuer, stranger, SPEC), "payout lain = alamat lain");
        assertTrue(a != reg.predictSplitter(BOT, issuer, payout, keccak256("spec-lain")), "spesifikasi lain = alamat lain");
        assertTrue(a != reg.predictSplitter("B1-TREND-2", issuer, payout, SPEC), "bot lain = alamat lain");
        // operator mendaftarkan botId yang sama dengan payout lain: klonnya di alamat LAIN, alamat yang sudah ditawarkan tidak tersentuh
        vm.prank(operator);
        address s = reg.register(BOT, issuer, stranger, SPEC, LAPORAN, R_TINJAU);
        assertTrue(s != a);
        assertEq(a.code.length, 0);
    }

    function test_deploySplitter_tanpa_izin_idempoten_dan_dipakai_register() public {
        address payTo = reg.predictSplitter(BOT, issuer, payout, SPEC);
        fab.mint(payTo, 100);
        vm.expectEmit(true, true, true, true, address(reg));
        emit BotRegistry.SplitterDeployed(BOT, payTo, issuer, payout, SPEC);
        vm.prank(stranger);
        assertEq(reg.deploySplitter(BOT, issuer, payout, SPEC), payTo);
        vm.prank(stranger);
        assertEq(reg.deploySplitter(BOT, issuer, payout, SPEC), payTo, "kedua kali: alamat sama, tidak ada deploy ulang");
        RevenueSplitter(payTo).release(fab);                            // tanpa pendaftaran pun uang bisa keluar ke pihak yang terikat salt
        assertEq(fab.balanceOf(payout), 60);
        assertEq(fab.balanceOf(kas), 40);
        assertEq(_register(BOT), payTo, "register memakai klon yang sudah ada");
        vm.expectRevert(BotRegistry.ZeroValue.selector);
        reg.deploySplitter(BOT, issuer, address(0), SPEC);
    }

    // -------------------------------------------------- vektor lintas bahasa (engine/splitter.py <-> kontrak)

    function test_vektor_create2_python_sama_dengan_kontrak() public view {
        string memory j = _json();
        address[] memory dep = vm.parseJsonAddressArray(j, ".create2.deployer");
        address[] memory impl = vm.parseJsonAddressArray(j, ".create2.implementation");
        bytes32[] memory bot = vm.parseJsonBytes32Array(j, ".create2.botId");
        address[] memory iss = vm.parseJsonAddressArray(j, ".create2.issuer");
        address[] memory pay = vm.parseJsonAddressArray(j, ".create2.issuerPayee");
        bytes32[] memory spec = vm.parseJsonBytes32Array(j, ".create2.specSha");
        bytes32[] memory salt = vm.parseJsonBytes32Array(j, ".create2.salt");
        address[] memory want = vm.parseJsonAddressArray(j, ".create2.predicted");
        assertEq(want.length, 4);
        for (uint256 i = 0; i < want.length; i++) {
            assertEq(reg.splitterSalt(bot[i], iss[i], pay[i], spec[i]), salt[i], "salt kontrak == salt Python");
            assertEq(Clones.predictDeterministicAddress(impl[i], salt[i], dep[i]), want[i], "alamat Clones == alamat Python");
        }
    }

    /// PEMBUAT vektor `evm` (dibaca `tools/gen_splitter_vectors.py --evm` dari `forge test --json`): klon yang BENAR-BENAR di-deploy register.
    function test_vektor_evm_dicetak() public {
        address s = _register(BOT);
        assertGt(s.code.length, 0);
        string memory o = "evm";
        vm.serializeAddress(o, "registry", address(reg));
        vm.serializeAddress(o, "implementation", reg.implementation());
        vm.serializeString(o, "botIdText", "B1-TREND");
        vm.serializeBytes32(o, "botId", BOT);
        vm.serializeAddress(o, "issuer", issuer);
        vm.serializeAddress(o, "issuerPayee", payout);
        vm.serializeBytes32(o, "specSha", SPEC);
        vm.serializeBytes32(o, "salt", reg.splitterSalt(BOT, issuer, payout, SPEC));
        string memory out = vm.serializeAddress(o, "deployed", s);
        console2.log(string.concat("VEKTOR_EVM ", out));
    }

    // -------------------------------------------------- transisi status

    function test_tabel_transisi_lengkap() public {
        // harapan eksplisit: baris = dari, kolom = ke (NONE, SHADOW, AKTIF, TERGUSUR, PENSIUN)
        bool[5][5] memory ok;
        ok[1][2] = true; ok[1][4] = true;                              // SHADOW -> AKTIF | PENSIUN
        ok[2][3] = true; ok[2][4] = true;                              // AKTIF -> TERGUSUR | PENSIUN
        ok[3][2] = true; ok[3][4] = true;                              // TERGUSUR -> AKTIF | PENSIUN
        uint256 n;
        for (uint8 f = 0; f < 5; f++) {
            for (uint8 t = 0; t < 5; t++) {
                assertEq(reg.isAllowed(BotRegistry.Status(f), BotRegistry.Status(t)), ok[f][t], "isAllowed == tabel");
                if (f == 0) continue;                                   // NONE: hanya lewat register, diuji terpisah
                bytes32 bot = bytes32(uint256(keccak256(abi.encode("bot", f, t))));
                _register(bot);
                if (f == 2 || f == 3) _set(bot, BotRegistry.Status.AKTIF, R_SLOT);
                if (f == 3) _set(bot, BotRegistry.Status.TERGUSUR, R_GUSUR);
                if (f == 4) _set(bot, BotRegistry.Status.PENSIUN, R_PENSIUN);
                assertEq(uint8(reg.getBot(bot).status), f);
                vm.prank(operator);
                if (!ok[f][t]) {
                    vm.expectRevert(abi.encodeWithSelector(BotRegistry.BadTransition.selector, BotRegistry.Status(f), BotRegistry.Status(t)));
                }
                reg.setStatus(bot, BotRegistry.Status(t), LAPORAN, R_SLOT);
                assertEq(uint8(reg.getBot(bot).status), ok[f][t] ? t : f);
                if (ok[f][t]) n++;
            }
        }
        assertEq(n, 6, "tepat enam panah");
        vm.prank(operator);
        vm.expectRevert(abi.encodeWithSelector(BotRegistry.UnknownBot.selector, bytes32("TIDAK-ADA")));
        reg.setStatus("TIDAK-ADA", BotRegistry.Status.SHADOW, LAPORAN, R_SLOT);
    }

    function test_transisi_wajib_laporan_yang_dipin_anchorer() public {
        _register(BOT);
        bytes32 belum = keccak256("laporan-belum-dipin");
        vm.prank(operator);
        vm.expectRevert(abi.encodeWithSelector(BotRegistry.ReportNotAnchored.selector, LAPORAN, belum));
        reg.setStatus(BOT, BotRegistry.Status.AKTIF, LAPORAN, belum);
        vm.prank(stranger);
        locks.lock(LAPORAN, belum, "pin orang lain tidak dihitung");
        vm.prank(operator);
        vm.expectRevert(abi.encodeWithSelector(BotRegistry.ReportNotAnchored.selector, LAPORAN, belum));
        reg.setStatus(BOT, BotRegistry.Status.AKTIF, LAPORAN, belum);
        vm.startPrank(operator);
        vm.expectRevert(BotRegistry.ZeroValue.selector);
        reg.setStatus(BOT, BotRegistry.Status.AKTIF, bytes32(0), R_SLOT);
        vm.expectRevert(BotRegistry.ZeroValue.selector);
        reg.setStatus(BOT, BotRegistry.Status.AKTIF, LAPORAN, bytes32(0));
        vm.expectEmit(true, true, true, true, address(reg));
        emit BotRegistry.StatusChanged(BOT, BotRegistry.Status.SHADOW, BotRegistry.Status.AKTIF, LAPORAN, R_SLOT);
        reg.setStatus(BOT, BotRegistry.Status.AKTIF, LAPORAN, R_SLOT);
        vm.stopPrank();
        BotRegistry.Bot memory b = reg.getBot(BOT);
        assertEq(b.reportLabel, LAPORAN);
        assertEq(b.reportSha, R_SLOT);
        assertEq(b.changedAt, uint64(block.timestamp));
    }

    function test_daftar_wajib_spesifikasi_dikunci_sebelum_laporan() public {
        bytes32 bot = "X2-BELUM-DIKUNCI";
        vm.prank(operator);
        vm.expectRevert(abi.encodeWithSelector(BotRegistry.SpecNotLocked.selector, bot, SPEC));
        reg.register(bot, issuer, payout, SPEC, LAPORAN, R_TINJAU);
        vm.prank(stranger);
        locks.lock(bot, SPEC, "kunci orang lain tidak dihitung");
        vm.prank(operator);
        vm.expectRevert(abi.encodeWithSelector(BotRegistry.SpecNotLocked.selector, bot, SPEC));
        reg.register(bot, issuer, payout, SPEC, LAPORAN, R_TINJAU);
        vm.warp(block.timestamp + 1 hours);
        _pin(bot, SPEC);                                                // dikunci SESUDAH laporannya di-pin
        uint64 specAt = locks.lockedAt(committer, bot, SPEC);
        uint64 reportAt = locks.lockedAt(committer, LAPORAN, R_TINJAU);
        vm.prank(operator);
        vm.expectRevert(abi.encodeWithSelector(BotRegistry.SpecLockedAfterReport.selector, specAt, reportAt));
        reg.register(bot, issuer, payout, SPEC, LAPORAN, R_TINJAU);
        bytes32 r2 = keccak256("laporan-sesudah-kunci");
        _pin(LAPORAN, r2);                                              // laporan baru sesudah kunci: sah
        vm.prank(operator);
        reg.register(bot, issuer, payout, SPEC, LAPORAN, r2);
        assertEq(uint8(reg.getBot(bot).status), uint8(BotRegistry.Status.SHADOW));
    }

    function test_daftar_ganda_dan_nilai_nol_ditolak() public {
        _register(BOT);
        vm.startPrank(operator);
        vm.expectRevert(abi.encodeWithSelector(BotRegistry.AlreadyRegistered.selector, BOT));
        reg.register(BOT, issuer, payout, SPEC, LAPORAN, R_TINJAU);
        vm.expectRevert(BotRegistry.ZeroValue.selector);
        reg.register(bytes32(0), issuer, payout, SPEC, LAPORAN, R_TINJAU);
        vm.expectRevert(BotRegistry.ZeroValue.selector);
        reg.register("X3", address(0), payout, SPEC, LAPORAN, R_TINJAU);
        vm.expectRevert(BotRegistry.ZeroValue.selector);
        reg.register("X3", issuer, payout, bytes32(0), LAPORAN, R_TINJAU);
        vm.stopPrank();
        assertEq(reg.botCount(), 1);
        assertEq(reg.botIdAt(0), BOT);
    }

    function test_event_pendaftaran() public {
        address s = reg.predictSplitter(BOT, issuer, payout, SPEC);
        vm.expectEmit(true, true, true, true, address(reg));
        emit BotRegistry.Registered(BOT, issuer, s, SPEC);
        vm.expectEmit(true, true, true, true, address(reg));
        emit BotRegistry.StatusChanged(BOT, BotRegistry.Status.NONE, BotRegistry.Status.SHADOW, LAPORAN, R_TINJAU);
        _register(BOT);
        BotRegistry.Bot memory b = reg.getBot(BOT);
        assertEq(b.issuer, issuer);
        assertEq(b.specSha, SPEC);
        assertEq(b.registeredAt, uint64(block.timestamp));
    }

    // -------------------------------------------------- hak akses

    function test_hanya_operator() public {
        _register(BOT);
        vm.startPrank(stranger);
        vm.expectRevert(abi.encodeWithSelector(Ownable.OwnableUnauthorizedAccount.selector, stranger));
        reg.register("X4", issuer, payout, SPEC, LAPORAN, R_TINJAU);
        vm.expectRevert(abi.encodeWithSelector(Ownable.OwnableUnauthorizedAccount.selector, stranger));
        reg.setStatus(BOT, BotRegistry.Status.AKTIF, LAPORAN, R_SLOT);
        vm.expectRevert(abi.encodeWithSelector(Ownable.OwnableUnauthorizedAccount.selector, stranger));
        reg.setAnchorer(stranger);
        vm.expectRevert(abi.encodeWithSelector(Ownable.OwnableUnauthorizedAccount.selector, stranger));
        reg.setFabiusPayee(stranger);
        vm.stopPrank();
        vm.prank(issuer);                                               // penerbit pun tidak mengubah status
        vm.expectRevert(abi.encodeWithSelector(Ownable.OwnableUnauthorizedAccount.selector, issuer));
        reg.setStatus(BOT, BotRegistry.Status.PENSIUN, LAPORAN, R_PENSIUN);
    }

    function test_ownable2step_fabius_pindah_hanya_sesudah_diterima() public {
        RevenueSplitter s = RevenueSplitter(_register(BOT));
        address baru = makeAddr("operator-baru");
        vm.prank(operator);
        reg.transferOwnership(baru);
        vm.prank(baru);                                                 // belum menerima: belum Fabius
        vm.expectRevert(RevenueSplitter.NotFabius.selector);
        s.lowerFabiusShare(3000, _none());
        vm.prank(baru);
        reg.acceptOwnership();
        vm.prank(operator);
        vm.expectRevert(RevenueSplitter.NotFabius.selector);
        s.lowerFabiusShare(3000, _none());
        vm.prank(baru);
        s.lowerFabiusShare(3000, _none());
        assertEq(s.fabiusBps(), 3000);
    }

    function test_ganti_anchorer_dan_dompet_fabius_untuk_splitter_baru() public {
        address lama = reg.predictSplitter(BOT, issuer, payout, SPEC);
        _register(BOT);
        address committer2 = makeAddr("committer-baru");
        address kas2 = makeAddr("kas-baru");
        vm.startPrank(operator);
        vm.expectEmit(true, true, false, false, address(reg));
        emit BotRegistry.AnchorerChanged(committer, committer2);
        reg.setAnchorer(committer2);
        reg.setFabiusPayee(kas2);
        vm.expectRevert(BotRegistry.ZeroValue.selector);
        reg.setAnchorer(address(0));
        vm.expectRevert(BotRegistry.ZeroValue.selector);
        reg.setFabiusPayee(address(0));
        vm.expectRevert(abi.encodeWithSelector(BotRegistry.ReportNotAnchored.selector, LAPORAN, R_SLOT));
        reg.setStatus(BOT, BotRegistry.Status.AKTIF, LAPORAN, R_SLOT);  // pin committer lama tidak lagi dihitung
        vm.stopPrank();
        vm.prank(committer2);
        locks.lock(LAPORAN, R_SLOT, "pin ulang oleh committer baru");
        _set(BOT, BotRegistry.Status.AKTIF, R_SLOT);
        assertEq(RevenueSplitter(lama).fabiusPayee(), kas, "splitter lama tidak berubah oleh setFabiusPayee registry");
        assertEq(RevenueSplitter(reg.deploySplitter("X5", issuer, payout, SPEC)).fabiusPayee(), kas2, "splitter baru memakai dompet baru");
    }

    function test_konstruktor_menolak_nol_dan_bps_di_atas_penuh() public {
        vm.expectRevert(BotRegistry.ZeroValue.selector);
        new BotRegistry(operator, ILockRegistry(address(0)), committer, kas, 4000);
        vm.expectRevert(BotRegistry.ZeroValue.selector);
        new BotRegistry(operator, ILockRegistry(address(locks)), address(0), kas, 4000);
        vm.expectRevert(BotRegistry.ZeroValue.selector);
        new BotRegistry(operator, ILockRegistry(address(locks)), committer, address(0), 4000);
        vm.expectRevert(abi.encodeWithSelector(BotRegistry.BadBps.selector, uint16(10_001)));
        new BotRegistry(operator, ILockRegistry(address(locks)), committer, kas, 10_001);
        vm.expectRevert(abi.encodeWithSelector(Ownable.OwnableInvalidOwner.selector, address(0)));
        new BotRegistry(address(0), ILockRegistry(address(locks)), committer, kas, 4000);
        assertEq(reg.initialFabiusBps(), 4000);
        assertEq(reg.owner(), operator);
        assertEq(address(reg.locks()), address(locks));
        assertEq(reg.anchorer(), committer);
    }

    // -------------------------------------------------- skrip deploy (dijalankan di EVM uji saja; tidak ada transaksi ke chain mana pun)

    function test_skrip_deploy_jalan_dan_membaca_ulang() public {
        DeployBotRegistryScript sc = new DeployBotRegistryScript();
        vm.setEnv("DEPLOYER_PRIVATE_KEY", vm.toString(uint256(keccak256("kunci-uji-sekali-pakai"))));   // hanya di EVM uji
        vm.setEnv("BOT_REGISTRY_OWNER", vm.toString(operator));
        vm.setEnv("LOCK_REGISTRY", vm.toString(address(0xdead)));
        vm.expectRevert(bytes("LOCK_REGISTRY tanpa kode di chain ini - berhenti sebelum mengirim"));
        sc.run();
        vm.setEnv("LOCK_REGISTRY", vm.toString(address(locks)));
        BotRegistry r = sc.run();
        assertEq(r.owner(), operator);
        assertEq(address(r.locks()), address(locks));
        assertEq(r.anchorer(), 0xCA9c7322210E9a7F7d0953c862d4Ef60cC0D64A4, "bawaan = committer M3 di deployments/97.json");
        assertEq(r.fabiusPayee(), operator, "bawaan = pemilik");
        assertEq(r.initialFabiusBps(), 4000, "bawaan = economics.FABIUS_SHARE_BPS");
        assertGt(r.implementation().code.length, 0);
    }

    // -------------------------------------------------- keluar slot != berhenti membayar

    function test_keluar_slot_tetap_membayar() public {
        RevenueSplitter s = RevenueSplitter(_register(BOT));
        _set(BOT, BotRegistry.Status.AKTIF, R_SLOT);
        fab.mint(address(s), 1_000);
        _set(BOT, BotRegistry.Status.TERGUSUR, R_GUSUR);
        fab.mint(address(s), 500);                                      // pembeli lama yang terlambat tetap terbagi
        _set(BOT, BotRegistry.Status.PENSIUN, R_PENSIUN);
        vm.prank(operator);
        vm.expectRevert(abi.encodeWithSelector(BotRegistry.BadTransition.selector, BotRegistry.Status.PENSIUN, BotRegistry.Status.AKTIF));
        reg.setStatus(BOT, BotRegistry.Status.AKTIF, LAPORAN, R_SLOT);
        vm.prank(stranger);
        (uint256 toI, uint256 toF) = s.release(fab);
        assertEq(toI, 900);
        assertEq(toF, 600);
        assertEq(fab.balanceOf(payout), 900);
        assertEq(fab.balanceOf(kas), 600);
    }
}


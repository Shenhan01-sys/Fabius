// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {LockRegistry} from "../contracts/LockRegistry.sol";
import {SignalAnchor, ILockRegistry} from "../contracts/SignalAnchor.sol";
import {MerkleProof} from "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";

/// Yang diuji: (1) kontrak menghitung daun dan memverifikasi bukti PERSIS sama dengan engine (vektor dari `tools/gen_signal_vectors.py`);
/// (2) aturan waktu yang membuat komit bermakna (kunci sebelum bar, komit sesudah bar tertutup dan dalam batas lag, satu komit per bar);
/// (3) pengungkapan tidak bisa dipalsukan atau dihitung dua kali, dan yang tidak diungkap tercatat permanen.
/// Tidak ada test yang mengklaim sinyalnya bagus - kontrak ini tidak bisa membuktikannya.
contract SignalAnchorTest is Test {
    LockRegistry internal reg;
    SignalAnchor internal sa;
    address internal op = makeAddr("operator-fabius");
    address internal stranger = makeAddr("orang-luar");
    string internal json;

    uint64 internal constant MAX_LAG = 12 hours;
    uint64 internal constant WINDOW = 7 days;

    bytes32 internal bot;
    bytes32 internal spec;
    uint64 internal asof;
    bytes32 internal root3;
    uint32 internal n3;

    function setUp() public {
        json = vm.readFile(string.concat(vm.projectRoot(), "/test/fixtures/signal_vectors.json"));
        bot = vm.parseJsonBytes32(json, ".tiga.botId");
        spec = vm.parseJsonBytes32(json, ".tiga.specSha");
        asof = uint64(vm.parseJsonUint(json, ".tiga.asof"));
        root3 = vm.parseJsonBytes32(json, ".tiga.root");
        n3 = uint32(vm.parseJsonUint(json, ".tiga.n"));
        reg = new LockRegistry();
        sa = new SignalAnchor(ILockRegistry(address(reg)), MAX_LAG, WINDOW);
        vm.warp(asof - 3 days);
        vm.prank(op);
        reg.lock(bot, spec, "engine/spec.py@B3-CARRY");
        vm.warp(asof + 1 hours);                                    // satu jam sesudah bar tertutup
    }

    function _sig(string memory g, uint256 i)
        internal
        view
        returns (SignalAnchor.Signal memory s, bytes32 salt, bytes32 leaf, bytes32[] memory proof)
    {
        string memory b = string.concat(".", g);
        string memory p = string.concat(b, ".signals[", vm.toString(i), "]");
        s = SignalAnchor.Signal({
            v: uint8(vm.parseJsonUint(json, string.concat(p, ".v"))),
            botId: vm.parseJsonBytes32(json, string.concat(b, ".botId")),
            specSha: vm.parseJsonBytes32(json, string.concat(b, ".specSha")),
            asof: uint64(vm.parseJsonUint(json, string.concat(b, ".asof"))),
            asset: vm.parseJsonBytes32(json, string.concat(p, ".asset")),
            aksi: uint8(vm.parseJsonUint(json, string.concat(p, ".aksi"))),
            bobotLama: vm.parseJsonInt(json, string.concat(p, ".bobotLama")),
            bobotBaru: vm.parseJsonInt(json, string.concat(p, ".bobotBaru")),
            hargaRef: vm.parseJsonUint(json, string.concat(p, ".hargaRef")),
            dataHash: vm.parseJsonBytes32(json, string.concat(p, ".dataHash"))
        });
        salt = vm.parseJsonBytes32(json, string.concat(p, ".salt"));
        leaf = vm.parseJsonBytes32(json, string.concat(p, ".leaf"));
        proof = vm.parseJsonBytes32Array(json, string.concat(p, ".proof"));
    }

    function _commit3() internal returns (bytes32 id) {
        vm.prank(op);
        id = sa.commit(bot, spec, asof, root3, n3);
    }

    // -------------------------------------------------- vektor lintas bahasa (engine <-> kontrak)

    function test_daun_dan_bukti_engine_sama_dengan_kontrak() public view {
        for (uint256 i = 0; i < n3; i++) {
            (SignalAnchor.Signal memory s, bytes32 salt, bytes32 leaf, bytes32[] memory proof) = _sig("tiga", i);
            assertEq(sa.leafOf(s, salt), leaf, "daun kontrak == daun engine");
            assertTrue(MerkleProof.verify(proof, root3, leaf), "bukti engine sah untuk akar engine");
        }
        (SignalAnchor.Signal memory s1, bytes32 salt1, bytes32 leaf1,) = _sig("satu", 0);
        assertEq(sa.leafOf(s1, salt1), leaf1, "daun tunggal");
        assertEq(leaf1, vm.parseJsonBytes32(json, ".satu.root"), "satu daun = akar (bukti kosong)");
    }

    function test_bobot_negatif_short_ikut_tepat() public view {
        (SignalAnchor.Signal memory s, bytes32 salt, bytes32 leaf,) = _sig("tiga", 2);
        assertLt(s.bobotBaru, 0, "vektor ketiga adalah MASUK_SHORT (bobot negatif)");
        assertEq(sa.leafOf(s, salt), leaf);
    }

    // -------------------------------------------------- LockRegistry

    function test_kunci_tercatat_dan_ganda_ditolak() public {
        assertGt(reg.lockedAt(op, bot, spec), 0);
        assertEq(reg.lockCount(), 1);
        bytes32 id = reg.lockId(op, bot, spec);
        vm.prank(op);
        vm.expectRevert(abi.encodeWithSelector(LockRegistry.AlreadyLocked.selector, id));
        reg.lock(bot, spec, "lagi");
    }

    function test_kunci_nol_ditolak() public {
        vm.expectRevert(LockRegistry.ZeroValue.selector);
        reg.lock(bytes32(0), spec, "");
        vm.expectRevert(LockRegistry.ZeroValue.selector);
        reg.lock(bot, bytes32(0), "");
    }

    function test_kunci_orang_lain_tidak_menggeser_kunci_kami() public {
        uint64 ours = reg.lockedAt(op, bot, spec);
        vm.warp(asof + 2 hours);
        vm.prank(stranger);
        reg.lock(bot, spec, "mendahului?");
        assertEq(reg.lockedAt(op, bot, spec), ours, "jam kunci kami tidak berubah");
        assertGt(reg.lockedAt(stranger, bot, spec), ours, "kunci orang lain = id lain, jam lain");
        assertTrue(reg.lockId(op, bot, spec) != reg.lockId(stranger, bot, spec));
    }

    // -------------------------------------------------- aturan komit

    function test_komit_tanpa_kunci_ditolak() public {
        vm.prank(stranger);
        vm.expectRevert(SignalAnchor.NotLocked.selector);
        sa.commit(bot, spec, asof, root3, n3);
    }

    function test_kunci_yang_lebih_baru_dari_bar_ditolak() public {
        address op2 = makeAddr("operator-lain");
        vm.prank(op2);
        reg.lock(bot, spec, "dikunci sesudah bar");                 // sekarang = asof + 1 jam
        uint64 lockedAt = reg.lockedAt(op2, bot, spec);
        vm.prank(op2);
        vm.expectRevert(abi.encodeWithSelector(SignalAnchor.LockedAfterBar.selector, lockedAt, asof));
        sa.commit(bot, spec, asof, root3, n3);
    }

    function test_bar_yang_belum_tertutup_ditolak() public {
        vm.warp(asof - 1);
        vm.prank(op);
        vm.expectRevert(abi.encodeWithSelector(SignalAnchor.BarNotClosed.selector, asof, asof - 1));
        sa.commit(bot, spec, asof, root3, n3);
    }

    function test_komit_lewat_batas_lag_ditolak() public {
        vm.warp(asof + MAX_LAG + 1);
        vm.prank(op);
        vm.expectRevert(abi.encodeWithSelector(SignalAnchor.TooLate.selector, asof, asof + MAX_LAG + 1, MAX_LAG));
        sa.commit(bot, spec, asof, root3, n3);
    }

    function test_komit_tepat_di_batas_lag_diterima() public {
        vm.warp(asof + MAX_LAG);
        _commit3();
        assertEq(sa.commitCount(), 1);
    }

    function test_komit_ganda_ditolak() public {
        bytes32 id = _commit3();
        vm.prank(op);
        vm.expectRevert(abi.encodeWithSelector(SignalAnchor.AlreadyCommitted.selector, id));
        sa.commit(bot, spec, asof, root3, n3);
    }

    function test_akar_nol_hanya_untuk_n_nol() public {
        vm.startPrank(op);
        vm.expectRevert(SignalAnchor.EmptyMismatch.selector);
        sa.commit(bot, spec, asof, bytes32(0), 3);
        vm.expectRevert(SignalAnchor.EmptyMismatch.selector);
        sa.commit(bot, spec, asof, root3, 0);
        bytes32 id = sa.commit(bot, spec, asof, bytes32(0), 0);      // bot diam pada bar ini: dikomit, bukan dilewati
        vm.stopPrank();
        SignalAnchor.Commit memory c = sa.getCommit(id);
        assertEq(c.n, 0);
        assertEq(c.root, bytes32(0));
    }

    // -------------------------------------------------- pengungkapan

    function test_ungkap_penuh_dari_vektor_engine() public {
        bytes32 id = _commit3();
        for (uint256 i = 0; i < n3; i++) {
            (SignalAnchor.Signal memory s, bytes32 salt, bytes32 leaf, bytes32[] memory proof) = _sig("tiga", i);
            vm.prank(stranger);                                     // siapa pun yang memegang muatan + salt + bukti boleh mengungkap
            sa.reveal(id, s, salt, proof);
            assertTrue(sa.isRevealed(id, leaf));
        }
        assertEq(sa.getCommit(id).revealed, n3);
    }

    function test_ungkap_ganda_ditolak() public {
        bytes32 id = _commit3();
        (SignalAnchor.Signal memory s, bytes32 salt, bytes32 leaf, bytes32[] memory proof) = _sig("tiga", 0);
        sa.reveal(id, s, salt, proof);
        vm.expectRevert(abi.encodeWithSelector(SignalAnchor.AlreadyRevealed.selector, leaf));
        sa.reveal(id, s, salt, proof);
    }

    function test_muatan_diubah_ditolak() public {
        bytes32 id = _commit3();
        (SignalAnchor.Signal memory s, bytes32 salt,, bytes32[] memory proof) = _sig("tiga", 0);
        s.bobotBaru = s.bobotBaru * 2;                              // penjual memalsukan ukuran sesudah komit
        vm.expectRevert(SignalAnchor.BadProof.selector);
        sa.reveal(id, s, salt, proof);
    }

    function test_salt_salah_ditolak() public {
        bytes32 id = _commit3();
        (SignalAnchor.Signal memory s,,, bytes32[] memory proof) = _sig("tiga", 1);
        vm.expectRevert(SignalAnchor.BadProof.selector);
        sa.reveal(id, s, keccak256("salt tebakan"), proof);
    }

    function test_sinyal_bot_atau_bar_lain_ditolak() public {
        bytes32 id = _commit3();
        (SignalAnchor.Signal memory s, bytes32 salt,, bytes32[] memory proof) = _sig("tiga", 0);
        s.asof = asof + 1 days;
        vm.expectRevert(SignalAnchor.SignalMismatch.selector);
        sa.reveal(id, s, salt, proof);
    }

    function test_n_yang_dikecilkan_tidak_bisa_menyembunyikan_daun() public {
        vm.prank(op);
        bytes32 id = sa.commit(bot, spec, asof, root3, 2);          // mengaku dua sinyal padahal akar memuat tiga
        for (uint256 i = 0; i < 2; i++) {
            (SignalAnchor.Signal memory s, bytes32 salt,, bytes32[] memory proof) = _sig("tiga", i);
            sa.reveal(id, s, salt, proof);
        }
        (SignalAnchor.Signal memory s3, bytes32 salt3,, bytes32[] memory proof3) = _sig("tiga", 2);
        vm.expectRevert(SignalAnchor.TooManyReveals.selector);
        sa.reveal(id, s3, salt3, proof3);
    }

    function test_komit_tak_dikenal_ditolak() public {
        (SignalAnchor.Signal memory s, bytes32 salt,, bytes32[] memory proof) = _sig("tiga", 0);
        vm.expectRevert(abi.encodeWithSelector(SignalAnchor.UnknownCommit.selector, bytes32(uint256(1))));
        sa.reveal(bytes32(uint256(1)), s, salt, proof);
    }

    // -------------------------------------------------- tidak-diungkap tercatat permanen

    function test_yang_tidak_diungkap_penuh_ditandai_sesudah_jendela() public {
        bytes32 id = _commit3();
        (SignalAnchor.Signal memory s, bytes32 salt,, bytes32[] memory proof) = _sig("tiga", 0);
        sa.reveal(id, s, salt, proof);
        vm.warp(asof + WINDOW + 1);
        vm.expectEmit(true, false, false, true);
        emit SignalAnchor.RevealMissed(id, 1, n3);
        vm.prank(stranger);
        sa.markMissed(id);
        assertTrue(sa.getCommit(id).missed);
        vm.expectRevert(SignalAnchor.NothingMissing.selector);
        sa.markMissed(id);
    }

    function test_tidak_bisa_ditandai_sebelum_jendela_tutup() public {
        bytes32 id = _commit3();
        vm.warp(asof + WINDOW);
        vm.expectRevert(abi.encodeWithSelector(SignalAnchor.WindowOpen.selector, asof + WINDOW));
        sa.markMissed(id);
    }

    function test_yang_diungkap_penuh_tidak_bisa_ditandai() public {
        bytes32 id = _commit3();
        for (uint256 i = 0; i < n3; i++) {
            (SignalAnchor.Signal memory s, bytes32 salt,, bytes32[] memory proof) = _sig("tiga", i);
            sa.reveal(id, s, salt, proof);
        }
        vm.warp(asof + WINDOW + 1);
        vm.expectRevert(SignalAnchor.NothingMissing.selector);
        sa.markMissed(id);
    }

    function test_bot_diam_tidak_bisa_ditandai_tidak_diungkap() public {
        vm.prank(op);
        bytes32 id = sa.commit(bot, spec, asof, bytes32(0), 0);
        vm.warp(asof + WINDOW + 1);
        vm.expectRevert(SignalAnchor.NothingMissing.selector);
        sa.markMissed(id);
    }

    function test_konstruktor_nol_ditolak() public {
        vm.expectRevert(SignalAnchor.ZeroValue.selector);
        new SignalAnchor(ILockRegistry(address(0)), MAX_LAG, WINDOW);
        vm.expectRevert(SignalAnchor.ZeroValue.selector);
        new SignalAnchor(ILockRegistry(address(reg)), 0, WINDOW);
        vm.expectRevert(SignalAnchor.ZeroValue.selector);
        new SignalAnchor(ILockRegistry(address(reg)), MAX_LAG, 0);
    }
}

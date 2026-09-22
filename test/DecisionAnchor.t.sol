// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {Vm} from "forge-std/Vm.sol";
import {DecisionAnchor} from "../contracts/DecisionAnchor.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/// Yang diuji: mekanika pencatatan, dan aturan yang membuat catatan tidak bisa dielusikan
/// (snapshot wajib, abstain wajib beralasan, kewenangan agen bisa dicabut).
/// Tidak ada satu pun test di sini yang mengklaim membuktikan keputusan model itu benar —
/// kontrak ini memang tidak bisa membuktikannya, dan test tidak boleh berpura-pura bisa.
contract DecisionAnchorTest is Test {
    DecisionAnchor internal a;
    address internal agentA = makeAddr("desk-likuiditas");
    address internal agentB = makeAddr("desk-arus-pintar");
    address internal stranger = makeAddr("orang-luar");

    bytes32 internal constant SNAP = keccak256("bsc-universe-snapshot-0001");

    function setUp() public {
        a = new DecisionAnchor();
        a.registerAgent(agentA, "likuiditas");
        a.registerAgent(agentB, "arus-pintar");
    }

    function _enter(address who, string memory asset, string memory seed) internal returns (bytes32) {
        vm.prank(who);
        return a.anchor(asset, DecisionAnchor.Verdict.Enter, keccak256(bytes(seed)), bytes32(0), SNAP);
    }

    // -------------------------------------------------- registrasi & kendali otoritas

    function test_roster_dan_agent_tercatat() public view {
        DecisionAnchor.Agent memory rec = a.getAgent(agentA);
        assertEq(rec.handler, agentA, "handler");
        assertEq(rec.label, "likuiditas", "label");
        assertTrue(rec.active, "aktif sejak lahir");
        assertEq(a.agents().length, 2, "roster dua agen");
        assertEq(a.countByAgent(agentA), 0, "belum ada keputusan");
    }

    function test_registrasi_ganda_ditolak() public {
        vm.expectRevert(DecisionAnchor.AlreadyAnAgent.selector);
        a.registerAgent(agentA, "nama-lain");
    }

    function test_registrasi_alamat_nol_ditolak() public {
        vm.expectRevert(DecisionAnchor.ZeroAgent.selector);
        a.registerAgent(address(0), "kosong");
    }

    function test_label_kosong_ditolak() public {
        vm.expectRevert(DecisionAnchor.EmptyLabel.selector);
        a.registerAgent(makeAddr("agen-c"), "");
    }

    function test_bukan_owner_tidak_bisa_mendaftarkan_agen() public {
        vm.prank(stranger);
        vm.expectRevert(abi.encodeWithSelector(Ownable.OwnableUnauthorizedAccount.selector, stranger));
        a.registerAgent(stranger, "diri-sendiri");
    }

    // ------------------------------------------------------------- pencatatan

    function test_agen_mencatat_untuk_dirinya_sendiri() public {
        bytes32 decision = keccak256("enter-WBNB-p0.62");
        vm.prank(agentA);
        bytes32 id = a.anchor("WBNB/USDT", DecisionAnchor.Verdict.Enter, decision, bytes32(0), SNAP);

        DecisionAnchor.Anchor memory rec = a.getAnchor(id);
        assertEq(rec.agent, agentA, "penanda tangan = agen itu sendiri, bukan backend");
        assertEq(rec.decisionHash, decision, "hash keputusan utuh");
        assertEq(rec.snapshotHash, SNAP, "terikat snapshot point-in-time");
        assertEq(uint8(rec.verdict), uint8(DecisionAnchor.Verdict.Enter), "verdict Enter");
        assertEq(rec.anchoredAt, uint64(block.timestamp), "stempel waktu blok");
        assertEq(a.countByAgent(agentA), 1, "hitungan per-agen naik");
    }

    function test_event_dipancarkan_dengan_id_dan_agent_terindexed() public {
        bytes32 decision = keccak256("event-check");
        bytes32 expectedId = keccak256(abi.encode(agentA, decision, SNAP, block.chainid));

        vm.recordLogs();
        vm.prank(agentA);
        bytes32 id = a.anchor("WBNB/USDT", DecisionAnchor.Verdict.Enter, decision, bytes32(0), SNAP);
        assertEq(id, expectedId, "id deterministik dari (agen, keputusan, snapshot, chainid)");

        Vm.Log[] memory logs = vm.getRecordedLogs();
        assertEq(logs.length, 1, "satu event");
        assertEq(logs[0].topics[0], keccak256("Anchored(bytes32,address,string,uint8,bytes32,bytes32)"),
            "selector event");
        assertEq(logs[0].topics[1], bytes32(expectedId), "topic1 = id (terindeks)");
        assertEq(uint160(uint256(logs[0].topics[2])), uint160(agentA), "topic2 = agen (terindeks)");
    }

    function test_panggilan_dari_luar_roster_ditolak() public {
        vm.prank(stranger);
        vm.expectRevert(DecisionAnchor.NotAnAgent.selector);
        a.anchor("WBNB/USDT", DecisionAnchor.Verdict.Enter, keccak256("d"), bytes32(0), SNAP);
    }

    function test_tanpa_snapshot_tidak_bisa_mencatat() public {
        vm.prank(agentA);
        vm.expectRevert(DecisionAnchor.MissingSnapshot.selector);
        a.anchor("WBNB/USDT", DecisionAnchor.Verdict.Enter, keccak256("d2"), bytes32(0), bytes32(0));
    }

    function test_tanpa_keputusan_tidak_bisa_mencatat() public {
        vm.prank(agentA);
        vm.expectRevert(DecisionAnchor.MissingDecision.selector);
        a.anchor("WBNB/USDT", DecisionAnchor.Verdict.Enter, bytes32(0), keccak256("g"), SNAP);
    }

    function test_asset_kosong_ditolak() public {
        vm.prank(agentA);
        vm.expectRevert(DecisionAnchor.EmptyAsset.selector);
        a.anchor("", DecisionAnchor.Verdict.Enter, keccak256("d3"), bytes32(0), SNAP);
    }

    // ------------------------------------- abstain = hasil, tapi wajib bawa alasan

    function test_abstain_tanpa_alasan_ditolak() public {
        vm.prank(agentA);
        vm.expectRevert(DecisionAnchor.AbstainWithoutReason.selector);
        a.anchor("WBNB/USDT", DecisionAnchor.Verdict.Abstain, keccak256("a"), bytes32(0), SNAP);
    }

    function test_abstain_dengan_alasan_tersimpan_hasil() public {
        bytes32 gates = keccak256("likuiditas<50k; umur<24h; top10>45%");
        vm.prank(agentA);
        a.anchor("WBNB/USDT", DecisionAnchor.Verdict.Abstain, keccak256("a2"), gates, SNAP);
        assertEq(a.countByVerdict(DecisionAnchor.Verdict.Abstain), 1,
            "penolakan dihitung sebagai hasil, bukan sebagai ketiadaan hasil");
    }

    function test_keputusan_sama_tidak_dihitung_dua_kali() public {
        bytes32 decision = keccak256("satu-keputusan-yang-sama");
        vm.prank(agentA);
        a.anchor("WBNB/USDT", DecisionAnchor.Verdict.Enter, decision, bytes32(0), SNAP);
        vm.prank(agentB);
        vm.expectRevert(abi.encodeWithSelector(DecisionAnchor.DuplicateDecision.selector, decision));
        a.anchor("WBNB/USDT", DecisionAnchor.Verdict.Enter, decision, bytes32(0), SNAP);
    }

    // ------------------------------------------------------ rem darurat on-chain

    function test_agen_yang_dicabut_tidak_lagi_bisa_mencatat() public {
        a.setAgentActive(agentA, false);
        vm.prank(agentA);
        vm.expectRevert(DecisionAnchor.AgentInactive.selector);
        a.anchor("WBNB/USDT", DecisionAnchor.Verdict.Enter, keccak256("d4"), bytes32(0), SNAP);
    }

    function test_mencabut_agen_yang_tidak_dikenal_ditolak() public {
        vm.expectRevert(DecisionAnchor.UnknownAgent.selector);
        a.setAgentActive(stranger, false);
    }

    function test_memasang_lagi_kembali_memulihkan_agen() public {
        a.setAgentActive(agentA, false);
        a.setAgentActive(agentA, true);
        bytes32 id = _enter(agentA, "WBNB/USDT", "d5");
        assertTrue(a.getAnchor(id).anchoredAt > 0, "agen pulih");
    }

    function test_owner_tidak_punya_jalan_pintas_mencatat_atas_nama_agen() public {
        // owner bisa MENDAFTARKAN agen, tapi tidak bisa anchor tanpa terdaftar sebagai agen aktif.
        // Jejak pendaftaran terekspos lewat event, jadi jalur ini tidak senyap.
        vm.expectRevert(DecisionAnchor.NotAnAgent.selector);
        a.anchor("WBNB/USDT", DecisionAnchor.Verdict.Enter, keccak256("owner-lane"), bytes32(0), SNAP);
    }

    // --------------------------------------------------------- agregasi untuk panel

    function test_hitungan_memisahkan_enter_dari_abstain() public {
        bytes32 gates = keccak256("gate-log");
        for (uint256 i = 0; i < 3; i++) {
            vm.prank(agentA);
            a.anchor("AKE/USDT", DecisionAnchor.Verdict.Abstain, keccak256(abi.encode("ab", i)), gates, SNAP);
        }
        _enter(agentB, "BTCB/USDT", "en1");

        assertEq(a.anchorCount(), 4, "total catatan");
        assertEq(a.countByVerdict(DecisionAnchor.Verdict.Abstain), 3, "tiga penolakan");
        assertEq(a.countByVerdict(DecisionAnchor.Verdict.Enter), 1, "satu eksekusi");
        assertEq(a.countByAgent(agentA), 3, "per-agen");
        assertTrue(a.anchorIdAt(0) != bytes32(0), "id bisa dibaca lewat indeks");
    }

    // ------------------------------------------------------------- fuzz: aturan rapat

    /// @notice Bentuk fuzz-nya sengaja menyiksa sisi abstain: apa pun nilai gatesHash, abstain
    ///         tanpa alasan tetap tidak boleh masuk. Di sinilah bug "nilai kosong dianggap lulus"
    ///         biasanya muncul.
    function testFuzz_abstain_tidak_pernah_lolos_tanpa_alasan(bytes32 gates) public {
        vm.prank(agentA);
        if (gates == bytes32(0)) {
            vm.expectRevert(DecisionAnchor.AbstainWithoutReason.selector);
            a.anchor("X/USDT", DecisionAnchor.Verdict.Abstain, keccak256(abi.encode(gates, "a")), gates, SNAP);
        } else {
            a.anchor("X/USDT", DecisionAnchor.Verdict.Abstain, keccak256(abi.encode(gates, "b")), gates, SNAP);
            assertEq(a.countByVerdict(DecisionAnchor.Verdict.Abstain), 1, "tersimpan");
        }
    }

    function testFuzz_snapshot_dan_keputusan_selalu_diwajibkan(bytes32 snap, bytes32 decision) public {
        vm.prank(agentA);
        if (snap == bytes32(0) || decision == bytes32(0)) {
            vm.expectRevert();
            a.anchor("Y/USDT", DecisionAnchor.Verdict.Enter, decision, bytes32(0), snap);
        } else {
            bytes32 id = a.anchor("Y/USDT", DecisionAnchor.Verdict.Enter, decision, bytes32(0), snap);
            assertEq(a.getAnchor(id).snapshotHash, snap, "snapshot tersimpan apa adanya");
        }
    }
}

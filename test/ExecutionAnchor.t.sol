// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test, Vm} from "forge-std/Test.sol";
import {LockRegistry} from "../contracts/LockRegistry.sol";
import {SignalAnchor, ILockRegistry} from "../contracts/SignalAnchor.sol";
import {ExecutionAnchor, ISignalAnchorView} from "../contracts/ExecutionAnchor.sol";

/// Yang diuji (P132, F-D96): catatan isi order hanya bisa dibuat (1) untuk komit SignalAnchor yang ada, (2) oleh committer komit itu,
/// (3) bila order mengaku dikirim SESUDAH komit dan diisi sesudah dikirim, (4) sekali per (pelapor, venue, clientOrderId); batch all-or-nothing;
/// event membawa seluruh metadata. Tidak ada tes yang mengklaim venue benar-benar mengisi order - kontrak ini tidak bisa membuktikannya.
contract ExecutionAnchorTest is Test {
    LockRegistry internal reg;
    SignalAnchor internal sa;
    ExecutionAnchor internal xa;
    address internal op = makeAddr("operator-fabius");
    address internal stranger = makeAddr("orang-luar");
    bytes32 internal constant BOT = "B1-TREND";
    bytes32 internal constant SPEC = keccak256("spec-b1");
    uint64 internal asof;
    bytes32 internal cid;
    uint64 internal committedAt;

    function setUp() public {
        reg = new LockRegistry();
        sa = new SignalAnchor(ILockRegistry(address(reg)), 12 hours, 7 days);
        xa = new ExecutionAnchor(ISignalAnchorView(address(sa)));
        asof = 1_790_985_600;                                       // 2026-10-04 00:00Z (penutupan bar 10-03)
        vm.warp(asof - 2 days);
        vm.prank(op);
        reg.lock(BOT, SPEC, "engine/spec.py@B1-TREND");
        vm.warp(asof + 8 hours);
        vm.prank(op);
        cid = sa.commit(BOT, SPEC, asof, bytes32(0), 0);
        committedAt = uint64(block.timestamp);
        vm.warp(asof + 9 hours);
    }

    function fill(bytes32 clientId, bool real, uint64 tSent) internal view returns (ExecutionAnchor.Fill memory f) {
        f = ExecutionAnchor.Fill({commitId: cid, venue: "binance-live", symbol: "XRPUSDT", clientOrderId: clientId, venueOrderId: 123456789,
                                  side: 1, real: real, tSent: tSent, tFilled: tSent + 300, qty: 3_4000_0000, avgPrice: 1_5005_0000,
                                  fee: 204_0000, feeAsset: "USDT", reportHash: keccak256("baris laporan")});
    }

    function test_a_real_fill_after_the_commit_is_recorded_once_with_all_metadata() public {
        uint64 t = (committedAt + 120) * 1000;
        vm.recordLogs();
        vm.prank(op);
        bytes32 key = xa.record(fill("fxaaaa", true, t));
        assertEq(key, xa.keyOf(op, "binance-live", "fxaaaa"));
        assertEq(xa.recordedAt(key), uint64(block.timestamp));
        assertEq(xa.fillCount(), 1);
        assertEq(xa.realFillCount(), 1);
        Vm.Log[] memory logs = vm.getRecordedLogs();
        assertEq(logs.length, 1);
        assertEq(logs[0].topics[1], key);
        assertEq(logs[0].topics[2], bytes32(uint256(uint160(op))));
        assertEq(logs[0].topics[3], cid);
        (ExecutionAnchor.Fill memory got,) = abi.decode(logs[0].data, (ExecutionAnchor.Fill, uint64));
        assertEq(got.symbol, bytes32("XRPUSDT"));
        assertEq(got.avgPrice, 1_5005_0000);
        assertTrue(got.real);
        vm.prank(op);
        vm.expectRevert(abi.encodeWithSelector(ExecutionAnchor.AlreadyRecorded.selector, key));
        xa.record(fill("fxaaaa", true, t));
    }

    function test_an_order_claimed_before_its_commit_cannot_be_recorded() public {
        uint64 early = (committedAt - 60) * 1000;
        vm.prank(op);
        vm.expectRevert(abi.encodeWithSelector(ExecutionAnchor.SentBeforeCommit.selector, committedAt - 60, committedAt));
        xa.record(fill("fxbbbb", true, early));
        ExecutionAnchor.Fill memory f = fill("fxcccc", true, (committedAt + 5) * 1000);
        f.tFilled = f.tSent - 1;
        vm.prank(op);
        vm.expectRevert(abi.encodeWithSelector(ExecutionAnchor.FilledBeforeSent.selector, f.tSent, f.tFilled));
        xa.record(f);
    }

    function test_only_the_committer_of_an_existing_commit_can_record() public {
        uint64 t = (committedAt + 120) * 1000;
        vm.prank(stranger);
        vm.expectRevert(abi.encodeWithSelector(ExecutionAnchor.NotCommitter.selector, stranger, op));
        xa.record(fill("fxdddd", true, t));
        ExecutionAnchor.Fill memory f = fill("fxeeee", true, t);
        f.commitId = keccak256("tidak-ada");
        vm.prank(op);
        vm.expectRevert(abi.encodeWithSelector(ExecutionAnchor.UnknownCommit.selector, f.commitId));
        xa.record(f);
        f = fill("fxffff", true, t);
        f.side = 3;
        vm.prank(op);
        vm.expectRevert(abi.encodeWithSelector(ExecutionAnchor.BadSide.selector, uint8(3)));
        xa.record(f);
        f = fill("fxgggg", true, t);
        f.qty = 0;
        vm.prank(op);
        vm.expectRevert(ExecutionAnchor.ZeroValue.selector);
        xa.record(f);
    }

    function test_a_batch_is_all_or_nothing_and_demo_fills_are_counted_apart() public {
        uint64 t = (committedAt + 120) * 1000;
        ExecutionAnchor.Fill[] memory ok = new ExecutionAnchor.Fill[](2);
        ok[0] = fill("fx0001", true, t);
        ok[1] = fill("fx0002", false, t);
        vm.prank(op);
        bytes32[] memory keys = xa.recordBatch(ok);
        assertEq(keys.length, 2);
        assertEq(xa.fillCount(), 2);
        assertEq(xa.realFillCount(), 1);
        ExecutionAnchor.Fill[] memory bad = new ExecutionAnchor.Fill[](2);
        bad[0] = fill("fx0003", true, t);
        bad[1] = fill("fx0003", true, t);                            // duplikat di batch yang sama
        vm.prank(op);
        vm.expectRevert();
        xa.recordBatch(bad);
        assertEq(xa.recordedAt(xa.keyOf(op, "binance-live", "fx0003")), 0);   // tidak ada catatan setengah
        assertEq(xa.fillCount(), 2);
    }
}

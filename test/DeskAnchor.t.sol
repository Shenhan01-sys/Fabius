// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {DeskAnchor} from "../contracts/DeskAnchor.sol";

/// Yang diuji (P152, F-D109): root keputusan satu siklus 5 menit hanya diterima dari committer, SELAMA siklus itu berjalan (bukan sebelum dimulai,
/// bukan sesudah berakhir - saat harga penentu hasilnya sudah ada), sekali per siklus, root dan jumlah daun bukan nol; event membawa semuanya.
contract DeskAnchorTest is Test {
    DeskAnchor desk;
    address committer = address(0xC0);
    uint64 constant T = 1_791_200_100; // kelipatan 300
    bytes32 constant R = keccak256("root");

    event Cycle(uint64 indexed cycleStart, bytes32 root, uint16 n);

    function setUp() public {
        desk = new DeskAnchor(committer);
        vm.warp(T + 250);
    }

    function test_the_committer_anchors_one_root_while_the_cycle_runs() public {
        vm.expectEmit(true, false, false, true);
        emit Cycle(T, R, 3);
        vm.prank(committer);
        desk.commit(T, R, 3);
        assertEq(desk.rootOf(T), R);
    }

    function test_only_the_committer_can_anchor() public {
        vm.expectRevert(DeskAnchor.NotCommitter.selector);
        desk.commit(T, R, 3);
    }

    function test_a_root_after_the_cycle_ended_is_too_late() public {
        vm.warp(T + 300);
        vm.prank(committer);
        vm.expectRevert(DeskAnchor.TooLate.selector);
        desk.commit(T, R, 3);
    }

    function test_future_or_misaligned_cycles_and_empty_roots_are_refused() public {
        vm.startPrank(committer);
        vm.expectRevert(DeskAnchor.BadCycle.selector);
        desk.commit(T + 300, R, 3);
        vm.expectRevert(DeskAnchor.BadCycle.selector);
        desk.commit(T + 1, R, 3);
        vm.expectRevert(DeskAnchor.ZeroRoot.selector);
        desk.commit(T, bytes32(0), 3);
        vm.expectRevert(DeskAnchor.ZeroRoot.selector);
        desk.commit(T, R, 0);
        vm.stopPrank();
    }

    function test_one_root_per_cycle() public {
        vm.startPrank(committer);
        desk.commit(T, R, 3);
        vm.expectRevert(DeskAnchor.AlreadyCommitted.selector);
        desk.commit(T, keccak256("lain"), 3);
        vm.stopPrank();
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {SelectionAnchor, IIdentityRegistry8004} from "../contracts/SelectionAnchor.sol";

/// Tiruan IdentityRegistry ERC-8004: hanya dua fungsi yang dipakai SelectionAnchor.
contract FakeIdentity is IIdentityRegistry8004 {
    mapping(uint256 => address) public owners;
    mapping(uint256 => address) public wallets;

    function set(uint256 id, address owner, address wallet) external {
        owners[id] = owner;
        wallets[id] = wallet;
    }

    function ownerOf(uint256 id) external view returns (address) {
        address o = owners[id];
        require(o != address(0), "ERC721NonexistentToken");
        return o;
    }

    function getAgentWallet(uint256 id) external view returns (address) {
        return wallets[id];
    }
}

/// Yang diuji (P141, F-D102): pilihan hanya bisa dibuat oleh dompet/pemilik identitas agent itu, SEBELUM penutupan bar harian yang dipilih (paling
/// jauh 2 hari ke depan), sekali per (agent, bar), dengan bot + hash alasan bukan nol dan keyakinan <= 100; event membawa semuanya.
contract SelectionAnchorTest is Test {
    FakeIdentity internal idr;
    SelectionAnchor internal sel;
    address internal owner = makeAddr("pemilik-agen");
    address internal wallet = makeAddr("dompet-agen");
    address internal stranger = makeAddr("orang-luar");
    uint256 internal constant AGENT = 2501;
    uint64 internal constant CLOSE = 1_791_072_000;                 // 2026-10-05 00:00Z (penutupan bar 10-04)
    bytes32 internal constant BOT = "B1-TREND";
    bytes32 internal constant WHY = keccak256("alasan");

    function setUp() public {
        idr = new FakeIdentity();
        sel = new SelectionAnchor(idr);
        idr.set(AGENT, owner, wallet);
        vm.warp(CLOSE - 10 hours);
    }

    function test_AgentWalletPicksBeforeCloseAndEventCarriesEverything() public {
        vm.expectEmit(true, true, true, true);
        emit SelectionAnchor.Picked(AGENT, CLOSE, BOT, 62, WHY, wallet);
        vm.prank(wallet);
        sel.pick(AGENT, CLOSE, BOT, 62, WHY);
        SelectionAnchor.Pick memory p = sel.getPick(AGENT, CLOSE);
        assertEq(p.botId, BOT);
        assertEq(p.confidence, 62);
        assertEq(p.reasonHash, WHY);
        assertEq(p.committedAt, uint64(block.timestamp));
        assertEq(sel.barCount(AGENT), 1);
        assertEq(sel.barAt(AGENT, 0), CLOSE);
    }

    function test_OwnerMayPickButNotAStranger() public {
        vm.prank(owner);
        sel.pick(AGENT, CLOSE, BOT, 50, WHY);
        vm.prank(stranger);
        vm.expectRevert(SelectionAnchor.NotAgent.selector);
        sel.pick(AGENT, CLOSE + 1 days, BOT, 50, WHY);
    }

    function test_NoPickAtOrAfterTheClose() public {
        vm.warp(CLOSE);
        vm.prank(wallet);
        vm.expectRevert(SelectionAnchor.TooLate.selector);
        sel.pick(AGENT, CLOSE, BOT, 50, WHY);
    }

    function test_OnePickPerAgentAndBar() public {
        vm.startPrank(wallet);
        sel.pick(AGENT, CLOSE, BOT, 50, WHY);
        vm.expectRevert(SelectionAnchor.AlreadyPicked.selector);
        sel.pick(AGENT, CLOSE, "B3-CARRY", 90, WHY);
        vm.stopPrank();
    }

    function test_RejectsBadInputs() public {
        vm.startPrank(wallet);
        vm.expectRevert(SelectionAnchor.ZeroValue.selector);
        sel.pick(AGENT, CLOSE, bytes32(0), 50, WHY);
        vm.expectRevert(SelectionAnchor.ZeroValue.selector);
        sel.pick(AGENT, CLOSE, BOT, 50, bytes32(0));
        vm.expectRevert(SelectionAnchor.BadConfidence.selector);
        sel.pick(AGENT, CLOSE, BOT, 101, WHY);
        vm.expectRevert(SelectionAnchor.BadBar.selector);
        sel.pick(AGENT, CLOSE + 1 hours, BOT, 50, WHY);              // bukan penutupan 00:00Z
        vm.expectRevert(SelectionAnchor.BadBar.selector);
        sel.pick(AGENT, CLOSE + 3 days, BOT, 50, WHY);               // terlalu jauh ke depan
        vm.stopPrank();
    }

    function test_UnknownAgentIsRejected() public {
        vm.prank(wallet);
        vm.expectRevert();
        sel.pick(9999, CLOSE, BOT, 50, WHY);
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console2} from "forge-std/Script.sol";
import {LockRegistry} from "../contracts/LockRegistry.sol";
import {SignalAnchor, ILockRegistry} from "../contracts/SignalAnchor.sol";

/// M3 (F-D79): deploy `LockRegistry` (C-A) lalu `SignalAnchor` v2 (C-B) yang membaca registry itu.
///
///   forge script script/DeploySignalAnchor.s.sol --rpc-url bscTestnet --broadcast -vv      # MENGIRIM transaksi - hanya atas kata builder
///
/// Butuh `DEPLOYER_PRIVATE_KEY` di environment. Parameter waktu (bisa diganti lewat env, bawaan di bawah):
///   SIGNAL_MAX_LAG_S       = 43200  (12 jam: sama dengan guard umur bar di engine/ledger; komit lebih lambat ditolak kontrak)
///   SIGNAL_REVEAL_WINDOW_S = 604800 (7 hari sesudah penutupan bar; sesudahnya komit yang tidak diungkap penuh bisa ditandai TIDAK-DIUNGKAP)
/// Kedua angka ini immutable: mengubahnya = deploy kontrak baru (alamat baru), bukan menyunting yang lama.
/// Alamat hasil deploy dibaca dari broadcast/ run-latest.json - bukan dari log di layar.
contract DeploySignalAnchorScript is Script {
    function run() external returns (LockRegistry registry, SignalAnchor anchor) {
        uint256 pk = vm.envUint("DEPLOYER_PRIVATE_KEY");
        uint64 maxLag = uint64(vm.envOr("SIGNAL_MAX_LAG_S", uint256(12 hours)));
        uint64 window = uint64(vm.envOr("SIGNAL_REVEAL_WINDOW_S", uint256(7 days)));

        vm.startBroadcast(pk);
        registry = new LockRegistry();
        anchor = new SignalAnchor(ILockRegistry(address(registry)), maxLag, window);
        vm.stopBroadcast();

        console2.log("LockRegistry :", address(registry));
        console2.log("SignalAnchor :", address(anchor));
        console2.log("maxLag (s)   :", uint256(maxLag));
        console2.log("window (s)   :", uint256(window));
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console2} from "forge-std/Script.sol";
import {BotRegistry} from "../contracts/BotRegistry.sol";
import {ILockRegistry} from "../contracts/SignalAnchor.sol";

/// P81 (C-H): deploy `BotRegistry` (yang memasang implementasi `RevenueSplitter` di konstruktornya). BELUM PERNAH DIJALANKAN ke chain mana pun.
///
///   forge script script/DeployBotRegistry.s.sol --rpc-url bscTestnet -vv                # simulasi terhadap chain 97 (tanpa transaksi)
///   forge script script/DeployBotRegistry.s.sol --rpc-url bscTestnet --broadcast -vv    # MENGIRIM transaksi - hanya atas kata builder
///
/// Butuh `DEPLOYER_PRIVATE_KEY` di environment. Parameter (env, bawaan di bawah):
///   BOT_REGISTRY_OWNER     = alamat deployer   operator Fabius (Ownable2Step); juga "Fabius" bagi setiap splitter
///   LOCK_REGISTRY          = 0xcF6f…Bb0C       LockRegistry chain 97 (deployments/97.json -> contracts.LockRegistry)
///   BOT_REGISTRY_ANCHORER  = 0xCA9c…64A4       committer M3 (deployments/97.json -> m3.committer): pin-nya yang dihitung
///   FABIUS_PAYEE           = BOT_REGISTRY_OWNER dompet Fabius untuk splitter baru
///   FABIUS_BPS             = 4000              bagian Fabius awal (engine/economics.py FABIUS_SHARE_BPS, kunci v1 F-D73); immutable
/// `implementation`, `locks`, `initialFabiusBps` immutable: mengubahnya = registry baru = alamat splitter baru (payTo lama tetap milik registry lama).
/// Sesudah deploy dibaca ulang (pemilik, locks, anchorer, payee, bps, kode implementasi); alamat dibaca dari broadcast/ run-latest.json.
contract DeployBotRegistryScript is Script {
    address internal constant LOCK_REGISTRY_97 = 0xcF6fBF95fc04DEd8d670512CEc0723a2246Fbb0C;
    address internal constant COMMITTER_97 = 0xCA9c7322210E9a7F7d0953c862d4Ef60cC0D64A4;

    function run() external returns (BotRegistry reg) {
        uint256 pk = vm.envUint("DEPLOYER_PRIVATE_KEY");
        address owner = vm.envOr("BOT_REGISTRY_OWNER", vm.addr(pk));
        address locks = vm.envOr("LOCK_REGISTRY", LOCK_REGISTRY_97);
        address anchorer = vm.envOr("BOT_REGISTRY_ANCHORER", COMMITTER_97);
        address payee = vm.envOr("FABIUS_PAYEE", owner);
        uint256 bps = vm.envOr("FABIUS_BPS", uint256(4000));
        require(bps <= 10_000, "FABIUS_BPS di atas 10000");
        require(locks.code.length > 0, "LOCK_REGISTRY tanpa kode di chain ini - berhenti sebelum mengirim");

        vm.startBroadcast(pk);
        reg = new BotRegistry(owner, ILockRegistry(locks), anchorer, payee, uint16(bps));
        vm.stopBroadcast();

        require(reg.owner() == owner && address(reg.locks()) == locks && reg.anchorer() == anchorer, "baca ulang: owner/locks/anchorer beda");
        require(reg.fabiusPayee() == payee && reg.initialFabiusBps() == bps, "baca ulang: payee/bps beda");
        require(reg.implementation().code.length > 0, "baca ulang: implementasi tanpa kode");

        console2.log("BotRegistry    :", address(reg));
        console2.log("implementation :", reg.implementation());
        console2.log("owner          :", owner);
        console2.log("anchorer       :", anchorer);
        console2.log("fabiusPayee    :", payee);
        console2.log("fabiusBps awal :", bps);
    }
}

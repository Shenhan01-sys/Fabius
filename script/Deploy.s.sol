// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script, console2} from "forge-std/Script.sol";
import {DecisionAnchor} from "../contracts/DecisionAnchor.sol";

/// Deploy DecisionAnchor dan (opsional) mendaftarkan agen pertamanya.
///
///   forge script script/Deploy.s.sol --rpc-url bscTestnet --broadcast -vv
///
/// Butuh `DEPLOYER_PRIVATE_KEY` di environment. Kalau `AGENT_ADDRESS` + `AGENT_LABEL` ikut diisi,
/// agen itu didaftarkan dalam transaksi berikutnya, jadi kontrak langsung punya satu pencatat
/// yang sah dan address-nya bisa langsung ditempel ke submission.
///
/// Address hasil deploy dibaca dari broadcast/ run-latest.json — bukan dari log di layar,
/// karena klaim "sudah ter-deploy" harus terbukti dari keadaan chain.
contract DeployScript is Script {
    function run() external returns (DecisionAnchor anchor) {
        uint256 pk = vm.envUint("DEPLOYER_PRIVATE_KEY");

        vm.startBroadcast(pk);
        anchor = new DecisionAnchor();

        address agent = vm.envOr("AGENT_ADDRESS", address(0));
        if (agent != address(0)) {
            string memory label = vm.envOr("AGENT_LABEL", string("desk-utama"));
            anchor.registerAgent(agent, label);
        }
        vm.stopBroadcast();

        console2.log("DecisionAnchor:", address(anchor));
        console2.log("deployer     :", vm.addr(pk));
        console2.log("chainid      :", block.chainid);
    }
}

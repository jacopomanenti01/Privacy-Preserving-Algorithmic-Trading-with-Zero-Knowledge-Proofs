// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Script, console} from "../lib/forge-std/src/Script.sol";
import {ModelRegistry} from "../src/model.sol";

contract CounterScript is Script {
    ModelRegistry public modelRegistry;

    function setUp() public {}

    function run() public {
        string memory initialHash = vm.envString("HASH_MODEL");
        vm.startBroadcast();

        modelRegistry = new ModelRegistry(initialHash);

        vm.stopBroadcast();
    }
}

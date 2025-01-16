// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

import {Script, console} from "../lib/forge-std/src/Script.sol";
import {Verifier} from "../src/verifier.sol";

contract CounterScript is Script {
    Verifier public verifier;

    function setUp() public {}

    function run() public {
        vm.startBroadcast();
        verifier = new Verifier();

        vm.stopBroadcast();
    }
}

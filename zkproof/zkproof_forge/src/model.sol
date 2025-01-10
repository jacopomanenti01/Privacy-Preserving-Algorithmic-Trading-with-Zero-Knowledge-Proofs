// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

contract ModelRegistry {
    string public modelHash;
    address public owner;

    event ModelHashUpdated(string oldHash, string newHash, uint256 timestamp);

    constructor(string memory _initialHash) {
        require(bytes(_initialHash).length > 0, "Initial hash cannot be empty");
        modelHash = _initialHash;
        owner = msg.sender;
    }

    function updateModelHash(string memory _hash) public {
        require(msg.sender == owner, "Only owner can update the hash");
        require(bytes(_hash).length > 0, "Hash cannot be empty");
        require(keccak256(bytes(_hash)) != keccak256(bytes(modelHash)), "Hash has not changed");

        string memory oldHash = modelHash; // Save the current hash
        modelHash = _hash; // Update with the new hash

        emit ModelHashUpdated(oldHash, _hash, block.timestamp);
    }
}

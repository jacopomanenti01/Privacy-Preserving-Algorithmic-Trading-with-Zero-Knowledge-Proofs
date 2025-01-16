// This file is MIT Licensed.
//
// Copyright 2017 Christian Reitwiessner
// Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
// The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
pragma solidity ^0.8.0;
library Pairing {
    struct G1Point {
        uint X;
        uint Y;
    }
    // Encoding of field elements is: X[0] * z + X[1]
    struct G2Point {
        uint[2] X;
        uint[2] Y;
    }
    /// @return the generator of G1
    function P1() pure internal returns (G1Point memory) {
        return G1Point(1, 2);
    }
    /// @return the generator of G2
    function P2() pure internal returns (G2Point memory) {
        return G2Point(
            [10857046999023057135944570762232829481370756359578518086990519993285655852781,
             11559732032986387107991004021392285783925812861821192530917403151452391805634],
            [8495653923123431417604973247489272438418190587263600148770280649306958101930,
             4082367875863433681332203403145435568316851327593401208105741076214120093531]
        );
    }
    /// @return the negation of p, i.e. p.addition(p.negate()) should be zero.
    function negate(G1Point memory p) pure internal returns (G1Point memory) {
        // The prime q in the base field F_q for G1
        uint q = 21888242871839275222246405745257275088696311157297823662689037894645226208583;
        if (p.X == 0 && p.Y == 0)
            return G1Point(0, 0);
        return G1Point(p.X, q - (p.Y % q));
    }
    /// @return r the sum of two points of G1
    function addition(G1Point memory p1, G1Point memory p2) internal view returns (G1Point memory r) {
        uint[4] memory input;
        input[0] = p1.X;
        input[1] = p1.Y;
        input[2] = p2.X;
        input[3] = p2.Y;
        bool success;
        assembly {
            success := staticcall(sub(gas(), 2000), 6, input, 0xc0, r, 0x60)
            // Use "invalid" to make gas estimation work
            switch success case 0 { invalid() }
        }
        require(success);
    }


    /// @return r the product of a point on G1 and a scalar, i.e.
    /// p == p.scalar_mul(1) and p.addition(p) == p.scalar_mul(2) for all points p.
    function scalar_mul(G1Point memory p, uint s) internal view returns (G1Point memory r) {
        uint[3] memory input;
        input[0] = p.X;
        input[1] = p.Y;
        input[2] = s;
        bool success;
        assembly {
            success := staticcall(sub(gas(), 2000), 7, input, 0x80, r, 0x60)
            // Use "invalid" to make gas estimation work
            switch success case 0 { invalid() }
        }
        require (success);
    }
    /// @return the result of computing the pairing check
    /// e(p1[0], p2[0]) *  .... * e(p1[n], p2[n]) == 1
    /// For example pairing([P1(), P1().negate()], [P2(), P2()]) should
    /// return true.
    function pairing(G1Point[] memory p1, G2Point[] memory p2) internal view returns (bool) {
        require(p1.length == p2.length);
        uint elements = p1.length;
        uint inputSize = elements * 6;
        uint[] memory input = new uint[](inputSize);
        for (uint i = 0; i < elements; i++)
        {
            input[i * 6 + 0] = p1[i].X;
            input[i * 6 + 1] = p1[i].Y;
            input[i * 6 + 2] = p2[i].X[1];
            input[i * 6 + 3] = p2[i].X[0];
            input[i * 6 + 4] = p2[i].Y[1];
            input[i * 6 + 5] = p2[i].Y[0];
        }
        uint[1] memory out;
        bool success;
        assembly {
            success := staticcall(sub(gas(), 2000), 8, add(input, 0x20), mul(inputSize, 0x20), out, 0x20)
            // Use "invalid" to make gas estimation work
            switch success case 0 { invalid() }
        }
        require(success);
        return out[0] != 0;
    }
    /// Convenience method for a pairing check for two pairs.
    function pairingProd2(G1Point memory a1, G2Point memory a2, G1Point memory b1, G2Point memory b2) internal view returns (bool) {
        G1Point[] memory p1 = new G1Point[](2);
        G2Point[] memory p2 = new G2Point[](2);
        p1[0] = a1;
        p1[1] = b1;
        p2[0] = a2;
        p2[1] = b2;
        return pairing(p1, p2);
    }
    /// Convenience method for a pairing check for three pairs.
    function pairingProd3(
            G1Point memory a1, G2Point memory a2,
            G1Point memory b1, G2Point memory b2,
            G1Point memory c1, G2Point memory c2
    ) internal view returns (bool) {
        G1Point[] memory p1 = new G1Point[](3);
        G2Point[] memory p2 = new G2Point[](3);
        p1[0] = a1;
        p1[1] = b1;
        p1[2] = c1;
        p2[0] = a2;
        p2[1] = b2;
        p2[2] = c2;
        return pairing(p1, p2);
    }
    /// Convenience method for a pairing check for four pairs.
    function pairingProd4(
            G1Point memory a1, G2Point memory a2,
            G1Point memory b1, G2Point memory b2,
            G1Point memory c1, G2Point memory c2,
            G1Point memory d1, G2Point memory d2
    ) internal view returns (bool) {
        G1Point[] memory p1 = new G1Point[](4);
        G2Point[] memory p2 = new G2Point[](4);
        p1[0] = a1;
        p1[1] = b1;
        p1[2] = c1;
        p1[3] = d1;
        p2[0] = a2;
        p2[1] = b2;
        p2[2] = c2;
        p2[3] = d2;
        return pairing(p1, p2);
    }
}

contract Verifier {
    using Pairing for *;
    struct VerifyingKey {
        Pairing.G1Point alpha;
        Pairing.G2Point beta;
        Pairing.G2Point gamma;
        Pairing.G2Point delta;
        Pairing.G1Point[] gamma_abc;
    }
    struct Proof {
        Pairing.G1Point a;
        Pairing.G2Point b;
        Pairing.G1Point c;
    }
    function verifyingKey() pure internal returns (VerifyingKey memory vk) {
        vk.alpha = Pairing.G1Point(uint256(0x0712659e3078a9b02b6945f257f4b3436094e6aabd32ac74f6dac5e9886235d8), uint256(0x0f2361576595c78dfa3ce4df696b00b395a8124b3227ceab239fcea307321b96));
        vk.beta = Pairing.G2Point([uint256(0x07615c0e8577ad94b82cf624e9d747e11dcc055024e687736eb8caf4a4c00381), uint256(0x274f292459a3b1f6f762e1c9421f5b71d249a44f975ad21d3954e758124ae96e)], [uint256(0x08300a74f74ce1dbf25625841421811dd75a3bd1beb741d05ab211efdfe37a8b), uint256(0x0e3bd64ebd25b00a34d5d3b2eaccf6318bbdbe02eb0c741f5926a442c9871188)]);
        vk.gamma = Pairing.G2Point([uint256(0x102e26b0d278a7f6a839aa2be74568e86575c495d9aacbf9bc4a12a9974cf03d), uint256(0x20570d336e4b4abbfe37852295feac29ad6be8b82495551bf192323022dd1fc6)], [uint256(0x1143060b6b34a475e6910f2db008ca4a81c2fc1e5e0b086e7d0d4ade931d0387), uint256(0x0553ae2351da474c594d3a5e491cf2d79d1e96bdc7328624dffec722c0b56c41)]);
        vk.delta = Pairing.G2Point([uint256(0x1ac6927f5efd4d3e96dabe121173ec736c2d8f5eb5297138a2dd21875255d07d), uint256(0x068545292f97371c5d1ff5bb484e2edd3e736c2c70d0aee500ea5027fb9343d7)], [uint256(0x0feba4ab2fb543ebe7fb7955c2015b32e659b79cf0aeeca1aa257542f23af2f5), uint256(0x0dc6ec04566de1c4413f17f500dd2e8eaa17a131743b8ac9d5ea93b2219f8130)]);
        vk.gamma_abc = new Pairing.G1Point[](6);
        vk.gamma_abc[0] = Pairing.G1Point(uint256(0x2859589f2fbb374df9e3ea8711d00697d604a6a88097e6c4db3c90d98d22d3ea), uint256(0x1f89080d51a2f57f943b00a99582296cd39cf02c3fd5114183bc20b9e98a682c));
        vk.gamma_abc[1] = Pairing.G1Point(uint256(0x2fa5152871f7a292355d393588e7cabc1bf8e4e01f1141e9baf033d06896d435), uint256(0x1cf68d7e0900139898e616a3f30c2a411bee514bb695dbef19c5185ff8e23291));
        vk.gamma_abc[2] = Pairing.G1Point(uint256(0x078a7e39cdbb6475e7fe10f78aea80d84c351869d1b9ce1025e4341db7a8db1a), uint256(0x1d00f532dd6d3b0be33e9d9a316f88d6845754f6a19a9193946f45196a33f16b));
        vk.gamma_abc[3] = Pairing.G1Point(uint256(0x27217af6ca5f095154c7a716af748c012a9088b27b801ced0cbd4434a90c6557), uint256(0x0fc2aa161f000d4ae4fbb93f3a62916d9e5f3855f89110ac61a59143cb3aca4b));
        vk.gamma_abc[4] = Pairing.G1Point(uint256(0x1d8ac34e5e0aef71d090be3aed6870d95f9cfa2898a4e95e422fa8522f240aa4), uint256(0x0b6c5ff55b6b4e4886e77e89b4a9473e2ef233006655c4c8e03942d9ada78bcc));
        vk.gamma_abc[5] = Pairing.G1Point(uint256(0x2f7b3abab470039d8d3c2715e937dcb7187da4c8e531508907465dc1efeb67a5), uint256(0x0aa2c56a7378322c1ebf28043fe7f3e94867caf3093e9af431c770b6b905e4df));
    }
    function verify(uint[] memory input, Proof memory proof) internal view returns (uint) {
        uint256 snark_scalar_field = 21888242871839275222246405745257275088548364400416034343698204186575808495617;
        VerifyingKey memory vk = verifyingKey();
        require(input.length + 1 == vk.gamma_abc.length);
        // Compute the linear combination vk_x
        Pairing.G1Point memory vk_x = Pairing.G1Point(0, 0);
        for (uint i = 0; i < input.length; i++) {
            require(input[i] < snark_scalar_field);
            vk_x = Pairing.addition(vk_x, Pairing.scalar_mul(vk.gamma_abc[i + 1], input[i]));
        }
        vk_x = Pairing.addition(vk_x, vk.gamma_abc[0]);
        if(!Pairing.pairingProd4(
             proof.a, proof.b,
             Pairing.negate(vk_x), vk.gamma,
             Pairing.negate(proof.c), vk.delta,
             Pairing.negate(vk.alpha), vk.beta)) return 1;
        return 0;
    }
    function verifyTx(
            Proof memory proof, uint[5] memory input
        ) public view returns (bool r) {
        uint[] memory inputValues = new uint[](5);
        
        for(uint i = 0; i < input.length; i++){
            inputValues[i] = input[i];
        }
        if (verify(inputValues, proof) == 0) {
            return true;
        } else {
            return false;
        }
    }
}

// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

interface IPaymentTokenRegistry {
    function enabled(address) external view returns (bool);
}

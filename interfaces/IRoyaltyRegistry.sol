// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

/**
* @title Royalty registry
* @notice Module which provides royalty functionality.
*/
interface IRoyaltyRegistry {
    struct RoyaltyInfo {
        address receiver;
        uint96 royaltyFraction;
    }
}

// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../ERC1155Marketplace.sol";

contract MarketplaceBaseMock is MarketplaceBase {
    constructor(address addressRegistry) MarketplaceBase(addressRegistry) {}
}
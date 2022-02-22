// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../ERC1155Marketplace.sol";

contract ERC1155MarketplaceMock is ERC1155Marketplace {
    constructor(address addressRegistry) ERC1155Marketplace(addressRegistry) {}
}
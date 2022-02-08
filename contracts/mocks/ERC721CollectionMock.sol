// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../ERC721Collection.sol";

contract ERC721CollectionMock is ERC721Collection {
    constructor(
        string memory name,
        string memory symbol,
        uint256 mintFee,
        address payable mintFeeRecipient,
        bool privateFlag
    ) ERC721Collection(name, symbol, mintFee, mintFeeRecipient, privateFlag) {}
}
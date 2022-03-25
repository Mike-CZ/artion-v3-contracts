// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../ERC1155Marketplace.sol";

contract ERC1155MarketplaceMock is ERC1155Marketplace {
    constructor(
        address addressRegistry,
        address payable feeRecipient
    ) ERC1155Marketplace(addressRegistry, feeRecipient) {}

    function createAuctionAndTransferToken(
        NFTAddress nft,
        uint256 tokenId,
        uint256 amount,
        uint256 auctionId,
        address owner,
        address paymentToken,
        uint256 reservePrice,
        uint256 startTime,
        uint256 endTime,
        bool isMinBidReservePrice
    ) public {
        _createAuctionAndTransferToken(
            nft, tokenId, amount, auctionId, owner, paymentToken, reservePrice, startTime, endTime, isMinBidReservePrice
        );
    }
}

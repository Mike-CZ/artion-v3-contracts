// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../ERC1155Marketplace.sol";

contract ERC1155MarketplaceMock is ERC1155Marketplace {
    constructor(
        address addressRegistry,
        address payable feeRecipient,
        bool escrowOfferPaymentTokens
    ) ERC1155Marketplace(addressRegistry, feeRecipient, escrowOfferPaymentTokens) {}

    function createAuctionAndTransferToken(
        NFTAddress nft,
        uint256 tokenId,
        uint256 amount,
        address owner,
        address paymentToken,
        uint256 reservePrice,
        uint256 startTime,
        uint256 endTime,
        bool isMinBidReservePrice
    ) public {
        _createAuctionAndTransferToken(
            nft, tokenId, amount, owner, paymentToken, reservePrice, startTime, endTime, isMinBidReservePrice
        );
    }
}

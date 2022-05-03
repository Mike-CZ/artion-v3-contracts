// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../ERC1155Marketplace.sol";

contract ERC1155MarketplaceMock is ERC1155Marketplace {
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

    function createListingAndTransferToken(
        NFTAddress nft,
        uint256 tokenId,
        address owner,
        address paymentToken,
        uint256 tokenAmount,
        uint256 buyTokenAmount,
        uint256 buyAmountPrice,
        uint256 listingId,
        uint256 startingTime
    ) public {
        _createListingAndTransferToken(
            nft, tokenId, owner, paymentToken, tokenAmount, buyTokenAmount, buyAmountPrice, listingId, startingTime
        );
    }
}

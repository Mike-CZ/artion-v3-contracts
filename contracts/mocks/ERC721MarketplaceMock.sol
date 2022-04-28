// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../ERC721Marketplace.sol";

contract ERC721MarketplaceMock is ERC721Marketplace {
    constructor(
        address addressRegistry,
        uint256 auctionFee,
        uint256 listingFee,
        uint256 offerFee,
        address payable feeRecipient,
        bool escrowOfferPaymentTokens
    ) ERC721Marketplace(addressRegistry, auctionFee, listingFee, offerFee, feeRecipient, escrowOfferPaymentTokens) {}

    function createAuctionAndTransferToken(
        NFTAddress nft,
        uint256 tokenId,
        address owner,
        address paymentToken,
        uint256 reservePrice,
        uint256 startTime,
        uint256 endTime,
        bool isMinBidReservePrice
    ) public {
        _createAuctionAndTransferToken(
            nft, tokenId, owner, paymentToken, reservePrice, startTime, endTime, isMinBidReservePrice
        );
    }

    /*
    function createListingAndTransferToken(
        NFTAddress nft,
        uint256 tokenId,
        address owner,
        address paymentToken,
        uint256 buyTokenAmount,
        uint256 buyAmountPrice,
        uint256 listingId,
        uint256 startingTime
    ) public {
        _createListingAndTransferToken(
            nft, tokenId, owner, paymentToken, buyTokenAmount, buyAmountPrice, listingId, startingTime
        );
    }*/
}

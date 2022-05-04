// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../ERC721Marketplace.sol";

contract ERC721MarketplaceMock is ERC721Marketplace {
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
}

// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "../contracts/library/NFTTradable.sol";

/**
* @title Marketplace base interface
*/
interface IMarketplaceBase {
    struct Auction {
        address owner;
        address paymentToken;
        uint256 reservePrice;
        bool isMinBidReservePrice;
        uint256 startTime;
        uint256 endTime;
    }

    struct HighestBid {
        address bidder;
        uint256 bidAmount;
        uint256 time;
    }

    /// @notice Structure for listed items
    struct Listing {
        address payable owner;
        address paymentToken;
        uint256 price;
        uint256 startingTime;
    }

    event AuctionCreated(
        address indexed nftAddress,
        uint256 indexed tokenId,
        address indexed owner,
        uint256 tokenAmount,
        address payToken
    );

    event AuctionCancelled(address indexed nftAddress, address indexed nftOwner, uint256 indexed tokenId);

    event AuctionFinished(
        address oldOwner,
        address indexed nftAddress,
        uint256 indexed tokenId,
        address indexed winner,
        address payToken,
        uint256 tokenAmount,
        uint256 winningBid
    );

    event AuctionReservePriceUpdated(
        address indexed nftAddress,
        uint256 indexed tokenId,
        address indexed owner,
        uint256 reservePrice
    );

    event BidRefunded(
        address indexed nftAddress,
        address nftOwner,
        uint256 indexed tokenId,
        address indexed bidder,
        uint256 bid
    );

    event BidPlaced(
        address indexed nftAddress,
        address nftOwner,
        uint256 indexed tokenId,
        address indexed bidder,
        uint256 bid
    );

    event BidWithdrawn(
        address indexed nftAddress,
        address nftOwner,
        uint256 indexed tokenId,
        address indexed bidder,
        uint256 bid
    );

    // @notice Events for listing
    event ListingCreated(
        address indexed owner,
        address indexed nft,
        uint256 indexed tokenId,
        address paymentToken,
        uint256 price,
        uint256 startingTime
    );

    event ListingUpdated(
        address indexed owner,
        address indexed nft,
        uint256 indexed tokenId,
        address newPaymentToken,
        uint256 newPrice
    );

    event ListingCanceled(
        address indexed owner,
        address indexed nft,
        uint256 indexed tokenId
    );

    event ListedItemSold(
        address indexed seller,
        address indexed buyer,
        address indexed nft,
        uint256 tokenId,
        uint256 price,
        address paymentToken
    );
}

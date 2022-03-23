// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "openzeppelin/contracts/token/ERC20/IERC20.sol";
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
        bool hasResulted;
    }

    struct HighestBid {
        address bidder;
        uint256 bidAmount;
        uint256 time;
    }

    /// @notice Structure for listed items
    struct Listing {
        address payable nftOwner;
        address paymentToken;
        uint256 price;
        uint256 startingTime;
    }

    /// @notice Structure for offer
    struct Offer {
        address paymentToken;
        address offeror;
        uint256 price;
        uint256 expirationTime;
        bool paymentTokensInEscrow;
    }

    event AuctionCancelled(address indexed nftAddress, address indexed nftOwner, uint256 indexed tokenId);

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
        address indexed nftOwner,
        address indexed nftAddress,
        uint256 indexed tokenId,
        address paymentToken,
        uint256 price,
        uint256 startingTime
    );

    event ListingUpdated(
        address indexed nftOwner,
        address indexed nftAddress,
        uint256 indexed tokenId,
        address newPaymentToken,
        uint256 newPrice
    );

    event ListingCanceled(
        address indexed nftOwner,
        address indexed nftAddress,
        uint256 indexed tokenId
    );

    event ListedItemSold(
        address indexed seller,
        address indexed buyer,
        address indexed nftAddress,
        uint256 tokenId,
        uint256 price,
        address paymentToken
    );

    // @notice Events for offers
    event OfferCreated(
        address indexed offeror,
        address indexed nftAddress,
        uint256 tokenId,
        address paymentToken,
        uint256 price,
        uint256 expirationTime
    );

    event OfferCanceled(
        address indexed offeror,
        address indexed nftAddress,
        uint256 tokenId
    );

    event OfferAccepted(
        address indexed nftAddress,
        uint256 tokenId,
        address indexed buyer,
        address seller,
        uint256 price,
        address paymentToken
    );
}

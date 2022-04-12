// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "./IMarketplaceBase.sol";

/**
* @title ERC1155 Marketplace interface
*/
interface IERC721Marketplace is IMarketplaceBase {
    // @notice Events for listing
    event ERC721ListingCreated(
        address indexed nftOwner,
        address indexed nftAddress,
        uint256 indexed tokenId,
        address paymentToken,
        uint256 price,
        uint256 startingTime
    );

    event ERC721ListingUpdated(
        address indexed nftOwner,
        address indexed nftAddress,
        uint256 indexed tokenId,
        address newPaymentToken,
        uint256 newPrice
    );

    event ERC721ListingCanceled(
        address indexed nftOwner,
        address indexed nftAddress,
        uint256 indexed tokenId
    );

    event ERC721ListedItemSold(
        address indexed seller,
        address indexed buyer,
        address indexed nftAddress,
        uint256 tokenId,
        uint256 price,
        address paymentToken
    );

    // @notice Events for offers
    event ERC721OfferCreated(
        address indexed offeror,
        address indexed nftAddress,
        uint256 tokenId,
        address paymentToken,
        uint256 price,
        uint256 expirationTime
    );

    event ERC721OfferCanceled(
        address indexed offeror,
        address indexed nftAddress,
        uint256 tokenId
    );

    event ERC721OfferAccepted(
        address indexed nftAddress,
        uint256 tokenId,
        address indexed buyer,
        address seller,
        uint256 price,
        address paymentToken
    );

    // @notice Events for auctions
    event ERC721AuctionCreated(
        address indexed nftAddress,
        uint256 indexed tokenId,
        address indexed owner,
        address payToken
    );

    event ERC721AuctionCancelled(
        address indexed nftAddress,
        address indexed nftOwner,
        uint256 indexed tokenId
    );

    event ERC721AuctionFinished(
        address oldOwner,
        address indexed nftAddress,
        uint256 indexed tokenId,
        address indexed winner,
        address payToken,
        uint256 winningBid
    );

    event ERC721AuctionReservePriceUpdated(
        address indexed nftAddress,
        uint256 indexed tokenId,
        address indexed owner,
        uint256 reservePrice
    );

    event ERC721BidRefunded(
        address indexed nftAddress,
        address nftOwner,
        uint256 indexed tokenId,
        address indexed bidder,
        uint256 bid
    );

    event ERC721BidPlaced(
        address indexed nftAddress,
        address nftOwner,
        uint256 indexed tokenId,
        address indexed bidder,
        uint256 bid
    );

    event ERC721BidWithdrawn(
        address indexed nftAddress,
        address nftOwner,
        uint256 indexed tokenId,
        address indexed bidder,
        uint256 bid
    );
}

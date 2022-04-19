// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "./IMarketplaceBase.sol";

/**
* @title ERC1155 Marketplace interface
*/
interface IERC1155Marketplace is IMarketplaceBase {
    event ERC1155AuctionCreated(
        address indexed nftAddress,
        uint256 indexed tokenId,
        uint256 auctionId,
        address indexed owner,
        uint256 tokenAmount,
        address payToken
    );

    event ERC1155AuctionCancelled(
        address indexed nftAddress,
        address indexed nftOwner,
        uint256 indexed tokenId,
        uint256 auctionId
    );

    event ERC1155AuctionFinished(
        address oldOwner,
        address indexed nftAddress,
        uint256 indexed tokenId,
        uint256 auctionId,
        address indexed winner,
        address payToken,
        uint256 tokenAmount,
        uint256 winningBid
    );

    event ERC1155AuctionReservePriceUpdated(
        address indexed nftAddress,
        uint256 indexed tokenId,
        uint256 auctionId,
        address indexed owner,
        uint256 reservePrice
    );

    event ERC1155BidRefunded(
        address indexed nftAddress,
        address nftOwner,
        uint256 indexed tokenId,
        uint256 auctionId,
        address indexed bidder,
        uint256 bid
    );

    event ERC1155BidPlaced(
        address indexed nftAddress,
        address nftOwner,
        uint256 indexed tokenId,
        uint256 auctionId,
        address indexed bidder,
        uint256 bid
    );

    event ERC1155BidWithdrawn(
        address indexed nftAddress,
        address nftOwner,
        uint256 indexed tokenId,
        uint256 auctionId,
        address indexed bidder,
        uint256 bid
    );

    event ERC1155ListingCreated(
        address indexed owner,
        address indexed nft,
        uint256 indexed tokenId,
        uint256 tokenAmount,
        uint256 unitSize,
        uint256 unitPrice,
        uint256 listingId,
        address paymentToken,
        uint256 startingTime
    );

    event ERC1155ListingUpdated(
        address indexed owner,
        address indexed nft,
        uint256 indexed tokenId,
        uint256 listingId,
        address newPaymentToken,
        uint256 newPrice
    );

    event ERC1155ListingCanceled(
        address indexed owner,
        address indexed nft,
        uint256 indexed tokenId,
        uint256 listingId
    );

    event ERC1155ListedItemSold(
        address indexed seller,
        address indexed buyer,
        address indexed nft,
        uint256 tokenId,
        uint256 amount,
        uint256 remainingAmount,
        uint256 price,
        address paymentToken
    );

    event ERC1155OfferCreated(
        address indexed offeror,
        address indexed nftAddress,
        uint256 indexed tokenId,
        uint256 tokenAmount,
        address paymentToken,
        uint256 price,
        uint256 expirationTime,
        bool isPayTokenInEscrow
    );

    event ERC1155OfferCanceled(
        address indexed offeror,
        address indexed nftAddress,
        uint256 indexed tokenId,
        uint256 tokenAmount
    );

    event ERC1155OfferAccepted(
        address indexed nftAddress,
        uint256 indexed tokenId,
        uint256 tokenAmount,
        address indexed buyer,
        address seller,
        uint256 price,
        address paymentToken
    );
}

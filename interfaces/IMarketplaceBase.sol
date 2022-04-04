// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "../contracts/library/NFTTradable.sol";

/**
* @title Marketplace base interface
*/
interface IMarketplaceBase {
    event AuctionCreated(
        address indexed nftAddress,
        uint256 indexed tokenId,
        address indexed owner,
        uint256 tokenAmount,
        address payToken
    );

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
}

// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "./IMarketplaceBase.sol";

/**
* @title ERC1155 Marketplace interface
*/
interface IERC1155Marketplace is IMarketplaceBase {
    struct ERC1155Auction {
        Auction auction;
        uint256 tokenAmount;
    }

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
}

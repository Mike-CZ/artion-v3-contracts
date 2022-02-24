// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "openzeppelin/contracts/utils/math/SafeMath.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "openzeppelin/contracts/token/ERC1155/utils/ERC1155Holder.sol";
import "./library/NFTTradable.sol";
import "./MarketplaceBase.sol";
import "../interfaces/IERC1155Marketplace.sol";

contract ERC1155Marketplace is ERC1155Holder, MarketplaceBase, IERC1155Marketplace {
    using NFTTradable for NFTAddress;

    /**
    * @notice ERC1155 address => token id => owner => auction
    */
    mapping(address => mapping(uint256 => mapping(address => ERC1155Auction))) internal _auctions;

    constructor(address addressRegistry) MarketplaceBase(addressRegistry) {

    }

    /**
     * @notice Create new auction
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param amount Token amount
     * @param paymentToken Payment token that will be used for auction
     * @param reservePrice NFT address
     * @param startTime NFT address
     * @param endTime NFT address
     * @param isMinBidReservePrice NFT address
     */
    function createAuction(
        NFTAddress nft,
        uint256 tokenId,
        uint256 amount,
        address paymentToken,
        uint256 reservePrice,
        uint256 startTime,
        uint256 endTime,
        bool isMinBidReservePrice
    ) public {
        _validateNewAuctionNFT(nft, tokenId, amount);

        _validatePaymentTokenIsEnabled(paymentToken);

        _validateNewAuctionTime(startTime, endTime);

        _validateAuctionHasNotStarted(getAuction(nft, tokenId, _msgSender()).auction);

        _createAuctionAndTransferToken(
            nft, tokenId, amount, _msgSender(), paymentToken, reservePrice, startTime, endTime, isMinBidReservePrice
        );
    }

    /**
     * @notice Place bid
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param bidAmount Bid amount
     */
    function placeBid(NFTAddress nft, uint256 tokenId, address owner, uint256 bidAmount) public {

    }

    /**
     * @notice Get auction
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @return ERC1155Auction
     */
    function getAuction(NFTAddress nft, uint256 tokenId, address owner) public view returns (ERC1155Auction memory) {
        return _auctions[nft.toAddress()][tokenId][owner];
    }

    /**
     * @notice Create new auction and transfer token
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param amount Token amount
     * @param owner Token owner
     * @param paymentToken Payment token that will be used for auction
     * @param reservePrice NFT address
     * @param startTime NFT address
     * @param endTime NFT address
     * @param isMinBidReservePrice NFT address
     */
    function _createAuctionAndTransferToken(
        NFTAddress nft,
        uint256 tokenId,
        uint256 amount,
        address owner,
        address paymentToken,
        uint256 reservePrice,
        uint256 startTime,
        uint256 endTime,
        bool isMinBidReservePrice
    ) internal {
        _auctions[nft.toAddress()][tokenId][owner] = ERC1155Auction({
            auction: Auction({
                owner: owner,
                paymentToken: paymentToken,
                isMinBidReservePrice: isMinBidReservePrice,
                reservePrice: reservePrice,
                startTime: startTime,
                endTime: endTime,
                hasResulted: false
            }),
            tokenAmount: amount
        });

        // transfer token to be held in escrow
        nft.toERC1155().safeTransferFrom(owner, address(this), tokenId, amount, new bytes(0));
    }

    /**
     * @notice Validate new auction nft
     * @param nft NFT instance
     * @param tokenId Token identifier
     * @param amount Token amount
     */
    function _validateNewAuctionNFT(NFTAddress nft, uint256 tokenId, uint256 amount) internal {
        require(nft.isERC1155(), 'ERC1155Marketplace: NFT not ERC1155');
        require(
            nft.toERC1155().balanceOf(_msgSender(), tokenId) >= amount,
            'ERC1155Marketplace: balance too low'
        );
        require(
            nft.toERC1155().isApprovedForAll(_msgSender(), address(this)),
            'ERC1155Marketplace: not approved'
        );
    }
}
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

contract ERC1155Marketplace is Ownable, ERC1155Holder, MarketplaceBase, IERC1155Marketplace {
    using NFTTradable for NFTAddress;

    /**
    * @notice ERC1155 address => token id => owner => auction
    */
    mapping(address => mapping(uint256 => mapping(address => ERC1155Auction))) private _auctions;

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
    ) external {
        // validate given nft and its amount
        _validateNewAuctionNFT(nft, tokenId, amount);

        // validate payment token is supported
        _validatePaymentTokenIsSupported(paymentToken);

        // validate auction time
        _validateNewAuctionTime(startTime, endTime);

        // validate auction is not already running
        _validateAuctionHasNotStarted(_auctions[nft.toAddress()][tokenId][_msgSender()].auction);

        // create auction
        _auctions[nft.toAddress()][tokenId][_msgSender()] = ERC1155Auction({
            auction: Auction({
                owner: _msgSender(),
                paymentToken: paymentToken,
                isMinBidReservePrice: isMinBidReservePrice,
                reservePrice: reservePrice,
                startTime: startTime,
                endTime: endTime,
                hasResulted: false
            }),
            tokenAmount: amount
        });

        // hold in escrow
        nft.toERC1155().safeTransferFrom(_msgSender(), address(this), tokenId, amount, new bytes(0));
    }

    /**
     * @notice Validate new auction nft
     * @param nft NFT instance
     * @param tokenId Token identifier
     * @param amount Token amount
     */
    function _validateNewAuctionNFT(NFTAddress nft, uint256 tokenId, uint256 amount) private {
        require(nft.isERC1155(), 'ERC1155Marketplace: NFT address is not ERC1155');
        require(
            nft.toERC1155().balanceOf(_msgSender(), tokenId) >= amount,
            'ERC1155Marketplace: does not hold enough tokens'
        );
        require(
            nft.toERC1155().isApprovedForAll(_msgSender(), address(this)),
            'ERC1155Marketplace: not approved for tokens'
        );
    }

}
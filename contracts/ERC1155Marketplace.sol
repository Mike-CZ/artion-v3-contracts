// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "openzeppelin/contracts/utils/math/SafeMath.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "./library/NFTTradable.sol";
import "./MarketplaceBase.sol";

contract ERC1155Marketplace is Ownable, MarketplaceBase {
    using NFTTradable for NFTAddress;

    mapping(address => uint256) private _escrow;

    struct Auction {
        address owner;
        NFTAddress nft;
        uint256 minBid;
        uint256 reservePrice;
        uint256 startTime;
        uint256 endTime;
        bool resulted;
    }

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
        _validateNewAuctionNFT(nft, tokenId, amount);
        _validatePaymentTokenIsSupported(paymentToken);
        _validateNewAuctionTime(startTime, endTime);

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
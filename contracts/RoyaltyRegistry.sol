// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/IPaymentTokenRegistry.sol";
import "../interfaces/IRoyaltyRegistry.sol";
import "./library/NFTTradable.sol";

/**
* @dev see {IRoyaltyRegistry}
*/
contract RoyaltyRegistry is Ownable, IRoyaltyRegistry {
    using NFTTradable for NFTAddress;

    /**
    * @notice nft address => token id => royalty info
    */
    mapping(address => mapping(uint256 => RoyaltyInfo)) internal _tokenRoyaltyInfo;

    /**
    * @notice nft address => royalty info
    */
    mapping(address => RoyaltyInfo) internal _defaultRoyaltyInfo;

    /**
    * @notice royalty percent denominator
    */
    uint256 internal constant ROYALTY_PERCENT_DENOMINATOR = 10_000;

    /**
     * @notice Returns how much royalty is owed and to whom, based on a sale price that may be denominated in any unit
     * of exchange. The royalty amount is denominated and should be payed in that same unit of exchange.
     * @param nft NFT collection
     * @param tokenId Token identifier
     * @param salePrice Sale price
     * @return address, uint256
     */
    function royaltyInfo(NFTAddress nft, uint256 tokenId, uint256 salePrice) public view returns (address, uint256) {
        if (nft.isERC2981()) {
            return nft.toERC2981().royaltyInfo(tokenId, salePrice);
        }

        RoyaltyInfo memory royalty = _getTokenRoyaltyInfo(nft, tokenId);
        if (! _royaltyInfoExists(royalty)) {
            royalty = _getDefaultRoyaltyInfo(nft);
        }

        return (royalty.receiver, _calculateRoyalty(salePrice, royalty.royaltyFraction));
    }

    /**
    * @notice Get token royalty info
    * @return RoyaltyInfo
    */
    function _getTokenRoyaltyInfo(NFTAddress nft, uint256 tokenId) internal view returns (RoyaltyInfo memory) {
        return _tokenRoyaltyInfo[nft.toAddress()][tokenId];
    }

    /**
    * @notice Get royalty info
    * @return RoyaltyInfo
    */
    function _getDefaultRoyaltyInfo(NFTAddress nft) internal view returns (RoyaltyInfo memory) {
        return _defaultRoyaltyInfo[nft.toAddress()];
    }

    /**
    * @notice Get royalty info
    * @param royalty Royalty info
    * @return bool
    */
    function _royaltyInfoExists(RoyaltyInfo memory royalty) internal pure returns (bool) {
        return royalty.receiver != address(0);
    }

    /**
    * @notice Calculate royalty
    * @param salePrice Sale price
    * @param royaltyFraction Royalty fraction
    * @return uint256
    */
    function _calculateRoyalty(uint256 salePrice, uint96 royaltyFraction) internal pure returns (uint256) {
        return (salePrice * royaltyFraction) / ROYALTY_PERCENT_DENOMINATOR;
    }
}
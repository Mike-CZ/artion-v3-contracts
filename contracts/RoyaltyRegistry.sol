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

    struct RoyaltyInfo {
        address receiver;
        uint96 royaltyFraction;
    }

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
     * @dev see {IRoyaltyRegistry-royaltyInfo}
     */
    function royaltyInfo(NFTAddress nft, uint256 tokenId, uint256 salePrice) public view returns (address, uint256) {
        if (nft.isERC2981()) {
            return nft.toERC2981().royaltyInfo(tokenId, salePrice);
        }

        RoyaltyInfo memory royalty = _getTokenRoyaltyInfo(nft, tokenId);
        if (! _royaltyInfoExists(royalty)) {
            royalty = _getDefaultRoyaltyInfo(nft);
        }

        return (royalty.receiver, (salePrice * royalty.royaltyFraction) / ROYALTY_PERCENT_DENOMINATOR);
    }

    /**
     * @dev see {IRoyaltyRegistry-setDefaultRoyalty}
     */
    function setDefaultRoyalty(NFTAddress nft, address recipient, uint96 royaltyFraction) onlyOwner public {
        require(! nft.isERC2981Settable(), 'RoyaltyRegistry: supports royalty setter');

        require(! _royaltyInfoExists(_getDefaultRoyaltyInfo(nft)), 'RoyaltyRegistry: royalty set');
        require(royaltyFraction <= ROYALTY_PERCENT_DENOMINATOR, 'RoyaltyRegistry: royalty too high');

        _defaultRoyaltyInfo[nft.toAddress()] = RoyaltyInfo(recipient, royaltyFraction);
    }

    /**
     * @dev see {IRoyaltyRegistry-setTokenRoyalty}
     */
    function setTokenRoyalty(NFTAddress nft, uint256 tokenId, address recipient, uint96 royaltyFraction) public {
        require(! nft.isERC2981Settable(), 'RoyaltyRegistry: supports royalty setter');

        _validateTokenOwner(nft, tokenId);

        require(! _royaltyInfoExists(_getTokenRoyaltyInfo(nft, tokenId)), 'RoyaltyRegistry: royalty set');
        require(royaltyFraction <= ROYALTY_PERCENT_DENOMINATOR, 'RoyaltyRegistry: royalty too high');

        _tokenRoyaltyInfo[nft.toAddress()][tokenId] = RoyaltyInfo(recipient, royaltyFraction);
    }

    /**
     * @dev see {IRoyaltyRegistry-updateDefaultRoyaltyRecipient}
     */
    function updateDefaultRoyaltyRecipient(NFTAddress nft, address recipient) public {
        _validateCurrentRoyaltyRecipient(_getDefaultRoyaltyInfo(nft), _msgSender());
        _defaultRoyaltyInfo[nft.toAddress()].receiver = recipient;
    }

    /**
     * @dev see {IRoyaltyRegistry-updateTokenRoyaltyRecipient}
     */
    function updateTokenRoyaltyRecipient(NFTAddress nft, uint256 tokenId, address recipient) public {
        _validateCurrentRoyaltyRecipient(_getTokenRoyaltyInfo(nft, tokenId), _msgSender());
        _tokenRoyaltyInfo[nft.toAddress()][tokenId].receiver = recipient;
    }

    /**
    * @notice Validate token owner
    * @param nft NFT address to validate
    * @param tokenId Token identifier to validate
    */
    function _validateTokenOwner(NFTAddress nft, uint256 tokenId) internal {
        if (nft.isERC721()) {
            require(nft.toERC721().ownerOf(tokenId) == _msgSender(), 'RoyaltyRegistry: not owner');
            return;
        }

        if (nft.isERC1155()) {
            require(nft.toERC1155().balanceOf(_msgSender(), tokenId) > 0, 'RoyaltyRegistry: not owner');
            return;
        }

        revert('RoyaltyRegistry: invalid nft');
    }

    /**
    * @notice Validate current royalty recipient
    * @param royalty Royalty info to validate
    * @param recipient Royalty recipient to validate
    */
    function _validateCurrentRoyaltyRecipient(RoyaltyInfo memory royalty, address recipient) internal pure {
        require(royalty.receiver == recipient, 'RoyaltyRegistry: not current recipient');
    }

    /**
    * @notice Get token royalty info
    * @param nft NFT address
    * @param tokenId Token identifier
    * @return RoyaltyInfo
    */
    function _getTokenRoyaltyInfo(NFTAddress nft, uint256 tokenId) internal view returns (RoyaltyInfo memory) {
        return _tokenRoyaltyInfo[nft.toAddress()][tokenId];
    }

    /**
    * @notice Get default royalty info
    * @param nft NFT address
    * @return RoyaltyInfo
    */
    function _getDefaultRoyaltyInfo(NFTAddress nft) internal view returns (RoyaltyInfo memory) {
        return _defaultRoyaltyInfo[nft.toAddress()];
    }

    /**
    * @notice Check royalty info exists
    * @param royalty Royalty info
    * @return bool
    */
    function _royaltyInfoExists(RoyaltyInfo memory royalty) internal pure returns (bool) {
        return royalty.receiver != address(0);
    }
}
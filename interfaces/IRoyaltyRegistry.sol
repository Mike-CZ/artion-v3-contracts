pragma solidity ^0.8.0;

import "../contracts/library/NFTTradable.sol";

/**
* @title Royalty registry
* @notice Module which provides royalty functionality.
*/
interface IRoyaltyRegistry {
    struct RoyaltyInfo {
        address receiver;
        uint96 royaltyFraction;
    }

    /**
     * @notice Returns how much royalty is owed and to whom, based on a sale price that may be denominated in any unit
     * of exchange. The royalty amount is denominated and should be payed in that same unit of exchange.
     * @param nft NFT collection
     * @param tokenId Token identifier
     * @param salePrice Sale price
     * @return address, uint256
     */
    function royaltyInfo(NFTAddress nft, uint256 tokenId, uint256 salePrice) external view returns (address, uint256);

    /**
     * @notice Sets the royalty information that all ids in this contract will default to.
     * @param nft NFT collection
     * @param recipient Royalty recipient
     * @param royaltyFraction Royalty fraction
     */
    function setDefaultRoyalty(NFTAddress nft, address recipient, uint96 royaltyFraction) external;

    /**
     * @notice Sets the royalty information for a specific token id, overriding the global default.
     * @param nft NFT collection
     * @param tokenId Token identifier
     * @param recipient Royalty recipient
     * @param royaltyFraction Royalty fraction
     */
    function setTokenRoyalty(NFTAddress nft, uint256 tokenId, address recipient, uint96 royaltyFraction) external;

    /**
    * @notice Update default royalty recipient
    * @param nft NFT address
    * @param recipient The receiver of royalty
    */
    function updateDefaultRoyaltyRecipient(NFTAddress nft, address recipient) external;

    /**
    * @notice Update royalty recipient for a token
    * @param nft NFT address
    * @param tokenId The token identifier
    * @param recipient The receiver of royalty
    */
    function updateTokenRoyaltyRecipient(NFTAddress nft, uint256 tokenId, address recipient) external;
}

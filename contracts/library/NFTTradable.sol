// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/token/ERC721/IERC721.sol";
import "openzeppelin/contracts/token/ERC1155/IERC1155.sol";
import "openzeppelin/contracts/utils/introspection/IERC165.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";

// @notice User defined type to unify ERC721 and ERC1155
type NFTAddress is address;

/**
* @title NFT Tradable library
* @notice Set of functions to work with NFTAddress type.
*/
library NFTTradable {
    /**
     * @notice Check NFT address is ERC721
     * @param nft NFT address
     * @return bool
     */
    function isERC721(NFTAddress nft) internal view returns (bool) {
        return IERC165(toAddress(nft)).supportsInterface(type(IERC721).interfaceId);
    }

    /**
     * @notice Check NFT address is ERC1155
     * @param nft NFT address
     * @return bool
     */
    function isERC1155(NFTAddress nft) internal view returns (bool) {
        return IERC165(toAddress(nft)).supportsInterface(type(IERC1155).interfaceId);
    }

    /**
     * @notice Check NFT address is ERC2981
     * @param nft NFT address
     * @return bool
     */
    function isERC2981(NFTAddress nft) internal view returns (bool) {
        return IERC165(toAddress(nft)).supportsInterface(type(IERC2981).interfaceId);
    }

    /**
     * @notice Convert NFT address into ERC721 instance
     * @param nft NFT address
     * @return IERC721
     */
    function toERC721(NFTAddress nft) internal pure returns (IERC721) {
        return IERC721(toAddress(nft));
    }

    /**
     * @notice Convert NFT address into ERC1155 instance
     * @param nft NFT address
     * @return IERC1155
     */
    function toERC1155(NFTAddress nft) internal pure returns (IERC1155) {
        return IERC1155(toAddress(nft));
    }

    /**
     * @notice Convert NFT address into ERC2981 instance
     * @param nft NFT address
     * @return IERC2981
     */
    function toERC2981(NFTAddress nft) internal pure returns (IERC2981) {
        return IERC2981(toAddress(nft));
    }

    /**
     * @notice Convert NFT address into underlying address
     * @param nft NFT address
     * @return address
     */
    function toAddress(NFTAddress nft) internal pure returns (address) {
        return NFTAddress.unwrap(nft);
    }
}
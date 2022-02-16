// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/token/ERC721/IERC721.sol";
import "openzeppelin/contracts/token/ERC1155/IERC1155.sol";
import "openzeppelin/contracts/utils/introspection/IERC165.sol";

type NFTAddress is address;

library NFTTradable {


    function transfer(NFTAddress nft, address from, address to, uint256 tokenId) internal {
        transfer(nft, from, to, tokenId, 1);
    }

    function transfer(NFTAddress nft, address from, address to, uint256 tokenId, uint256 amount) internal {
        address nftAddress = NFTAddress.unwrap(nft);

        if (isERC721(nft)) {
            IERC721(nftAddress).safeTransferFrom(from, to, tokenId);
            return;
        }

        if (isERC1155(nft)) {
            IERC1155(nftAddress).safeTransferFrom(from, to, tokenId, amount, bytes(''));
            return;
        }

        revert('NFTTradable: invalid nft address');
    }

    function isERC721(NFTAddress nft) internal view returns (bool) {
        return IERC165(NFTAddress.unwrap(nft)).supportsInterface(type(IERC721).interfaceId);
    }

    function isERC1155(NFTAddress nft) internal view returns (bool) {
        return IERC165(NFTAddress.unwrap(nft)).supportsInterface(type(IERC1155).interfaceId);
    }
}
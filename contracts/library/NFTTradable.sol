// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/token/ERC721/IERC721.sol";
import "openzeppelin/contracts/token/ERC1155/IERC1155.sol";
import "openzeppelin/contracts/utils/introspection/IERC165.sol";

type NFTAddress is address;

library NFTTradable {


    function safeTransferFrom(NFTAddress nft, address from, address to, uint256 tokenId) internal {
        safeTransferFrom(nft, from, to, tokenId, 1);
    }

    function safeTransferFrom(NFTAddress nft, address from, address to, uint256 tokenId, uint256 amount) internal {
        address nftAddress = NFTAddress.unwrap(nft);

        if (IERC165(nftAddress).supportsInterface(type(IERC721).interfaceId)) {
            IERC721(nftAddress).safeTransferFrom(from, to, tokenId);
            return;
        }

        if (IERC165(nftAddress).supportsInterface(type(IERC1155).interfaceId)) {
            IERC1155(nftAddress).safeTransferFrom(from, to, tokenId, amount, bytes(''));
            return;
        }

        revert('NFTTradable: invalid nft address');
    }
}
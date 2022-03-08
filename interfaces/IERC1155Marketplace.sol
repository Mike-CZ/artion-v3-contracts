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
}

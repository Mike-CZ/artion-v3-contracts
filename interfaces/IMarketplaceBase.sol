// SPDX-License-Identifier: UNLICENSED

pragma solidity ^0.8.0;

import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "../contracts/library/NFTTradable.sol";

/**
* @title Marketplace base interface
*/
interface IMarketplaceBase {
    struct Auction {
        address owner;
        address paymentToken;
        uint256 reservePrice;
        bool isMinBidReservePrice;
        uint256 startTime;
        uint256 endTime;
        bool hasResulted;
    }

    /// @notice Structure for listed items
    struct Listing {
        address owner;
        address paymentToken;
        uint256 price;
        uint256 startingTime;
    }
}

// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../ERC1155Marketplace.sol";

contract MarketplaceBaseMock is MarketplaceBase {
    constructor(
        address addressRegistry,
        uint256 auctionFee,
        uint256 listingFee,
        uint256 offerFee,
        address payable feeRecipient,
        bool escrowOfferPaymentTokens
    ) MarketplaceBase(addressRegistry, auctionFee, listingFee, offerFee, feeRecipient, escrowOfferPaymentTokens) {}
}

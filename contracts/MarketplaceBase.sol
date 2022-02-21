// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "openzeppelin/contracts/utils/math/SafeMath.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "./library/NFTTradable.sol";
import "../interfaces/IAddressRegistry.sol";

abstract contract MarketplaceBase {
    IAddressRegistry internal addressRegistry;

    /// @notice maximum duration of an auction
    uint256 internal constant MAX_AUCTION_DURATION = 30 days;

    /// @notice minimum duration of an auction
    uint256 internal constant MIN_AUCTION_DURATION = 5 minutes;

    /**
     * @notice Validate payment token
     * @param paymentToken Payment token address
     */
    function _validatePaymentTokenIsSupported(address paymentToken) internal pure {
        // TODO: validate pay token via payment token registry
    }

    /**
     * @notice Validate new auction time
     * @param startTime Start time as unix time
     * @param endTime End time as unix time
     */
    function _validateNewAuctionTime(uint256 startTime, uint256 endTime) internal pure {
        require(
            endTime <= (startTime + MAX_AUCTION_DURATION),
            'MarketplaceBase: Auction time exceeds maximum duration'
        );
        require(
            endTime >= startTime + MIN_AUCTION_DURATION,
            "MarketplaceBase: Auction time does not meet minimum duration"
        );
    }
}
// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "openzeppelin/contracts/utils/math/SafeMath.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "./library/NFTTradable.sol";
import "../interfaces/IAddressRegistry.sol";
import "../interfaces/IMarketplaceBase.sol";
import "../interfaces/IPaymentTokenRegistry.sol";

abstract contract MarketplaceBase is Ownable, IMarketplaceBase {
    /**
    * @notice maximum duration of an auction
    */
    uint256 internal constant MAX_AUCTION_DURATION = 30 days;

    /**
    * @notice minimum duration of an auction
    */
    uint256 internal constant MIN_AUCTION_DURATION = 5 minutes;

    /**
    * @notice address registry containing addresses of other contracts
    */
    IAddressRegistry internal _addressRegistry;

    constructor(address addressRegistry) {
        _addressRegistry = IAddressRegistry(addressRegistry);
    }

    /**
     * @notice Update address registry address
     * @param addressRegistry address registry address
     */
    function updateAddressRegistryAddress(address addressRegistry) external onlyOwner {
        _addressRegistry = IAddressRegistry(addressRegistry);
    }

    /**
     * @notice Get address registry address
     * @return address
     */
    function getAddressRegistryAddress() external view returns (address) {
        return address(_addressRegistry);
    }

    /**
     * @notice Get auction maximum duration
     * @return int
     */
    function getMaximumAuctionDuration() external view returns (uint256) {
        return MAX_AUCTION_DURATION;
    }

    /**
     * @notice Get auction minimum duration
     * @return int
     */
    function getMinimumAuctionDuration() external view returns (uint256) {
        return MIN_AUCTION_DURATION;
    }

    /**
     * @notice Validate payment token is enabled
     * @param paymentToken Payment token address
     */
    function _validatePaymentTokenIsEnabled(address paymentToken) internal {
        require(
            _getPaymentTokenRegistry().isEnabled(paymentToken),
            'MarketplaceBase: payment token is not enabled'
        );
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
            endTime >= (startTime + MIN_AUCTION_DURATION),
            "MarketplaceBase: Auction time does not meet minimum duration"
        );
    }

    /**
     * @notice Validate auction has not started
     * @param auction Auction to validate
     */
    function _validateAuctionHasNotStarted(Auction memory auction) internal pure {
        require(auction.endTime == 0, 'MarketplaceBase: auction has already started');
    }

    /**
     * @notice Validate auction has not started
     * @param auction Auction to validate
     */
    function _validateAuctionExists(Auction memory auction) internal pure {
        require(auction.endTime > 0, 'MarketplaceBase: auction does not exist');
    }

    /**
     * @notice Validate auction has not started
     * @param auction Auction to validate
     */
    function _validateAuctionExists(Auction memory auction) internal pure {
        require(auction.endTime > 0, 'MarketplaceBase: auction does not exist');
    }

    /**
     * @notice Get payment token registry contract
     * @return IPaymentTokenRegistry
     */
    function _getPaymentTokenRegistry() internal returns (IPaymentTokenRegistry) {
        return IPaymentTokenRegistry(_addressRegistry.getPaymentTokenRegistryAddress());
    }

    /**
     * @notice Get current timestamp
     * @return uint256
     */
    function _getNow() internal view returns (uint256) {
        return block.timestamp;
    }
}
// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "openzeppelin/contracts/utils/math/SafeMath.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "openzeppelin/contracts/interfaces/IERC20.sol";
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
     * @notice Refund highest bid
     * @param nft NFT token related to bid
     * @param auction Auction related to bid
     * @param highestBid Bid to refund
     */
    function _refundHighestBidIfExists(NFTAddress nft, Auction auction, HighestBid highestBid) internal {
        if (_highestBidExists(highestBid)) {
            _sendERC20Amount(auction.paymentToken, highestBid.bidder, highestBid.bidAmount);
            emit BidRefunded(nft.toAddress(), auction.owner, auction);
        }
    }

    /**
     * @notice Receive ERC20 amount
     * @param payToken Address of ERC20
     * @param from Sender address
     * @param amount Amount to transfer
     */
    function _receiveERC20Amount(address payToken, address from, uint256 amount) internal {
        _transferERC20Amount(payToken, from, address(this), amount);
    }

    /**
     * @notice Send ERC20 amount
     * @param payToken Address of ERC20
     * @param to Receiver address
     * @param amount Amount to transfer
     */
    function _sendERC20Amount(address payToken, address to, uint256 amount) internal {
        _transferERC20Amount(payToken, address(this), to, amount);
    }

    /**
     * @notice Transfer ERC20 amount
     * @param payToken Address of ERC20
     * @param from Sender address
     * @param to Receiver address
     * @param amount Amount to transfer
     */
    function _transferERC20Amount(address payToken, address from, address to, uint256 amount) internal {
        require(IERC20(payToken).transferFrom(from, to, amount), 'MarketplaceBase: low balance or not approved');
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
     * @notice Validate auction exists
     * @param auction Auction to validate
     */
    function _validateAuctionExists(Auction memory auction) internal pure {
        require(_auctionExists(auction), 'MarketplaceBase: auction not exist');
    }

    /**
     * @notice Validate auction does not exist
     * @param auction Auction to validate
     */
    function _validateAuctionNotExists(Auction memory auction) internal pure {
        require(! _auctionExists(auction), 'MarketplaceBase: auction exists');
    }

    /**
     * @notice Validate auction has started
     * @param auction Auction to validate
     */
    function _validateAuctionStarted(Auction memory auction) internal pure {
        require(_auctionStarted(auction), 'MarketplaceBase: auction not started');
    }

    /**
     * @notice Validate auction has not started
     * @param auction Auction to validate
     */
    function _validateAuctionNotStarted(Auction memory auction) internal pure {
        require(! _auctionStarted(auction), 'MarketplaceBase: auction started');
    }

    /**
     * @notice Validate auction has ended
     * @param auction Auction to validate
     */
    function _validateAuctionEnded(Auction memory auction) internal pure {
        require(_auctionEnded(auction), 'MarketplaceBase: auction not ended');
    }

    /**
     * @notice Validate auction has not ended
     * @param auction Auction to validate
     */
    function _validateAuctionNotEnded(Auction memory auction) internal pure {
        require(! _auctionEnded(auction), 'MarketplaceBase: ended');
    }

    /**
     * @notice Validate auction bid amount
     * @param auction Auction to validate
     * @param auction Highest bid to validate
     * @param bidAmount Bid amount to validate
     */
    function _validateAuctionBidAmount(Auction memory auction, HighestBid highestBid, uint256 bidAmount) internal pure {
        require(bidAmount > 0, 'MarketplaceBase: low bid amount');
        // if minimal bid is set to reserve price, bid can not be lower than reserve price
        if (auction.isMinBidReservePrice) {
            require(bidAmount >= auction.reservePrice, 'MarketplaceBase: bid lower than reserve price');
        }
        require(bidAmount > highestBid.bidAmount, 'MarketplaceBase: bid lower than highest bid');
    }

     /**
     * @notice Check auction exists
     * @param auction Auction to check
     * @return bool
     */
    function _auctionExists(Auction memory auction) internal pure returns (bool) {
        return auction.startTime > 0;
    }

    /**
     * @notice Check highest bid exists
     * @param highestBid Bid to check
     * @return bool
     */
    function _highestBidExists(HighestBid memory highestBid) internal pure returns (bool) {
        return highestBid.bidAmount > 0;
    }

    /**
     * @notice Check auction has started
     * @param auction Auction to check
     * @return bool
     */
    function _auctionStarted(Auction memory auction) internal pure returns (bool) {
        return auction.startTime <= _getNow();
    }

    /**
     * @notice Check auction has ended
     * @param auction Auction to check
     * @return bool
     */
    function _auctionEnded(Auction memory auction) internal pure returns (bool) {
        return auction.endTime <= _getNow();
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
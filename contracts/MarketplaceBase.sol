// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "openzeppelin/contracts/interfaces/IERC20.sol";
import "openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "./library/NFTTradable.sol";
import "../interfaces/IAddressRegistry.sol";
import "../interfaces/IMarketplaceBase.sol";
import "../interfaces/IPaymentTokenRegistry.sol";
import "../interfaces/IRoyaltyRegistry.sol";

abstract contract MarketplaceBase is Ownable, IMarketplaceBase {
    using SafeERC20 for IERC20;

    /**
    * @notice maximum duration of an auction
    */
    uint256 internal constant MAX_AUCTION_DURATION = 30 days;

    /**
    * @notice minimum duration of an auction
    */
    uint256 internal constant MIN_AUCTION_DURATION = 5 minutes;

    /**
    * @notice bid is withdrawable after specified amount of time
    */
    uint256 internal constant HIGHEST_BID_WITHDRAW_DELAY = 12 hours;

    /**
    * @notice amount by which a bid has to increase
    */
    uint256 internal _minBidIncrementAmount = 1;

    /*
    * @notice auction fee, assumed to be 1 decimal place i.e. 25 = 2,5%
    */
    uint256 internal _auctionFee = 25;

    /**
    * @notice recipient of fees
    */
    address internal _feeRecipient;

    /**
    * @notice address registry containing addresses of other contracts
    */
    IAddressRegistry internal _addressRegistry;

    constructor(address addressRegistry, address feeRecipient) {
        _addressRegistry = IAddressRegistry(addressRegistry);
        _feeRecipient = feeRecipient;
    }

    /**
     * @notice Get minimal increment bid amount
     * @return uint256
     */
    function getMinBidIncrementAmount() public view returns (uint256) {
        return _minBidIncrementAmount;
    }

    /**
     * @notice Update minimal increment bid amount
     * @param amount New amount
     */
    function updateMinBidIncrementAmount(uint256 amount) public onlyOwner {
        _minBidIncrementAmount = amount;
    }

    /**
    * @notice Get auction fee
    * @return uint256
    */
    function getAuctionFee() public view returns (uint256) {
        return _auctionFee;
    }

    /**
     * @notice Update auction fee
     * @param auctionFee Fee amount - assumed to be 1 decimal place i.e. 25 = 2,5%
     */
    function updateAuctionFee(uint256 auctionFee) public onlyOwner {
        _auctionFee = auctionFee;
    }

    /**
    * @notice Get fee recipient
    * @return address
    */
    function getFeeRecipient() public view returns (address) {
        return _feeRecipient;
    }

    /**
     * @notice Update fee recipient
     * @param feeRecipient Fee recipient
     */
    function updateFeeRecipient(address feeRecipient) public onlyOwner {
        _feeRecipient = feeRecipient;
    }

    /**
     * @notice Update address registry address
     * @param addressRegistry address registry address
     */
    function updateAddressRegistryAddress(address addressRegistry) public onlyOwner {
        _addressRegistry = IAddressRegistry(addressRegistry);
    }

    /**
     * @notice Get address registry address
     * @return address
     */
    function getAddressRegistryAddress() public view returns (address) {
        return address(_addressRegistry);
    }

    /**
     * @notice Get auction maximum duration
     * @return uint256
     */
    function getMaximumAuctionDuration() public pure returns (uint256) {
        return MAX_AUCTION_DURATION;
    }

    /**
     * @notice Get auction minimum duration
     * @return uint256
     */
    function getMinimumAuctionDuration() public pure returns (uint256) {
        return MIN_AUCTION_DURATION;
    }

    /**
     * @notice Get highest bid withdraw delay
     * @return uint256
     */
    function getHighestBidWithdrawDelay() public pure returns (uint256) {
        return HIGHEST_BID_WITHDRAW_DELAY;
    }

    /**
     * @notice Refund highest bid
     * @param auction Auction related to bid
     * @param highestBid Bid to refund
     */
    function _refundHighestBid(Auction memory auction, HighestBid memory highestBid) internal {
        _sendPayTokenAmount(auction.paymentToken, highestBid.bidder, highestBid.bidAmount);
    }

    /**
    * @notice Calculate and take auction fee
    * @param auction Auction to calculate fee from
    * @param highestBid Highest bid to calculate fee from
    * @return uint256 - taken fee
    */
    function _calculateAndTakeAuctionFee(
        Auction memory auction,
        HighestBid memory highestBid
    ) internal returns (uint256) {
        uint256 feeBase = highestBid.bidAmount - auction.reservePrice;
        if (feeBase > 0) {
            uint256 fee = feeBase * _auctionFee / 1_000;
            _sendPayTokenAmount(auction.paymentToken, _feeRecipient, fee);
            return fee;
        }
        return 0;
    }

    /**
     * @notice Receive pay token amount
     * @param payToken Address of ERC20
     * @param from Sender address
     * @param amount Amount to transfer
     */
    function _receivePayTokenAmount(address payToken, address from, uint256 amount) internal {
        IERC20(payToken).safeTransferFrom(from, address(this), amount);
    }

    /**
     * @notice Send ERC20 amount
     * @param payToken Address of ERC20
     * @param to Receiver address
     * @param amount Amount to transfer
     */
    function _sendPayTokenAmount(address payToken, address to, uint256 amount) internal {
        IERC20(payToken).safeTransfer(to, amount);
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
     * @notice Validate auction has not resulted
     * @param auction Auction to validate
     */
    function _validateAuctionNotResulted(Auction memory auction) internal pure {
        require(! _auctionResulted(auction), 'MarketplaceBase: auction resulted');
    }

    /**
     * @notice Validate address is auction owner
     * @param auction Auction to validate
     * @param entrant Address to validate
     */
    function _validateAuctionOwner(Auction memory auction, address entrant) internal pure {
        require(auction.owner == entrant, 'MarketplaceBase: not owner');
    }

    /**
     * @notice Validate highest bid owner
     * @param highestBid Highest bid to validate
     */
    function _validateAuctionHighestBidOwner(HighestBid memory highestBid, address bidder) internal pure {
        require(highestBid.bidder == bidder, 'MarketplaceBase: not highest bidder');
    }

    /**
     * @notice Validate address is auction or highest bid owner
     * @param auction Auction to validate
     * @param highestBid Highest bid to validate
     * @param entrant Address to validate
     */
    function _validateAuctionOrHighestBidOwner(
        Auction memory auction,
        HighestBid memory highestBid,
        address entrant
    ) internal pure {
        require(
            auction.owner == entrant || highestBid.bidder == entrant,
            'MarketplaceBase: not auction or highest bid owner'
        );
    }

    /**
     * @notice Validate highest bid owner
     * @param auction Auction to validate
     * @param highestBid Highest bid to validate
     */
    function _validateAuctionHighestBidIsWithdrawable(
        Auction memory auction,
        HighestBid memory highestBid
    ) internal {
        // must wait when bid is above or equal reserve price
        if (_auctionHighestBidAboveOrEqualReservePrice(auction, highestBid)) {
            require(
                (HIGHEST_BID_WITHDRAW_DELAY + auction.endTime) <= _getNow(),
                'MarketplaceBase: must wait to withdraw'
            );
        }
    }

    /**
     * @notice Validate highest bid exists
     * @param highestBid Highest bid to validate
     */
    function _validateHighestBidExists(HighestBid memory highestBid) internal pure {
        require(_highestBidExists(highestBid), 'MarketplaceBase: highest bid not exist');
    }

    /**
     * @notice Validate auction highest bid is above or equal reserve price
     * @param auction Auction to validate
     * @param highestBid Highest bid to validate
     */
    function _validateAuctionHighestBidAboveOrEqualReservePrice(
        Auction memory auction,
        HighestBid memory highestBid
    ) internal pure {
        require(
            _auctionHighestBidAboveOrEqualReservePrice(auction, highestBid),
            'MarketplaceBase: highest bid below reserve price'
        );
    }

    /**
     * @notice Validate auction highest bid is not above reserve price
     * @param auction Auction to validate
     * @param highestBid Highest bid to validate
     */
    function _validateAuctionHighestBidBelowReservePrice(
        Auction memory auction,
        HighestBid memory highestBid
    ) internal pure {
        require(
            ! _auctionHighestBidAboveOrEqualReservePrice(auction, highestBid),
            'MarketplaceBase: highest bid above reserve price'
        );
    }

    /**
     * @notice Validate auction has resulted
     * @param auction Auction to validate
     */
    function _validateAuctionResulted(Auction memory auction) internal pure {
        require(_auctionResulted(auction), 'MarketplaceBase: auction not resulted');
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
    function _validateAuctionStarted(Auction memory auction) internal view {
        require(_auctionStarted(auction), 'MarketplaceBase: auction not started');
    }

    /**
     * @notice Validate auction has not started
     * @param auction Auction to validate
     */
    function _validateAuctionNotStarted(Auction memory auction) internal view {
        require(! _auctionStarted(auction), 'MarketplaceBase: auction started');
    }

    /**
     * @notice Validate auction has ended
     * @param auction Auction to validate
     */
    function _validateAuctionEnded(Auction memory auction) internal view {
        require(_auctionEnded(auction), 'MarketplaceBase: auction not ended');
    }

    /**
     * @notice Validate auction has not ended
     * @param auction Auction to validate
     */
    function _validateAuctionNotEnded(Auction memory auction) internal view {
        require(! _auctionEnded(auction), 'MarketplaceBase: auction ended');
    }

    /**
     * @notice Validate auction bid amount
     * @param auction Auction to validate
     * @param auction Highest bid to validate
     * @param bidAmount Bid amount to validate
     */
    function _validateAuctionBidAmount(
        Auction memory auction,
        HighestBid memory highestBid,
        uint256 bidAmount
    ) internal {
        // bid amount must be increased at least by minimal bid increment amount
        uint256 minBidAmount = highestBid.bidAmount + _minBidIncrementAmount;
        require(bidAmount >= minBidAmount, 'MarketplaceBase: low bid amount');

        // if minimal bid is set to reserve price, bid can not be lower than reserve price
        if (auction.isMinBidReservePrice) {
            require(bidAmount >= auction.reservePrice, 'MarketplaceBase: bid lower than reserve price');
        }
    }

    /**
     * @notice Validate auction bidder is not owner
     * @param auction Auction to validate
     * @param bidder Bidder to validate
     */
    function _validateAuctionBidderNotOwner(Auction memory auction, address bidder) internal pure {
        require(auction.owner != bidder, 'MarketplaceBase: bidder auction owner');
    }

    /**
     * @notice Check auction highest bid is above or equal reserve price
     * @param auction Auction to check
     * @param highestBid Highest bid to check
     */
    function _auctionHighestBidAboveOrEqualReservePrice(
        Auction memory auction,
        HighestBid memory highestBid
    ) internal pure returns (bool) {
        return highestBid.bidAmount >= auction.reservePrice;
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
    function _auctionStarted(Auction memory auction) internal view returns (bool) {
        return auction.startTime <= _getNow();
    }

    /**
     * @notice Check auction has ended
     * @param auction Auction to check
     * @return bool
     */
    function _auctionEnded(Auction memory auction) internal view returns (bool) {
        return auction.endTime <= _getNow();
    }

    /**
     * @notice Check auction has resulted
     * @param auction Auction to check
     * @return bool
     */
    function _auctionResulted(Auction memory auction) internal pure returns (bool) {
        return auction.hasResulted;
    }

    /**
     * @notice Get payment token registry contract
     * @return IPaymentTokenRegistry
     */
    function _getPaymentTokenRegistry() internal returns (IPaymentTokenRegistry) {
        return IPaymentTokenRegistry(_addressRegistry.getPaymentTokenRegistryAddress());
    }

    /**
     * @notice Get royalty registry contract
     * @return IRoyaltyRegistry
     */
    function _getRoyaltyRegistry() internal returns (IRoyaltyRegistry) {
        return IRoyaltyRegistry(_addressRegistry.getRoyaltyRegistryAddress());
    }

    /**
     * @notice Get current timestamp
     * @return uint256
     */
    function _getNow() internal view returns (uint256) {
        return block.timestamp;
    }
}
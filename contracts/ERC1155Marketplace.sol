// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "openzeppelin/contracts/utils/math/SafeMath.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";
import "openzeppelin/contracts/token/ERC1155/utils/ERC1155Holder.sol";
import "./library/NFTTradable.sol";
import "./MarketplaceBase.sol";
import "../interfaces/IERC1155Marketplace.sol";

contract ERC1155Marketplace is ERC1155Holder, MarketplaceBase, IERC1155Marketplace {
    using NFTTradable for NFTAddress;

    event AuctionCreated(
        address indexed nftAddress,
        uint256 indexed tokenId,
        uint256 auctionId,
        address indexed owner,
        uint256 tokenAmount,
        address payToken
    );

    /**
    * @notice ERC1155 address => token id => owner => auction id => auction
    */
    mapping(address => mapping(uint256 => mapping(address => mapping(uint256 => ERC1155Auction)))) internal _auctions;

    /**
    * @notice ERC1155 address => token id => owner => auction id => bid
    */
    mapping(address => mapping(uint256 => mapping(address => mapping(uint256 => HighestBid)))) internal _highestBids;

    constructor(address addressRegistry, address payable feeRecipient) MarketplaceBase(addressRegistry, feeRecipient) {}

    /**
     * @notice Get auction for given token and owner
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param auctionId Auction identifier
     * @return ERC1155Auction
     */
    function getAuction(
        NFTAddress nft,
        uint256 tokenId,
        address owner,
        uint256 auctionId
    ) public view returns (ERC1155Auction memory) {
        return _auctions[nft.toAddress()][tokenId][owner][auctionId];
    }

    /**
     * @notice Check given token and owner have any auction
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param auctionId Auction identifier
     * @return bool
     */
    function hasAuction(NFTAddress nft, uint256 tokenId, address owner, uint256 auctionId) public view returns (bool) {
        return _auctionExists(getAuction(nft, tokenId, owner, auctionId).auction);
    }

    /**
     * @notice Get highest bid for given token and owner
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param auctionId Auction identifier
     * @return HighestBid
     */
    function getHighestBid(
        NFTAddress nft,
        uint256 tokenId,
        address owner,
        uint256 auctionId
    ) public view returns (HighestBid memory) {
        return _highestBids[nft.toAddress()][tokenId][owner][auctionId];
    }

    /**
     * @notice Check given token and owner have any bid
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param auctionId Auction identifier
     * @return bool
     */
    function hasHighestBid(
        NFTAddress nft,
        uint256 tokenId,
        address owner,
        uint256 auctionId
    ) public view returns (bool) {
        return _highestBidExists(getHighestBid(nft, tokenId, owner, auctionId));
    }

    /**
     * @notice Create new auction
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param amount Token amount
     * @param auctionId Auction identifier
     * @param paymentToken Payment token that will be used for auction
     * @param reservePrice NFT address
     * @param startTime NFT address
     * @param endTime NFT address
     * @param isMinBidReservePrice NFT address
     */
    function createAuction(
        NFTAddress nft,
        uint256 tokenId,
        uint256 amount,
        uint256 auctionId,
        address paymentToken,
        uint256 reservePrice,
        uint256 startTime,
        uint256 endTime,
        bool isMinBidReservePrice
    ) public {
        _validateNewAuctionNFT(nft, tokenId, amount);

        _validatePaymentTokenIsEnabled(paymentToken);

        _validateNewAuctionTime(startTime, endTime);

        _validateAuctionNotExists(getAuction(nft, tokenId, _msgSender(), auctionId).auction);

        _createAuctionAndTransferToken(
            nft,
            tokenId,
            amount,
            auctionId,
            _msgSender(),
            paymentToken,
            reservePrice,
            startTime,
            endTime,
            isMinBidReservePrice
        );

        emit AuctionCreated(nft.toAddress(), tokenId, auctionId, _msgSender(), amount, paymentToken);
    }

    /**
     * @notice Cancel auction
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param auctionId Auction identifier
     */
    function cancelAuction(NFTAddress nft, uint256 tokenId, uint256 auctionId) public {
        ERC1155Auction memory erc1155Auction = getAuction(nft, tokenId, _msgSender(), auctionId);

        _validateAuctionExists(erc1155Auction.auction);

        HighestBid memory highestBid = getHighestBid(nft, tokenId, _msgSender());

        _validateAuctionHighestBidBelowReservePrice(erc1155Auction.auction, highestBid);

        _deleteAuctionAndTransferToken(nft, erc1155Auction, tokenId);

        emit AuctionCancelled(nft.toAddress(), _msgSender(), tokenId);

        if (_highestBidExists(highestBid)) {
            _refundHighestBid(erc1155Auction.auction, highestBid);
            _deleteHighestBid(nft, tokenId, _msgSender(), auctionId);
            emit BidRefunded(
                nft.toAddress(), erc1155Auction.auction.owner, tokenId, highestBid.bidder, highestBid.bidAmount
            );
        }
    }

    /**
     * @notice Finish auction successfully
     * @dev Successfully finish auction, to unsuccessfully finish auction call `cancelAuction`
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param auctionId
     */
    function finishAuction(NFTAddress nft, uint256 tokenId, address owner, uint256 auctionId) public {
        (ERC1155Auction memory erc1155Auction, HighestBid memory highestBid) =
            _getValidatedFinishedAuctionAndHighestBid(nft, tokenId, owner, auctionId);

        _validateAuctionOrHighestBidOwner(erc1155Auction.auction, highestBid, _msgSender());
        _validateAuctionHighestBidAboveOrEqualReservePrice(erc1155Auction.auction, highestBid);

        _finishAuctionSuccessFully(nft, tokenId, auctionId, erc1155Auction, highestBid);
    }

    /**
     * @notice Finish auction successfully with bid below reserve price
     * @dev Successfully finish auction, to unsuccessfully finish auction call `cancelAuction`
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param auctionId Auction identifier
     */
    function finishAuctionBelowReservePrice(NFTAddress nft, uint256 tokenId, address owner, uint256 auctionId) public {
        (ERC1155Auction memory erc1155Auction, HighestBid memory highestBid) =
            _getValidatedFinishedAuctionAndHighestBid(nft, tokenId, owner, auctionId);

        _validateAuctionOwner(erc1155Auction.auction, _msgSender());
        _validateAuctionHighestBidBelowReservePrice(erc1155Auction.auction, highestBid);

        _finishAuctionSuccessFully(nft, tokenId, erc1155Auction, highestBid);
    }

    /**
     * @notice Update auction reserve price
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param auctionId Auction identifier
     * @param reservePrice New reserve price
     */
    function updateAuctionReservePrice(
        NFTAddress nft,
        uint256 tokenId,
        uint256 auctionId,
        uint256 reservePrice
    ) public {
        ERC1155Auction memory erc1155Auction = getAuction(nft, tokenId, _msgSender(), auctionId);

        _validateAuctionExists(erc1155Auction.auction);

        _validateAuctionReservePriceUpdate(erc1155Auction.auction, reservePrice);

        _auctions[nft.toAddress()][tokenId][_msgSender()][auctionId].auction.reservePrice = reservePrice;

        emit AuctionReservePriceUpdated(
            nft.toAddress(),
            tokenId,
            _msgSender(),
            reservePrice
        );
    }

    /**
     * @notice Place bid
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param auctionId Auction identifier
     * @param bidAmount Bid amount
     */
    function placeBid(NFTAddress nft, uint256 tokenId, address owner, uint256 auctionId, uint256 bidAmount) public {
        Auction memory auction = getAuction(nft, tokenId, owner, auctionId).auction;

        _validateAuctionExists(auction);

        _validateAuctionStarted(auction);

        _validateAuctionNotEnded(auction);

        _validateAuctionBidderNotOwner(auction, _msgSender());

        HighestBid memory highestBid = getHighestBid(nft, tokenId, owner, auctionId);

        _validateAuctionBidAmount(auction, highestBid, bidAmount);

        _createBidAndTransferPayTokenAmount(nft, auction.paymentToken, tokenId, owner, _msgSender(), bidAmount);

        emit BidPlaced(nft.toAddress(), auction.owner, tokenId, _msgSender(), bidAmount);

        if (_highestBidExists(highestBid)) {
            _refundHighestBid(auction, highestBid);
            emit BidRefunded(nft.toAddress(), auction.owner, tokenId, highestBid.bidder, highestBid.bidAmount);
        }
    }

    /**
     * @notice Withdraw bid
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     */
    function withdrawBid(NFTAddress nft, uint256 tokenId, address owner) public {
        HighestBid memory highestBid = getHighestBid(nft, tokenId, owner);

        _validateAuctionHighestBidOwner(highestBid, _msgSender());

        Auction memory auction = getAuction(nft, tokenId, owner).auction;

        _validateAuctionEnded(auction);

        _validateAuctionHighestBidIsWithdrawable(auction, highestBid);

        _deleteHighestBid(nft, tokenId, owner);

        _refundHighestBid(auction, highestBid);

        emit BidWithdrawn(nft.toAddress(), auction.owner, tokenId, _msgSender(), highestBid.bidAmount);
    }

    /**
     * @notice Successfully finish an auction
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param erc1155Auction Auction to finish
     * @param highestBid Auction highest bid
     */
    function _finishAuctionSuccessFully(
        NFTAddress nft,
        uint256 tokenId,
        ERC1155Auction memory erc1155Auction,
        HighestBid memory highestBid
    ) internal {
        _deleteAuction(nft, tokenId, erc1155Auction.auction.owner);
        _deleteHighestBid(nft, tokenId, _msgSender());

        uint256 fee = _calculateAndTakeAuctionFee(erc1155Auction.auction, highestBid);
        uint256 finalAmount = highestBid.bidAmount - fee;

        uint256 royaltyFee = _calculateAndTakeRoyaltyFee(
            nft, tokenId, erc1155Auction.auction.paymentToken, finalAmount
        );

        finalAmount -= royaltyFee;

        if (finalAmount > 0) {
            _sendPayTokenAmount(erc1155Auction.auction.paymentToken, erc1155Auction.auction.owner, finalAmount);
        }

        nft.toERC1155().safeTransferFrom(
            address(this), highestBid.bidder, tokenId, erc1155Auction.tokenAmount, new bytes(0)
        );

        emit AuctionFinished(
            erc1155Auction.auction.owner,
            nft.toAddress(),
            tokenId,
            highestBid.bidder,
            erc1155Auction.auction.paymentToken,
            erc1155Auction.tokenAmount,
            highestBid.bidAmount
        );
    }

    /**
     * @notice Create bid and transfer pay token amount
     * @param nft NFT address
     * @param paymentToken Payment token
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param bidAmount Bid amount
     */
    function _createBidAndTransferPayTokenAmount(
        NFTAddress nft,
        address paymentToken,
        uint256 tokenId,
        address owner,
        address bidder,
        uint256 bidAmount
    ) internal {
        _highestBids[nft.toAddress()][tokenId][owner] = HighestBid({
            bidder: bidder,
            bidAmount: bidAmount,
            time: _getNow()
        });

        _receivePayTokenAmount(paymentToken, bidder, bidAmount);
    }

    /**
     * @notice Create new auction and transfer token
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param amount Token amount
     * @param auctionId Auction identifier
     * @param owner Token owner
     * @param paymentToken Payment token that will be used for auction
     * @param reservePrice NFT address
     * @param startTime NFT address
     * @param endTime NFT address
     * @param isMinBidReservePrice NFT address
     */
    function _createAuctionAndTransferToken(
        NFTAddress nft,
        uint256 tokenId,
        uint256 amount,
        uint256 auctionId,
        address owner,
        address paymentToken,
        uint256 reservePrice,
        uint256 startTime,
        uint256 endTime,
        bool isMinBidReservePrice
    ) internal {
        _auctions[nft.toAddress()][tokenId][owner][auctionId] = ERC1155Auction({
            auction: Auction({
                owner: owner,
                paymentToken: paymentToken,
                isMinBidReservePrice: isMinBidReservePrice,
                reservePrice: reservePrice,
                startTime: startTime,
                endTime: endTime
            }),
            tokenAmount: amount
        });

        // transfer token to be held in escrow
        nft.toERC1155().safeTransferFrom(owner, address(this), tokenId, amount, new bytes(0));
    }

    /**
     * @notice Delete auction and transfer token
     * @param nft NFT address
     * @param erc1155Auction Auction to delete
     * @param tokenId Token identifier
     */
    function _deleteAuctionAndTransferToken(
        NFTAddress nft,
        ERC1155Auction memory erc1155Auction,
        uint256 tokenId
    ) internal {
        address owner = erc1155Auction.auction.owner;

        _deleteAuction(nft, tokenId, owner);

        // transfer token back to owner
        nft.toERC1155().safeTransferFrom(address(this), owner, tokenId, erc1155Auction.tokenAmount, new bytes(0));
    }

    /**
     * @notice Delete auction
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     */
    function _deleteAuction(NFTAddress nft, uint256 tokenId, address owner) internal {
        delete _auctions[nft.toAddress()][tokenId][owner];
    }

    /**
     * @notice Delete highest bid
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param auctionId Auction identifier
     */
    function _deleteHighestBid(NFTAddress nft, uint256 tokenId, address owner, uint256 auctionId) internal {
        delete _highestBids[nft.toAddress()][tokenId][owner][auctionId];
    }

    /**
     * @notice Get validated finished auction and highest bid
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     */
    function _getValidatedFinishedAuctionAndHighestBid(
        NFTAddress nft,
        uint256 tokenId,
        address owner
    ) internal returns (ERC1155Auction memory, HighestBid memory) {
        ERC1155Auction memory erc1155Auction = getAuction(nft, tokenId, owner);

        _validateAuctionExists(erc1155Auction.auction);

        _validateAuctionEnded(erc1155Auction.auction);

        HighestBid memory highestBid = getHighestBid(nft, tokenId, owner);

        _validateHighestBidExists(highestBid);

        return (erc1155Auction, highestBid);
    }

    /**
     * @notice Validate new auction nft
     * @param nft NFT instance
     * @param tokenId Token identifier
     * @param amount Token amount
     */
    function _validateNewAuctionNFT(NFTAddress nft, uint256 tokenId, uint256 amount) internal {
        require(nft.isERC1155(), 'ERC1155Marketplace: NFT not ERC1155');
        require(
            nft.toERC1155().balanceOf(_msgSender(), tokenId) >= amount,
            'ERC1155Marketplace: balance too low'
        );
        require(
            nft.toERC1155().isApprovedForAll(_msgSender(), address(this)),
            'ERC1155Marketplace: not approved'
        );
    }
}

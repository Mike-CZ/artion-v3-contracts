// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/token/ERC20/IERC20.sol";
import "openzeppelin/contracts/token/ERC721/IERC721.sol";
import "openzeppelin/contracts/token/ERC1155/IERC1155.sol";
import "openzeppelin/contracts/token/ERC721/utils/ERC721Holder.sol";
import "openzeppelin/contracts/security/ReentrancyGuard.sol";
import "../interfaces/IAddressRegistry.sol";
import "../interfaces/IPaymentTokenRegistry.sol";
import "../interfaces/IERC721Marketplace.sol";
import "./library/NFTTradable.sol";
import "./MarketplaceBase.sol";

contract ERC721Marketplace is ERC721Holder, MarketplaceBase, IERC721Marketplace {
    using NFTTradable for NFTAddress;

    /// @notice NftAddress -> Token ID -> Listed item
    mapping(address => mapping(uint256 => Listing)) internal _listings;

    /// @notice NftAddress -> Token ID -> Offeror -> Offer
    mapping(address => mapping(uint256 =>  mapping(address => Offer))) internal _offers;

    /// @notice NftAddress -> Token ID -> auction
    mapping(address => mapping(uint256 => Auction)) internal _auctions;

    /// @notice NftAddress -> Token ID -> highest bid
    mapping(address => mapping(uint256 => HighestBid)) internal _highestBids;

    /// @notice Method for listing an NFT
    /// @param nftAddress Address of NFT contract
    /// @param tokenId Token ID of NFT
    /// @param paymentToken Payment token
    /// @param price Sale price for token
    /// @param startingTime Scheduling for a future sale
    function createListing(
        NFTAddress nftAddress,
        uint256 tokenId,
        address paymentToken,
        uint256 price,
        uint256 startingTime
    ) public whenNotPaused {
        _validateTokenInterface(nftAddress);
        _validateListingNotExists(getListing(nftAddress.toAddress(), tokenId));
        _validateNewListingTime(startingTime);
        _validatePaymentTokenIsEnabled(paymentToken);

        // transfer token to be held in escrow
        nftAddress.toERC721().safeTransferFrom(_msgSender(), address(this), tokenId, new bytes(0));

        _listings[nftAddress.toAddress()][tokenId] = Listing(
            payable(_msgSender()),
            paymentToken,
            price,
            startingTime
        );

        emit ERC721ListingCreated(
            _msgSender(),
            nftAddress.toAddress(),
            tokenId,
            paymentToken,
            price,
            startingTime
        );
    }

    /// @notice Method for updating listed NFT
    /// @param nftAddress Address of NFT contract
    /// @param tokenId Token ID of NFT
    /// @param newPaymentToken Payment token
    /// @param newPrice New sale price for token
    function updateListing(
        NFTAddress nftAddress,
        uint256 tokenId,
        address newPaymentToken,
        uint256 newPrice
    ) public {
        _validateListingExists(getListing(nftAddress.toAddress(), tokenId));
        _validatePaymentTokenIsEnabled(newPaymentToken);

        Listing storage listedItem = _listings[nftAddress.toAddress()][tokenId];
        _validateOwnership(listedItem.owner, _msgSender());

        listedItem.paymentToken = newPaymentToken;
        listedItem.price = newPrice;

        emit ERC721ListingUpdated(
            _msgSender(),
            nftAddress.toAddress(),
            tokenId,
            newPaymentToken,
            newPrice
        );
    }

    /// @notice Method for canceling listed NFT
    /// @param nftAddress Address of NFT contract
    /// @param tokenId Token ID of NFT
    function cancelListing(
        NFTAddress nftAddress,
        uint256 tokenId
    ) public nonReentrant {
        Listing memory listing = getListing(nftAddress.toAddress(), tokenId);

        _validateListingExists(listing);
        _validateOwnership(listing.owner, _msgSender());

        // transfer token from escrow back to original owner
        nftAddress.toERC721().safeTransferFrom(address(this), listing.owner, tokenId, new bytes(0));

        delete (_listings[nftAddress.toAddress()][tokenId]);
        emit ERC721ListingCanceled(_msgSender(), nftAddress.toAddress(), tokenId);
    }

    /// @notice Method for buying listed NFT
    /// @param nftAddress NFT contract address
    /// @param tokenId TokenId
    /// @param requestedPaymentToken Payment token
    function buyListedItem(
        NFTAddress nftAddress,
        uint256 tokenId,
        uint256 requestedUnitPrice,
        address requestedPaymentToken
    ) public nonReentrant whenNotPaused {
        Listing memory listing = getListing(nftAddress.toAddress(), tokenId);

        _validateListingExists(listing);
        _validateListingStarted(listing.startingTime);
        // validate price and payment token in case of listing update
        _validatePriceMatch(listing.price, requestedUnitPrice);
        _validatePaymentTokenAddressMatch(listing.paymentToken, requestedPaymentToken);

        delete (_listings[nftAddress.toAddress()][tokenId]);

        // Calculate and transfer platform fee and royalty
        uint256 finalAmount = listing.price - _calculateAndTakeListingFeeFrom(
            listing.price, listing.paymentToken, _msgSender()
        );
        finalAmount -= _calculateAndTakeRoyaltyFeeFrom(
            nftAddress, tokenId, listing.paymentToken, finalAmount, _msgSender()
        );

        // Transfer payment tokens from buyer to owner of NFT
        _transferPayTokenAmount(listing.paymentToken, _msgSender(), listing.owner, finalAmount);

        // Transfer NFT to buyer
        nftAddress.toERC721().safeTransferFrom(address(this), _msgSender(), tokenId, new bytes(0));

        emit ERC721ListedItemSold(
            listing.owner,
            _msgSender(),
            nftAddress.toAddress(),
            tokenId,
            listing.price,
            listing.paymentToken
        );
    }

    /// @notice Method for creating an offer on NFT
    /// @param nftAddress NFT contract address
    /// @param tokenId TokenId
    /// @param paymentToken Payment token
    /// @param price Offered price
    /// @param expirationTime Offer expiration
    function createOffer(
        NFTAddress nftAddress,
        uint256 tokenId,
        address paymentToken,
        uint256 price,
        uint256 expirationTime
    ) public whenNotPaused {
        _validateTokenInterface(nftAddress);
        _validatePaymentTokenIsEnabled(paymentToken);
        _validateOfferExpirationTime(expirationTime);
        _validateOfferNotExists(getOffer(nftAddress.toAddress(), tokenId, _msgSender()));

        // Lock payment token amount in marketplace
        if (_escrowOfferPaymentTokens) {
            _receivePayTokenAmount(paymentToken, _msgSender(), price);
        }

        _offers[nftAddress.toAddress()][tokenId][_msgSender()] = Offer(
            paymentToken,
            _msgSender(),
            price,
            expirationTime,
            _escrowOfferPaymentTokens
        );

        emit ERC721OfferCreated(
            _msgSender(),
            nftAddress.toAddress(),
            tokenId,
            paymentToken,
            price,
            expirationTime,
            _escrowOfferPaymentTokens
        );
    }

    /// @notice Method for canceling the offer
    /// @param nftAddress NFT contract address
    /// @param tokenId TokenId
    function cancelOffer(
        NFTAddress nftAddress,
        uint256 tokenId
    ) public nonReentrant {
        Offer memory offer = getOffer(nftAddress.toAddress(), tokenId, _msgSender());

        _validateOfferExists(offer);

        delete (_offers[nftAddress.toAddress()][tokenId][_msgSender()]);

        // Return locked payment tokens to offeror
        if (offer.paymentTokensInEscrow) {
            _sendPayTokenAmount(offer.paymentToken, offer.offeror, offer.price);
        }

        emit ERC721OfferCanceled(_msgSender(), nftAddress.toAddress(), tokenId);
    }

    /// @notice Method for accepting the offer
    /// @param nftAddress NFT contract address
    /// @param tokenId TokenId
    function acceptOffer(
        NFTAddress nftAddress,
        uint256 tokenId,
        address offeror
    ) public nonReentrant whenNotPaused {
        Offer memory offer = getOffer(nftAddress.toAddress(), tokenId, offeror);

        _validateOfferExists(offer);
        _validateOfferNotExpired(offer);

        delete (_offers[nftAddress.toAddress()][tokenId][offeror]);

        // Calculate and transfer platform fee
        uint256 finalAmount = offer.price - _calculateAndTakeOfferFee(offer);

        // Calculate royalty and transfer payment tokens
        // If offer was created when payment tokens were not stored in escrow,
        // transfer payment tokens from escrow to owner of NF,
        // transfer payment tokens from offeror to owner of NFT otherwise
        if (offer.paymentTokensInEscrow) {
            finalAmount -= _calculateAndTakeRoyaltyFee(nftAddress, tokenId, offer.paymentToken, finalAmount);
            _sendPayTokenAmount(offer.paymentToken, _msgSender(), finalAmount);
        } else {
            finalAmount -= _calculateAndTakeRoyaltyFeeFrom(
                nftAddress, tokenId, offer.paymentToken, finalAmount, offer.offeror
            );
            _transferPayTokenAmount(offer.paymentToken, offeror, _msgSender(), finalAmount);
        }

        // Transfer NFT to offeror
        nftAddress.toERC721().safeTransferFrom(_msgSender(), offeror, tokenId, new bytes(0));

        emit ERC721OfferAccepted(
            nftAddress.toAddress(),
            tokenId,
            offeror,
            _msgSender(),
            offer.price,
            offer.paymentToken
        );
    }

    /**
     * @notice Create new auction
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     * @param paymentToken Payment token that will be used for auction
     * @param reservePrice NFT address
     * @param startTime NFT address
     * @param endTime NFT address
     * @param isMinBidReservePrice NFT address
     */
    function createAuction(
        NFTAddress nftAddress,
        uint256 tokenId,
        address paymentToken,
        uint256 reservePrice,
        uint256 startTime,
        uint256 endTime,
        bool isMinBidReservePrice
    ) public whenNotPaused {
        _validateTokenInterface(nftAddress);
        _validatePaymentTokenIsEnabled(paymentToken);
        _validateAuctionNotExists(getAuction(nftAddress, tokenId));
        _validateNewAuctionTime(startTime, endTime);

        _createAuctionAndTransferToken(
            nftAddress, tokenId, _msgSender(), paymentToken, reservePrice, startTime, endTime, isMinBidReservePrice
        );

        emit ERC721AuctionCreated(nftAddress.toAddress(), tokenId, _msgSender(), paymentToken);
    }

    /**
     * @notice Cancel auction
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     */
    function cancelAuction(NFTAddress nftAddress, uint256 tokenId) public nonReentrant {
        Auction memory auction = getAuction(nftAddress, tokenId);
        _validateAuctionExists(auction);
        _validateOwnership(auction.owner, _msgSender());

        HighestBid memory highestBid = getHighestBid(nftAddress, tokenId);
        _validateAuctionHighestBidBelowReservePrice(auction, highestBid);
        _deleteAuctionAndTransferToken(nftAddress, auction, tokenId);

        emit ERC721AuctionCancelled(nftAddress.toAddress(), _msgSender(), tokenId);

        if (_highestBidExists(highestBid)) {
            _refundHighestBid(auction, highestBid);
            _deleteHighestBid(nftAddress, tokenId);
            emit ERC721BidRefunded(
                nftAddress.toAddress(), auction.owner, tokenId, highestBid.bidder, highestBid.bidAmount
            );
        }
    }

    /**
     * @notice Finish auction successfully
     * @dev Successfully finish auction, to unsuccessfully finish auction call `cancelAuction`
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     */
    function finishAuction(NFTAddress nftAddress, uint256 tokenId) public nonReentrant {
        (Auction memory auction, HighestBid memory highestBid) =
            _getValidatedFinishedAuctionAndHighestBid(nftAddress, tokenId);

        _validateAuctionOrHighestBidOwner(auction, highestBid, _msgSender());
        _validateAuctionHighestBidAboveOrEqualReservePrice(auction, highestBid);

        _finishAuctionSuccessFully(nftAddress, tokenId, auction, highestBid);
    }

    /**
     * @notice Finish auction successfully with bid below reserve price
     * @dev Successfully finish auction, to unsuccessfully finish auction call `cancelAuction`
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     */
    function finishAuctionBelowReservePrice(NFTAddress nftAddress, uint256 tokenId) public nonReentrant {
        (Auction memory auction, HighestBid memory highestBid) =
            _getValidatedFinishedAuctionAndHighestBid(nftAddress, tokenId);

        _validateAuctionOwner(auction, _msgSender());
        _validateAuctionHighestBidBelowReservePrice(auction, highestBid);

        _finishAuctionSuccessFully(nftAddress, tokenId, auction, highestBid);
    }

    /**
     * @notice Update auction reserve price
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     * @param reservePrice New reserve price
     */
    function updateAuctionReservePrice(
        NFTAddress nftAddress,
        uint256 tokenId,
        uint256 reservePrice
    ) public {
        Auction memory auction = getAuction(nftAddress, tokenId);

        _validateAuctionExists(auction);
        _validateAuctionOwner(auction, _msgSender());
        _validateAuctionReservePriceUpdate(auction, reservePrice);

        _auctions[nftAddress.toAddress()][tokenId].reservePrice = reservePrice;

        emit ERC721AuctionReservePriceUpdated(
            nftAddress.toAddress(),
            tokenId,
            _msgSender(),
            reservePrice
        );
    }

    /**
     * @notice Place bid
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     * @param bidAmount Bid amount
     */
    function placeBid(NFTAddress nftAddress, uint256 tokenId, uint256 bidAmount) public nonReentrant whenNotPaused {
        Auction memory auction = getAuction(nftAddress, tokenId);

        _validateAuctionExists(auction);
        _validateAuctionStarted(auction);
        _validateAuctionNotEnded(auction);
        _validateAuctionBidderNotOwner(auction, _msgSender());

        HighestBid memory highestBid = getHighestBid(nftAddress, tokenId);

        _validateAuctionBidAmount(auction, highestBid, bidAmount);

        _createBidAndTransferPayTokenAmount(
            nftAddress, auction.paymentToken, tokenId, _msgSender(), bidAmount
        );

        emit ERC721BidPlaced(nftAddress.toAddress(), auction.owner, tokenId, _msgSender(), bidAmount);

        if (_highestBidExists(highestBid)) {
            _refundHighestBid(auction, highestBid);
            emit ERC721BidRefunded(
                nftAddress.toAddress(),
                auction.owner,
                tokenId,
                highestBid.bidder,
                highestBid.bidAmount
            );
        }
    }

    /**
     * @notice Withdraw bid
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     */
    function withdrawBid(NFTAddress nftAddress, uint256 tokenId) public nonReentrant whenNotPaused {
        HighestBid memory highestBid = getHighestBid(nftAddress, tokenId);

        _validateHighestBidExists(highestBid);
        _validateAuctionHighestBidOwner(highestBid, _msgSender());

        Auction memory auction = getAuction(nftAddress, tokenId);

        _validateAuctionEnded(auction);
        _validateAuctionHighestBidIsWithdrawable(auction, highestBid);

        _deleteHighestBid(nftAddress, tokenId);

        _refundHighestBid(auction, highestBid);

        emit ERC721BidWithdrawn(
            nftAddress.toAddress(), auction.owner, tokenId, _msgSender(), highestBid.bidAmount
        );
    }

    ////////////////////////////
    /// Setters and Getters ///
    ///////////////////////////

    /**
     * @notice Get listing
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     * @return Listing
     */
    function getListing(address nftAddress, uint256 tokenId) public view returns (Listing memory) {
        return _listings[nftAddress][tokenId];
    }

    /**
     * @notice Get offer
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     * @return Offer
     */
    function getOffer(address nftAddress, uint256 tokenId, address offeror) public view returns (Offer memory) {
        return _offers[nftAddress][tokenId][offeror];
    }

    /**
     * @notice Get auction for given token and owner
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     * @return ERC1155Auction
     */
    function getAuction(NFTAddress nftAddress, uint256 tokenId) public view returns (Auction memory) {
        return _auctions[nftAddress.toAddress()][tokenId];
    }

    /**
     * @notice Get highest bid for given token and owner
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     * @return HighestBid
     */
    function getHighestBid(NFTAddress nftAddress, uint256 tokenId) public view returns (HighestBid memory) {
        return _highestBids[nftAddress.toAddress()][tokenId];
    }

    /**
     * @notice Check given token and owner have any auction
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     * @return bool
     */
    function hasAuction(NFTAddress nftAddress, uint256 tokenId) public view returns (bool) {
        return _auctionExists(getAuction(nftAddress, tokenId));
    }

    /**
     * @notice Check given token and owner have any bid
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     * @return bool
     */
    function hasHighestBid(NFTAddress nftAddress, uint256 tokenId) public view returns (bool) {
        return _highestBidExists(getHighestBid(nftAddress, tokenId));
    }

    ////////////////////////////
    /// Internal and Private ///
    ////////////////////////////

    /**
     * @notice Validate nft token interface
     * @param nftAddress NFT instance
     */
    function _validateTokenInterface(NFTAddress nftAddress) internal {
        require(nftAddress.isERC721(), 'ERC721Marketplace: NFT is not ERC721');
    }

    /**
     * @notice Successfully finish an auction
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     * @param auction Auction to finish
     * @param highestBid Auction highest bid
     */
    function _finishAuctionSuccessFully(
        NFTAddress nftAddress,
        uint256 tokenId,
        Auction memory auction,
        HighestBid memory highestBid
    ) internal {
        _deleteAuction(nftAddress, tokenId);
        _deleteHighestBid(nftAddress, tokenId);

        uint256 finalAmount = highestBid.bidAmount - _calculateAndTakeAuctionFee(auction, highestBid);
        finalAmount -= _calculateAndTakeRoyaltyFee(nftAddress, tokenId, auction.paymentToken, finalAmount);

        if (finalAmount > 0) {
            _sendPayTokenAmount(auction.paymentToken, auction.owner, finalAmount);
        }

        nftAddress.toERC721().safeTransferFrom(
            address(this), highestBid.bidder, tokenId, new bytes(0)
        );

        emit ERC721AuctionFinished(
            auction.owner,
            nftAddress.toAddress(),
            tokenId,
            highestBid.bidder,
            auction.paymentToken,
            highestBid.bidAmount
        );
    }

    /**
     * @notice Create new auction and transfer token
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     * @param owner Token owner
     * @param paymentToken Payment token that will be used for auction
     * @param reservePrice NFT address
     * @param startTime NFT address
     * @param endTime NFT address
     * @param isMinBidReservePrice NFT address
     */
    function _createAuctionAndTransferToken(
        NFTAddress nftAddress,
        uint256 tokenId,
        address owner,
        address paymentToken,
        uint256 reservePrice,
        uint256 startTime,
        uint256 endTime,
        bool isMinBidReservePrice
    ) internal {
        _auctions[nftAddress.toAddress()][tokenId] = Auction({
            owner: owner,
            paymentToken: paymentToken,
            isMinBidReservePrice: isMinBidReservePrice,
            reservePrice: reservePrice,
            startTime: startTime,
            endTime: endTime
        });

        // transfer token to be held in escrow
        nftAddress.toERC721().safeTransferFrom(owner, address(this), tokenId, new bytes(0));
    }

    /**
     * @notice Delete auction and transfer token
     * @param nftAddress NFT address
     * @param auction Auction to delete
     * @param tokenId Token identifier
     */
    function _deleteAuctionAndTransferToken(NFTAddress nftAddress, Auction memory auction, uint256 tokenId) internal {
        address owner = auction.owner;

        _deleteAuction(nftAddress, tokenId);

        // transfer token back to owner
        nftAddress.toERC721().safeTransferFrom(address(this), owner, tokenId, new bytes(0));
    }

    /**
     * @notice Delete auction
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     */
    function _deleteAuction(NFTAddress nftAddress, uint256 tokenId) internal {
        delete _auctions[nftAddress.toAddress()][tokenId];
    }

    /**
     * @notice Delete highest bid
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     */
    function _deleteHighestBid(NFTAddress nftAddress, uint256 tokenId) internal {
        delete _highestBids[nftAddress.toAddress()][tokenId];
    }

    /**
     * @notice Get validated finished auction and highest bid
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     */
    function _getValidatedFinishedAuctionAndHighestBid(
        NFTAddress nftAddress,
        uint256 tokenId
    ) internal returns (Auction memory, HighestBid memory) {
        Auction memory auction = getAuction(nftAddress, tokenId);

        _validateAuctionExists(auction);

        _validateAuctionEnded(auction);

        HighestBid memory highestBid = getHighestBid(nftAddress, tokenId);

        _validateHighestBidExists(highestBid);

        return (auction, highestBid);
    }

    /**
     * @notice Create bid and transfer pay token amount
     * @param nftAddress NFT address
     * @param paymentToken Payment token
     * @param tokenId Token identifier
     * @param bidder Bid owner
     * @param bidAmount Bid amount
     */
    function _createBidAndTransferPayTokenAmount(
        NFTAddress nftAddress,
        address paymentToken,
        uint256 tokenId,
        address bidder,
        uint256 bidAmount
    ) internal {
        _highestBids[nftAddress.toAddress()][tokenId] = HighestBid({
            bidder: bidder,
            bidAmount: bidAmount,
            time: _getNow()
        });

        _receivePayTokenAmount(paymentToken, bidder, bidAmount);
    }
}

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

    struct ERC1155Auction {
        Auction auction;
        uint256 tokenAmount;
    }

    struct ERC1155Listing {
        Listing listing;
        uint256 tokenAmount;
        uint256 remainingTokenAmount;
        uint256 unitSize;
    }

    struct ERC1155Offer {
        Offer offer;
        uint256 tokenAmount;
    }

    /**
    * @notice ERC1155 address => token id => owner => auction id => auction
    */
    mapping(address => mapping(uint256 => mapping(address => mapping(uint256 => ERC1155Auction)))) internal _auctions;

    /**
    * @notice ERC1155 address => token id => owner => auction id => bid
    */
    mapping(address => mapping(uint256 => mapping(address => mapping(uint256 => HighestBid)))) internal _highestBids;

    /**
    * @notice ERC1155 address => token id => owner => listing id => listing
    */
    mapping(address => mapping(uint256 => mapping(address => mapping(uint256 => ERC1155Listing)))) internal _listings;

    /**
    * @notice ERC1155 address => token id => offeror => offer
    */
    mapping(address => mapping(uint256 => mapping(address => ERC1155Offer))) internal _offers;

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
     * @notice Get listing for given token and owner
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param listingId Listing identifier
     * @return ERC1155Auction
     */
    function getListing(
        NFTAddress nft,
        uint256 tokenId,
        address owner,
        uint256 listingId
    ) public view returns (ERC1155Listing memory) {
        return _listings[nft.toAddress()][tokenId][owner][listingId];
    }

    /**
     * @notice Get offer for given token and offeror
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param offeror offeror address
     * @return ERC1155Offer
     */
    function getOffer(NFTAddress nft, uint256 tokenId, address offeror) public view returns (ERC1155Offer memory) {
        return _offers[nft.toAddress()][tokenId][offeror];
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
     * @notice Check given token and owner have any listing
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param listingId Listing identifier
     * @return bool
     */
    function hasListing(NFTAddress nft, uint256 tokenId, address owner, uint256 listingId) public view returns (bool) {
        return _listingExists(getListing(nft, tokenId, owner, listingId).listing);
    }

    /**
     * @notice Check given token and offeror have any offer
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param offeror offeror address
     * @return bool
     */
    function hasOffer(NFTAddress nft, uint256 tokenId, address offeror) public view returns (bool) {
        return _offerExists(getOffer(nft, tokenId, offeror).offer);
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
    ) public whenNotPaused {
        _validateTokenInterface(nft);
        _validateTokenAmountGtZero(amount);
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

        emit ERC1155AuctionCreated(nft.toAddress(), tokenId, auctionId, _msgSender(), amount, paymentToken);
    }

    /**
     * @notice Cancel auction
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param auctionId Auction identifier
     */
    function cancelAuction(NFTAddress nft, uint256 tokenId, uint256 auctionId) public nonReentrant {
        ERC1155Auction memory erc1155Auction = getAuction(nft, tokenId, _msgSender(), auctionId);

        _validateAuctionExists(erc1155Auction.auction);

        HighestBid memory highestBid = getHighestBid(nft, tokenId, _msgSender(), auctionId);

        _validateAuctionHighestBidBelowReservePrice(erc1155Auction.auction, highestBid);

        _deleteAuctionAndTransferToken(nft, tokenId, auctionId, erc1155Auction);

        emit ERC1155AuctionCancelled(nft.toAddress(), _msgSender(), tokenId, auctionId);

        if (_highestBidExists(highestBid)) {
            _refundHighestBid(erc1155Auction.auction, highestBid);
            _deleteHighestBid(nft, tokenId, _msgSender(), auctionId);
            emit ERC1155BidRefunded(
                nft.toAddress(),
                erc1155Auction.auction.owner,
                tokenId,
                auctionId,
                highestBid.bidder,
                highestBid.bidAmount
            );
        }
    }

    /**
     * @notice Finish auction successfully
     * @dev Successfully finish auction, to unsuccessfully finish auction call `cancelAuction`
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param auctionId Auction identifier
     */
    function finishAuction(NFTAddress nft, uint256 tokenId, address owner, uint256 auctionId) public nonReentrant {
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
    function finishAuctionBelowReservePrice(
        NFTAddress nft,
        uint256 tokenId,
        address owner,
        uint256 auctionId
    ) public nonReentrant {
        (ERC1155Auction memory erc1155Auction, HighestBid memory highestBid) =
            _getValidatedFinishedAuctionAndHighestBid(nft, tokenId, owner, auctionId);

        _validateAuctionOwner(erc1155Auction.auction, _msgSender());
        _validateAuctionHighestBidBelowReservePrice(erc1155Auction.auction, highestBid);

        _finishAuctionSuccessFully(nft, tokenId, auctionId, erc1155Auction, highestBid);
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

        emit ERC1155AuctionReservePriceUpdated(
            nft.toAddress(),
            tokenId,
            auctionId,
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
    function placeBid(
        NFTAddress nft,
        uint256 tokenId,
        address owner,
        uint256 auctionId,
        uint256 bidAmount
    ) public nonReentrant whenNotPaused {
        Auction memory auction = getAuction(nft, tokenId, owner, auctionId).auction;

        _validateAuctionExists(auction);
        _validateAuctionStarted(auction);
        _validateAuctionNotEnded(auction);
        _validateAuctionBidderNotOwner(auction, _msgSender());

        HighestBid memory highestBid = getHighestBid(nft, tokenId, owner, auctionId);

        _validateAuctionBidAmount(auction, highestBid, bidAmount);

        _createBidAndTransferPayTokenAmount(
            nft, auction.paymentToken, tokenId, auctionId, owner, _msgSender(), bidAmount
        );

        emit ERC1155BidPlaced(nft.toAddress(), auction.owner, tokenId, auctionId, _msgSender(), bidAmount);

        if (_highestBidExists(highestBid)) {
            _refundHighestBid(auction, highestBid);
            emit ERC1155BidRefunded(
                nft.toAddress(),
                auction.owner,
                tokenId,
                auctionId,
                highestBid.bidder,
                highestBid.bidAmount
            );
        }
    }

    /**
     * @notice Withdraw bid
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param auctionId Auction identifier
     */
    function withdrawBid(
        NFTAddress nft,
        uint256 tokenId,
        address owner,
        uint256 auctionId
    ) public nonReentrant whenNotPaused {
        HighestBid memory highestBid = getHighestBid(nft, tokenId, owner, auctionId);

        _validateHighestBidExists(highestBid);
        _validateAuctionHighestBidOwner(highestBid, _msgSender());

        Auction memory auction = getAuction(nft, tokenId, owner, auctionId).auction;

        _validateAuctionEnded(auction);
        _validateAuctionHighestBidIsWithdrawable(auction, highestBid);

        _deleteHighestBid(nft, tokenId, owner, auctionId);

        _refundHighestBid(auction, highestBid);

        emit ERC1155BidWithdrawn(
            nft.toAddress(), auction.owner, tokenId, auctionId, _msgSender(), highestBid.bidAmount
        );
    }

    /**
     * @notice Method for listing an NFT
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param paymentToken Payment token that will be used for listing
     * @param tokenAmount Amount of tokens to list
     * @param unitSize Purchasable size of tokens
     * @param unitPrice Price of unit
     * @param listingId Listing identifier
     * @param startingTime Listing start time
     */
    function createListing(
        NFTAddress nft,
        uint256 tokenId,
        address paymentToken,
        uint256 tokenAmount,
        uint256 unitSize,
        uint256 unitPrice,
        uint256 listingId,
        uint256 startingTime
    ) public whenNotPaused {
        _validateTokenInterface(nft);
        _validateTokenAmountGtZero(tokenAmount);
        _validateListingNotExists(getListing(nft, tokenId, _msgSender(), listingId).listing);
        _validateNewListingTime(startingTime);
        _validatePaymentTokenIsEnabled(paymentToken);

        // amount has to be divisible by unit size
        require(tokenAmount % unitSize == 0, 'ERC1155Marketplace: invalid amount');

        _createListingAndTransferToken(
            nft,
            tokenId,
            _msgSender(),
            paymentToken,
            tokenAmount,
            unitSize,
            unitPrice,
            listingId,
            startingTime
        );

        emit ERC1155ListingCreated(
            _msgSender(),
            nft.toAddress(),
            tokenId,
            tokenAmount,
            unitSize,
            unitPrice,
            listingId,
            paymentToken,
            startingTime
        );
    }

    /**
     * @notice Method for updating listed NFT
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param listingId Listing identifier
     * @param newPaymentToken Payment token that will be used for listing
     * @param newBuyAmountPrice New listing price
     */
    function updateListing(
        NFTAddress nft,
        uint256 tokenId,
        uint256 listingId,
        address newPaymentToken,
        uint256 newBuyAmountPrice
    ) public {
        _validateListingExists(getListing(nft, tokenId, _msgSender(), listingId).listing);
        _validatePaymentTokenIsEnabled(newPaymentToken);

        ERC1155Listing storage erc1155Listing = _listings[nft.toAddress()][tokenId][_msgSender()][listingId];
        erc1155Listing.listing.paymentToken = newPaymentToken;
        erc1155Listing.listing.price = newBuyAmountPrice;

        emit ERC1155ListingUpdated(
            _msgSender(),
            nft.toAddress(),
            tokenId,
            listingId,
            newPaymentToken,
            newBuyAmountPrice
        );
    }

    /**
     * @notice Method for canceling listed NFT
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param listingId Listing identifier
     */
    function cancelListing(NFTAddress nft, uint256 tokenId, uint256 listingId) public nonReentrant {
        ERC1155Listing memory erc1155Listing = getListing(nft, tokenId, _msgSender(), listingId);

        _validateListingExists(erc1155Listing.listing);

        _deleteListingAndTransferToken(nft, tokenId, listingId, _msgSender(), erc1155Listing);

        emit ERC1155ListingCanceled(_msgSender(), nft.toAddress(), tokenId, listingId);
    }

    /**
     * @notice Method for buying listed NFT
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Listing owner
     * @param listingId Listing identifier
     * @param requestedUnitPrice Price buyer is willing to pay per unit
     * @param requestedPaymentToken Payment token buyer is willing to use
     * @param requestedUnits Requested units of tokens to buy
     */
    function buyListedItem(
        NFTAddress nft,
        uint256 tokenId,
        address owner,
        uint256 listingId,
        uint256 requestedUnitPrice,
        address requestedPaymentToken,
        uint256 requestedUnits
    ) public nonReentrant whenNotPaused {
        ERC1155Listing memory erc1155Listing = getListing(nft, tokenId, owner, listingId);

        _validateListingExists(erc1155Listing.listing);
        _validateListingStarted(erc1155Listing.listing);
        // validate price and payment token in case of listing update
        _validatePriceMatch(erc1155Listing.listing.price, requestedUnitPrice);
        _validatePaymentTokenAddressMatch(erc1155Listing.listing.paymentToken, requestedPaymentToken);

        uint256 requestedTokenAmount = requestedUnits * erc1155Listing.unitSize;

        // requested amount has to be available
        require(
            requestedTokenAmount > 0 && requestedTokenAmount <= erc1155Listing.remainingTokenAmount,
            'ERC1155Marketplace: invalid units'
        );

        // calculate base price based on units
        uint256 basePrice = requestedUnits * erc1155Listing.listing.price;

        // calculate remaining tokens and subtract from / delete listing
        uint256 remainingTokenAmount = erc1155Listing.remainingTokenAmount - requestedTokenAmount;
        if (remainingTokenAmount > 0) {
            _listings[nft.toAddress()][tokenId][owner][listingId].remainingTokenAmount = remainingTokenAmount;
        } else {
            _deleteListing(nft, tokenId, owner, listingId);
        }

        uint256 finalAmount = basePrice - _calculateAndTakeListingFeeFrom(
            basePrice, erc1155Listing.listing.paymentToken, _msgSender()
        );
        finalAmount -= _calculateAndTakeRoyaltyFeeFrom(
            nft, tokenId, erc1155Listing.listing.paymentToken, finalAmount, _msgSender()
        );

        _transferPayTokenAmount(erc1155Listing.listing.paymentToken, _msgSender(), owner, finalAmount);

        nft.toERC1155().safeTransferFrom(address(this), _msgSender(), tokenId, requestedTokenAmount, new bytes(0));

        emit ERC1155ListedItemSold(
            owner,
            _msgSender(),
            nft.toAddress(),
            tokenId,
            requestedTokenAmount,
            remainingTokenAmount,
            basePrice,
            erc1155Listing.listing.paymentToken
        );
    }

    /**
     * @notice Method for creating an offer on NFT
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param tokenAmount Token amount
     * @param paymentToken Payment token
     * @param price Offered price
     * @param expirationTime Offer expiration
     */
    function createOffer(
        NFTAddress nft,
        uint256 tokenId,
        uint256 tokenAmount,
        address paymentToken,
        uint256 price,
        uint256 expirationTime
    ) public whenNotPaused {
        _validateTokenInterface(nft);
        _validateTokenAmountGtZero(tokenAmount);
        _validatePaymentTokenIsEnabled(paymentToken);
        _validateOfferExpirationTime(expirationTime);
        _validateOfferNotExists(getOffer(nft, tokenId, _msgSender()).offer);

        // Lock payment token amount in marketplace
        if (_escrowOfferPaymentTokens) {
            _receivePayTokenAmount(paymentToken, _msgSender(), price);
        }

        _offers[nft.toAddress()][tokenId][_msgSender()] = ERC1155Offer({
            offer: Offer({
                paymentToken: paymentToken,
                offeror: _msgSender(),
                price: price,
                expirationTime: expirationTime,
                paymentTokensInEscrow: _escrowOfferPaymentTokens
            }),
            tokenAmount: tokenAmount
        });

        emit ERC1155OfferCreated(
            _msgSender(),
            nft.toAddress(),
            tokenId,
            tokenAmount,
            paymentToken,
            price,
            expirationTime,
            _escrowOfferPaymentTokens
        );
    }

    /**
     * @notice Method for canceling an offer on NFT
     * @param nft NFT address
     * @param tokenId Token identifier
     */
    function cancelOffer(NFTAddress nft, uint256 tokenId) public nonReentrant {
        ERC1155Offer memory erc1155Offer = getOffer(nft, tokenId, _msgSender());

        _validateOfferExists(erc1155Offer.offer);

        _deleteOffer(nft, tokenId, _msgSender());

        // Return locked payment tokens to offeror
        if (erc1155Offer.offer.paymentTokensInEscrow) {
            _sendPayTokenAmount(erc1155Offer.offer.paymentToken, erc1155Offer.offer.offeror, erc1155Offer.offer.price);
        }

        emit ERC1155OfferCanceled(_msgSender(), nft.toAddress(), tokenId, erc1155Offer.tokenAmount);
    }

    /**
     * @notice Method for accepting an offer on NFT
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param offeror Offeror address
     */
    function acceptOffer(NFTAddress nft, uint256 tokenId, address offeror) public nonReentrant whenNotPaused {
        ERC1155Offer memory erc1155Offer = getOffer(nft, tokenId, offeror);

        _validateOfferExists(erc1155Offer.offer);
        _validateOfferNotExpired(erc1155Offer.offer);

        _deleteOffer(nft, tokenId, offeror);

        uint256 finalAmount = erc1155Offer.offer.price - _calculateAndTakeOfferFee(erc1155Offer.offer);

        if (erc1155Offer.offer.paymentTokensInEscrow) {
            finalAmount -= _calculateAndTakeRoyaltyFee(nft, tokenId, erc1155Offer.offer.paymentToken, finalAmount);
            _sendPayTokenAmount(erc1155Offer.offer.paymentToken, _msgSender(), finalAmount);
        } else {
            finalAmount -= _calculateAndTakeRoyaltyFeeFrom(
                nft, tokenId, erc1155Offer.offer.paymentToken, finalAmount, erc1155Offer.offer.offeror
            );
            _transferPayTokenAmount(erc1155Offer.offer.paymentToken, offeror, _msgSender(), finalAmount);
        }

        nft.toERC1155().safeTransferFrom(_msgSender(), offeror, tokenId, erc1155Offer.tokenAmount, new bytes(0));

        emit ERC1155OfferAccepted(
            nft.toAddress(),
            tokenId,
            erc1155Offer.tokenAmount,
            offeror,
            _msgSender(),
            erc1155Offer.offer.price,
            erc1155Offer.offer.paymentToken
        );
    }

    /**
     * @notice Successfully finish an auction
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param auctionId Auction identifier
     * @param erc1155Auction Auction to finish
     * @param highestBid Auction highest bid
     */
    function _finishAuctionSuccessFully(
        NFTAddress nft,
        uint256 tokenId,
        uint256 auctionId,
        ERC1155Auction memory erc1155Auction,
        HighestBid memory highestBid
    ) internal {
        _deleteAuction(nft, tokenId, erc1155Auction.auction.owner, auctionId);
        _deleteHighestBid(nft, tokenId, erc1155Auction.auction.owner, auctionId);

        uint256 finalAmount = highestBid.bidAmount - _calculateAndTakeAuctionFee(erc1155Auction.auction, highestBid);
        finalAmount -= _calculateAndTakeRoyaltyFee(nft, tokenId, erc1155Auction.auction.paymentToken, finalAmount);

        if (finalAmount > 0) {
            _sendPayTokenAmount(erc1155Auction.auction.paymentToken, erc1155Auction.auction.owner, finalAmount);
        }

        nft.toERC1155().safeTransferFrom(
            address(this), highestBid.bidder, tokenId, erc1155Auction.tokenAmount, new bytes(0)
        );

        emit ERC1155AuctionFinished(
            erc1155Auction.auction.owner,
            nft.toAddress(),
            tokenId,
            auctionId,
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
     * @param auctionId Auction identifier
     * @param owner Auction owner
     * @param bidAmount Bid amount
     */
    function _createBidAndTransferPayTokenAmount(
        NFTAddress nft,
        address paymentToken,
        uint256 tokenId,
        uint256 auctionId,
        address owner,
        address bidder,
        uint256 bidAmount
    ) internal {
        _highestBids[nft.toAddress()][tokenId][owner][auctionId] = HighestBid({
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
     * @notice Create new listing and transfer token
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Token owner
     * @param paymentToken Payment token that will be used for listing
     * @param tokenAmount Amount of tokens to list
     * @param unitSize Purchasable size of tokens
     * @param unitPrice Price of unit
     * @param listingId Listing identifier
     * @param startingTime Listing start time
     */
    function _createListingAndTransferToken(
        NFTAddress nft,
        uint256 tokenId,
        address owner,
        address paymentToken,
        uint256 tokenAmount,
        uint256 unitSize,
        uint256 unitPrice,
        uint256 listingId,
        uint256 startingTime
    ) internal {
        _listings[nft.toAddress()][tokenId][owner][listingId] = ERC1155Listing({
            listing: Listing({
                owner: owner,
                paymentToken: paymentToken,
                price: unitPrice,
                startingTime: startingTime
            }),
            tokenAmount: tokenAmount,
            remainingTokenAmount: tokenAmount,
            unitSize: unitSize
        });

        // transfer token to be held in escrow
        nft.toERC1155().safeTransferFrom(owner, address(this), tokenId, tokenAmount, new bytes(0));
    }

    /**
     * @notice Delete auction and transfer token
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param auctionId Auction identifier
     * @param erc1155Auction Auction to delete
     */
    function _deleteAuctionAndTransferToken(
        NFTAddress nft,
        uint256 tokenId,
        uint256 auctionId,
        ERC1155Auction memory erc1155Auction
    ) internal {
        address owner = erc1155Auction.auction.owner;

        _deleteAuction(nft, tokenId, owner, auctionId);

        // transfer token back to owner
        nft.toERC1155().safeTransferFrom(address(this), owner, tokenId, erc1155Auction.tokenAmount, new bytes(0));
    }

    /**
     * @notice Delete listing and transfer remaining token amount
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param listingId Listing identifier
     * @param owner Listing owner
     * @param erc1155Listing Listing to delete
     */
    function _deleteListingAndTransferToken(
        NFTAddress nft,
        uint256 tokenId,
        uint256 listingId,
        address owner,
        ERC1155Listing memory erc1155Listing
    ) internal {
        _deleteListing(nft, tokenId, owner, listingId);

        // transfer token back to owner
        nft.toERC1155().safeTransferFrom(
            address(this), owner, tokenId, erc1155Listing.remainingTokenAmount, new bytes(0)
        );
    }

    /**
     * @notice Delete auction
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param auctionId Auction identifier
     */
    function _deleteAuction(NFTAddress nft, uint256 tokenId, address owner, uint256 auctionId) internal {
        delete _auctions[nft.toAddress()][tokenId][owner][auctionId];
    }

    /**
     * @notice Delete listing
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Listing owner
     * @param listingId Listing identifier
     */
    function _deleteListing(NFTAddress nft, uint256 tokenId, address owner, uint256 listingId) internal {
        delete _listings[nft.toAddress()][tokenId][owner][listingId];
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
     * @notice Delete offer
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param offeror Offeror address
     */
    function _deleteOffer(NFTAddress nft, uint256 tokenId, address offeror) internal {
        delete _offers[nft.toAddress()][tokenId][offeror];
    }

    /**
     * @notice Get validated finished auction and highest bid
     * @param nft NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     * @param auctionId Auction identifier
     */
    function _getValidatedFinishedAuctionAndHighestBid(
        NFTAddress nft,
        uint256 tokenId,
        address owner,
        uint256 auctionId
    ) internal returns (ERC1155Auction memory, HighestBid memory) {
        ERC1155Auction memory erc1155Auction = getAuction(nft, tokenId, owner, auctionId);

        _validateAuctionExists(erc1155Auction.auction);

        _validateAuctionEnded(erc1155Auction.auction);

        HighestBid memory highestBid = getHighestBid(nft, tokenId, owner, auctionId);

        _validateHighestBidExists(highestBid);

        return (erc1155Auction, highestBid);
    }

    /**
     * @notice Validate nft token interface
     * @param nft NFT instance
     */
    function _validateTokenInterface(NFTAddress nft) internal {
        require(nft.isERC1155(), 'ERC1155Marketplace: NFT not ERC1155');
    }

    /**
     * @notice Validate token amount is greater than zero
     * @param amount Token amount
     */
    function _validateTokenAmountGtZero(uint256 amount) internal pure {
        require(amount > 0, 'ERC1155Marketplace: invalid amount');
    }
}

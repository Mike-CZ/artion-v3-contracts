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

contract ERC721Marketplace is ERC721Holder, ReentrancyGuard, MarketplaceBase, IERC721Marketplace {
    using NFTTradable for NFTAddress;

    /// @notice NftAddress -> Token ID -> Listed item
    mapping(address => mapping(uint256 => Listing)) private _listings;
    /// @notice NftAddress -> Token ID -> Offer
    mapping(address => mapping(uint256 =>  Offer)) private _offers;
    /// @notice NftAddress -> Token ID -> auction
    mapping(address => mapping(uint256 => Auction)) internal _auctions;
    /// @notice NftAddress -> Token ID -> highest bid
    mapping(address => mapping(uint256 => HighestBid)) internal _highestBids;

    modifier isListed(address nftAddress, uint256 tokenId) {
        Listing memory listing = _listings[nftAddress][tokenId];
        require(listing.paymentToken != address(0), "ERC721Marketplace: NFT is not listed");
        _;
    }

    modifier isNotListed(address nftAddress, uint256 tokenId) {
        Listing memory listing = _listings[nftAddress][tokenId];
        require(listing.paymentToken == address(0), "ERC721Marketplace: NFT is already listed");
        _;
    }

    modifier offerExists(address nftAddress, uint256 tokenId) {
        Offer memory offer = _offers[nftAddress][tokenId];
        require(offer.paymentToken != address(0), "ERC721Marketplace: offer does not exists");
        _;
    }

    modifier offerNotExpired(address nftAddress, uint256 tokenId) {
        Offer memory offer = _offers[nftAddress][tokenId];
        require(offer.expirationTime > _getNow(), "ERC721Marketplace: offer is expired");
        _;
    }

    modifier offerNotExists(address nftAddress, uint256 tokenId) {
        Offer memory offer = _offers[nftAddress][tokenId];
        require(offer.paymentToken == address(0), "ERC721Marketplace: offer already exists");
        _;
    }

    constructor(
        address addressRegistry,
        address payable feeRecipient,
        bool escrowOfferPaymentTokens
    ) MarketplaceBase(addressRegistry, feeRecipient, escrowOfferPaymentTokens) {}

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
    ) external isNotListed(nftAddress.toAddress(), tokenId) {
        _validateTokenInterface(nftAddress);
        _validateNewListingTime(startingTime);
        _validatePaymentTokenIsEnabled(paymentToken);
        _validateOwnershipAndApproval(nftAddress, tokenId);

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
    /// @param paymentToken Payment token
    /// @param newPrice New sale price for token
    function updateListing(
        NFTAddress nftAddress,
        uint256 tokenId,
        address paymentToken,
        uint256 newPrice
    ) external nonReentrant isListed(nftAddress.toAddress(), tokenId) {
        _validatePaymentTokenIsEnabled(paymentToken);

        Listing storage listedItem = _listings[nftAddress.toAddress()][tokenId];
        _validateOwnership(listedItem.nftOwner);

        listedItem.paymentToken = paymentToken;
        listedItem.price = newPrice;

        emit ERC721ListingUpdated(
            _msgSender(),
            nftAddress.toAddress(),
            tokenId,
            paymentToken,
            newPrice
        );
    }

    /// @notice Method for canceling listed NFT
    /// @param nftAddress Address of NFT contract
    /// @param tokenId Token ID of NFT
    function cancelListing(
        NFTAddress nftAddress,
        uint256 tokenId
    ) external nonReentrant isListed(nftAddress.toAddress(), tokenId) {
        address listingOwner = _listings[nftAddress.toAddress()][tokenId].nftOwner;
        _validateOwnership(listingOwner);

        // transfer token from escrow back to original owner
        nftAddress.toERC721().safeTransferFrom(address(this), listingOwner, tokenId, new bytes(0));

        delete (_listings[nftAddress.toAddress()][tokenId]);
        emit ERC721ListingCanceled(_msgSender(), nftAddress.toAddress(), tokenId);
    }

    /// @notice Method for buying listed NFT
    /// @param nftAddress NFT contract address
    /// @param tokenId TokenId
    /// @param paymentToken Payment token
    function buyListedItem(NFTAddress nftAddress, uint256 tokenId, address paymentToken)
        external
        nonReentrant
        isListed(nftAddress.toAddress(), tokenId)
    {
        require(
            _listings[nftAddress.toAddress()][tokenId].paymentToken == paymentToken,
            "ERC721Marketplace: invalid payment token"
        );
        _validateListingStarted(_listings[nftAddress.toAddress()][tokenId].startingTime);

        _buyListedItem(nftAddress, tokenId);
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
    ) external offerNotExists(nftAddress.toAddress(), tokenId) {
        _validateTokenInterface(nftAddress);

        _validatePaymentTokenIsEnabled(paymentToken);

        _validateOfferExpirationTime(expirationTime);

        _validateTokenIsNotEscrow(nftAddress, tokenId);

        // Lock payment token amount in marketplace
        if (_escrowOfferPaymentTokens) {
            _receivePayTokenAmount(paymentToken, _msgSender(), price);
        }

        _offers[nftAddress.toAddress()][tokenId] = Offer(
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
            expirationTime
        );
    }

    /// @notice Method for canceling the offer
    /// @param nftAddress NFT contract address
    /// @param tokenId TokenId
    function cancelOffer(
        NFTAddress nftAddress,
        uint256 tokenId
    ) external offerExists(nftAddress.toAddress(), tokenId) {
        Offer memory offer = _offers[nftAddress.toAddress()][tokenId];
        _validateOfferOwnership(offer.offeror);

        // Return locked payment tokens to offeror
        if (offer.paymentTokensInEscrow) {
            _sendPayTokenAmount(offer.paymentToken, payable(offer.offeror), offer.price);
        }

        delete (_offers[nftAddress.toAddress()][tokenId]);
        emit ERC721OfferCanceled(_msgSender(), nftAddress.toAddress(), tokenId);
    }

    /// @notice Method for accepting the offer
    /// @param nftAddress NFT contract address
    /// @param tokenId TokenId
    function acceptOffer(
        NFTAddress nftAddress,
        uint256 tokenId
    )
        external
        nonReentrant
        offerExists(nftAddress.toAddress(), tokenId)
        offerNotExpired(nftAddress.toAddress(), tokenId)
    {
        _validateOwnership(nftAddress.toERC721().ownerOf(tokenId));

        Offer memory offer = _offers[nftAddress.toAddress()][tokenId];

        // If offer was created when payment tokens were not stored in escrow, check if offeror has enough of them
        if (!offer.paymentTokensInEscrow) {
            _validateOfferorPaymentTokenAmount(offer.offeror, offer.paymentToken, offer.price);
        }

        // Calculate and transfer platform fee
        uint256 feeAmount = _calculateAndTakeOfferFee(offer);

        // TODO: Royalty

        // If offer was created when payment tokens were not stored in escrow,
        // transfer payment tokens from offeror to owner of NFT,
        // transfer payment tokens from escrow to owner of NF otherwise
        if (!offer.paymentTokensInEscrow) {
            _transferPayTokenAmount(offer.paymentToken, offer.offeror, payable(_msgSender()), offer.price - feeAmount);
        } else {
            _sendPayTokenAmount(offer.paymentToken, payable(_msgSender()), offer.price - feeAmount);
        }

        // Transfer NFT to offeror
        nftAddress.toERC721().safeTransferFrom(_msgSender(), offer.offeror, tokenId, new bytes(0));

        emit ERC721OfferAccepted(
            nftAddress.toAddress(),
            tokenId,
            offer.offeror,
            _msgSender(),
            offer.price,
            offer.paymentToken
        );

        // If an offer was created, then the token listed and then the offer accepted,
        // there is and listing to be removed
        delete (_listings[nftAddress.toAddress()][tokenId]);
        delete (_offers[nftAddress.toAddress()][tokenId]);
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
    ) public {
        _validateTokenInterface(nftAddress);
        _validatePaymentTokenIsEnabled(paymentToken);
        _validateOwnershipAndApproval(nftAddress, tokenId);
        _validateNewAuctionTime(startTime, endTime);
        _validateAuctionNotExists(getAuction(nftAddress, tokenId));

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
    function cancelAuction(NFTAddress nftAddress, uint256 tokenId) public {
        Auction memory auction = getAuction(nftAddress, tokenId);
        _validateAuctionExists(auction);

        // TODO: Validate auction ownership

        HighestBid memory highestBid = getHighestBid(nftAddress, tokenId);
        _validateAuctionHighestBidBelowReservePrice(auction, highestBid);
        _deleteAuctionAndTransferToken(nftAddress, auction, tokenId);

        emit ERC721AuctionCancelled(nftAddress.toAddress(), _msgSender(), tokenId);

        if (_highestBidExists(highestBid)) {
            _refundHighestBid(auction, highestBid);
            _deleteHighestBid(nftAddress, tokenId);
            emit BidRefunded(
                nftAddress.toAddress(), auction.owner, tokenId, highestBid.bidder, highestBid.bidAmount
            );
        }
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
    function getListing(address nftAddress, uint256 tokenId) external view returns (Listing memory) {
        return _listings[nftAddress][tokenId];
    }

    /**
     * @notice Get offer
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     * @return Offer
     */
    function getOffer(address nftAddress, uint256 tokenId) external view returns (Offer memory) {
        return _offers[nftAddress][tokenId];
    }

    /**
     * @notice Get auction for given token and owner
     * @param nft NFT address
     * @param tokenId Token identifier
     * @return ERC1155Auction
     */
    function getAuction(NFTAddress nft, uint256 tokenId) public view returns (Auction memory) {
        return _auctions[nft.toAddress()][tokenId];
    }

    /**
     * @notice Get highest bid for given token and owner
     * @param nft NFT address
     * @param tokenId Token identifier
     * @return HighestBid
     */
    function getHighestBid(NFTAddress nft, uint256 tokenId) public view returns (HighestBid memory) {
        return _highestBids[nft.toAddress()][tokenId];
    }

    /**
     * @notice Check given token and owner have any auction
     * @param nft NFT address
     * @param tokenId Token identifier
     * @return bool
     */
    function hasAuction(NFTAddress nft, uint256 tokenId) public view returns (bool) {
        return _auctionExists(getAuction(nft, tokenId));
    }

    /**
     * @notice Check given token and owner have any bid
     * @param nft NFT address
     * @param tokenId Token identifier
     * @return bool
     */
    function hasHighestBid(NFTAddress nft, uint256 tokenId) public view returns (bool) {
        return _highestBidExists(getHighestBid(nft, tokenId));
    }

    ////////////////////////////
    /// Internal and Private ///
    ////////////////////////////

    function _validateTokenInterface(NFTAddress nftAddress) internal {
        require(nftAddress.isERC721(), 'ERC721Marketplace: NFT is not ERC721');
    }

    function _validateOwnershipAndApproval(NFTAddress nftAddress, uint256 tokenId) internal {
        require(
            nftAddress.toERC721().ownerOf(tokenId) == _msgSender(),
            "ERC721Marketplace: does not own the token"
        );
        require(
            nftAddress.toERC721().isApprovedForAll(_msgSender(), address(this)) ||
            nftAddress.toERC721().getApproved(tokenId) == address(this),
            "ERC721Marketplace: not approved for the token"
        );
    }

    function _validateOwnership(address owner) internal {
        require(owner == _msgSender(), "ERC721Marketplace: does not own the token");
    }

    function _validateTokenIsNotEscrow(NFTAddress nftAddress, uint256 tokenId) internal {
        require(
            nftAddress.toERC721().ownerOf(tokenId) != address(this),
            "ERC721Marketplace: NFT already in escrow"
        );
    }

    function _buyListedItem(NFTAddress nftAddress, uint256 tokenId) private {
        Listing memory listedItem = _listings[nftAddress.toAddress()][tokenId];
        address payable owner = listedItem.nftOwner;
        address paymentToken = listedItem.paymentToken;
        uint256 price = listedItem.price;

        // Calculate and transfer platform fee from buyer to platform
        uint256 feeAmount = _calculateAndTakeListingFee(listedItem);

        // TODO: Royalty

        // Transfer payment tokens from buyer to owner of NFT
        _transferPayTokenAmount(paymentToken, _msgSender(), owner, price - feeAmount);

        // Transfer NFT to buyer
        nftAddress.toERC721().safeTransferFrom(address(this), _msgSender(), tokenId, new bytes(0));

        emit ERC721ListedItemSold(
            owner,
            _msgSender(),
            nftAddress.toAddress(),
            tokenId,
            price,
            paymentToken
        );

        delete (_listings[nftAddress.toAddress()][tokenId]);
    }

    /**
     * @notice Create new auction and transfer token
     * @param nft NFT address
     * @param tokenId Token identifier
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
        address owner,
        address paymentToken,
        uint256 reservePrice,
        uint256 startTime,
        uint256 endTime,
        bool isMinBidReservePrice
    ) internal {
        _auctions[nft.toAddress()][tokenId] = Auction({
            owner: owner,
            paymentToken: paymentToken,
            isMinBidReservePrice: isMinBidReservePrice,
            reservePrice: reservePrice,
            startTime: startTime,
            endTime: endTime
        });

        // transfer token to be held in escrow
        nft.toERC721().safeTransferFrom(owner, address(this), tokenId, new bytes(0));
    }

    /**
     * @notice Delete auction and transfer token
     * @param nftAddress NFT address
     * @param auction Auction to delete
     * @param tokenId Token identifier
     */
    function _deleteAuctionAndTransferToken(NFTAddress nftAddress, Auction memory auction, uint256 tokenId) internal {
        address owner = auction.owner;

        _deleteAuction(nftAddress, tokenId, owner);

        // transfer token back to owner
        nftAddress.toERC721().safeTransferFrom(address(this), owner, tokenId, new bytes(0));
    }

    /**
     * @notice Delete auction
     * @param nftAddress NFT address
     * @param tokenId Token identifier
     * @param owner Auction owner
     */
    function _deleteAuction(NFTAddress nftAddress, uint256 tokenId, address owner) internal {
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
}

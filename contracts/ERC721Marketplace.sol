// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/token/ERC20/IERC20.sol";
import "openzeppelin/contracts/token/ERC721/IERC721.sol";
import "openzeppelin/contracts/token/ERC1155/IERC1155.sol";
import "openzeppelin/contracts/token/ERC721/utils/ERC721Holder.sol";
import "openzeppelin/contracts/access/Ownable.sol";
import "openzeppelin/contracts/security/ReentrancyGuard.sol";
import "../interfaces/IAddressRegistry.sol";
import "../interfaces/IPaymentTokenRegistry.sol";
import "./library/NFTTradable.sol";
import "./MarketplaceBase.sol";

contract ERC721Marketplace is ERC721Holder, Ownable, ReentrancyGuard, MarketplaceBase {
    using NFTTradable for NFTAddress;

    /// @notice NftAddress -> Token ID -> Listed item
    mapping(address => mapping(uint256 => Listing)) private _listings;
    /// @notice NftAddress -> Token ID -> Offer
    mapping(address => mapping(uint256 =>  Offer)) private _offers;

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
    /// @param owner Owner of NFT
    /// @param paymentToken Payment token
    /// @param price Sale price for token
    /// @param startingTime Scheduling for a future sale
    function createListing(
        NFTAddress nftAddress,
        uint256 tokenId,
        address payable owner,
        address paymentToken,
        uint256 price,
        uint256 startingTime
    ) external isNotListed(nftAddress.toAddress(), tokenId) {
        _validateTokenInterface(nftAddress);
        _validateNewListingTime(startingTime);
        _validatePaymentTokenIsEnabled(paymentToken);
        _validateOwnershipAndApproval(nftAddress, tokenId, owner);

        // transfer token to be held in escrow
        nftAddress.toERC721().safeTransferFrom(owner, address(this), tokenId, new bytes(0));

        _listings[nftAddress.toAddress()][tokenId] = Listing(
            owner,
            paymentToken,
            price,
            startingTime
        );

        emit ListingCreated(
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

        emit ListingUpdated(
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
        emit ListingCanceled(_msgSender(), nftAddress.toAddress(), tokenId);
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

        emit OfferCreated(
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
        emit OfferCanceled(_msgSender(), nftAddress.toAddress(), tokenId);
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
        // transfer payment tokens from offeror to owner of NFT
        // otherwise transfer payment tokens from escrow to fee recipient
        if (!offer.paymentTokensInEscrow) {
            _transferPayTokenAmount(offer.paymentToken, offer.offeror, payable(_msgSender()), offer.price - feeAmount);
        } else {
            _sendPayTokenAmount(offer.paymentToken, payable(_msgSender()), offer.price - feeAmount);
        }

        // Transfer NFT to offeror
        nftAddress.toERC721().safeTransferFrom(_msgSender(), offer.offeror, tokenId, new bytes(0));

        emit OfferAccepted(
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

    ////////////////////////////
    /// Internal and Private ///
    ////////////////////////////

    function _validateTokenInterface(NFTAddress nftAddress) internal {
        require(nftAddress.isERC721(), 'ERC721Marketplace: NFT is not ERC721');
    }

    function _validateOwnershipAndApproval(NFTAddress nftAddress, uint256 tokenId, address owner) internal {
        require(
            owner == _msgSender(),
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

        emit ListedItemSold(
            owner,
            _msgSender(),
            nftAddress.toAddress(),
            tokenId,
            price,
            paymentToken
        );

        delete (_listings[nftAddress.toAddress()][tokenId]);
    }
}

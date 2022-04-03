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
    mapping(address => mapping(uint256 => Listing)) internal _listings;

    modifier isListed(address nftAddress, uint256 tokenId) {
        Listing memory listing = _listings[nftAddress][tokenId];
        require(listing.paymentToken > address(0), "ERC721Marketplace: NFT is not listed");
        _;
    }

    modifier isNotListed(address nftAddress, uint256 tokenId) {
        Listing memory listing = _listings[nftAddress][tokenId];
        require(listing.paymentToken == address(0), "ERC721Marketplace: NFT is already listed");
        _;
    }

    constructor(address addressRegistry, address payable feeRecipient) MarketplaceBase(addressRegistry, feeRecipient) {}

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
        _validateOwnership(nftAddress, listedItem.owner);

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
        address listingOwner = _listings[nftAddress.toAddress()][tokenId].owner;
        _validateOwnership(nftAddress, listingOwner);

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
        require(
            block.timestamp >= _listings[nftAddress.toAddress()][tokenId].startingTime,
            "ERC721Marketplace: listing has not started yet"
        );

        _buyListedItem(nftAddress, tokenId);
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

    ////////////////////////////
    /// Internal and Private ///
    ////////////////////////////

    function _validateOwnershipAndApproval(NFTAddress nftAddress, uint256 tokenId, address owner) internal view {
        require(nftAddress.isERC721(), 'ERC721Marketplace: NFT is not ERC721');

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

    function _validateOwnership(NFTAddress nftAddress, address owner) internal view {
        require(nftAddress.isERC721(), 'ERC721Marketplace: NFT is not ERC721');
        require(owner == _msgSender(), "ERC721Marketplace: does not own the token");
    }

    function _buyListedItem(NFTAddress nftAddress, uint256 tokenId) private {
        Listing memory listedItem = _listings[nftAddress.toAddress()][tokenId];
        address owner = listedItem.owner;
        address paymentToken = listedItem.paymentToken;
        uint256 price = listedItem.price;

        // Calculate and transfer platform fee from buyer to platform
        uint256 feeAmount = _calculateAndTakeListingFee(listedItem);

        // TODO: Royalty

        // Transfer payment tokens from buyer to owner of NFT
        _transferPayTokenAmount(paymentToken, _msgSender(), owner, price - feeAmount);

        // Transfer NFT to buyer
        IERC721(nftAddress.toAddress()).safeTransferFrom(address(this), _msgSender(), tokenId);

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

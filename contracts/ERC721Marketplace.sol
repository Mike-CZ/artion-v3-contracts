// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/token/ERC20/IERC20.sol";
import "openzeppelin/contracts/token/ERC721/IERC721.sol";
import "openzeppelin/contracts/token/ERC1155/IERC1155.sol";
import "openzeppelin/contracts/token/ERC721/utils/ERC721Holder.sol";
import "openzeppelin/contracts/access/Ownable.sol";
import "openzeppelin/contracts/security/ReentrancyGuard.sol";
import "openzeppelin/contracts/utils/math/SafeMath.sol";
import "../interfaces/IAddressRegistry.sol";
import "../interfaces/IPaymentTokenRegistry.sol";
import "./library/NFTTradable.sol";
import "./MarketplaceBase.sol";

contract ERC721Marketplace is ERC721Holder, Ownable, ReentrancyGuard, MarketplaceBase {
    using NFTTradable for NFTAddress;
    using SafeMath for uint256;

    /// @notice Events for the contract
    event ItemListingCreated(
        address indexed owner,
        address indexed nft,
        uint256 tokenId,
        address paymentToken,
        uint256 price,
        uint256 startingTime
    );

    event ItemListingUpdated(
        address indexed owner,
        address indexed nft,
        uint256 tokenId,
        address newPaymentToken,
        uint256 newPrice
    );

    event ItemListingCanceled(
        address indexed owner,
        address indexed nft,
        uint256 tokenId
    );

    event ListedItemSold(
        address indexed seller,
        address indexed buyer,
        address indexed nft,
        uint256 tokenId,
        address paymentToken
    );

    /// @notice NftAddress -> Token ID -> Listed item
    mapping(address => mapping(uint256 => Listing)) private _listings;

    /// @notice Platform fee
    uint256 private _platformFee;

    /// @notice Platform fee recipient
    address payable private _platformFeeRecipient;

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

    constructor(address addressRegistry) MarketplaceBase(addressRegistry) {

    }

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
        address owner,
        address paymentToken,
        uint256 price,
        uint256 startingTime
    ) external isNotListed(nftAddress.toAddress(), tokenId) {
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

        emit ItemListingCreated(
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
        _validateOwnership(nftAddress, tokenId, listedItem.owner);

        listedItem.paymentToken = paymentToken;
        listedItem.price = newPrice;

        emit ItemListingUpdated(
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
        _validateOwnership(nftAddress, tokenId, listingOwner);

        delete (_listings[nftAddress.toAddress()][tokenId]);
        emit ItemListingCanceled(_msgSender(), nftAddress.toAddress(), tokenId);
    }

    /// @notice Method for buying listed NFT
    /// @param nftAddress NFT contract address
    /// @param tokenId TokenId
    function buyListedItem(NFTAddress nftAddress, uint256 tokenId, address paymentToken)
        external
        nonReentrant
        isListed(nftAddress.toAddress(), tokenId)
    {
        address listingOwner = _listings[nftAddress.toAddress()][tokenId].owner;
        _validateOwnership(nftAddress, tokenId, listingOwner);

        require(
            _listings[nftAddress.toAddress()][tokenId].paymentToken == paymentToken,
            "ERC721Marketplace: invalid payment token"
        );
        require(
            block.timestamp >= _listings[nftAddress.toAddress()][tokenId].startingTime,
            "ERC721Marketplace: listing has not started yet"
        );

        _buyListedItem(nftAddress, tokenId, paymentToken);
    }

    ////////////////////////////
    /// Setters and Getters ///
    ///////////////////////////

    function setPlatformFee(uint256 platformFee) external onlyOwner {
        _platformFee = platformFee;
    }

    function setPlatformFeeRecipient(address payable platformFeeRecipient) external onlyOwner {
        _platformFeeRecipient = platformFeeRecipient;
    }

    function updateAddressRegistry(address addressRegistry) external onlyOwner {
        _addressRegistry = IAddressRegistry(addressRegistry);
    }

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

    function _validateOwnershipAndApproval(NFTAddress nftAddress, uint256 tokenId, address owner) internal {
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

    function _validateOwnership(NFTAddress nftAddress, uint256 tokenId, address owner) internal {
        require(nftAddress.isERC721(), 'ERC721Marketplace: NFT is not ERC721');
        require(owner == _msgSender(), "ERC721Marketplace: does not own the token");
    }

    function _buyListedItem(NFTAddress nftAddress, uint256 tokenId, address paymentToken) private {
        address owner = nftAddress.toERC721().ownerOf(tokenId);
        Listing memory listedItem = _listings[nftAddress.toAddress()][tokenId];
        uint256 price = listedItem.price;
        uint256 feeAmount = price.mul(_platformFee).div(1e3);

        // Transfer platform fee from buyer to platform
        IERC20(paymentToken).transferFrom(
            _msgSender(),
            _platformFeeRecipient,
            feeAmount
        );

        // TODO: Royalty

        // Transfer payment tokens from buyer to owner of NFT
        IERC20(paymentToken).transferFrom(
            _msgSender(),
            owner,
            price.sub(feeAmount)
        );

        // Transfer NFT to buyer
        IERC721(nftAddress.toAddress()).safeTransferFrom(owner, _msgSender(), tokenId);

        emit ListedItemSold(
            owner,
            _msgSender(),
            nftAddress.toAddress(),
            tokenId,
            paymentToken
        );
        
        delete (_listings[nftAddress.toAddress()][tokenId]);
    }
}

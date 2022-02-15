// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../interfaces/IAddressRegistry.sol"
import "../interfaces/IPaymentTokenRegistry.sol"

contract Marketplace {
    /// @notice Structure for listed items
    struct Listing {
        uint256 quantity;
        address payToken;
        uint256 pricePerItem;
        uint256 startingTime;
    }

    /// @notice NftAddress -> Token ID -> Owner -> Listing item
    mapping(address => mapping(uint256 => mapping(address => Listing))) private _listings;

    IAddressRegistry private _addressRegistry;

    modifier isListed(address nftAddress, uint256 tokenId, address owner) {
        Listing memory listing = _listings[nftAddress][tokenId][owner];
        require(listing.quantity > 0, "Marketplace: NFT is not listed");
        _;
    }

    modifier isNotListed(address nftAddress, uint256 tokenId, address owner) {
        Listing memory listing = _listings[nftAddress][tokenId][owner];
        require(listing.quantity == 0, "Marketplace: NFT is already listed");
        _;
    }

    /// @notice Method for listing an NFT
    /// @param nftAddress Address of NFT contract
    /// @param tokenId Token ID of NFT
    /// @param quantity token amount to list (needed for ERC-1155 NFTs, set as 1 for ERC-721)
    /// @param payToken Paying token
    /// @param pricePerItem sale price for each item
    /// @param startingTime scheduling for a future sale
    function createListing(
        address nftAddress,
        uint256 tokenId,
        uint256 quantity,
        address payToken,
        uint256 pricePerItem,
        uint256 startingTime
    ) external notListed(nftAddress, tokenId, msgSender()) {
        if (IERC165(nftAddress).supportsInterface(INTERFACE_ID_ERC721)) {
            IERC721 nft = IERC721(nftAddress);

            require(nft.ownerOf(tokenId) == _msgSender(), "Marketplace: not owning item");
            require(nft.isApprovedForAll(_msgSender(), address(this)), "Marketplace: item not approved");

        } else if (IERC165(nftAddress).supportsInterface(INTERFACE_ID_ERC1155)) {
            IERC1155 nft = IERC1155(nftAddress);

            require(nft.balanceOf(_msgSender(), tokenId) >= quantity, "Marketplace: must hold enough nfts");
            require(nft.isApprovedForAll(_msgSender(), address(this)), "Marketplace: item is not approved");

        } else {
            revert("invalid nft address");
        }

        _validatePayToken(payToken);

        _listings[nftAddress][tokenId][_msgSender()] = Listing(
            quantity,
            payToken,
            pricePerItem,
            startingTime
        );

        emit ItemListed(
            _msgSender(),
            nftAddress,
            tokenId,
            quantity,
            payToken,
            pricePerItem,
            startingTime
        );
    }

    /// @notice Method for updating listed NFT
    /// @param nftAddress Address of NFT contract
    /// @param tokenId Token ID of NFT
    /// @param payToken payment token
    /// @param newPrice New sale price for each item
    function updateListing(
        address nftAddress,
        uint256 tokenId,
        address payToken,
        uint256 newPrice
    ) external nonReentrant isListed(nftAddress, tokenId, _msgSender()) {
        Listing listedItem = _listings[nftAddress][tokenId][_msgSender()];

        _validateOwnership(nftAddress, tokenId, _msgSender(), listedItem.quantity);
        _validatePayToken(payToken);

        listedItem.payToken = payToken;
        listedItem.pricePerItem = newPrice;

        emit ListedItemUpdated(
            _msgSender(),
            nftAddress,
            tokenId,
            payToken,
            newPrice
        );
    }

    /// @notice Method for canceling listed NFT
    function cancelListing(
        address nftAddress,
        uint256 tokenId
    ) external nonReentrant isListed(nftAddress, tokenId, _msgSender()) {
        Listing listedItem = _listings[nftAddress][tokenId][_msgSender()];

        _validateOwnership(nftAddress, tokenId, _msgSender(), listedItem.quantity);
        _cancelListing(nftAddress, tokenId, _msgSender());
    }

    ////////////////////////////
    /// Internal and Private ///
    ////////////////////////////

    function _validatePayToken(address payToken) internal {
        require(payToken == address(0) ||
            (_addressRegistry.tokenRegistry() != address(0) &&
            IPaymentTokenRegistry(_addressRegistry.tokenRegistry()).enabled(payToken)),
            "Marketplace: invalid pay token"
        );
    }

    function _validateOwnership(address nftAddress, uint256 tokenId, address owner, uint256 quantity) internal {
        if (IERC165(nftAddress).supportsInterface(INTERFACE_ID_ERC721)) {
            IERC721 nft = IERC721(nftAddress);
            require(nft.ownerOf(tokenId) == owner, "Marketplace: not owning item");
        } else if (IERC165(nftAddress).supportsInterface(INTERFACE_ID_ERC1155)) {
            IERC1155 nft = IERC1155(nftAddress);
            require(nft.balanceOf(owner, tokenId) >= quantity, "Marketplace: not owning item");
        } else {
            revert("Marketplace: invalid nft address");
        }
    }

    function _cancelListing(address nftAddress, uint256 tokenId, address owner) private {
        delete (_listings[nftAddress][tokenId][owner]);
        emit ListedItemCanceled(owner, nftAddress, tokenId);
    }
}

// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/utils/Context.sol";
import "openzeppelin/contracts/utils/Address.sol";
import "./ERC721Collection.sol";

/// @title Factory contract for deployment of ERC721 collections
contract ERC721CollectionFactory is Context {
    using Address for address payable;

    /// @notice Events of the contract
    event ERC721CollectionCreated(address creator, address nft);

    /// @notice Platform fee for deploying new NFT collection contract
    uint256 private _platformFee;

    /// @notice Platform fee recipient
    address payable private _platformFeeRecipient;

    /// @notice Contract constructor
    constructor(uint256 platformFee, address payable platformFeeRecipient) {
        _platformFee = platformFee;
        _platformFeeRecipient = platformFeeRecipient;
    }

    /// @notice Method for deploy new ERC721Collection contract
    /// @param name Name of NFT collection
    /// @param symbol Symbol of NFT collection
    /// @param mintFee Price of minting new NFT in collection
    /// @param mintFeeRecipient Recipient of mintFee value
    /// @param isPrivate If true, only owner of collection can mint new tokens
    /// @return nftCollectionAddress Address of newly created ERC721 collection
    function createERC721Collection(
        string memory name,
        string memory symbol,
        uint256 mintFee,
        address payable mintFeeRecipient,
        bool isPrivate
    ) external payable returns (address) {
        require(msg.value >= _platformFee, "ERC721CollectionFactory: Insufficient funds");

        _platformFeeRecipient.sendValue(msg.value);

        ERC721Collection nftCollection = new ERC721Collection(
            name,
            symbol,
            mintFee,
            mintFeeRecipient,
            isPrivate
        );

        nftCollection.transferOwnership(_msgSender());

        address nftCollectionAddress = address(nftCollection);

        emit ERC721CollectionCreated(_msgSender(), nftCollectionAddress);

        return nftCollectionAddress;
    }
}

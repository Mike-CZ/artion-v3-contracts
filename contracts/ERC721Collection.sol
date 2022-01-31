// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "openzeppelin/contracts/utils/math/SafeMath.sol";
import "openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

contract ERC721Collection is ERC721URIStorage, Ownable {
    using SafeMath for uint256;
    using Address for address payable;

    event Minted(uint256 tokenId, address beneficiary, string tokenUri, address minter);
    event UpdatedMintFee(uint256 mintFee);
    event UpdatedMintFeeRecipient(address payable mintFeeRecipient);

    uint256 private _latestTokenId;

    uint256 private _mintFee;

    address payable private _mintFeeRecipient;

    bool private _isPrivate;

    constructor(
        string memory name,
        string memory symbol,
        uint256 mintFee,
        address payable mintFeeRecipient,
        bool isPrivate
    ) ERC721(name, symbol) {
        _mintFee = mintFee;
        _mintFeeRecipient = mintFeeRecipient;
        _isPrivate = isPrivate;
    }

    /**
     * @notice Mints a NFT AND when minting to a contract checks if the beneficiary is a 721 compatible
     * @param beneficiary Recipient of the NFT
     * @param tokenUri URI for the token being minted
     * @return uint256 The token ID of the token that was minted
     */
    function mint(address beneficiary, string calldata tokenUri) external payable returns (uint256) {
        // only owner can mint tokens when collection is marked as private
        if (_isPrivate) {
            require(owner() == _msgSender(), "ERC721Collection: only owner can mint tokens");
        }

        // validate parameters
        require(msg.value >= _mintFee, "ERC721Collection: insufficient funds to mint");
        require(bytes(tokenUri).length > 0, "ERC721Collection: token URI for minting is empty");
        require(_msgSender() != address(0), "ERC721Collection: minter is zero address");

        // increment id of latest minted token
        _latestTokenId = _latestTokenId.add(1);
        uint256 tokenId = _latestTokenId;

        // mint token
        _safeMint(beneficiary, tokenId);
        _setTokenURI(tokenId, tokenUri);

        // TODO: Royalty settings

        // send fee to fee recipient
        _mintFeeRecipient.sendValue(msg.value);

        emit Minted(tokenId, beneficiary, tokenUri, _msgSender());

        return tokenId;
    }

    /**
    * @notice Method for updating mint fee
    * @param mintFee uint256 the mint fee to set
    */
    function updateMintFee(uint256 mintFee) external onlyOwner {
        _mintFee = mintFee;
        emit UpdatedMintFee(_mintFee);
    }

    /**
    * @notice Method for updating mint fee address
    * @param mintFeeRecipient address payable the address to sends the funds to
    */
    function updateMintFeeRecipient(address payable mintFeeRecipient) external onlyOwner {
        _mintFeeRecipient = mintFeeRecipient;
        emit UpdatedMintFeeRecipient(_mintFeeRecipient);
    }
}
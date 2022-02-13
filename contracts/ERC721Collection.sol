// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "openzeppelin/contracts/utils/math/SafeMath.sol";
import "openzeppelin/contracts/utils/Address.sol";
import "./extensions/ERC2981Settable.sol";
import "./library/ERC2981.sol";
import "openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "openzeppelin/contracts/token/ERC721/ERC721.sol";

contract ERC721Collection is Ownable, ERC2981Settable, ERC721URIStorage {
    using SafeMath for uint256;
    using Address for address payable;

    event Minted(uint256 tokenId, address tokenRecipient, string tokenUri, address minter);
    event Burned(uint256 tokenId, address caller);
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
        bool privateFlag
    ) ERC721(name, symbol) {
        _mintFee = mintFee;
        _mintFeeRecipient = mintFeeRecipient;
        _isPrivate = privateFlag;
    }

    /**
     * @notice Validates user is authorized for token manipulation
     * @param tokenId The token identifier
     */
    modifier tokenAuth(uint256 tokenId) {
        address owner = ownerOf(tokenId);
        address operator = _msgSender();
        require(
            owner == operator || getApproved(tokenId) == operator || isApprovedForAll(owner, operator),
            "ERC721Collection: only owner or approved can manipulate with token"
        );
        _;
    }

    /**
     * @notice Mint new token
     * @param tokenRecipient Recipient of the token
     * @param tokenUri URI for the token being minted
     * @return uint256 The token ID of the token that was minted
     * @param royaltyRecipient The receiver of royalty
     * @param royaltyPercent The royalty percentage (using 2 decimals - 10000 = 100%, 0 = 0%)
     */
    function mint(
        address tokenRecipient,
        string calldata tokenUri,
        address royaltyRecipient,
        uint16 royaltyPercent
    ) external payable returns (uint256) {
        // only owner can mint tokens when collection is marked as private
        if (_isPrivate) {
            require(owner() == _msgSender(), "ERC721Collection: only owner can mint tokens");
        }

        // validate parameters
        require(msg.value >= _mintFee, "ERC721Collection: insufficient funds to mint");
        require(bytes(tokenUri).length > 0, "ERC721Collection: token URI for minting is empty");

        // increment id of latest minted token
        _latestTokenId = _latestTokenId.add(1);
        uint256 tokenId = _latestTokenId;

        // mint token
        _safeMint(tokenRecipient, tokenId);
        _setTokenURI(tokenId, tokenUri);

        // set token royalty
        if (royaltyPercent > 0) {
            _setTokenRoyalty(tokenId, royaltyRecipient, royaltyPercent);
        }

        // send fee
        _mintFeeRecipient.sendValue(msg.value);

        emit Minted(tokenId, tokenRecipient, tokenUri, _msgSender());

        return tokenId;
    }

    /**
     @notice Burns given token
     @param tokenId The token identifier
     */
    function burn(uint256 tokenId) external tokenAuth(tokenId) {
        _burn(tokenId);
        // could not use OpenZeppelin ERC721Royalty extension because of "custom" ERC2981 implementation
        _resetTokenRoyalty(tokenId);
        emit Burned(tokenId, _msgSender());
    }

    /**
     * @dev See {IERC2981RoyaltySetter-setDefaultRoyalty}.
     */
    function setDefaultRoyalty(address recipient, uint96 royaltyPercent) public override onlyOwner {
        require(! _isDefaultRoyaltySet(), "ERC721Collection: default royalty already set");
        super.setDefaultRoyalty(recipient, royaltyPercent);
    }

    /**
     * @dev See {IERC2981RoyaltySetter-setTokenRoyalty}.
     */
    function setTokenRoyalty(
        uint256 tokenId,
        address recipient,
        uint96 royaltyPercent
    ) public override tokenAuth(tokenId) {
        require(! _isTokenRoyaltySet(tokenId), "ERC721Collection: token royalty already set");
        super.setTokenRoyalty(tokenId, recipient, royaltyPercent);
    }

    /**
     * @dev See {IERC2981RoyaltySetter-updateDefaultRoyaltyRecipient}.
     */
    function updateDefaultRoyaltyRecipient(address recipient) public override onlyOwner {
        super.updateDefaultRoyaltyRecipient(recipient);
    }

    /**
     * @dev See {IERC2981RoyaltySetter-updateTokenRoyaltyRecipient}.
     */
    function updateTokenRoyaltyRecipient(uint256 tokenId, address recipient) public override tokenAuth(tokenId) {
        super.updateTokenRoyaltyRecipient(tokenId, recipient);
    }

    /**
    * @notice Update mint fee
    * @param mintFee uint256 the mint fee to set
    */
    function updateMintFee(uint256 mintFee) external onlyOwner {
        _mintFee = mintFee;
        emit UpdatedMintFee(_mintFee);
    }

    /**
    * @notice Update mint fee address
    * @param mintFeeRecipient address payable the address to sends the funds to
    */
    function updateMintFeeRecipient(address payable mintFeeRecipient) external onlyOwner {
        _mintFeeRecipient = mintFeeRecipient;
        emit UpdatedMintFeeRecipient(_mintFeeRecipient);
    }

    /**
     * @notice Get mint fee
     * @return uint256
     */
    function getMintFee() external view returns (uint256) {
        return _mintFee;
    }

    /**
     * @notice Get mint fee recipient
     * @return address
     */
    function getMintFeeRecipient() external view returns (address) {
        return _mintFeeRecipient;
    }

    /**
     * @notice Get isPrivate flag
     * @return bool
     */
    function isPrivate() external view returns (bool) {
        return _isPrivate;
    }

    /**
     * @dev See {IERC165-supportsInterface}.
     */
    function supportsInterface(bytes4 interfaceId) public view override(ERC721, ERC2981Settable) returns (bool) {
        return ERC2981Settable.supportsInterface(interfaceId) || super.supportsInterface(interfaceId);
    }
}
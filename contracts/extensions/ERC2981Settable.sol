// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../../interfaces/IERC2981Settable.sol";
import "../library/ERC2981.sol";

/**
* @dev See {IERC2981Settable}.
*/
abstract contract ERC2981Settable is ERC2981, IERC2981Settable {
    /**
     * @dev See {IERC2981Settable-setDefaultRoyalty}.
     */
    function setDefaultRoyalty(address recipient, uint96 royaltyPercent) public virtual {
        require(! _isDefaultRoyaltySet(), "ERC2981Settable: default royalty already set");
        _setDefaultRoyalty(recipient, royaltyPercent);
    }

    /**
     * @dev See {IERC2981Settable-setTokenRoyalty}.
     */
    function setTokenRoyalty(uint256 tokenId, address recipient, uint96 royaltyPercent) public virtual {
        require(! _isTokenRoyaltySet(tokenId), "ERC2981Settable: token royalty already set");
        _setTokenRoyalty(tokenId, recipient, royaltyPercent);
    }

    /**
     * @dev See {IERC2981Settable-updateDefaultRoyaltyRecipient}.
     */
    function updateDefaultRoyaltyRecipient(address recipient) public virtual {
        require(_isDefaultRoyaltySet(), "ERC2981Settable: default royalty is not set");
        _setDefaultRoyalty(recipient, _defaultRoyaltyInfo.royaltyFraction);
    }

    /**
     * @dev See {IERC2981Settable-updateTokenRoyaltyRecipient}.
     */
    function updateTokenRoyaltyRecipient(uint256 tokenId, address recipient) public virtual {
        require(_isTokenRoyaltySet(tokenId), "ERC2981Settable: token royalty is not set");
        _setTokenRoyalty(tokenId, recipient, _tokenRoyaltyInfo[tokenId].royaltyFraction);
    }

     /**
     * @dev See {IERC165-supportsInterface}.
     */
    function supportsInterface(bytes4 interfaceId) public view virtual override(IERC165, ERC2981) returns (bool) {
        return interfaceId == type(IERC2981Settable).interfaceId || super.supportsInterface(interfaceId);
    }

    /**
    * @notice Get receiver of token royalty
    * @param tokenId The token identifier
    * @return address
    */
    function _recipientOfTokenRoyalty(uint256 tokenId) internal view returns (address) {
        return _tokenRoyaltyInfo[tokenId].receiver;
    }

    /**
    * @notice Get recipient of default royalty
    * @return address
    */
    function _recipientOfDefaultRoyalty() internal view returns (address) {
        return _defaultRoyaltyInfo.receiver;
    }

    /**
    * @notice Get royalty fraction of a token
    * @param tokenId The token identifier
    * @return uint96
    */
    function _royaltyFractionOfToken(uint256 tokenId) internal view returns (uint96) {
        return _tokenRoyaltyInfo[tokenId].royaltyFraction;
    }

    /**
    * @notice Get default royalty fraction
    * @return uint96
    */
    function _royaltyFractionOfDefault() internal view returns (uint96) {
        return _defaultRoyaltyInfo.royaltyFraction;
    }

    /**
    * @notice Check token royalty is set
    * @param tokenId The token identifier
    * @return bool
    */
    function _isTokenRoyaltySet(uint256 tokenId) internal view returns (bool) {
        return _recipientOfTokenRoyalty(tokenId) != address(0);
    }

    /**
    * @notice Check default royalty is set
    * @return bool
    */
    function _isDefaultRoyaltySet() internal view returns (bool) {
        return _recipientOfDefaultRoyalty() != address(0);
    }
}
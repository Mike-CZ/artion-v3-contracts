// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../../interfaces/IERC2981Settable.sol";
import "../library/ERC2981.sol";
import "openzeppelin/contracts/token/ERC721/ERC721.sol";

abstract contract ERC2981SettableRoyalty is ERC2981, IERC2981Settable, ERC721 {
    /**
     * @dev See {IERC165-supportsInterface}.
     */
    function supportsInterface(bytes4 interfaceId) public view virtual override(ERC721, ERC2981) returns (bool) {
        return super.supportsInterface(interfaceId);
    }

    /**
     * @dev See {IERC2981RoyaltySetter-setDefaultRoyalty}.
     */
    function setDefaultRoyalty(address recipient, uint16 royaltyPercent) public virtual {
        require(! _isDefaultRoyaltySet(), "ERC2981Settable: default royalty already set");
        _setDefaultRoyalty(recipient, royaltyPercent);
    }

    /**
     * @dev See {IERC2981RoyaltySetter-setTokenRoyalty}.
     */
    function setTokenRoyalty(uint256 tokenId, address recipient, uint16 royaltyPercent) public virtual {
        require(! _isTokenRoyaltySet(tokenId), "ERC2981Settable: token royalty already set");
        _setTokenRoyalty(tokenId, recipient, royaltyPercent);
    }

    /**
     * @dev See {IERC2981RoyaltySetter-updateDefaultRoyaltyRecipient}.
     */
    function updateDefaultRoyaltyRecipient(address recipient) public virtual {
        require(_isDefaultRoyaltySet(), "ERC2981Settable: default royalty is not set");
        _setDefaultRoyalty(recipient, _defaultRoyaltyInfo.royaltyFraction);
    }

    /**
     * @dev See {IERC2981RoyaltySetter-updateTokenRoyaltyRecipient}.
     */
    function updateTokenRoyaltyRecipient(uint256 tokenId, address recipient) public virtual {
        require(_isTokenRoyaltySet(tokenId), "ERC2981Settable: token royalty is not set");
        _setTokenRoyalty(tokenId, recipient, _tokenRoyaltyInfo[tokenId].royaltyFraction);
    }

    /**
    * @notice Check token royalty is set
    * @param tokenId The token identifier
    * @return bool
    */
    function _isTokenRoyaltySet(uint256 tokenId) internal view returns (bool) {
        return _tokenRoyaltyInfo[tokenId].receiver != address(0);
    }

    /**
    * @notice Check default royalty is set
    * @return bool
    */
    function _isDefaultRoyaltySet() internal view returns (bool) {
        return _defaultRoyaltyInfo.receiver != address(0);
    }

    /**
     * @dev See {ERC721-_burn}. This override additionally clears the royalty information for the token.
     */
    function _burn(uint256 tokenId) internal virtual override {
        super._burn(tokenId);
        _resetTokenRoyalty(tokenId);
    }
}
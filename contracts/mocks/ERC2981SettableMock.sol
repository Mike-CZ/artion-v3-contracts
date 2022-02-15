// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../extensions/ERC2981Settable.sol";

contract ERC2981SettableMock is ERC2981Settable {
    function recipientOfTokenRoyalty(uint256 tokenId) public view returns (address) {
        return _getRecipientOfTokenRoyalty(tokenId);
    }

    function recipientOfDefaultRoyalty() public view returns (address) {
        return _getRecipientOfDefaultRoyalty();
    }

    function royaltyFractionOfToken(uint256 tokenId) public view returns (uint96) {
        return _getRoyaltyFractionOfToken(tokenId);
    }

    function royaltyFractionOfDefault() public view returns (uint96) {
        return _getRoyaltyFractionOfDefault();
    }
}
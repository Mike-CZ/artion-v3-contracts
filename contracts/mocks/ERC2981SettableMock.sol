// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../extensions/ERC2981Settable.sol";

contract ERC2981SettableMock is ERC2981Settable {
    function receiverOfTokenRoyalty(uint256 tokenId) public view returns (address) {
        return _receiverOfTokenRoyalty(tokenId);
    }

    function receiverOfDefaultRoyalty() public view returns (address) {
        return _receiverOfDefaultRoyalty();
    }

    function royaltyFractionOfToken(uint256 tokenId) public view returns (uint96) {
        return _royaltyFractionOfToken(tokenId);
    }

    function royaltyFractionOfDefault() public view returns (uint96) {
        return _royaltyFractionOfDefault();
    }
}
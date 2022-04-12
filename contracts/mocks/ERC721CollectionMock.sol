// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../ERC721Collection.sol";
import "./ERC2981SettableMock.sol";

contract ERC721CollectionMock is ERC721Collection {
    constructor(
        string memory name,
        string memory symbol,
        uint256 mintFee,
        address payable mintFeeRecipient,
        bool privateFlag
    ) ERC721Collection(name, symbol, mintFee, mintFeeRecipient, privateFlag) {}

    function recipientOfTokenRoyalty(uint256 tokenId) public view returns (address) {
        return _getRecipientOfTokenRoyalty(tokenId);
    }

    function recipientOfDefaultRoyalty() public view returns (address) {
        return _getRecipientOfDefaultRoyalty();
    }

    function getLatestTokenId() public view returns (uint256) {
        return _getLatestTokenId();
    }

    function mintAndGetTokenId(
        address tokenRecipient,
        string memory tokenUri,
        address royaltyRecipient,
        uint16 royaltyPercent
    ) public returns (uint256) {
        uint256 tokenId =  _mintAndGetTokenId(tokenRecipient, tokenUri);

        if (royaltyRecipient != address(0) && royaltyPercent > 0) {
            _setTokenRoyalty(tokenId, royaltyRecipient, royaltyPercent);
        }

        return tokenId;
    }
}

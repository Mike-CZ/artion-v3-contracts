// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/mocks/ERC1155Mock.sol";

contract ERC1155CollectionMock is ERC1155Mock('some-uri/{id}') {
    uint256 private _latestTokenId;

    function mintAndGetTokenId(address tokenRecipient, uint256 amount) public returns (uint256) {
        _latestTokenId++;
        _mint(tokenRecipient, _latestTokenId, amount, new bytes(0));
        return _latestTokenId;
    }
}
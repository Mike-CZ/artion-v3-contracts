pragma solidity ^0.8.0;

import "openzeppelin/contracts/interfaces/IERC2981.sol";

/**
* @title ERC-2981 royalty setter
* @dev Custom implementation, ERC-2981 does not include royalty settings.
*/
interface IERC2981Settable is IERC2981 {
    /**
    * @notice Set default royalty for whole collection
    * @param recipient The receiver of royalty
    * @param royaltyPercent The royalty percentage (using 2 decimals - 10000 = 100%, 0 = 0%)
    */
    function setDefaultRoyalty(address recipient, uint16 royaltyPercent) external;

    /**
    * @notice Set royalty for a token
    * @param tokenId The token identifier
    * @param recipient The receiver of royalty
    * @param royaltyPercent The royalty percentage (using 2 decimals - 10000 = 100%, 0 = 0%)
    */
    function setTokenRoyalty(uint256 tokenId, address recipient, uint16 royaltyPercent) external;

    /**
    * @notice Update royalty recipient for whole collection
    * @param recipient The receiver of royalty
    */
    function updateDefaultRoyaltyRecipient(address recipient) external;

    /**
    * @notice Update royalty recipient for a token
    * @param tokenId The token identifier
    * @param recipient The receiver of royalty
    */
    function updateTokenRoyaltyRecipient(uint256 tokenId, address recipient) external;
}

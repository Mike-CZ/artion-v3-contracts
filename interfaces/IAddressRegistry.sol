// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

/**
* @title Address registry
* @dev Contains addresses of other contracts
*/
interface IAddressRegistry {
    /**
    * @notice Get ERC721 marketplace address
    * @return address
    */
    function getERC721MarketplaceAddress() external view returns (address);

    /**
    * @notice Get payment token registry address
    * @return address
    */
    function getPaymentTokenRegistryAddress() external view returns (address);

    /**
    * @notice Get royalty registry address
    * @return address
    */
    function getRoyaltyRegistryAddress() external view returns (address);
}

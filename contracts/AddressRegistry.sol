// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "../interfaces/IAddressRegistry.sol";
import "openzeppelin/contracts/access/Ownable.sol";

/**
 * @dev See {IAddressRegistry}.
 */
contract AddressRegistry is Ownable, IAddressRegistry {
    /**
     * @notice Payment token registry address
     */
    address private _paymentTokenRegistryAddress;

    /**
     * @notice Royalty registry address
     */
    address private _royaltyRegistryAddress;

    /**
     * @dev See {IAddressRegistry-getPaymentTokenRegistryAddress}.
     */
    function getPaymentTokenRegistryAddress() public view returns (address) {
        return _paymentTokenRegistryAddress;
    }

    /**
     * @dev See {IAddressRegistry-updatePaymentTokenRegistryAddress}.
     */
    function updatePaymentTokenRegistryAddress(address paymentTokenRegistryAddress) public onlyOwner {
        _paymentTokenRegistryAddress = paymentTokenRegistryAddress;
    }

    /**
     * @dev See {IAddressRegistry-getRoyaltyRegistryAddress}.
     */
    function getRoyaltyRegistryAddress() public view returns (address) {
        return _royaltyRegistryAddress;
    }

    /**
     * @dev See {IAddressRegistry-updateRoyaltyRegistryAddress}.
     */
    function updateRoyaltyRegistryAddress(address royaltyRegistryAddress) public onlyOwner {
        _royaltyRegistryAddress = royaltyRegistryAddress;
    }
}

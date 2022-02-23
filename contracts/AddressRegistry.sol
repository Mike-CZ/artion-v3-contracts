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
     * @dev See {IAddressRegistry-getPaymentTokenRegistryAddress}.
     */
    function getPaymentTokenRegistryAddress() public view returns (address) {
        return _paymentTokenRegistryAddress;
    }

    /**
     * @dev See {IAddressRegistry-updatePaymentTokenRegistryAddress}.
     */
    function updatePaymentTokenRegistryAddress(address paymentTokenRegistryAddress) onlyOwner public {
        _paymentTokenRegistryAddress = paymentTokenRegistryAddress;
    }
}

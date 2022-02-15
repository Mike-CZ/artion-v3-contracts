// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/IAddressRegistry.sol";

contract AddressRegistry is IAddressRegistry, Ownable {
    /// @notice Marketplace contract
    address private _marketplace;

    /// @notice PaymentTokenRegistry contract
    address private _paymentTokenRegistry;

    /// @notice RoyaltyRegistry contract
    address private _royaltyRegistry;

    ////////////////
    /// Setters ///
    //////////////

    /**
     @notice Update Marketplace contract
     @dev Only admin
     */
    function updateMarketplace(address marketplace) external onlyOwner {
        _marketplace = marketplace;
    }

    /**
     @notice Update token registry contract
     @dev Only admin
     */
    function updatePaymentTokenRegistry(address paymentTokenRegistry) external onlyOwner {
        _paymentTokenRegistry = paymentTokenRegistry;
    }

    /**
     @notice Update royalty registry contract
     @dev Only admin
     */
    function updateRoyaltyRegistry(address royaltyRegistry) external onlyOwner {
        _royaltyRegistry = royaltyRegistry;
    }

    ////////////////
    /// Getters ///
    //////////////

    function marketplace() external view returns (address) {
        return _marketplace;
    }

    function paymentTokenRegistry() external view returns (address) {
        return _paymentTokenRegistry;
    }

    function royaltyRegistry() external view returns (address) {
        return _royaltyRegistry;
    }
}

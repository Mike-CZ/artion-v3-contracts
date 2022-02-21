// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/IAddressRegistry.sol";

contract AddressRegistry is IAddressRegistry, Ownable {
    /// @notice ERC721 marketplace contract
    address private _ERC721Marketplace;

    /// @notice PaymentTokenRegistry contract
    address private _paymentTokenRegistry;

    /// @notice RoyaltyRegistry contract
    address private _royaltyRegistry;

    ////////////////
    /// Setters ///
    //////////////

    /**
     @notice Update ERC721 Marketplace contract
     @dev Only admin
     */
    function updateERC721Marketplace(address newERC721Marketplace) external onlyOwner {
        _ERC721Marketplace = newERC721Marketplace;
    }

    /**
     @notice Update token registry contract
     @dev Only admin
     */
    function updatePaymentTokenRegistry(address newPaymentTokenRegistry) external onlyOwner {
        _paymentTokenRegistry = newPaymentTokenRegistry;
    }

    /**
     @notice Update royalty registry contract
     @dev Only admin
     */
    function updateRoyaltyRegistry(address newRoyaltyRegistry) external onlyOwner {
        _royaltyRegistry = newRoyaltyRegistry;
    }

    ////////////////
    /// Getters ///
    //////////////

    function getERC721MarketplaceAddress() external view returns (address) {
        return _ERC721Marketplace;
    }

    function getPaymentTokenRegistryAddress() external view returns (address) {
        return _paymentTokenRegistry;
    }

    function getRoyaltyRegistryAddress() external view returns (address) {
        return _royaltyRegistry;
    }
}

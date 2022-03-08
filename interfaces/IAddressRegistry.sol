pragma solidity ^0.8.0;

import "openzeppelin/contracts/interfaces/IERC2981.sol";

/**
* @title Address registry
* @dev Contains addresses of other contracts
*/
interface IAddressRegistry {
    /**
    * @notice Get payment token registry address
    * @return address
    */
    function getPaymentTokenRegistryAddress() external view returns (address);

    /**
    * @notice Update payment token registry address
    * @param paymentTokenRegistryAddress Payment token registry address
    */
    function updatePaymentTokenRegistryAddress(address paymentTokenRegistryAddress) external;

    /**
    * @notice Get royalty registry address
    * @return address
    */
    function getRoyaltyRegistryAddress() external view returns (address);

    /**
    * @notice Update royalty registry address
    * @param royaltyRegistryAddress Royalty registry address
    */
    function updateRoyaltyRegistryAddress(address royaltyRegistryAddress) external;
}

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
}

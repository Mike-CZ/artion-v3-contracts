// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/interfaces/IERC2981.sol";

/**
* @title Address registry
* @dev Contains addresses of other contracts
*/
interface IPaymentTokenRegistry {
    /**
    * @notice Method for adding payment token
    * @param token ERC20 token address
    */
    function add(address token) external;

    /**
    * @notice Method for removing payment token
    * @param token ERC20 token address
    */
    function remove(address token) external;

    /**
    * @notice Check token is enabled
    * @param token ERC20 token address
    * @return bool
    */
    function isEnabled(address token) external view returns (bool);
}

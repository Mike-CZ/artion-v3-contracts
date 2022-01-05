// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
* @notice Payment token registry module which stores available
* payment tokens for artion.
*/
contract PaymentTokenRegistry is Ownable {
    event PaymentTokenAdded(address token);
    event PaymentTokenRemoved(address token);

    /**
    * @notice ERC20 Address -> Bool
    */
    mapping(address => bool) public enabled;

    /**
    * @notice Method for adding payment token
    * @dev Only admin
    * @param _token ERC20 token address
    */
    function add(address _token) external onlyOwner {
        require(! enabled[_token], "PaymentTokenRegistry: payment token already added");
        enabled[_token] = true;
        emit PaymentTokenAdded(_token);
    }

    /**
    * @notice Method for removing payment token
    * @dev Only admin
    * @param _token ERC20 token address
    */
    function remove(address _token) external onlyOwner {
        require(enabled[_token], "PaymentTokenRegistry: payment token does not exist");
        enabled[_token] = false;
        emit PaymentTokenRemoved(_token);
    }
}
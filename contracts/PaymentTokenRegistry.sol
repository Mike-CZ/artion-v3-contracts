// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";

/**
* @title Payment token registry
* @notice Module which stores available payment tokens for artion.
*/
contract PaymentTokenRegistry is Ownable {
    event PaymentTokenAdded(address token);
    event PaymentTokenRemoved(address token);

    /**
    * @notice ERC20 Address -> Bool
    */
    mapping(address => bool) private _enabled;

    /**
    * @notice Method for adding payment token
    * @param token ERC20 token address
    */
    function add(address token) external onlyOwner {
        require(! _enabled[token], "PaymentTokenRegistry: payment token already added");
        _enabled[token] = true;
        emit PaymentTokenAdded(token);
    }

    /**
    * @notice Method for removing payment token
    * @param token ERC20 token address
    */
    function remove(address token) external onlyOwner {
        require(_enabled[token], "PaymentTokenRegistry: payment token does not exist");
        _enabled[token] = false;
        emit PaymentTokenRemoved(token);
    }

    /**
    * @notice Check token is enabled
    * @param token ERC20 token address
    * @return bool
    */
    function isEnabled(address token) external view returns (bool) {
        return _enabled[token];
    }
}
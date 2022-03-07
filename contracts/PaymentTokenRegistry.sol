// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/IPaymentTokenRegistry.sol";

/**
* @title Payment token registry
* @notice Module which stores available payment tokens for artion.
*/
contract PaymentTokenRegistry is Ownable, IPaymentTokenRegistry {
    event PaymentTokenAdded(address token);
    event PaymentTokenRemoved(address token);

    /**
    * @notice ERC20 Address -> Bool
    */
    mapping(address => bool) private _enabled;

    /**
     * @dev See {IPaymentTokenRegistry-add}.
     */
    function add(address token) public onlyOwner {
        require(! _enabled[token], "PaymentTokenRegistry: payment token already added");
        _enabled[token] = true;
        emit PaymentTokenAdded(token);
    }

    /**
     * @dev See {IPaymentTokenRegistry-remove}.
     */
    function remove(address token) public onlyOwner {
        require(_enabled[token], "PaymentTokenRegistry: payment token does not exist");
        _enabled[token] = false;
        emit PaymentTokenRemoved(token);
    }

    /**
     * @dev See {IPaymentTokenRegistry-isEnabled}.
     */
    function isEnabled(address token) public view returns (bool) {
        return _enabled[token];
    }
}

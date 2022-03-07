// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/IPaymentTokenRegistry.sol";
import "../interfaces/IRoyaltyRegistry.sol";

/**
* @dev see {IRoyaltyRegistry}
*/
contract RoyaltyRegistry is Ownable, IRoyaltyRegistry {

}
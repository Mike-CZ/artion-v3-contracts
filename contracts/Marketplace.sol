// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "openzeppelin/contracts/access/Ownable.sol";
import "openzeppelin/contracts/utils/math/SafeMath.sol";
import "openzeppelin/contracts/interfaces/IERC2981.sol";

contract Marketplace is Ownable {
    using SafeMath for uint256;

    function test() external view returns (bytes4)  {
        return type(IERC2981).interfaceId;
    }
}
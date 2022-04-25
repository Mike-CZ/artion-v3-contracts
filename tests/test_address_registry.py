import pytest
from brownie import reverts, Wei, ERC721CollectionMock, accounts
from brownie.test import given, strategy
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount


@given(address=strategy('address'))
def test_update_payment_token_registry_address(
        address_registry: ProjectContract,
        owner: LocalAccount,
        address: LocalAccount
) -> None:
    """Test updating payment token registry address"""
    address_registry.updatePaymentTokenRegistryAddress(address, {'from': owner})
    assert address_registry.getPaymentTokenRegistryAddress() == address


@given(address=strategy('address'))
def test_update_payment_token_registry_address_unauthorized(
        address_registry: ProjectContract,
        user: LocalAccount,
        address: LocalAccount
) -> None:
    """Test updating payment token registry address - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        address_registry.updatePaymentTokenRegistryAddress(address, {'from': user})


@given(address=strategy('address'))
def test_update_royalty_registry_address(
        address_registry: ProjectContract,
        owner: LocalAccount,
        address: LocalAccount
) -> None:
    """Test updating royalty registry address"""
    address_registry.updateRoyaltyRegistryAddress(address, {'from': owner})
    assert address_registry.getRoyaltyRegistryAddress() == address


@given(address=strategy('address'))
def test_update_royalty_registry_address_unauthorized(
        address_registry: ProjectContract,
        user: LocalAccount,
        address: LocalAccount
) -> None:
    """Test updating royalty registry address - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        address_registry.updateRoyaltyRegistryAddress(address, {'from': user})

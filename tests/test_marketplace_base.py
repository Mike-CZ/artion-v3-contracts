import pytest
from brownie import reverts
from brownie.test import given, strategy


@pytest.fixture(scope="module")
def marketplace_base_mock(address_registry, owner):
    return MarketplaceBaseMock.deploy(address_registry, owner, {'from': owner})


@given(address=strategy('address'))
def test_update_address_registry_address(erc1155_marketplace_mock, address, owner):
    """Test update address registry"""
    erc1155_marketplace_mock.updateAddressRegistryAddress(address, {'from': owner})
    assert erc1155_marketplace_mock.getAddressRegistryAddress() == address


@given(address=strategy('address'))
def test_update_address_registry_address_unauthorized(erc1155_marketplace_mock, address, user):
    """Test update address registry - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        erc1155_marketplace_mock.updateAddressRegistryAddress(address, {'from': user})


def test_update_min_bid_increment_amount(erc1155_marketplace_mock, owner):
    """Test update min bid increment amount"""
    amount = 5
    erc1155_marketplace_mock.updateMinBidIncrementAmount(amount, {'from': owner})
    assert erc1155_marketplace_mock.getMinBidIncrementAmount() == amount


def test_update_address_min_bid_increment_amount_unauthorized(erc1155_marketplace_mock, user):
    """Test update min bid increment amount - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        erc1155_marketplace_mock.updateMinBidIncrementAmount(5, {'from': user})

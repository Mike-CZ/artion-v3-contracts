import pytest
from brownie import reverts
from brownie.test import given, strategy


@pytest.fixture(scope="module")
def marketplace_base_mock(address_registry, owner):
    return MarketplaceBaseMock.deploy(address_registry, {'from': owner})


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

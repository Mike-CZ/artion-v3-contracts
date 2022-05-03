import pytest
from brownie import reverts, MarketplaceBaseMock
from brownie.test import given, strategy
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable


@pytest.fixture(scope="module")
def marketplace_base_mock(address_registry: ProjectContract, owner: LocalAccount) -> ProjectContract:
    contract = MarketplaceBaseMock.deploy({'from': owner})
    contract.initialize(address_registry, 25, 25, 25, owner, False)
    return contract


@given(address=strategy('address'))
def test_update_address_registry_address(
        marketplace_base_mock: ProjectContract,
        address: LocalAccount,
        owner: LocalAccount
) -> None:
    """Test update address registry"""
    marketplace_base_mock.updateAddressRegistryAddress(address, {'from': owner})
    assert marketplace_base_mock.getAddressRegistryAddress() == address


@given(address=strategy('address'))
def test_update_address_registry_address_unauthorized(
        marketplace_base_mock: ProjectContract,
        address: LocalAccount,
        user: LocalAccount
) -> None:
    """Test update address registry - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        marketplace_base_mock.updateAddressRegistryAddress(address, {'from': user})


def test_update_min_bid_increment_amount(marketplace_base_mock: ProjectContract, owner: LocalAccount) -> None:
    """Test update min bid increment amount"""
    amount = 5
    marketplace_base_mock.updateMinBidIncrementAmount(amount, {'from': owner})
    assert marketplace_base_mock.getMinBidIncrementAmount() == amount


def test_update_address_min_bid_increment_amount_unauthorized(
        marketplace_base_mock: ProjectContract,
        user: LocalAccount
) -> None:
    """Test update min bid increment amount - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        marketplace_base_mock.updateMinBidIncrementAmount(5, {'from': user})


def test_update_auction_fee(marketplace_base_mock: ProjectContract, owner: LocalAccount) -> None:
    """Test update auction fee"""
    amount = 5
    marketplace_base_mock.updateAuctionFee(amount, {'from': owner})
    assert marketplace_base_mock.getAuctionFee() == amount


def test_update_auction_fee_unauthorized(marketplace_base_mock: ProjectContract, user: LocalAccount) -> None:
    """Test update auction fee - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        marketplace_base_mock.updateAuctionFee(5, {'from': user})


def test_update_listing_fee(marketplace_base_mock: ProjectContract, owner: LocalAccount) -> None:
    """Test update listing fee"""
    amount = 5
    marketplace_base_mock.updateListingFee(amount, {'from': owner})
    assert marketplace_base_mock.getListingFee() == amount


def test_update_listing_fee_unauthorized(marketplace_base_mock: ProjectContract, user: LocalAccount) -> None:
    """Test update listing fee - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        marketplace_base_mock.updateListingFee(5, {'from': user})


def test_update_offer_fee(marketplace_base_mock: ProjectContract, owner: LocalAccount) -> None:
    """Test update offer fee"""
    amount = 5
    marketplace_base_mock.updateOfferFee(amount, {'from': owner})
    assert marketplace_base_mock.getOfferFee() == amount


def test_update_offer_fee_unauthorized(marketplace_base_mock: ProjectContract, user: LocalAccount) -> None:
    """Test update offer fee - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        marketplace_base_mock.updateOfferFee(5, {'from': user})


@given(address=strategy('address'))
def test_update_fee_recipient(
        marketplace_base_mock: ProjectContract,
        address: LocalAccount,
        owner: LocalAccount
) -> None:
    """Test update fee recipient"""
    marketplace_base_mock.updateFeeRecipient(address, {'from': owner})
    assert marketplace_base_mock.getFeeRecipient() == address


@given(address=strategy('address'))
def test_update_fee_recipient_unauthorized(
        marketplace_base_mock: ProjectContract,
        address: LocalAccount,
        user: LocalAccount
) -> None:
    """Test update fee recipient - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        marketplace_base_mock.updateFeeRecipient(address, {'from': user})


def test_escrow_offer_payment_tokens(marketplace_base_mock: ProjectContract, owner: LocalAccount) -> None:
    """Test update escrow offer payment tokens"""
    value = True
    marketplace_base_mock.updateEscrowOfferPaymentTokens(value, {'from': owner})
    assert marketplace_base_mock.getEscrowOfferPaymentTokens() == value


def test_escrow_offer_payment_tokens_unauthorized(
        marketplace_base_mock: ProjectContract,
        user: LocalAccount
) -> None:
    """Test update escrow offer payment tokens - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        marketplace_base_mock.updateEscrowOfferPaymentTokens(True, {'from': user})

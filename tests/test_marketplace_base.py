import pytest
from brownie import reverts
from brownie.test import given, strategy
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount


@pytest.fixture(scope="module")
def marketplace_base_mock(address_registry: ProjectContract, owner: LocalAccount) -> None:
    return MarketplaceBaseMock.deploy(address_registry, owner, {'from': owner})


@given(address=strategy('address'))
def test_update_address_registry_address(
        erc1155_marketplace_mock: ProjectContract,
        address: LocalAccount,
        owner: LocalAccount
) -> None:
    """Test update address registry"""
    erc1155_marketplace_mock.updateAddressRegistryAddress(address, {'from': owner})
    assert erc1155_marketplace_mock.getAddressRegistryAddress() == address


@given(address=strategy('address'))
def test_update_address_registry_address_unauthorized(
        erc1155_marketplace_mock: ProjectContract,
        address: LocalAccount,
        user: LocalAccount
) -> None:
    """Test update address registry - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        erc1155_marketplace_mock.updateAddressRegistryAddress(address, {'from': user})


def test_update_min_bid_increment_amount(erc1155_marketplace_mock: ProjectContract, owner: LocalAccount) -> None:
    """Test update min bid increment amount"""
    amount = 5
    erc1155_marketplace_mock.updateMinBidIncrementAmount(amount, {'from': owner})
    assert erc1155_marketplace_mock.getMinBidIncrementAmount() == amount


def test_update_address_min_bid_increment_amount_unauthorized(
        erc1155_marketplace_mock: ProjectContract,
        user: LocalAccount
) -> None:
    """Test update min bid increment amount - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        erc1155_marketplace_mock.updateMinBidIncrementAmount(5, {'from': user})


def test_update_auction_fee(erc1155_marketplace_mock: ProjectContract, owner: LocalAccount) -> None:
    """Test update auction fee"""
    amount = 5
    erc1155_marketplace_mock.updateAuctionFee(amount, {'from': owner})
    assert erc1155_marketplace_mock.getAuctionFee() == amount


def test_update_auction_fee_unauthorized(erc1155_marketplace_mock: ProjectContract, user: LocalAccount) -> None:
    """Test update auction fee - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        erc1155_marketplace_mock.updateAuctionFee(5, {'from': user})


def test_update_listing_fee(erc1155_marketplace_mock: ProjectContract, owner: LocalAccount) -> None:
    """Test update listing fee"""
    amount = 5
    erc1155_marketplace_mock.updateListingFee(amount, {'from': owner})
    assert erc1155_marketplace_mock.getListingFee() == amount


def test_update_listing_fee_unauthorized(erc1155_marketplace_mock: ProjectContract, user: LocalAccount) -> None:
    """Test update listing fee - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        erc1155_marketplace_mock.updateListingFee(5, {'from': user})


def test_update_offer_fee(erc1155_marketplace_mock: ProjectContract, owner: LocalAccount) -> None:
    """Test update offer fee"""
    amount = 5
    erc1155_marketplace_mock.updateOfferFee(amount, {'from': owner})
    assert erc1155_marketplace_mock.getOfferFee() == amount


def test_update_offer_fee_unauthorized(erc1155_marketplace_mock: ProjectContract, user: LocalAccount) -> None:
    """Test update offer fee - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        erc1155_marketplace_mock.updateOfferFee(5, {'from': user})


@given(address=strategy('address'))
def test_update_fee_recipient(
        erc1155_marketplace_mock: ProjectContract,
        address: LocalAccount,
        owner: LocalAccount
) -> None:
    """Test update fee recipient"""
    erc1155_marketplace_mock.updateFeeRecipient(address, {'from': owner})
    assert erc1155_marketplace_mock.getFeeRecipient() == address


@given(address=strategy('address'))
def test_update_fee_recipient_unauthorized(
        erc1155_marketplace_mock: ProjectContract,
        address: LocalAccount,
        user: LocalAccount
) -> None:
    """Test update fee recipient - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        erc1155_marketplace_mock.updateFeeRecipient(address, {'from': user})


def test_escrow_offer_payment_tokens(erc1155_marketplace_mock: ProjectContract, owner: LocalAccount) -> None:
    """Test update escrow offer payment tokens"""
    value = True
    erc1155_marketplace_mock.updateEscrowOfferPaymentTokens(value, {'from': owner})
    assert erc1155_marketplace_mock.getEscrowOfferPaymentTokens() == value


def test_escrow_offer_payment_tokens_unauthorized(
        erc1155_marketplace_mock: ProjectContract,
        user: LocalAccount
) -> None:
    """Test update escrow offer payment tokens - unauthorized"""
    with reverts("Ownable: caller is not the owner"):
        erc1155_marketplace_mock.updateEscrowOfferPaymentTokens(True, {'from': user})

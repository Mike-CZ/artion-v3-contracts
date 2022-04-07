import pytest
from enum import Enum
from dataclasses import dataclass
from brownie import reverts, chain, accounts
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable
from utils.structs import ERC1155Offer, Offer
from utils.constants import TOMB_TOKEN
from utils.helpers import calculate_offer_fee, calculate_royalty_fee
from brownie.test import given, strategy
from hypothesis import settings


@dataclass(frozen=True)
class OfferParams:
    token_id: int = 1_000_000
    token_amount: int = 50
    price: int = 100
    expiration_time: int = chain.time() + (60 * 60 * 24)  # expire offer at current time + 24 hour


@dataclass(frozen=True)
class RoyaltyParams:
    fraction: int = 1_000  # 10%


class OfferStatus(Enum):
    CREATED = 0
    EXPIRED = 1


@pytest.fixture(scope="session")
def offeror(user: LocalAccount) -> LocalAccount:
    return user


@pytest.fixture(scope="session")
def token_owner(user_2: LocalAccount) -> LocalAccount:
    return user_2


@pytest.fixture(scope="session")
def royalty_recipient(user_3: LocalAccount) -> LocalAccount:
    return user_3


def handle_offer_status(status: OfferStatus) -> None:
    if status is OfferStatus.EXPIRED:
        chain.sleep(OfferParams.expiration_time - chain.time())
        chain.mine()


@pytest.fixture(scope='module')
def setup_offer(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        royalty_registry: ProjectContract,
        royalty_recipient: LocalAccount,
        payment_token: ProjectContract,
        offeror: LocalAccount,
        token_owner: LocalAccount,
        owner: LocalAccount
) -> Callable:
    def setup_listing_(enable_escrow: bool = False, status: OfferStatus = OfferStatus.CREATED) -> None:
        erc1155_marketplace_mock.updateEscrowOfferPaymentTokens(enable_escrow, {'from': owner})

        # mint token and set royalty
        erc1155_collection_mock.mint(token_owner, OfferParams.token_id, OfferParams.token_amount, '')
        royalty_registry.setTokenRoyalty(
            erc1155_collection_mock,
            OfferParams.token_id,
            royalty_recipient,
            RoyaltyParams.fraction,
            {'from': token_owner}
        )

        # transfer token if required
        if enable_escrow is True:
            payment_token.approveInternal(offeror, erc1155_marketplace_mock, OfferParams.price)

        # create offer
        erc1155_marketplace_mock.createOffer(
            erc1155_collection_mock,
            OfferParams.token_id,
            OfferParams.token_amount,
            payment_token,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )

        # set approval for future use
        erc1155_collection_mock.setApprovalForAll(erc1155_marketplace_mock, True, {'from': token_owner})

        # expire offer if required
        handle_offer_status(status)
    return setup_listing_


@pytest.mark.parametrize("escrow_tokens", [True, False])
def test_create_offer(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        erc1155_collection_mint_with_approval: Callable,
        payment_token: ProjectContract,
        offeror: LocalAccount,
        owner: LocalAccount,
        escrow_tokens: bool
) -> None:
    """Test offer creation"""
    erc1155_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_tokens, {'from': owner})

    token_amount = 10
    token_id = 2
    price = 5
    expiration_time = chain.time() + (60 * 60 * 2)

    initial_marketplace_balance = payment_token.balanceOf(erc1155_marketplace_mock)
    initial_offeror_balance = payment_token.balanceOf(offeror)

    if escrow_tokens:
        payment_token.approveInternal(offeror, erc1155_marketplace_mock, OfferParams.price)

    tx = erc1155_marketplace_mock.createOffer(
        erc1155_collection_mock,
        token_id,
        token_amount,
        payment_token,
        price,
        expiration_time,
        {'from': offeror}
    )

    # validate listing successfully created
    data = erc1155_marketplace_mock.getOffer(erc1155_collection_mock, token_id, offeror)
    erc1155_offer = ERC1155Offer(Offer(*data[0]), *data[1:])

    assert erc1155_offer.exists()
    assert erc1155_offer.offer.payment_token == payment_token.address
    assert erc1155_offer.offer.offeror == offeror.address
    assert erc1155_offer.offer.price == price
    assert erc1155_offer.offer.expiration_time == expiration_time
    assert erc1155_offer.offer.payment_token_in_escrow is escrow_tokens
    assert erc1155_offer.token_amount == token_amount

    # check event
    assert tx.events["ERC1155OfferCreated"] is not None
    assert tx.events["ERC1155OfferCreated"]["offeror"] == offeror.address
    assert tx.events["ERC1155OfferCreated"]["nftAddress"] == erc1155_collection_mock.address
    assert tx.events["ERC1155OfferCreated"]["tokenId"] == token_id
    assert tx.events["ERC1155OfferCreated"]["tokenAmount"] == token_amount
    assert tx.events["ERC1155OfferCreated"]["paymentToken"] == payment_token.address
    assert tx.events["ERC1155OfferCreated"]["price"] == price
    assert tx.events["ERC1155OfferCreated"]["expirationTime"] == expiration_time
    assert tx.events["ERC1155OfferCreated"]["isPayTokenInEscrow"] is escrow_tokens

    # assert tokens transferred
    if escrow_tokens:
        assert payment_token.balanceOf(erc1155_marketplace_mock) == initial_marketplace_balance + price
        assert payment_token.balanceOf(offeror) == initial_offeror_balance - price
    else:
        assert payment_token.balanceOf(erc1155_marketplace_mock) == initial_marketplace_balance
        assert payment_token.balanceOf(offeror) == initial_offeror_balance


def test_create_offer_invalid_token_type(
        erc1155_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        offeror: LocalAccount
) -> None:
    """Test offer creation with invalid token type"""
    with reverts('ERC1155Marketplace: NFT not ERC1155'):
        erc1155_marketplace_mock.createOffer(
            erc721_collection_mock,
            OfferParams.token_id,
            OfferParams.token_amount,
            payment_token,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )


def test_create_offer_invalid_amount(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        offeror: LocalAccount
) -> None:
    """Test offer creation with invalid amount"""
    with reverts('ERC1155Marketplace: invalid amount'):
        erc1155_marketplace_mock.createOffer(
            erc1155_collection_mock,
            OfferParams.token_id,
            0,
            payment_token,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )


@given(token_address=strategy('address'))
@settings(max_examples=1)
def test_create_offer_invalid_payment_token(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        token_address: LocalAccount,
        offeror: LocalAccount
):
    """Test offer creation with invalid payment token"""
    with reverts('MarketplaceBase: payment token is not enabled'):
        erc1155_marketplace_mock.createOffer(
            erc1155_collection_mock,
            OfferParams.token_id,
            OfferParams.token_amount,
            token_address,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )


def test_create_offer_already_exists(
        setup_offer: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        offeror: LocalAccount
) -> None:
    """Test offer creation when already exists"""
    setup_offer()

    with reverts('MarketplaceBase: offer exist'):
        erc1155_marketplace_mock.createOffer(
            erc1155_collection_mock,
            OfferParams.token_id,
            OfferParams.token_amount,
            payment_token,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )


def test_create_offer_invalid_expiration_time(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        offeror: LocalAccount
) -> None:
    """Test offer creation with invalid expiration time"""
    with reverts('MarketplaceBase: invalid expiration time'):
        erc1155_marketplace_mock.createOffer(
            erc1155_collection_mock,
            OfferParams.token_id,
            OfferParams.token_amount,
            payment_token,
            OfferParams.price,
            chain.time() - 1,
            {'from': offeror}
        )


@pytest.mark.parametrize("escrow_tokens", [True, False])
def test_cancel_offer(
        setup_offer: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        offeror: LocalAccount,
        escrow_tokens: bool
) -> None:
    """Test offer cancel"""
    setup_offer(enable_escrow=escrow_tokens)

    initial_marketplace_balance = payment_token.balanceOf(erc1155_marketplace_mock)
    initial_offeror_balance = payment_token.balanceOf(offeror)

    tx = erc1155_marketplace_mock.cancelOffer(
        erc1155_collection_mock,
        OfferParams.token_id,
        {'from': offeror}
    )

    # assert offer no longer exists
    assert erc1155_marketplace_mock.hasOffer(erc1155_collection_mock, OfferParams.token_id, offeror) is False

    # check event
    assert tx.events["ERC1155OfferCanceled"] is not None
    assert tx.events["ERC1155OfferCanceled"]["offeror"] == offeror.address
    assert tx.events["ERC1155OfferCanceled"]["nftAddress"] == erc1155_collection_mock.address
    assert tx.events["ERC1155OfferCanceled"]["tokenId"] == OfferParams.token_id
    assert tx.events["ERC1155OfferCanceled"]["tokenAmount"] == OfferParams.token_amount

    # assert tokens refunded
    if escrow_tokens:
        assert payment_token.balanceOf(erc1155_marketplace_mock) == initial_marketplace_balance - OfferParams.price
        assert payment_token.balanceOf(offeror) == initial_offeror_balance + OfferParams.price
    else:
        assert payment_token.balanceOf(erc1155_marketplace_mock) == initial_marketplace_balance
        assert payment_token.balanceOf(offeror) == initial_offeror_balance


def test_cancel_offer_not_exists(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        offeror: LocalAccount
) -> None:
    """Test offer cancel when does not exist"""

    with reverts('MarketplaceBase: offer not exist'):
        erc1155_marketplace_mock.cancelOffer(
            erc1155_collection_mock,
            OfferParams.token_id,
            {'from': offeror}
        )


@pytest.mark.parametrize("escrow_tokens", [True, False])
def test_accept_offer(
        setup_offer: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        offeror: LocalAccount,
        token_owner: LocalAccount,
        royalty_recipient: LocalAccount,
        escrow_tokens: bool
) -> None:
    """Test offer accept"""
    setup_offer(enable_escrow=escrow_tokens)

    fee_recipient = accounts.at(erc1155_marketplace_mock.getFeeRecipient())
    initial_marketplace_balance = payment_token.balanceOf(erc1155_marketplace_mock)
    initial_token_owner_balance = payment_token.balanceOf(token_owner)
    initial_offeror_balance = payment_token.balanceOf(offeror)
    initial_fee_recipient_amount = payment_token.balanceOf(fee_recipient)
    initial_royalty_recipient_amount = payment_token.balanceOf(royalty_recipient)

    initial_offeror_token_amount = erc1155_collection_mock.balanceOf(offeror, OfferParams.token_id)
    initial_token_owner_token_amount = erc1155_collection_mock.balanceOf(token_owner, OfferParams.token_id)

    if not escrow_tokens:
        payment_token.approveInternal(offeror, erc1155_marketplace_mock, OfferParams.price)

    tx = erc1155_marketplace_mock.acceptOffer(
        erc1155_collection_mock,
        OfferParams.token_id,
        offeror,
        {'from': token_owner}
    )

    fee = calculate_offer_fee(OfferParams.price, erc1155_marketplace_mock.getOfferFee())
    royalty_fee = calculate_royalty_fee(OfferParams.price - fee, RoyaltyParams.fraction)

    assert erc1155_marketplace_mock.hasOffer(erc1155_collection_mock, OfferParams.token_id, offeror) is False

    # check event
    assert tx.events["ERC1155OfferAccepted"] is not None
    assert tx.events["ERC1155OfferAccepted"]["seller"] == token_owner.address
    assert tx.events["ERC1155OfferAccepted"]["buyer"] == offeror.address
    assert tx.events["ERC1155OfferAccepted"]["nftAddress"] == erc1155_collection_mock.address
    assert tx.events["ERC1155OfferAccepted"]["tokenId"] == OfferParams.token_id
    assert tx.events["ERC1155OfferAccepted"]["tokenAmount"] == OfferParams.token_amount
    assert tx.events["ERC1155OfferAccepted"]["price"] == OfferParams.price
    assert tx.events["ERC1155OfferAccepted"]["paymentToken"] == payment_token.address

    # assert tokens transferred
    assert erc1155_collection_mock.balanceOf(offeror, OfferParams.token_id) == \
           initial_offeror_token_amount + OfferParams.token_amount
    assert erc1155_collection_mock.balanceOf(token_owner, OfferParams.token_id) == \
           initial_token_owner_token_amount - OfferParams.token_amount

    # assert payment tokens sent
    assert payment_token.balanceOf(fee_recipient) == initial_fee_recipient_amount + fee
    assert payment_token.balanceOf(royalty_recipient) == initial_royalty_recipient_amount + royalty_fee
    assert payment_token.balanceOf(token_owner) == initial_token_owner_balance + OfferParams.price - fee - royalty_fee

    if escrow_tokens:
        assert payment_token.balanceOf(erc1155_marketplace_mock) == initial_marketplace_balance - OfferParams.price
        assert payment_token.balanceOf(offeror) == initial_offeror_balance
    else:
        assert payment_token.balanceOf(erc1155_marketplace_mock) == initial_marketplace_balance
        assert payment_token.balanceOf(offeror) == initial_offeror_balance - OfferParams.price


def test_accept_offer_not_exists(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        token_owner: LocalAccount
) -> None:
    """Test offer accept - not exist"""
    with reverts('MarketplaceBase: offer not exist'):
        erc1155_marketplace_mock.cancelOffer(
            erc1155_collection_mock,
            OfferParams.token_id,
            {'from': token_owner}
        )


def test_accept_offer_expired(
        setup_offer: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        token_owner: LocalAccount,
        offeror: LocalAccount
) -> None:
    """Test offer accept - expired"""
    setup_offer(status=OfferStatus.EXPIRED)

    with reverts('MarketplaceBase: offer expired'):
        erc1155_marketplace_mock.acceptOffer(
            erc1155_collection_mock,
            OfferParams.token_id,
            offeror,
            {'from': token_owner}
        )

import math

import pytest
from enum import Enum
from dataclasses import dataclass
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable
from utils.structs import Offer
from utils.helpers import calculate_offer_fee, calculate_royalty_fee
from brownie import reverts, Wei, chain, ZERO_ADDRESS


class OfferStatus(Enum):
    ACTIVE = 0
    EXPIRED = 1


@dataclass(frozen=True)
class OfferParams:
    price: int = 100
    expiration_time: int = chain.time() + (60 * 60)  # start listing at current time + 1 hour


@dataclass(frozen=True)
class RoyaltyParams:
    fraction: int = 1_000  # 10%


@pytest.fixture(scope="module")
def token_owner(user: LocalAccount) -> LocalAccount:
    return user


@pytest.fixture(scope="module")
def offeror(user_2: LocalAccount) -> LocalAccount:
    return user_2


@pytest.fixture(scope="session")
def royalty_recipient(user_3: LocalAccount) -> LocalAccount:
    return user_3


def handle_offer_status(status: OfferStatus) -> None:
    if status is not OfferStatus.ACTIVE:
        chain.sleep(OfferParams.expiration_time - chain.time())
        chain.mine()


@pytest.fixture(scope='module')
def setup_offer(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        token_owner: LocalAccount,
        offeror: LocalAccount,
        royalty_recipient: LocalAccount,
) -> Callable:
    def setup_offer_(status: OfferStatus = OfferStatus.ACTIVE) -> int:
        token_id = erc721_collection_mock.mintAndGetTokenId(
            token_owner,
            '',
            royalty_recipient,
            RoyaltyParams.fraction
        ).return_value

        # create offer
        erc721_collection_mock.setApprovalForAll(erc721_marketplace_mock, True, {'from': token_owner})
        erc721_marketplace_mock.createOffer(
            erc721_collection_mock,
            token_id,
            payment_token,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )

        # start/end offer
        handle_offer_status(status)

        return token_id
    return setup_offer_


@pytest.mark.parametrize("escrow_tokens", [True, False])
def test_create_offer_escrow(
        payment_token: ProjectContract,
        erc721_collection_mint_with_approval: Callable,
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        offeror: LocalAccount,
        owner: LocalAccount,
        escrow_tokens: bool
) -> None:
    """Test valid offer creation WITH storing offered payment tokens in escrow"""
    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_tokens, {'from': owner})

    initial_marketplace_balance = payment_token.balanceOf(erc721_marketplace_mock)
    initial_offeror_balance = payment_token.balanceOf(offeror)

    token_id = erc721_collection_mint_with_approval(offeror)

    # set allowance
    if escrow_tokens:
        payment_token.approve(erc721_marketplace_mock, OfferParams.price, {"from": offeror})

    # create offer
    tx = erc721_marketplace_mock.createOffer(
        erc721_collection_mock,
        token_id,
        payment_token,
        OfferParams.price,
        OfferParams.expiration_time,
        {'from': offeror}
    )

    # assert offer was created with correct data
    offer = Offer(*erc721_marketplace_mock.getOffer(erc721_collection_mock, token_id, offeror))
    assert offer.exists()
    assert offer.payment_token == payment_token.address
    assert offer.offeror == offeror
    assert offer.price == OfferParams.price
    assert offer.expiration_time == OfferParams.expiration_time
    assert offer.payment_token_in_escrow == escrow_tokens

    # check event
    assert tx.events["ERC721OfferCreated"] is not None
    assert tx.events["ERC721OfferCreated"]["offeror"] == offeror
    assert tx.events["ERC721OfferCreated"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ERC721OfferCreated"]["tokenId"] == token_id
    assert tx.events["ERC721OfferCreated"]["paymentToken"] == payment_token.address
    assert tx.events["ERC721OfferCreated"]["price"] == OfferParams.price
    assert tx.events["ERC721OfferCreated"]["expirationTime"] == OfferParams.expiration_time
    assert tx.events["ERC721OfferCreated"]["isPayTokenInEscrow"] == escrow_tokens

    # assert tokens transferred
    if escrow_tokens:
        assert payment_token.balanceOf(erc721_marketplace_mock) == initial_marketplace_balance + OfferParams.price
        assert payment_token.balanceOf(offeror) == initial_offeror_balance - OfferParams.price
    else:
        assert payment_token.balanceOf(erc721_marketplace_mock) == initial_marketplace_balance
        assert payment_token.balanceOf(offeror) == initial_offeror_balance


def test_create_offer_invalid_payment_token(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        offeror: LocalAccount
) -> None:
    """Test offer creation with invalid payment token"""
    token_id = 1
    payment_token = ZERO_ADDRESS

    # try to create offer
    with reverts('MarketplaceBase: payment token not enabled'):
        erc721_marketplace_mock.createOffer(
            erc721_collection_mock,
            token_id,
            payment_token,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )


def test_create_offer_invalid_nft_contract(
        erc721_marketplace_mock: ProjectContract,
        payment_token: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        offeror: LocalAccount
) -> None:
    """Test offer creation with invalid nft contract address (not ERC721 standard)"""
    token_id = 1

    # try to create offer
    with reverts('ERC721Marketplace: NFT not ERC721'):
        erc721_marketplace_mock.createOffer(
            erc1155_collection_mock,
            token_id,
            payment_token,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )


def test_create_offer_invalid_expiration_time(
        erc721_collection_mint_with_approval: Callable,
        erc721_marketplace_mock: ProjectContract,
        payment_token: ProjectContract,
        erc721_collection_mock: ProjectContract,
        offeror: LocalAccount
) -> None:
    """Test offer creation with invalid expiration time (in the past)"""
    expiration_time = chain.time() - (60 * 60)  # offer expired 1 hour ago

    token_id = erc721_collection_mint_with_approval(offeror)

    # try to create offer
    with reverts('MarketplaceBase: invalid expiration time'):
        erc721_marketplace_mock.createOffer(
            erc721_collection_mock,
            token_id,
            payment_token,
            OfferParams.price,
            expiration_time,
            {'from': offeror}
        )


def test_create_offer_twice(
        erc721_marketplace_mock: ProjectContract,
        payment_token: ProjectContract,
        erc721_collection_mock: ProjectContract,
        offeror: LocalAccount,
        setup_offer: Callable
) -> None:
    """Test creating two same offers on the same NFT"""

    # set allowance
    payment_token.approve(erc721_marketplace_mock, OfferParams.price, {"from": offeror})

    # create listing
    token_id = setup_offer()

    # try to create offer
    with reverts("MarketplaceBase: offer exists"):
        erc721_marketplace_mock.createOffer(
            erc721_collection_mock,
            token_id,
            payment_token,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )


@pytest.mark.parametrize(
    'escrow_offer_payment_tokens, expired_offer',
    [
        (True, OfferStatus.ACTIVE),
        (True, OfferStatus.EXPIRED),
        (False, OfferStatus.ACTIVE),
        (False, OfferStatus.EXPIRED)
    ]
)
def test_cancel_offer(
        erc721_marketplace_mock: ProjectContract,
        payment_token: ProjectContract,
        erc721_collection_mock: ProjectContract,
        offeror: LocalAccount,
        setup_offer: Callable,
        escrow_offer_payment_tokens: bool,
        expired_offer: OfferStatus
) -> None:
    """Test canceling offer WITH and WITHOUT storing offered payment tokens in escrow"""
    initial_marketplace_balance = payment_token.balanceOf(erc721_marketplace_mock.address)
    initial_offeror_balance = payment_token.balanceOf(offeror.address)

    # turn on/off storing payment tokens in escrow
    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_offer_payment_tokens)

    if escrow_offer_payment_tokens:
        # set allowance
        payment_token.approve(erc721_marketplace_mock, OfferParams.price, {"from": offeror})

    # create offer
    token_id = setup_offer(expired_offer)

    # cancel offer
    tx = erc721_marketplace_mock.cancelOffer(
        erc721_collection_mock,
        token_id,
        {'from': offeror}
    )

    # check if payment tokens were returned from escrow
    assert payment_token.balanceOf(erc721_marketplace_mock.address) == initial_marketplace_balance
    assert payment_token.balanceOf(offeror.address) == initial_offeror_balance

    # check offer existence
    assert erc721_marketplace_mock.hasOffer(erc721_collection_mock, token_id, offeror) is False

    # check event
    assert tx.events["ERC721OfferCanceled"] is not None
    assert tx.events["ERC721OfferCanceled"]["offeror"] == offeror
    assert tx.events["ERC721OfferCanceled"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ERC721OfferCanceled"]["tokenId"] == token_id


@pytest.mark.parametrize(
    'escrow_offer_payment_tokens, expired_offer',
    [
        (True, OfferStatus.ACTIVE),
        (True, OfferStatus.EXPIRED),
        (False, OfferStatus.ACTIVE),
        (False, OfferStatus.EXPIRED)
    ]
)
def test_cancel_offer_after_escrow_update(
        erc721_marketplace_mock: ProjectContract,
        payment_token: ProjectContract,
        erc721_collection_mock: ProjectContract,
        offeror: LocalAccount,
        setup_offer: Callable,
        escrow_offer_payment_tokens: bool,
        expired_offer: OfferStatus
) -> None:
    """Test canceling offer AFTER storing offered payment tokens in escrow was tuned ON/OFF"""
    initial_marketplace_balance = payment_token.balanceOf(erc721_marketplace_mock.address)
    initial_offeror_balance = payment_token.balanceOf(offeror.address)

    # turn on/off storing payment tokens in escrow
    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_offer_payment_tokens)

    if escrow_offer_payment_tokens:
        # set allowance
        payment_token.approve(erc721_marketplace_mock, OfferParams.price, {"from": offeror})

    # create offer
    token_id = setup_offer(expired_offer)

    # turn off/on storing payment tokens in escrow
    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(not escrow_offer_payment_tokens)

    # cancel offer
    erc721_marketplace_mock.cancelOffer(erc721_collection_mock, token_id, {'from': offeror})

    # check if payment tokens were returned from escrow
    assert payment_token.balanceOf(erc721_marketplace_mock.address) == initial_marketplace_balance
    assert payment_token.balanceOf(offeror.address) == initial_offeror_balance

    # check offer existence
    assert erc721_marketplace_mock.hasOffer(erc721_collection_mock, token_id, offeror) is False


def test_canceling_non_existent_offer(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        erc721_collection_mint_with_approval: Callable,
        offeror
) -> None:
    """Test canceling offer that does NOT exist"""
    token_id = erc721_collection_mint_with_approval(offeror)

    # cancel offer
    with reverts("MarketplaceBase: offer not exists"):
        erc721_marketplace_mock.cancelOffer(
            erc721_collection_mock,
            token_id,
            {'from': offeror}
        )


@pytest.mark.parametrize('escrow_offer_payment_tokens', [True, False])
def test_accept_offer(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        owner: LocalAccount,
        token_owner: LocalAccount,
        offeror: LocalAccount,
        royalty_recipient: LocalAccount,
        setup_offer: Callable,
        escrow_offer_payment_tokens: bool
) -> None:
    """Test accepting an offer"""
    initial_platform_balance = payment_token.balanceOf(owner.address)
    initial_owner_balance = payment_token.balanceOf(token_owner.address)
    initial_offeror_balance = payment_token.balanceOf(offeror.address)
    initial_royalty_recipient_amount = payment_token.balanceOf(royalty_recipient.address)
    platform_fee = calculate_offer_fee(OfferParams.price, erc721_marketplace_mock.getOfferFee())
    royalty_fee = calculate_royalty_fee(OfferParams.price - platform_fee, RoyaltyParams.fraction)

    # turn on/off storing payment tokens in escrow
    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_offer_payment_tokens)

    # set allowance
    payment_token.approve(erc721_marketplace_mock, OfferParams.price, {"from": offeror})

    token_id = setup_offer()

    tx = erc721_marketplace_mock.acceptOffer(erc721_collection_mock, token_id, offeror, {"from": token_owner})

    # check balances
    assert payment_token.balanceOf(owner) == initial_platform_balance + platform_fee
    assert payment_token.balanceOf(token_owner) == initial_owner_balance + OfferParams.price - platform_fee - royalty_fee
    assert payment_token.balanceOf(offeror) == initial_offeror_balance - OfferParams.price
    assert payment_token.balanceOf(royalty_recipient) == initial_royalty_recipient_amount + royalty_fee

    # check NFT owner
    assert erc721_collection_mock.ownerOf(token_id) == offeror

    # check event
    assert tx.events["ERC721OfferAccepted"] is not None
    assert tx.events["ERC721OfferAccepted"]["seller"] == token_owner
    assert tx.events["ERC721OfferAccepted"]["buyer"] == offeror
    assert tx.events["ERC721OfferAccepted"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ERC721OfferAccepted"]["tokenId"] == token_id
    assert tx.events["ERC721OfferAccepted"]["price"] == OfferParams.price
    assert tx.events["ERC721OfferAccepted"]["paymentToken"] == payment_token

    # check offer existence
    assert erc721_marketplace_mock.hasOffer(erc721_collection_mock, token_id, offeror) is False

    # check listing existence
    assert erc721_marketplace_mock.hasListing(erc721_collection_mock, token_id) is False


def test_accept_nonexistent_offer(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        token_owner: LocalAccount,
        offeror: LocalAccount
) -> None:
    """Test accepting an offer that doesn't exist"""

    token_id = 1

    # try to accept offer
    with reverts("MarketplaceBase: offer not exists"):
        erc721_marketplace_mock.acceptOffer(erc721_collection_mock, token_id, offeror, {"from": token_owner})


def test_accept_expired_offer(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        offeror: LocalAccount,
        token_owner: LocalAccount,
        payment_token: ProjectContract,
        setup_offer: Callable
) -> None:
    """Test accepting an offer that doesn't exist"""

    # set allowance
    payment_token.approve(erc721_marketplace_mock, OfferParams.price, {"from": offeror})

    token_id = setup_offer(OfferStatus.EXPIRED)

    # try to accept offer
    with reverts("MarketplaceBase: offer expired"):
        erc721_marketplace_mock.acceptOffer(erc721_collection_mock, token_id, offeror, {"from": token_owner})


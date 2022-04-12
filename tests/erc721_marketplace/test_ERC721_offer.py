import math

import pytest
from enum import Enum
from dataclasses import dataclass
from brownie import reverts, Wei, chain, ZERO_ADDRESS


class OfferStatus(Enum):
    ACTIVE = 0
    EXPIRED = 1


@dataclass(frozen=True)
class OfferParams:
    price: int = 100
    expiration_time: int = chain.time() + (60 * 60)  # start listing at current time + 1 hour


@pytest.fixture(scope="module")
def token_owner(user):
    return user


@pytest.fixture(scope="module")
def offeror(user_2):
    return user_2


def handle_offer_status(status: OfferStatus):
    if status is not OfferStatus.ACTIVE:
        chain.sleep(OfferParams.expiration_time - chain.time())
        chain.mine()


@pytest.fixture(scope='module')
def setup_offer(
        erc721_marketplace_mock,
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        offeror
):
    def setup_offer_(status: OfferStatus = OfferStatus.ACTIVE):
        erc721_marketplace_mock.createOffer(
            erc721_collection_mock,
            erc721_collection_mint_with_approval,
            payment_token,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )

        # start/end offer
        handle_offer_status(status)

        return erc721_collection_mint_with_approval
    return setup_offer_


def test_create_offer_escrow_on(
        payment_token,
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        erc721_collection_mock,
        offeror
):
    """Test valid offer creation WITH storing offered payment tokens in escrow"""
    initial_marketplace_balance = payment_token.balanceOf(erc721_marketplace_mock.address)
    initial_offeror_balance = payment_token.balanceOf(offeror.address)

    # set allowance
    payment_token.approve(erc721_marketplace_mock, OfferParams.price, {"from": offeror})

    # create offer
    tx = erc721_marketplace_mock.createOffer(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        OfferParams.price,
        OfferParams.expiration_time,
        {'from': offeror}
    )

    # assert offer was created with correct data
    offer = erc721_marketplace_mock.getOffer(erc721_collection_mock, erc721_collection_mint_with_approval, offeror)
    assert offer[0] == payment_token.address
    assert offer[1] == offeror
    assert offer[2] == OfferParams.price
    assert offer[3] == OfferParams.expiration_time

    # check event
    assert tx.events["ERC721OfferCreated"] is not None
    assert tx.events["ERC721OfferCreated"]["offeror"] == offeror
    assert tx.events["ERC721OfferCreated"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ERC721OfferCreated"]["tokenId"] == erc721_collection_mint_with_approval
    assert tx.events["ERC721OfferCreated"]["paymentToken"] == payment_token.address
    assert tx.events["ERC721OfferCreated"]["price"] == OfferParams.price
    assert tx.events["ERC721OfferCreated"]["expirationTime"] == OfferParams.expiration_time

    # check if payment tokens were stored in escrow
    assert payment_token.balanceOf(erc721_marketplace_mock.address) == initial_marketplace_balance + OfferParams.price
    assert payment_token.balanceOf(offeror.address) == initial_offeror_balance - OfferParams.price


def test_create_offer_escrow_off(
        payment_token,
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        erc721_collection_mock,
        offeror,
        token_owner
):
    """Test valid offer creation WITHOUT storing offered payment tokens in escrow"""
    initial_token_owner_balance = payment_token.balanceOf(token_owner.address)
    initial_marketplace_balance = payment_token.balanceOf(erc721_marketplace_mock.address)
    initial_offeror_balance = payment_token.balanceOf(offeror.address)

    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(False)

    # create offer
    erc721_marketplace_mock.createOffer(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        OfferParams.price,
        OfferParams.expiration_time,
        {'from': offeror}
    )

    # assert offer was created with correct data
    offer = erc721_marketplace_mock.getOffer(erc721_collection_mock, erc721_collection_mint_with_approval, offeror)
    assert offer[0] == payment_token.address
    assert offer[1] == offeror
    assert offer[2] == OfferParams.price
    assert offer[3] == OfferParams.expiration_time

    # check if payment tokens were NOT stored in escrow
    assert payment_token.balanceOf(token_owner.address) == initial_token_owner_balance
    assert payment_token.balanceOf(erc721_marketplace_mock.address) == initial_marketplace_balance
    assert payment_token.balanceOf(offeror.address) == initial_offeror_balance


@pytest.mark.parametrize('escrow_offer_payment_tokens', [True, False])
def test_create_offer_invalid_payment_token(
        erc721_marketplace_mock,
        erc721_collection_mock,
        offeror,
        escrow_offer_payment_tokens
):
    """Test offer creation with invalid payment token"""
    token_id = 1
    payment_token = ZERO_ADDRESS

    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_offer_payment_tokens)

    # try to create offer
    with reverts('MarketplaceBase: payment token is not enabled'):
        erc721_marketplace_mock.createOffer(
            erc721_collection_mock,
            token_id,
            payment_token,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )


@pytest.mark.parametrize('escrow_offer_payment_tokens', [True, False])
def test_create_offer_invalid_nft_contract(
        erc721_marketplace_mock,
        payment_token,
        erc1155_collection_mock,
        offeror,
        escrow_offer_payment_tokens
):
    """Test offer creation with invalid nft contract address (not ERC721 standard)"""
    token_id = 1

    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_offer_payment_tokens)

    # try to create offer
    with reverts('ERC721Marketplace: NFT is not ERC721'):
        erc721_marketplace_mock.createOffer(
            erc1155_collection_mock,
            token_id,
            payment_token,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )


@pytest.mark.parametrize('escrow_offer_payment_tokens', [True, False])
def test_create_offer_invalid_expiration_time(
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        payment_token,
        erc721_collection_mock,
        offeror,
        escrow_offer_payment_tokens
):
    """Test offer creation with invalid expiration time (in the past)"""
    expiration_time = chain.time() - (60 * 60)  # offer expired 1 hour ago

    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_offer_payment_tokens)

    # try to create offer
    with reverts('MarketplaceBase: invalid expiration time'):
        erc721_marketplace_mock.createOffer(
            erc721_collection_mock,
            erc721_collection_mint_with_approval,
            payment_token,
            OfferParams.price,
            expiration_time,
            {'from': offeror}
        )


@pytest.mark.parametrize('escrow_offer_payment_tokens', [True, False])
def test_create_offer_on_listed_nft(
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        payment_token,
        erc721_collection_mock,
        offeror,
        token_owner,
        escrow_offer_payment_tokens,
        setup_offer
):
    """Test offer creation on NFT that is already listed"""
    price = 100
    starting_time = chain.time() + (60 * 60)

    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_offer_payment_tokens)

    # create listing
    erc721_marketplace_mock.createListing(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        price,
        starting_time,
        {'from': token_owner}
    )

    # try to create offer
    with reverts("ERC721Marketplace: NFT already in escrow"):
        setup_offer()


@pytest.mark.parametrize('escrow_offer_payment_tokens', [True, False])
def test_create_offer_twice(
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        payment_token,
        erc721_collection_mock,
        offeror,
        escrow_offer_payment_tokens,
        setup_offer
):
    """Test creating two same offers on the same NFT"""
    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_offer_payment_tokens)

    # set allowance
    payment_token.approve(erc721_marketplace_mock, OfferParams.price, {"from": offeror})

    # create listing
    setup_offer()

    # try to create offer
    with reverts("ERC721Marketplace: offer already exists"):
        setup_offer()


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
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        payment_token,
        erc721_collection_mock,
        offeror,
        setup_offer,
        escrow_offer_payment_tokens,
        expired_offer
):
    """Test canceling offer WITH and WITHOUT storing offered payment tokens in escrow"""
    initial_marketplace_balance = payment_token.balanceOf(erc721_marketplace_mock.address)
    initial_offeror_balance = payment_token.balanceOf(offeror.address)

    # turn on/off storing payment tokens in escrow
    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_offer_payment_tokens)

    if escrow_offer_payment_tokens:
        # set allowance
        payment_token.approve(erc721_marketplace_mock, OfferParams.price, {"from": offeror})

    # create offer
    setup_offer(expired_offer)

    # cancel offer
    tx = erc721_marketplace_mock.cancelOffer(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        {'from': offeror}
    )

    # check if payment tokens were returned from escrow
    assert payment_token.balanceOf(erc721_marketplace_mock.address) == initial_marketplace_balance
    assert payment_token.balanceOf(offeror.address) == initial_offeror_balance

    # check offer existence
    offer = erc721_marketplace_mock.getOffer(erc721_collection_mock, erc721_collection_mint_with_approval, offeror)
    assert offer[0] == ZERO_ADDRESS
    assert offer[1] == ZERO_ADDRESS
    assert offer[2] == 0
    assert offer[3] == 0

    # check event
    assert tx.events["ERC721OfferCanceled"] is not None
    assert tx.events["ERC721OfferCanceled"]["offeror"] == offeror
    assert tx.events["ERC721OfferCanceled"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ERC721OfferCanceled"]["tokenId"] == erc721_collection_mint_with_approval


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
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        payment_token,
        erc721_collection_mock,
        offeror,
        setup_offer,
        escrow_offer_payment_tokens,
        expired_offer
):
    """Test canceling offer AFTER storing offered payment tokens in escrow was tuned ON/OFF"""
    initial_marketplace_balance = payment_token.balanceOf(erc721_marketplace_mock.address)
    initial_offeror_balance = payment_token.balanceOf(offeror.address)

    # turn on/off storing payment tokens in escrow
    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_offer_payment_tokens)

    if escrow_offer_payment_tokens:
        # set allowance
        payment_token.approve(erc721_marketplace_mock, OfferParams.price, {"from": offeror})

    # create offer
    setup_offer(expired_offer)

    # turn off/on storing payment tokens in escrow
    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(not escrow_offer_payment_tokens)

    # cancel offer
    erc721_marketplace_mock.cancelOffer(erc721_collection_mock, erc721_collection_mint_with_approval, {'from': offeror})

    # check if payment tokens were returned from escrow
    assert payment_token.balanceOf(erc721_marketplace_mock.address) == initial_marketplace_balance
    assert payment_token.balanceOf(offeror.address) == initial_offeror_balance

    # check offer existence
    offer = erc721_marketplace_mock.getOffer(erc721_collection_mock, erc721_collection_mint_with_approval, offeror)
    assert offer[0] == ZERO_ADDRESS
    assert offer[1] == ZERO_ADDRESS
    assert offer[2] == 0
    assert offer[3] == 0


def test_canceling_non_existent_offer(
        erc721_marketplace_mock,
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        offeror
):
    """Test canceling offer that does NOT exist"""
    # cancel offer
    with reverts("ERC721Marketplace: offer does not exists"):
        erc721_marketplace_mock.cancelOffer(
            erc721_collection_mock,
            erc721_collection_mint_with_approval,
            {'from': offeror}
        )


@pytest.mark.parametrize('escrow_offer_payment_tokens', [True, False])
def test_accept_offer(
        erc721_marketplace_mock,
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        owner,
        token_owner,
        offeror,
        setup_offer,
        escrow_offer_payment_tokens
):
    """Test accepting an offer"""
    initial_platform_balance = payment_token.balanceOf(owner.address)
    initial_owner_balance = payment_token.balanceOf(token_owner.address)
    initial_offeror_balance = payment_token.balanceOf(offeror.address)
    fee_amount = math.floor(OfferParams.price * erc721_marketplace_mock.getOfferFee() / 1000)

    # turn on/off storing payment tokens in escrow
    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_offer_payment_tokens)

    # set allowance
    payment_token.approve(erc721_marketplace_mock, OfferParams.price, {"from": offeror})

    token_id = setup_offer()

    tx = erc721_marketplace_mock.acceptOffer(erc721_collection_mock, token_id, offeror, {"from": token_owner})

    # check balances
    assert payment_token.balanceOf(owner.address) == initial_platform_balance + fee_amount
    assert payment_token.balanceOf(token_owner.address) == initial_owner_balance + (OfferParams.price - fee_amount)
    assert payment_token.balanceOf(offeror.address) == initial_offeror_balance - OfferParams.price

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
    offer = erc721_marketplace_mock.getOffer(erc721_collection_mock, erc721_collection_mint_with_approval, offeror)
    assert offer[0] == ZERO_ADDRESS
    assert offer[1] == ZERO_ADDRESS
    assert offer[2] == 0
    assert offer[3] == 0

    # check listing existence
    listing = erc721_marketplace_mock.getListing(erc721_collection_mock, erc721_collection_mint_with_approval)
    assert listing[0] == ZERO_ADDRESS
    assert listing[1] == ZERO_ADDRESS
    assert listing[2] == 0
    assert listing[3] == 0


@pytest.mark.parametrize('escrow_offer_payment_tokens', [True, False])
def test_accept_nonexistent_offer(
        erc721_marketplace_mock,
        erc721_collection_mock,
        token_owner,
        offeror,
        escrow_offer_payment_tokens
):
    """Test accepting an offer that doesn't exist"""
    # turn on/off storing payment tokens in escrow
    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_offer_payment_tokens)

    token_id = 1

    # try to accept offer
    with reverts("ERC721Marketplace: offer does not exists"):
        erc721_marketplace_mock.acceptOffer(erc721_collection_mock, token_id, offeror, {"from": token_owner})


@pytest.mark.parametrize('escrow_offer_payment_tokens', [True, False])
def test_accept_expired_offer(
        erc721_marketplace_mock,
        erc721_collection_mock,
        offeror,
        token_owner,
        payment_token,
        setup_offer,
        escrow_offer_payment_tokens
):
    """Test accepting an offer that doesn't exist"""
    # turn on/off storing payment tokens in escrow
    erc721_marketplace_mock.updateEscrowOfferPaymentTokens(escrow_offer_payment_tokens)

    # set allowance
    payment_token.approve(erc721_marketplace_mock, OfferParams.price, {"from": offeror})

    token_id = setup_offer(OfferStatus.EXPIRED)

    # try to accept offer
    with reverts("ERC721Marketplace: offer is expired"):
        erc721_marketplace_mock.acceptOffer(erc721_collection_mock, token_id, offeror, {"from": token_owner})


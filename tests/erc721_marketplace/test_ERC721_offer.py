import pytest
from dataclasses import dataclass
from brownie import reverts, Wei, chain
from utils.constants import WFTM_TOKEN


@dataclass(frozen=True)
class OfferParams:
    price: int = 100
    expiration_time: int = chain.time() + (60 * 60)  # start listing at current time + 1 hour


@pytest.fixture(scope="module")
def payment_token(erc20_mock):
    return erc20_mock


@pytest.fixture(scope="module")
def token_owner(user):
    return user


@pytest.fixture(scope="module")
def offeror(user_2):
    return user_2


@pytest.fixture(scope="function")
def minted_and_approved_token_id(erc721_collection_mock, erc721_collection_mint, erc721_marketplace, token_owner):
    # mint token and set approval
    token_id = erc721_collection_mint(token_owner)
    erc721_collection_mock.approve(erc721_marketplace, token_id, {'from': token_owner})

    return token_id


def test_create_offer(payment_token, minted_and_approved_token_id, erc721_marketplace, erc721_collection_mock, offeror):
    """Test valid offer creation"""
    # create offer
    tx = erc721_marketplace.createOffer(
        erc721_collection_mock,
        minted_and_approved_token_id,
        payment_token,
        OfferParams.price,
        OfferParams.expiration_time,
        {'from': offeror}
    )

    # assert offer was created with correct data
    offer = erc721_marketplace.getOffer(erc721_collection_mock, minted_and_approved_token_id)
    assert offer[0] == payment_token.address
    assert offer[1] == offeror
    assert offer[2] == OfferParams.price
    assert offer[3] == OfferParams.expiration_time

    # check event
    assert tx.events["OfferCreated"] is not None
    assert tx.events["OfferCreated"]["offeror"] == offeror
    assert tx.events["OfferCreated"]["nftAddress"] == erc721_collection_mock
    assert tx.events["OfferCreated"]["tokenId"] == minted_and_approved_token_id
    assert tx.events["OfferCreated"]["paymentToken"] == payment_token.address
    assert tx.events["OfferCreated"]["price"] == OfferParams.price
    assert tx.events["OfferCreated"]["expirationTime"] == OfferParams.expiration_time


def test_create_offer_invalid_payment_token(erc721_marketplace, erc721_collection_mock, offeror):
    """Test offer creation with invalid payment token"""
    token_id = 1
    payment_token = '0x0000000000000000000000000000000000000000'

    # try to create offer
    with reverts('MarketplaceBase: payment token is not enabled'):
        erc721_marketplace.createOffer(
            erc721_collection_mock,
            token_id,
            payment_token,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )


def test_create_offer_invalid_nft_contract(erc721_marketplace, payment_token, erc1155_collection_mock, offeror):
    """Test offer creation with invalid nft contract address (not ERC721 standard)"""
    token_id = 1

    # try to create offer
    with reverts('ERC721Marketplace: NFT is not ERC721'):
        erc721_marketplace.createOffer(
            erc1155_collection_mock,
            token_id,
            payment_token,
            OfferParams.price,
            OfferParams.expiration_time,
            {'from': offeror}
        )


def test_create_offer_invalid_expiration_time(
        minted_and_approved_token_id,
        erc721_marketplace,
        payment_token,
        erc721_collection_mock,
        offeror
):
    """Test offer creation with invalid expiration time (in the past)"""
    expiration_time = chain.time() - (60 * 60)  # offer expired 1 hour ago

    # try to create offer
    with reverts('MarketplaceBase: invalid expiration time'):
        erc721_marketplace.createOffer(
            erc721_collection_mock,
            minted_and_approved_token_id,
            payment_token,
            OfferParams.price,
            expiration_time,
            {'from': offeror}
        )

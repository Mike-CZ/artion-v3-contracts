import pytest
from dataclasses import dataclass
from brownie import reverts, Wei, chain
from utils.constants import WFTM_TOKEN, TOMB_TOKEN


@dataclass(frozen=True)
class ListingParams:
    token_price: int = Wei('1 ether')
    start_time: int = chain.time() + (60 * 60)  # start listing at current time + 1 hour
    pay_token: str = WFTM_TOKEN


@pytest.fixture(scope="function")
def minted_and_approved_token_id(erc721_collection_mock, erc721_collection_mint, erc721_marketplace, user):
    # mint token and set approval
    token_id = erc721_collection_mint(user)
    erc721_collection_mock.approve(erc721_marketplace, token_id, {'from': user})

    return token_id


def test_create_listing(minted_and_approved_token_id, erc721_marketplace, erc721_collection_mock, user):
    """Test listing creation"""
    # create listing
    tx = erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        ListingParams.pay_token,
        ListingParams.token_price,
        ListingParams.start_time,
        {'from': user}
    )

    # assert token has been transferred into escrow
    assert erc721_collection_mock.ownerOf(minted_and_approved_token_id) == erc721_marketplace

    # assert listing was created with correct data
    listing = erc721_marketplace.getListing(erc721_collection_mock, minted_and_approved_token_id)
    assert listing[0] == user
    assert listing[1] == ListingParams.pay_token
    assert listing[2] == ListingParams.token_price
    assert listing[3] == ListingParams.start_time

    # check event
    assert tx.events["ItemListingCreated"] is not None
    assert tx.events["ItemListingCreated"]["owner"] == user
    assert tx.events["ItemListingCreated"]["nft"] == erc721_collection_mock
    assert tx.events["ItemListingCreated"]["tokenId"] == minted_and_approved_token_id
    assert tx.events["ItemListingCreated"]["paymentToken"] == ListingParams.pay_token
    assert tx.events["ItemListingCreated"]["price"] == ListingParams.token_price
    assert tx.events["ItemListingCreated"]["startingTime"] == ListingParams.start_time


def test_list_already_listed_token(minted_and_approved_token_id, erc721_marketplace, erc721_collection_mock, user):
    """Test listing already listed token"""
    # create listing
    erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        ListingParams.pay_token,
        ListingParams.token_price,
        ListingParams.start_time,
        {'from': user}
    )

    # create new listing with same token
    with reverts('ERC721Marketplace: NFT is already listed'):
        erc721_marketplace.createListing(
            erc721_collection_mock,
            minted_and_approved_token_id,
            user,
            ListingParams.pay_token,
            ListingParams.token_price,
            ListingParams.start_time,
            {'from': user}
        )


def test_listing_not_erc721(erc721_marketplace, erc1155_collection_mock, erc721_collection_mint, user):
    """Test listing ERC1155 token in ERC721 marketplace"""
    token_id = 1

    with reverts('ERC721Marketplace: NFT is not ERC721'):
        erc721_marketplace.createListing(
            erc1155_collection_mock,
            token_id,
            user,
            ListingParams.pay_token,
            ListingParams.token_price,
            ListingParams.start_time,
            {'from': user}
        )


def test_listing_as_not_owner(minted_and_approved_token_id, erc721_marketplace, erc721_collection_mock, user, user_2):
    """Test listing token as not owner"""
    with reverts('ERC721Marketplace: does not own the token'):
        erc721_marketplace.createListing(
            erc721_collection_mock,
            minted_and_approved_token_id,
            user,
            ListingParams.pay_token,
            ListingParams.token_price,
            ListingParams.start_time,
            {'from': user_2}
        )


def test_listing_not_approved_token(erc721_marketplace, erc721_collection_mock, erc721_collection_mint, user):
    """Test listing now approved token"""
    token_id = erc721_collection_mint(user)

    with reverts('ERC721Marketplace: not approved for the token'):
        erc721_marketplace.createListing(
            erc721_collection_mock,
            token_id,
            user,
            ListingParams.pay_token,
            ListingParams.token_price,
            ListingParams.start_time,
            {'from': user}
        )


def test_update_listing(minted_and_approved_token_id, erc721_marketplace, erc721_collection_mock, user):
    """Test listing update"""
    # create listing
    erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        ListingParams.pay_token,
        ListingParams.token_price,
        ListingParams.start_time,
        {'from': user}
    )

    # update listing
    tx = erc721_marketplace.updateListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        TOMB_TOKEN,
        Wei('2 ether'),
        {'from': user}
    )

    # assert listing was updated with correct data
    listing = erc721_marketplace.getListing(erc721_collection_mock, minted_and_approved_token_id)
    assert listing[1] == TOMB_TOKEN
    assert listing[2] == Wei('2 ether')

    # check event
    assert tx.events["ItemListingUpdated"] is not None
    assert tx.events["ItemListingUpdated"]["owner"] == user
    assert tx.events["ItemListingUpdated"]["nft"] == erc721_collection_mock
    assert tx.events["ItemListingUpdated"]["tokenId"] == minted_and_approved_token_id
    assert tx.events["ItemListingUpdated"]["newPaymentToken"] == TOMB_TOKEN
    assert tx.events["ItemListingUpdated"]["newPrice"] == Wei('2 ether')


def test_update_listing_as_not_owner(minted_and_approved_token_id, erc721_marketplace, erc721_collection_mock, user, user_2):
    """Test listing update as not owner of NFT"""
    # create listing
    erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        ListingParams.pay_token,
        ListingParams.token_price,
        ListingParams.start_time,
        {'from': user}
    )

    # update listing
    with reverts('ERC721Marketplace: does not own the token'):
        erc721_marketplace.updateListing(
            erc721_collection_mock,
            minted_and_approved_token_id,
            TOMB_TOKEN,
            Wei('2 ether'),
            {'from': user_2}
        )


def test_update_not_listed(minted_and_approved_token_id, erc721_marketplace, erc721_collection_mock, user):
    """Test updating non-existent listing"""
    # update non-existent listing
    with reverts('ERC721Marketplace: NFT is not listed'):
        erc721_marketplace.updateListing(
            erc721_collection_mock,
            minted_and_approved_token_id,
            TOMB_TOKEN,
            Wei('2 ether'),
            {'from': user}
        )


def test_cancel_listing(minted_and_approved_token_id, erc721_marketplace, erc721_collection_mock, user):
    """Test listing cancellation"""
    # create listing
    erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        ListingParams.pay_token,
        ListingParams.token_price,
        ListingParams.start_time,
        {'from': user}
    )

    # cancel listing
    tx = erc721_marketplace.cancelListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        {'from': user}
    )

    # assert listing was canceled
    listing = erc721_marketplace.getListing(erc721_collection_mock, minted_and_approved_token_id)
    assert listing[0] == '0x0000000000000000000000000000000000000000'
    assert listing[1] == '0x0000000000000000000000000000000000000000'
    assert listing[2] == 0
    assert listing[3] == 0

    # check event
    assert tx.events["ItemListingCanceled"] is not None
    assert tx.events["ItemListingCanceled"]["owner"] == user
    assert tx.events["ItemListingCanceled"]["nft"] == erc721_collection_mock
    assert tx.events["ItemListingCanceled"]["tokenId"] == minted_and_approved_token_id


def test_cancel_not_listed(minted_and_approved_token_id, erc721_marketplace, erc721_collection_mock, user):
    """Test cancelling non-existent listing"""
    # cancel non-existent listing
    with reverts('ERC721Marketplace: NFT is not listed'):
        erc721_marketplace.cancelListing(
            erc721_collection_mock,
            minted_and_approved_token_id,
            {'from': user}
        )

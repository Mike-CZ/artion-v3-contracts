import pytest
import math
from dataclasses import dataclass
from brownie import reverts, Wei, chain
from utils.constants import WFTM_TOKEN, TOMB_TOKEN


@dataclass(frozen=True)
class ListingParams:
    price: int = 100
    start_time: int = chain.time() + (60 * 60)  # start listing at current time + 1 hour


@pytest.fixture(scope="module")
def payment_token(erc20_mock):
    return erc20_mock


@pytest.fixture(scope="function")
def minted_and_approved_token_id(erc721_collection_mock, erc721_collection_mint, erc721_marketplace, user):
    # mint token and set approval
    token_id = erc721_collection_mint(user)
    erc721_collection_mock.approve(erc721_marketplace, token_id, {'from': user})

    return token_id


def test_create_listing(payment_token, minted_and_approved_token_id, erc721_marketplace, erc721_collection_mock, user):
    """Test listing creation"""
    # create listing
    tx = erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': user}
    )

    # assert token has been transferred into escrow
    assert erc721_collection_mock.ownerOf(minted_and_approved_token_id) == erc721_marketplace

    # assert listing was created with correct data
    listing = erc721_marketplace.getListing(erc721_collection_mock, minted_and_approved_token_id)
    assert listing[0] == user
    assert listing[1] == payment_token.address
    assert listing[2] == ListingParams.price
    assert listing[3] == ListingParams.start_time

    # check event
    assert tx.events["ListingCreated"] is not None
    assert tx.events["ListingCreated"]["nftOwner"] == user
    assert tx.events["ListingCreated"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ListingCreated"]["tokenId"] == minted_and_approved_token_id
    assert tx.events["ListingCreated"]["paymentToken"] == payment_token.address
    assert tx.events["ListingCreated"]["price"] == ListingParams.price
    assert tx.events["ListingCreated"]["startingTime"] == ListingParams.start_time


def test_list_already_listed_token(
        payment_token,
        minted_and_approved_token_id,
        erc721_marketplace,
        erc721_collection_mock,
        user
):
    """Test listing already listed token"""
    # create listing
    erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': user}
    )

    # create new listing with same token
    with reverts('ERC721Marketplace: NFT is already listed'):
        erc721_marketplace.createListing(
            erc721_collection_mock,
            minted_and_approved_token_id,
            user,
            payment_token,
            ListingParams.price,
            ListingParams.start_time,
            {'from': user}
        )


def test_listing_not_erc721(payment_token, erc721_marketplace, erc1155_collection_mock, erc721_collection_mint, user):
    """Test listing ERC1155 token in ERC721 marketplace"""
    token_id = 1

    with reverts('ERC721Marketplace: NFT is not ERC721'):
        erc721_marketplace.createListing(
            erc1155_collection_mock,
            token_id,
            user,
            payment_token,
            ListingParams.price,
            ListingParams.start_time,
            {'from': user}
        )


def test_invalid_start_time(payment_token, erc721_marketplace, erc721_collection_mock, erc721_collection_mint, user):
    """Test listing with start time in the past"""
    token_id = 1

    with reverts('MarketplaceBase: invalid start time'):
        erc721_marketplace.createListing(
            erc721_collection_mock,
            token_id,
            user,
            payment_token,
            ListingParams.price,
            chain.time() - (60 * 60),  # start listing at current time - 1 hour,
            {'from': user}
        )


def test_listing_as_not_owner(
        payment_token,
        minted_and_approved_token_id,
        erc721_marketplace,
        erc721_collection_mock,
        user,
        user_2
):
    """Test listing token as not owner"""
    with reverts('ERC721Marketplace: does not own the token'):
        erc721_marketplace.createListing(
            erc721_collection_mock,
            minted_and_approved_token_id,
            user,
            payment_token,
            ListingParams.price,
            ListingParams.start_time,
            {'from': user_2}
        )


def test_listing_not_approved_token(
        payment_token,
        erc721_marketplace,
        erc721_collection_mock,
        erc721_collection_mint,
        user
):
    """Test listing now approved token"""
    token_id = erc721_collection_mint(user)

    with reverts('ERC721Marketplace: not approved for the token'):
        erc721_marketplace.createListing(
            erc721_collection_mock,
            token_id,
            user,
            payment_token,
            ListingParams.price,
            ListingParams.start_time,
            {'from': user}
        )


def test_update_listing(
        payment_token,
        minted_and_approved_token_id,
        erc721_marketplace,
        erc721_collection_mock,
        user
):
    """Test listing update"""
    # create listing
    erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': user}
    )

    # update listing
    updated_listing_price = ListingParams.price + 50

    tx = erc721_marketplace.updateListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        TOMB_TOKEN,
        updated_listing_price,
        {'from': user}
    )

    # assert listing was updated with correct data
    listing = erc721_marketplace.getListing(erc721_collection_mock, minted_and_approved_token_id)
    assert listing[1] == TOMB_TOKEN
    assert listing[2] == updated_listing_price

    # check event
    assert tx.events["ListingUpdated"] is not None
    assert tx.events["ListingUpdated"]["nftOwner"] == user
    assert tx.events["ListingUpdated"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ListingUpdated"]["tokenId"] == minted_and_approved_token_id
    assert tx.events["ListingUpdated"]["newPaymentToken"] == TOMB_TOKEN
    assert tx.events["ListingUpdated"]["newPrice"] == updated_listing_price


def test_update_listing_as_not_owner(
        payment_token,
        minted_and_approved_token_id,
        erc721_marketplace,
        erc721_collection_mock,
        user,
        user_2
):
    """Test listing update as not owner of NFT"""
    # create listing
    erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        payment_token,
        ListingParams.price,
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


def test_cancel_listing(payment_token, minted_and_approved_token_id, erc721_marketplace, erc721_collection_mock, user):
    """Test listing cancellation"""
    # create listing
    erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': user}
    )

    # cancel listing
    tx = erc721_marketplace.cancelListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        {'from': user}
    )

    # assert token has been returned from escrow to original owner
    assert erc721_collection_mock.ownerOf(minted_and_approved_token_id) == user

    # assert listing was canceled
    listing = erc721_marketplace.getListing(erc721_collection_mock, minted_and_approved_token_id)
    assert listing[0] == '0x0000000000000000000000000000000000000000'
    assert listing[1] == '0x0000000000000000000000000000000000000000'
    assert listing[2] == 0
    assert listing[3] == 0

    # check event
    assert tx.events["ListingCanceled"] is not None
    assert tx.events["ListingCanceled"]["nftOwner"] == user
    assert tx.events["ListingCanceled"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ListingCanceled"]["tokenId"] == minted_and_approved_token_id


def test_cancel_listing_as_not_owner(
        payment_token,
        minted_and_approved_token_id,
        erc721_marketplace,
        erc721_collection_mock,
        user,
        user_2
):
    """Test listing cancelling as not owner of NFT"""
    # create listing
    erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': user}
    )

    # cancel listing
    with reverts('ERC721Marketplace: does not own the token'):
        erc721_marketplace.cancelListing(
            erc721_collection_mock,
            minted_and_approved_token_id,
            {'from': user_2}
        )


def test_cancel_not_listed(minted_and_approved_token_id, erc721_marketplace, erc721_collection_mock, user):
    """Test cancelling non-existent listing"""
    # cancel non-existent listing
    with reverts('ERC721Marketplace: NFT is not listed'):
        erc721_marketplace.cancelListing(
            erc721_collection_mock,
            minted_and_approved_token_id,
            {'from': user}
        )


def test_buy_listed_nft(
        payment_token,
        minted_and_approved_token_id,
        erc721_marketplace,
        erc721_collection_mock,
        owner,
        user,
        user_2
):
    """Test valid buying process"""

    platform_initial_balance = payment_token.balanceOf(owner)
    token_owner_initial_balance = payment_token.balanceOf(user)
    buyer_initial_balance = payment_token.balanceOf(user_2)

    # create listing
    erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        payment_token,
        ListingParams.price,
        chain.time(),
        {'from': user}
    )

    # set allowance
    payment_token.approve(erc721_marketplace, ListingParams.price, {"from": user_2})

    # buy listed NFT
    tx = erc721_marketplace.buyListedItem(
        erc721_collection_mock,
        minted_and_approved_token_id,
        payment_token,
        {"from": user_2}
    )

    platform_balance = payment_token.balanceOf(owner)
    token_owner_balance = payment_token.balanceOf(user)
    buyer_balance = payment_token.balanceOf(user_2)
    fee_amount = math.floor(ListingParams.price * erc721_marketplace.getListingFee() / 1000)

    # check balances
    assert platform_balance == platform_initial_balance + fee_amount
    assert token_owner_balance == token_owner_initial_balance + (ListingParams.price - fee_amount)
    assert buyer_balance == buyer_initial_balance - ListingParams.price

    # check NFT owner
    assert erc721_collection_mock.ownerOf(minted_and_approved_token_id) == user_2

    # check event
    assert tx.events["ListedItemSold"] is not None
    assert tx.events["ListedItemSold"]["seller"] == user
    assert tx.events["ListedItemSold"]["buyer"] == user_2
    assert tx.events["ListedItemSold"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ListedItemSold"]["tokenId"] == minted_and_approved_token_id
    assert tx.events["ListedItemSold"]["price"] == ListingParams.price
    assert tx.events["ListedItemSold"]["paymentToken"] == payment_token

    # check Listing removal
    listing = erc721_marketplace.getListing(erc721_collection_mock, minted_and_approved_token_id)
    assert listing[0] == '0x0000000000000000000000000000000000000000'
    assert listing[1] == '0x0000000000000000000000000000000000000000'
    assert listing[2] == 0
    assert listing[3] == 0


def test_buy_invalid_collection_address(payment_token, minted_and_approved_token_id, erc721_marketplace, user):
    """Test buying listing with invalid NFT contract address"""
    # buy NOT listed with invalid NFT contract address
    with reverts('ERC721Marketplace: NFT is not listed'):
        erc721_marketplace.buyListedItem(
            '0x0000000000000000000000000000000000000000',
            minted_and_approved_token_id,
            payment_token,
            {"from": user}
        )


def test_buy_not_listed(payment_token, erc721_collection_mock, minted_and_approved_token_id, erc721_marketplace, user):
    """Test buying NOT listed NFT"""
    token_id = 1

    # buy NOT listed NFT
    with reverts('ERC721Marketplace: NFT is not listed'):
        erc721_marketplace.buyListedItem(
            erc721_collection_mock,
            token_id,
            payment_token,
            {"from": user}
        )


def test_buy_listed_token_before_start_time(
        payment_token,
        minted_and_approved_token_id,
        erc721_marketplace,
        erc721_collection_mock,
        owner,
        user,
        user_2
):
    """Test buying listed nft before listing starts"""
    # create listing
    erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': user}
    )

    # set allowance
    payment_token.approve(erc721_marketplace, ListingParams.price, {"from": user_2})

    # try buying listed NFT
    with reverts('MarketplaceBase: listing has not started yet'):
        erc721_marketplace.buyListedItem(
            erc721_collection_mock,
            minted_and_approved_token_id,
            payment_token,
            {"from": user_2}
        )


def test_buy_listed_nft_with_invalid_pay_token(
        payment_token,
        minted_and_approved_token_id,
        erc721_marketplace,
        erc721_collection_mock,
        owner,
        user,
        user_2
):
    """Test buying listed nft with other payment token"""
    # create listing
    erc721_marketplace.createListing(
        erc721_collection_mock,
        minted_and_approved_token_id,
        user,
        payment_token,
        ListingParams.price,
        chain.time(),
        {'from': user}
    )

    # set allowance
    payment_token.approve(erc721_marketplace, ListingParams.price, {"from": user_2})

    # try buying listed NFT
    with reverts('ERC721Marketplace: invalid payment token'):
        erc721_marketplace.buyListedItem(
            erc721_collection_mock,
            minted_and_approved_token_id,
            WFTM_TOKEN,
            {"from": user_2}
        )

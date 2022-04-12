import pytest
import math
from dataclasses import dataclass
from brownie import reverts, Wei, chain, ZERO_ADDRESS
from utils.constants import WFTM_TOKEN, TOMB_TOKEN


@dataclass(frozen=True)
class ListingParams:
    price: int = 100
    start_time: int = chain.time() + (60 * 60)  # start listing at current time + 1 hour


def test_create_listing(payment_token, erc721_collection_mint_with_approval, erc721_marketplace_mock, erc721_collection_mock, user):
    """Test listing creation"""
    # create listing
    tx = erc721_marketplace_mock.createListing(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': user}
    )

    # assert token has been transferred into escrow
    assert erc721_collection_mock.ownerOf(erc721_collection_mint_with_approval) == erc721_marketplace_mock

    # assert listing was created with correct data
    listing = erc721_marketplace_mock.getListing(erc721_collection_mock, erc721_collection_mint_with_approval)
    assert listing[0] == user
    assert listing[1] == payment_token.address
    assert listing[2] == ListingParams.price
    assert listing[3] == ListingParams.start_time

    # check event
    assert tx.events["ERC721ListingCreated"] is not None
    assert tx.events["ERC721ListingCreated"]["nftOwner"] == user
    assert tx.events["ERC721ListingCreated"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ERC721ListingCreated"]["tokenId"] == erc721_collection_mint_with_approval
    assert tx.events["ERC721ListingCreated"]["paymentToken"] == payment_token.address
    assert tx.events["ERC721ListingCreated"]["price"] == ListingParams.price
    assert tx.events["ERC721ListingCreated"]["startingTime"] == ListingParams.start_time


def test_list_already_listed_token(
        payment_token,
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        erc721_collection_mock,
        user
):
    """Test listing already listed token"""
    # create listing
    erc721_marketplace_mock.createListing(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': user}
    )

    # create new listing with same token
    with reverts('ERC721Marketplace: NFT is already listed'):
        erc721_marketplace_mock.createListing(
            erc721_collection_mock,
            erc721_collection_mint_with_approval,
            payment_token,
            ListingParams.price,
            ListingParams.start_time,
            {'from': user}
        )


def test_listing_not_erc721(payment_token, erc721_marketplace_mock, erc1155_collection_mock, erc721_collection_mint, user):
    """Test listing ERC1155 token in ERC721 marketplace"""
    token_id = 1

    with reverts('ERC721Marketplace: NFT is not ERC721'):
        erc721_marketplace_mock.createListing(
            erc1155_collection_mock,
            token_id,
            payment_token,
            ListingParams.price,
            ListingParams.start_time,
            {'from': user}
        )


def test_invalid_start_time(payment_token, erc721_marketplace_mock, erc721_collection_mock, erc721_collection_mint, user):
    """Test listing with start time in the past"""
    token_id = 1

    with reverts('MarketplaceBase: invalid start time'):
        erc721_marketplace_mock.createListing(
            erc721_collection_mock,
            token_id,
            payment_token,
            ListingParams.price,
            chain.time() - (60 * 60),  # start listing at current time - 1 hour,
            {'from': user}
        )


def test_listing_as_not_owner(
        payment_token,
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        erc721_collection_mock,
        user,
        user_2
):
    """Test listing token as not owner"""
    with reverts('ERC721Marketplace: does not own the token'):
        erc721_marketplace_mock.createListing(
            erc721_collection_mock,
            erc721_collection_mint_with_approval,
            payment_token,
            ListingParams.price,
            ListingParams.start_time,
            {'from': user_2}
        )


def test_listing_not_approved_token(
        payment_token,
        erc721_marketplace_mock,
        erc721_collection_mock,
        erc721_collection_mint,
        user
):
    """Test listing now approved token"""
    token_id = erc721_collection_mint(user)

    with reverts('ERC721Marketplace: not approved for the token'):
        erc721_marketplace_mock.createListing(
            erc721_collection_mock,
            token_id,
            payment_token,
            ListingParams.price,
            ListingParams.start_time,
            {'from': user}
        )


def test_update_listing(
        payment_token,
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        erc721_collection_mock,
        user
):
    """Test listing update"""
    # create listing
    erc721_marketplace_mock.createListing(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': user}
    )

    # update listing
    updated_listing_price = ListingParams.price + 50

    tx = erc721_marketplace_mock.updateListing(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        TOMB_TOKEN,
        updated_listing_price,
        {'from': user}
    )

    # assert listing was updated with correct data
    listing = erc721_marketplace_mock.getListing(erc721_collection_mock, erc721_collection_mint_with_approval)
    assert listing[1] == TOMB_TOKEN
    assert listing[2] == updated_listing_price

    # check event
    assert tx.events["ERC721ListingUpdated"] is not None
    assert tx.events["ERC721ListingUpdated"]["nftOwner"] == user
    assert tx.events["ERC721ListingUpdated"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ERC721ListingUpdated"]["tokenId"] == erc721_collection_mint_with_approval
    assert tx.events["ERC721ListingUpdated"]["newPaymentToken"] == TOMB_TOKEN
    assert tx.events["ERC721ListingUpdated"]["newPrice"] == updated_listing_price


def test_update_listing_as_not_owner(
        payment_token,
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        erc721_collection_mock,
        user,
        user_2
):
    """Test listing update as not owner of NFT"""
    # create listing
    erc721_marketplace_mock.createListing(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': user}
    )

    # update listing
    with reverts('ERC721Marketplace: does not own the token'):
        erc721_marketplace_mock.updateListing(
            erc721_collection_mock,
            erc721_collection_mint_with_approval,
            TOMB_TOKEN,
            Wei('2 ether'),
            {'from': user_2}
        )


def test_update_not_listed(erc721_collection_mint_with_approval, erc721_marketplace_mock, erc721_collection_mock, user):
    """Test updating non-existent listing"""
    # update non-existent listing
    with reverts('ERC721Marketplace: NFT is not listed'):
        erc721_marketplace_mock.updateListing(
            erc721_collection_mock,
            erc721_collection_mint_with_approval,
            TOMB_TOKEN,
            Wei('2 ether'),
            {'from': user}
        )


def test_cancel_listing(
        payment_token,
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        erc721_collection_mock,
        user
):
    """Test listing cancellation"""
    # create listing
    erc721_marketplace_mock.createListing(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': user}
    )

    # cancel listing
    tx = erc721_marketplace_mock.cancelListing(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        {'from': user}
    )

    # assert token has been returned from escrow to original owner
    assert erc721_collection_mock.ownerOf(erc721_collection_mint_with_approval) == user

    # assert listing was canceled
    listing = erc721_marketplace_mock.getListing(erc721_collection_mock, erc721_collection_mint_with_approval)
    assert listing[0] == ZERO_ADDRESS
    assert listing[1] == ZERO_ADDRESS
    assert listing[2] == 0
    assert listing[3] == 0

    # check event
    assert tx.events["ERC721ListingCanceled"] is not None
    assert tx.events["ERC721ListingCanceled"]["nftOwner"] == user
    assert tx.events["ERC721ListingCanceled"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ERC721ListingCanceled"]["tokenId"] == erc721_collection_mint_with_approval


def test_cancel_listing_as_not_owner(
        payment_token,
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        erc721_collection_mock,
        user,
        user_2
):
    """Test listing cancelling as not owner of NFT"""
    # create listing
    erc721_marketplace_mock.createListing(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': user}
    )

    # cancel listing
    with reverts('ERC721Marketplace: does not own the token'):
        erc721_marketplace_mock.cancelListing(
            erc721_collection_mock,
            erc721_collection_mint_with_approval,
            {'from': user_2}
        )


def test_cancel_not_listed(erc721_collection_mint_with_approval, erc721_marketplace_mock, erc721_collection_mock, user):
    """Test cancelling non-existent listing"""
    # cancel non-existent listing
    with reverts('ERC721Marketplace: NFT is not listed'):
        erc721_marketplace_mock.cancelListing(
            erc721_collection_mock,
            erc721_collection_mint_with_approval,
            {'from': user}
        )


def test_buy_listed_nft(
        payment_token,
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
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
    erc721_marketplace_mock.createListing(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        ListingParams.price,
        chain.time(),
        {'from': user}
    )

    # set allowance
    payment_token.approve(erc721_marketplace_mock, ListingParams.price, {"from": user_2})

    # buy listed NFT
    tx = erc721_marketplace_mock.buyListedItem(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        {"from": user_2}
    )

    platform_balance = payment_token.balanceOf(owner)
    token_owner_balance = payment_token.balanceOf(user)
    buyer_balance = payment_token.balanceOf(user_2)
    fee_amount = math.floor(ListingParams.price * erc721_marketplace_mock.getListingFee() / 1000)

    # check balances
    assert platform_balance == platform_initial_balance + fee_amount
    assert token_owner_balance == token_owner_initial_balance + (ListingParams.price - fee_amount)
    assert buyer_balance == buyer_initial_balance - ListingParams.price

    # check NFT owner
    assert erc721_collection_mock.ownerOf(erc721_collection_mint_with_approval) == user_2

    # check event
    assert tx.events["ERC721ListedItemSold"] is not None
    assert tx.events["ERC721ListedItemSold"]["seller"] == user
    assert tx.events["ERC721ListedItemSold"]["buyer"] == user_2
    assert tx.events["ERC721ListedItemSold"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ERC721ListedItemSold"]["tokenId"] == erc721_collection_mint_with_approval
    assert tx.events["ERC721ListedItemSold"]["price"] == ListingParams.price
    assert tx.events["ERC721ListedItemSold"]["paymentToken"] == payment_token

    # check Listing removal
    listing = erc721_marketplace_mock.getListing(erc721_collection_mock, erc721_collection_mint_with_approval)
    assert listing[0] == ZERO_ADDRESS
    assert listing[1] == ZERO_ADDRESS
    assert listing[2] == 0
    assert listing[3] == 0


def test_buy_invalid_collection_address(
        payment_token,
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        user
):
    """Test buying listing with invalid NFT contract address"""
    # buy NOT listed with invalid NFT contract address
    with reverts('ERC721Marketplace: NFT is not listed'):
        erc721_marketplace_mock.buyListedItem(
            ZERO_ADDRESS,
            erc721_collection_mint_with_approval,
            payment_token,
            {"from": user}
        )


def test_buy_not_listed(
        payment_token,
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        user
):
    """Test buying NOT listed NFT"""
    token_id = 1

    # buy NOT listed NFT
    with reverts('ERC721Marketplace: NFT is not listed'):
        erc721_marketplace_mock.buyListedItem(
            erc721_collection_mock,
            token_id,
            payment_token,
            {"from": user}
        )


def test_buy_listed_token_before_start_time(
        payment_token,
        erc721_collection_mint_with_approval,
        erc721_marketplace_mock,
        erc721_collection_mock,
        owner,
        user,
        user_2
):
    """Test buying listed nft before listing starts"""
    # create listing
    erc721_marketplace_mock.createListing(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': user}
    )

    # set allowance
    payment_token.approve(erc721_marketplace_mock, ListingParams.price, {"from": user_2})

    # try buying listed NFT
    with reverts('MarketplaceBase: listing has not started yet'):
        erc721_marketplace_mock.buyListedItem(
            erc721_collection_mock,
            erc721_collection_mint_with_approval,
            payment_token,
            {"from": user_2}
        )


import pytest
import math
from enum import Enum
from dataclasses import dataclass
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable
from utils.helpers import calculate_offer_fee, calculate_royalty_fee
from brownie import reverts, Wei, chain, ZERO_ADDRESS
from utils.constants import WFTM_TOKEN, TOMB_TOKEN, ZOO_TOKEN


@dataclass(frozen=True)
class ListingParams:
    price: int = 100
    unit_price: int = 100
    start_time: int = chain.time() + (60 * 60)  # start listing at current time + 1 hour


@dataclass(frozen=True)
class RoyaltyParams:
    fraction: int = 1_000  # 10%


class ListingStatus(Enum):
    NOT_STARTED = 0
    STARTED = 1


@pytest.fixture(scope="session")
def seller(user: LocalAccount) -> LocalAccount:
    return user


@pytest.fixture(scope="session")
def buyer(user_2: LocalAccount) -> LocalAccount:
    return user_2


@pytest.fixture(scope="session")
def royalty_recipient(user_3: LocalAccount) -> LocalAccount:
    return user_3


def handle_listing_status(status: ListingStatus) -> None:
    if status is ListingStatus.STARTED:
        chain.sleep(ListingParams.start_time - chain.time())
        chain.mine()


@pytest.fixture(scope='module')
def setup_listing(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        royalty_registry: ProjectContract,
        royalty_recipient: LocalAccount,
        payment_token: ProjectContract,
        seller: LocalAccount
) -> Callable:
    def setup_listing_(status: ListingStatus = ListingStatus.STARTED) -> int:
        # mint token and set royalty
        token_id = erc721_collection_mock.mintAndGetTokenId(
            seller,
            '',
            royalty_recipient,
            RoyaltyParams.fraction
        ).return_value

        # create listing
        erc721_collection_mock.setApprovalForAll(erc721_marketplace_mock, True, {'from': seller})
        erc721_marketplace_mock.createListing(
            erc721_collection_mock,
            token_id,
            payment_token,
            ListingParams.price,
            ListingParams.start_time,
            {'from': seller}
        )

        # start listing if required
        handle_listing_status(status)

        return token_id
    return setup_listing_


def test_create_listing(
        payment_token: ProjectContract,
        erc721_collection_mint_with_approval: int,
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test listing creation"""
    # create listing
    tx = erc721_marketplace_mock.createListing(
        erc721_collection_mock,
        erc721_collection_mint_with_approval,
        payment_token,
        ListingParams.price,
        ListingParams.start_time,
        {'from': seller}
    )

    # assert token has been transferred into escrow
    assert erc721_collection_mock.ownerOf(erc721_collection_mint_with_approval) == erc721_marketplace_mock

    # assert listing was created with correct data
    listing = erc721_marketplace_mock.getListing(erc721_collection_mock, erc721_collection_mint_with_approval)
    assert listing[0] == seller
    assert listing[1] == payment_token.address
    assert listing[2] == ListingParams.price
    assert listing[3] == ListingParams.start_time

    # check event
    assert tx.events["ERC721ListingCreated"] is not None
    assert tx.events["ERC721ListingCreated"]["nftOwner"] == seller
    assert tx.events["ERC721ListingCreated"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ERC721ListingCreated"]["tokenId"] == erc721_collection_mint_with_approval
    assert tx.events["ERC721ListingCreated"]["paymentToken"] == payment_token.address
    assert tx.events["ERC721ListingCreated"]["price"] == ListingParams.price
    assert tx.events["ERC721ListingCreated"]["startingTime"] == ListingParams.start_time


def test_list_already_listed_token(
        payment_token: ProjectContract,
        erc721_collection_mint_with_approval: int,
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        seller: LocalAccount,
        setup_listing: Callable
) -> None:
    """Test listing already listed token"""
    # create listing
    token_id = setup_listing()

    # create new listing with same token
    with reverts('MarketplaceBase: listing exists'):
        erc721_marketplace_mock.createListing(
            erc721_collection_mock,
            token_id,
            payment_token,
            ListingParams.price,
            ListingParams.start_time,
            {'from': seller}
        )


def test_listing_not_erc721(
        payment_token: ProjectContract,
        erc721_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        erc721_collection_mint: Callable,
        seller: LocalAccount
) -> None:
    """Test listing ERC1155 token in ERC721 marketplace"""
    token_id = 1

    with reverts('ERC721Marketplace: NFT is not ERC721'):
        erc721_marketplace_mock.createListing(
            erc1155_collection_mock,
            token_id,
            payment_token,
            ListingParams.price,
            ListingParams.start_time,
            {'from': seller}
        )


def test_invalid_start_time(
        payment_token: ProjectContract,
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        erc721_collection_mint: Callable,
        seller: LocalAccount
) -> None:
    """Test listing with start time in the past"""
    token_id = 1

    with reverts('MarketplaceBase: invalid start time'):
        erc721_marketplace_mock.createListing(
            erc721_collection_mock,
            token_id,
            payment_token,
            ListingParams.price,
            chain.time() - (60 * 60),  # start listing at current time - 1 hour,
            {'from': seller}
        )


@pytest.mark.parametrize('new_payment_token', [TOMB_TOKEN, WFTM_TOKEN, ZOO_TOKEN])
def test_update_listing(
        payment_token: ProjectContract,
        setup_listing: Callable,
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        seller: LocalAccount,
        new_payment_token: str
) -> None:
    """Test listing update"""
    # create listing
    token_id = setup_listing()

    # update listing
    updated_listing_price = ListingParams.price + 50

    tx = erc721_marketplace_mock.updateListing(
        erc721_collection_mock,
        token_id,
        new_payment_token,
        updated_listing_price,
        {'from': seller}
    )

    # assert listing was updated with correct data
    listing = erc721_marketplace_mock.getListing(erc721_collection_mock, token_id)
    assert listing[1] == new_payment_token
    assert listing[2] == updated_listing_price

    # check event
    assert tx.events["ERC721ListingUpdated"] is not None
    assert tx.events["ERC721ListingUpdated"]["nftOwner"] == seller
    assert tx.events["ERC721ListingUpdated"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ERC721ListingUpdated"]["tokenId"] == token_id
    assert tx.events["ERC721ListingUpdated"]["newPaymentToken"] == new_payment_token
    assert tx.events["ERC721ListingUpdated"]["newPrice"] == updated_listing_price


def test_update_listing_as_not_owner(
        payment_token: ProjectContract,
        setup_listing: Callable,
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        seller: LocalAccount,
        buyer: LocalAccount
) -> None:
    """Test listing update as not owner of NFT"""
    # create listing
    token_id = setup_listing()

    # update listing
    with reverts('MarketplaceBase: not owner'):
        erc721_marketplace_mock.updateListing(
            erc721_collection_mock,
            token_id,
            TOMB_TOKEN,
            Wei('2 ether'),
            {'from': buyer}
        )


def test_update_not_listed(
        erc721_collection_mint_with_approval: int,
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test updating non-existent listing"""
    # update non-existent listing
    with reverts('MarketplaceBase: listing not exists'):
        erc721_marketplace_mock.updateListing(
            erc721_collection_mock,
            erc721_collection_mint_with_approval,
            TOMB_TOKEN,
            Wei('2 ether'),
            {'from': seller}
        )


def test_cancel_listing(
        payment_token: ProjectContract,
        setup_listing: Callable,
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test listing cancellation"""
    # create listing
    token_id = setup_listing()

    # cancel listing
    tx = erc721_marketplace_mock.cancelListing(
        erc721_collection_mock,
        token_id,
        {'from': seller}
    )

    # assert token has been returned from escrow to original owner
    assert erc721_collection_mock.ownerOf(token_id) == seller

    # assert listing was canceled
    listing = erc721_marketplace_mock.getListing(erc721_collection_mock, token_id)
    assert listing[0] == ZERO_ADDRESS
    assert listing[1] == ZERO_ADDRESS
    assert listing[2] == 0
    assert listing[3] == 0

    # check event
    assert tx.events["ERC721ListingCanceled"] is not None
    assert tx.events["ERC721ListingCanceled"]["nftOwner"] == seller
    assert tx.events["ERC721ListingCanceled"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ERC721ListingCanceled"]["tokenId"] == token_id


def test_cancel_listing_as_not_owner(
        payment_token: ProjectContract,
        setup_listing: Callable,
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        seller: LocalAccount,
        buyer: LocalAccount
) -> None:
    """Test listing cancelling as not owner of NFT"""
    # create listing
    token_id = setup_listing()

    # cancel listing
    with reverts('MarketplaceBase: not owner'):
        erc721_marketplace_mock.cancelListing(
            erc721_collection_mock,
            token_id,
            {'from': buyer}
        )


def test_cancel_not_listed(
        erc721_collection_mint_with_approval: int,
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test cancelling non-existent listing"""
    # cancel non-existent listing
    with reverts('MarketplaceBase: listing not exists'):
        erc721_marketplace_mock.cancelListing(
            erc721_collection_mock,
            erc721_collection_mint_with_approval,
            {'from': seller}
        )


def test_buy_listed_nft(
        payment_token: ProjectContract,
        setup_listing: Callable,
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        owner: LocalAccount,
        seller: LocalAccount,
        buyer: LocalAccount,
        royalty_recipient: LocalAccount
) -> None:
    """Test valid buying process"""

    initial_platform_balance = payment_token.balanceOf(owner)
    initial_owner_balance = payment_token.balanceOf(seller)
    initial_buyer_balance = payment_token.balanceOf(buyer)
    initial_royalty_recipient_amount = payment_token.balanceOf(royalty_recipient)
    platform_fee = calculate_offer_fee(ListingParams.price, erc721_marketplace_mock.getOfferFee())
    royalty_fee = calculate_royalty_fee(ListingParams.price - platform_fee, RoyaltyParams.fraction)

    # create listing
    token_id = setup_listing()

    # set allowance
    payment_token.approve(erc721_marketplace_mock, ListingParams.price, {"from": buyer})

    # buy listed NFT
    tx = erc721_marketplace_mock.buyListedItem(
        erc721_collection_mock,
        token_id,
        ListingParams.price,
        payment_token,
        {"from": buyer}
    )

    # check balances
    assert payment_token.balanceOf(owner) == initial_platform_balance + platform_fee
    assert payment_token.balanceOf(seller) == initial_owner_balance + ListingParams.price - platform_fee - royalty_fee
    assert payment_token.balanceOf(buyer) == initial_buyer_balance - ListingParams.price
    assert payment_token.balanceOf(royalty_recipient) == initial_royalty_recipient_amount + royalty_fee

    # check NFT owner
    assert erc721_collection_mock.ownerOf(token_id) == buyer

    # check event
    assert tx.events["ERC721ListedItemSold"] is not None
    assert tx.events["ERC721ListedItemSold"]["seller"] == seller
    assert tx.events["ERC721ListedItemSold"]["buyer"] == buyer
    assert tx.events["ERC721ListedItemSold"]["nftAddress"] == erc721_collection_mock
    assert tx.events["ERC721ListedItemSold"]["tokenId"] == token_id
    assert tx.events["ERC721ListedItemSold"]["price"] == ListingParams.price
    assert tx.events["ERC721ListedItemSold"]["paymentToken"] == payment_token

    # check Listing removal
    listing = erc721_marketplace_mock.getListing(erc721_collection_mock, token_id)
    assert listing[0] == ZERO_ADDRESS
    assert listing[1] == ZERO_ADDRESS
    assert listing[2] == 0
    assert listing[3] == 0


def test_buy_invalid_collection_address(
        payment_token: ProjectContract,
        erc721_collection_mint_with_approval: int,
        erc721_marketplace_mock: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test buying listing with invalid NFT contract address"""
    # buy NOT listed with invalid NFT contract address
    with reverts('MarketplaceBase: listing not exists'):
        erc721_marketplace_mock.buyListedItem(
            ZERO_ADDRESS,
            erc721_collection_mint_with_approval,
            ListingParams.price,
            payment_token,
            {"from": seller}
        )


def test_buy_not_listed(
        payment_token: ProjectContract,
        erc721_collection_mock: ProjectContract,
        erc721_marketplace_mock: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test buying NOT listed NFT"""
    token_id = 1

    # buy NOT listed NFT
    with reverts('MarketplaceBase: listing not exists'):
        erc721_marketplace_mock.buyListedItem(
            erc721_collection_mock,
            token_id,
            ListingParams.price,
            payment_token,
            {"from": seller}
        )


def test_buy_listed_token_before_start_time(
        payment_token: ProjectContract,
        setup_listing: Callable,
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        owner: LocalAccount,
        seller: LocalAccount,
        buyer: LocalAccount
) -> None:
    """Test buying listed nft before listing starts"""
    # create listing
    token_id = setup_listing(ListingStatus.NOT_STARTED)

    # set allowance
    payment_token.approve(erc721_marketplace_mock, ListingParams.price, {"from": buyer})

    # try buying listed NFT
    with reverts('MarketplaceBase: listing has not started yet'):
        erc721_marketplace_mock.buyListedItem(
            erc721_collection_mock,
            token_id,
            ListingParams.price,
            payment_token,
            {"from": buyer}
        )


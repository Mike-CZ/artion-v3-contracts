import pytest
from enum import Enum
from dataclasses import dataclass
from brownie import reverts, chain
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable
from utils.structs import ERC1155Listing, Listing
from utils.constants import TOMB_TOKEN


@dataclass(frozen=True)
class ListingParams:
    token_id: int = 1_000_000
    token_amount: int = 50
    buy_token_amount: int = 10
    buy_amount_price: int = 100
    start_time: int = chain.time() + (60 * 60)  # start listing at current time + 1 hour
    listing_id: int = 1


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


def handle_listing_status(status: ListingStatus):
    if status is ListingStatus.STARTED:
        chain.sleep(ListingParams.start_time - chain.time())
        chain.mine()


@pytest.fixture(scope='module')
def setup_listing(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        royalty_registry: ProjectContract,
        royalty_recipient: LocalAccount,
        payment_token: ProjectContract,
        seller: LocalAccount
) -> Callable:
    def setup_listing_(status: ListingStatus = ListingStatus.STARTED) -> None:
        # mint token and set royalty
        erc1155_collection_mock.mint(seller, ListingParams.token_id, 100, '')
        royalty_registry.setTokenRoyalty(
            erc1155_collection_mock,
            ListingParams.token_id,
            royalty_recipient,
            RoyaltyParams.fraction,
            {'from': seller}
        )
        # create auction
        erc1155_collection_mock.setApprovalForAll(erc1155_marketplace_mock, True, {'from': seller})
        erc1155_marketplace_mock.createListingAndTransferToken(
            erc1155_collection_mock,
            ListingParams.token_id,
            seller,
            payment_token,
            ListingParams.token_amount,
            ListingParams.buy_token_amount,
            ListingParams.buy_amount_price,
            ListingParams.listing_id,
            ListingParams.start_time
        )
        # start listing if required
        handle_listing_status(status)
    return setup_listing_


def test_create_listing(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        erc1155_collection_mint_with_approval: Callable,
        payment_token: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test listing creation"""
    token_amount = 10
    buy_amount = 1
    price = 5
    listing_id = 9
    start_time = chain.time() + 30

    # mint token
    token_id = erc1155_collection_mint_with_approval(seller, token_amount)

    tx = erc1155_marketplace_mock.createListing(
        erc1155_collection_mock,
        token_id,
        payment_token,
        token_amount,
        buy_amount,
        price,
        listing_id,
        start_time,
        {'from': seller}
    )

    # validate listing successfully created
    data = erc1155_marketplace_mock.getListing(erc1155_collection_mock, token_id, seller, listing_id)
    listing = ERC1155Listing(Listing(*data[0]), *data[1:])

    assert listing.exists()
    assert listing.listing.owner == seller.address
    assert listing.listing.payment_token == payment_token.address
    assert listing.listing.price == price
    assert listing.listing.startingTime == start_time
    assert listing.totalTokenAmount == token_amount
    assert listing.buyTokenAmount == buy_amount
    assert listing.remainingTokenAmount == token_amount

    # assert token has been transferred into escrow
    assert erc1155_collection_mock.balanceOf(seller, token_id) == 0
    assert erc1155_collection_mock.balanceOf(erc1155_marketplace_mock, token_id) == token_amount

    # asset event emitted correctly
    assert tx.events['ERC1155ListingCreated'] is not None
    assert tx.events['ERC1155ListingCreated']['owner'] == seller.address
    assert tx.events['ERC1155ListingCreated']['nft'] == erc1155_collection_mock.address
    assert tx.events['ERC1155ListingCreated']['tokenId'] == token_id
    assert tx.events['ERC1155ListingCreated']['tokenAmount'] == token_amount
    assert tx.events['ERC1155ListingCreated']['buyTokenAmount'] == buy_amount
    assert tx.events['ERC1155ListingCreated']['buyAmountPrice'] == price
    assert tx.events['ERC1155ListingCreated']['listingId'] == listing_id
    assert tx.events['ERC1155ListingCreated']['paymentToken'] == payment_token.address
    assert tx.events['ERC1155ListingCreated']['startingTime'] == start_time


def test_update_listing(
        setup_listing: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        seller: LocalAccount
):
    """Test listing update"""
    setup_listing()

    updated_listing_price = ListingParams.buy_amount_price + 50

    tx = erc1155_marketplace_mock.updateListing(
        erc1155_collection_mock,
        ListingParams.token_id,
        ListingParams.listing_id,
        TOMB_TOKEN,
        updated_listing_price,
        {'from': seller}
    )

    # validate listing successfully created
    data = erc1155_marketplace_mock.getListing(
        erc1155_collection_mock, ListingParams.token_id, seller, ListingParams.listing_id
    )
    listing = ERC1155Listing(Listing(*data[0]), *data[1:])

    assert listing.exists()
    assert listing.listing.price == updated_listing_price
    assert listing.listing.payment_token == TOMB_TOKEN

    # check event
    assert tx.events["ERC1155ListingUpdated"] is not None
    assert tx.events["ERC1155ListingUpdated"]["owner"] == seller.address
    assert tx.events["ERC1155ListingUpdated"]["nft"] == erc1155_collection_mock.address
    assert tx.events["ERC1155ListingUpdated"]["tokenId"] == ListingParams.token_id
    assert tx.events["ERC1155ListingUpdated"]["listingId"] == ListingParams.listing_id
    assert tx.events["ERC1155ListingUpdated"]["newPaymentToken"] == TOMB_TOKEN
    assert tx.events["ERC1155ListingUpdated"]["newPrice"] == updated_listing_price


def test_cancel_listing(
        setup_listing: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        seller: LocalAccount
):
    """Test listing cancellation"""
    setup_listing()

    initial_seller_token_amount = erc1155_collection_mock.balanceOf(seller, ListingParams.token_id)
    initial_marketplace_token_amount = erc1155_collection_mock.balanceOf(
        erc1155_marketplace_mock, ListingParams.token_id
    )

    tx = erc1155_marketplace_mock.cancelListing(
        erc1155_collection_mock,
        ListingParams.token_id,
        ListingParams.listing_id,
        {'from': seller}
    )

    # assert tokens transferred
    assert erc1155_collection_mock.balanceOf(seller, ListingParams.token_id) \
           == initial_seller_token_amount + ListingParams.token_amount

    assert erc1155_collection_mock.balanceOf(
        erc1155_marketplace_mock, ListingParams.token_id
    ) == initial_marketplace_token_amount - ListingParams.token_amount

    # validate listing successfully deleted
    data = erc1155_marketplace_mock.getListing(
        erc1155_collection_mock, ListingParams.token_id, seller, ListingParams.listing_id
    )
    listing = ERC1155Listing(Listing(*data[0]), *data[1:])
    assert not listing.exists()

    # check event
    assert tx.events["ERC1155ListingCanceled"] is not None
    assert tx.events["ERC1155ListingCanceled"]["owner"] == seller.address
    assert tx.events["ERC1155ListingCanceled"]["nft"] == erc1155_collection_mock.address
    assert tx.events["ERC1155ListingCanceled"]["tokenId"] == ListingParams.token_id
    assert tx.events["ERC1155ListingCanceled"]["listingId"] == ListingParams.listing_id

import pytest
from enum import Enum
from dataclasses import dataclass
from brownie import reverts, chain, accounts
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable
from utils.structs import ERC1155Listing, Listing
from utils.constants import TOMB_TOKEN
from utils.helpers import calculate_listing_fee, calculate_royalty_fee
from brownie.test import given, strategy
from hypothesis import settings


@dataclass(frozen=True)
class ListingParams:
    token_id: int = 1_000_000
    token_amount: int = 50
    unit_size: int = 10
    unit_price: int = 100
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


def handle_listing_status(status: ListingStatus) -> None:
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
        # create listing
        erc1155_collection_mock.setApprovalForAll(erc1155_marketplace_mock, True, {'from': seller})
        erc1155_marketplace_mock.createListingAndTransferToken(
            erc1155_collection_mock,
            ListingParams.token_id,
            seller,
            payment_token,
            ListingParams.token_amount,
            ListingParams.unit_size,
            ListingParams.unit_price,
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
    unit_size = 1
    unit_price = 5
    listing_id = 9
    start_time = chain.time() + 30

    # mint token
    token_id = erc1155_collection_mint_with_approval(seller, token_amount)

    tx = erc1155_marketplace_mock.createListing(
        erc1155_collection_mock,
        token_id,
        payment_token,
        token_amount,
        unit_size,
        unit_price,
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
    assert listing.listing.price == unit_price
    assert listing.listing.starting_time == start_time
    assert listing.token_amount == token_amount
    assert listing.unit_size == unit_size
    assert listing.remaining_token_amount == token_amount

    # assert token has been transferred into escrow
    assert erc1155_collection_mock.balanceOf(seller, token_id) == 0
    assert erc1155_collection_mock.balanceOf(erc1155_marketplace_mock, token_id) == token_amount

    # asset event emitted correctly
    assert tx.events['ERC1155ListingCreated'] is not None
    assert tx.events['ERC1155ListingCreated']['owner'] == seller.address
    assert tx.events['ERC1155ListingCreated']['nft'] == erc1155_collection_mock.address
    assert tx.events['ERC1155ListingCreated']['tokenId'] == token_id
    assert tx.events['ERC1155ListingCreated']['tokenAmount'] == token_amount
    assert tx.events['ERC1155ListingCreated']['unitSize'] == unit_size
    assert tx.events['ERC1155ListingCreated']['unitPrice'] == unit_price
    assert tx.events['ERC1155ListingCreated']['listingId'] == listing_id
    assert tx.events['ERC1155ListingCreated']['paymentToken'] == payment_token.address
    assert tx.events['ERC1155ListingCreated']['startingTime'] == start_time


def test_create_listing_invalid_token_type(
        erc1155_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        erc721_collection_mint: Callable,
        payment_token: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test listing creation with invalid token type"""
    token_id = erc721_collection_mint(seller)
    with reverts('ERC1155Marketplace: NFT not ERC1155'):
        erc1155_marketplace_mock.createListing(
            erc721_collection_mock,
            token_id,
            payment_token,
            1,
            1,
            ListingParams.unit_price,
            ListingParams.listing_id,
            ListingParams.start_time,
            {'from': seller}
        )


def test_create_listing_invalid_time(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        erc1155_collection_mint_with_approval: Callable,
        payment_token: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test listing creation - invalid time"""
    token_id = erc1155_collection_mint_with_approval(seller, ListingParams.token_amount)
    with reverts('MarketplaceBase: invalid start time'):
        erc1155_marketplace_mock.createListing(
            erc1155_collection_mock,
            token_id,
            payment_token,
            ListingParams.token_amount,
            ListingParams.unit_size,
            ListingParams.unit_price,
            ListingParams.listing_id,
            chain.time() - 1,
            {'from': seller}
        )


@given(token_address=strategy('address'))
@settings(max_examples=1)
def test_create_listing_payment_token_not_enabled(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        erc1155_collection_mint_with_approval: Callable,
        seller: LocalAccount,
        token_address: LocalAccount
) -> None:
    """Test listing creation - payment token not enabled"""
    token_id = erc1155_collection_mint_with_approval(seller, ListingParams.token_amount)
    with reverts('MarketplaceBase: payment token is not enabled'):
        erc1155_marketplace_mock.createListing(
            erc1155_collection_mock,
            token_id,
            token_address,
            ListingParams.token_amount,
            ListingParams.unit_size,
            ListingParams.unit_price,
            ListingParams.listing_id,
            ListingParams.start_time,
            {'from': seller}
        )


def test_create_listing_already_exists(
        setup_listing: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test listing creation - already exists"""
    setup_listing()
    with reverts('MarketplaceBase: listing exists'):
        erc1155_marketplace_mock.createListing(
            erc1155_collection_mock,
            ListingParams.token_id,
            payment_token,
            ListingParams.token_amount,
            ListingParams.unit_size,
            ListingParams.unit_price,
            ListingParams.listing_id,
            ListingParams.start_time,
            {'from': seller}
        )


def test_create_listing_invalid_amount(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        erc1155_collection_mint_with_approval: Callable,
        payment_token: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test listing creation - invalid mount"""
    token_id = erc1155_collection_mint_with_approval(seller, 10)
    with reverts('ERC1155Marketplace: invalid amount'):
        erc1155_marketplace_mock.createListing(
            erc1155_collection_mock,
            token_id,
            payment_token,
            10,
            3,
            ListingParams.unit_price,
            ListingParams.listing_id,
            ListingParams.start_time,
            {'from': seller}
        )


def test_update_listing(
        setup_listing: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test listing update"""
    setup_listing()

    updated_listing_price = ListingParams.unit_price + 50

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


def test_update_listing_not_exists(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test updating process - token not listed"""
    with reverts('MarketplaceBase: listing not exists'):
        erc1155_marketplace_mock.updateListing(
            erc1155_collection_mock,
            ListingParams.token_id,
            ListingParams.listing_id,
            TOMB_TOKEN,
            ListingParams.unit_price,
            {'from': seller}
        )


@given(token_address=strategy('address'))
@settings(max_examples=1)
def test_update_listing_payment_token_not_enabled(
        setup_listing: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        seller: LocalAccount,
        token_address: LocalAccount
) -> None:
    """Test updating process - payment token not enabled"""
    setup_listing()

    with reverts('MarketplaceBase: payment token is not enabled'):
        erc1155_marketplace_mock.updateListing(
            erc1155_collection_mock,
            ListingParams.token_id,
            ListingParams.listing_id,
            token_address,
            ListingParams.unit_price,
            {'from': seller}
        )


def test_cancel_listing(
        setup_listing: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        seller: LocalAccount
) -> None:
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


def test_cancel_listing_not_exists(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test canceling process - token not listed"""
    with reverts('MarketplaceBase: listing not exists'):
        erc1155_marketplace_mock.cancelListing(
            erc1155_collection_mock,
            ListingParams.token_id,
            ListingParams.listing_id,
            {'from': seller}
        )


def test_buy_listed_nft(
        setup_listing: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        buyer: LocalAccount,
        seller: LocalAccount,
        royalty_recipient: LocalAccount
) -> None:
    """Test valid buying process"""
    setup_listing()

    fee_recipient = accounts.at(erc1155_marketplace_mock.getFeeRecipient())
    initial_fee_recipient_amount = payment_token.balanceOf(fee_recipient)
    initial_royalty_recipient_amount = payment_token.balanceOf(royalty_recipient)
    initial_seller_amount = payment_token.balanceOf(seller)
    initial_buyer_amount = payment_token.balanceOf(buyer)

    initial_buyer_token_amount = erc1155_collection_mock.balanceOf(buyer, ListingParams.token_id)
    initial_marketplace_token_amount = erc1155_collection_mock.balanceOf(
        erc1155_marketplace_mock, ListingParams.token_id
    )

    requested_units = ListingParams.token_amount / ListingParams.unit_size
    price = int(requested_units * ListingParams.unit_price)
    payment_token.approveInternal(buyer, erc1155_marketplace_mock, price)

    tx = erc1155_marketplace_mock.buyListedItem(
        erc1155_collection_mock,
        ListingParams.token_id,
        seller,
        ListingParams.listing_id,
        ListingParams.unit_price,
        payment_token,
        requested_units,
        {"from": buyer}
    )

    fee = calculate_listing_fee(price, erc1155_marketplace_mock.getListingFee())
    royalty_fee = calculate_royalty_fee(price - fee, RoyaltyParams.fraction)

    # assert payment tokens sent
    assert payment_token.balanceOf(fee_recipient) == initial_fee_recipient_amount + fee
    assert payment_token.balanceOf(royalty_recipient) == initial_royalty_recipient_amount + royalty_fee
    assert payment_token.balanceOf(seller) == initial_seller_amount + price - fee - royalty_fee
    assert payment_token.balanceOf(buyer) == initial_buyer_amount - price

    # assert tokens transferred
    assert erc1155_collection_mock.balanceOf(buyer, ListingParams.token_id) == \
           initial_buyer_token_amount + ListingParams.token_amount
    assert erc1155_collection_mock.balanceOf(erc1155_marketplace_mock, ListingParams.token_id) == \
           initial_marketplace_token_amount - ListingParams.token_amount

    # check event
    assert tx.events["ERC1155ListedItemSold"] is not None
    assert tx.events["ERC1155ListedItemSold"]["seller"] == seller.address
    assert tx.events["ERC1155ListedItemSold"]["buyer"] == buyer.address
    assert tx.events["ERC1155ListedItemSold"]["nft"] == erc1155_collection_mock.address
    assert tx.events["ERC1155ListedItemSold"]["tokenId"] == ListingParams.token_id
    assert tx.events["ERC1155ListedItemSold"]["amount"] == ListingParams.token_amount
    assert tx.events["ERC1155ListedItemSold"]["remainingAmount"] == 0
    assert tx.events["ERC1155ListedItemSold"]["price"] == price
    assert tx.events["ERC1155ListedItemSold"]["paymentToken"] == payment_token.address

    # validate listing successfully deleted
    data = erc1155_marketplace_mock.getListing(
        erc1155_collection_mock, ListingParams.token_id, seller, ListingParams.listing_id
    )
    listing = ERC1155Listing(Listing(*data[0]), *data[1:])
    assert not listing.exists()


def test_buy_listed_nft_partially(
        setup_listing: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        buyer: LocalAccount,
        seller: LocalAccount
) -> None:
    """Test valid partial buying process"""
    setup_listing()

    buy_units = 2
    token_amount = buy_units * ListingParams.unit_size
    price = buy_units * ListingParams.unit_price
    payment_token.approveInternal(buyer, erc1155_marketplace_mock, price)

    tx = erc1155_marketplace_mock.buyListedItem(
        erc1155_collection_mock,
        ListingParams.token_id,
        seller,
        ListingParams.listing_id,
        ListingParams.unit_price,
        payment_token,
        buy_units,
        {"from": buyer}
    )

    # validate listing successfully updated
    data = erc1155_marketplace_mock.getListing(
        erc1155_collection_mock, ListingParams.token_id, seller, ListingParams.listing_id
    )
    listing = ERC1155Listing(Listing(*data[0]), *data[1:])

    assert listing.exists()
    assert listing.remaining_token_amount == ListingParams.token_amount - token_amount

    # check event
    assert tx.events["ERC1155ListedItemSold"] is not None
    assert tx.events["ERC1155ListedItemSold"]["amount"] == token_amount
    assert tx.events["ERC1155ListedItemSold"]["remainingAmount"] == ListingParams.token_amount - token_amount
    assert tx.events["ERC1155ListedItemSold"]["price"] == price


def test_buy_listed_nft_not_listed(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        buyer: LocalAccount,
        seller: LocalAccount
) -> None:
    """Test buying process - token not listed"""
    with reverts('MarketplaceBase: listing not exists'):
        erc1155_marketplace_mock.buyListedItem(
            erc1155_collection_mock,
            ListingParams.token_id,
            seller,
            ListingParams.listing_id,
            ListingParams.unit_price,
            payment_token,
            ListingParams.token_amount / ListingParams.unit_size,
            {"from": buyer}
        )


def test_buy_listed_nft_not_started(
        setup_listing: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        buyer: LocalAccount,
        seller: LocalAccount
) -> None:
    """Test buying process - token not started"""
    setup_listing(status=ListingStatus.NOT_STARTED)

    with reverts('MarketplaceBase: listing not started'):
        erc1155_marketplace_mock.buyListedItem(
            erc1155_collection_mock,
            ListingParams.token_id,
            seller,
            ListingParams.listing_id,
            ListingParams.unit_price,
            payment_token,
            ListingParams.token_amount / ListingParams.unit_size,
            {"from": buyer}
        )


def test_buy_listed_nft_invalid_units(
        setup_listing: Callable,
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        buyer: LocalAccount,
        seller: LocalAccount
) -> None:
    """Test buying process - invalid amount"""
    setup_listing()

    with reverts('ERC1155Marketplace: invalid units'):
        erc1155_marketplace_mock.buyListedItem(
            erc1155_collection_mock,
            ListingParams.token_id,
            seller,
            ListingParams.listing_id,
            ListingParams.unit_price,
            payment_token,
            0,
            {"from": buyer}
        )

    with reverts('ERC1155Marketplace: invalid units'):
        erc1155_marketplace_mock.buyListedItem(
            erc1155_collection_mock,
            ListingParams.token_id,
            seller,
            ListingParams.listing_id,
            ListingParams.unit_price,
            payment_token,
            ((ListingParams.token_amount / ListingParams.unit_size) + 1) * ListingParams.unit_price,
            {"from": buyer}
        )


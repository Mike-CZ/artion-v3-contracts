import pytest
from enum import Enum
from dataclasses import dataclass
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable
from brownie import reverts, chain, accounts, ZERO_ADDRESS
from brownie.test import given, strategy
from utils.helpers import calculate_auction_fee, calculate_royalty_fee
from utils.structs import Auction, HighestBid


@dataclass(frozen=True)
class AuctionParams:
    token_id: int = 1_000_000
    token_uri: str = 'mock-uri'
    token_amount: int = 10
    reserve_price: int = 50
    start_time: int = chain.time() + (60 * 30)  # start auction at current time + 30 minutes
    end_time: int = start_time + (60 * 60 * 2)  # end auction in 2 hours from start


@dataclass(frozen=True)
class HighestBidParams:
    bid_amount: int = 10


@dataclass(frozen=True)
class RoyaltyParams:
    fraction: int = 1_000  # 10%


class AuctionStatus(Enum):
    NOT_STARTED = 0
    STARTED = 1
    ENDED = 2


@pytest.fixture(scope="session")
def seller(user: LocalAccount) -> LocalAccount:
    return user


@pytest.fixture(scope="session")
def bidder(user_2: LocalAccount) -> LocalAccount:
    return user_2


@pytest.fixture(scope="session")
def outbidder(user_3: LocalAccount) -> LocalAccount:
    return user_3


@pytest.fixture(scope="session")
def royalty_recipient(user_4: LocalAccount) -> LocalAccount:
    return user_4


def handle_auction_status(status: AuctionStatus) -> None:
    if status is not AuctionStatus.NOT_STARTED:
        chain.sleep(
            (AuctionParams.end_time if status is AuctionStatus.ENDED else AuctionParams.start_time) - chain.time()
        )
        chain.mine()


@pytest.fixture(scope='module')
def setup_auction(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        royalty_registry: ProjectContract,
        payment_token: ProjectContract,
        royalty_recipient: LocalAccount,
        seller: LocalAccount
) -> Callable:
    def setup_auction_(is_min_bid_reserve_price: bool = False, status: AuctionStatus = AuctionStatus.STARTED) -> int:
        # mint token and set royalty
        token_id = erc721_collection_mock.mintAndGetTokenId(
            seller,
            '',
            royalty_recipient,
            RoyaltyParams.fraction
        ).return_value

        # create auction
        erc721_collection_mock.setApprovalForAll(erc721_marketplace_mock, True, {'from': seller})
        erc721_marketplace_mock.createAuctionAndTransferToken(
            erc721_collection_mock,
            token_id,
            seller,
            payment_token,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            is_min_bid_reserve_price
        )
        # start/end auction
        handle_auction_status(status)
        return token_id
    return setup_auction_


@pytest.fixture(scope='module')
def setup_auction_with_bid(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        setup_auction: Callable,
        bidder: LocalAccount
) -> Callable:
    def setup_auction_with_bid_(
            status: AuctionStatus = AuctionStatus.STARTED,
            bid_amount: int = HighestBidParams.bid_amount
    ):
        # setup with started status to be able to place bid
        token_id = setup_auction(status=AuctionStatus.STARTED)
        payment_token.approveInternal(bidder, erc721_marketplace_mock, bid_amount)
        erc721_marketplace_mock.placeBid(
            erc721_collection_mock,
            token_id,
            bid_amount,
            {'from': bidder}
        )
        # end when required
        if status == AuctionStatus.ENDED:
            handle_auction_status(AuctionStatus.ENDED)
        return token_id
    return setup_auction_with_bid_


def test_create_auction(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        erc721_collection_mint_with_approval: Callable,
        payment_token: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test auction creation"""
    reserve_price = 50
    is_min_bid_reserve_price = False

    # start auction at current time + 1 hour
    start_time = chain.time() + (60 * 60)
    # end auction in 24 hours from start
    end_time = start_time + (60 * 60 * 24)

    # mint token
    token_id = erc721_collection_mint_with_approval(seller)

    # create auction
    tx = erc721_marketplace_mock.createAuction(
        erc721_collection_mock,
        token_id,
        payment_token,
        reserve_price,
        start_time,
        end_time,
        is_min_bid_reserve_price,
        {'from': seller}
    )

    # assert token has been transferred into escrow
    assert erc721_collection_mock.ownerOf(token_id) == erc721_marketplace_mock

    # asset event emitted correctly
    assert tx.events['ERC721AuctionCreated'] is not None
    assert tx.events['ERC721AuctionCreated']['nftAddress'] == erc721_collection_mock.address
    assert tx.events['ERC721AuctionCreated']['tokenId'] == token_id
    assert tx.events['ERC721AuctionCreated']['owner'] == seller.address
    assert tx.events['ERC721AuctionCreated']['payToken'] == payment_token.address

    # assert auction created
    auction = Auction(*erc721_marketplace_mock.getAuction(erc721_collection_mock, token_id))
    assert auction.exists()
    assert auction.owner == seller.address
    assert auction.payment_token == payment_token.address
    assert auction.reserve_price == reserve_price
    assert auction.is_min_bid_reserve_price == is_min_bid_reserve_price
    assert auction.start_time == start_time
    assert auction.end_time == end_time


def test_create_auction_invalid_token_type(
        erc721_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        erc721_collection_mint: Callable,
        payment_token: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test auction creation with invalid token type"""
    token_id = erc721_collection_mint(seller)
    with reverts('ERC721Marketplace: NFT not ERC721'):
        erc721_marketplace_mock.createAuction(
            erc1155_collection_mock,
            token_id,
            payment_token,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            False,
            {'from': seller}
        )


@given(token_address=strategy('address'))
def test_create_auction_invalid_payment_token(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        erc721_collection_mint_with_approval: Callable,
        token_address: LocalAccount,
        seller: LocalAccount
) -> None:
    """Test auction creation with invalid payment token"""
    token_id = erc721_collection_mint_with_approval(seller)
    with reverts('MarketplaceBase: payment token not enabled'):
        erc721_marketplace_mock.createAuction(
            erc721_collection_mock,
            token_id,
            token_address,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            False,
            {'from': seller}
        )


def test_create_auction_invalid_time_maximum_duration(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        erc721_collection_mint_with_approval: Callable,
        payment_token: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test auction creation with invalid time - maximum duration"""
    token_id = erc721_collection_mint_with_approval(seller)
    with reverts('MarketplaceBase: Auction time exceeds maximum duration'):
        erc721_marketplace_mock.createAuction(
            erc721_collection_mock,
            token_id,
            payment_token,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.start_time + (erc721_marketplace_mock.getMaximumAuctionDuration() + 1),
            False,
            {'from': seller}
        )


def test_create_auction_invalid_time_minimum_duration(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        erc721_collection_mint_with_approval: Callable,
        payment_token: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test auction creation with invalid time - minimum duration"""
    token_id = erc721_collection_mint_with_approval(seller)
    with reverts('MarketplaceBase: Auction time does not meet minimum duration'):
        erc721_marketplace_mock.createAuction(
            erc721_collection_mock,
            token_id,
            payment_token,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.start_time + (erc721_marketplace_mock.getMinimumAuctionDuration() - 1),
            False,
            {'from': seller}
        )


def test_create_auction_already_exists(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        setup_auction: Callable,
        seller: LocalAccount
) -> None:
    """Test auction creation when already started"""
    token_id = setup_auction()
    with reverts('MarketplaceBase: auction exists'):
        erc721_marketplace_mock.createAuction(
            erc721_collection_mock,
            token_id,
            payment_token,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            False,
            {'from': seller}
        )


def test_place_bid(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        payment_token: ProjectContract,
        setup_auction: Callable,
        seller: LocalAccount,
        bidder: LocalAccount
) -> None:
    """Test place bid"""
    token_id = setup_auction()

    bid_amount = 1
    initial_bidder_balance = payment_token.balanceOf(bidder)
    initial_marketplace_balance = payment_token.balanceOf(erc721_marketplace_mock)

    # approve token
    payment_token.approveInternal(bidder, erc721_marketplace_mock, bid_amount)

    # place bid
    tx = erc721_marketplace_mock.placeBid(
        erc721_collection_mock, token_id, bid_amount, {'from': bidder}
    )

    # assert bid exists
    highest_bid = HighestBid(*erc721_marketplace_mock.getHighestBid(erc721_collection_mock, token_id))
    assert highest_bid.exists()
    assert highest_bid.bid_amount == bid_amount
    assert highest_bid.bidder == bidder.address

    # asset event emitted correctly
    assert tx.events['ERC721BidPlaced'] is not None
    assert tx.events['ERC721BidPlaced']['nftAddress'] == erc721_collection_mock.address
    assert tx.events['ERC721BidPlaced']['nftOwner'] == seller.address
    assert tx.events['ERC721BidPlaced']['tokenId'] == token_id
    assert tx.events['ERC721BidPlaced']['bidder'] == bidder.address
    assert tx.events['ERC721BidPlaced']['bid'] == bid_amount

    # assert tokens transferred
    assert payment_token.balanceOf(bidder) == initial_bidder_balance - bid_amount
    assert payment_token.balanceOf(erc721_marketplace_mock) == initial_marketplace_balance + bid_amount


def test_place_bid_auction_not_exist(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        bidder: LocalAccount
):
    """Test place bid when auction does not exist"""
    with reverts('MarketplaceBase: auction not exists'):
        erc721_marketplace_mock.placeBid(
            erc721_collection_mock, AuctionParams.token_id, 10, {'from': bidder}
        )


def test_place_bid_auction_not_started(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction: Callable,
        bidder: LocalAccount
) -> None:
    """Test place bid when auction has not started"""
    token_id = setup_auction(status=AuctionStatus.NOT_STARTED)
    with reverts('MarketplaceBase: auction not started'):
        erc721_marketplace_mock.placeBid(
            erc721_collection_mock, token_id, 10, {'from': bidder}
        )


def test_place_bid_auction_ended(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction: Callable,
        bidder: LocalAccount
) -> None:
    """Test place bid when auction has ended"""
    token_id = setup_auction(status=AuctionStatus.ENDED)

    with reverts('MarketplaceBase: auction ended'):
        erc721_marketplace_mock.placeBid(
            erc721_collection_mock, token_id, 10, {'from': bidder}
        )


def test_place_bid_bidder_is_owner(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction: Callable,
        seller: LocalAccount
) -> None:
    """Test place bid when bidder is owner"""
    token_id = setup_auction()

    with reverts('MarketplaceBase: bidder auction owner'):
        erc721_marketplace_mock.placeBid(
            erc721_collection_mock, token_id, 10, {'from': seller}
        )


def test_place_bid_below_reserve_price(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction: Callable,
        bidder: LocalAccount
) -> None:
    """Test place bid below reserve price"""
    token_id = setup_auction(is_min_bid_reserve_price=True)

    with reverts('MarketplaceBase: bid lower than reserve price'):
        erc721_marketplace_mock.placeBid(
            erc721_collection_mock,
            token_id,
            AuctionParams.reserve_price - 1,
            {'from': bidder}
        )


def test_place_bid_outbid_highest_bid(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        payment_token: ProjectContract,
        seller: LocalAccount,
        bidder: LocalAccount,
        outbidder: LocalAccount
) -> None:
    """Test outbidding the highest bid"""
    token_id = setup_auction_with_bid()

    bid_amount = HighestBidParams.bid_amount + 1
    initial_previous_bidder_balance = payment_token.balanceOf(bidder)
    initial_marketplace_balance = payment_token.balanceOf(erc721_marketplace_mock)

    # approve token
    payment_token.approveInternal(outbidder, erc721_marketplace_mock, bid_amount)

    # place bid
    tx = erc721_marketplace_mock.placeBid(
        erc721_collection_mock,
        token_id,
        bid_amount,
        {'from': outbidder}
    )

    # assert tokens transferred
    assert payment_token.balanceOf(bidder) == initial_previous_bidder_balance + HighestBidParams.bid_amount
    assert payment_token.balanceOf(erc721_marketplace_mock) \
           == initial_marketplace_balance - HighestBidParams.bid_amount + bid_amount

    # asset event emitted correctly
    assert tx.events['ERC721BidRefunded'] is not None
    assert tx.events['ERC721BidRefunded']['nftAddress'] == erc721_collection_mock.address
    assert tx.events['ERC721BidRefunded']['nftOwner'] == seller.address
    assert tx.events['ERC721BidRefunded']['tokenId'] == token_id
    assert tx.events['ERC721BidRefunded']['bidder'] == bidder.address
    assert tx.events['ERC721BidRefunded']['bid'] == HighestBidParams.bid_amount


def test_place_bid_below_previous_highest_bid(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        outbidder: LocalAccount
) -> None:
    """Test placing bid below previous highest bid"""
    token_id = setup_auction_with_bid()

    bid_amount = HighestBidParams.bid_amount - 1

    with reverts('MarketplaceBase: low bid amount'):
        erc721_marketplace_mock.placeBid(
            erc721_collection_mock,
            token_id,
            bid_amount,
            {'from': outbidder}
        )


def test_place_bid_below_min_bid_increment(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        owner: LocalAccount,
        outbidder:  LocalAccount
) -> None:
    """Test placing bid below min bid increment"""
    token_id = setup_auction_with_bid()

    # increase min bid increment
    erc721_marketplace_mock.updateMinBidIncrementAmount(5, {'from': owner})

    # amount greater than the highest bid, but below min bid increment amount
    bid_amount = HighestBidParams.bid_amount + 4

    with reverts('MarketplaceBase: low bid amount'):
        erc721_marketplace_mock.placeBid(
            erc721_collection_mock,
            token_id,
            bid_amount,
            {'from': outbidder}
        )


def test_cancel_auction(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        payment_token: ProjectContract,
        seller: LocalAccount,
        bidder: LocalAccount
) -> None:
    """Test cancelling auction"""
    token_id = setup_auction_with_bid()

    initial_bidder_amount = payment_token.balanceOf(bidder)
    initial_marketplace_amount = payment_token.balanceOf(erc721_marketplace_mock)

    tx = erc721_marketplace_mock.cancelAuction(
        erc721_collection_mock, token_id, {'from': seller}
    )

    # assert payment tokens sent
    assert payment_token.balanceOf(bidder) == initial_bidder_amount + HighestBidParams.bid_amount
    assert payment_token.balanceOf(erc721_marketplace_mock) == initial_marketplace_amount - HighestBidParams.bid_amount

    # assert token transferred
    assert erc721_collection_mock.ownerOf(token_id) == seller

    # asset events emitted correctly
    assert tx.events['ERC721AuctionCancelled'] is not None
    assert tx.events['ERC721AuctionCancelled']['nftAddress'] == erc721_collection_mock.address
    assert tx.events['ERC721AuctionCancelled']['nftOwner'] == seller.address
    assert tx.events['ERC721AuctionCancelled']['tokenId'] == token_id

    assert tx.events['ERC721BidRefunded'] is not None
    assert tx.events['ERC721BidRefunded']['nftAddress'] == erc721_collection_mock.address
    assert tx.events['ERC721BidRefunded']['nftOwner'] == seller.address
    assert tx.events['ERC721BidRefunded']['tokenId'] == token_id
    assert tx.events['ERC721BidRefunded']['bidder'] == bidder.address
    assert tx.events['ERC721BidRefunded']['bid'] == HighestBidParams.bid_amount

    # assert auction does not exist
    assert erc721_marketplace_mock.hasAuction(erc721_collection_mock, token_id) is False

    # assert bid does not exist
    assert erc721_marketplace_mock.hasHighestBid(erc721_collection_mock, token_id) is False


def test_cancel_auction_auction_not_exist(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test cancelling auction when auction does not exist"""
    with reverts('MarketplaceBase: auction not exists'):
        erc721_marketplace_mock.cancelAuction(
            erc721_collection_mock, AuctionParams.token_id, {'from': seller}
        )


def test_cancel_auction_auction_not_owner(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction: Callable,
        bidder: LocalAccount
) -> None:
    """Test cancelling auction when not owner"""
    token_id = setup_auction()

    with reverts('MarketplaceBase: not owner'):
        erc721_marketplace_mock.cancelAuction(
            erc721_collection_mock, token_id, {'from': bidder}
        )


def test_cancel_auction_highest_bid_equal_reserve_price(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        seller: LocalAccount
) -> None:
    """Test cancelling auction when highest bid is equal reserve price"""
    token_id = setup_auction_with_bid(bid_amount=AuctionParams.reserve_price)

    with reverts('MarketplaceBase: highest bid above reserve price'):
        erc721_marketplace_mock.cancelAuction(
            erc721_collection_mock, token_id, {'from': seller}
        )


def test_withdraw_bid(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        payment_token: ProjectContract,
        seller: LocalAccount,
        bidder: LocalAccount
) -> None:
    """Test withdraw bid"""
    token_id = setup_auction_with_bid(status=AuctionStatus.ENDED)

    initial_bidder_amount = payment_token.balanceOf(bidder)
    initial_marketplace_amount = payment_token.balanceOf(erc721_marketplace_mock)

    tx = erc721_marketplace_mock.withdrawBid(
        erc721_collection_mock, token_id, {'from': bidder}
    )

    # assert payment tokens sent
    assert payment_token.balanceOf(bidder) == initial_bidder_amount + HighestBidParams.bid_amount
    assert payment_token.balanceOf(erc721_marketplace_mock) == initial_marketplace_amount - HighestBidParams.bid_amount

    # assert event emitted
    assert tx.events['ERC721BidWithdrawn'] is not None
    assert tx.events['ERC721BidWithdrawn']['nftAddress'] == erc721_collection_mock.address
    assert tx.events['ERC721BidWithdrawn']['nftOwner'] == seller.address
    assert tx.events['ERC721BidWithdrawn']['tokenId'] == token_id
    assert tx.events['ERC721BidWithdrawn']['bidder'] == bidder.address
    assert tx.events['ERC721BidWithdrawn']['bid'] == HighestBidParams.bid_amount

    # assert bid does not exist
    assert erc721_marketplace_mock.hasHighestBid(erc721_collection_mock, token_id) is False


def test_withdraw_bid_not_bidder(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        seller: LocalAccount
) -> None:
    """Test withdraw bid not bidder"""
    token_id = setup_auction_with_bid(status=AuctionStatus.ENDED)

    with reverts('MarketplaceBase: not highest bidder'):
        erc721_marketplace_mock.withdrawBid(
            erc721_collection_mock, token_id, {'from': seller}
        )


def test_withdraw_bid_auction_not_ended(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        seller: LocalAccount,
        bidder: LocalAccount
) -> None:
    """Test withdraw bid before auction ended"""
    token_id = setup_auction_with_bid(bid_amount=AuctionParams.reserve_price)

    with reverts('MarketplaceBase: auction not ended'):
        erc721_marketplace_mock.withdrawBid(
            erc721_collection_mock, token_id, {'from': bidder}
        )


def test_withdraw_bid_before_delay(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        seller: LocalAccount,
        bidder: LocalAccount
) -> None:
    """Test withdraw bid before withdraw delay"""
    token_id = setup_auction_with_bid(status=AuctionStatus.ENDED, bid_amount=AuctionParams.reserve_price)

    with reverts('MarketplaceBase: must wait to withdraw'):
        erc721_marketplace_mock.withdrawBid(
            erc721_collection_mock, token_id, {'from': bidder}
        )


def test_finish_auction(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        payment_token: ProjectContract,
        seller: LocalAccount,
        bidder: LocalAccount,
        royalty_recipient: LocalAccount,
) -> None:
    """Test finish auction"""
    price = AuctionParams.reserve_price + 100  # to make sure fee is calculated from price - reserve_price

    token_id = setup_auction_with_bid(status=AuctionStatus.ENDED, bid_amount=price)

    fee_recipient = accounts.at(erc721_marketplace_mock.getFeeRecipient())
    initial_fee_recipient_amount = payment_token.balanceOf(fee_recipient)
    initial_royalty_recipient_amount = payment_token.balanceOf(royalty_recipient)
    initial_seller_amount = payment_token.balanceOf(seller)
    initial_marketplace_amount = payment_token.balanceOf(erc721_marketplace_mock)

    fee = calculate_auction_fee(price, erc721_marketplace_mock.getAuctionFee())
    royalty_fee = calculate_royalty_fee(price - fee, RoyaltyParams.fraction)

    tx = erc721_marketplace_mock.finishAuction(
        erc721_collection_mock, token_id, {'from': seller}
    )

    # assert payment tokens sent
    assert payment_token.balanceOf(fee_recipient) == initial_fee_recipient_amount + fee
    assert payment_token.balanceOf(royalty_recipient) == initial_royalty_recipient_amount + royalty_fee
    assert payment_token.balanceOf(seller) == initial_seller_amount + price - fee - royalty_fee
    assert payment_token.balanceOf(erc721_marketplace_mock) == initial_marketplace_amount - price

    # assert tokens transferred
    assert erc721_collection_mock.ownerOf(token_id) == bidder

    # assert event emitted
    assert tx.events['ERC721AuctionFinished'] is not None
    assert tx.events['ERC721AuctionFinished']['oldOwner'] == seller.address
    assert tx.events['ERC721AuctionFinished']['nftAddress'] == erc721_collection_mock.address
    assert tx.events['ERC721AuctionFinished']['tokenId'] == token_id
    assert tx.events['ERC721AuctionFinished']['winner'] == bidder.address
    assert tx.events['ERC721AuctionFinished']['payToken'] == payment_token.address
    assert tx.events['ERC721AuctionFinished']['winningBid'] == price

    # assert auction does not exist
    assert erc721_marketplace_mock.hasAuction(erc721_collection_mock, token_id) is False

    # assert bid does not exist
    assert erc721_marketplace_mock.hasHighestBid(erc721_collection_mock, token_id) is False


def test_finish_auction_from_bidder(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        bidder: LocalAccount
) -> None:
    """Test finish auction from bidder"""
    token_id = setup_auction_with_bid(status=AuctionStatus.ENDED, bid_amount=AuctionParams.reserve_price)
    erc721_marketplace_mock.finishAuction(
        erc721_collection_mock, token_id, {'from': bidder}
    )


def test_finish_auction_not_exist(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        bidder: LocalAccount
) -> None:
    """Test finish auction when not exist"""
    with reverts('MarketplaceBase: auction not exists'):
        erc721_marketplace_mock.finishAuction(
            erc721_collection_mock, AuctionParams.token_id, {'from': bidder}
        )


def test_finish_auction_not_ended(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        bidder: LocalAccount
) -> None:
    """Test finish auction when not ended"""
    token_id = setup_auction_with_bid(bid_amount=AuctionParams.reserve_price)
    with reverts('MarketplaceBase: auction not ended'):
        erc721_marketplace_mock.finishAuction(
            erc721_collection_mock, token_id, {'from': bidder}
        )


def test_finish_auction_without_bid(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction: Callable,
        bidder: LocalAccount
) -> None:
    """Test finish auction when bid does not exist"""
    token_id = setup_auction(status=AuctionStatus.ENDED)
    with reverts('MarketplaceBase: highest bid not exists'):
        erc721_marketplace_mock.finishAuction(
            erc721_collection_mock, token_id, {'from': bidder}
        )


def test_finish_auction_not_owner_or_bidder(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        outbidder: LocalAccount
) -> None:
    """Test finish auction when not owner or bidder"""
    token_id = setup_auction_with_bid(status=AuctionStatus.ENDED, bid_amount=AuctionParams.reserve_price)
    with reverts('MarketplaceBase: not auction or highest bid owner'):
        erc721_marketplace_mock.finishAuction(
            erc721_collection_mock, token_id, {'from': outbidder}
        )


def test_finish_auction_low_bid(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        seller: LocalAccount
) -> None:
    """Test finish auction when bid is below reserve price"""
    token_id = setup_auction_with_bid(status=AuctionStatus.ENDED, bid_amount=AuctionParams.reserve_price - 1)
    with reverts('MarketplaceBase: highest bid below reserve price'):
        erc721_marketplace_mock.finishAuction(
            erc721_collection_mock, token_id, {'from': seller}
        )


def test_finish_auction_below_reserve_price(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        seller: LocalAccount
) -> None:
    """Test finish auction below reserve price"""
    token_id = setup_auction_with_bid(status=AuctionStatus.ENDED, bid_amount=AuctionParams.reserve_price - 1)
    erc721_marketplace_mock.finishAuctionBelowReservePrice(
        erc721_collection_mock, token_id, {'from': seller}
    )


def test_finish_auction_below_reserve_price_not_owner(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        bidder: LocalAccount
) -> None:
    """Test finish auction below reserve price when not auction owner"""
    token_id = setup_auction_with_bid(status=AuctionStatus.ENDED, bid_amount=AuctionParams.reserve_price - 1)
    with reverts('MarketplaceBase: not owner'):
        erc721_marketplace_mock.finishAuctionBelowReservePrice(
            erc721_collection_mock, token_id, {'from': bidder}
        )


def test_finish_auction_below_reserve_price_above_reserve_price(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction_with_bid: Callable,
        seller: LocalAccount
) -> None:
    """Test finish auction below reserve price when bid is above reserve price"""
    token_id = setup_auction_with_bid(status=AuctionStatus.ENDED, bid_amount=AuctionParams.reserve_price + 1)
    with reverts('MarketplaceBase: highest bid above reserve price'):
        erc721_marketplace_mock.finishAuctionBelowReservePrice(
            erc721_collection_mock, token_id, {'from': seller}
        )


def test_update_auction_reserve_price(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction: Callable,
        seller: LocalAccount
) -> None:
    """Test update auction reserve price"""
    token_id = setup_auction()

    reserve_price = AuctionParams.reserve_price - 1

    tx = erc721_marketplace_mock.updateAuctionReservePrice(
        erc721_collection_mock, token_id, reserve_price, {'from': seller}
    )

    # assert reserve price changed
    auction = Auction(*erc721_marketplace_mock.getAuction(erc721_collection_mock, token_id))
    assert auction.reserve_price == reserve_price

    # assert event emitted
    assert tx.events['ERC721AuctionReservePriceUpdated'] is not None
    assert tx.events['ERC721AuctionReservePriceUpdated']['nftAddress'] == erc721_collection_mock.address
    assert tx.events['ERC721AuctionReservePriceUpdated']['tokenId'] == token_id
    assert tx.events['ERC721AuctionReservePriceUpdated']['owner'] == seller.address
    assert tx.events['ERC721AuctionReservePriceUpdated']['reservePrice'] == reserve_price


def test_update_auction_reserve_price_auction_not_exist(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        seller: LocalAccount
) -> None:
    """Test update auction reserve price when auction does not exist"""
    with reverts('MarketplaceBase: auction not exists'):
        erc721_marketplace_mock.updateAuctionReservePrice(
            erc721_collection_mock,
            AuctionParams.token_id,
            AuctionParams.reserve_price - 1,
            {'from': seller}
        )


def test_update_auction_reserve_price_auction_not_owner(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction: Callable,
        bidder: LocalAccount
) -> None:
    """Test cancelling auction when not owner"""
    token_id = setup_auction()

    with reverts('MarketplaceBase: not owner'):
        erc721_marketplace_mock.updateAuctionReservePrice(
            erc721_collection_mock,
            token_id,
            AuctionParams.reserve_price - 1,
            {'from': bidder}
        )


def test_update_auction_reserve_price_above_reserve_price(
        erc721_marketplace_mock: ProjectContract,
        erc721_collection_mock: ProjectContract,
        setup_auction: Callable,
        seller: LocalAccount
) -> None:
    """Test update auction reserve price when new reserve price is above previous"""
    token_id = setup_auction()

    with reverts('MarketplaceBase: reserve price can only decrease'):
        erc721_marketplace_mock.updateAuctionReservePrice(
            erc721_collection_mock,
            token_id,
            AuctionParams.reserve_price + 1,
            {'from': seller}
        )

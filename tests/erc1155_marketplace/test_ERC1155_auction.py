import pytest
from enum import Enum
from dataclasses import dataclass
from brownie import reverts, Wei, chain
from brownie.test import given, strategy


@dataclass(frozen=True)
class AuctionParams:
    token_id: int = 1_000_000
    token_amount: int = 10
    reserve_price: int = 50
    start_time: int = chain.time() + (60 * 30)  # start auction at current time + 30 minutes
    end_time: int = start_time + (60 * 60 * 2)  # end auction in 2 hours from start


@dataclass(frozen=True)
class HighestBidParams:
    bid_amount: int = 10


class AuctionStatus(Enum):
    NOT_STARTED = 0
    STARTED = 1
    ENDED = 2


@pytest.fixture(scope='module')
def setup_auction(erc1155_marketplace_mock, erc1155_collection_mock, erc20_mock, user):
    def setup_auction_(is_min_bid_reserve_price: bool = False, status: AuctionStatus = AuctionStatus.STARTED):
        erc1155_collection_mock.mint(user, AuctionParams.token_id, 50, '')
        erc1155_collection_mock.setApprovalForAll(erc1155_marketplace_mock, True, {'from': user})
        erc1155_marketplace_mock.createAuctionAndTransferToken(
            erc1155_collection_mock,
            AuctionParams.token_id,
            AuctionParams.token_amount,
            user,
            erc20_mock,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            is_min_bid_reserve_price
        )
        # start/end auction
        if status is not AuctionStatus.NOT_STARTED:
            chain.sleep(
                (AuctionParams.end_time if status is AuctionStatus.ENDED else AuctionParams.start_time) - chain.time()
            )
            chain.mine()
    return setup_auction_


@pytest.fixture(scope='module')
def setup_auction_with_bid(erc1155_marketplace_mock, erc1155_collection_mock, setup_auction, erc20_mock, user, user_2):
    def setup_auction_with_bid_(
            status: AuctionStatus = AuctionStatus.STARTED,
            bid_amount: int = HighestBidParams.bid_amount
    ):
        setup_auction(status=status)
        erc20_mock.approveInternal(user_2, erc1155_marketplace_mock, bid_amount)
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, user, bid_amount, {'from': user_2}
        )
    return setup_auction_with_bid_


@pytest.fixture(scope='module')
def erc1155_collection_mint_with_approval(erc1155_marketplace_mock, erc1155_collection_mock, erc1155_collection_mint):
    def erc1155_collection_mint_with_approval_(recipient, amount):
        token_id = erc1155_collection_mint(recipient, amount)
        erc1155_collection_mock.setApprovalForAll(erc1155_marketplace_mock, True, {'from': recipient})
        return token_id
    return erc1155_collection_mint_with_approval_


def test_create_auction(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc1155_collection_mint_with_approval,
        erc20_mock,
        user
):
    """Test auction creation"""
    token_amount = 5
    auction_token_amount = 2
    reserve_price = 50
    is_min_bid_reserve_price = False

    # start auction at current time + 1 hour
    start_time = chain.time() + (60 * 60)
    # end auction in 24 hours from start
    end_time = start_time + (60 * 60 * 24)

    # mint token
    token_id = erc1155_collection_mint_with_approval(user, token_amount)

    # create auction
    tx = erc1155_marketplace_mock.createAuction(
        erc1155_collection_mock,
        token_id,
        auction_token_amount,
        erc20_mock,
        reserve_price,
        start_time,
        end_time,
        is_min_bid_reserve_price,
        {'from': user}
    )

    # assert token has been transferred into escrow
    assert erc1155_collection_mock.balanceOf(user, token_id) == token_amount - auction_token_amount
    assert erc1155_collection_mock.balanceOf(erc1155_marketplace_mock, token_id) == auction_token_amount

    # TODO: events etc...


def test_create_action_invalid_token_type(
        erc1155_marketplace_mock,
        erc721_collection_mock,
        erc721_collection_mint,
        erc20_mock,
        user
):
    """Test auction creation with invalid token type"""
    token_id = erc721_collection_mint(user)
    with reverts('ERC1155Marketplace: NFT not ERC1155'):
        erc1155_marketplace_mock.createAuction(
            erc721_collection_mock,
            token_id,
            1,
            erc20_mock,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            False,
            {'from': user}
        )


def test_create_action_not_enough_tokens(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc1155_collection_mint,
        erc20_mock,
        user
):
    """Test auction creation without enough tokens"""
    token_id = erc1155_collection_mint(user, 5)
    with reverts('ERC1155Marketplace: balance too low'):
        erc1155_marketplace_mock.createAuction(
            erc1155_collection_mock,
            token_id,
            10,
            erc20_mock,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            False,
            {'from': user}
        )


def test_create_action_not_approved(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc1155_collection_mint,
        erc20_mock,
        user
):
    """Test auction creation without approval"""
    token_id = erc1155_collection_mint(user, AuctionParams.token_amount)
    with reverts('ERC1155Marketplace: not approved'):
        erc1155_marketplace_mock.createAuction(
            erc1155_collection_mock,
            token_id,
            AuctionParams.token_amount,
            erc20_mock,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            False,
            {'from': user}
        )


@given(token_address=strategy('address'))
def test_create_action_invalid_payment_token(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc1155_collection_mint_with_approval,
        token_address,
        user
):
    """Test auction creation with invalid payment token"""
    token_id = erc1155_collection_mint_with_approval(user, AuctionParams.token_amount)
    with reverts('MarketplaceBase: payment token is not enabled'):
        erc1155_marketplace_mock.createAuction(
            erc1155_collection_mock,
            token_id,
            AuctionParams.token_amount,
            token_address,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            False,
            {'from': user}
        )


def test_create_action_invalid_time_maximum_duration(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc1155_collection_mint_with_approval,
        erc20_mock,
        user
):
    """Test auction creation with invalid time - maximum duration"""
    token_id = erc1155_collection_mint_with_approval(user, AuctionParams.token_amount)
    with reverts('MarketplaceBase: Auction time exceeds maximum duration'):
        erc1155_marketplace_mock.createAuction(
            erc1155_collection_mock,
            token_id,
            AuctionParams.token_amount,
            erc20_mock,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.start_time + (erc1155_marketplace_mock.getMaximumAuctionDuration() + 1),
            False,
            {'from': user}
        )


def test_create_action_invalid_time_minimum_duration(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc1155_collection_mint_with_approval,
        erc20_mock,
        user
):
    """Test auction creation with invalid time - minimum duration"""
    token_id = erc1155_collection_mint_with_approval(user, AuctionParams.token_amount)
    with reverts('MarketplaceBase: Auction time does not meet minimum duration'):
        erc1155_marketplace_mock.createAuction(
            erc1155_collection_mock,
            token_id,
            AuctionParams.token_amount,
            erc20_mock,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.start_time + (erc1155_marketplace_mock.getMinimumAuctionDuration() - 1),
            False,
            {'from': user}
        )


def test_create_action_already_exists(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc20_mock,
        setup_auction,
        user
):
    """Test auction creation when already started"""
    setup_auction()
    with reverts('MarketplaceBase: auction exists'):
        erc1155_marketplace_mock.createAuction(
            erc1155_collection_mock,
            AuctionParams.token_id,
            AuctionParams.token_amount,
            erc20_mock,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            False,
            {'from': user}
        )


def test_place_bid(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc20_mock,
        setup_auction,
        user,
        user_2
):
    """Test place bid"""
    setup_auction()

    bid_amount = 1
    initial_bidder_balance = erc20_mock.balanceOf(user_2)
    initial_marketplace_balance = erc20_mock.balanceOf(erc1155_marketplace_mock)

    # approve token
    erc20_mock.approveInternal(user_2, erc1155_marketplace_mock, bid_amount)

    # place bid
    tx = erc1155_marketplace_mock.placeBid(
        erc1155_collection_mock, AuctionParams.token_id, user, bid_amount, {'from': user_2}
    )

    # assert bid exists
    assert erc1155_marketplace_mock.getHighestBid(erc1155_collection_mock, AuctionParams.token_id, user)[:2] \
           == (user_2.address, bid_amount)

    # asset event emitted correctly
    assert tx.events['BidPlaced'] is not None
    assert tx.events['BidPlaced']['nftAddress'] == erc1155_collection_mock.address
    assert tx.events['BidPlaced']['nftOwner'] == user.address
    assert tx.events['BidPlaced']['tokenId'] == AuctionParams.token_id
    assert tx.events['BidPlaced']['bidder'] == user_2.address
    assert tx.events['BidPlaced']['bid'] == bid_amount

    # assert tokens transferred
    assert erc20_mock.balanceOf(user_2) == initial_bidder_balance - bid_amount
    assert erc20_mock.balanceOf(erc1155_marketplace_mock) == initial_marketplace_balance + bid_amount


def test_place_bid_auction_not_exist(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        user,
        user_2
):
    """Test place bid when auction does not exist"""
    with reverts('MarketplaceBase: auction not exist'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, user, 10, {'from': user_2}
        )


def test_place_bid_auction_not_started(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction,
        user,
        user_2
):
    """Test place bid when auction has not started"""
    setup_auction(status=AuctionStatus.NOT_STARTED)
    with reverts('MarketplaceBase: auction not started'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, user, 10, {'from': user_2}
        )


def test_place_bid_auction_ended(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction,
        user,
        user_2
):
    """Test place bid when auction has ended"""
    setup_auction(status=AuctionStatus.ENDED)

    with reverts('MarketplaceBase: auction ended'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, user, 10, {'from': user_2}
        )


def test_place_bid_bidder_is_owner(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction,
        user
):
    """Test place bid when bidder is owner"""
    setup_auction()

    with reverts('MarketplaceBase: bidder auction owner'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, user, 10, {'from': user}
        )


def test_place_bid_below_reserve_price(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction,
        user,
        user_2
):
    """Test place bid below reserve price"""
    setup_auction(is_min_bid_reserve_price=True)

    with reverts('MarketplaceBase: bid lower than reserve price'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, user, AuctionParams.reserve_price - 1, {'from': user_2}
        )


def test_place_bid_outbid_highest_bid(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        erc20_mock,
        user,
        user_2,
        user_3
):
    """Test outbidding the highest bid"""
    setup_auction_with_bid()

    bid_amount = HighestBidParams.bid_amount + 1
    initial_previous_bidder_balance = erc20_mock.balanceOf(user_2)
    initial_marketplace_balance = erc20_mock.balanceOf(erc1155_marketplace_mock)

    # approve token
    erc20_mock.approveInternal(user_3, erc1155_marketplace_mock, bid_amount)

    # place bid
    tx = erc1155_marketplace_mock.placeBid(
        erc1155_collection_mock, AuctionParams.token_id, user, bid_amount, {'from': user_3}
    )

    # assert tokens transferred
    assert erc20_mock.balanceOf(user_2) == initial_previous_bidder_balance + HighestBidParams.bid_amount
    assert erc20_mock.balanceOf(erc1155_marketplace_mock) \
           == initial_marketplace_balance - HighestBidParams.bid_amount + bid_amount

    # asset event emitted correctly
    assert tx.events['BidRefunded'] is not None
    assert tx.events['BidRefunded']['nftAddress'] == erc1155_collection_mock.address
    assert tx.events['BidRefunded']['nftOwner'] == user.address
    assert tx.events['BidRefunded']['tokenId'] == AuctionParams.token_id
    assert tx.events['BidRefunded']['bidder'] == user_2.address
    assert tx.events['BidRefunded']['bid'] == HighestBidParams.bid_amount


def test_place_bid_below_previous_highest_bid(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        user,
        user_3
):
    """Test placing bid below previous highest bid"""
    setup_auction_with_bid()

    bid_amount = HighestBidParams.bid_amount - 1

    with reverts('MarketplaceBase: low bid amount'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, user, bid_amount, {'from': user_3}
        )


def test_place_bid_below_min_bid_increment(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        erc20_mock,
        owner,
        user,
        user_3
):
    """Test placing bid below min bid increment"""
    setup_auction_with_bid()

    # increase min bid increment
    erc1155_marketplace_mock.updateMinBidIncrementAmount(5, {'from': owner})

    # amount greater than the highest bid, but below min bid increment amount
    bid_amount = HighestBidParams.bid_amount + 4

    with reverts('MarketplaceBase: low bid amount'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, user, bid_amount, {'from': user_3}
        )


def test_cancel_auction(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        erc20_mock,
        user,
        user_2
):
    """Test placing bid below min bid increment"""
    setup_auction_with_bid()

    initial_auction_owner_amount = erc20_mock.balanceOf(user)
    initial_bidder_amount = erc20_mock.balanceOf(user_2)

    erc1155_marketplace_mock.cancelAuction(erc1155_collection_mock, AuctionParams.token_id)

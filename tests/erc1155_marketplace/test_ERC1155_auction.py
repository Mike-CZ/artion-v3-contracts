import pytest
from enum import Enum
from dataclasses import dataclass
from brownie import reverts, chain, accounts, ZERO_ADDRESS
from brownie.test import given, strategy
from utils.helpers import calculate_auction_fee, calculate_royalty_fee


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


@dataclass(frozen=True)
class RoyaltyParams:
    fraction: int = 1_000  # 10%


class AuctionStatus(Enum):
    NOT_STARTED = 0
    STARTED = 1
    ENDED = 2


@pytest.fixture(scope="session")
def seller(user):
    return user


@pytest.fixture(scope="session")
def bidder(user_2):
    return user_2


@pytest.fixture(scope="session")
def outbidder(user_3):
    return user_3


@pytest.fixture(scope="session")
def royalty_recipient(user_3):
    return user_3


def handle_auction_status(status: AuctionStatus):
    if status is not AuctionStatus.NOT_STARTED:
        chain.sleep(
            (AuctionParams.end_time if status is AuctionStatus.ENDED else AuctionParams.start_time) - chain.time()
        )
        chain.mine()


@pytest.fixture(scope='module')
def setup_auction(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        royalty_registry,
        royalty_recipient,
        erc20_mock,
        seller
):
    def setup_auction_(is_min_bid_reserve_price: bool = False, status: AuctionStatus = AuctionStatus.STARTED):
        # mint token and set royalty
        erc1155_collection_mock.mint(seller, AuctionParams.token_id, 50, '')
        royalty_registry.setTokenRoyalty(
            erc1155_collection_mock,
            AuctionParams.token_id,
            royalty_recipient,
            RoyaltyParams.fraction,
            {'from': seller}
        )
        # create auction
        erc1155_collection_mock.setApprovalForAll(erc1155_marketplace_mock, True, {'from': seller})
        erc1155_marketplace_mock.createAuctionAndTransferToken(
            erc1155_collection_mock,
            AuctionParams.token_id,
            AuctionParams.token_amount,
            seller,
            erc20_mock,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            is_min_bid_reserve_price
        )
        # start/end auction
        handle_auction_status(status)
    return setup_auction_


@pytest.fixture(scope='module')
def setup_auction_with_bid(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction,
        erc20_mock,
        seller,
        bidder
):
    def setup_auction_with_bid_(
            status: AuctionStatus = AuctionStatus.STARTED,
            bid_amount: int = HighestBidParams.bid_amount
    ):
        # setup with started status to be able to place bid
        setup_auction(status=AuctionStatus.STARTED)
        erc20_mock.approveInternal(bidder, erc1155_marketplace_mock, bid_amount)
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, seller, bid_amount, {'from': bidder}
        )
        # end when required
        if status == AuctionStatus.ENDED:
            handle_auction_status(AuctionStatus.ENDED)
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
        seller
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
    token_id = erc1155_collection_mint_with_approval(seller, token_amount)

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
        {'from': seller}
    )

    # assert token has been transferred into escrow
    assert erc1155_collection_mock.balanceOf(seller, token_id) == token_amount - auction_token_amount
    assert erc1155_collection_mock.balanceOf(erc1155_marketplace_mock, token_id) == auction_token_amount

    # TODO: events etc...


def test_create_action_invalid_token_type(
        erc1155_marketplace_mock,
        erc721_collection_mock,
        erc721_collection_mint,
        erc20_mock,
        seller
):
    """Test auction creation with invalid token type"""
    token_id = erc721_collection_mint(seller)
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
            {'from': seller}
        )


def test_create_action_not_enough_tokens(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc1155_collection_mint,
        erc20_mock,
        seller
):
    """Test auction creation without enough tokens"""
    token_id = erc1155_collection_mint(seller, 5)
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
            {'from': seller}
        )


def test_create_action_not_approved(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc1155_collection_mint,
        erc20_mock,
        seller
):
    """Test auction creation without approval"""
    token_id = erc1155_collection_mint(seller, AuctionParams.token_amount)
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
            {'from': seller}
        )


@given(token_address=strategy('address'))
def test_create_action_invalid_payment_token(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc1155_collection_mint_with_approval,
        token_address,
        seller
):
    """Test auction creation with invalid payment token"""
    token_id = erc1155_collection_mint_with_approval(seller, AuctionParams.token_amount)
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
            {'from': seller}
        )


def test_create_action_invalid_time_maximum_duration(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc1155_collection_mint_with_approval,
        erc20_mock,
        seller
):
    """Test auction creation with invalid time - maximum duration"""
    token_id = erc1155_collection_mint_with_approval(seller, AuctionParams.token_amount)
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
            {'from': seller}
        )


def test_create_action_invalid_time_minimum_duration(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc1155_collection_mint_with_approval,
        erc20_mock,
        seller
):
    """Test auction creation with invalid time - minimum duration"""
    token_id = erc1155_collection_mint_with_approval(seller, AuctionParams.token_amount)
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
            {'from': seller}
        )


def test_create_action_already_exists(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc20_mock,
        setup_auction,
        seller
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
            {'from': seller}
        )


def test_place_bid(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        erc20_mock,
        setup_auction,
        seller,
        bidder
):
    """Test place bid"""
    setup_auction()

    bid_amount = 1
    initial_bidder_balance = erc20_mock.balanceOf(bidder)
    initial_marketplace_balance = erc20_mock.balanceOf(erc1155_marketplace_mock)

    # approve token
    erc20_mock.approveInternal(bidder, erc1155_marketplace_mock, bid_amount)

    # place bid
    tx = erc1155_marketplace_mock.placeBid(
        erc1155_collection_mock, AuctionParams.token_id, seller, bid_amount, {'from': bidder}
    )

    # assert bid exists
    assert erc1155_marketplace_mock.getHighestBid(erc1155_collection_mock, AuctionParams.token_id, seller)[:2] \
           == (bidder.address, bid_amount)

    # asset event emitted correctly
    assert tx.events['BidPlaced'] is not None
    assert tx.events['BidPlaced']['nftAddress'] == erc1155_collection_mock.address
    assert tx.events['BidPlaced']['nftOwner'] == seller.address
    assert tx.events['BidPlaced']['tokenId'] == AuctionParams.token_id
    assert tx.events['BidPlaced']['bidder'] == bidder.address
    assert tx.events['BidPlaced']['bid'] == bid_amount

    # assert tokens transferred
    assert erc20_mock.balanceOf(bidder) == initial_bidder_balance - bid_amount
    assert erc20_mock.balanceOf(erc1155_marketplace_mock) == initial_marketplace_balance + bid_amount


def test_place_bid_auction_not_exist(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        seller,
        bidder
):
    """Test place bid when auction does not exist"""
    with reverts('MarketplaceBase: auction not exist'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, seller, 10, {'from': bidder}
        )


def test_place_bid_auction_not_started(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction,
        seller,
        bidder
):
    """Test place bid when auction has not started"""
    setup_auction(status=AuctionStatus.NOT_STARTED)
    with reverts('MarketplaceBase: auction not started'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, seller, 10, {'from': bidder}
        )


def test_place_bid_auction_ended(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction,
        seller,
        bidder
):
    """Test place bid when auction has ended"""
    setup_auction(status=AuctionStatus.ENDED)

    with reverts('MarketplaceBase: auction ended'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, seller, 10, {'from': bidder}
        )


def test_place_bid_bidder_is_owner(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction,
        seller
):
    """Test place bid when bidder is owner"""
    setup_auction()

    with reverts('MarketplaceBase: bidder auction owner'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, seller, 10, {'from': seller}
        )


def test_place_bid_below_reserve_price(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction,
        seller,
        bidder
):
    """Test place bid below reserve price"""
    setup_auction(is_min_bid_reserve_price=True)

    with reverts('MarketplaceBase: bid lower than reserve price'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, seller, AuctionParams.reserve_price - 1, {'from': bidder}
        )


def test_place_bid_outbid_highest_bid(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        erc20_mock,
        seller,
        bidder,
        outbidder
):
    """Test outbidding the highest bid"""
    setup_auction_with_bid()

    bid_amount = HighestBidParams.bid_amount + 1
    initial_previous_bidder_balance = erc20_mock.balanceOf(bidder)
    initial_marketplace_balance = erc20_mock.balanceOf(erc1155_marketplace_mock)

    # approve token
    erc20_mock.approveInternal(outbidder, erc1155_marketplace_mock, bid_amount)

    # place bid
    tx = erc1155_marketplace_mock.placeBid(
        erc1155_collection_mock, AuctionParams.token_id, seller, bid_amount, {'from': outbidder}
    )

    # assert tokens transferred
    assert erc20_mock.balanceOf(bidder) == initial_previous_bidder_balance + HighestBidParams.bid_amount
    assert erc20_mock.balanceOf(erc1155_marketplace_mock) \
           == initial_marketplace_balance - HighestBidParams.bid_amount + bid_amount

    # asset event emitted correctly
    assert tx.events['BidRefunded'] is not None
    assert tx.events['BidRefunded']['nftAddress'] == erc1155_collection_mock.address
    assert tx.events['BidRefunded']['nftOwner'] == seller.address
    assert tx.events['BidRefunded']['tokenId'] == AuctionParams.token_id
    assert tx.events['BidRefunded']['bidder'] == bidder.address
    assert tx.events['BidRefunded']['bid'] == HighestBidParams.bid_amount


def test_place_bid_below_previous_highest_bid(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        seller,
        outbidder
):
    """Test placing bid below previous highest bid"""
    setup_auction_with_bid()

    bid_amount = HighestBidParams.bid_amount - 1

    with reverts('MarketplaceBase: low bid amount'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, seller, bid_amount, {'from': outbidder}
        )


def test_place_bid_below_min_bid_increment(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        owner,
        seller,
        outbidder
):
    """Test placing bid below min bid increment"""
    setup_auction_with_bid()

    # increase min bid increment
    erc1155_marketplace_mock.updateMinBidIncrementAmount(5, {'from': owner})

    # amount greater than the highest bid, but below min bid increment amount
    bid_amount = HighestBidParams.bid_amount + 4

    with reverts('MarketplaceBase: low bid amount'):
        erc1155_marketplace_mock.placeBid(
            erc1155_collection_mock, AuctionParams.token_id, seller, bid_amount, {'from': outbidder}
        )


def test_cancel_auction(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        erc20_mock,
        seller,
        bidder
):
    """Test cancelling auction"""
    setup_auction_with_bid()

    initial_bidder_amount = erc20_mock.balanceOf(bidder)
    initial_marketplace_amount = erc20_mock.balanceOf(erc1155_marketplace_mock)
    initial_seller_token_amount = erc1155_collection_mock.balanceOf(seller, AuctionParams.token_id)
    initial_marketplace_token_amount = erc1155_collection_mock.balanceOf(
        erc1155_marketplace_mock, AuctionParams.token_id
    )

    tx = erc1155_marketplace_mock.cancelAuction(erc1155_collection_mock, AuctionParams.token_id, {'from': seller})

    # assert payment tokens sent
    assert erc20_mock.balanceOf(bidder) == initial_bidder_amount + HighestBidParams.bid_amount
    assert erc20_mock.balanceOf(erc1155_marketplace_mock) == initial_marketplace_amount - HighestBidParams.bid_amount

    # assert tokens transferred
    assert erc1155_collection_mock.balanceOf(seller, AuctionParams.token_id) == \
           initial_seller_token_amount + AuctionParams.token_amount
    assert erc1155_collection_mock.balanceOf(erc1155_marketplace_mock, AuctionParams.token_id) == \
           initial_marketplace_token_amount - AuctionParams.token_amount

    # asset events emitted correctly
    assert tx.events['AuctionCancelled'] is not None
    assert tx.events['AuctionCancelled']['nftAddress'] == erc1155_collection_mock.address
    assert tx.events['AuctionCancelled']['nftOwner'] == seller.address
    assert tx.events['AuctionCancelled']['tokenId'] == AuctionParams.token_id

    assert tx.events['BidRefunded'] is not None
    assert tx.events['BidRefunded']['nftAddress'] == erc1155_collection_mock.address
    assert tx.events['BidRefunded']['nftOwner'] == seller.address
    assert tx.events['BidRefunded']['tokenId'] == AuctionParams.token_id
    assert tx.events['BidRefunded']['bidder'] == bidder.address
    assert tx.events['BidRefunded']['bid'] == HighestBidParams.bid_amount

    # assert auction does not exist
    assert erc1155_marketplace_mock.getAuction(erc1155_collection_mock, AuctionParams.token_id, seller)[0][0] == \
           ZERO_ADDRESS

    # assert bid does not exist
    assert erc1155_marketplace_mock.getHighestBid(erc1155_collection_mock, AuctionParams.token_id, seller)[0] == \
           ZERO_ADDRESS


def test_cancel_auction_action_not_exist(erc1155_marketplace_mock, erc1155_collection_mock, seller):
    """Test cancelling auction when auction does not exist"""
    with reverts('MarketplaceBase: auction not exist'):
        erc1155_marketplace_mock.cancelAuction(erc1155_collection_mock, AuctionParams.token_id, {'from': seller})


# TODO: TEST CANCEL WHEN RESULTED


def test_cancel_auction_highest_bid_equal_reserve_price(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        seller
):
    """Test cancelling auction when highest bid is equal reserve price"""
    setup_auction_with_bid(bid_amount=AuctionParams.reserve_price)

    with reverts('MarketplaceBase: highest bid above reserve price'):
        erc1155_marketplace_mock.cancelAuction(erc1155_collection_mock, AuctionParams.token_id, {'from': seller})


def test_withdraw_bid(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        erc20_mock,
        seller,
        bidder
):
    """Test withdraw bid"""
    setup_auction_with_bid(status=AuctionStatus.ENDED)

    initial_bidder_amount = erc20_mock.balanceOf(bidder)
    initial_marketplace_amount = erc20_mock.balanceOf(erc1155_marketplace_mock)

    tx = erc1155_marketplace_mock.withdrawBid(erc1155_collection_mock, AuctionParams.token_id, seller, {'from': bidder})

    # assert payment tokens sent
    assert erc20_mock.balanceOf(bidder) == initial_bidder_amount + HighestBidParams.bid_amount
    assert erc20_mock.balanceOf(erc1155_marketplace_mock) == initial_marketplace_amount - HighestBidParams.bid_amount

    # assert event emitted
    assert tx.events['BidWithdrawn'] is not None
    assert tx.events['BidWithdrawn']['nftAddress'] == erc1155_collection_mock.address
    assert tx.events['BidWithdrawn']['nftOwner'] == seller.address
    assert tx.events['BidWithdrawn']['tokenId'] == AuctionParams.token_id
    assert tx.events['BidWithdrawn']['bidder'] == bidder.address
    assert tx.events['BidWithdrawn']['bid'] == HighestBidParams.bid_amount

    # assert bid does not exist
    assert erc1155_marketplace_mock.getHighestBid(erc1155_collection_mock, AuctionParams.token_id, seller)[0] == \
           ZERO_ADDRESS


def test_withdraw_bid_not_bidder(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        seller
):
    """Test withdraw bid not bidder"""
    setup_auction_with_bid(status=AuctionStatus.ENDED)

    with reverts('MarketplaceBase: not highest bidder'):
        erc1155_marketplace_mock.withdrawBid(erc1155_collection_mock, AuctionParams.token_id, seller, {'from': seller})


def test_withdraw_bid_auction_not_ended(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        seller,
        bidder
):
    """Test withdraw bid before auction ended"""
    setup_auction_with_bid(bid_amount=AuctionParams.reserve_price)

    with reverts('MarketplaceBase: auction not ended'):
        erc1155_marketplace_mock.withdrawBid(erc1155_collection_mock, AuctionParams.token_id, seller, {'from': bidder})


def test_withdraw_bid_before_delay(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        seller,
        bidder
):
    """Test withdraw bid before withdraw delay"""
    setup_auction_with_bid(status=AuctionStatus.ENDED, bid_amount=AuctionParams.reserve_price)

    with reverts('MarketplaceBase: must wait to withdraw'):
        erc1155_marketplace_mock.withdrawBid(erc1155_collection_mock, AuctionParams.token_id, seller, {'from': bidder})


def test_finish_auction(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        erc20_mock,
        seller,
        bidder,
        royalty_recipient,
):
    """Test finish auction"""
    price = AuctionParams.reserve_price + 100  # to make sure fee is calculated from price - reserve_price

    setup_auction_with_bid(status=AuctionStatus.ENDED, bid_amount=price)

    fee_recipient = accounts.at(erc1155_marketplace_mock.getFeeRecipient())
    initial_fee_recipient_amount = erc20_mock.balanceOf(fee_recipient)
    initial_royalty_recipient_amount = erc20_mock.balanceOf(royalty_recipient)
    initial_seller_amount = erc20_mock.balanceOf(seller)
    initial_marketplace_amount = erc20_mock.balanceOf(erc1155_marketplace_mock)

    initial_bidder_token_amount = erc1155_collection_mock.balanceOf(bidder, AuctionParams.token_id)
    initial_marketplace_token_amount = erc1155_collection_mock.balanceOf(
        erc1155_marketplace_mock, AuctionParams.token_id
    )

    fee = calculate_auction_fee(price, AuctionParams.reserve_price, erc1155_marketplace_mock.getAuctionFee())
    royalty_fee = calculate_royalty_fee(price - fee, RoyaltyParams.fraction)

    tx = erc1155_marketplace_mock.finishAuction(
        erc1155_collection_mock, AuctionParams.token_id, seller, {'from': seller}
    )

    # assert payment tokens sent
    assert erc20_mock.balanceOf(fee_recipient) == initial_fee_recipient_amount + fee
    assert erc20_mock.balanceOf(royalty_recipient) == initial_royalty_recipient_amount + royalty_fee
    assert erc20_mock.balanceOf(seller) == initial_seller_amount + price - fee - royalty_fee
    assert erc20_mock.balanceOf(erc1155_marketplace_mock) == initial_marketplace_amount - price

    # assert tokens transferred
    assert erc1155_collection_mock.balanceOf(bidder, AuctionParams.token_id) == \
           initial_bidder_token_amount + AuctionParams.token_amount
    assert erc1155_collection_mock.balanceOf(erc1155_marketplace_mock, AuctionParams.token_id) == \
           initial_marketplace_token_amount - AuctionParams.token_amount

    # assert event emitted
    assert tx.events['AuctionFinished'] is not None
    assert tx.events['AuctionFinished']['oldOwner'] == seller.address
    assert tx.events['AuctionFinished']['nftAddress'] == erc1155_collection_mock.address
    assert tx.events['AuctionFinished']['tokenId'] == AuctionParams.token_id
    assert tx.events['AuctionFinished']['winner'] == bidder.address
    assert tx.events['AuctionFinished']['payToken'] == erc20_mock.address
    assert tx.events['AuctionFinished']['tokenAmount'] == AuctionParams.token_amount
    assert tx.events['AuctionFinished']['winningBid'] == price


def test_finish_auction_from_bidder(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        seller,
        bidder
):
    """Test finish auction from bidder"""
    setup_auction_with_bid(status=AuctionStatus.ENDED, bid_amount=AuctionParams.reserve_price)
    erc1155_marketplace_mock.finishAuction(erc1155_collection_mock, AuctionParams.token_id, seller, {'from': bidder})


def test_finish_auction_not_owner_or_bidder(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
        setup_auction_with_bid,
        seller,
        outbidder
):
    """Test finish auction when not owner or bidder"""
    setup_auction_with_bid(status=AuctionStatus.ENDED, bid_amount=AuctionParams.reserve_price)
    with reverts('MarketplaceBase: not auction or highest bid owner'):
        erc1155_marketplace_mock.finishAuction(
            erc1155_collection_mock, AuctionParams.token_id, seller, {'from': outbidder}
        )


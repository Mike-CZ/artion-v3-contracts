import pytest
from dataclasses import dataclass
from brownie import reverts, Wei, chain
from brownie.test import given, strategy
from utils.constants import WFTM_TOKEN


@dataclass(frozen=True)
class AuctionParams:
    token_id: int = 1
    token_amount: int = 10
    reserve_price: int = Wei('1 ether')
    start_time: int = chain.time() + (60 * 30)  # start auction at current time + 30 minutes
    end_time: int = start_time + (60 * 60 * 2)  # end auction in 2 hours from start
    pay_token: str = WFTM_TOKEN


@dataclass(frozen=True)
class HighestBidParams:
    bid_amount: int = Wei('2 ether')


@pytest.fixture(scope='module')
def setup_auction(erc1155_marketplace_mock, erc1155_collection_mock, user):
    def setup_auction_(is_min_bid_reserve_price: bool = False):
        erc1155_collection_mock.mint(user, AuctionParams.token_id, 50, '')
        erc1155_collection_mock.setApprovalForAll(erc1155_marketplace_mock, True, {'from': user})
        erc1155_marketplace_mock.createAuctionAndTransferToken(
            erc1155_collection_mock,
            AuctionParams.token_id,
            AuctionParams.token_amount,
            user,
            AuctionParams.pay_token,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            is_min_bid_reserve_price
        )
    return setup_auction_


@pytest.fixture(scope='module')
def erc1155_collection_mint_with_approval(erc1155_marketplace_mock, erc1155_collection_mock, erc1155_collection_mint):
    def erc1155_collection_mint_with_approval_(recipient, amount):
        token_id = erc1155_collection_mint(recipient, amount)
        erc1155_collection_mock.setApprovalForAll(erc1155_marketplace_mock, True, {'from': recipient})
        return token_id
    return erc1155_collection_mint_with_approval_


def test_create_auction(erc1155_marketplace_mock, erc1155_collection_mock, erc1155_collection_mint_with_approval, user):
    """Test auction creation"""
    token_amount = 5
    auction_token_amount = 2
    reserve_price = Wei('2 ether')
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
        WFTM_TOKEN,
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
        user
):
    """Test auction creation with invalid token type"""
    token_id = erc721_collection_mint(user)
    with reverts('ERC1155Marketplace: NFT not ERC1155'):
        erc1155_marketplace_mock.createAuction(
            erc721_collection_mock,
            token_id,
            1,
            AuctionParams.pay_token,
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
        user
):
    """Test auction creation without enough tokens"""
    token_id = erc1155_collection_mint(user, 5)
    with reverts('ERC1155Marketplace: balance too low'):
        erc1155_marketplace_mock.createAuction(
            erc1155_collection_mock,
            token_id,
            10,
            AuctionParams.pay_token,
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
        user
):
    """Test auction creation without approval"""
    token_id = erc1155_collection_mint(user, AuctionParams.token_amount)
    with reverts('ERC1155Marketplace: not approved'):
        erc1155_marketplace_mock.createAuction(
            erc1155_collection_mock,
            token_id,
            AuctionParams.token_amount,
            AuctionParams.pay_token,
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
        user
):
    """Test auction creation with invalid time - maximum duration"""
    token_id = erc1155_collection_mint_with_approval(user, AuctionParams.token_amount)
    with reverts('MarketplaceBase: Auction time exceeds maximum duration'):
        erc1155_marketplace_mock.createAuction(
            erc1155_collection_mock,
            token_id,
            AuctionParams.token_amount,
            AuctionParams.pay_token,
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
        user
):
    """Test auction creation with invalid time - minimum duration"""
    token_id = erc1155_collection_mint_with_approval(user, AuctionParams.token_amount)
    with reverts('MarketplaceBase: Auction time does not meet minimum duration'):
        erc1155_marketplace_mock.createAuction(
            erc1155_collection_mock,
            token_id,
            AuctionParams.token_amount,
            AuctionParams.pay_token,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.start_time + (erc1155_marketplace_mock.getMinimumAuctionDuration() - 1),
            False,
            {'from': user}
        )


def test_create_action_already_exists(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
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
            AuctionParams.pay_token,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            False,
            {'from': user}
        )


def test_place_bid(
        erc1155_marketplace_mock,
        erc1155_collection_mock,
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
            AuctionParams.pay_token,
            AuctionParams.reserve_price,
            AuctionParams.start_time,
            AuctionParams.end_time,
            False,
            {'from': user}
        )

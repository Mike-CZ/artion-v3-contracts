import pytest
from dataclasses import dataclass
from brownie import reverts, Wei, chain
from utils.constants import WFTM_TOKEN


@dataclass(frozen=True)
class AuctionParams:
    token_id: int = 1
    token_amount: int = 10
    reserve_price: int = Wei('1 ether')
    start_time: int = chain.time() + (60 * 30)  # start auction at current time + 30 minutes
    end_time: int = start_time + (60 * 60 * 2)  # end auction in 2 hours from start
    pay_token: str = WFTM_TOKEN


@pytest.fixture(scope='module')
def setup_auction(erc1155_marketplace_mock, erc1155_collection_mock, user):
    def setup_auction_(is_min_bid_reserve_price: bool = False):
        erc1155_collection_mock.mint(user, AuctionParams.token_id, AuctionParams.token_amount, '')
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


def test_create_auction(erc1155_marketplace_mock, erc1155_collection_mock, erc1155_collection_mint, user):
    """Test auction creation"""
    token_amount = 5
    auction_token_amount = 2
    reserve_price = Wei('2 ether')
    is_min_bid_reserve_price = False

    # start auction at current time + 1 hour
    start_time = chain.time() + (60 * 60)
    # end auction in 24 hours from start
    end_time = start_time + (60 * 60 * 24)

    # mint token and set approval
    token_id = erc1155_collection_mint(user, token_amount)
    erc1155_collection_mock.setApprovalForAll(erc1155_marketplace_mock, True, {'from': user})

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




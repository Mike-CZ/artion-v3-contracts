from brownie import chain, ERC20TokenMock, ERC1155CollectionMock
from brownie.test import strategy
from brownie.network import Accounts
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable, List, Dict, DefaultDict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import utils
from utils.helpers import calculate_auction_fee
import time
import random
import copy

ACCOUNT_ERC20_AMOUNT = 1_000_000


@dataclass(frozen=True)
class Auction:
    owner: str
    nft: str
    token_id: int
    token_amount: int
    pay_token: str
    reserve_price: int
    start_time: int
    end_time: int
    auction_id: int
    is_min_bid_reserve: bool


@dataclass(frozen=True)
class HighestBid:
    bidder: str
    bid_amount: int


MIN_AUCTION_DURATION = 60 * 5  # 5 minutes
MAX_AUCTION_DURATION = 60 * 60  # 1 hour


class StateMachine:
    st_address = strategy('address')

    def __init__(
            self,
            owner: LocalAccount,
            accounts: Accounts,
            erc1155_marketplace_mock: ProjectContract,
            payment_token_registry: ProjectContract
    ) -> None:
        self.owner = owner
        self.marketplace = erc1155_marketplace_mock
        self.payment_token_registry = payment_token_registry
        self.accounts = accounts
        self.available_accounts: List[LocalAccount] = list(filter(lambda x: x.address != owner.address, accounts))
        self.fee_recipient: LocalAccount = random.choice(self.available_accounts)

        random.seed(time.time())
        self.latestAuctionId = 1

        # dicts of deployed payment tokens and nf tokens
        self.erc20_contracts: Dict[str, ProjectContract] = {}
        self.erc1155_contracts: Dict[str, ProjectContract] = {}

        # dicts of account payment token balances and nf tokens balances
        self.balances: DefaultDict[str, DefaultDict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.nft_balances: DefaultDict[str, DefaultDict[str, DefaultDict[int, int]]] = \
            defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        self.auctions: List[Auction] = []
        self.bids: Dict[int, HighestBid] = {}

        StateMachine._init_payment_tokens(self)
        StateMachine._init_nft_tokens(self)
        self.initial_balances = copy.deepcopy(self.balances)
        self.initial_nft_balances = copy.deepcopy(self.nft_balances)
        self.marketplace.updateFeeRecipient(self.fee_recipient, {'from': self.owner})

    def setup(self) -> None:
        self.balances = copy.deepcopy(self.initial_balances)
        self.nft_balances = copy.deepcopy(self.initial_nft_balances)
        self.auctions.clear()
        self.bids.clear()

    def rule_create_auction(self) -> None:
        data = self._get_owner_with_nft()
        if data is None or data[0] == self.marketplace.address:
            return

        nft_owner, nft_contract, token_id, token_amount = data
        auction_amount = random.randint(1, token_amount)
        erc20 = random.choice(list(self.erc20_contracts.values()))
        price = random.randint(1, 10)
        start_time = chain.time() + random.randint(0, 50)
        end_time = start_time + random.randint(MIN_AUCTION_DURATION, MAX_AUCTION_DURATION)
        is_min_bid_reserve = bool(random.randint(0, 1))

        nft_contract.setApprovalForAll(self.marketplace, True, {'from': nft_owner})

        self.marketplace.createAuction(
            nft_contract,
            token_id,
            auction_amount,
            self.latestAuctionId,
            erc20,
            price,
            start_time,
            end_time,
            is_min_bid_reserve,
            {'from': nft_owner}
        )

        self._subtract_nft_amount(nft_owner, nft_contract, token_id, auction_amount)
        self._add_nft_amount(self.marketplace.address, nft_contract, token_id, auction_amount)
        self.auctions.append(
            Auction(
                nft_owner,
                nft_contract.address,
                token_id,
                auction_amount,
                erc20.address,
                price,
                start_time,
                end_time,
                self.latestAuctionId,
                is_min_bid_reserve
            )
        )

        self.latestAuctionId += 1

    def rule_bid(self) -> None:
        auction = self._get_biddable_auction()
        if auction is None:
            # try to create auction
            self.rule_create_auction()

        # check created successfully
        auction = self._get_biddable_auction()
        if auction is None:
            return

        # randomly select bidder
        bidder: LocalAccount = next(
            filter(lambda x: x.address != auction.owner, sorted(self.available_accounts, key=lambda k: random.random()))
        )

        erc20 = self.erc20_contracts[auction.pay_token]

        if auction.auction_id in self.bids:
            highest_bid = self.bids[auction.auction_id]
            min_bid_amount = highest_bid.bid_amount + random.randint(1, 20)
            # refund previous highest bid
            self._add_pay_token_amount(highest_bid.bidder, erc20, highest_bid.bid_amount)
            self._subtract_pay_token_amount(self.marketplace.address, erc20, highest_bid.bid_amount)
        else:
            min_bid_amount = auction.reserve_price if auction.is_min_bid_reserve else + random.randint(1, 20)

        bid_amount = random.randint(min_bid_amount, min_bid_amount + 10)

        erc20.approveInternal(bidder, self.marketplace, bid_amount)

        if auction.start_time > chain.time():
            chain.sleep(auction.start_time - chain.time())

        self.marketplace.placeBid(
            self.erc1155_contracts[auction.nft],
            auction.token_id,
            auction.owner,
            auction.auction_id,
            bid_amount,
            {'from': bidder}
        )

        self._subtract_pay_token_amount(bidder.address, erc20, bid_amount)
        self._add_pay_token_amount(self.marketplace.address, erc20, bid_amount)
        self.bids[auction.auction_id] = HighestBid(bidder.address, bid_amount)

    def rule_finish_auction(self) -> None:
        auction = self._get_finishable_auction()
        if auction is None:
            # try to bind on auction
            self.rule_bid()

        # check placed bid successfully
        auction = self._get_finishable_auction()
        if auction is None:
            return

        nft_contract = self.erc1155_contracts[auction.nft]
        bid = self.bids[auction.auction_id]

        if auction.end_time > chain.time():
            chain.sleep(auction.end_time - chain.time())

        if bid.bid_amount < auction.reserve_price:
            self.marketplace.finishAuctionBelowReservePrice(
                nft_contract,
                auction.token_id,
                auction.owner,
                auction.auction_id,
                {'from': auction.owner}
            )
        else:
            self.marketplace.finishAuction(
                nft_contract,
                auction.token_id,
                auction.owner,
                auction.auction_id,
                {'from': bid.bidder if random.randint(0, 1) == 1 else auction.owner}
            )

        fee = calculate_auction_fee(bid.bid_amount, self.marketplace.getAuctionFee())

        erc20 = self.erc20_contracts[auction.pay_token]
        self._subtract_pay_token_amount(self.marketplace.address, erc20, bid.bid_amount)
        self._add_pay_token_amount(auction.owner, erc20, bid.bid_amount - fee)
        self._add_pay_token_amount(self.fee_recipient.address, erc20, fee)
        self._subtract_nft_amount(self.marketplace.address, nft_contract, auction.token_id, auction.token_amount)
        self._add_nft_amount(bid.bidder, nft_contract, auction.token_id, auction.token_amount)

        self._delete_auction(auction)
        self.bids.pop(auction.auction_id)

    def rule_cancel_auction(self) -> None:
        auction = self._get_cancelable_auction()
        if auction is None:
            # try to create auction
            self.rule_create_auction()

        # check created successfully
        auction = self._get_cancelable_auction()
        if auction is None:
            return

        nft_contract = self.erc1155_contracts[auction.nft]

        self.marketplace.cancelAuction(
            nft_contract, auction.token_id, auction.auction_id, {'from': auction.owner}
        )

        self._subtract_nft_amount(self.marketplace.address, nft_contract, auction.token_id, auction.token_amount)
        self._add_nft_amount(auction.owner, nft_contract, auction.token_id, auction.token_amount)
        self._delete_auction(auction)

        # refund highest bid
        if auction.auction_id in self.bids:
            erc20 = self.erc20_contracts[auction.pay_token]
            highest_bid = self.bids[auction.auction_id]
            self._add_pay_token_amount(highest_bid.bidder, erc20, highest_bid.bid_amount)
            self._subtract_pay_token_amount(self.marketplace.address, erc20, highest_bid.bid_amount)
            self.bids.pop(auction.auction_id)

    def rule_withdraw_bid(self) -> None:
        auction = self._get_withdrawable_auction()
        if auction is None:
            # try to create auction
            self.rule_bid()

        # check created successfully
        auction = self._get_withdrawable_auction()
        if auction is None:
            return

        assert auction == 1

    def insvariant_payment_tokens(self) -> None:
        for owner_address, token_addresses in self.balances.items():
            for token_address, balance in token_addresses.items():
                assert balance == self.erc20_contracts[token_address].balanceOf(owner_address)

    def insvariant_nft_tokens(self) -> None:
        for owner_address, nft_addresses in self.nft_balances.items():
            for nft_address, tokens in nft_addresses.items():
                for token_id, amount in tokens.items():
                    assert amount == self.erc1155_contracts[nft_address].balanceOf(owner_address, token_id)

    def _get_owner_with_nft(self) -> Optional[Tuple[str, ProjectContract, int, int]]:
        for owner_address, nft_addresses in sorted(self.nft_balances.items(), key=lambda x: random.random()):
            for nft_address, tokens in sorted(nft_addresses.items(), key=lambda x: random.random()):
                for token_id, amount in sorted(tokens.items(), key=lambda x: random.random()):
                    if amount > 0:
                        return owner_address, self.erc1155_contracts[nft_address], token_id, amount
        return None

    def _get_withdrawable_auction(self) -> Optional[Auction]:
        found_auction = None
        for auction in sorted(self.auctions, key=lambda x: random.random()):
            if (found_auction is None or auction.end_time < found_auction.end_time) \
                    and auction.auction_id in self.bids \
                    and self.bids[auction.auction_id].bid_amount < auction.reserve_price:
                found_auction = auction
        return found_auction

    def _get_cancelable_auction(self) -> Optional[Auction]:
        found_auction = None
        for auction in sorted(self.auctions, key=lambda x: random.random()):
            if (found_auction is None or auction.end_time < found_auction.end_time) \
                    and (auction.auction_id not in self.bids
                         or self.bids[auction.auction_id].bid_amount < auction.reserve_price):
                found_auction = auction
        return found_auction

    def _get_finishable_auction(self) -> Optional[Auction]:
        found_auction = None
        for auction in sorted(self.auctions, key=lambda x: random.random()):
            if (found_auction is None or auction.end_time < found_auction.end_time) and auction.auction_id in self.bids:
                found_auction = auction
        return found_auction

    def _get_biddable_auction(self) -> Optional[Auction]:
        found_auction = None
        for auction in sorted(self.auctions, key=lambda x: random.random()):
            if (found_auction is None or auction.start_time < found_auction.start_time) and \
                    auction.end_time > chain.time():
                found_auction = auction
        return found_auction

    def _delete_auction(self, auction: Auction) -> None:
        self.auctions = list(filter(lambda x: x.auction_id != auction.auction_id, self.auctions))

    def _subtract_pay_token_amount(self, address: str, erc20_contract: ProjectContract, amount: int) -> None:
        self.balances[address][erc20_contract.address] -= amount

    def _add_pay_token_amount(self, address: str, erc20_contract: ProjectContract, amount: int) -> None:
        self.balances[address][erc20_contract.address] += amount

    def _subtract_nft_amount(self, address: str, nft_contract: ProjectContract, token_id: int, amount: int) -> None:
        self.nft_balances[address][nft_contract.address][token_id] -= amount

    def _add_nft_amount(self, address: str, nft_contract: ProjectContract, token_id: int, amount: int) -> None:
        self.nft_balances[address][nft_contract.address][token_id] += amount

    def _init_nft_tokens(self) -> None:
        # setup 3 different NFT contracts with 4 tokens per each
        for _ in range(1, 4):
            contract = ERC1155CollectionMock.deploy({'from': self.owner})
            self.erc1155_contracts[contract.address] = contract
            for token_id in range(1, 5):
                # randomly select nft owner and token amount
                token_owner = random.choice(self.available_accounts)
                token_amount = random.randint(1, 50)
                contract.mint(token_owner, token_id, token_amount, '')
                self.nft_balances[token_owner.address][contract.address][token_id] = token_amount

    def _init_payment_tokens(self) -> None:
        # setup 2 different payment tokens
        for x in range(1, 3):
            contract = ERC20TokenMock.deploy(
                utils.constants.TEST_TOKEN_NAME + str(x),
                utils.constants.TEST_TOKEN_SYMBOL + str(x),
                self.owner,
                utils.constants.TEST_TOKEN_OWNER_AMOUNT,
                {'from': self.owner}
            )
            self.payment_token_registry.add(contract, {'from': self.owner})
            self.erc20_contracts[contract.address] = contract

            # mint tokens for accounts
            for account in self.available_accounts:
                contract.mint(account, ACCOUNT_ERC20_AMOUNT)
                self.balances[account.address][contract.address] = ACCOUNT_ERC20_AMOUNT


def test_stateful(
        state_machine: Callable,
        owner: LocalAccount,
        accounts: Accounts,
        erc1155_marketplace_mock: ProjectContract,
        payment_token_registry: ProjectContract
) -> None:
    state_machine(
        StateMachine,
        owner,
        accounts,
        erc1155_marketplace_mock,
        payment_token_registry,
        settings={'max_examples': 50}
    )

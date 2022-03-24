from brownie import chain, ERC20TokenMock, ERC1155CollectionMock
from brownie.test import strategy
from brownie.network import Accounts
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable, List, Dict, DefaultDict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import utils
import random

ACCOUNT_ERC20_AMOUNT = 1_000_000


class StateMachine:
    st_address = strategy('address')

    def __init__(
        self,
        owner: LocalAccount,
        accounts: Accounts,
        erc1155_marketplace_mock: ProjectContract,
        payment_token_registry: ProjectContract
    ):
        self.owner = owner
        self.marketplace = erc1155_marketplace_mock
        self.payment_token_registry = payment_token_registry
        self.accounts = accounts
        self.available_accounts: List[LocalAccount] = list(filter(lambda x: x.address != owner.address, accounts))

        self.time = chain.time()

        # dicts of deployed payment tokens and nf tokens
        self.erc20_contracts: Dict[str, ProjectContract] = {}
        self.erc1155_contracts: Dict[str, ProjectContract] = {}

        # dicts of account payment token balances and nf tokens balances
        self.balances: DefaultDict[str, DefaultDict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.nft_balances: DefaultDict[str, DefaultDict[str, DefaultDict[int, int]]] = \
            defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        StateMachine._init_payment_tokens(self)
        StateMachine._init_nft_tokens(self)

    def rule_create_auction(self):
        data = self._get_owner_with_nft()
        if data is None or data[0] == self.marketplace.address:
            return

        nft_owner, nft_contract, token_id, token_amount = data
        auction_amount = random.randint(1, token_amount)
        erc20 = random.choice(list(self.erc20_contracts.values()))

        nft_contract.setApprovalForAll(self.marketplace, True, {'from': nft_owner})

        self.marketplace.createAuction(
            nft_contract,
            token_id,
            auction_amount,
            erc20,
            1,
            self.time + 1,
            self.time + 1000,
            False,
            {'from': nft_owner}
        )

        self._subtract_nft_amount(nft_owner, nft_contract, token_id, auction_amount)
        self._add_nft_amount(self.marketplace.address, nft_contract, token_id, auction_amount)

    def _get_owner_with_nft(self) -> Optional[Tuple[str, ProjectContract, int, int]]:
        for owner_address, nft_addresses in sorted(self.nft_balances.items(), key=lambda x: random.random()):
            for nft_address, tokens in sorted(nft_addresses.items(), key=lambda x: random.random()):
                for token_id, amount in sorted(tokens.items(), key=lambda x: random.random()):
                    if amount > 0:
                        return owner_address, self.erc1155_contracts[nft_address], token_id, amount
        return None

    def _subtract_nft_amount(self, address: str, nft_contract: ProjectContract, token_id: int, amount: int):
        self.nft_balances[address][nft_contract.address][token_id] -= amount

    def _add_nft_amount(self, address: str, nft_contract: ProjectContract, token_id: int, amount: int):
        self.nft_balances[address][nft_contract.address][token_id] += amount

    def _init_nft_tokens(self):
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

    def _init_payment_tokens(self):
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
):
    state_machine(
        StateMachine,
        owner,
        accounts,
        erc1155_marketplace_mock,
        payment_token_registry,
        settings={'max_examples': 5, 'deadline': 500}
    )

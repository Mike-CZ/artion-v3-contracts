from brownie import reverts, ERC20TokenMock, ERC1155CollectionMock
from brownie.test import strategy
from brownie.network import Accounts
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable, List, Dict, DefaultDict
from dataclasses import dataclass
import utils
import random

ACCOUNT_ERC20_AMOUNT = 1_000_000


@dataclass(frozen=True)
class NFT:
    contract: ProjectContract
    owner: LocalAccount
    token_amount: int


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
        self.accounts: List[LocalAccount] = list(filter(lambda x: x.address != owner.address, accounts))
        self.nft_tokens: Dict[str, Dict[int, NFT]] = {}
        self.payment_tokens: Dict[str, ProjectContract] = {}
        self.balances: Dict[str, Dict[str, int]] = {}
        self.nft_balances

        StateMachine._init_payment_tokens(self)
        StateMachine._init_nft_tokens(self)

    def _init_nft_tokens(self):
        # setup 3 different NFT contracts with 4 tokens per each
        for _ in range(1, 4):
            contract = ERC1155CollectionMock.deploy({'from': self.owner})
            self.nft_tokens[contract.address] = {}
            for token_id in range(1, 5):
                # randomly select nft owner and token amount
                token_owner = random.choice(self.accounts)
                token_amount = random.randint(1, 50)
                contract.mint(token_owner, token_id, token_amount, '')
                self.nft_tokens[contract.address][token_id] = NFT(contract, token_owner, token_amount)

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
            self.payment_tokens[contract.address] = contract

            # mint tokens for accounts
            for account in self.accounts:
                contract.mint(account, ACCOUNT_ERC20_AMOUNT)
                self.balances[account.address][contract.address] = ACCOUNT_ERC20_AMOUNT

    def rule_create_auction(self):
        assert len(self.accounts) == 9


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
        settings={'max_examples': 5}
    )

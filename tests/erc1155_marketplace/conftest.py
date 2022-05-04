import pytest
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable


@pytest.fixture(scope='module')
def erc1155_collection_mint_with_approval(
        erc1155_marketplace_mock: ProjectContract,
        erc1155_collection_mock: ProjectContract,
        erc1155_collection_mint: Callable
) -> Callable:
    def erc1155_collection_mint_with_approval_(recipient: LocalAccount, amount: int):
        token_id = erc1155_collection_mint(recipient, amount)
        erc1155_collection_mock.setApprovalForAll(erc1155_marketplace_mock, True, {'from': recipient})
        return token_id
    return erc1155_collection_mint_with_approval_

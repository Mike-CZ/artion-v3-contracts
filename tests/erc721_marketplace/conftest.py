import pytest
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable


@pytest.fixture(scope="module")
def erc721_collection_mint_with_approval(
        erc721_collection_mock: ProjectContract,
        erc721_collection_mint: Callable,
        erc721_marketplace_mock: ProjectContract
) -> Callable:
    def erc721_collection_mint_with_approval_(recipient: LocalAccount) -> int:
        # mint token and set approval
        token_id = erc721_collection_mint(recipient)
        erc721_collection_mock.approve(erc721_marketplace_mock, token_id, {'from': recipient})
        return token_id
    return erc721_collection_mint_with_approval_

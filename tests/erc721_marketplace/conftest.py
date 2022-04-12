import pytest


@pytest.fixture(scope="module")
def erc721_collection_mint_with_approval(erc721_collection_mock, erc721_collection_mint, erc721_marketplace_mock, user):
    # mint token and set approval
    token_id = erc721_collection_mint(user)
    erc721_collection_mock.approve(erc721_marketplace_mock, token_id, {'from': user})

    return token_id


@pytest.fixture(scope="module")
def payment_token(erc20_mock):
    return erc20_mock

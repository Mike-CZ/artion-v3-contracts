import pytest


@pytest.fixture(scope='module')
def erc1155_collection_mint_with_approval(erc1155_marketplace_mock, erc1155_collection_mock, erc1155_collection_mint):
    def erc1155_collection_mint_with_approval_(recipient, amount):
        token_id = erc1155_collection_mint(recipient, amount)
        erc1155_collection_mock.setApprovalForAll(erc1155_marketplace_mock, True, {'from': recipient})
        return token_id
    return erc1155_collection_mint_with_approval_

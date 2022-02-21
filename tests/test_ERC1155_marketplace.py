import pytest
from brownie import reverts, Wei, ERC721CollectionMock, accounts



def test_create_auction(erc1155_marketplace_mock, erc1155_collection_mock, erc1155_collection_mint, user):
    """Test auction creation"""
    amount = 10
    token_id = erc1155_collection_mint(user.address, amount)

    erc1155_marketplace_mock.createAuction(erc1155_collection_mock, token_id, amount, '0x0', 1, 1, 2, True)

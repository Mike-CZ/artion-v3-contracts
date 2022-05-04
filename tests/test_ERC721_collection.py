import pytest
from brownie import reverts, Wei, ERC721CollectionMock, accounts
from utils.constants import COLLECTION_MINT_FEE, COLLECTION_NAME, COLLECTION_SYMBOL, COLLECTION_MINT_FEE
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable


@pytest.fixture(scope="module")
def erc721_collection_private_mock(owner: LocalAccount) -> ProjectContract:
    return ERC721CollectionMock.deploy(
        COLLECTION_NAME,
        COLLECTION_SYMBOL,
        COLLECTION_MINT_FEE,
        owner.address,
        True,
        {'from': owner}
    )


def test_mint(erc721_collection_mock: ProjectContract, user: LocalAccount) -> None:
    """Test minting"""
    latest_token_id = erc721_collection_mock.getLatestTokenId()
    fee_recipient = accounts.at(erc721_collection_mock.getMintFeeRecipient())
    fee_recipient_initial_balance = fee_recipient.balance()

    # mint token
    tx = erc721_collection_mock.mint(
        user.address, 'some+uri', user.address, 500, {'from': user, 'amount': COLLECTION_MINT_FEE}
    )

    # get token id
    token_id = tx.return_value

    # assert token id has incremented
    assert token_id == latest_token_id + 1

    # assert fee recipient received minting fee
    assert fee_recipient.balance() == fee_recipient_initial_balance + COLLECTION_MINT_FEE

    # assert event has been emitted
    assert tx.events['Minted'] is not None


def test_mint_insufficient_funds(erc721_collection_mock: ProjectContract, user: LocalAccount) -> None:
    """Test mint insufficient funds"""
    with reverts('ERC721Collection: insufficient funds'):
        erc721_collection_mock.mint(
            user.address, 'some+uri', user.address, 0, {'from': user, 'amount': COLLECTION_MINT_FEE - 1}
        )


def test_mint_empty_uri(erc721_collection_mock: ProjectContract, user: LocalAccount) -> None:
    """Test mint empty uri"""
    with reverts('ERC721Collection: token URI empty'):
        erc721_collection_mock.mint(
            user.address, '', user.address, 0, {'from': user, 'amount': COLLECTION_MINT_FEE}
        )


def test_mint_private(erc721_collection_private_mock: ProjectContract, owner: LocalAccount) -> None:
    """Test private minting"""
    tx = erc721_collection_private_mock.mint(
        owner.address, 'some+uri', owner.address, 0, {'from': owner, 'amount': COLLECTION_MINT_FEE}
    )
    assert tx.return_value > 0


def test_mint_private_non_owner(erc721_collection_private_mock: ProjectContract, user: LocalAccount) -> None:
    """Test private minting for non-owner"""
    with reverts('ERC721Collection: only owner'):
        erc721_collection_private_mock.mint(
            user.address, 'some+uri', user.address, 0, {'from': user, 'amount': COLLECTION_MINT_FEE}
        )


def test_burn(erc721_collection_mock: ProjectContract, erc721_collection_mint: Callable, user: LocalAccount) -> None:
    """Test burning"""
    token_id = erc721_collection_mint(user.address)
    tx = erc721_collection_mock.burn(token_id, {'from': user})
    assert tx.events['Burned'] is not None


def test_burn_unauthorized(
        erc721_collection_mock: ProjectContract,
        erc721_collection_mint: Callable,
        user: LocalAccount,
        user_2: LocalAccount
) -> None:
    """Test unauthorized burning"""
    token_id = erc721_collection_mint(user.address)
    with reverts('ERC721Collection: only owner or approved'):
        erc721_collection_mock.burn(token_id, {'from': user_2})


def test_set_default_royalty(erc721_collection_mock: ProjectContract, owner: LocalAccount) -> None:
    """Test set default royalty"""
    erc721_collection_mock.setDefaultRoyalty(owner.address, 500, {'from': owner})
    # can not re-set royalty
    with reverts('ERC721Collection: default royalty already set'):
        erc721_collection_mock.setDefaultRoyalty(owner.address, 500, {'from': owner})


def test_set_default_royalty_unauthorized(erc721_collection_mock: ProjectContract, user: LocalAccount) -> None:
    """Test set default royalty - unauthorized"""
    with reverts('Ownable: caller is not the owner'):
        erc721_collection_mock.setDefaultRoyalty(user.address, 500, {'from': user})


def test_set_token_royalty(
        erc721_collection_mock: ProjectContract,
        erc721_collection_mint: Callable,
        user: LocalAccount
) -> None:
    """Test set default royalty"""
    token_id = erc721_collection_mint(user.address)
    erc721_collection_mock.setTokenRoyalty(token_id, user.address, 500, {'from': user})
    # can not re-set royalty
    with reverts('ERC721Collection: token royalty already set'):
        erc721_collection_mock.setTokenRoyalty(token_id, user.address, 500, {'from': user})


def test_set_token_royalty_unauthorized(
        erc721_collection_mock: ProjectContract,
        erc721_collection_mint: Callable,
        user: LocalAccount,
        user_2: LocalAccount
) -> None:
    """Test set token royalty - unauthorized"""
    token_id = erc721_collection_mint(user.address)
    with reverts('ERC721Collection: only owner or approved'):
        erc721_collection_mock.setTokenRoyalty(token_id, user.address, 500, {'from': user_2})


def test_update_default_royalty_recipient(
        erc721_collection_mock: ProjectContract,
        owner: LocalAccount,
        user: LocalAccount
) -> None:
    """Test update default royalty recipient"""
    # set royalty first
    erc721_collection_mock.setDefaultRoyalty(owner.address, 500, {'from': owner})
    # update recipient
    erc721_collection_mock.updateDefaultRoyaltyRecipient(user.address, {'from': owner})
    assert erc721_collection_mock.recipientOfDefaultRoyalty() == user.address


def test_update_default_royalty_recipient_unauthorized(
        erc721_collection_mock: ProjectContract,
        user: LocalAccount
) -> None:
    """Test update default royalty recipient - unauthorized"""
    with reverts('Ownable: caller is not the owner'):
        erc721_collection_mock.updateDefaultRoyaltyRecipient(user.address, {'from': user})


def test_update_token_royalty_recipient(
        erc721_collection_mock: ProjectContract,
        erc721_collection_mint: Callable,
        user: LocalAccount,
        user_2: LocalAccount
) -> None:
    """Test update token royalty recipient"""
    token_id = erc721_collection_mint(user.address, royalty_recipient=user.address, royalty_percent=500)
    erc721_collection_mock.updateTokenRoyaltyRecipient(token_id, user_2.address, {'from': user})
    assert erc721_collection_mock.recipientOfTokenRoyalty(token_id) == user_2.address


def test_update_token_royalty_recipient_unauthorized(
        erc721_collection_mock: ProjectContract,
        erc721_collection_mint: Callable,
        user: LocalAccount,
        user_2: LocalAccount
) -> None:
    """Test update token royalty recipient - unauthorized"""
    token_id = erc721_collection_mint(user.address)
    with reverts('ERC721Collection: only owner or approved'):
        erc721_collection_mock.updateTokenRoyaltyRecipient(token_id, user.address, {'from': user_2})


def test_update_mint_fee(
        erc721_collection_mock: ProjectContract,
        owner: LocalAccount
) -> None:
    """Test update mint fee"""
    tx = erc721_collection_mock.updateMintFee(Wei('2 ether'), {'from': owner})
    assert erc721_collection_mock.getMintFee() == Wei('2 ether')
    assert tx.events['UpdatedMintFee'] is not None


def test_update_mint_fee_unauthorized(
        erc721_collection_mock: ProjectContract,
        user: LocalAccount
) -> None:
    """Test update mint fee - unauthorized"""
    with reverts('Ownable: caller is not the owner'):
        erc721_collection_mock.updateMintFee(Wei('2 ether'), {'from': user})


def test_update_mint_fee_recipient(
        erc721_collection_mock: ProjectContract,
        owner: LocalAccount,
        user: LocalAccount
) -> None:
    """Test update mint fee recipient"""
    tx = erc721_collection_mock.updateMintFeeRecipient(user.address, {'from': owner})
    assert erc721_collection_mock.getMintFeeRecipient() == user.address
    assert tx.events['UpdatedMintFeeRecipient'] is not None


def test_update_mint_fee_recipient_unauthorized(
        erc721_collection_mock: ProjectContract,
        user: LocalAccount
) -> None:
    """Test update mint fee recipient - unauthorized"""
    with reverts('Ownable: caller is not the owner'):
        erc721_collection_mock.updateMintFeeRecipient(user.address, {'from': user})

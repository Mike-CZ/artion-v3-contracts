import pytest
from dataclasses import dataclass
from brownie import reverts
from brownie.test import given, strategy


@pytest.fixture(scope="session")
def royalty_recipient(user):
    return user


@pytest.fixture(scope="session")
def token_owner(user_2):
    return user_2


@dataclass(frozen=True)
class RoyaltyParams:
    fraction: int = 1_000  # 10%


@dataclass(frozen=True)
class TokenParams:
    token_id: int = 1_000_000


@pytest.fixture(scope='module')
def setup_registry_with_default(royalty_registry, erc1155_collection_mock, royalty_recipient, owner):
    def setup_registry_with_default_():
        royalty_registry.setDefaultRoyalty(
            erc1155_collection_mock, royalty_recipient, RoyaltyParams.fraction, {'from': owner}
        )
    return setup_registry_with_default_


@pytest.fixture(scope='module')
def setup_registry_with_token(royalty_registry, erc1155_collection_mock, royalty_recipient, token_owner):
    def setup_registry_with_token_():
        erc1155_collection_mock.mint(token_owner, TokenParams.token_id, 1, '')
        royalty_registry.setTokenRoyalty(
            erc1155_collection_mock,
            TokenParams.token_id,
            royalty_recipient,
            RoyaltyParams.fraction,
            {'from': token_owner}
        )
    return setup_registry_with_token_


@pytest.mark.parametrize("setup_function", ['setup_registry_with_default', 'setup_registry_with_token'])
def test_royalty_info(
        royalty_registry,
        setup_function,
        setup_registry_with_default,
        setup_registry_with_token,
        erc1155_collection_mock,
        royalty_recipient
):
    """Test royalty info"""

    # dynamically call setup function
    locals()[setup_function]()

    sale_price = 10_000

    (returned_recipient, royalty_amount) = royalty_registry.royaltyInfo(
        erc1155_collection_mock, TokenParams.token_id, sale_price
    )

    assert returned_recipient == royalty_recipient.address
    assert royalty_amount == sale_price * RoyaltyParams.fraction / 10_000


def test_set_default_royalty(royalty_registry, erc1155_collection_mock, royalty_recipient, owner):
    """Test set default royalty"""
    royalty_registry.setDefaultRoyalty(
        erc1155_collection_mock, royalty_recipient, RoyaltyParams.fraction, {'from': owner}
    )


def test_set_default_royalty_supports_setter(royalty_registry, erc721_collection_mock, royalty_recipient, owner):
    """Test set default royalty when supports setter"""
    with reverts('RoyaltyRegistry: supports royalty setter'):
        royalty_registry.setDefaultRoyalty(
            erc721_collection_mock, royalty_recipient, RoyaltyParams.fraction, {'from': owner}
        )


def test_set_default_royalty_too_high(royalty_registry, erc1155_collection_mock, royalty_recipient, owner):
    """Test set default royalty too high"""
    with reverts('RoyaltyRegistry: royalty too high'):
        royalty_registry.setDefaultRoyalty(
            erc1155_collection_mock, royalty_recipient, 20_000, {'from': owner}
        )


def test_set_default_royalty_already_set(
    setup_registry_with_default,
    royalty_registry,
    erc1155_collection_mock,
    royalty_recipient,
    owner
):
    """Test set default royalty when already set"""
    setup_registry_with_default()
    with reverts('RoyaltyRegistry: royalty set'):
        royalty_registry.setDefaultRoyalty(
            erc1155_collection_mock, royalty_recipient, RoyaltyParams.fraction, {'from': owner}
        )


def test_set_default_royalty_unauthorized(royalty_registry, erc1155_collection_mock, royalty_recipient, user):
    """Test set default royalty - unauthorized"""
    with reverts('Ownable: caller is not the owner'):
        royalty_registry.setDefaultRoyalty(
            erc1155_collection_mock, royalty_recipient, RoyaltyParams.fraction, {'from': user}
        )


def test_set_token_royalty(
        royalty_registry,
        erc1155_collection_mint,
        erc1155_collection_mock,
        royalty_recipient,
        token_owner
):
    """Test set token royalty"""
    token_id = erc1155_collection_mint(token_owner)
    royalty_registry.setTokenRoyalty(
        erc1155_collection_mock, token_id, royalty_recipient, RoyaltyParams.fraction, {'from': token_owner}
    )


def test_set_token_royalty_supports_setter(
        royalty_registry,
        erc721_collection_mint,
        erc721_collection_mock,
        royalty_recipient,
        token_owner
):
    """Test set token royalty when supports setter"""
    token_id = erc721_collection_mint(token_owner)
    with reverts('RoyaltyRegistry: supports royalty setter'):
        royalty_registry.setTokenRoyalty(
            erc721_collection_mock, token_id, royalty_recipient, RoyaltyParams.fraction, {'from': token_owner}
        )


def test_set_token_royalty_not_owner(
        royalty_registry,
        erc1155_collection_mint,
        erc1155_collection_mock,
        royalty_recipient,
        token_owner
):
    """Test set token royalty when not token owner"""
    token_id = erc1155_collection_mint(token_owner)
    with reverts('RoyaltyRegistry: not owner'):
        royalty_registry.setTokenRoyalty(
            erc1155_collection_mock, token_id, royalty_recipient, RoyaltyParams.fraction, {'from': royalty_recipient}
        )


def test_set_token_royalty_too_high(
        royalty_registry,
        erc1155_collection_mint,
        erc1155_collection_mock,
        royalty_recipient,
        token_owner
):
    """Test set token royalty too high"""
    token_id = erc1155_collection_mint(token_owner)
    with reverts('RoyaltyRegistry: royalty too high'):
        royalty_registry.setTokenRoyalty(
            erc1155_collection_mock, token_id, royalty_recipient, 20_000, {'from': token_owner}
        )


def test_set_token_royalty_already_set(
        setup_registry_with_token,
        royalty_registry,
        erc1155_collection_mock,
        royalty_recipient,
        token_owner
):
    """Test set token royalty when already set"""
    setup_registry_with_token()
    with reverts('RoyaltyRegistry: royalty set'):
        royalty_registry.setTokenRoyalty(
            erc1155_collection_mock,
            TokenParams.token_id,
            royalty_recipient,
            RoyaltyParams.fraction,
            {'from': token_owner}
        )


def test_update_default_royalty_recipient(
        setup_registry_with_default,
        royalty_registry,
        erc1155_collection_mock,
        royalty_recipient,
        owner
):
    """Test update default royalty recipient"""
    setup_registry_with_default()
    royalty_registry.updateDefaultRoyaltyRecipient(erc1155_collection_mock, owner, {'from': royalty_recipient})


def test_update_default_royalty_recipient_not_current(
        setup_registry_with_default,
        royalty_registry,
        erc1155_collection_mock,
        owner
):
    """Test update default royalty recipient when not current recipient"""
    setup_registry_with_default()
    with reverts('RoyaltyRegistry: not current recipient'):
        royalty_registry.updateDefaultRoyaltyRecipient(erc1155_collection_mock, owner, {'from': owner})


def test_update_token_royalty_recipient(
        setup_registry_with_token,
        royalty_registry,
        erc1155_collection_mock,
        royalty_recipient,
        owner
):
    """Test update token royalty recipient"""
    setup_registry_with_token()
    royalty_registry.updateTokenRoyaltyRecipient(
        erc1155_collection_mock, TokenParams.token_id, owner, {'from': royalty_recipient}
    )


def test_update_token_royalty_recipient_not_current(
        setup_registry_with_token,
        royalty_registry,
        erc1155_collection_mock,
        owner
):
    """Test update token royalty recipient when not current recipient"""
    setup_registry_with_token()
    with reverts('RoyaltyRegistry: not current recipient'):
        royalty_registry.updateTokenRoyaltyRecipient(
            erc1155_collection_mock, TokenParams.token_id, owner, {'from': owner}
        )

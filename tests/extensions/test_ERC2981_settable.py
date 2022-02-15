import pytest
from brownie import reverts, ERC2981SettableMock
from brownie.test import given, strategy
from hypothesis import settings


MAX_EXAMPLES = 5


@pytest.fixture(scope='module')
def erc2981_settable(user):
    return ERC2981SettableMock.deploy({'from': user})


@given(
    address=strategy('address'),
    royalty_percent=strategy('uint96', max_value=10000),
)
@settings(max_examples=MAX_EXAMPLES)
def test_set_default_royalty(erc2981_settable, address, royalty_percent):
    """Test setter for default royalty"""
    erc2981_settable.setDefaultRoyalty(address, royalty_percent)
    assert erc2981_settable.recipientOfDefaultRoyalty() == address
    assert erc2981_settable.royaltyFractionOfDefault() == royalty_percent


@given(
    address=strategy('address'),
    new_address=strategy('address'),
    royalty_percent=strategy('uint96', max_value=10000),
)
@settings(max_examples=MAX_EXAMPLES)
def test_default_royalty_update_recipient(erc2981_settable, address, new_address, royalty_percent):
    """Test default royalty recipient update"""
    erc2981_settable.setDefaultRoyalty(address, royalty_percent)
    erc2981_settable.updateDefaultRoyaltyRecipient(new_address)
    assert new_address == erc2981_settable.recipientOfDefaultRoyalty()


@given(address=strategy('address'))
@settings(max_examples=MAX_EXAMPLES)
def test_default_royalty_update_recipient_not_set(erc2981_settable, address):
    """Test default royalty recipient can not be updated without setting it first"""
    with reverts('ERC2981Settable: default royalty is not set'):
        erc2981_settable.updateDefaultRoyaltyRecipient(address)


@given(
    address=strategy('address'),
    royalty_percent=strategy('uint96', max_value=10000),
    token_id=strategy('uint256', min_value=1),
)
@settings(max_examples=MAX_EXAMPLES)
def test_set_token_royalty(erc2981_settable, address, royalty_percent, token_id):
    """Test setter for token royalty"""
    erc2981_settable.setTokenRoyalty(token_id, address, royalty_percent)
    assert erc2981_settable.recipientOfTokenRoyalty(token_id) == address
    assert erc2981_settable.royaltyFractionOfToken(token_id) == royalty_percent


@given(
    address=strategy('address'),
    new_address=strategy('address'),
    royalty_percent=strategy('uint96', max_value=10000),
    token_id=strategy('uint256', min_value=1),
)
@settings(max_examples=MAX_EXAMPLES)
def test_token_royalty_update_recipient(erc2981_settable, token_id, address, new_address, royalty_percent):
    """Test token royalty recipient update"""
    erc2981_settable.setTokenRoyalty(token_id, address, royalty_percent)
    erc2981_settable.updateTokenRoyaltyRecipient(token_id, new_address)
    assert new_address == erc2981_settable.recipientOfTokenRoyalty(token_id)


@given(
    address=strategy('address'),
    token_id=strategy('uint256', min_value=1),
)
@settings(max_examples=MAX_EXAMPLES)
def test_token_royalty_update_recipient_not_set(erc2981_settable, token_id, address):
    """Test token royalty recipient can not be updated without setting it first"""
    with reverts('ERC2981Settable: token royalty is not set'):
        erc2981_settable.updateTokenRoyaltyRecipient(token_id, address)

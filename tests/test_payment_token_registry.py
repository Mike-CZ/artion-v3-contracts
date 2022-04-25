from brownie import reverts, PaymentTokenRegistry
from brownie.test import given, strategy
from utils.constants import TOMB_TOKEN
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount


def test_add_when_not_owner(payment_token_registry: ProjectContract, user: LocalAccount) -> None:
    with reverts("Ownable: caller is not the owner"):
        payment_token_registry.add(TOMB_TOKEN, {"from": user})


@given(token_address=strategy('address'))
def test_add_token(
        payment_token_registry: ProjectContract,
        token_address: LocalAccount,
        owner: LocalAccount
) -> None:
    assert payment_token_registry.isEnabled(token_address) is False

    tx = payment_token_registry.add(token_address, {"from": owner})

    assert payment_token_registry.isEnabled(token_address)
    assert len(tx.events) == 1
    assert tx.events["PaymentTokenAdded"] is not None
    assert tx.events["PaymentTokenAdded"]["token"] == token_address


def test_add_already_enabled_token(payment_token_registry: ProjectContract, owner: LocalAccount) -> None:
    with reverts("PaymentTokenRegistry: payment token already added"):
        payment_token_registry.add(TOMB_TOKEN, {"from": owner})


def test_remove_when_not_owner(payment_token_registry: ProjectContract, user: LocalAccount) -> None:
    with reverts("Ownable: caller is not the owner"):
        payment_token_registry.remove(TOMB_TOKEN, {"from": user})


def test_remove_token(payment_token_registry: ProjectContract, owner: LocalAccount) -> None:
    tx = payment_token_registry.remove(TOMB_TOKEN, {"from": owner})

    assert payment_token_registry.isEnabled(TOMB_TOKEN) is False
    assert len(tx.events) == 1
    assert tx.events["PaymentTokenRemoved"] is not None
    assert tx.events["PaymentTokenRemoved"]["token"] == TOMB_TOKEN


@given(token_address=strategy('address'))
def test_remove_non_existent_token(
        payment_token_registry: ProjectContract,
        token_address: LocalAccount,
        owner: LocalAccount
) -> None:
    with reverts("PaymentTokenRegistry: payment token does not exist"):
        payment_token_registry.remove(token_address, {"from": owner})


def test_remove_already_removed_token(payment_token_registry: ProjectContract, owner: LocalAccount) -> None:
    payment_token_registry.remove(TOMB_TOKEN, {"from": owner})
    with reverts("PaymentTokenRegistry: payment token does not exist"):
        payment_token_registry.remove(TOMB_TOKEN, {"from": owner})

import pytest
from brownie import accounts, reverts
from brownie.test import given, strategy


class TestAdd:
    def test_add_when_not_owner(self, payment_token_registry, payment_token_addresses):
        with reverts("Ownable: caller is not the owner"):
            payment_token_registry.add(payment_token_addresses["TOMB"], {"from": accounts[1]})

    @given(token_address=strategy('address'))
    def test_add_single_token(self, payment_token_registry, token_address):
        assert payment_token_registry.enabled(token_address) is False

        payment_token_registry.add(token_address, {"from": accounts[0]})

        assert payment_token_registry.enabled(token_address)

    def test_add_already_enabled_token(self, payment_token_registry, payment_token_addresses):
        payment_token_registry.add(payment_token_addresses["TOMB"], {"from": accounts[0]})

        with reverts("PaymentTokenRegistry: payment token already added"):
            payment_token_registry.add(payment_token_addresses["TOMB"], {"from": accounts[0]})

    def test_add_single_token_emits_event(self, payment_token_registry, payment_token_addresses):
        tx = payment_token_registry.add(payment_token_addresses["TOMB"], {"from": accounts[0]})

        assert len(tx.events) == 1
        assert tx.events["PaymentTokenAdded"] is not None
        assert tx.events["PaymentTokenAdded"]["token"] == payment_token_addresses["TOMB"]

    def test_add_multiple_tokens(self, payment_token_registry, payment_token_addresses):
        assert payment_token_registry.enabled(payment_token_addresses["TOMB"]) is False
        assert payment_token_registry.enabled(payment_token_addresses["WFTM"]) is False
        assert payment_token_registry.enabled(payment_token_addresses["ZOO"]) is False

        payment_token_registry.add(payment_token_addresses["TOMB"], {"from": accounts[0]})
        payment_token_registry.add(payment_token_addresses["WFTM"], {"from": accounts[0]})
        payment_token_registry.add(payment_token_addresses["ZOO"], {"from": accounts[0]})

        assert payment_token_registry.enabled(payment_token_addresses["TOMB"])
        assert payment_token_registry.enabled(payment_token_addresses["WFTM"])
        assert payment_token_registry.enabled(payment_token_addresses["ZOO"])

    def test_add_multiple_tokens_emits_events(self, payment_token_registry, payment_token_addresses):
        tx1 = payment_token_registry.add(payment_token_addresses["ZOO"], {"from": accounts[0]})

        assert len(tx1.events) == 1
        assert tx1.events["PaymentTokenAdded"] is not None
        assert tx1.events["PaymentTokenAdded"]["token"] == payment_token_addresses["ZOO"]

        tx2 = payment_token_registry.add(payment_token_addresses["TOMB"], {"from": accounts[0]})

        assert len(tx2.events) == 1
        assert tx2.events["PaymentTokenAdded"] is not None
        assert tx2.events["PaymentTokenAdded"]["token"] == payment_token_addresses["TOMB"]

        tx3 = payment_token_registry.add(payment_token_addresses["WFTM"], {"from": accounts[0]})

        assert len(tx3.events) == 1
        assert tx3.events["PaymentTokenAdded"] is not None
        assert tx3.events["PaymentTokenAdded"]["token"] == payment_token_addresses["WFTM"]

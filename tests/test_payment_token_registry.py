import pytest
from brownie import accounts, reverts
from brownie.test import given, strategy
from utils.constants import TOMB_TOKEN, WFTM_TOKEN, ZOO_TOKEN


class TestAdd:
    def test_add_when_not_owner(self, payment_token_registry, user):
        with reverts("Ownable: caller is not the owner"):
            payment_token_registry.add(TOMB_TOKEN, {"from": user})

    @given(token_address=strategy('address'))
    def test_add_single_token(self, payment_token_registry, token_address, owner):
        assert payment_token_registry.isEnabled(token_address) is False

        payment_token_registry.add(token_address, {"from": owner})

        assert payment_token_registry.isEnabled(token_address)

    @pytest.mark.no_payment_token_registry_init
    def test_add_already_enabled_token(self, payment_token_registry, owner):
        payment_token_registry.add(TOMB_TOKEN, {"from": owner})

        with reverts("PaymentTokenRegistry: payment token already added"):
            payment_token_registry.add(TOMB_TOKEN, {"from": owner})

    def test_add_single_token_emits_event(self, payment_token_registry, owner):
        tx = payment_token_registry.add(TOMB_TOKEN, {"from": owner})

        assert len(tx.events) == 1
        assert tx.events["PaymentTokenAdded"] is not None
        assert tx.events["PaymentTokenAdded"]["token"] == TOMB_TOKEN

    def test_add_multiple_tokens(self, payment_token_registry, owner):
        assert payment_token_registry.isEnabled(TOMB_TOKEN) is False
        assert payment_token_registry.isEnabled(WFTM_TOKEN) is False
        assert payment_token_registry.isEnabled(ZOO_TOKEN) is False

        payment_token_registry.add(TOMB_TOKEN, {"from": owner})
        payment_token_registry.add(WFTM_TOKEN, {"from": owner})
        payment_token_registry.add(ZOO_TOKEN, {"from": owner})

        assert payment_token_registry.isEnabled(TOMB_TOKEN)
        assert payment_token_registry.isEnabled(WFTM_TOKEN)
        assert payment_token_registry.isEnabled(ZOO_TOKEN)

    def test_add_multiple_tokens_emits_events(self, payment_token_registry, owner):
        tx1 = payment_token_registry.add(ZOO_TOKEN, {"from": owner})

        assert len(tx1.events) == 1
        assert tx1.events["PaymentTokenAdded"] is not None
        assert tx1.events["PaymentTokenAdded"]["token"] == ZOO_TOKEN

        tx2 = payment_token_registry.add(TOMB_TOKEN, {"from": owner})

        assert len(tx2.events) == 1
        assert tx2.events["PaymentTokenAdded"] is not None
        assert tx2.events["PaymentTokenAdded"]["token"] == TOMB_TOKEN

        tx3 = payment_token_registry.add(WFTM_TOKEN, {"from": owner})

        assert len(tx3.events) == 1
        assert tx3.events["PaymentTokenAdded"] is not None
        assert tx3.events["PaymentTokenAdded"]["token"] == WFTM_TOKEN


class TestRemove:
    def test_remove_when_not_owner(self, payment_token_registry, user):
        with reverts("Ownable: caller is not the owner"):
            payment_token_registry.remove(TOMB_TOKEN, {"from": user})

    def test_remove_single_token(self, payment_token_registry, owner):
        assert payment_token_registry.isEnabled(TOMB_TOKEN)

        payment_token_registry.remove(TOMB_TOKEN, {"from": owner})

        assert payment_token_registry.isEnabled(TOMB_TOKEN) is False

    @given(token_address=strategy('address'))
    def test_remove_non_existent_token(self, payment_token_registry, token_address, owner):
        with reverts("PaymentTokenRegistry: payment token does not exist"):
            payment_token_registry.remove(token_address, {"from": owner})

    def test_remove_already_removed_token(self, payment_token_registry, owner):
        payment_token_registry.remove(TOMB_TOKEN, {"from": owner})

        with reverts("PaymentTokenRegistry: payment token does not exist"):
            payment_token_registry.remove(TOMB_TOKEN, {"from": owner})

    def test_remove_single_token_emits_event(self, payment_token_registry, owner):
        tx = payment_token_registry.remove(TOMB_TOKEN, {"from": owner})

        assert len(tx.events) == 1
        assert tx.events["PaymentTokenRemoved"] is not None
        assert tx.events["PaymentTokenRemoved"]["token"] == TOMB_TOKEN

    def test_remove_multiple_tokens(self, payment_token_registry, owner):
        assert payment_token_registry.isEnabled(TOMB_TOKEN)
        assert payment_token_registry.isEnabled(WFTM_TOKEN)
        assert payment_token_registry.isEnabled(ZOO_TOKEN)

        payment_token_registry.remove(TOMB_TOKEN, {"from": owner})
        payment_token_registry.remove(WFTM_TOKEN, {"from": owner})
        payment_token_registry.remove(ZOO_TOKEN, {"from": owner})

        assert payment_token_registry.isEnabled(TOMB_TOKEN) is False
        assert payment_token_registry.isEnabled(WFTM_TOKEN) is False
        assert payment_token_registry.isEnabled(ZOO_TOKEN) is False

    def test_add_multiple_tokens_emits_events(self, payment_token_registry, owner):
        tx1 = payment_token_registry.remove(ZOO_TOKEN, {"from": owner})

        assert len(tx1.events) == 1
        assert tx1.events["PaymentTokenRemoved"] is not None
        assert tx1.events["PaymentTokenRemoved"]["token"] == ZOO_TOKEN

        tx2 = payment_token_registry.remove(TOMB_TOKEN, {"from": owner})

        assert len(tx2.events) == 1
        assert tx2.events["PaymentTokenRemoved"] is not None
        assert tx2.events["PaymentTokenRemoved"]["token"] == TOMB_TOKEN

        tx3 = payment_token_registry.remove(WFTM_TOKEN, {"from": owner})

        assert len(tx3.events) == 1
        assert tx3.events["PaymentTokenRemoved"] is not None
        assert tx3.events["PaymentTokenRemoved"]["token"] == WFTM_TOKEN

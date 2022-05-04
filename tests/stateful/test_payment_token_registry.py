from brownie import reverts
from brownie.test import strategy


class StateMachine:
    st_address = strategy('address')

    def __init__(self, owner, payment_token_registry):
        self.owner = owner
        self.registry = payment_token_registry

    def setup(self):
        self.addresses = {}

    def rule_add(self, st_address):
        """Add payment token into registry"""
        if self.addresses.get(st_address, False) is True:
            with reverts("PaymentTokenRegistry: payment token already added"):
                self.registry.add(st_address, {'from': self.owner})
        else:
            self.registry.add(st_address, {'from': self.owner})
            self.addresses[st_address] = True

    def rule_remove(self, st_address):
        """Remove payment token from registry"""
        if self.addresses.get(st_address, False) is True:
            self.registry.remove(st_address, {'from': self.owner})
            self.addresses[st_address] = False
        else:
            with reverts("PaymentTokenRegistry: payment token not exists"):
                self.registry.remove(st_address, {'from': self.owner})

    def invariant_address_status(self):
        """Validate addresses status"""
        for address, enabled in self.addresses.items():
            assert self.registry.isEnabled(address) == enabled


def test_stateful(owner, payment_token_registry, state_machine):
    state_machine(StateMachine, owner, payment_token_registry)

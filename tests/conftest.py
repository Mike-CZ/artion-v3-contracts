import pytest
from brownie import PaymentTokenRegistry, ERC721CollectionFactory, accounts


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def payment_token_registry():
    contract = accounts[0].deploy(PaymentTokenRegistry)
    return contract


@pytest.fixture(scope="module")
def erc721_collection_factory():
    contract = accounts[0].deploy(ERC721CollectionFactory, 5000000000000000000, accounts[0])
    return contract


@pytest.fixture(scope="session")
def payment_token_addresses():
    return {
        "TOMB": "0x6c021ae822bea943b2e66552bde1d2696a53fbb7",
        "ZOO": "0x09e145A1D53c0045F41aEEf25D8ff982ae74dD56",
        "WFTM": "0x21be370d5312f44cb42ce377bc9b8a0cef1a4c83"
    }

import pytest
from brownie import PaymentTokenRegistry, ERC721CollectionMock, ERC721CollectionFactory, accounts, ZERO_ADDRESS
import utils.constants


@pytest.fixture(scope="session")
def owner():
    return accounts[0]


@pytest.fixture(scope="session")
def user():
    return accounts[1]


@pytest.fixture(scope="session")
def user_2():
    return accounts[2]


@pytest.fixture(scope="session")
def user_3():
    return accounts[3]


@pytest.fixture(scope="module")
def erc721_collection_mock(owner):
    return ERC721CollectionMock.deploy(
        utils.constants.COLLECTION_NAME,
        utils.constants.COLLECTION_SYMBOL,
        utils.constants.COLLECTION_MINT_FEE,
        owner.address,
        False,
        {'from': owner}
    )


@pytest.fixture(scope="module")
def erc721_collection_private_mock(owner):
    return ERC721CollectionMock.deploy(
        utils.constants.COLLECTION_NAME,
        utils.constants.COLLECTION_SYMBOL,
        utils.constants.COLLECTION_MINT_FEE,
        owner.address,
        True,
        {'from': owner}
    )


@pytest.fixture(scope="function")
def erc721_collection_mint(erc721_collection_mock):
    return lambda recipient, token_uri='some+uri', royalty_recipient=ZERO_ADDRESS, royalty_percent=0: \
        erc721_collection_mock.mintAndGetTokenId(recipient, token_uri, royalty_recipient, royalty_percent).return_value


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


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


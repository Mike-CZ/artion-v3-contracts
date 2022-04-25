import pytest
from brownie import PaymentTokenRegistry, ERC721CollectionMock, ERC721CollectionFactory, ERC1155CollectionMock, \
    ERC1155MarketplaceMock, MarketplaceBaseMock, AddressRegistry, ERC20TokenMock, RoyaltyRegistry, accounts, \
    ERC721MarketplaceMock, ZERO_ADDRESS, Wei
import utils.constants
from brownie.network.contract import ProjectContract
from brownie.network.account import LocalAccount
from typing import Callable


@pytest.fixture(scope="session")
def owner() -> LocalAccount:
    return accounts[0]


@pytest.fixture(scope="session")
def user() -> LocalAccount:
    return accounts[1]


@pytest.fixture(scope="session")
def user_2() -> LocalAccount:
    return accounts[2]


@pytest.fixture(scope="session")
def user_3() -> LocalAccount:
    return accounts[3]


@pytest.fixture(scope="session")
def user_4() -> LocalAccount:
    return accounts[4]


@pytest.fixture(scope="module")
def erc20_mock(owner: LocalAccount, user: LocalAccount, user_2: LocalAccount, user_3: LocalAccount) -> ProjectContract:
    contract = ERC20TokenMock.deploy(
        utils.constants.TEST_TOKEN_NAME,
        utils.constants.TEST_TOKEN_SYMBOL,
        owner,
        utils.constants.TEST_TOKEN_OWNER_AMOUNT,
        {'from': owner}
    )
    contract.mint(user, utils.constants.TEST_TOKEN_USER_AMOUNT)
    contract.mint(user_2, utils.constants.TEST_TOKEN_USER_2_AMOUNT)
    contract.mint(user_3, utils.constants.TEST_TOKEN_USER_3_AMOUNT)
    return contract


@pytest.fixture(scope="module")
def payment_token(erc20_mock: ProjectContract) -> ProjectContract:
    return erc20_mock


@pytest.fixture(scope="module")
def payment_token_registry(owner: LocalAccount, erc20_mock: ProjectContract) -> ProjectContract:
    contract = PaymentTokenRegistry.deploy({'from': owner})
    contract.add(utils.constants.TOMB_TOKEN)
    contract.add(utils.constants.ZOO_TOKEN)
    contract.add(utils.constants.WFTM_TOKEN)
    contract.add(erc20_mock)
    return contract


@pytest.fixture(scope="module")
def royalty_registry(owner: LocalAccount) -> ProjectContract:
    return RoyaltyRegistry.deploy({'from': owner})


@pytest.fixture(scope="module")
def address_registry(
        payment_token_registry: ProjectContract,
        royalty_registry: ProjectContract,
        owner: LocalAccount
) -> ProjectContract:
    contract = AddressRegistry.deploy({'from': owner})
    contract.updatePaymentTokenRegistryAddress(payment_token_registry, {'from': owner})
    contract.updateRoyaltyRegistryAddress(royalty_registry, {'from': owner})
    return contract


@pytest.fixture(scope="module")
def erc1155_marketplace_mock(address_registry: ProjectContract, owner: LocalAccount) -> ProjectContract:
    return ERC1155MarketplaceMock.deploy(address_registry, owner, True, {'from': owner})


@pytest.fixture(scope="module")
def erc1155_collection_mock(owner: LocalAccount) -> ProjectContract:
    return ERC1155CollectionMock.deploy({'from': owner})


@pytest.fixture(scope="module")
def erc1155_collection_mint(erc1155_collection_mock: ProjectContract) -> Callable:
    return lambda recipient, amount=1: \
        erc1155_collection_mock.mintAndGetTokenId(recipient, amount).return_value


@pytest.fixture(scope="module")
def erc721_marketplace(address_registry: ProjectContract, owner: LocalAccount) -> ProjectContract:
    return ERC721Marketplace.deploy(address_registry, owner, True, {'from': owner})


@pytest.fixture(scope="module")
def erc721_marketplace_mock(address_registry, owner):
    return ERC721MarketplaceMock.deploy(address_registry, owner, True, {'from': owner})


@pytest.fixture(scope="module")
def erc721_collection_mock(owner: LocalAccount) -> ProjectContract:
    return ERC721CollectionMock.deploy(
        utils.constants.COLLECTION_NAME,
        utils.constants.COLLECTION_SYMBOL,
        utils.constants.COLLECTION_MINT_FEE,
        owner.address,
        False,
        {'from': owner}
    )


@pytest.fixture(scope="module")
def erc721_collection_mint(erc721_collection_mock: ProjectContract) -> Callable:
    return lambda recipient, token_uri='some+uri', royalty_recipient=ZERO_ADDRESS, royalty_percent=0: \
        erc721_collection_mock.mintAndGetTokenId(recipient, token_uri, royalty_recipient, royalty_percent).return_value


@pytest.fixture(scope="module")
def erc721_collection_factory() -> ProjectContract:
    contract = accounts[0].deploy(ERC721CollectionFactory, Wei('5 ether'), accounts[0])
    return contract


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation) -> None:
    # perform a chain rewind after completing each test, to ensure proper isolation
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


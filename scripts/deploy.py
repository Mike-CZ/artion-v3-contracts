import click
from brownie import AddressRegistry, PaymentTokenRegistry, RoyaltyRegistry, AddressRegistry, ERC721Marketplace, \
    ERC1155Marketplace, ERC721Collection, ERC721CollectionFactory, ProxyAdmin, TransparentUpgradeableProxy
from brownie import network, accounts
from brownie.network.account import LocalAccount
from eth_utils import is_address
from scripts.helpful_scripts import encode_function_data


def validate_eth_address(value):
    if not is_address(value):
        raise click.UsageError("Invalid address!")
    return value


def deploy_marketplace(account: LocalAccount) -> None:
    click.echo(f"You are deploying marketplace")
    auction_fee = click.prompt('Insert auction fee (assumed to be 1 decimal place i.e. 25 = 2,5%)',
                               type=click.IntRange(min=0))
    listing_fee = click.prompt('Insert listing fee (assumed to be 1 decimal place i.e. 25 = 2,5%)',
                               type=click.IntRange(min=0))
    offer_fee = click.prompt('Insert offer fee (assumed to be 1 decimal place i.e. 25 = 2,5%)',
                             type=click.IntRange(min=0))
    fee_recipient = click.prompt('Insert fee recipient address', value_proc=validate_eth_address)
    escrow_offer_tokens = click.prompt('Escrow offer tokens', type=click.BOOL)
    proxy_admin = click.prompt('Insert proxy admin address', value_proc=validate_eth_address)

    click.echo(
        f"""
    Marketplace Deployment Parameters
            auction fee: {auction_fee}
            listing fee: {listing_fee}
              offer fee: {offer_fee}
          fee recipient: {fee_recipient}
    escrow offer tokens: {escrow_offer_tokens}
            proxy admin: {proxy_admin}
    """
    )

    if not click.confirm("Deploy Marketplace"):
        return

    payment_token_registry = PaymentTokenRegistry.deploy({'from': account})
    royalty_registry = RoyaltyRegistry.deploy({'from': account})
    address_registry = AddressRegistry.deploy({'from': account})
    address_registry.updatePaymentTokenRegistryAddress(payment_token_registry, {'from': account})
    address_registry.updateRoyaltyRegistryAddress(royalty_registry, {'from': account})

    proxy_admin_contract = ProxyAdmin.deploy({"from": account})

    for marketplace in [ERC721Marketplace, ERC1155Marketplace]:
        marketplace_contract = marketplace.deploy({'from': account})
        TransparentUpgradeableProxy.deploy(
            marketplace_contract,
            proxy_admin_contract,
            encode_function_data(
                marketplace_contract.initialize,
                address_registry, auction_fee, listing_fee, offer_fee, fee_recipient, escrow_offer_tokens
            ),
            {'from': account}
        )

    proxy_admin_contract.transferOwnership(proxy_admin, {'from': account})

    click.echo("Marketplace successfully deployed")


def deploy_erc721_collection(account: LocalAccount) -> None:
    click.echo(f"You are deploying ERC721Collection")
    name = click.prompt('Insert name', type=click.STRING)
    symbol = click.prompt('Insert symbol', type=click.STRING)
    mint_fee = click.prompt('Insert mint fee', type=click.IntRange(min=0))
    fee_recipient = click.prompt('Insert mint fee recipient address', value_proc=validate_eth_address)
    is_private = click.prompt('Is private', type=click.BOOL)

    click.echo(
        f"""
    ERC721Collection Deployment Parameters
             name: {name}
           symbol: {symbol}
         mint fee: {mint_fee}
    fee recipient: {fee_recipient}
       is private: {is_private}
    """
    )

    if not click.confirm("Deploy ERC721Collection"):
        return

    ERC721Collection.deploy(name, symbol, mint_fee, fee_recipient, is_private, {'from': account})

    click.echo("ERC721Collection successfully deployed")


def deploy_erc721_collection_factory(account: LocalAccount) -> None:
    click.echo(f"You are deploying ERC721CollectionFactory")
    platform_fee = click.prompt('Insert platform fee', type=click.IntRange(min=0))
    fee_recipient = click.prompt('Insert platform fee recipient address', value_proc=validate_eth_address)

    click.echo(
        f"""
    ERC721CollectionFactory Deployment Parameters
     platform fee: {platform_fee}
    fee recipient: {fee_recipient}
    """
    )

    if not click.confirm("Deploy ERC721CollectionFactory"):
        return

    ERC721CollectionFactory.deploy(platform_fee, fee_recipient, {'from': account})

    click.echo("ERC721CollectionFactory successfully deployed")


def main():
    click.echo(f"You are using the '{network.show_active()}' network")
    account = accounts.load(click.prompt("Account", type=click.Choice(accounts.load())))
    click.echo(f"You are using account: {account.address}")

    click.echo(
        f"""
    Available deployments
    
    Marketplace => 1
    ERC721Collection => 2
    ERC721CollectionFactory => 3
    """
    )

    option = click.prompt('Select deployment by index', type=click.Choice(["1", "2", "3"]))

    if option == "1":
        deploy_marketplace(account)
    if option == "2":
        deploy_erc721_collection(account)
    if option == "3":
        deploy_erc721_collection_factory(account)





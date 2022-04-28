import click
from brownie import AddressRegistry, PaymentTokenRegistry
from brownie import network, accounts
from brownie.network.account import LocalAccount


def deploy_marketplace(account: LocalAccount) -> None:
    click.echo(f"You are using deploying marketplace")
    auction_fee = click.prompt('Insert auction fee (assumed to be 1 decimal place i.e. 25 = 2,5%)',
                               type=click.IntRange(min=0))
    listing_fee = click.prompt('Insert listing fee (assumed to be 1 decimal place i.e. 25 = 2,5%)',
                               type=click.IntRange(min=0))
    offer_fee = click.prompt('Insert offer fee (assumed to be 1 decimal place i.e. 25 = 2,5%)',
                             type=click.IntRange(min=0))
    fee_recipient = click.prompt('Insert fee recipient address', type=click.STRING)
    escrow_offer_tokens = click.prompt('Escrow offer tokens', type=click.BOOL)

    payment_token_registry = PaymentTokenRegistry.deploy({'from': account})
    print(payment_token_registry)




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





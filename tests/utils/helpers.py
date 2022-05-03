import math


def calculate_auction_fee(sell_price: int, percents: int) -> int:
    return math.floor(sell_price * percents / 1_000)


def calculate_listing_fee(sell_price: int, percents: int) -> int:
    return math.floor(sell_price * percents / 1_000)


def calculate_offer_fee(sell_price: int, percents: int) -> int:
    return math.floor(sell_price * percents / 1_000)


def calculate_royalty_fee(price: int, percents: int) -> int:
    return math.floor(price * percents / 10_000)


def encode_function_data(initializer=None, *args: tuple):
    """Encodes the function call so we can work with an initializer.
    Args:
        initializer ([brownie.network.contract.ContractTx], optional):
        The initializer function we want to call. Example: `box.store`.
        Defaults to None.
        args (Any, optional):
        The arguments to pass to the initializer function
    Returns:
        [bytes]: Return the encoded bytes.
    """
    if not len(args):
        args = b''

    if initializer:
        return initializer.encode_input(*args)

    return b''

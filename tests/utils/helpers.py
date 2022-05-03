import math


def calculate_auction_fee(sell_price: int, percents: int) -> int:
    return math.floor(sell_price * percents / 1_000)


def calculate_listing_fee(sell_price: int, percents: int) -> int:
    return math.floor(sell_price * percents / 1_000)


def calculate_offer_fee(sell_price: int, percents: int) -> int:
    return math.floor(sell_price * percents / 1_000)


def calculate_royalty_fee(price: int, percents: int) -> int:
    return math.floor(price * percents / 10_000)

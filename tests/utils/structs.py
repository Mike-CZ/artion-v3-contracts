from dataclasses import dataclass


@dataclass(frozen=True)
class Auction:
    owner: str
    payment_token: str
    reserve_price: int
    is_min_bid_reserve_price: bool
    start_time: int
    end_time: int

    def exists(self) -> bool:
        return self.start_time > 0


@dataclass(frozen=True)
class ERC1155Auction:
    auction: Auction
    token_amount: int

    def exists(self) -> bool:
        return self.auction.exists()


@dataclass(frozen=True)
class HighestBid:
    bidder: str
    bid_amount: int
    time: int

    def exists(self) -> bool:
        return self.bid_amount > 0


@dataclass(frozen=True)
class Listing:
    owner: str
    payment_token: str
    price: int
    starting_time: int

    def exists(self) -> bool:
        return self.starting_time > 0


@dataclass(frozen=True)
class ERC1155Listing:
    listing: Listing
    token_amount: int
    remaining_token_amount: int
    unit_size: int

    def exists(self) -> bool:
        return self.listing.exists()


@dataclass(frozen=True)
class Offer:
    payment_token: str
    offeror: str
    price: int
    expiration_time: int
    payment_token_in_escrow: bool

    def exists(self) -> bool:
        return self.expiration_time > 0


@dataclass(frozen=True)
class ERC1155Offer:
    offer: Offer
    token_amount: int

    def exists(self) -> bool:
        return self.offer.exists()

from dataclasses import dataclass


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
    total_token_amount: int
    buy_token_amount: int
    remaining_token_amount: int

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

from dataclasses import dataclass


@dataclass(frozen=True)
class Listing:
    owner: str
    payment_token: str
    price: int
    startingTime: int

    def exists(self) -> bool:
        return self.startingTime > 0


@dataclass(frozen=True)
class ERC1155Listing:
    listing: Listing
    totalTokenAmount: int
    buyTokenAmount: int
    remainingTokenAmount: int

    def exists(self) -> bool:
        return self.listing.exists()

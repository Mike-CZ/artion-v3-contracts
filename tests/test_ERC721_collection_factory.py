from brownie import Wei, accounts, reverts, ERC721Collection

class TestCreateERC721Collection:
    create_collection_fee = Wei("5 ether")  # fee recipient is accounts[0]

    def test_insufficient_funds(self, erc721_collection_factory):
        with reverts("ERC721CollectionFactory: Insufficient funds to create a collection"):
            erc721_collection_factory.createERC721Collection(
                "TestToken",
                "TT",
                Wei("2 ether"),
                accounts[0],
                False,
                {"from": accounts[0], "value": 1}
            )

    def test_transfer_platform_fee(self, erc721_collection_factory):
        fee_recipient_balance_before = accounts[0].balance()

        erc721_collection_factory.createERC721Collection(
            "TestToken",
            "TT",
            Wei("2 ether"),
            accounts[1],
            False,
            {"from": accounts[1], "value": self.create_collection_fee}
        )

        assert accounts[0].balance() == fee_recipient_balance_before + self.create_collection_fee

    def test_creates_collection_and_set_owner(self, erc721_collection_factory):
        tx = erc721_collection_factory.createERC721Collection(
            "TestToken",
            "TT",
            Wei("2 ether"),
            accounts[1],
            False,
            {"from": accounts[1], "value": self.create_collection_fee}
        )

        collection = ERC721Collection.at(tx.return_value)
        assert collection is not None
        assert collection._name == "ERC721Collection"
        assert collection.owner() == accounts[1]

    def test_emits_correct_event(self, erc721_collection_factory):
        tx = erc721_collection_factory.createERC721Collection(
            "TestToken",
            "TT",
            Wei("2 ether"),
            accounts[1],
            False,
            {"from": accounts[1], "value": self.create_collection_fee}
        )

        assert tx.events["ERC721CollectionCreated"] is not None
        assert tx.events["ERC721CollectionCreated"]["creator"] == accounts[1]
        assert tx.events["ERC721CollectionCreated"]["nft"] == tx.return_value

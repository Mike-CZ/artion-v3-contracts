interface IAddressRegistry {
    function marketplace() external view returns (address);

    function paymentTokenRegistry() external view returns (address);

    function royaltyRegistry() external view returns (address);
}

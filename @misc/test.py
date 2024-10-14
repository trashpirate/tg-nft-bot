from tg_nft_bot.nft.nft_operations import *

nftContract = "0xE9e5d3F02E91B8d3bc74Cf7cc27d6F13bdfc0BB6"
network = "base-mainnet"
token_id = "569"

fromAddress = "0xA4afbA149200B08E917A368C9cc9eD77d0c279a1"
toAddress = "0xA4afbA149200B08E917A368C9cc9eD77d0c279a1"
hash = "0x920ab11b589a03fe2960fba2f766af0e29848678432f928ff91c265a190b55e9"

info = {
    "type": "mint",
    "price": "N/A",
    "price_usd": "N/A",
    "currency": "N/A",
    "marketplace": "N/A",
}


def test_getNftData():

    data = getNftData(network, nftContract, token_id)
    print(data)


def test_get_metadata():

    [img, text] = get_metadata(
        network,
        nftContract,
        toAddress,
        token_id,
        hash,
        info,
    )
    print(img)
    print(text)


if __name__ == "__main__":

    test_getNftData()
    # test_get_metadata()

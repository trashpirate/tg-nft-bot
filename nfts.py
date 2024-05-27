from credentials import ALCHEMY_API_KEY_ETH, ALCHEMY_API_KEY_BASE, TABLE
import requests

from models import query_website_by_contract


async def getCollectionInfo(chain, contract):

    match chain:
        case "ETH_MAINNET":
            chain_tag = "eth-mainnet"
        case "BASE_MAINNET":
            chain_tag = "base-mainnet"
        case _:
            chain_tag = "eth-mainnet"

    url = f"https://{chain_tag}.g.alchemy.com/nft/v3/{ALCHEMY_API_KEY_ETH}/getContractMetadata?contractAddress={contract}"

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)
    data_json = response.json()
    return [data_json["name"], data_json["symbol"]]


async def getMetadata(contract, owner, tokenId, hash, chain):

    match chain:
        case "ETH_MAINNET":
            url = f"https://eth-mainnet.g.alchemy.com/nft/v3/{ALCHEMY_API_KEY_ETH}/getNFTMetadata?contractAddress={contract}&tokenId={tokenId}"
            opensea = f"https://opensea.io/assets/ethereum/{contract}/{tokenId}"
            rarible = f"https://rarible.com/token/{contract}:{tokenId}"
            magicEden = (
                f"https://magiceden.io/item-details/ethereum/{contract}/{tokenId}"
            )
            etherscan = "https://etherscan.io/"
        case "BASE_MAINNET":
            url = f"https://base-mainnet.g.alchemy.com/nft/v3/{ALCHEMY_API_KEY_BASE}/getNFTMetadata?contractAddress={contract}&tokenId={tokenId}"
            opensea = f"https://opensea.io/assets/base/{contract}/{tokenId}"
            rarible = f"https://rarible.com/token/base/{contract}:{tokenId}"
            magicEden = f"https://magiceden.io/item-details/base/{contract}/{tokenId}"
            etherscan = "https://basescan.org/"
        case _:
            url = f"https://eth-mainnet.g.alchemy.com/nft/v3/{ALCHEMY_API_KEY_ETH}/getNFTMetadata?contractAddress={contract}&tokenId={tokenId}"
            opensea = f"https://opensea.io/assets/ethereum/{contract}/{tokenId}"
            rarible = f"https://rarible.com/token/{contract}:{tokenId}"
            magicEden = (
                f"https://magiceden.io/item-details/ethereum/{contract}/{tokenId}"
            )
            etherscan = "https://etherscan.io/"

    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    data_json = response.json()

    contract_data = data_json["contract"]
    collection_name = contract_data["name"]
    total_supply = contract_data["totalSupply"]

    nft_name = data_json["name"]
    nft_metadata = data_json["raw"]["metadata"]
    nft_image = data_json["image"]["originalUrl"]

    [_, website] = query_website_by_contract(TABLE, contract)

    title = (f"NEW {collection_name} MINT!").upper()
    message = f"  \n<b>{title}</b>\n\n"

    message += (
        '<a href="' + etherscan + "tx/" + hash + '">' + f"<b>{nft_name}</b>" + "</a>\n"
    )

    message += f"Token ID: {tokenId}\n"
    short_address = f"{owner[:5]}...{owner[-3:]}"
    message += (
        'Owner: <a href="'
        + etherscan
        + "address/"
        + owner
        + '">'
        + short_address
        + "</a>\n"
    )

    if "attributes" in nft_metadata:
        message += "\n<u>Traits:</u>\n"
        for attr in nft_metadata["attributes"]:
            message += f'{attr["trait_type"]}: {attr["value"]}\n'

    message += f"\nTotal minted: {total_supply}\n"

    message += '<a href="' + website + '">Website</a> | '

    message += '<a href="' + opensea + '">Opensea</a> | '

    message += '<a href="' + rarible + '">Rarible</a> | '

    message += '<a href="' + magicEden + '">MagicEden</a>\n'

    message += "\n<i>Powered by @EARNServices</i>"
    return [nft_image, message]

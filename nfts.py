from credentials import (
    ALCHEMY_API_KEY_ETH,
    ALCHEMY_API_KEY_BASE,
    OPENSEA_API_KEY,
    TABLE,
)
import requests

from models import (
    query_name_by_contract,
    query_slug_by_contract,
    query_website_by_contract,
)
from graphql import RPC
import json

OPENSEA_API = {
    "ethereum-mainnet": "https://api.opensea.io/api/v2/chain/ethereum/",
    "bnbchain-mainnet": "https://api.opensea.io/api/v2/chain/bsc/",
    "base-mainnet": "https://api.opensea.io/api/v2/chain/base/",
    "avalanche-mainnet": "https://api.opensea.io/api/v2/chain/avalanche/",
    "arbitrum-mainnet": "https://api.opensea.io/api/v2/chain/arbitrum/",
    "polygon-mainnet": "https://api.opensea.io/api/v2/chain/matic/",
}

OPENSEA_LINK = {
    "ethereum-mainnet": "https://api.opensea.io/api/v2/chain/ethereum/",
    "bnbchain-mainnet": "https://api.opensea.io/api/v2/chain/bsc/",
    "base-mainnet": "https://api.opensea.io/api/v2/chain/base/",
    "avalanche-mainnet": "https://api.opensea.io/api/v2/chain/avalanche/",
    "arbitrum-mainnet": "https://api.opensea.io/api/v2/chain/arbitrum/",
    "polygon-mainnet": "https://api.opensea.io/api/v2/chain/matic/",
}

RARIBLE = {
    "ethereum-mainnet": "https://rarible.com/token/",
    "bnbchain-mainnet": "https://rarible.com/token/bsc/",
    "base-mainnet": "https://rarible.com/token/base/",
    "avalanche-mainnet": "https://rarible.com/token/avalanche/",
    "arbitrum-mainnet": "https://rarible.com/token/arbitrum/",
    "polygon-mainnet": "https://rarible.com/token/matic/",
}

MAGIC_EDEN = {
    "ethereum-mainnet": "https://magiceden.io/item-details/ethereum/",
    "bnbchain-mainnet": "https://magiceden.io/item-details/bsc/",
    "base-mainnet": "https://magiceden.io/item-details/base/",
    "avalanche-mainnet": "https://magiceden.io/item-details/avalanche/",
    "arbitrum-mainnet": "https://magiceden.io/item-details/arbitrum/",
    "polygon-mainnet": "https://magiceden.io/item-details/matic/",
}

SCANS = {
    "ethereum-mainnet": "https://etherscan.io",
    "bnbchain-mainnet": "https://bscscan.com/",
    "base-mainnet": "https://basescan.org/",
    "avalanche-mainnet": "https://snowtrace.io/",
    "arbitrum-mainnet": "https://arbiscan.io/",
    "polygon-mainnet": "https://polygonscan.com/",
}


async def getCollectionInfo(chain, contract):

    url = OPENSEA_API[chain] + "contract/" + contract

    headers = {
        "accept": "application/json",
        "x-api-key": OPENSEA_API_KEY,
    }
    response = requests.get(url, headers=headers)
    data_json = response.json()

    return [data_json["name"], data_json["collection"]]


async def getTotalSupply(slug):
    url = "https://api.opensea.io/api/v2/collections/" + slug

    headers = {
        "accept": "application/json",
        "x-api-key": OPENSEA_API_KEY,
    }
    response = requests.get(url, headers=headers)
    data_json = response.json()
    return data_json["total_supply"]


async def getMetadata(network, contract, owner, tokenId, hash, txType):

    collection_name = query_name_by_contract(network, contract)
    website = query_website_by_contract(contract)
    slug = query_slug_by_contract(network, contract)
    total_supply = getTotalSupply(slug)

    # get opensea data
    url = OPENSEA_API[network] + "contract/" + contract + "/nfts/" + tokenId
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    data_json = response.json()
    nft_data = data_json["nft"]

    nft_name = nft_data["name"]
    nft_image = nft_data["image_url"]

    opensea = nft_data["opensea_url"]
    rarible = RARIBLE[network] + contract + ":" + tokenId
    magicEden = MAGIC_EDEN[network] + contract + "/" + tokenId
    scan = SCANS[network]

    if txType == "mint":
        title = (f"NEW {collection_name} MINT!").upper()
    else:
        title = (f"NEW {collection_name} SELL!").upper()

    message = f"  \n<b>{title}</b>\n\n"

    message += (
        '<a href="' + scan + "tx/" + hash + '">' + f"<b>{nft_name}</b>" + "</a>\n"
    )

    message += f"Token ID: {tokenId}\n"
    short_address = f"{owner[:5]}...{owner[-3:]}"
    message += (
        'Owner: <a href="' + scan + "address/" + owner + '">' + short_address + "</a>\n"
    )

    if "traits" in nft_data:
        message += "\n<u>Traits:</u>\n"
        for attr in nft_data["traits"]:
            message += f'{attr["trait_type"]}: {attr["value"]}\n'

    message += f"\nTotal minted: {total_supply}\n"

    message += '<a href="' + website + '">Website</a> | '

    message += '<a href="' + opensea + '">Opensea</a> | '

    message += '<a href="' + rarible + '">Rarible</a> | '

    message += '<a href="' + magicEden + '">MagicEden</a>\n'

    message += "\n<i>Powered by @EARNServices</i>"
    return [nft_image, message]

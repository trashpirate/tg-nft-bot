from web3 import HTTPProvider, Web3
from credentials import (
    OPENSEA_API_KEY,
    RESERVOIR_API_KEY,
)
import requests
import json

from helpers import RPC
from models import (
    query_collection,
)

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
    "ethereum-mainnet": "https://etherscan.io/",
    "bnbchain-mainnet": "https://bscscan.com/",
    "base-mainnet": "https://basescan.org/",
    "avalanche-mainnet": "https://snowtrace.io/",
    "arbitrum-mainnet": "https://arbiscan.io/",
    "polygon-mainnet": "https://polygonscan.com/",
}

CURRENCY = {
    "ethereum-mainnet": "ETH",
    "bnbchain-mainnet": "BNB",
    "base-mainnet": "ETH",
    "avalanche-mainnet": "AVAX",
    "arbitrum-mainnet": "ETH",
    "polygon-mainnet": "MATIC",
}

RARIBLE_CHAINS = {
    "ethereum-mainnet": "ETHEREUM",
    "bnbchain-mainnet": "BNB",
    "base-mainnet": "BASE",
    "avalanche-mainnet": "AVAX",
    "arbitrum-mainnet": "ARBITRUM",
    "polygon-mainnet": "POLYGON",
}

RESERVOIR_URL = {
    "ethereum-mainnet": "https://api.reservoir.tools/",
    "bnbchain-mainnet": "https://api-bsc.reservoir.tools/",
    "base-mainnet": "https://api-base.reservoir.tools/",
    "avalanche-mainnet": "https://api-avalanche.reservoir.tools/",
    "arbitrum-mainnet": "https://api-arbitrum.reservoir.tools/",
    "polygon-mainnet": "https://api-polygon.reservoir.tools/",
}


def getSaleInfo(network, contract, tokenId):

    url = f"{RESERVOIR_URL[network]}tokens/{contract}%3A{tokenId}/activity/v5?limit=1&sortBy=eventTimestamp&types=sale"
    headers = {"accept": "*/*", "x-api-key": RESERVOIR_API_KEY}

    response = requests.get(url, headers=headers)
    data_json = response.json()

    events = data_json["activities"]
    if len(events) > 0:
        price_native = events[0]["price"]["amount"]["decimal"]
        price_usd = events[0]["price"]["amount"]["usd"]
        currency = events[0]["price"]["currency"]["symbol"]
        marketplace = events[0]["fillSource"]["name"]

        return {
            "type": events[0]["type"],
            "price": price_native,
            "price_usd": price_usd,
            "currency": currency,
            "marketplace": marketplace,
        }

    else:
        return None


def getCollectionInfo(network, contract):

    url = OPENSEA_API[network] + "contract/" + contract

    headers = {
        "accept": "application/json",
        "x-api-key": OPENSEA_API_KEY,
    }
    response = requests.get(url, headers=headers)
    data_json = response.json()

    return [data_json["name"], data_json["collection"]]


def getTotalSupply(slug):
    url = "https://api.opensea.io/api/v2/collections/" + slug

    headers = {
        "accept": "application/json",
        "x-api-key": OPENSEA_API_KEY,
    }
    response = requests.get(url, headers=headers)
    data_json = response.json()
    return data_json["total_supply"]


def getMetadata(network, contract, owner, tokenId, hash, info):

    tokenId = str(tokenId)
    collection = query_collection(network, contract)

    collection_name = collection["name"]
    slug = collection["slug"]
    website = collection["website"]

    total_supply = getTotalSupply(slug)

    # get opensea data
    url = OPENSEA_API[network] + "contract/" + contract + "/nfts/" + tokenId
    headers = {
        "accept": "application/json",
        "x-api-key": OPENSEA_API_KEY,
    }
    response = requests.get(url, headers=headers)
    data_json = response.json()

    nft_data = data_json["nft"]

    nft_name = nft_data["name"]
    nft_image = nft_data["image_url"]

    opensea = nft_data["opensea_url"]
    rarible = RARIBLE[network] + contract + ":" + tokenId
    magicEden = MAGIC_EDEN[network] + contract + "/" + tokenId
    scan = SCANS[network]

    if info["type"] == "mint":
        title = (f"NEW {collection_name} MINT! 🔥").upper()
        message = f"\n<b>{title}</b>\n\n"
    elif info["type"] == "sale":
        title = (f"NEW {collection_name} PURCHASE! 🔥").upper()
        message = f"\n<b>{title}</b>\n\n"

        price = info["price"]
        usd = info["price_usd"]
        currency = info["currency"]
        marketplace = info["marketplace"]
        message += f"Price: {price:.3f} {currency} ({usd:.3f} USD)\n"
        message += f"Marketplace: {marketplace.upper()}\n"

    message += f"\n<u><b>{nft_name}</b></u>\n"
    message += f"Token ID: {tokenId}\n"

    message += '<a href="' + scan + "address/" + owner + '">Owner</a> | '
    message += '<a href="' + scan + "tx/" + hash + '">TX Hash</a> | '
    message += '<a href="' + scan + "token/" + contract + "#code" + '">Contract</a>\n'

    if nft_data["traits"] is not None:
        message += "\n<u>Traits:</u>\n"
        for attr in nft_data["traits"]:
            message += f'{attr["trait_type"]}: {attr["value"]}\n'

    message += f"\nTotal minted: {total_supply}\n"

    message += '<a href="' + website + '">Website</a> | '

    message += '<a href="' + opensea + '">Opensea</a> | '

    message += '<a href="' + rarible + '">Rarible</a> | '

    message += '<a href="' + magicEden + '">MagicEden</a>\n'

    message += "\n\nAD: "
    message += (
        '<a href="https://t.me/EARNServices">Book a slot to show your ad here!</a>\n'
    )
    message += "\n<i>Powered by @EARNServices</i>"
    return [nft_image, message]

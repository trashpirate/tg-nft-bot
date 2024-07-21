import json
import traceback
from web3 import HTTPProvider, Web3
from credentials import (
    OPENSEA_API_KEY,
    RESERVOIR_API_KEY,
)
import requests
from PIL import Image
from io import BytesIO
import tempfile

from helpers import RPC
from models import (
    query_collection,
)
from urllib.request import urlopen

OPENSEA_NETWORK = {
    "ethereum-mainnet": "ethereum",
    "bnbchain-mainnet": "bsc",
    "base-mainnet": "base",
    "avalanche-mainnet": "avalanche",
    "arbitrum-mainnet": "arbitrum",
    "polygon-mainnet": "polygon",
}

OPENSEA_API = {
    "ethereum-mainnet": "https://api.opensea.io/api/v2/chain/ethereum/",
    "bnbchain-mainnet": "https://api.opensea.io/api/v2/chain/bsc/",
    "base-mainnet": "https://api.opensea.io/api/v2/chain/base/",
    "avalanche-mainnet": "https://api.opensea.io/api/v2/chain/avalanche/",
    "arbitrum-mainnet": "https://api.opensea.io/api/v2/chain/arbitrum/",
    "polygon-mainnet": "https://api.opensea.io/api/v2/chain/matic/",
}

OPENSEA = {
    "ethereum-mainnet": "https://opensea.io/assets/ethereum/",
    "bnbchain-mainnet": "https://opensea.io/assets/bsc/",
    "base-mainnet": "https://opensea.io/assets/base/",
    "avalanche-mainnet": "https://opensea.io/assets/avalanche/",
    "arbitrum-mainnet": "https://opensea.io/assets/arbitrum/",
    "polygon-mainnet": "https://opensea.io/assets/matic/",
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


def downloadImage(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content))
        file_extension = image.format.lower()  # e.g., 'jpeg' or 'png'
        if file_extension == "jpeg":
            file_extension = "jpg"

        # Create a temporary file to save the image
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{file_extension}"
        ) as tmp_file:
            image.save(tmp_file, format=image.format)
            temp_file_path = tmp_file.name
        return temp_file_path

    except Exception as e:
        print(e)
        raise


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
    data_json: dict = response.json()

    if "name" in data_json.keys() and len(data_json["name"]) > 0:
        name: str = data_json["name"]
    else:
        w3 = Web3(Web3.HTTPProvider(RPC[network]))

        with open("./assets/NFT.json", "r") as f:
            abi = json.load(f)
            contract_instance = w3.eth.contract(address=contract, abi=abi)
            name: str = contract_instance.functions.name.call()

    if "collection" in data_json.keys() and len(data_json["collection"]) > 0:
        collection = data_json["collection"]

    else:
        collection = name.replace(" ", "-")
        collection = collection.lower()

    return [name, collection]


def getTotalSupply(network, contract):
    # url = "https://api.opensea.io/api/v2/collections/" + slug

    # headers = {
    #     "accept": "application/json",
    #     "x-api-key": OPENSEA_API_KEY,
    # }
    # response = requests.get(url, headers=headers)
    # data_json = response.json()
    # return data_json["total_supply"]
    w3 = Web3(Web3.HTTPProvider(RPC[network]))

    with open("./assets/NFT.json", "r") as f:
        abi = json.load(f)
        contract_instance = w3.eth.contract(address=contract, abi=abi)
        totalSupply = contract_instance.functions.totalSupply().call()
        return totalSupply


def isValidImageUrl(url: str):

    try:
        # Send a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Try to open the image
            image = Image.open(BytesIO(response.content))
            # Try to load the image to ensure it is valid
            image.verify()
            return True
        else:
            print(f"Error: Received status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        traceback.print_exc()
        return False
    except (IOError, SyntaxError) as e:
        print(f"Invalid image: {e}")
        traceback.print_exc()
        return False


def isValidJsonUrl(url):
    try:
        # Send a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            try:
                # Try to parse the response content as JSON
                json_data = response.json()
                return True, json_data
            except ValueError as e:
                print(f"Invalid JSON: {e}")
                traceback.print_exc()
                return False, None
        else:
            print(f"Error: Received status code {response.status_code}")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        traceback.print_exc()
        return False, None


def getUrl(ipfsLink: str, isImage: bool = False):

    gateways = ["gateway.pinata.cloud", "dweb.link", "ipfs.io", "w3s.link"]

    for gateway in gateways:
        suburl = ipfsLink.replace("://", "/")
        url = "https://" + gateway + "/" + suburl

        if isImage:
            isValid = isValidImageUrl(url)
            if isValid:
                break
        else:
            isValid = isValidJsonUrl(url)
            if isValid:
                break
    print("URL: ", url)
    return url


def getNftData(network: str, contract: str, tokenId: str):
    w3 = Web3(Web3.HTTPProvider(RPC[network]))

    with open("./assets/NFT.json", "r") as f:
        abi = json.load(f)
        contract_instance = w3.eth.contract(address=contract, abi=abi)
        metadata_url = contract_instance.functions.tokenURI(
            Web3.to_int(int(tokenId))
        ).call()

    try:
        weburl = getUrl(metadata_url)  # "dweb.link"

        headers = {
            "accept": "application/json",
        }
        response = requests.get(weburl, headers=headers)
        data_json = response.json()
    except:
        print("Fetching metadata failed:")
        traceback.print_exc()

    return data_json


def getMetadata(network, contract, owner, tokenId, hash, info):

    tokenId = str(tokenId)
    collection = query_collection(network, contract)

    collection_name = collection["name"]
    slug = collection["slug"]
    website = collection["website"]

    total_supply = getTotalSupply(network, contract)

    nft_data = getNftData(network, contract, tokenId)

    nft_name = nft_data["name"]
    nft_image = getUrl(nft_data["image"], isImage=True)

    opensea = OPENSEA[network] + contract + "/" + tokenId
    rarible = RARIBLE[network] + contract + ":" + tokenId
    magicEden = MAGIC_EDEN[network] + contract + "/" + tokenId
    scan = SCANS[network]

    # message = '<a href="' + nft_image + '">&#8205;</a>'
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

    if nft_data["attributes"] is not None:
        message += "\n<u>Traits:</u>\n"
        for attr in nft_data["attributes"]:
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

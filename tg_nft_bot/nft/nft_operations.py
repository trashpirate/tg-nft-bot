import json
import traceback
from web3 import Web3
from tronpy import Tron
from tronpy.providers import HTTPProvider

import requests
from PIL import Image
from io import BytesIO
import tempfile
from urllib.request import urlopen

from tg_nft_bot.utils.credentials import (
    OPENSEA_API_KEY,
    RESERVOIR_API_KEY,
    TRONGRID_API_KEY,
)
from tg_nft_bot.nft.nft_constants import (
    MAGIC_EDEN,
    OPENSEA,
    OPENSEA_API,
    RARIBLE,
    RESERVOIR_URL,
)
from tg_nft_bot.utils.networks import RPC
from tg_nft_bot.db.db_operations import (
    query_collection,
)
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
abi_json = os.path.join(current_dir, "..", "..", "assets", "NFT.json")

gateways = ["gateway.pinata.cloud", "dweb.link", "ipfs.io", "w3s.link"]


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

    name = None

    try:
        if network == "tron-mainnet":
            try:
                client = Tron(HTTPProvider(api_key=TRONGRID_API_KEY))
                contract_instance = client.get_contract(contract)
                with open(abi_json, "r") as f:
                    contract_instance.abi = json.load(f)
                    name = contract_instance.functions.name()
            except Exception as e:
                print(f"TRON: {e}")
                raise e

        else:
            try:
                w3 = Web3(Web3.HTTPProvider(RPC[network]))
                with open(abi_json, "r") as f:
                    abi = json.load(f)
                    contract_instance = w3.eth.contract(address=contract, abi=abi)
                    name: str = contract_instance.functions.name.call()

            except Exception as e:
                print(f"EVM: {e}")
                raise e

    except Exception as e:
        print(f"Reading contract failed: {e}")

    finally:

        if name is not None:
            collection = name.replace(" ", "-")
            collection = collection.lower()
        else:
            collection = None

        return [name, collection]


def getTotalSupply(network, contract):

    totalSupply = None

    try:
        if network == "tron-mainnet":
            try:
                client = Tron(HTTPProvider(api_key=TRONGRID_API_KEY))
                contract_instance = client.get_contract(contract)
                with open(abi_json, "r") as f:
                    contract_instance.abi = json.load(f)
                    totalSupply = contract_instance.functions.totalSupply()
            except Exception as e:
                print(f"TRON: {e}")
                raise e

        else:
            try:
                w3 = Web3(Web3.HTTPProvider(RPC[network]))
                with open(abi_json, "r") as f:
                    abi = json.load(f)
                    contract_instance = w3.eth.contract(address=contract, abi=abi)
                    totalSupply = contract_instance.functions.totalSupply().call()
                    return totalSupply

            except Exception as e:
                print(f"EVM: {e}")
                raise e

    except Exception as e:
        print(f"Reading contract failed: {e}")

    finally:
        return totalSupply


def getImageUrl(imageLink: str):

    for gateway in gateways:
        if imageLink[:8] != "https://":
            suburl = imageLink.replace("://", "/")
            url = "https://" + gateway + "/" + suburl
        else:
            url = imageLink

        try:
            # Send a GET request to the URL
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code == 200:
                # Try to open the image
                image = Image.open(BytesIO(response.content))
                # Try to load the image to ensure it is valid
                image.verify()
                return url
            else:
                print(f"Error: Received status code {response.status_code}")
        except Exception as e:
            print(f"image request failed: {e}")

    return ""


def getIPFSData(metadataLink: str):

    for gateway in gateways:

        if metadataLink[:8] != "https://":
            suburl = metadataLink.replace("://", "/")
            url = "https://" + gateway + "/" + suburl
        else:
            url = metadataLink

        try:
            # Send a GET request to the URL
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code == 200:
                try:
                    # Try to parse the response content as JSON
                    json_data = response.json()
                    return json_data
                except Exception as e:
                    print(f"Invalid JSON: {e}")
            else:
                print(f"Error: Received status code {response.status_code}")
        except Exception as e:
            print(f"Request metadata failed: {e}")

    return None


def getNftData(network: str, contract: str, tokenId: str):

    metadata_url = None
    if network == "tron-mainnet":
        try:
            client = Tron(HTTPProvider(api_key=TRONGRID_API_KEY))
            contract_instance = client.get_contract(contract)
            print("got contract")
            with open(abi_json, "r") as f:
                contract_instance.abi = json.load(f)

                metadata_url = contract_instance.functions.tokenURI(int(tokenId))
                print(metadata_url)
        except Exception as e:
            print(f"Fetching metadata url failed (TRON): {e}")

    else:
        try:
            w3 = Web3(Web3.HTTPProvider(RPC[network]))
            with open(abi_json, "r") as f:
                abi = json.load(f)
                contract_instance = w3.eth.contract(address=contract, abi=abi)
                metadata_url = contract_instance.functions.tokenURI(
                    Web3.to_int(int(tokenId))
                ).call()
        except Exception as e:
            print(f"Fetching metadata url failed (EVM): {e}")

    if metadata_url is not None:
        data_json = getIPFSData(metadata_url)
    else:
        data_json = None

    return data_json

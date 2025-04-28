import json
import traceback
from types import NoneType
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union
from web3 import Web3
from tronpy import Tron
from tronpy.abi import trx_abi
from tronpy.providers import HTTPProvider

import os
import requests
from PIL import Image
from io import BytesIO
import tempfile
from urllib.request import urlopen

from tg_nft_bot.utils.credentials import (
    RESERVOIR_API_KEY,
    TRONGRID_API_KEY,
)
from tg_nft_bot.nft.nft_constants import (
    RESERVOIR_URL,
)
from tg_nft_bot.utils.networks import RPC


current_dir = os.path.dirname(os.path.abspath(__file__))
abi_json = os.path.join(current_dir, "..", "..", "assets", "NFT.json")

gateways = {
    "ipfs": ["ipfs.io", "dweb.link", "gateway.pinata.cloud", "w3s.link"],
    "btfs": ["gateway.btfs.io"],
}


class SaleData(TypedDict):
    type: str
    price: str  # Assuming price can be int or float
    price_usd: str
    currency: str
    marketplace: str


class LogData(TypedDict):
    network: str
    webhook_id: str
    token_id: int
    contract: str
    owner: str
    hash: str
    info: SaleData


def is_valid_url(url: str, is_image=False) -> bool:

    try:
        response = requests.get(url)

        if response.status_code == 200:

            if is_image:
                image = Image.open(BytesIO(response.content))
                image.verify()

            return True
        else:
            return False

    except Exception:
        return False


def get_url(link: str, is_image=False) -> str:

    if link[:8] == "https://":
        url = link
        if is_valid_url(url, is_image):
            return url
        else:
            url = link[:4] + link[5:]
            if is_valid_url(url, is_image):
                return url
    else:
        url_parts = link.split("://")
        protocol = url_parts[0]
        suburl = url_parts[1]
        for gateway in gateways[protocol]:
            url = "https://" + gateway + "/" + protocol + "/" + suburl
            if is_valid_url(url, is_image):
                return url
            else:
                url = url[:4] + url[5:]
                if is_valid_url(url, is_image):
                    return url

    return ""


def is_transfer(topics: List[str]) -> bool:
    return (
        len(topics) == 4
        and topics[0]
        == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    )

def is_mint(addr_from: str, minter: str) -> bool:
    print("address from: ", addr_from)
    print("minter: ", minter)
    return addr_from == minter


def get_log_data(
    network: str, minter: str, webhook_id: str, logs: List[Dict[str, Any]]
) -> Union[List[LogData], NoneType]:

    data: List[LogData] = []
    for log in logs:

        if is_transfer(log["topics"]):

            # check if mint or purchase
            info = get_sale_info(network, minter, log)
            if info is None:
                return None

            data.append(
                LogData(
                    network=network,
                    webhook_id=webhook_id,
                    token_id=int(log["topics"][3], 16),
                    contract=Web3.to_checksum_address(log["address"]),
                    owner=Web3.to_checksum_address("0x" + log["topics"][2][-40:]),
                    hash=log["transactionHash"],
                    info=info,
                )
            )

    return data


def get_sale_info(network: str, minter: str, log) -> Union[SaleData, NoneType]:

    addr_from = Web3.to_checksum_address("0x" + log["topics"][1][-40:])
    if is_mint(addr_from, minter):
        return {
            "type": "mint",
            "price": "N/A",
            "price_usd": "N/A",
            "currency": "N/A",
            "marketplace": "N/A",
        }
    elif network == "tron-mainnet":
        w3 = Web3(Web3.HTTPProvider(RPC[network]))
        tx = w3.eth.get_transaction_receipt(log["transactionHash"])
        for log in tx["logs"]:
            hex_str = log["data"].hex()
            if len(hex_str) == 192:
                price = float(int(hex_str[128:], 16)) / 1e6

                return {
                    "type": "sale",
                    "price": "%.2f" % price,
                    "price_usd": "N/A",
                    "currency": "TRX",
                    "marketplace": "ApeNFT.io",
                }
    else:
        contract = Web3.to_checksum_address(log["address"])
        token_id = int(log["topics"][3], 16)
        url = f"{RESERVOIR_URL[network]}tokens/{contract}%3A{token_id}/activity/v5?limit=1&sortBy=eventTimestamp&types=sale"
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
                "price": f"{price_native:.3f}",
                "price_usd": f"{price_usd:.3f}",
                "currency": currency,
                "marketplace": marketplace,
            }

    return None


def get_collection_info(network, contract):

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


def get_total_supply(network, contract, minter):

    total_supply = None

    try:
        if network == "tron-mainnet":
            try:
                client = Tron(HTTPProvider(api_key=TRONGRID_API_KEY))
                contract_instance = client.get_contract(contract)
                with open(abi_json, "r") as f:
                    contract_instance.abi = json.load(f)
                    contract_instance.abi.append(trx_abi)
                    if(minter != w3.zero_address):
                        total_supply = contract_instance.functions.totalSupply() - contract_instance.functions.balanceOf(minter)
                    else:
                        total_supply = contract_instance.functions.totalSupply()
            except Exception as e:
                print(f"TRON: {e}")
                raise e

        else:
            try:
                w3 = Web3(Web3.HTTPProvider(RPC[network]))
                with open(abi_json, "r") as f:
                    abi = json.load(f)
                    contract_instance = w3.eth.contract(address=contract, abi=abi)
                    if(minter != w3.zero_address):
                        total_supply = contract_instance.functions.totalSupply().call() - contract_instance.functions.balanceOf(minter).call()
                    else:
                        total_supply = contract_instance.functions.totalSupply().call()
                    return total_supply

            except Exception as e:
                print(f"EVM: {e}")
                raise e

    except Exception as e:
        print(f"Reading contract failed: {e}")

    finally:
        return total_supply


def get_metadata_json(metadataLink: str):

    url = get_url(metadataLink)
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


def get_metadata(network: str, contract: str, token_id: str):

    metadata_url = None
    if network == "tron-mainnet":
        try:
            client = Tron(HTTPProvider(api_key=TRONGRID_API_KEY))
            base58_address = Tron.to_base58check_address(Tron.to_hex_address(contract))
            contract_instance = client.get_contract(base58_address)
            with open(abi_json, "r") as f:
                contract_instance.abi = json.load(f)
                metadata_url = contract_instance.functions.tokenURI(int(token_id))
        except Exception as e:
            print(f"Fetching metadata url failed (TRON): {e}")

    else:
        try:
            w3 = Web3(Web3.HTTPProvider(RPC[network]))
            with open(abi_json, "r") as f:
                abi = json.load(f)
                contract_instance = w3.eth.contract(address=contract, abi=abi)
                metadata_url = contract_instance.functions.tokenURI(
                    Web3.to_int(int(token_id))
                ).call()
        except Exception as e:
            print(f"Fetching metadata url failed (EVM): {e}")

    if metadata_url is not None:
        data_json = get_metadata_json(metadata_url)
    else:
        data_json = None

    return data_json

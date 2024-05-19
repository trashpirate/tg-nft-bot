from web3 import Web3
from credentials import ALCHEMY_API_KEY, RPC_URL
import requests

BUYHOLDEARN_WALLET = Web3.to_checksum_address(
    "0x0cf66382d52c2d6c1d095c536c16c203117e2b2f"
)


def calcReflections(address):

    sumOut = getTransfersOut(address)
    sumIn = getTransfersIn(address)

    remaining = sumIn - sumOut
    balance = float(getBalanceOf(address))

    reflections = balance - remaining
    return round(reflections, 3)


def getBalanceOf(address):

    url = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "alchemy_getTokenBalances",
        "params": [
            address,
            ["0x0b61C4f33BCdEF83359ab97673Cb5961c6435F4E"],
        ],
    }
    headers = {"accept": "application/json", "content-type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    json_data = response.json()
    hexBalance = json_data["result"]["tokenBalances"][0]["tokenBalance"]
    balance = Web3.from_wei(Web3.to_int(hexstr=hexBalance), "ether")

    return balance


def getTransfersOut(address):

    url = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "alchemy_getAssetTransfers",
        "params": [
            {
                "fromBlock": "0x1174868",
                "toBlock": "latest",
                "fromAddress": address,
                "contractAddresses": ["0x0b61C4f33BCdEF83359ab97673Cb5961c6435F4E"],
                "withMetadata": False,
                "excludeZeroValue": True,
                "category": ["erc20"],
            }
        ],
    }
    headers = {"accept": "application/json", "content-type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    json_data = response.json()
    transfers = json_data["result"]["transfers"]

    sum = 0
    for tx in transfers:
        if tx["value"] is not None:
            if (
                Web3.to_checksum_address(address) == BUYHOLDEARN_WALLET
                or Web3.to_checksum_address(tx["to"]) == BUYHOLDEARN_WALLET
            ):
                tax = 1
            else:
                tax = 0.98
            sum += tx["value"] / tax

    return sum


def getTransfersIn(address):

    url = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "alchemy_getAssetTransfers",
        "params": [
            {
                "fromBlock": "0x1174868",
                "toBlock": "latest",
                "toAddress": address,
                "contractAddresses": ["0x0b61C4f33BCdEF83359ab97673Cb5961c6435F4E"],
                "withMetadata": False,
                "excludeZeroValue": True,
                "category": ["erc20"],
            }
        ],
    }
    headers = {"accept": "application/json", "content-type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    json_data = response.json()
    transfers = json_data["result"]["transfers"]

    sum = 0
    for tx in transfers:
        if tx["value"] is not None:
            sum += tx["value"]

    return sum

from web3 import Web3
from credentials import ALCHEMY_API_KEY, RPC_URL
import requests
from alchemy import Alchemy, Network

alchemy = Alchemy(ALCHEMY_API_KEY, Network.ETH_MAINNET, max_retries=3)

BUYHOLDEARN_WALLET = Web3.to_checksum_address(
    "0x0cf66382d52c2d6c1d095c536c16c203117e2b2f"
)


async def calcReflections(address):

    try:
        sumOut = await getTransfersOut(address)
        sumIn = await getTransfersIn(address)

        remaining = sumIn - sumOut
        balance = await getBalanceOf(address)
        balance = float(balance)

        reflections = balance - remaining
        return round(reflections, 3)
    except:
        print("Fetching reflections failed.")
        return None


async def getBalanceOf(address):

    try:
        response = alchemy.core.get_token_balances(
            address=address,
            data=["0x0b61C4f33BCdEF83359ab97673Cb5961c6435F4E"],
        )

        hexBalance = response["token_balances"][0].token_balance
        balance = Web3.from_wei(Web3.to_int(hexstr=hexBalance), "ether")
        return balance
    except:
        print("Fetching Balance failed.")
        return None


async def getTransfersOut(address):

    response = alchemy.core.get_asset_transfers(
        from_block="0x1174868",
        from_address=address,
        contract_addresses=["0x0b61C4f33BCdEF83359ab97673Cb5961c6435F4E"],
        with_metadata=False,
        exclude_zero_value=True,
        category=["erc20"],
    )

    txs = response["transfers"]

    sum = 0
    for tx in txs:
        if tx.value is not None:
            if (
                Web3.to_checksum_address(address) == BUYHOLDEARN_WALLET
                or Web3.to_checksum_address(tx.to) == BUYHOLDEARN_WALLET
            ):
                tax = 1
            else:
                tax = 0.98
            sum += tx.value / tax

    return sum


async def getTransfersIn(address):

    response = alchemy.core.get_asset_transfers(
        from_block="0x1174868",
        to_address=address,
        contract_addresses=["0x0b61C4f33BCdEF83359ab97673Cb5961c6435F4E"],
        with_metadata=False,
        exclude_zero_value=True,
        category=["erc20"],
    )

    txs = response["transfers"]

    sum = 0
    for tx in txs:
        if tx.value is not None:
            sum += tx.value

    return sum

import traceback
from types import NoneType
from typing import Union
import requests
from web3 import Web3, HTTPProvider
from tronpy import Tron
from tronpy import providers
from tg_nft_bot.utils.addresses import get_hex_address
from tg_nft_bot.utils.networks import RPC
from tg_nft_bot.utils.credentials import ENV, QUICKNODE_API_KEY, TEST_TYPE, TRONGRID_API_KEY, URL
from tg_nft_bot.streams.streams_utils import get_filter

from tg_nft_bot.config import local, staging, production
config = {"local": local, "staging": staging, "production": production}[ENV]

qn_headers = {
    "Content-Type": "application/json",
        "accept": "application/json",
        "x-api-key": QUICKNODE_API_KEY,  # Replace with your actual API key
    }

qn_stream_url = "https://api.quicknode.com/streams/rest/v1/streams"


def qn_post(url:str, payload:str) -> requests.Response:

    response = requests.post(url, headers=qn_headers, json=payload)
    return response

def qn_get(url:str, data:str={}) -> requests.Response:

    response = requests.request("GET", url, headers=qn_headers, data=data)
    return response

def get_streams() -> str:
    response = qn_get(qn_stream_url)
    data_json = response.json()
    return data_json["data"]

def check_if_stream_exists(id:str) -> bool:
    url = qn_stream_url + "/" + id
    response = qn_get(url)
    if response.status_code == 200:
        return True
    else:
        return False

def get_stream_by_id(id:str) -> str:
    
    url = qn_stream_url + "/" + id
    response = qn_get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception('Webhook does not exist.')

def delete_stream(id:str):

    url = qn_stream_url + "/" + id
    response = requests.request("DELETE", url, headers=qn_headers, data={})
    if response.status_code == 200:
        print("Webhook deleted successfully.")
    elif response.status_code == 404:
        raise Exception('Webhook does not exist.')
    else:
        raise Exception('Deleting webhook failed.')

def pause_stream(id:str):
    url = qn_stream_url + "/" + id + "/pause"
    response = qn_post(url,{})
    print(response.text)


def activate_stream(id:str):

    url = qn_stream_url + "/" + id + "/activate"
    response = qn_post(url,{})
    print(response.text)


def create_qn_stream(network:str, contract:str, route:str, start_block:int = 0, stop_block:int = -1, status = "active", url:str = qn_stream_url) -> Union[str,NoneType]:
    
    stream_id = None
    stream_name = network + "-" + Web3.to_checksum_address(contract) + "-" + route[1:]
    if config.env != 'production':
        stream_name += "-" + config.env
    stream_url = f"{URL}{route}"
    
    if start_block == 0:
        if network == "tron-mainnet":
            client = Tron(providers.HTTPProvider(api_key=TRONGRID_API_KEY))
            start_block = client.get_latest_block_number()
        else:
            w3 = Web3(HTTPProvider(RPC[network]))
            start_block = w3.eth.block_number
    
    streams = get_streams()
    if streams is not None:
        for stream in streams:
            if (
                stream["name"] == stream_name
                and stream["destination_attributes"]["url"] == stream_url
            ):
                if config.env != 'production':
                    delete_stream(stream["id"])
                else:
                    stream_id = stream["id"]
                    print(f"Webhook already exists for this collection: id = {stream_id}")
                    break

    if stream_id is None:
        try:
            filter = get_filter(contract)
            payload = {
                "name": stream_name,
                "network": network,
                "dataset": "receipts",
                "filter_function": filter,
                "region": "usa_east",
                "start_range": start_block,
                "end_range": stop_block,
                "dataset_batch_size": 1,
                "include_stream_metadata": "body",
                "destination": "webhook",
                "fix_block_reorgs": 0,
                "keep_distance_from_tip": 0,
                "destination_attributes": {
                    "url": stream_url,
                    "compression": "none",
                    "headers": {
                        "Content-Type": "application/json",
                    },
                    "max_retry": 3,
                    "retry_interval_sec": 1,
                    "post_timeout_sec": 10,
                },
                "status": status,
            }

            response = qn_post(url=url,payload=payload)
            
            if response.status_code == 201:
                data_json = response.json()
                stream_id = data_json["id"]
                print("Webhook created successfully.")
            else:
                raise Exception('Failed to create stream.')
            
        except Exception as e:
            print("Exception: ", e)
            traceback.print_exc()

    return stream_id      

def create_stream(network:str, contract:str, route:str) -> Union[str,NoneType]:
    if config.env == 'local':
        # Use local/staging-specific test block logic
        base58_contract = Tron.to_base58check_address(Tron.to_hex_address(contract))
        test_block = config.test_blocks[TEST_TYPE][base58_contract]
        webhook_id = create_qn_stream(
            network=network,
            contract=contract,
            route=route,
            start_block=test_block + config.START_BLOCK_OFFSET,
            stop_block=test_block + config.STOP_BLOCK_OFFSET,
            status="active"
        )
    elif config.env == 'staging':
        webhook_id = create_qn_stream(network=network, contract=contract, route=route, status="paused")
        
    else:
         webhook_id = create_qn_stream(network=network, contract=contract, route=route)
    return webhook_id
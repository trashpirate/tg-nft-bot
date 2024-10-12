import base64
import json
import pytest
import requests
from web3 import Web3

from tests.test_utils import get_test_filter
from tg_nft_bot.streams.streams_operations import (
    activate_stream,
    check_if_stream_exists,
    create_stream,
    delete_stream,
    get_streams,
    get_filter,
    get_stream_by_id,
    pause_stream,
    qn_headers
)

from tg_nft_bot.utils.credentials import QUICKNODE_API_KEY
from tg_nft_bot.streams.streams_utils import encode_base64, get_qn_filter_code

TEST_NETWORK = "tron-mainnet"
TEST_CONTRACT = "TDuEK3tqCn9YPFNAFd7SDypdqDisNXm1xr"
TEST_STREAM_ID = "f526fdeb-7f58-414f-9ad6-c2246d32a3f3"

VALID_BASE_CONTRACT = "0xE9e5d3F02E91B8d3bc74Cf7cc27d6F13bdfc0BB6"
INVALID_BASE_CONTRACT = "0xE9e5d3F02E91B8d3bc74CD7cc27d6F13bdfc0BB6"
VALID_TRON_CONTRACT = "TDuEK3tqCn9YPFNAFd7SDypdqDisNXm1xr"
INVALID_TRON_CONTRACT = "TRKTrqwxd1EkjfRMcocVu2CP9onVpHhbt9"

BASE_MINT_BLOCK = 16929599
TRON_MINT_BLOCK = 65927841

blocks = {
    "0x12A961E8cC6c94Ffd0ac08deB9cde798739cF775": 20041787,  # sale: 20041787, mint: 20172127
    "0x49902747796C2ABcc5ea640648551DDbc2c50ba2": 19458239,  # sale: 19458239, mint: 20103930
    "0x897cf93Cef78f8DddFf41962cD63CF030dFF81C8": 15497265,
    "0x0528C4DFc247eA8b678D0CA325427C4ca639DEC2": 15987005,
    "0xE9e5d3F02E91B8d3bc74Cf7cc27d6F13bdfc0BB6": 16929599,  # multi: 16935164, single: 16929599, none: 17974345
}

def stream_filter(network, contract, block):

    filter_code = get_filter(contract)
    # base64_str = encode_base64(filter_code)

    url = "https://api.quicknode.com/streams/rest/v1/streams/test_filter"

    payload = {
        "network": network,
        "dataset": "receipts",
        "filter_function": filter_code,
        "block": str(block),
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "x-api-key": QUICKNODE_API_KEY,  # Replace with your actual API key
    }

    response = requests.post(url, headers=headers, json=payload)
    data_json = response.json()
    print(data_json)

    return data_json["filteredCount"]

def test_all_stream_filters():

    count = stream_filter("base-mainnet", VALID_BASE_CONTRACT, BASE_MINT_BLOCK)
    assert count == 1

    count = stream_filter("tron-mainnet", VALID_TRON_CONTRACT, TRON_MINT_BLOCK)
    assert count == 1

def test_get_streams():
    streams = get_streams()
    
    assert "id" in streams[0]
    
    for stream in streams:
        print(stream["name"] + ": " + stream["id"])

def test_check_if_stream_exists():
    id = create_stream(network=TEST_NETWORK, contract=TEST_CONTRACT, route="/test", status="paused")
    assert check_if_stream_exists(id) == True

def test_get_stream_by_id():
    id = create_stream(network=TEST_NETWORK, contract=TEST_CONTRACT, route="/test", status="paused")
    data = get_stream_by_id(id)
    assert data['id'] == id
    
def test_activate_and_pause_stream():
    id = create_stream(network=TEST_NETWORK, contract=TEST_CONTRACT, route="/test", status="paused")
    
    activate_stream(id)
    data = get_stream_by_id(id)
    assert data['status'] == "active"
    
    pause_stream(id)
    data = get_stream_by_id(id)
    assert data['status'] == "paused"

def test_delete_nonexistent_stream():
    id = "f17e02c5-afc4-4705-b8fc-3cd3013e773e"
    
    with pytest.raises(Exception):
        delete_stream(id)

def test_delete_stream():
    id = create_stream(network=TEST_NETWORK, contract=TEST_CONTRACT, route="/test", status="paused")
    delete_stream(id)
        
    assert not check_if_stream_exists(id)
    
def test_create_stream():
    
    id = create_stream(network=TEST_NETWORK, contract=TEST_CONTRACT, route="/test", status="paused")
    delete_stream(id)
    
    id = create_stream(network=TEST_NETWORK, contract=TEST_CONTRACT, route="/test", status="paused")
    assert check_if_stream_exists(id)
 
 
 
 
 
# def test_create_webhook_request():
    
#     # copy url from https://typedwebhook.tools/
    
#     network = "base-mainnet"
#     contract = "0xE9e5d3F02E91B8d3bc74Cf7cc27d6F13bdfc0BB6"
#     response = create_stream(network=network, contract=contract, route="/test", start_block=BASE_MINT_BLOCK, stop_block=BASE_MINT_BLOCK+1, url="https://typedwebhook.tools/webhook/cef92bac-2658-4cc5-b4b3-f9eca49a3a1b")
    
#     print(response)
    
# def test_create_test_webhook():
    
#     url = "https://api.quicknode.com/streams/rest/v1/streams"

#     filter = get_test_filter()
#     payload = {
#         "name": "ey_test_stream",
#         "network": "base-mainnet",
#         "dataset": "block_with_receipts",
#         "filter_function": filter,
#         "region": "usa_east",
#         "start_range": 16929500,
#         "end_range": 16929600,
#         "dataset_batch_size": 1,
#         "include_stream_metadata": "body",
#         "destination": "webhook",
#         "fix_block_reorgs": 0,
#         "keep_distance_from_tip": 0,
#         "destination_attributes": {
#             "url": "https://exotic-crayfish-striking.ngrok-free.app/test",
#             "compression": "none",
#             "headers": {"Content-Type": "application/json"},
#             "max_retry": 3,
#             "retry_interval_sec": 1,
#             "post_timeout_sec": 10
#         },
#         "status": "active"
#     }

#     try:
#         response = requests.post(url, headers=qn_headers, json=payload)
#         response.raise_for_status()  # Raises an HTTPError for bad responses
#         print("Webhook created successfully:")
#         print(json.dumps(response.json(), indent=2))
#     except requests.exceptions.RequestException as e:
#         print(f"Error creating webhook: {e}")
#         if response.text:
#             print(f"Response content: {response.text}")

# def test_request_webhook():

#     url = "https://typedwebhook.tools/webhook/c4786ad4-ef1e-4215-bd0b-eecc34f15b73"

#     payload = {
#         "name": "Test event",
#         "data": {
#             "id": 1,
#             "name": "Tester McTestFace",
#             "by": "Inngest",
#             "at": "2024-10-11T13:51:46.548Z",
#         },
#         "user": {"email": "tester@example.com"},
#     }
    
#     headers = {
#         "accept": "application/json",
#         "Content-Type": "application/json",
#         "x-api-key": QUICKNODE_API_KEY,  # Replace with your actual API key
#     }
    
#     response = requests.post(url, headers=headers, json=payload)
#     print(response.text)
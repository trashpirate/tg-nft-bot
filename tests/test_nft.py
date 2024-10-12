import json
import pytest
import requests
from tronpy import Tron

from tg_nft_bot.bot.bot_utils import parse_tx
from tg_nft_bot.nft.nft_operations import get_log_data, get_collection_info, get_metadata, get_sale_info, get_total_supply

VALID_BASE_CONTRACT = "0xE9e5d3F02E91B8d3bc74Cf7cc27d6F13bdfc0BB6"
INVALID_BASE_CONTRACT = "0xE9e5d3F02E91B8d3bc74CD7cc27d6F13bdfc0BB6"
VALID_TRON_CONTRACT = "TGG5FzPPXLxfsAAgYEe1LDPnat2RoVZJXf"
INVALID_TRON_CONTRACT = "TRKTrqwxd1EkjfRMcocVu2CP9onVpHhbt9"

def get_receipts(chain_type, tx_type):
    
    with open(f"./tests/test_full_res_{chain_type}_{tx_type}.json", "r") as f:
        json_data = json.load(f)
    
    return json_data

def get_logs(chain_type, tx_type):
    
    with open(f"./tests/test_wh_resp_{chain_type}_{tx_type}.json", "r") as f:
        json_data = json.load(f)
        
    receipts = json_data["receipts"]
    logs_list = [log for receipt in receipts for log in receipt["logs"]]
    return logs_list

def test_parse_tx_tron_sale():
    receipts = get_receipts("tron", "sale")
    logs = parse_tx(receipts)
    
    assert len(logs) == 1
    for log in logs:
        assert log["info"]["type"] == "sale"
        
def test_get_log_data_evm_mint():
    logs_list = get_logs("evm", "mint")
    logs = get_log_data("ethereum-mainnet", "asdfasd", logs_list)
    
    assert len(logs) == 5
    for log in logs:
        assert log["info"]["type"] == "mint"

def test_get_log_data_evm_sale():
    
    logs_list = get_logs("evm", "sale")
    logs = get_log_data("base-mainnet", "asdfasd", logs_list)
    
    assert len(logs) == 1
    for log in logs:
        assert log["info"]["type"] == "sale"
        
def test_get_log_data_tron_mint():
    
    logs_list = get_logs("tron", "mint")
    logs = get_log_data("tron-mainnet", "asdfasd", logs_list)
    
    assert len(logs) == 1
    for log in logs:
        assert log["info"]["type"] == "mint"

def test_get_log_data_tron_sale():
    
    logs_list = get_logs("tron", "sale")
    logs = get_log_data("tron-mainnet", "asdfasd", logs_list)
    
    assert len(logs) == 1
    for log in logs:
        assert log["info"]["type"] == "sale"

def test_get_collection_info_evm():

    network = "base-mainnet"
    [name, collection] = get_collection_info(network, VALID_BASE_CONTRACT)

    print("Name: ", name)
    print("Collection: ", collection)

    assert name == "Touch Grassy"
    assert collection == "touch-grassy"


def test_get_collection_info_evm_invalid_contract():

    network = "base-mainnet"
    [name, collection] = get_collection_info(network, INVALID_BASE_CONTRACT)

    print("Name: ", name)
    print("Collection: ", collection)

    assert name == None
    assert collection == None


def test_get_collection_info_tron():

    network = "tron-mainnet"
    [name, collection] = get_collection_info(network, VALID_TRON_CONTRACT)

    print("Name: ", name)
    print("Collection: ", collection)

    assert name == "PCards"
    assert collection == "pcards"


def test_get_collection_info_tron_invalid_contract():

    network = "tron-mainnet"
    [name, collection] = get_collection_info(network, INVALID_TRON_CONTRACT)

    print("Name: ", name)
    print("Collection: ", collection)

    assert name == None
    assert collection == None


def test_total_supply_evm():

    network = "base-mainnet"
    total_supply = get_total_supply(network, VALID_BASE_CONTRACT)

    assert total_supply == 1000


def test_total_supply_evm_invalid_contract():

    network = "base-mainnet"
    total_supply = get_total_supply(network, INVALID_BASE_CONTRACT)

    assert total_supply == None


def test_total_supply_tron():

    network = "tron-mainnet"
    total_supply = get_total_supply(network, VALID_TRON_CONTRACT)

    assert total_supply == 3438


def test_total_supply_tron_invalid_contract():

    network = "tron-mainnet"
    total_supply = get_total_supply(network, INVALID_TRON_CONTRACT)

    assert total_supply == None


def test_get_metadata_evm():

    network = "base-mainnet"

    data = get_metadata(network, VALID_BASE_CONTRACT, "2")
    assert "name" in data


def test_get_metadata_tron():

    network = "tron-mainnet"

    data = get_metadata(network, VALID_TRON_CONTRACT, "2")
    assert "name" in data

import json
import pytest
import requests
from tronpy import Tron

from tg_nft_bot.nft.nft_operations import get_log_data, getCollectionInfo, getMetadata, get_sale_info, getTotalSupply

VALID_BASE_CONTRACT = "0xE9e5d3F02E91B8d3bc74Cf7cc27d6F13bdfc0BB6"
INVALID_BASE_CONTRACT = "0xE9e5d3F02E91B8d3bc74CD7cc27d6F13bdfc0BB6"
VALID_TRON_CONTRACT = "TGG5FzPPXLxfsAAgYEe1LDPnat2RoVZJXf"
INVALID_TRON_CONTRACT = "TRKTrqwxd1EkjfRMcocVu2CP9onVpHhbt9"

def get_logs(chain_type, tx_type):
    
    with open(f"./tests/test_wh_resp_{chain_type}_{tx_type}.json", "r") as f:
        json_data = json.load(f)
        
    receipts = json_data["receipts"]
    logs_list = [log for receipt in receipts for log in receipt["logs"]]
    return logs_list

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

def test_getCollectionInfo_evm():

    network = "base-mainnet"
    [name, collection] = getCollectionInfo(network, VALID_BASE_CONTRACT)

    print("Name: ", name)
    print("Collection: ", collection)

    assert name == "Touch Grassy"
    assert collection == "touch-grassy"


def test_getCollectionInfo_evm_invalidContract():

    network = "base-mainnet"
    [name, collection] = getCollectionInfo(network, INVALID_BASE_CONTRACT)

    print("Name: ", name)
    print("Collection: ", collection)

    assert name == None
    assert collection == None


def test_getCollectionInfo_tron():

    network = "tron-mainnet"
    [name, collection] = getCollectionInfo(network, VALID_TRON_CONTRACT)

    print("Name: ", name)
    print("Collection: ", collection)

    assert name == "PCards"
    assert collection == "pcards"


def test_getCollectionInfo_tron_invalidContract():

    network = "tron-mainnet"
    [name, collection] = getCollectionInfo(network, INVALID_TRON_CONTRACT)

    print("Name: ", name)
    print("Collection: ", collection)

    assert name == None
    assert collection == None


def test_totalSupply_evm():

    network = "base-mainnet"
    totalSupply = getTotalSupply(network, VALID_BASE_CONTRACT)

    assert totalSupply == 991


def test_totalSupply_evm_invalidContract():

    network = "base-mainnet"
    totalSupply = getTotalSupply(network, INVALID_BASE_CONTRACT)

    assert totalSupply == None


def test_totalSupply_tron():

    network = "tron-mainnet"
    totalSupply = getTotalSupply(network, VALID_TRON_CONTRACT)

    assert totalSupply == 3418


def test_totalSupply_tron_invalidContract():

    network = "tron-mainnet"
    totalSupply = getTotalSupply(network, INVALID_TRON_CONTRACT)

    assert totalSupply == None


def test_getNftData_evm():

    network = "base-mainnet"

    data = getMetadata(network, VALID_BASE_CONTRACT, "2")
    assert "name" in data


def test_getNftData_tron():

    network = "tron-mainnet"

    data = getMetadata(network, VALID_TRON_CONTRACT, "2")
    assert "name" in data


def test_get_sale_info_Tron_Sale():

    network = "tron-mainnet"
    txHash = "5688aaccc33e2c9b512eca62dda4224902eae79210da4bded51434101b3a6fd9"
    tron_hex_address = Tron.to_hex_address("TDuEK3tqCn9YPFNAFd7SDypdqDisNXm1xr")
    address = "0x" + tron_hex_address[2:]
    
    info = get_sale_info(network, address, 926, txHash)
    assert info["type"] == "sale"
    assert info["price"] == "300.00"
    
def test_get_sale_info_Tron_Mint():

    network = "tron-mainnet"
    txHash = "59e07b82fa2c4552a5e780c646eedfa654231047b1c454a6ef8803783a1c2906"
    tron_hex_address = Tron.to_hex_address("TCw15VEWyi8E4BfoowZb2tovHVRyJnx6oq")
    address = "0x" + tron_hex_address[2:]
    
    info = get_sale_info(network, address, 7, txHash)
    assert info["type"] == "mint"
    assert info["price"] == "N/A"
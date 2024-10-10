import pytest

from tg_nft_bot.nft.nft_operations import getCollectionInfo, getNftData, getTotalSupply

VALID_BASE_CONTRACT = "0xE9e5d3F02E91B8d3bc74Cf7cc27d6F13bdfc0BB6"
INVALID_BASE_CONTRACT = "0xE9e5d3F02E91B8d3bc74CD7cc27d6F13bdfc0BB6"
VALID_TRON_CONTRACT = "TGG5FzPPXLxfsAAgYEe1LDPnat2RoVZJXf"
INVALID_TRON_CONTRACT = "TRKTrqwxd1EkjfRMcocVu2CP9onVpHhbt9"


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

    assert totalSupply == 911


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

    data = getNftData(network, VALID_BASE_CONTRACT, "2")
    assert "name" in data


def test_getNftData_tron():

    network = "tron-mainnet"

    data = getNftData(network, VALID_TRON_CONTRACT, "2")
    assert "name" in data

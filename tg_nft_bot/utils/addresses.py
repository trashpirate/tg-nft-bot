from tronpy import Tron
from web3 import Web3


def get_hex_address(contractAddress):
    tron_hex_address = Tron.to_hex_address(contractAddress)
    address = "0x" + tron_hex_address[2:]
    return address


def isTronAddress(address):
    return Tron.is_address(address)


def isEVMAddress(address):
    return Web3.is_address(address)


def is_address(address):
    return Web3.is_address(address) or Tron.is_address(address)

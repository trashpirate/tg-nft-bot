

from tg_nft_bot.utils.addresses import is_address


def test_is_address():
    
    contract = "TDuEK3tqCn9YPFNAFd7SDypdqDisNXm1xr"
    assert is_address(contract) == True
    
    contract = "0xE9e5d3F02E91B8d3bc74Cf7cc27d6F13bdfc0BB6"
    assert is_address(contract) == True
from tronpy import Tron
from tronpy.providers import HTTPProvider
from tg_nft_bot.credentials import TRONGRID_API_KEY
import json

if __name__ == "__main__":

    contrAddr = "TJrgvegnALCFz148TUagF6SPhXfVDmXE2Z"
    client = Tron(HTTPProvider(api_key=TRONGRID_API_KEY))

    cntr = client.get_contract(contrAddr)
    with open("../assets/NFT.json", "r") as f:
        cntr.abi = json.load(f)

    print(dir(cntr.functions))

import requests
from credentials import ALCHEMY_AUTH_TOKEN, URL, MORALIS_API_KEY
from moralis import streams
import json
from frozendict import frozendict


def getMoralisWebhookQuery(chainId, contractAddress, description, tag):

    NFT_transfer_ABI = {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "from",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "to",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "uint256",
                "name": "tokenId",
                "type": "uint256",
            },
        ],
        "name": "Transfer",
        "type": "event",
    }

    body = {
        "description": description,
        "tag": tag,
        "abi": frozendict(NFT_transfer_ABI),
        "topic0": ["Transfer(address,address,uint256)"],
        "allAddresses": True,
        "triggers": [
            {
                "type": "log",
                "contractAddress": contractAddress,
                "functionAbi": NFT_transfer_ABI,
            }
        ],
        "webhookUrl": f"{URL}/nfts",
        "includeNativeTxs": True,
        "includeInternalTxs": True,
        "includeContractLogs": True,
        "chainIds": [chainId],
    }

    return body


def getGraphQLQuery(contractAddress, blockFilter):

    query = """
    {
    block blockFilter {
      logs(filter: {addresses: [contractAddress], topics: ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]}) {
        account {
          address
        }
        topics
        transaction{
          hash
          index
          to{
            address
          }
          from {
            address
          }
          status
        }
      }
    }
  }
  """

    if blockFilter == "None":
        query = query.replace("blockFilter", "")
    else:
        query = query.replace("blockFilter", blockFilter)
    query = query.replace("contractAddress", f'"{contractAddress}"')

    return query


def create_webhook(network, contract, filter):
    print(MORALIS_API_KEY)

    params = {
        "limit": 100,
        "cursor": "",
    }

    result = streams.evm_streams.get_streams(
        api_key=MORALIS_API_KEY,
        params=params,
    )

    print(result)

    stream_body = getMoralisWebhookQuery(network, contract, "TEST", "test")

    result = streams.evm_streams.create_stream(
        api_key=MORALIS_API_KEY,
        body=stream_body,
    )

    print(result)


# url = "https://dashboard.alchemy.com/api/create-webhook"
# query = getGraphQLQuery(contractAddress=contract, blockFilter=filter)

# payload = {
#     "network": network,
#     "webhook_type": "GRAPHQL",
#     "graphql_query": {
#         "query": query,
#         "skip_empty_messages": True,
#     },
#     "webhook_url": f"{URL}/nfts",
# }
# headers = {
#     "accept": "application/json",
#     "X-Alchemy-Token": ALCHEMY_AUTH_TOKEN,
#     "content-type": "application/json",
# }

# response = requests.post(url, json=payload, headers=headers)
# data_json = response.json()

# # needs some error hanlding here
# return data_json["data"]["id"]

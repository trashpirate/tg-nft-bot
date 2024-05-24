import requests
from credentials import TEST, ALCHEMY_AUTH_TOKEN


def getGraphQLQuery(contractAddress, network):

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

    if TEST == "true":
        if network == "BASE_MAINNET":
            filter = '(hash: "0x8b8cc704ac816f0b9155cba4b47480d7b7ad08f9e1180de323e9bdd787ac1d53")'
        else:
            filter = '(hash: "0xa02c605284028f62c099c8e8fb7f72f8aa27093a1ffc09b1c27e725040b1b572")'
    else:
        filter = ""

    query = query.replace("blockFilter", filter)
    query = query.replace("contractAddress", f'"{contractAddress}"')

    return query


def create_webhook(network, contract):

    url = "https://dashboard.alchemy.com/api/create-webhook"
    query = getGraphQLQuery(
        contractAddress=contract,
        network=network,
    )

    payload = {
        "network": network,
        "webhook_type": "GRAPHQL",
        "graphql_query": {
            "query": query,
            "skip_empty_messages": True,
        },
        "webhook_url": "https://exotic-crayfish-striking.ngrok-free.app/nfts",
    }
    headers = {
        "accept": "application/json",
        "X-Alchemy-Token": ALCHEMY_AUTH_TOKEN,
        "content-type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.text)

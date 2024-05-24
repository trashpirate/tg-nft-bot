import requests
from credentials import TEST, ALCHEMY_AUTH_TOKEN


def getGraphQLQuery(contractAddress, network, blockFilter):

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

    query = query.replace("blockFilter", blockFilter)
    query = query.replace("contractAddress", f'"{contractAddress}"')

    return query


def create_webhook(network, contract, filter):

    url = "https://dashboard.alchemy.com/api/create-webhook"
    query = getGraphQLQuery(
        contractAddress=contract, network=network, blockFilter=filter
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

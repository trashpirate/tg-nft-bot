import requests
from credentials import QUICKNODE_API_KEY, TEST, URL
import base64
from web3 import HTTPProvider, Web3

RPC = {
    "ethereum-mainnet": "https://wild-still-yard.quiknode.pro/ac51481a54301aae02e01bc7651111bdfc0835dc/",
    "bnbchain-mainnet": "https://clean-light-bush.bsc.quiknode.pro/8ef25fcc9b3b66c1511c0e8df2accaf49782ace0/",
    "base-mainnet": "https://light-summer-theorem.base-mainnet.quiknode.pro/7e5ea5d963edab5820f279017f1f0aaa02395d5f/",
    "avalanche-mainnet": "https://quick-twilight-river.avalanche-mainnet.quiknode.pro/21047f4234e2f035ad804edf6019e153efb4f2a5/ext/bc/C/rpc/",
    "arbitrum-mainnet": "https://fluent-distinguished-research.arbitrum-mainnet.quiknode.pro/b1c4d69561c9735d4d15c5ad81ad88bb26409bea/",
    "polygon-mainnet": "https://convincing-nameless-replica.matic.quiknode.pro/6dbf5fed1a503962f06a822716e4bb04155dcb2d/",
}


def getQuickNodeFilter(contractAddress):
    js_code = """
    function main(data) {
        try {
            var data = data.streamData;
            var filteredReceipts = [];
            data.forEach(receipt => {
                let relevantLogs = receipt.logs.filter(log =>
                    log.topics[0] === "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef" && log.address.toLowerCase() === contractAddress.toLowerCase() && log.topics.length === 4
                );
                if (relevantLogs.length > 0) {
                    filteredReceipts.push(receipt);
                }
            });

            return {
              totalReceipts: data.length,
              filteredCount: filteredReceipts.length,
              receipts: filteredReceipts
            };
        } catch (e) {
            return {error: e.message};
        }
    }
    """

    js_code = js_code.replace("contractAddress", f'"{contractAddress}"')

    # Convert the JavaScript code to bytes
    js_code_bytes = js_code.encode("utf-8")

    # Encode the bytes using base64
    base64_encoded_js_code = base64.b64encode(js_code_bytes)

    # Convert the base64 bytes back to a string
    base64_encoded_js_code_str = base64_encoded_js_code.decode("utf-8")
    return base64_encoded_js_code_str


def post_quicknode(payload, url):

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "x-api-key": QUICKNODE_API_KEY,  # Replace with your actual API key
    }

    response = requests.post(url, headers=headers, json=payload)
    return response


def get_quicknode_streams():
    url = "https://api.quicknode.com/streams/rest/v1/streams"

    headers = {"accept": "application/json", "x-api-key": QUICKNODE_API_KEY}

    response = requests.request("GET", url, headers=headers, data={})
    data_json = response.json()
    return data_json["data"]


def delete_webhook(id):
    url = "https://api.quicknode.com/streams/rest/v1/streams/" + id
    headers = {"accept": "application/json", "x-api-key": QUICKNODE_API_KEY}
    response = requests.request("DELETE", url, headers=headers, data={})
    print(response.text)


def pause_webhook(id):
    url = "https://api.quicknode.com/streams/rest/v1/streams/" + id + "/pause"
    response = post_quicknode({}, url)
    print(response.text)


def activate_webhook(id):

    url = "https://api.quicknode.com/streams/rest/v1/streams/" + id + "/activate"
    response = post_quicknode({}, url)
    print(response.text)


def create_webhook(network, contract, route):

    stream_id = None
    stream_name = network + "-" + Web3.to_checksum_address(contract)
    if TEST == "true":
        stream_name += "-test"
    streams = get_quicknode_streams()
    if streams is not None:
        for stream in streams:
            if stream["name"] == stream_name:
                stream_id = stream["id"]
                print(f"Webhook already exists for this collection: id = {stream_id}")
                break
                # delete_webhook(stream_id)

    if stream_id is None:
        w3 = Web3(HTTPProvider(RPC[network]))
        currentBlock = w3.eth.block_number
        filter = getQuickNodeFilter(contract)

        # url = "https://api.quicknode.com/streams/rest/v1/streams/test_filter"

        # payload = {
        #     "network": network,
        #     "dataset": "receipts",
        #     "filter_function": filter,
        #     "block": "37953944",
        # }
        # data_json = post_quicknode(payload, url)
        # print(data_json.text)

        url = "https://api.quicknode.com/streams/rest/v1/streams"

        payload = {
            "name": stream_name,
            "network": network,
            "dataset": "receipts",
            "filter_function": filter,
            "region": "usa_east",
            "start_range": currentBlock,
            "end_range": -1,
            "dataset_batch_size": 1,
            "include_stream_metadata": "body",
            "destination": "webhook",
            "fix_block_reorgs": 0,
            "keep_distance_from_tip": 0,
            "destination_attributes": {
                "url": f"{URL}/{route}",
                "compression": "none",
                "headers": {
                    "Content-Type": "application/json",
                },
                "max_retry": 3,
                "retry_interval_sec": 1,
                "post_timeout_sec": 10,
            },
            "status": "active",
        }

        response = post_quicknode(payload, url)
        data_json = response.json()
        return data_json["id"]

    else:
        return stream_id


def create_test_webhook(network, contract, route):
    # network = "ethereum-mainnet"
    # contract = "0x12A961E8cC6c94Ffd0ac08deB9cde798739cF775"

    # transfer
    # "start_range": 19976946,
    # "end_range": 19976948,
    # purchase
    # "start_range": 20025604,
    # "end_range": 20025606,
    # mint
    # "start_range": 19628336,
    # "end_range": 19628338,

    # liquid mint
    # "start_range": 14724597,
    # "end_range": 14724599,

    # flameling purchase
    # 19458239

    # queens mint
    # 15448852

    filter = getQuickNodeFilter(contract)
    url = "https://api.quicknode.com/streams/rest/v1/streams"

    payload = {
        "name": network + "-" + Web3.to_checksum_address(contract) + "-test",
        "network": network,
        "dataset": "receipts",
        "filter_function": filter,
        "region": "usa_east",
        "start_range": 15450503,
        "end_range": 15450505,
        "dataset_batch_size": 1,
        "include_stream_metadata": "body",
        "destination": "webhook",
        "fix_block_reorgs": 0,
        "keep_distance_from_tip": 0,
        "destination_attributes": {
            "url": f"{URL}/{route}",
            "compression": "none",
            "headers": {
                "Content-Type": "application/json",
            },
            "max_retry": 3,
            "retry_interval_sec": 1,
            "post_timeout_sec": 10,
        },
        "status": "active",
    }

    response = post_quicknode(payload, url)
    data_json = response.json()
    return data_json["id"]

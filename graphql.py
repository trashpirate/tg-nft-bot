import requests
from credentials import QUICKNODE_API_KEY, TEST, URL
import base64
from web3 import HTTPProvider, Web3

from helpers import RPC


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
            if (filteredReceipts.length > 0) {
                return {
                totalReceipts: data.length,
                filteredCount: filteredReceipts.length,
                receipts: filteredReceipts
                };
            }
            
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
    stream_url = f"{URL}{route}"

    if TEST == "true":
        stream_name += "-test"
    streams = get_quicknode_streams()
    if streams is not None:
        for stream in streams:

            if (
                stream["name"] == stream_name
                and stream["destination_attributes"]["url"] == stream_url
            ):
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
                "url": stream_url,
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
    # ETHEREUM:0x12A961E8cC6c94Ffd0ac08deB9cde798739cF775:188
    blocks = {
        "0x12A961E8cC6c94Ffd0ac08deB9cde798739cF775": 20041787,  # sale: 20041787, mint: 20172127
        "0x49902747796C2ABcc5ea640648551DDbc2c50ba2": 19458239,  # sale: 19458239, mint: 20103930
        "0x897cf93Cef78f8DddFf41962cD63CF030dFF81C8": 15497265,
        "0x0528C4DFc247eA8b678D0CA325427C4ca639DEC2": 15987005,
        "0xE9e5d3F02E91B8d3bc74Cf7cc27d6F13bdfc0BB6": 16929599,  # multi: 16935164, single: 16929599, none: 17974345
    }

    stream_name = network + "-" + Web3.to_checksum_address(contract)
    stream_url = f"{URL}{route}"

    if TEST == "true":
        stream_name += "-test"
    streams = get_quicknode_streams()
    if streams is not None:
        for stream in streams:

            if (
                stream["name"] == stream_name
                and stream["destination_attributes"]["url"] == stream_url
            ):
                stream_id = stream["id"]
                delete_webhook(stream_id)
                print(f"Webhook updated: id = {stream_id}")

    start_block = blocks[contract] - 10
    end_block = blocks[contract] + 10

    filter = getQuickNodeFilter(contract)
    url = "https://api.quicknode.com/streams/rest/v1/streams"

    payload = {
        "name": network + "-" + Web3.to_checksum_address(contract) + "-test",
        "network": network,
        "dataset": "receipts",
        "filter_function": filter,
        "region": "usa_east",
        "start_range": start_block,
        "end_range": end_block,
        "dataset_batch_size": 1,
        "include_stream_metadata": "body",
        "destination": "webhook",
        "fix_block_reorgs": 0,
        "keep_distance_from_tip": 0,
        "destination_attributes": {
            "url": f"{URL}{route}",
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

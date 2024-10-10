import pytest
import requests
from tg_nft_bot.webhooks.webhook_operations import create_test_webhook

from tg_nft_bot.utils.credentials import QUICKNODE_API_KEY


def test_create_webhook():

    # network = "base-mainnet"
    # contract = "0xE9e5d3F02E91B8d3bc74Cf7cc27d6F13bdfc0BB6"
    # route = "webhook"

    # data = create_test_webhook(network, contract, route)
    # print(data)

    url = "https://api.quicknode.com/streams/rest/v1/streams"

    payload = {
        "name": "My Stream",
        "network": "ethereum-mainnet",
        "dataset": "block",
        "filter_function": "ZnVuY3Rpb24gbWFpbihkYXRhKSB7CiAgICB2YXIgbnVtYmVyRGVjaW1hbCA9IHBhcnNlSW50KGRhdGEuc3RyZWFtRGF0YS5udW1iZXIsIDE2KTsKICAgIHZhciBmaWx0ZXJlZERhdGEgPSB7CiAgICAgICAgaGFzaDogZGF0YS5zdHJlYW1EYXRhLmhhc2gsCiAgICAgICAgbnVtYmVyOiBudW1iZXJEZWNpbWFsCiAgICB9OwogICAgcmV0dXJuIGZpbHRlcmVkRGF0YTsKfQ==",
        "region": "usa_east",
        "start_range": 100,
        "end_range": 200,
        "dataset_batch_size": 1,
        "include_stream_metadata": "body",
        "destination": "webhook",
        "fix_block_reorgs": 0,
        "keep_distance_from_tip": 0,
        "destination_attributes": {
            "url": "https://webhook.site",
            "compression": "none",
            "headers": {"Content-Type": "Test", "Authorization": "again"},
            "max_retry": 3,
            "retry_interval_sec": 1,
            "post_timeout_sec": 10,
        },
        "status": "active",
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "x-api-key": QUICKNODE_API_KEY,  # Replace with your actual API key
    }

    response = requests.post(url, headers=headers, json=payload)

    print(response.text)

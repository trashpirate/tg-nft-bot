import base64
from tronpy import Tron

from tg_nft_bot.utils.addresses import get_hex_address


def get_qn_filter_code(contractAddress):

    address = get_hex_address(contractAddress)
    js_code = """
    function main(payload) {
    const { data, metadata } = payload;

    let returnData = {};
    try {
        const txData = data.length < data[0].length ? data[0] : data
        let filteredReceipts = [];
        txData.forEach(receipt => {
        const relevantLogs = receipt.logs.filter(
            log =>
            log.topics[0] ===
            '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef' &&
            log.address.toLowerCase() ===
            contractAddress.toLowerCase() &&
            log.topics.length === 4
        );
        if (relevantLogs.length > 0) {
            filteredReceipts.push(receipt);
        }
        });
        if (filteredReceipts.length > 0) {
        returnData = {
            totalReceipts: txData.length,
            filteredCount: filteredReceipts.length,
            receipts: filteredReceipts,
            metadata: metadata,
        };
        }
    } catch (error) {
        console.error("Error processing payload:", error.message);
    }
    return returnData;
    }
    """

    js_code = js_code.replace("contractAddress", f'"{address}"')

    return js_code


def encode_base64(js_code):

    base64_filter = base64.b64encode(js_code.encode("utf-8")).decode("utf-8")
    return base64_filter


def get_filter(contractAddress):
    js_code = get_qn_filter_code(contractAddress)
    base64_code = encode_base64(js_code)

    return base64_code

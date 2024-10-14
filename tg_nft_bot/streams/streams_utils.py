import base64
from tronpy import Tron

from tg_nft_bot.utils.addresses import get_hex_address


def get_qn_filter_code(contractAddress):
    
    address = get_hex_address(contractAddress)
    
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

    js_code = js_code.replace("contractAddress", f'"{address}"')
    
    return js_code

def encode_base64(js_code):
    
    base64_filter = base64.b64encode(js_code.encode('utf-8')).decode('utf-8')
    return base64_filter

def get_filter(contractAddress):
    js_code = get_qn_filter_code(contractAddress)
    base64_code = encode_base64(js_code)
    
    return base64_code


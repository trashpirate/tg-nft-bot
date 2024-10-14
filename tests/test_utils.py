import base64


def get_test_filter():
    # JavaScript filter function
    js_filter = """
    function main(data) {
        try {
            var data = data.streamData;
            var filteredReceipts = [];
            data.receipts.forEach(receipt => {
                let relevantLogs = receipt.logs.filter(log =>
                    log.topics[0] === "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef" &&
                    log.topics.length === 3
                );
                if (relevantLogs.length > 0) {
                    filteredReceipts.push(receipt);
                }
            });
            return {
                totalReceipts: data.receipts.length,
                filteredCount: filteredReceipts.length,
                receipts: filteredReceipts
            };
        } catch (e) {
            return {error: e.message};
        }
    }
    """

    # Encode the JavaScript function to base64
    base64_filter = base64.b64encode(js_filter.encode("utf-8")).decode("utf-8")

    return base64_filter

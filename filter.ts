function main(data) {
  try {
    var data = data.streamData;
    var filteredReceipts = [];
    data.forEach((receipt) => {
      let relevantLogs = receipt.logs.filter(
        (log) =>
          log.topics[0] ===
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef" &&
          log.address.toLowerCase() ===
            "0x12A961E8cC6c94Ffd0ac08deB9cde798739cF775".toLowerCase() &&
          log.topics.length === 4
      );
      if (relevantLogs.length > 0) {
        filteredReceipts.push(receipt);
      }
    });

    return {
      totalReceipts: data.length,
      filteredCount: filteredReceipts.length,
      receipts: filteredReceipts,
    };
  } catch (e) {
    return { error: e.message };
  }
}

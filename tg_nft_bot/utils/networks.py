from tg_nft_bot.utils.credentials import QUICKNODE_ENDPOINT_API_KEY

NETWORK_SYMBOLS = {
    "ethereum-mainnet": "ETH",
    "base-mainnet": "BASE",
    "bnbchain-mainnet": "BNB",
    "arbitrum-mainnet": "ARB",
    "avalanche-mainnet": "AVAX",
    "polygon-mainnet": "MATIC",
    "tron-mainnet": "TRON",
}

RPC = {
    "ethereum-mainnet": "https://tame-divine-leaf.quiknode.pro/" + QUICKNODE_ENDPOINT_API_KEY + "/",
    "bnbchain-mainnet": "https://tame-divine-leaf.bsc.quiknode.pro/" + QUICKNODE_ENDPOINT_API_KEY + "/",
    "base-mainnet": "https://tame-divine-leaf.base-mainnet.quiknode.pro/" + QUICKNODE_ENDPOINT_API_KEY + "/",
    "avalanche-mainnet": "https://tame-divine-leaf.avalanche-mainnet.quiknode.pro/" + QUICKNODE_ENDPOINT_API_KEY+"/ext/bc/C/rpc/",
    "arbitrum-mainnet": "https://tame-divine-leaf.arbitrum-mainnet.quiknode.pro/" + QUICKNODE_ENDPOINT_API_KEY + "/",
    "polygon-mainnet": "https://tame-divine-leaf.matic.quiknode.pro/" + QUICKNODE_ENDPOINT_API_KEY + "/",
    "tron-mainnet": "https://tame-divine-leaf.tron-mainnet.quiknode.pro/" + QUICKNODE_ENDPOINT_API_KEY,
    "solana-mainnet": "https://tame-divine-leaf.solana-mainnet.quiknode.pro/" + QUICKNODE_ENDPOINT_API_KEY,
}

SCANS = {
    "ethereum-mainnet": "https://etherscan.io/",
    "bnbchain-mainnet": "https://bscscan.com/",
    "base-mainnet": "https://basescan.org/",
    "avalanche-mainnet": "https://snowtrace.io/",
    "arbitrum-mainnet": "https://arbiscan.io/",
    "polygon-mainnet": "https://polygonscan.com/",
    "tron-mainnet": "https://tronscan.org/",
}

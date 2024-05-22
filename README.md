# TELEGRAM REFLECTIONS BOT
![Version](https://img.shields.io/badge/version-1.1.0-blue.svg?style=for-the-badge)
![Python](https://img.shields.io/badge/python-v3.10.12-blue.svg?style=for-the-badge)
[![License: MIT](https://img.shields.io/github/license/trashpirate/reflections-bot?style=for-the-badge)](https://github.com/trashpirate/reflections-bot/blob/master/LICENSE)

[![Website: nadinaoates.com](https://img.shields.io/badge/Portfolio-00e0a7?style=for-the-badge&logo=Website)](https://nadinaoates.com)
[![LinkedIn: nadinaoates](https://img.shields.io/badge/LinkedIn-0a66c2?style=for-the-badge&logo=LinkedIn&logoColor=f5f5f5)](https://linkedin.com/in/nadinaoates)
[![Twitter: N0_crypto](https://img.shields.io/badge/@N0_crypto-black?style=for-the-badge&logo=X)](https://twitter.com/N0_crypto)


> This telegram calculates the reflections for a particular wallet that holds a ERC20 reflection token. Reflection tokens distribute rewards based on transaction fees. However, the rewards are typically distributed without individual transactions and the reflections collected by each wallet are hard to determine. This bot was designed to allow users to easily determine the amount of reflections they have collected since they acquired the token. The bot calculates the total of incoming and outgoing funds and then calculates the difference of the actual balance and the remaining funds (= reflection amount). The bot was deployed on Heroku.

**Token Contract: Hold ($EARN)**  
https://etherscan.io/address/0x0b61C4f33BCdEF83359ab97673Cb5961c6435F4E#code

### ✨ [EARN Telegram](https://t.me/buyholdearn)

## Installation

```bash
$ virtualenv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

## Running the app

1. Create a new bot with [@BotFather](https://t.me/BotFather) using the command ```/newbot``` and copy the bot token into the ```.env``` file.
2. Get the RPC url and API Key for ```alchemy-sdk``` and the chain you want to interact with. Add the credentials to the ```.env``` file.
3. Start the app: 
    ```bash
    $ python main.py
    ```


## Author

👤 **Nadina Oates**

* Website: [nadinaoates.com](https://nadinaoates.com)
* Twitter: [@N0\_crypto](https://twitter.com/N0\_crypto)
* Github: [@trashpirate](https://github.com/trashpirate)
* LinkedIn: [@nadinaoates](https://linkedin.com/in/nadinaoates)


## 📝 License

Copyright © 2023 [Nadina Oates](https://github.com/trashpirate).

This project is [MIT](https://github.com/trashpirate/betting-dapp-frontend/blob/master/LICENSE) licensed.









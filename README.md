# TELEGRAM NFT BOT
![Version](https://img.shields.io/badge/version-1.1.0-blue.svg?style=for-the-badge)
![Python](https://img.shields.io/badge/python-v3.10.12-blue.svg?style=for-the-badge)
[![License: MIT](https://img.shields.io/github/license/trashpirate/reflections-bot?style=for-the-badge)](https://github.com/trashpirate/reflections-bot/blob/master/LICENSE)

[![Website: nadinaoates.com](https://img.shields.io/badge/Portfolio-00e0a7?style=for-the-badge&logo=Website)](https://nadinaoates.com)
[![LinkedIn: nadinaoates](https://img.shields.io/badge/LinkedIn-0a66c2?style=for-the-badge&logo=LinkedIn&logoColor=f5f5f5)](https://linkedin.com/in/nadinaoates)
[![Twitter: N0_crypto](https://img.shields.io/badge/@N0_crypto-black?style=for-the-badge&logo=X)](https://twitter.com/N0_crypto)

## About

This telegram bot listens to transfer events of NFT collections on evm compatible chains. The admins of a group chat can add the bot to a group and configure their desired NFT collections. The bot was deployed on Heroku.

### Currently supported chains:
- Ethereum
- BNB
- Base
- Arbitrum
- Avalanche
- Polygon

### ✨ [EARN Telegram](https://t.me/buyholdearn)

## Installation

### Configure TG Bot
Create a new bot with [@BotFather](https://t.me/BotFather) using the command ```/newbot``` and copy the bot token into the ```.env``` file.

### Environment variables
Obtain the necessary API keys and save them in a ```.env``` file:
```
TOKEN=<BOT_TOKEN>
QUICKNODE_API_KEY=<API_KEY>
OPENSEA_API_KEY=<API_KEY>
RESERVOIR_API_KEY=<API_KEY>

URL="https://ngrok-url.app"
DATABASE_URL="postgresql://test_user:mysecretpassword@172.17.0.1:5432/local_test_db"
TABLE='collections'
TEST="true"
```

### Setup Python environment
Setup a python environemnt and install the required packages:
```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure Ngrok agent
In order to listen to webhook events from the blockchain ngrok needs to be configured (static domain is recommended):
```bash
ngrok config add-authtoken <AUTH_TOKEN>
```

### Setup local database
To test the bot locally you also need to configure a local database. Install docker and run the following commands:

#### Run docker container:
```bash
sudo docker run --name mypostgres --net host -e POSTGRES_PASSWORD=mysecretpassword -d -p 5432:5432 postgres
```
#### Access docker container:
```bash
sudo docker exec -it mypostgres psql -U postgres
```
#### Set user priveleges:
```bash
CREATE DATABASE local_test_db;
CREATE USER test_user WITH PASSWORD 'mysecretpassword';
GRANT ALL PRIVILEGES ON DATABASE local_test_db TO test_user;
```
#### Access database:
```bash
sudo docker exec -it mypostgres psql -U postgres -d local_test_db
```
#### Allow user access:
```bash
GRANT ALL ON SCHEMA public TO test_user;
```

#### Remove docker container:
```bash
sudo docker rm -f mypostgres
```

#### List running containers:
```bash
sudo docker ps -a
```
#### View IP:
```bash
ifconfig
```

## Running the app
### Development

#### Start the bot:

```bash
$ python main.py
```
#### Start ngrok: 
```bash
ngrok http --domain=<ngrok-url>.ngrok-free.app 8000
```
#### Kill running process:
```bash
kill -9 $(ps -A | grep python | awk '{print $1}')
```

#### Listen to webhook events:


### Production

#### Edit Database:

1. Connect to Heroku
```bash
heroku login
heroku pg:psql --app app-name
```
2. Query database/table and update entry
```bash
SELECT * FROM collections;
UPDATE collections SET <variable> = <id> WHERE id = <id>;
```

## Author

👤 **Nadina Oates**

* Website: [nadinaoates.com](https://nadinaoates.com)
* Twitter: [@N0\_crypto](https://twitter.com/N0\_crypto)
* Github: [@trashpirate](https://github.com/trashpirate)
* LinkedIn: [@nadinaoates](https://linkedin.com/in/nadinaoates)


## 📝 License

Copyright © 2024 [Nadina Oates](https://github.com/trashpirate).
This project is [MIT](https://github.com/trashpirate/reflections-bot/blob/master/LICENSE) licensed.










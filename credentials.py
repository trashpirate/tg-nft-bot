import os
from dotenv import load_dotenv

load_dotenv()

RPC_URL = str(os.getenv("RPC_URL"))
TOKEN = str(os.getenv("TOKEN"))
PORT = int(os.environ.get("PORT", 88))

BOT_TOKEN = f"t{TOKEN}"

ALCHEMY_AUTH_TOKEN = str(os.getenv("ALCHEMY_AUTH_TOKEN"))
ALCHEMY_API_KEY = str(os.getenv("ALCHEMY_API_KEY"))

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}/"
URL = str(os.getenv("URL"))  # "https://exotic-crayfish-striking.ngrok-free.app/getpost/"

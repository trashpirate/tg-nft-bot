import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = str(os.getenv("TOKEN"))
PORT = int(os.environ.get("PORT", 8000))
URL = str(os.getenv("URL"))
DATABASE_URL = str(os.getenv("DATABASE_URL"))
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
TABLE = str(os.getenv("TABLE"))
ALCHEMY_AUTH_TOKEN = str(os.getenv("ALCHEMY_AUTH_TOKEN"))
ALCHEMY_API_KEY_ETH = str(os.getenv("ALCHEMY_API_KEY_ETH"))
ALCHEMY_API_KEY_BASE = str(os.getenv("ALCHEMY_API_KEY_BASE"))

ADMIN_ID = str(os.getenv("ADMIN_ID"))
GROUP_IDS = str(os.getenv("GROUP_IDS"))

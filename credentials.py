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
QUICKNODE_API_KEY = str(os.getenv("QUICKNODE_API_KEY"))
OPENSEA_API_KEY = str(os.getenv("OPENSEA_API_KEY"))

TEST = str(os.getenv("TEST"))

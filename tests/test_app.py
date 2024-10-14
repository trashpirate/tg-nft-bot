from flask import Flask, request, Response
import json

from flask_sqlalchemy import SQLAlchemy

from tg_nft_bot.db.db_operations import initial_config
from tg_nft_bot.utils.credentials import DATABASE_URL

dummy_app = Flask(__name__)
dummy_app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
dummy_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
            
            
@dummy_app.route("/test", methods=["POST"])
def webhook():
    print("Received webhook. Request details:")
    print("Headers:", json.dumps(dict(request.headers), indent=2))

    data = request.get_data()
    try:
        json_data = json.loads(data)
        print("Parsed JSON data:")
        print(json.dumps(json_data, indent=2))
    except json.JSONDecodeError as e:
        print("Error parsing JSON:", str(e))
        print("Raw body:", data.decode())

    return Response("Webhook received", status=200)


if __name__ == "__main__":
    
    initial_config(dummy_app)
    dummy_app.run(port=8000)

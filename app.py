# Set up webserver
from flask import Flask
from dataclasses import dataclass

from credentials import DATABASE_URL


# dataclasses
@dataclass
class WebhookUpdate:
    data: str


flask_app = Flask(__name__)
flask_app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

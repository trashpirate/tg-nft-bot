# Set up webserver
from flask import Flask

from credentials import DATABASE_URL


flask_app = Flask(__name__)
flask_app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

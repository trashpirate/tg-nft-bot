from flask_sqlalchemy import SQLAlchemy
import psycopg2
from psycopg2.extras import RealDictCursor
from web3 import Web3

from credentials import DATABASE_URL, GROUP_IDS, TABLE

db = SQLAlchemy()
from app import flask_app


class CollectionConfigs(db.Model):
    __tablename__ = TABLE

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    network = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    webhookid = db.Column(db.String(255), nullable=True)
    chats = db.Column(db.ARRAY(db.BigInteger), nullable=True)


class CollectionTestConfigs(db.Model):
    __tablename__ = "collections_test"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    network = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    webhookid = db.Column(db.String(255), nullable=True)
    chats = db.Column(db.ARRAY(db.BigInteger), nullable=True)


def connect_to_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode="prefer")
    return conn


def query_table(table):
    with flask_app.app_context():
        collections = CollectionConfigs.query.all()
        collection_list = [
            [collection.name, collection.address, collection.network]
            for collection in collections
        ]
    return collection_list


def query_network_by_webhook(table, webhookId):
    with flask_app.app_context():
        entry = CollectionConfigs.query.filter_by(webhookId=webhookId).first()

    if entry is None:
        return None
    else:
        return entry.network


def query_website_by_contract(table, contract, network):
    with flask_app.app_context():
        entry = CollectionConfigs.query.filter_by(
            address=contract, network=network
        ).first()

    if entry is None:
        return None
    else:
        return entry.website


async def check_if_exists(network, contract):

    with flask_app.app_context():

        entry = CollectionConfigs.query.filter_by(
            address=contract, network=network
        ).first()

    if entry is None:
        return None
    else:
        return entry.id


async def initial_config():
    print("initializing app with database...")
    db.init_app(flask_app)
    # with flask_app.app_context():
    #     db.drop_all()
    #     db.create_all()
    #     db.session.commit()


async def add_config(name, network, address, website, webhookid, ids):

    with flask_app.app_context():
        config = CollectionConfigs(
            name=name,
            network=network,
            address=Web3.to_checksum_address(address),
            website=website,
            webhookid=webhookid,
            chats=ids,
        )
        db.session.add(config)
        db.session.commit()


async def update_config(name, network, address, website, webhookid, ids):

    with flask_app.app_context():

        row_to_update = CollectionConfigs.query.filter_by(
            address=address, network=network
        ).first()
        row_to_update.name = name
        row_to_update.network = network
        row_to_update.address = Web3.to_checksum_address(address)
        row_to_update.website = website
        row_to_update.webhookid = webhookid
        row_to_update.chats = ids
        db.session.commit()

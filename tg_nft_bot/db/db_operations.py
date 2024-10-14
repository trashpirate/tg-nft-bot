from flask_sqlalchemy import SQLAlchemy
import psycopg2
from psycopg2.extras import RealDictCursor
from web3 import Web3

from tg_nft_bot.utils.credentials import TABLE

db = SQLAlchemy()
from tg_nft_bot.bot.bot_config import flask_app


class CollectionConfigs(db.Model):
    __tablename__ = TABLE

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=True)
    slug = db.Column(db.String(255), nullable=True)
    network = db.Column(db.String(255), nullable=True)
    contract = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    webhookId = db.Column(db.String(255), nullable=True)
    chats = db.Column(db.ARRAY(db.BigInteger), nullable=True)


# class BotAuthorizations(db.Model):
#     __tablename__ = "authorizations"

#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(255), nullable=True)
#     tgId = db.Column(db.BigInteger, nullable=True)


def query_table():
    with flask_app.app_context():
        collections = CollectionConfigs.query.all()
        collection_list = [
            {
                "id": collection.id,
                "name": collection.name,
                "slug": collection.slug,
                "contract": collection.contract,
                "network": collection.network,
                "website": collection.website,
                "webhookId": collection.webhookId,
                "chats": collection.chats,
            }
            for collection in collections
        ]
    return collection_list


def query_collection(network, contract):
    with flask_app.app_context():
        collection = CollectionConfigs.query.filter_by(
            contract=contract, network=network
        ).first()
        collection_dict = {
            "id": collection.id,
            "name": collection.name,
            "slug": collection.slug,
            "contract": collection.contract,
            "network": collection.network,
            "website": collection.website,
            "webhookId": collection.webhookId,
            "chats": collection.chats,
        }
    return collection_dict


def query_collection_by_webhook(webhook_id):
    with flask_app.app_context():
        collection = CollectionConfigs.query.filter_by(webhookId=webhook_id).first()
        collection_dict = {
            "id": collection.id,
            "name": collection.name,
            "slug": collection.slug,
            "contract": collection.contract,
            "network": collection.network,
            "website": collection.website,
            "webhookId": collection.webhookId,
            "chats": collection.chats,
        }
    return collection_dict


def query_collection_by_chat(chatId):
    with flask_app.app_context():

        collections = CollectionConfigs.query.filter(
            CollectionConfigs.chats.any(chatId)
        ).all()
        collection_list = [
            {
                "id": collection.id,
                "name": collection.name,
                "slug": collection.slug,
                "contract": collection.contract,
                "network": collection.network,
                "website": collection.website,
                "webhookId": collection.webhookId,
                "chats": collection.chats,
            }
            for collection in collections
        ]
    return collection_list


def query_collection_by_id(cid):
    with flask_app.app_context():
        collection = CollectionConfigs.query.filter_by(id=cid).first()
        collection_dict = {
            "id": collection.id,
            "name": collection.name,
            "slug": collection.slug,
            "contract": collection.contract,
            "network": collection.network,
            "website": collection.website,
            "webhookId": collection.webhookId,
            "chats": collection.chats,
        }
    return collection_dict


def query_network_by_webhook(webhook_id):
    with flask_app.app_context():
        entry = CollectionConfigs.query.filter_by(webhookId=webhook_id).first()

    if entry is None:
        return None
    else:
        return entry.network


def query_website_by_contract(contract, network):
    with flask_app.app_context():
        entry = CollectionConfigs.query.filter_by(
            contract=contract, network=network
        ).first()

    if entry is None:
        return None
    else:
        return entry.website


def query_name_by_contract(network, contract):
    with flask_app.app_context():
        entry = CollectionConfigs.query.filter_by(
            contract=contract, network=network
        ).first()

    if entry is None:
        return None
    else:
        return entry.name


def query_slug_by_contract(network, contract):
    with flask_app.app_context():
        entry = CollectionConfigs.query.filter_by(
            contract=contract, network=network
        ).first()

    if entry is None:
        return None
    else:
        return entry.slug


def query_chats_by_contract(network, contract):
    with flask_app.app_context():
        entry = CollectionConfigs.query.filter_by(
            contract=contract, network=network
        ).first()

    if entry is None:
        return None
    else:
        return entry.chats


def check_if_exists(network, contract):
    print("Network: ",  network)
    print("Contract: ", contract)
    with flask_app.app_context():

        entry = CollectionConfigs.query.filter_by(
            contract=contract, network=network
        ).first()
    print("Entry: ", entry)
    if entry is None:
        return None
    else:
        return entry.id


def initial_config():
    print("initializing app with database...")
    db.init_app(flask_app)
    with flask_app.app_context():
        engine = db.get_engine()
        if not engine.dialect.has_table(engine.connect(), TABLE):
            db.drop_all()
            db.create_all()
            db.session.commit()


def add_config(name, slug, network, contract, website, webhook_id, chats):

    with flask_app.app_context():
        config = CollectionConfigs(
            name=name,
            slug=slug,
            network=network,
            contract=Web3.to_checksum_address(contract),
            website=website,
            webhookId=webhook_id,
            chats=chats,
        )
        db.session.add(config)
        db.session.commit()


def update_config(name, slug, network, contract, website, webhook_id, chats):

    with flask_app.app_context():

        row_to_update = CollectionConfigs.query.filter_by(
            contract=contract, network=network
        ).first()
        row_to_update.name = name
        row_to_update.slug = slug
        row_to_update.network = network
        row_to_update.contract = Web3.to_checksum_address(contract)
        row_to_update.website = website
        row_to_update.webhookId = webhook_id
        row_to_update.chats = chats
        db.session.commit()


def update_chats_by_id(id, chats):
    with flask_app.app_context():
        collection_update = CollectionConfigs.query.filter(
            CollectionConfigs.id == id
        ).one()
        collection_update.chats = chats
        db.session.commit()


def delete_config_by_id(id):

    with flask_app.app_context():
        collection = CollectionConfigs.query.filter(CollectionConfigs.id == id).one()
        db.session.delete(collection)
        db.session.commit()

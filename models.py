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
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(f"SELECT * FROM {TABLE}")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    info = [[r.get("name"), r.get("address"), r.get("network")] for r in rows]
    return info


def query_network_by_webhook(table, webhookId):
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(f"SELECT * FROM {TABLE} WHERE webhookid='{webhookId}'")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return [result.get("chats"), result.get("network")] if result else None


def query_website_by_contract(table, contract):
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(f"SELECT * FROM {TABLE} WHERE address='{contract}'")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return [result.get("chats"), result.get("website")] if result else None


async def check_if_exists(network, contract):
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        f"SELECT * FROM {TABLE} WHERE network='{network}' AND address='{contract}'"
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result if result else None


async def initial_config():
    id_strings = GROUP_IDS.split(",")
    ids = [int("-100" + chatid) for chatid in id_strings]

    print("initializing app with database...")
    db.init_app(flask_app)
    with flask_app.app_context():
        db.drop_all()
        db.create_all()

        config = CollectionConfigs(
            name="Flames",
            network="ETH_MAINNET",
            address=Web3.to_checksum_address(
                "0x12A961E8cC6c94Ffd0ac08deB9cde798739cF775"
            ),
            website="https://flames.buyholdearn.com",
            webhookid="wh_plrryh8h7hvii7lf",
            chats=ids,
        )
        db.session.add(config)

        config = CollectionConfigs(
            name="Flamelings",
            network="ETH_MAINNET",
            address=Web3.to_checksum_address(
                "0x49902747796C2ABcc5ea640648551DDbc2c50ba2"
            ),
            website="https://flamelings.buyholdearn.com",
            webhookid="wh_52iyjprm4bguy0nb",
            chats=ids,
        )
        db.session.add(config)

        db.session.commit()


async def add_config(name, network, address, website, webhookid, ids):
    # id_strings = GROUP_IDS.split(",")
    # ids = [int("-100" + chatid) for chatid in id_strings]

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

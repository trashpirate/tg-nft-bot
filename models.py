from flask_sqlalchemy import SQLAlchemy
import psycopg2
from psycopg2.extras import RealDictCursor

from credentials import DATABASE_URL

db = SQLAlchemy()


class CollectionConfigs(db.Model):
    __tablename__ = "collections"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    network = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    website = db.Column(db.String(255), nullable=False)
    webhookid = db.Column(db.String(255), nullable=False)
    chats = db.Column(db.ARRAY(db.BigInteger), nullable=True)


def connect_to_db():
    conn = psycopg2.connect(DATABASE_URL, sslmode="prefer")
    return conn


def query_table(table_name):
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def query_network_by_webhook(table_name, webhookId):
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(f"SELECT * FROM {table_name} WHERE webhookid='{webhookId}'")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return [result.get("chats"), result.get("network")] if result else None


def query_website_by_contract(table_name, contract):
    conn = connect_to_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(f"SELECT * FROM {table_name} WHERE address='{contract}'")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return [result.get("chats"), result.get("website")] if result else None

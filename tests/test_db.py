

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from tg_nft_bot.db.db_operations import initial_config
from tg_nft_bot.utils.credentials import DATABASE_URL

# Constants for Testing
TEST_TABLE = "collections"

# Pytest fixture to create a Flask app and DB for testing
@pytest.fixture
def app():
    """Create and configure a new Flask app instance for each test."""
    dummy_app = Flask(__name__)
    dummy_app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    dummy_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return dummy_app

@pytest.fixture
def db(app):
    """Create a SQLAlchemy object and initialize it with the app."""
    db = SQLAlchemy(app)
    with app.app_context():
        db.create_all()
    yield db
    db.session.remove()
    db.drop_all()
    
def test_initial_config(app, db, mocker):
    """Test if `initial_config` creates tables when they don't exist."""
    
    # Mock the `has_table` method to return False (simulate table not existing).
    mocker.patch(
        'sqlalchemy.engine.reflection.Inspector.has_table', 
        return_value=False
    )

    # Call the function
    initial_config(app, db)

    # Verify that the table was created
    engine = db.get_engine()
    inspector = engine.inspect()
    assert TEST_TABLE in inspector.get_table_names()
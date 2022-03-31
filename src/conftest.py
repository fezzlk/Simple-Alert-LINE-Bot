# flake8: noqa
import os
import sys
import pytest
from dotenv import load_dotenv
from src.mongo_client import mongo_client
from src import app
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

load_dotenv()


@pytest.fixture()
def dummy_app():
    return app


@pytest.fixture(scope='function', autouse=True)
def reset_db():
    mongo_client.drop_database('db')

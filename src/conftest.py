# flake8: noqa
import os
import sys
import pytest
from dotenv import load_dotenv
from src.mongo_client import mongo_client

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

load_dotenv()


@pytest.fixture(scope='function', autouse=True)
def reset_db():
    print('hoge')
    mongo_client.drop_database('db')

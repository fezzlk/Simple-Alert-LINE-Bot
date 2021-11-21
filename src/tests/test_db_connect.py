from src import config
from src.mongo_client import mongo_client


def test_connect_mongo_with():
    mongo_client.db.users.insert_one({'name': 'fuga'})

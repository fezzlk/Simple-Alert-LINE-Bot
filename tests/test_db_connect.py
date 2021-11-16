import config
from PyMongo import MongoClient


def test_connect_mongo_with():
    with MongoClient(config.MONGO_URI) as client:
        assert client is not None
